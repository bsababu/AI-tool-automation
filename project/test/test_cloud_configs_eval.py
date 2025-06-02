import os
import tempfile
import yaml
import unittest
from deepeval import evaluate
from deepeval.metrics import AnswerRelevancyMetric, HallucinationMetric
from deepeval.test_case import LLMTestCase
from deepeval.dataset import EvaluationDataset

from project.container.aws_lambda import generate_aws_lambda_config
from project.container.aws_ec2 import generate_aws_ecs_config
from project.container.azure_container import generate_azure_container_config
from project.container.gcp import generate_gcp_cloudrun_config
from project.container.kubernates import generate_kubernetes_config
from project.container.openshift import generate_openshift_config
from project.container.terraform import generate_terraform_config

# Test data
mock_results = {
    "repository_url": "https://github.com/example/project.git",
    "profile": {
        "recommendations": {
            "memory": {"recommended_allocation": "2048MB"},
            "cpu": {"recommended_cores": 2},
            "bandwidth": {"peak_requirement": "500Mbps"}
        }
    }
}

class TestCloudConfigsEvaluation(unittest.TestCase):
    def setUp(self):
        # Initialize metrics
        self.answer_relevancy = AnswerRelevancyMetric(threshold=0.7)
        self.hallucination = HallucinationMetric(threshold=0.3)
        
        # Create temporary directory for test files
        self.temp_dir = tempfile.TemporaryDirectory()
        
    def tearDown(self):
        self.temp_dir.cleanup()

    def evaluate_config(self, config, expected_config, context):
        """Helper method to evaluate a configuration using DeepEval metrics"""
        test_case = LLMTestCase(
            input=str(mock_results),
            actual_output=str(config),
            expected_output=str(expected_config),
            retrieval_context=[context]
        )
        
        # Evaluate using both metrics
        relevancy_score = self.answer_relevancy.measure(test_case)
        hallucination_score = self.hallucination.measure(test_case)
        
        return {
            'relevancy': relevancy_score,
            'hallucination': hallucination_score,
            'test_case': test_case
        }

    def test_aws_lambda_config_evaluation(self):
        path = os.path.join(self.temp_dir.name, "lambda.yaml")
        result = generate_aws_lambda_config(mock_results, path)
        
        with open(path) as f:
            config = yaml.safe_load(f)
            
        expected_config = {
            "Resources": {
                "LambdaFunction": {
                    "Properties": {
                        "MemorySize": 2048,
                        "Environment": {
                            "Variables": {
                                "MEMORY_REQUIREMENT": "2048",
                                "CPU_CORES": "2"
                            }
                        }
                    }
                }
            }
        }
        
        context = "AWS Lambda configuration should match memory and CPU requirements from input"
        evaluation = self.evaluate_config(config, expected_config, context)
        
        self.assertGreaterEqual(evaluation['relevancy'], 0.7)
        self.assertLessEqual(evaluation['hallucination'], 0.3)

    def test_aws_ecs_config_evaluation(self):
        path = os.path.join(self.temp_dir.name, "ecs.yaml")
        result = generate_aws_ecs_config(mock_results, path)
        
        with open(path) as f:
            config = yaml.safe_load(f)
            
        expected_config = {
            "Resources": {
                "TaskDefinition": {
                    "Properties": {
                        "Memory": "2048",
                        "Cpu": "2048",
                        "ContainerDefinitions": [{
                            "Memory": 2048,
                            "Cpu": 2048
                        }]
                    }
                }
            }
        }
        
        context = "AWS ECS configuration should match memory and CPU requirements from input"
        evaluation = self.evaluate_config(config, expected_config, context)
        
        self.assertGreaterEqual(evaluation['relevancy'], 0.7)
        self.assertLessEqual(evaluation['hallucination'], 0.3)

    def test_azure_container_config_evaluation(self):
        path = os.path.join(self.temp_dir.name, "azure.yaml")
        result = generate_azure_container_config(mock_results, path)
        
        with open(path) as f:
            config = yaml.safe_load(f)
            
        expected_config = {
            "properties": {
                "containers": [{
                    "properties": {
                        "resources": {
                            "requests": {
                                "cpu": 2,
                                "memoryInGB": 2.0
                            }
                        }
                    }
                }]
            }
        }
        
        context = "Azure Container configuration should match memory and CPU requirements from input"
        evaluation = self.evaluate_config(config, expected_config, context)
        
        self.assertGreaterEqual(evaluation['relevancy'], 0.7)
        self.assertLessEqual(evaluation['hallucination'], 0.3)

    def test_gcp_cloudrun_config_evaluation(self):
        path = os.path.join(self.temp_dir.name, "gcp.yaml")
        result = generate_gcp_cloudrun_config(mock_results, path)
        
        with open(path) as f:
            config = yaml.safe_load(f)
            
        expected_config = {
            "spec": {
                "template": {
                    "spec": {
                        "containers": [{
                            "resources": {
                                "limits": {
                                    "cpu": "2",
                                    "memory": "2048MB"
                                }
                            }
                        }]
                    }
                }
            }
        }
        
        context = "GCP Cloud Run configuration should match memory and CPU requirements from input"
        evaluation = self.evaluate_config(config, expected_config, context)
        
        self.assertGreaterEqual(evaluation['relevancy'], 0.7)
        self.assertLessEqual(evaluation['hallucination'], 0.3)

    def test_kubernetes_config_evaluation(self):
        path = os.path.join(self.temp_dir.name, "k8s.yaml")
        result = generate_kubernetes_config(mock_results, path)
        
        with open(path) as f:
            config = yaml.safe_load(f)
            
        expected_config = {
            "spec": {
                "template": {
                    "spec": {
                        "containers": [{
                            "resources": {
                                "limits": {
                                    "memory": "2048Mi",
                                    "cpu": "2"
                                }
                            },
                            "env": [{
                                "value": "Network bandwidth: 500Mbps"
                            }]
                        }]
                    }
                }
            }
        }
        
        context = "Kubernetes configuration should match memory, CPU, and bandwidth requirements from input"
        evaluation = self.evaluate_config(config, expected_config, context)
        
        self.assertGreaterEqual(evaluation['relevancy'], 0.7)
        self.assertLessEqual(evaluation['hallucination'], 0.3)

    def test_openshift_config_evaluation(self):
        path = os.path.join(self.temp_dir.name, "openshift.yaml")
        result = generate_openshift_config(mock_results, path)
        
        with open(path) as f:
            config = yaml.safe_load(f)
            
        expected_config = {
            "spec": {
                "template": {
                    "spec": {
                        "containers": [{
                            "resources": {
                                "limits": {
                                    "memory": "2048MB",
                                    "cpu": "2"
                                }
                            }
                        }]
                    }
                }
            }
        }
        
        context = "OpenShift configuration should match memory and CPU requirements from input"
        evaluation = self.evaluate_config(config, expected_config, context)
        
        self.assertGreaterEqual(evaluation['relevancy'], 0.7)
        self.assertLessEqual(evaluation['hallucination'], 0.3)

    def test_terraform_config_evaluation(self):
        path = os.path.join(self.temp_dir.name, "terraform.tf")
        result_path = generate_terraform_config(mock_results, path)
        
        with open(path) as f:
            content = f.read()
            
        expected_content = {
            "instance_type": "t2.large",
            "name": "project-instance",
            "bandwidth": "500Mbps"
        }
        
        context = "Terraform configuration should match instance type and bandwidth requirements from input"
        evaluation = self.evaluate_config(content, str(expected_content), context)
        
        self.assertGreaterEqual(evaluation['relevancy'], 0.7)
        self.assertLessEqual(evaluation['hallucination'], 0.3)

    def test_bulk_evaluation(self):
        """Test evaluating all configurations in bulk using EvaluationDataset"""
        test_cases = []
        
        # Generate and collect all configurations
        configs = {
            'lambda': generate_aws_lambda_config(mock_results, os.path.join(self.temp_dir.name, "lambda.yaml")),
            'ecs': generate_aws_ecs_config(mock_results, os.path.join(self.temp_dir.name, "ecs.yaml")),
            'azure': generate_azure_container_config(mock_results, os.path.join(self.temp_dir.name, "azure.yaml")),
            'gcp': generate_gcp_cloudrun_config(mock_results, os.path.join(self.temp_dir.name, "gcp.yaml")),
            'k8s': generate_kubernetes_config(mock_results, os.path.join(self.temp_dir.name, "k8s.yaml")),
            'openshift': generate_openshift_config(mock_results, os.path.join(self.temp_dir.name, "openshift.yaml"))
        }
        
        # Create test cases for each configuration
        for platform, config in configs.items():
            test_case = LLMTestCase(
                input=str(mock_results),
                actual_output=str(config),
                expected_output=f"Configuration for {platform} should match input requirements",
                retrieval_context=[f"Configuration for {platform} should match memory and CPU requirements"]
            )
            test_cases.append(test_case)
        
        # Create dataset and evaluate
        dataset = EvaluationDataset(test_cases=test_cases)
        results = evaluate(dataset, [self.answer_relevancy, self.hallucination])
        
        # Assert overall evaluation results
        self.assertGreaterEqual(results['answer_relevancy'], 0.7)
        self.assertLessEqual(results['hallucination'], 0.3)


if __name__ == "__main__":
    unittest.main() 