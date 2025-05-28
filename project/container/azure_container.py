import os
import json

def generate_azure_container_config(results, output_path):
    """Generate Azure Container Instances configuration"""
    profile = results["profile"]
    repo_name = results["repository_url"].split('/')[-1].replace('.git', '')
    
    memory = float(profile["recommendations"]["memory"]["recommended_allocation"].replace("MB", "")) / 1024  # Convert to GB
    cpu_cores = profile["recommendations"]["cpu"]["recommended_cores"]
    
    config = {
        "apiVersion": "2021-07-01",
        "location": "eastus",  # Default location
        "name": f"{repo_name}-container",
        "properties": {
            "containers": [{
                "name": repo_name,
                "properties": {
                    "image": "python:3.9-slim",
                    "resources": {
                        "requests": {
                            "cpu": cpu_cores,
                            "memoryInGB": memory
                        }
                    },
                    "ports": [{"port": 80}]
                }
            }],
            "osType": "Linux",
            "restartPolicy": "Always"
        }
    }
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(config, f, indent=2)
    return output_path
