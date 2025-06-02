import os
import yaml

def generate_openshift_config(results, output_path):
    """Generate OpenShift configuration"""
    profile = results["profile"]
    repo_name = results["repository_url"].split('/')[-1].replace('.git', '')
    
    memory = profile["recommendations"]["memory"]["recommended_allocation"]
    cpu_cores = str(profile["recommendations"]["cpu"]["recommended_cores"])
    
    config = f"""
            {{
                "apiVersion": "apps.openshift.io/v1",
                "kind": "DeploymentConfig",
                "metadata": {{
                    "name": "{repo_name}"
                }},
                "spec": {{
                    "replicas": 1,
                    "template": {{
                        "metadata": {{
                            "labels": {{
                                "app": "{repo_name}"
                            }}
                        }},
                        "spec": {{
                            "containers": [{{
                                "name": "{repo_name}",
                                "image": "python:3.9-slim",
                                "resources": {{
                                    "limits": {{
                                        "cpu": "{cpu_cores}",
                                        "memory": "{memory}"
                                    }},
                                    "requests": {{
                                        "cpu": "{cpu_cores}",
                                        "memory": "{memory}"
                                    }}
                                }}
                            }}]
                        }}
                    }}
                }}
            }}
        """

    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(config)
    return output_path