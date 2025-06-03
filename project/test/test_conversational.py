import os
import sys
import unittest
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from conversational.conversational import (
    GenerateKubernetesConfigTool, GenerateTerraformConfigTool, 
    GetChangeLogsTool, SummarizeAnalysisTool, GetLatestAnalysisTool,
    create_analysis_agent
)



class TestConversationalAgent(unittest.TestCase):
    def setUp(self):
        self.test_repo_url = "https://github.com/test/repo.git"
        self.test_profile = {
            "memory": {"base_mb": 100},
            "cpu": {"estimated_cores": 2},
            "bandwidth": {"network_calls_per_execution": 10}
        }

    @patch('conversational.conversational.get_latest_analysis')
    def test_get_latest_analysis_tool(self, mock_get_latest):
        mock_get_latest.return_value = {"profile": self.test_profile}
        tool = GetLatestAnalysisTool()
        result = tool._run(self.test_repo_url)
        self.assertIsInstance(result, str)
        mock_get_latest.assert_called_once_with(self.test_repo_url)

    @patch('conversational.conversational.get_change_logs')
    def test_get_change_logs_tool(self, mock_get_logs):
        test_logs = [{
            "timestamp": "2025-05-21",
            "changes": ["Memory increased", "CPU cores added"]
        }]
        mock_get_logs.return_value = test_logs
        tool = GetChangeLogsTool()
        result = tool._run(self.test_repo_url)
        self.assertIsInstance(result, str)
        self.assertIn("Memory increased", result)
        mock_get_logs.assert_called_once_with(self.test_repo_url)

    @patch('conversational.conversational.get_latest_analysis')
    @patch('conversational.conversational.generate_kubernetes_config')
    def test_generate_kubernetes_config_tool(self, mock_generate, mock_get_latest):
        mock_get_latest.return_value = {"profile": self.test_profile}
        mock_generate.return_value = "/path/to/config.yaml"
        tool = GenerateKubernetesConfigTool()
        result = tool._run(self.test_repo_url)
        self.assertIn("config.yaml", result)
        mock_get_latest.assert_called_once()
        mock_generate.assert_called_once()

    @patch('conversational.conversational.get_latest_analysis')
    @patch('conversational.conversational.generate_terraform_config')
    def test_generate_terraform_config_tool(self, mock_generate, mock_get_latest):
        mock_get_latest.return_value = {"profile": self.test_profile}
        mock_generate.return_value = "/path/to/config.tf"
        tool = GenerateTerraformConfigTool()
        result = tool._run(self.test_repo_url)
        self.assertIn("config.tf", result)
        mock_get_latest.assert_called_once()
        mock_generate.assert_called_once()

    @patch('conversational.conversational.summarize_analysis')
    def test_summarize_analysis_tool(self, mock_summarize):
        mock_summarize.return_value = "Test summary"
        tool = SummarizeAnalysisTool()
        result = tool._run(self.test_repo_url)
        self.assertEqual(result, "Test summary")
        mock_summarize.assert_called_once_with(self.test_repo_url)

    def test_create_analysis_agent(self):
        agent = create_analysis_agent(model="gpt-3.5-turbo")
        self.assertEqual(agent.role, "Resource Analyzer")
        self.assertEqual(len(agent.tools), 12)
        self.assertFalse(agent.allow_delegation)

if __name__ == '__main__':
    unittest.main()