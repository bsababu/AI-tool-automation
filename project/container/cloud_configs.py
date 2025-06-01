import datetime


from project.container.kubernates import generate_kubernetes_config
from project.container.aws_ec2 import generate_aws_ecs_config
from project.container.aws_lambda import generate_aws_lambda_config
from project.container.gcp import generate_gcp_cloudrun_config
from project.container.azure_container import generate_azure_container_config
from project.container.openshift import generate_openshift_config


def generate_all_cloud_configs(results, base_output_dir="./Results"):
    """Generate configurations for all supported cloud platforms"""
    repo_name = results["repository_url"].split('/')[-1].replace('.git', '')
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    
    configs = {
        "kubernetes": f"{base_output_dir}/kubernetes_{timestamp}.yaml",
        "aws_ecs": f"{base_output_dir}/aws_ecs_{timestamp}.yaml",
        "aws_lambda": f"{base_output_dir}/aws_lambda_{timestamp}.yaml",
        "gcp_cloudrun": f"{base_output_dir}/gcp_cloudrun_{timestamp}.yaml",
        "azure_container": f"{base_output_dir}/azure_container_{timestamp}.yaml",
        "openshift": f"{base_output_dir}/openshift_{timestamp}.yaml",
        "terraform": f"{base_output_dir}/terraform_{timestamp}.tf"
    }
    
    # Generate all configurations
    generated_configs = {
        "kubernetes": generate_kubernetes_config(results, configs["kubernetes"]),
        "aws_ecs": generate_aws_ecs_config(results, configs["aws_ecs"]),
        "aws_lambda": generate_aws_lambda_config(results, configs["aws_lambda"]),
        "gcp_cloudrun": generate_gcp_cloudrun_config(results, configs["gcp_cloudrun"]),
        "azure_container": generate_azure_container_config(results, configs["azure_container"]),
        "openshift": generate_openshift_config(results, configs["openshift"])
    }
    
    return generated_configs