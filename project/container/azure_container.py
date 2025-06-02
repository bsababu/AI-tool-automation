import os
import yaml

def generate_azure_container_config(results, output_path):
    """Generate Azure Container Instances configuration"""
    profile = results["profile"]
    repo_name = results["repository_url"].split('/')[-1].replace('.git', '')
    
    memory = float(profile["recommendations"]["memory"]["recommended_allocation"].replace("MB", "")) / 1024  # Convert to GB
    cpu_cores = profile["recommendations"]["cpu"]["recommended_cores"]
    
    config = f"""
{{
    "apiVersion": "2021-07-01",
    "location": "eastus",
    "name": "{repo_name}-container",
    "properties": {{
        "containers": [{{
            "name": "{repo_name}",
            "properties": {{
                "image": "python:3.9-slim",
                "resources": {{
                    "requests": {{
                        "cpu": {cpu_cores},
                        "memoryInGB": {memory}
                    }}
                }},
                "ports": [{{"port": 80}}]
            }}
        }}],
        "osType": "Linux",
        "restartPolicy": "Always"
    }}
}}
"""

    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        # yaml.safe_dump(config, f, default_flow_style=False)
        f.write(config)
    return output_path
