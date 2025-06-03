import unittest
import os
import json
from unittest.mock import patch, MagicMock, mock_open
import openai
import sys
from io import StringIO

from dotenv import load_dotenv


sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from githubRepo.resource_analyzer import ResourceAnalyzer


class TestResourceAnalyzer(unittest.TestCase):
    def setUp(self):
        load_dotenv("../.env")
        llm_api_key = os.getenv("TEST_KEY_O")
        self.analyzer = ResourceAnalyzer(llm_api_key)
        
        # Sample Python code for testing
        self.sample_code = """
                import pandas as pd
                import numpy as np
                import requests

                def process_data(url):
                    # Download data
                    response = requests.get(url)
                    data = response.json()
                    
                    # Process with pandas
                    df = pd.DataFrame(data)
                    result = df.groupby('category').agg({'value': ['mean', 'sum']})
                    
                    # Some computation
                    for i in range(len(df)):
                        for j in range(len(df.columns)):
                            df.iloc[i, j] = df.iloc[i, j] * 2
                    
                    return result
                """
        
        # Sample repo structure
        self.repo_structure = {
            "files": ["main.py", "utils.py", "data_processor.py"],
            "dirs": ["tests", "config"]
        }

    @patch('builtins.open', new_callable=mock_open, read_data="import os\nprint('Hello')")
    def test_analyze_file_simple(self, mock_file):
        """Test analyzing a simple file with static analysis"""
        with patch.object(self.analyzer, '_analyze_code') as mock_analyze:
            mock_analyze.return_value = {"test": "result"}
            result = self.analyzer.analyze_file("test.py", {})
            self.assertEqual(result, {"test": "result"})
            mock_analyze.assert_called_once()

    def test_compute_static_metrics(self):
        """Test static metrics computation"""
        metrics = self.analyzer._compute_static_metrics(self.sample_code, "test.py")
        self.assertIsInstance(metrics, dict)
        self.assertIn("loc", metrics)
        self.assertIn("libraries", metrics)
        self.assertGreater(metrics["loc"], 0)
        self.assertIn("pandas", metrics["libraries"])
        self.assertIn("numpy", metrics["libraries"])
        self.assertIn("requests", metrics["libraries"])

    def test_estimate_memory_usage(self):
        """Test memory usage estimation"""
        memory_profile = self.analyzer._estimate_memory_usage(self.sample_code)
        self.assertIsInstance(memory_profile, dict)
        self.assertIn("base_mb", memory_profile)
        self.assertIn("peak_mb", memory_profile)
        self.assertIn("scaling_factor", memory_profile)
        self.assertIn("notes", memory_profile)
        # Should detect pandas and numpy as memory intensive
        self.assertGreater(memory_profile["base_mb"], 100.0)
        self.assertGreater(memory_profile["peak_mb"], 100.0)

    def test_estimate_cpu_usage(self):
        """Test CPU usage estimation"""
        cpu_profile = self.analyzer._estimate_cpu_usage(self.sample_code)
        self.assertIsInstance(cpu_profile, dict)
        self.assertIn("complexity", cpu_profile)
        self.assertIn("estimated_cores", cpu_profile)
        self.assertIn("parallelization_potential", cpu_profile)
        self.assertIn("notes", cpu_profile)
        # Should detect nested loops
        self.assertEqual(cpu_profile["complexity"], "O(n^2)")

    def test_estimate_bandwidth_usage(self):
        """Test bandwidth usage estimation"""
        bandwidth_profile = self.analyzer._estimate_bandwidth_usage(self.sample_code)
        self.assertIsInstance(bandwidth_profile, dict)
        self.assertIn("network_calls_per_execution", bandwidth_profile)
        self.assertIn("data_transfer_mb", bandwidth_profile)
        self.assertIn("bandwidth_mbps", bandwidth_profile)
        self.assertIn("transfer_type", bandwidth_profile)
        self.assertIn("notes", bandwidth_profile)
        # Should detect requests library and get method
        self.assertGreater(bandwidth_profile["network_calls_per_execution"], 0)
        self.assertGreater(bandwidth_profile["data_transfer_mb"], 0.0)

    @patch('githubRepo.resource_analyzer.load_dotenv')
    @patch('githubRepo.resource_analyzer.os.getenv')
    def test_get_llm_insights_success(self, mock_getenv, mock_load_dotenv):
        """Test successful LLM insights retrieval"""

        # Set up environment mocks
        mock_getenv.side_effect = lambda key: {
            "OPENAI_API_KEY": "12345677",
            "MODEL": "gpt-3.5-turbo",
        }.get(key)

        # Prepare the mocked LLM client
        mock_response = MagicMock()
        mock_choice = MagicMock()
        mock_message = MagicMock()
        mock_message.content = json.dumps({
            "memory": {"base_mb": 100.0, "peak_mb": 200.0, "scaling_factor": 2.0, "notes": "Test"},
            "cpu": {"complexity": "O(n)", "estimated_cores": 2.0, "parallelization_potential": "medium", "notes": "Test"},
            "bandwidth": {"network_calls_per_execution": 1, "data_transfer_mb": 2.0, "bandwidth_mbps": 1.0, "transfer_type": "bulk", "notes": "Test"}
        })
        mock_choice.message = mock_message
        mock_response.choices = [mock_choice]

        mock_llm_client = MagicMock()
        mock_llm_client.chat.completions.create.return_value = mock_response

        # Inject the mocked LLM client
        self.analyzer.llm_client = mock_llm_client

        result = self.analyzer._get_llm_insights(
            self.sample_code,
            "test.py",
            self.repo_structure,
            {"loc": 20, "libraries": ["pandas", "requests"]}
        )

        self.assertIsInstance(result, dict)
        self.assertIn("memory", result)
        self.assertIn("cpu", result)
        self.assertIn("bandwidth", result)
        self.assertEqual(result["memory"]["base_mb"], 150.0)
        self.assertEqual(result["memory"]["peak_mb"], 300.0)
        self.assertEqual(result["cpu"]["complexity"], "O(n^2)")
        self.assertEqual(result["bandwidth"]["network_calls_per_execution"], 5)


    @patch('openai.OpenAI')
    def test_get_llm_insights_failure(self, mock_openai):
        """Test LLM insights failure and error handling"""
        mock_client = MagicMock()
        mock_openai.return_value = mock_client
        mock_client.chat.completions.create.side_effect = openai.APIError("API Error")
        
        with patch('os.getenv', return_value='gpt-3.5-turbo'):
            result = self.analyzer._get_llm_insights(self.sample_code, "test.py", self.repo_structure, {"loc": 20, "libraries": ["pandas", "requests"]})
            
            self.assertIsInstance(result, dict)
            self.assertIn("error", result)
            self.assertEqual(result["error"], "API Error")

    @patch('openai.OpenAI')
    def test_get_llm_insights_failure(self, mock_openai):
        """Test LLM insights failure and error handling"""
        # Mock the OpenAI client to raise an exception
        mock_client = MagicMock()
        mock_openai.return_value = mock_client
        mock_client.chat.completions.create.side_effect = Exception("API Error")
        
        with patch('os.getenv', return_value='gpt-3.5-turbo'):
            result = self.analyzer._get_llm_insights(self.sample_code, "test.py", self.repo_structure, {"loc": 20, "libraries": ["pandas", "requests"]})
            
            self.assertIsInstance(result, dict)
            self.assertIn("error", result)

    @patch('builtins.open', new_callable=mock_open, read_data="import flask\n@app.route('/')\ndef index(): return 'Hello'")
    def test_analyze_file_with_flask(self, mock_file):
        """Test analyzing a Flask application file"""
        with patch.object(self.analyzer, '_get_llm_insights') as mock_llm:
            mock_llm.return_value = {"error": "LLM failed"}
            
            result = self.analyzer.analyze_file("app.py", self.repo_structure)
            
            self.assertIsInstance(result, dict)
            self.assertIn("metrics", result)
            self.assertIn("resources", result)
            self.assertEqual(result["source"], "static")
            self.assertTrue(result["resources"]["static_fallback"])
            
            # Check if bandwidth was properly estimated for Flask
            self.assertGreater(result["resources"]["bandwidth"]["network_calls_per_execution"], 0)
            self.assertGreater(result["resources"]["bandwidth"]["bandwidth_mbps"], 0.1)

    @patch('builtins.open', new_callable=mock_open, read_data="import threading\ndef worker(): pass\nt = threading.Thread(target=worker)\nt.start()")
    def test_analyze_file_with_threading(self, mock_file):
        """Test analyzing a file with threading"""
        with patch.object(self.analyzer, '_get_llm_insights') as mock_llm:
            
            mock_llm.return_value = {
                    "memory": {"base_mb": 100.0, "peak_mb": 200.0},
                    "cpu": {"estimated_cores": 2.0, "parallelization_potential": "medium"},
                    "bandwidth": {"bandwidth_mbps": 1.0}
                }
            
            result = self.analyzer.analyze_file("threaded.py", self.repo_structure)
            
            self.assertIsInstance(result, dict)
            self.assertEqual(result["source"], "static")
            
            # Check if CPU was properly estimated for threading
            self.assertEqual(result["resources"]["cpu"]["parallelization_potential"], "medium")
            self.assertGreater(result["resources"]["cpu"]["estimated_cores"], 1.0)

    def test_is_valid_llm_profile(self):
        """Test LLM profile validation"""
        # Valid profile
        valid_profile = {
            "memory": {"base_mb": 100.0, "peak_mb": 200.0},
            "cpu": {"estimated_cores": 2.0},
            "bandwidth": {"bandwidth_mbps": 1.0}
        }
        self.assertTrue(self.analyzer._is_valid_llm_profile(valid_profile))
        
        # Invalid profiles
        invalid_profile1 = {
            "memory": {"base_mb": 0.5, "peak_mb": 200.0},  # base_mb too low
            "cpu": {"estimated_cores": 2.0},
            "bandwidth": {"bandwidth_mbps": 1.0}
        }
        self.assertFalse(self.analyzer._is_valid_llm_profile(invalid_profile1))
        
        invalid_profile2 = {
            "memory": {"base_mb": 100.0, "peak_mb": 0.5},  # peak_mb too low
            "cpu": {"estimated_cores": 2.0},
            "bandwidth": {"bandwidth_mbps": 1.0}
        }
        self.assertFalse(self.analyzer._is_valid_llm_profile(invalid_profile2))
        
        invalid_profile3 = {
            "memory": {"base_mb": 100.0, "peak_mb": 200.0},
            "cpu": {"estimated_cores": 0.4},  # estimated_cores too low
            "bandwidth": {"bandwidth_mbps": 1.0}
        }
        self.assertFalse(self.analyzer._is_valid_llm_profile(invalid_profile3))

    def test_get_analysis_counts(self):
        """Test getting analysis counts"""
        # Initially both counts should be 0
        counts = self.analyzer.get_analysis_counts()
        self.assertEqual(counts["llm"], 0)
        self.assertEqual(counts["static"], 0)
        
        # Simulate some analyses
        self.analyzer.llm_count = 5
        self.analyzer.static_count = 3
        
        counts = self.analyzer.get_analysis_counts()
        self.assertEqual(counts["llm"], 5)
        self.assertEqual(counts["static"], 3)

    @patch('builtins.open')
    def test_analyze_file_error_handling(self, mock_open):
        """Test error handling when file cannot be read"""
        mock_open.side_effect = Exception("Cannot read file")
        
        result = self.analyzer.analyze_file("nonexistent.py", self.repo_structure)
        
        self.assertIsInstance(result, dict)
        self.assertEqual(result["source"], "static")
        self.assertTrue(result["resources"]["static_fallback"])
        self.assertEqual(self.analyzer.static_count, 1)


if __name__ == '__main__':
    unittest.main()
