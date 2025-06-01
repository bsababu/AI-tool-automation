import os
import tempfile
import yaml
import unittest

from project.container.aws_lambda import generate_aws_lambda_config
from project.container.aws_ec2 import generate_aws_ecs_config
from project.container.azure_container import generate_azure_container_config
from project.container.gcp import generate_gcp_cloudrun_config
from project.container.kubernates import generate_kubernetes_config
from project.container.openshift import generate_openshift_config
from project.container.terraform import generate_terraform_config


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


class TestCloudConfigs(unittest.TestCase):

    def test_generate_aws_lambda_config(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "lambda.yaml")
            result = generate_aws_lambda_config(mock_results, path)

            with open(path) as f:
                config = yaml.safe_load(f)

            props = config["Resources"]["LambdaFunction"]["Properties"]
            self.assertEqual(result["aws_lambda"], config)
            self.assertEqual(props["FunctionName"], "project-function")
            self.assertEqual(props["MemorySize"], 2048)
            self.assertEqual(props["Environment"]["Variables"]["MEMORY_REQUIREMENT"], "2048")
            self.assertEqual(props["Environment"]["Variables"]["CPU_CORES"], "2")

    def test_generate_aws_ecs_config(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "ecs.yaml")
            result = generate_aws_ecs_config(mock_results, path)

            with open(path) as f:
                config = yaml.safe_load(f)

            td_props = config["Resources"]["TaskDefinition"]["Properties"]
            self.assertEqual(result["aws_ecs"], config)
            self.assertEqual(td_props["Memory"], "2048")
            self.assertEqual(td_props["Cpu"], "2048")
            self.assertEqual(td_props["ContainerDefinitions"][0]["Memory"], 2048)
            self.assertEqual(td_props["ContainerDefinitions"][0]["Cpu"], 2048)

    def test_generate_azure_container_config(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "azure.yaml")
            result = generate_azure_container_config(mock_results, path)

            with open(path) as f:
                config = yaml.safe_load(f)

            container = config["properties"]["containers"][0]
            self.assertEqual(result["azure"], config)
            self.assertEqual(container["name"], "project")
            self.assertEqual(container["properties"]["resources"]["requests"]["cpu"], 2)
            self.assertEqual(container["properties"]["resources"]["requests"]["memoryInGB"], 2.0)


    def test_generate_gcp_cloudrun_config(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "gcp.yaml")
            result = generate_gcp_cloudrun_config(mock_results, path)

            with open(path) as f:
                config = yaml.safe_load(f)

            limits = config["spec"]["template"]["spec"]["containers"][0]["resources"]["limits"]
            self.assertEqual(result["gcp"], config)
            self.assertEqual(limits["cpu"], "2")
            self.assertEqual(limits["memory"], "2048MB")

    def test_generate_kubernetes_config(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "k8s.yaml")
            result = generate_kubernetes_config(mock_results, path)

            with open(path) as f:
                config = yaml.safe_load(f)

            container = config["spec"]["template"]["spec"]["containers"][0]
            self.assertEqual(result["kubernetes"], config)
            self.assertEqual(container["resources"]["limits"]["memory"], "2048Mi")
            self.assertEqual(container["resources"]["limits"]["cpu"], "2")
            self.assertEqual(container["env"][0]["value"], "Network bandwidth: 500Mbps")

    def test_generate_openshift_config(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "openshift.yaml")
            result = generate_openshift_config(mock_results, path)

            with open(path) as f:
                config = yaml.safe_load(f)

            container = config["spec"]["template"]["spec"]["containers"][0]
            self.assertEqual(result["openshift"], config)
            self.assertEqual(container["resources"]["limits"]["memory"], "2048MB")
            self.assertEqual(container["resources"]["limits"]["cpu"], "2")

    def test_generate_terraform_config(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "terraform.tf")
            result_path = generate_terraform_config(mock_results, path)

            self.assertEqual(result_path, path)
            with open(path) as f:
                content = f.read()
                self.assertIn("t2.large", content)
                self.assertIn("project-instance", content)
                self.assertIn('Bandwidth = "500Mbps"', content)


    def test_tearDown(self):
        return super().tearDown()


if __name__ == "__main__":
    unittest.main()
