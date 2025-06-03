import os
import sys
import unittest
from unittest.mock import Mock, patch, MagicMock
import datetime
from pathlib import Path

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from conversational.run_convo import GithubResourceAnalyzer, analyzer_main, init_database, store_analysis, compare_and_log_changes, generate_kubernetes_config

class TestGithubResourceAnalyzer(unittest.TestCase):
    def setUp(self):
        self.github_token = "test_token"
        self.llm_api_key = "test_key"
        
    @patch('conversational.run_convo.RepoFetcher')
    @patch('conversational.run_convo.ResourceAnalyzer')
    @patch('conversational.run_convo.ResourceProfiler')
    def test_initialization(self, mock_profiler, mock_analyzer, mock_fetcher):
        analyzer = GithubResourceAnalyzer(self.github_token, self.llm_api_key)
        
        mock_fetcher.assert_called_once_with(self.github_token)
        mock_analyzer.assert_called_once_with(self.llm_api_key)
        self.assertIsNotNone(analyzer.profiler)

    @patch('conversational.run_convo.RepoFetcher')
    @patch('conversational.run_convo.ResourceAnalyzer')
    @patch('conversational.run_convo.ResourceProfiler')
    @patch('git.Repo')
    def test_analyze_repository(self, mock_git, mock_profiler, mock_analyzer, mock_fetcher):
        # Setup mocks
        mock_instance = mock_fetcher.return_value
        mock_instance.fetch_repo.return_value = "/fake/path"
        mock_instance.get_repo_structure.return_value = {"files": ["test.py"]}
        
        mock_profiler_instance = mock_profiler.return_value
        mock_profiler_instance.profile_repository.return_value = {
            "recommendations": {"memory": {}, "cpu": {}, "bandwidth": {}}
        }
        
        mock_git.return_value.head.commit.hexsha = "test_hash"
        
        # Test
        analyzer = GithubResourceAnalyzer(self.github_token, self.llm_api_key)
        result = analyzer.analyze_repository("test_url")
        
        self.assertEqual(result["repository_url"], "test_url")
        self.assertIn("structure", result)
        self.assertIn("profile", result)
        self.assertIn("commit_hash", result)

class TestAnalyzerMain(unittest.TestCase):
    def setUp(self):
        self.github_token = "test_token"
        self.llm_api_key = "test_key"
        self.valid_repo_url = "https://github.com/test/repo.git"
        
    def test_invalid_url(self):
        result = analyzer_main("invalid_url", self.github_token, self.llm_api_key)
        self.assertEqual(result, {'error': 'Invalid URL. Please enter a valid GitHub .git URL.'})

    @patch('conversational.run_convo.init_database')
    @patch('conversational.run_convo.GithubResourceAnalyzer')
    @patch('conversational.run_convo.store_analysis')
    @patch('conversational.run_convo.compare_and_log_changes')
    @patch('conversational.run_convo.generate_kubernetes_config')
    @patch('os.makedirs')
    @patch('json.dump')
    def test_successful_analysis(self, mock_json_dump, mock_makedirs, mock_k8s, 
                               mock_compare, mock_store, mock_analyzer, mock_db):
        # Setup mocks
        mock_db.return_value = MagicMock()
        
        mock_analyzer_instance = mock_analyzer.return_value
        mock_analyzer_instance.analyze_repository.return_value = {
            "repository_url": self.valid_repo_url,
            "profile": {
                "recommendations": {
                    "memory": {"recommended_allocation": "1024MB"},
                    "cpu": {"recommended_cores": 2},
                    "bandwidth": {"peak_requirement": "100Mbps"}
                }
            }
        }
        
        mock_compare.return_value = {"status": "unchanged"}
        
        # Test
        result = analyzer_main(self.valid_repo_url, self.github_token, self.llm_api_key)
        
        self.assertIsNotNone(result)
        self.assertIn("results", result)
        self.assertIn("estimated", result)
        self.assertEqual(result["estimated"]["estimated_Memory"], "1024MB")
        self.assertEqual(result["estimated"]["estimated_CPU_cores"], 2)
        self.assertEqual(result["estimated"]["estimated_network_bandwidth"], "100Mbps")

    @patch('conversational.run_convo.init_database')
    @patch('conversational.run_convo.GithubResourceAnalyzer')
    @patch('conversational.run_convo.store_analysis')
    @patch('conversational.run_convo.compare_and_log_changes')
    @patch('conversational.run_convo.generate_kubernetes_config')
    def test_missing_keys_handling(self, mock_k8s, mock_compare, mock_store, mock_analyzer, mock_db):
        # Setup mocks
        mock_db.return_value = MagicMock()
        mock_analyzer_instance = mock_analyzer.return_value
        mock_analyzer_instance.analyze_repository.return_value = {
            "repository_url": self.valid_repo_url,
            "commit_hash": "test_hash",
            "structure": {"files": []},
            "profile": {
                "recommendations": {
                    
                }
            }
        }
        mock_compare.return_value = {"status": "unchanged"}
        mock_k8s.return_value = True
        
        result = analyzer_main(self.valid_repo_url, self.github_token, self.llm_api_key)
        self.assertEqual(result, {'error': "Analysis failed: 'memory'"})

if __name__ == '__main__':
    unittest.main()