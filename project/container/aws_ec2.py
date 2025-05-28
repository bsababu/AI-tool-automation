import os
import yaml

def generate_aws_ecs_config(results, output_path):
    """Generate AWS ECS configuration"""
    profile = results["profile"]
    repo_name = results["repository_url"].split('/')[-1].replace('.git', '')
    
    memory = int(profile["recommendations"]["memory"]["recommended_allocation"].replace("MB", ""))
    cpu_cores = int(profile["recommendations"]["cpu"]["recommended_cores"])
    
    config = {
        "AWSTemplateFormatVersion": "2010-09-09",
        "Resources": {
            "ECSCluster": {
                "Type": "AWS::ECS::Cluster",
                "Properties": {
                    "CapacityProviders": ["FARGATE"],
                    "ClusterName": f"{repo_name}-cluster"
                }
            },
            "TaskDefinition": {
                "Type": "AWS::ECS::TaskDefinition",
                "Properties": {
                    "Family": f"{repo_name}-task",
                    "RequiresCompatibilities": ["FARGATE"],
                    "NetworkMode": "awsvpc",
                    "Cpu": str(cpu_cores * 1024),  # Convert to AWS CPU units
                    "Memory": str(memory),
                    "ContainerDefinitions": [{
                        "Name": repo_name,
                        "Image": "python:3.9-slim",
                        "Memory": memory,
                        "Cpu": cpu_cores * 1024
                    }]
                }
            }
        }
    }
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w") as f:
        yaml.safe_dump(config, f, default_flow_style=False)
    return output_path