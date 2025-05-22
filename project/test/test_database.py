import sys
import unittest
import sqlite3
import json
import os
from datetime import datetime

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from RL.db_feedback import compare_and_log_changes, init_database


class TestDatabaseAnalysis(unittest.TestCase):
    def setUp(self):
        """Set up test database and sample data before each test"""
        self.db_path = "test_analysis_history.db"
        self.conn = init_database()
        self.sample_results = {
            "repository_url": "https://github.com/test/repo",
            "commit_hash": "abcdef1234567890", 
            "structure": {
                "src": ["file1.py", "file2.py"],
                "tests": ["test1.py"]
            },
            "profile": {
                "recommendations": {
                    "memory": {"recommended_allocation": "100MB"},
                    "cpu": {"recommended_cores": 2},
                    "bandwidth": {"peak_requirement": "10Mbps"}
                },
                "sources_used": {"llm": 1, "static": 1},
                "static_metrics": {}
            }
        }

    def tearDown(self):
        """Clean up after each test"""
        self.conn.close()
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_threshold_changes(self):
        """Test changes just above/below the threshold"""
        initial_profile = dict(self.sample_results["profile"])
        # Change just above 10% threshold
        initial_profile["recommendations"]["memory"]["recommended_allocation"] = "89MB" # 11% change
        initial_profile["recommendations"]["bandwidth"]["peak_requirement"] = "8.9Mbps" # 11% change

        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO repository_analyses (repo_url, timestamp, commit_hash, structure, profile, sources_used, static_metrics) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                self.sample_results["repository_url"],
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                self.sample_results["commit_hash"],
                json.dumps(self.sample_results["structure"]),
                json.dumps(initial_profile),
                json.dumps(initial_profile["sources_used"]),
                "{}"
            )
        )
        self.conn.commit()
        
        result = compare_and_log_changes(self.conn, self.sample_results)
        changes = result["changes"]
        self.assertTrue(any("Memory:" in change for change in changes))
        self.assertTrue(any("Bandwidth:" in change for change in changes))

    def test_empty_structure(self):
        """Test with empty file structure"""
        empty_results = dict(self.sample_results)
        empty_results["structure"] = {}
        
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO repository_analyses (repo_url, timestamp, commit_hash, structure, profile, sources_used, static_metrics) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                self.sample_results["repository_url"],
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                self.sample_results["commit_hash"],
                json.dumps({"src": ["old.py"]}),
                json.dumps(self.sample_results["profile"]),
                json.dumps(self.sample_results["profile"]["sources_used"]),
                "{}"
            )
        )
        self.conn.commit()
        
        result = compare_and_log_changes(self.conn, empty_results)
        changes = result["changes"]
        self.assertTrue(any("Removed files:" in change for change in changes))

    def test_invalid_metrics(self):
        """Test with invalid metric values"""
        invalid_results = dict(self.sample_results)
        invalid_results["profile"]["recommendations"]["memory"]["recommended_allocation"] = "invalid"
        invalid_results["profile"]["recommendations"]["bandwidth"]["peak_requirement"] = "invalid"
        
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO repository_analyses (repo_url, timestamp, commit_hash, structure, profile, sources_used, static_metrics) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                self.sample_results["repository_url"],
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                self.sample_results["commit_hash"],
                json.dumps(self.sample_results["structure"]),
                json.dumps(self.sample_results["profile"]),
                json.dumps(self.sample_results["profile"]["sources_used"]),
                "{}"
            )
        )
        self.conn.commit()

        with self.assertRaises(ValueError):
            compare_and_log_changes(self.conn, invalid_results)

    def test_missing_fields(self):
        """Test with missing fields in analysis"""
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM repository_analyses")
        self.conn.commit()
        incomplete_results = {
            "repository_url": "https://github.com/test/repo",
            "commit_hash": "different_hash_123",
            "structure": {},
            "profile": {
                "recommendations": {
                    "memory": {"recommended_allocation": "100MB"},
                    "cpu": {"recommended_cores": 2},
                    "bandwidth": {"peak_requirement": "10Mbps"}
                },
                "sources_used": {"llm": 0, "static": 0},
                "static_metrics": {} 
                }
        }
        
        result = compare_and_log_changes(self.conn, incomplete_results)
        self.assertEqual(result["message"], "No previous analysis found.")

    def test_multiple_changes(self):
        """Test multiple simultaneous changes"""
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM repository_analyses")
        self.conn.commit()
        
        initial_profile = dict(self.sample_results["profile"])
        initial_profile["recommendations"]["memory"]["recommended_allocation"] = "200MB"
        initial_profile["recommendations"]["cpu"]["recommended_cores"] = 4
        initial_profile["recommendations"]["bandwidth"]["peak_requirement"] = "20Mbps"
        initial_profile["sources_used"] = {"llm": 0, "static": 1}
        
        initial_structure = {
            "src": ["old_file.py"],
            "tests": ["old_test.py"]
        }
        
        old_commit = "oldcommit1234567890"
        cursor.execute(
            "INSERT INTO repository_analyses (repo_url, timestamp, commit_hash, structure, profile, sources_used, static_metrics) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                self.sample_results["repository_url"],
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                old_commit,
                json.dumps(initial_structure),
                json.dumps(initial_profile),
                json.dumps(initial_profile["sources_used"]),
                "{}"
            )
        )
        self.conn.commit()
        
        result = compare_and_log_changes(self.conn, self.sample_results)
        changes = result["changes"]
        self.assertGreater(len(changes), 3)
        self.assertTrue(any("New commit:" in change for change in changes))

def test_no_previous_analysis(test_db, sample_results):
    """Test when there is no previous analysis"""
    result = compare_and_log_changes(test_db, sample_results)
    assert result["message"] == "No previous analysis found."
    assert result["changes"] == []

def test_identical_analysis(test_db, sample_results):
    """Test when current and previous analyses are identical"""
    # Store initial analysis
    cursor = test_db.cursor()
    cursor.execute(
        "INSERT INTO repository_analyses (repo_url, timestamp, commit_hash, structure, profile, sources_used, static_metrics) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (
            sample_results["repository_url"],
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            sample_results["commit_hash"],
            json.dumps(sample_results["structure"]),
            json.dumps(sample_results["profile"]),
            json.dumps(sample_results["profile"]["sources_used"]),
            "{}"
        )
    )
    test_db.commit()
    
    result = compare_and_log_changes(test_db, sample_results)
    assert result["message"] == "No changes."
    assert result["changes"] == []

def test_different_commit(test_db, sample_results):
    """Test when commit hash changes"""
    # Store initial analysis
    cursor = test_db.cursor()
    cursor.execute(
        "INSERT INTO repository_analyses (repo_url, timestamp, commit_hash, structure, profile, sources_used, static_metrics) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (
            sample_results["repository_url"],
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "oldcommit1234567890",
            json.dumps(sample_results["structure"]),
            json.dumps(sample_results["profile"]),
            json.dumps(sample_results["profile"]["sources_used"]),
            "{}"
        )
    )
    test_db.commit()
    
    result = compare_and_log_changes(test_db, sample_results)
    assert "New commit:" in result["changes"][0]
    assert result["message"] == "Changes detected."

def test_resource_changes(test_db, sample_results):
    """Test when resource recommendations change"""
    # Store initial analysis with different resources
    initial_profile = dict(sample_results["profile"])
    initial_profile["recommendations"]["memory"]["recommended_allocation"] = "200MB"
    initial_profile["recommendations"]["cpu"]["recommended_cores"] = 4
    initial_profile["recommendations"]["bandwidth"]["peak_requirement"] = "20Mbps"
    
    cursor = test_db.cursor()
    cursor.execute(
        "INSERT INTO repository_analyses (repo_url, timestamp, commit_hash, structure, profile, sources_used, static_metrics) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (
            sample_results["repository_url"],
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            sample_results["commit_hash"],
            json.dumps(sample_results["structure"]),
            json.dumps(initial_profile),
            json.dumps(sample_results["profile"]["sources_used"]),
            "{}"
        )
    )
    test_db.commit()
    
    result = compare_and_log_changes(test_db, sample_results)
    changes = result["changes"]
    assert any("Memory:" in change for change in changes)
    assert any("CPU cores:" in change for change in changes)
    assert any("Bandwidth:" in change for change in changes)

def test_file_structure_changes(test_db, sample_results):
    """Test when file structure changes"""
    # Store initial analysis with different file structure
    initial_structure = {
        "src": ["file1.py"],
        "tests": ["test1.py", "test2.py"]
    }
    
    cursor = test_db.cursor()
    cursor.execute(
        "INSERT INTO repository_analyses (repo_url, timestamp, commit_hash, structure, profile, sources_used, static_metrics) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (
            sample_results["repository_url"],
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            sample_results["commit_hash"],
            json.dumps(initial_structure),
            json.dumps(sample_results["profile"]),
            json.dumps(sample_results["profile"]["sources_used"]),
            "{}"
        )
    )
    test_db.commit()
    
    result = compare_and_log_changes(test_db, sample_results)
    changes = result["changes"]
    assert any("New files:" in change for change in changes)
    assert any("Removed files:" in change for change in changes)

def test_source_changes(test_db, sample_results):
    """Test when sources used changes"""
    # Store initial analysis with different sources
    initial_profile = dict(sample_results["profile"])
    initial_profile["sources_used"] = {"llm": 0, "static": 2}
    
    cursor = test_db.cursor()
    cursor.execute(
        "INSERT INTO repository_analyses (repo_url, timestamp, commit_hash, structure, profile, sources_used, static_metrics) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (
            sample_results["repository_url"],
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            sample_results["commit_hash"],
            json.dumps(sample_results["structure"]),
            json.dumps(initial_profile),
            json.dumps(initial_profile["sources_used"]),
            "{}"
        )
    )
    test_db.commit()
    
    result = compare_and_log_changes(test_db, sample_results)
    changes = result["changes"]
    assert any("Llm analysis:" in change for change in changes)
    assert any("Static analysis:" in change for change in changes)


if __name__ == '__main__':
    unittest.main()