import os

def generate_terraform_config(results, output_path):
    """Generate Terraform configuration for an AWS EC2 instance"""
    profile = results["profile"]
    repo_name = results["repository_url"].split('/')[-1].replace('.git', '')
    
    memory_mb = float(profile["recommendations"]["memory"]["recommended_allocation"].replace("MB", ""))
    cpu_cores = int(profile["recommendations"]["cpu"]["recommended_cores"])
    bandwidth = profile["recommendations"]["bandwidth"]["peak_requirement"]
    
    # Map memory and CPU to AWS instance types (simplified)
    instance_type = "t2.micro"  # Default
    if memory_mb >= 2000 or cpu_cores >= 4:
        instance_type = "t2.large"
    elif memory_mb >= 1000 or cpu_cores >= 2:
        instance_type = "t2.medium"
    
    config = f"""
        provider "aws" {{
        region = "us-east-1"
        }}

        resource "aws_instance" "{repo_name}_instance" {{
        ami           = "ami-0c55b159cbfafe1f0"  # Amazon Linux 2 AMI (update as needed)
        instance_type = "{instance_type}"
        
        tags = {{
            Name = "{repo_name}-instance"
            Bandwidth = "{bandwidth}"
        }}
        }}
        """
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(config)
    return output_path