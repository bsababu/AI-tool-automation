import yaml
import os

def generate_kubernetes_config(results, output_path):
    """Generate Kubernetes Deployment YAML"""
    profile = results["profile"]
    repo_name = results["repository_url"].split('/')[-1].replace('.git', '')
    
    memory = profile["recommendations"]["memory"]["recommended_allocation"].replace("MB", "Mi")
    cpu_cores = str(profile["recommendations"]["cpu"]["recommended_cores"])
    bandwidth = profile["recommendations"]["bandwidth"]["peak_requirement"]
    
    config = f"""
                {{
                    "apiVersion": "apps/v1",
                    "kind": "Deployment",
                    "metadata": {{
                        "name": "{repo_name}-deployment",
                        "labels": {{"app": "{repo_name}"}},
                    }},
                    "spec": {{
                        "replicas": 1,
                        "selector": {{"matchLabels": {{"app": "{repo_name}"}}}},
                        "template": {{
                            "metadata": {{"labels": {{"app": "{repo_name}"}}}},
                            "spec": {{
                                "containers": [
                                    {{
                                        "name": "{repo_name}",
                                        "image": "python:3.9-slim",
                                        "resources": {{
                                            "limits": {{"memory": "{memory}", "cpu": "{cpu_cores}"}},
                                            "requests": {{"memory": "{memory}", "cpu": "{cpu_cores}"}},
                                        }},
                                        "env": [
                                            {{"name": "NETWORK_BANDWIDTH", "value": "Network bandwidth: {bandwidth}"}}
                                        ],
                                    }}
                                ]
                            }},
                        }},
                    }},
                }}
                """

    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(config)
    return output_path