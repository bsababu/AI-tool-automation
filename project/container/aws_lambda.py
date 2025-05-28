import os
import yaml

def generate_aws_lambda_config(results, output_path):
    """Generate AWS Lambda configuration"""
    profile = results["profile"]
    repo_name = results["repository_url"].split('/')[-1].replace('.git', '')
    
    memory = int(profile["recommendations"]["memory"]["recommended_allocation"].replace("MB", ""))
    # Lambda memory must be a multiple of 64MB between 128MB and 10240MB
    memory = max(128, min(10240, ((memory + 63) // 64) * 64))
    
    config = {
        "AWSTemplateFormatVersion": "2010-09-09",
        "Resources": {
            "LambdaFunction": {
                "Type": "AWS::Lambda::Function",
                "Properties": {
                    "FunctionName": f"{repo_name}-function",
                    "Runtime": "python3.9",
                    "Handler": "index.handler",
                    "MemorySize": memory,
                    "Timeout": 900,
                    "Environment": {
                        "Variables": {
                            "MEMORY_REQUIREMENT": str(memory),
                            "CPU_CORES": str(profile["recommendations"]["cpu"]["recommended_cores"])
                        }
                    }
                }
            }
        }
    }
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w") as f:
        yaml.safe_dump(config, f, default_flow_style=False)
    return output_path