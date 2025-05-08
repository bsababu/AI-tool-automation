import yaml

def generate_kubernetes_config(results, output_path):
    """Generate Kubernetes Deployment YAML"""
    profile = results["profile"]
    repo_name = results["repository_url"].split('/')[-1].replace('.git', '')
    
    memory = profile["recommendations"]["memory"]["recommended_allocation"].replace("MB", "Mi")
    cpu_cores = str(profile["recommendations"]["cpu"]["recommended_cores"])
    bandwidth = profile["recommendations"]["bandwidth"]["peak_requirement"]
    
    config = {
        "apiVersion": "apps/v1",
        "kind": "Deployment",
        "metadata": {
            "name": f"{repo_name}-deployment",
            "labels": {"app": repo_name},
        },
        "spec": {
            "replicas": 1,
            "selector": {"matchLabels": {"app": repo_name}},
            "template": {
                "metadata": {"labels": {"app": repo_name}},
                "spec": {
                    "containers": [
                        {
                            "name": repo_name,
                            "image": "python:3.9-slim",
                            "resources": {
                                "limits": {"memory": memory, "cpu": cpu_cores},
                                "requests": {"memory": memory, "cpu": cpu_cores},
                            },
                            "env": [
                                {"name": "NETWORK_BANDWIDTH", "value": f"Network bandwidth: {bandwidth}"}
                            ],
                        }
                    ]
                },
            },
        },
    }
    
    with open(output_path, "w", encoding="utf-8") as f:
        yaml.safe_dump(config, f, default_flow_style=False)
    print(f"Kubernetes config written to {output_path}")


def generate_aws_config(results, output_path):
    """Generate AWS CloudFormation config"""
    pass

def generate_terraform_config(results, output_path):
    """Generate Terraform CloudFormation config """
    pass