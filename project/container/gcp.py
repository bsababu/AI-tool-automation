import os
import yaml


def generate_gcp_cloudrun_config(results, output_path):
    """Generate Google Cloud Run configuration"""
    profile = results["profile"]
    repo_name = results["repository_url"].split('/')[-1].replace('.git', '')
    
    memory = profile["recommendations"]["memory"]["recommended_allocation"]
    cpu_cores = profile["recommendations"]["cpu"]["recommended_cores"]
    
    config = {
        "apiVersion": "serving.knative.dev/v1",
        "kind": "Service",
        "metadata": {
            "name": repo_name
        },
        "spec": {
            "template": {
                "metadata": {
                    "annotations": {
                        "autoscaling.knative.dev/maxScale": "100"
                    }
                },
                "spec": {
                    "containerConcurrency": 80,
                    "containers": [{
                        "image": f"gcr.io/project/{repo_name}",
                        "resources": {
                            "limits": {
                                "cpu": str(cpu_cores),
                                "memory": memory
                            }
                        }
                    }]
                }
            }
        }
    }
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w") as f:
        yaml.safe_dump(config, f, default_flow_style=False)
    return output_path