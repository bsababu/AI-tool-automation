import os
import sys
import unittest
from unittest.mock import Mock, patch


sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from githubRepo.resource_profiler import ResourceProfiler

class TestResourceProfiler(unittest.TestCase):
    def setUp(self):
        self.mock_analyzer = Mock()

        self.mock_analyzer.network_libs = ["requests", "urllib", "aiohttp"]
        self.profiler = ResourceProfiler(self.mock_analyzer)
        
        # Sample test data
        self.sample_file_profile = {
            "resources": {
                "memory": {
                    "base_mb": 100.0,
                    "peak_mb": 200.0,
                    "scaling_factor": 1.5,
                    "notes": "Test memory notes"
                },
                "cpu": {
                    "estimated_cores": 2.0,
                    "parallelization_potential": "medium",
                    "notes": "Test CPU notes"
                },
                "bandwidth": {
                    "network_calls_per_execution": 5,
                    "data_transfer_mb": 10.0,
                    "bandwidth_mbps": 1.0,
                    "transfer_type": "bulk",
                    "notes": "Test bandwidth notes"
                }
            },
            "source": "llm"
        }

    def test_profile_repository_empty(self):
        """Test profiling an empty repository"""
        with patch('os.walk') as mock_walk:
            mock_walk.return_value = []
            result = self.profiler.profile_repository("/fake/path", {})
            
            self.assertIn("recommendations", result)
            self.assertIn("network_summary", result)
            self.assertEqual(result["files_analyzed"], 0)

    @patch('os.walk')
    def test_profile_repository_with_files(self, mock_walk):
        """Test profiling a repository with Python files"""
        mock_walk.return_value = [
            ("/root", [], ["test.py", "main.py", "setup.py", "test_file.py"])
        ]
        
        self.mock_analyzer.analyze_file.return_value = self.sample_file_profile
        
        result = self.profiler.profile_repository("/fake/path", {})

        self.mock_analyzer.network_libs = ["requests", "urllib", "aiohttp"]
        self.mock_analyzer.analyze_file.return_value = self.sample_file_profile
        
        result = self.profiler.profile_repository("/fake/path", {})
        
        self.assertEqual(result["files_analyzed"], 1)
        self.assertIn("component_profiles", result)
        self.assertEqual(result["sources_used"]["llm"], 1)  # Only main.py (excluding test.py and setup.py)
        

    def test_update_aggregate_profile(self):
        """Test updating aggregate profile with file results"""
        total_profile = {
            "resources": {
                "memory": {"estimated_base_mb": 0.0, "estimated_peak_mb": 0.0, "scaling_factor": 1.0, "notes": ""},
                "cpu": {"estimated_cores": 0.0, "parallelization_potential": "low", "notes": ""},
                "bandwidth": {"network_calls_per_execution": 0, "data_transfer_mb": 0.0, "bandwidth_mbps": 0.0, "transfer_type": "bulk", "notes": ""}
            }
        }
        
        self.profiler._update_aggregate_profile(total_profile, self.sample_file_profile)
        
        self.assertEqual(total_profile["resources"]["memory"]["estimated_base_mb"], 100.0)
        self.assertEqual(total_profile["resources"]["memory"]["estimated_peak_mb"], 200.0)
        self.assertEqual(total_profile["resources"]["cpu"]["parallelization_potential"], "medium")
        self.assertEqual(total_profile["resources"]["bandwidth"]["network_calls_per_execution"], 5)

    def test_summarize_network_usage(self):
        """Test network usage summarization"""
        total_profile = {
            "component_profiles": {
                "file1.py": {
                    "bandwidth": {
                        "network_calls_per_execution": 5,
                        "data_transfer_mb": 10.0,
                        "notes": "Using requests"
                    }
                }
            }
        }
        
        self.mock_analyzer.network_libs = ["requests"]
        summary = self.profiler.summarize_network_usage(total_profile)
        
        self.assertEqual(summary["total_network_calls"], 5)
        self.assertEqual(summary["estimated_data_transfer_kbps"], 10.0)
        self.assertIn("requests", summary["network_libraries_used"])

    def test_generate_recommendations(self):
        """Test recommendations generation"""
        profile = {
            "resources": {
                "memory": {
                    "estimated_base_mb": 100.0,
                    "estimated_peak_mb": 200.0,
                    "scaling_factor": 2.0,
                },
                "cpu": {
                    "estimated_cores": 3.0,
                    "parallelization_potential": "high",
                },
                "bandwidth": {
                    "bandwidth_mbps": 10.0,
                    "transfer_type": "streaming",
                }
            }
        }
        
        recommendations = self.profiler._generate_recommendations(profile)
        
        self.assertEqual(recommendations["memory"]["min_allocation"], "100MB")
        self.assertEqual(recommendations["memory"]["recommended_allocation"], "300MB")
        self.assertEqual(recommendations["cpu"]["recommended_cores"], 3)
        self.assertEqual(recommendations["scaling"]["priority_dimension"], "memory")

if __name__ == '__main__':
    unittest.main()