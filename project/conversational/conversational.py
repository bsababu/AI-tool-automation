import datetime
import os
from pathlib import Path
from dotenv import load_dotenv
from crewai import Agent, Process, Task, Crew
from langchain.tools import BaseTool
from crewai.tools import BaseTool
from project.RL.db_feedback import get_change_logs, get_cloud_config_feedback, get_latest_analysis, init_database, summarize_analysis, store_cloud_config_feedback
from project.container.kubernates import generate_kubernetes_config
from project.container.terraform import generate_terraform_config
# from project.conversational.evaluation import evaluate_response
from project.conversational.run_convo import analyzer_main
from project.container.cloud_configs import (generate_all_cloud_configs, generate_aws_ecs_config, generate_aws_lambda_config, generate_gcp_cloudrun_config, generate_azure_container_config, generate_openshift_config)


class GetLatestAnalysisTool(BaseTool):
    name: str = "Get Latest Analysis"
    description: str = "Retrieves the latest analysis results for a given repository URL from the database."

    def _run(self, repo_url: str) -> str:
        analysis = get_latest_analysis(repo_url)
        return summarize_analysis(repo_url)

class GetChangeLogsTool(BaseTool):
    name: str = "Get Change Logs"
    description: str = "Retrieves change logs for a given repository URL from the database."

    def _run(self, repo_url: str) -> str:
        logs = get_change_logs(repo_url)
        if logs:
            output = f"Change logs for {repo_url}:\n"
            for log in logs:
                output += f"- {log['timestamp']}:\n"
                for change in log["changes"]:
                    output += f"  - {change}\n"
            return output
        return f"No change logs found for {repo_url}."

class GenerateKubernetesConfigTool(BaseTool):
    name: str = "Generate Kubernetes Config"
    description: str = "Generates a Kubernetes configuration file for a given repository URL based on the latest analysis."

    def _run(self, repo_url: str) -> str:
        result = get_latest_analysis(repo_url)
        if not result:
            return f"No analysis found for {repo_url}, cannot generate config."
        
        results_dir = "./Results/kubernetes/"
        if not os.path.exists(results_dir):
            os.makedirs(results_dir, exist_ok=True)
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        config_path = os.path.join(results_dir, f"config_kubernetes_{timestamp}.yaml")
        
        results = {
            "repository_url": repo_url,
            "profile": result["profile"],
        }
        config_path = generate_kubernetes_config(results, config_path)
        return f"Kubernetes configuration generated at {config_path}."

class GenerateTerraformConfigTool(BaseTool):
    name: str = "Generate Terraform Config"
    description: str = "Generates a Terraform configuration file for a given repository URL based on the latest analysis."

    def _run(self, repo_url: str) -> str:
        result = get_latest_analysis(repo_url)
        if not result:
            return f"No analysis found for {repo_url}, cannot generate config."
        
        results_dir = "./Results/terraform/"
        if not os.path.exists(results_dir):
            os.makedirs(results_dir, exist_ok=True)
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        config_path = os.path.join(results_dir, f"config_terraform_{timestamp}.tf")
        
        results = {
            "repository_url": repo_url,
            "profile": result["profile"],
        }
        config_path = generate_terraform_config(results, config_path)
        return f"Terraform configuration generated at {config_path}."

class GenerateAllCloudConfigsTool(BaseTool):
    name: str = "Generate All Cloud Configs"
    description: str = "Generates configurations for all supported cloud platforms (AWS ECS, AWS Lambda, GCP Cloud Run, Azure Container, OpenShift)."

    def _run(self, repo_url: str) -> str:
        result = get_latest_analysis(repo_url)
        if not result:
            return f"No analysis found for {repo_url}, cannot generate configs."
        
        results_dir = "./Results/AllConfigs/"
        if not os.path.exists(results_dir):
            os.makedirs(results_dir, exist_ok=True)
        
        results = {
            "repository_url": repo_url,
            "profile": result["profile"],
        }
        
        configs = generate_all_cloud_configs(results, results_dir)
        
        output = "Generated cloud configurations:\n"
        for platform, path in configs.items():
            output += f"- {platform}: {path}\n"
        return output

class GenerateAWSECSConfigTool(BaseTool):
    name: str = "Generate AWS ECS Config"
    description: str = "Generates an AWS ECS (Elastic Container Service) configuration file."

    def _run(self, repo_url: str) -> str:
        result = get_latest_analysis(repo_url)
        if not result:
            return f"No analysis found for {repo_url}, cannot generate config."
        
        results_dir = "./Results/ECS"
        if not os.path.exists(results_dir):
            os.makedirs(results_dir, exist_ok=True)
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        config_path = os.path.join(results_dir, f"config_aws_ecs_{timestamp}.yaml")
        
        results = {
            "repository_url": repo_url,
            "profile": result["profile"],
        }
        configs = generate_aws_ecs_config(results, config_path)
        return f"AWS ECS configuration generated at {configs}."

class GenerateAWSLambdaConfigTool(BaseTool):
    name: str = "Generate AWS Lambda Config"
    description: str = "Generates an AWS Lambda configuration file."

    def _run(self, repo_url: str) -> str:
        result = get_latest_analysis(repo_url)
        if not result:
            return f"No analysis found for {repo_url}, cannot generate config."
        
        results_dir = "./Results/aws_lambda/"
        if not os.path.exists(results_dir):
            os.makedirs(results_dir, exist_ok=True)
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        config_path = os.path.join(results_dir, f"config_aws_lambda_{timestamp}.yaml")
        results = {
            "repository_url": repo_url,
            "profile": result["profile"],
        }
        configs = generate_aws_lambda_config(results, config_path)
        return f"AWS Lambda configuration generated at {configs}."

class GenerateGCPCloudRunConfigTool(BaseTool):
    name: str = "Generate GCP Cloud Run Config"
    description: str = "Generates a Google Cloud Run configuration file."

    def _run(self, repo_url: str) -> str:
        result = get_latest_analysis(repo_url)
        if not result:
            return f"No analysis found for {repo_url}, cannot generate config."
        
        results_dir = "./Results/gcp/"
        if not os.path.exists(results_dir):
            os.makedirs(results_dir, exist_ok=True)
        
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        config_path = os.path.join(results_dir, f"config_GPC_{timestamp}.yaml")
        
        results = {
            "repository_url": repo_url,
            "profile": result["profile"],
        }
        configs = generate_gcp_cloudrun_config(results, config_path)
        return f"google cloud configuration generated at {configs}."

class GenerateAzureContainerConfigTool(BaseTool):
    name: str = "Generate Azure Container Config"
    description: str = "Generates an Azure Container Instances configuration file."

    def _run(self, repo_url: str) -> str:
        result = get_latest_analysis(repo_url)
        if not result:
            return f"No analysis found for {repo_url}, cannot generate config."
        
        results_dir = "./Results/azure/"
        if not os.path.exists(results_dir):
            os.makedirs(results_dir, exist_ok=True)

        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        config_path = os.path.join(results_dir, f"config_azure_{timestamp}.yaml")
        
        results = {
            "repository_url": repo_url,
            "profile": result["profile"],
        }
        config_path = generate_azure_container_config(results, config_path)
        return f"Azure configuration generated at {config_path}."

class GenerateOpenShiftConfigTool(BaseTool):
    name: str = "Generate OpenShift Config"
    description: str = "Generates an OpenShift configuration file."

    def _run(self, repo_url: str) -> str:
        result = get_latest_analysis(repo_url)
        if not result:
            return f"No analysis found for {repo_url}, cannot generate config."
        
        results_dir = "./Results/openshift/"
        if not os.path.exists(results_dir):
            os.makedirs(results_dir, exist_ok=True)
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        config_path = os.path.join(results_dir, f"config_openshift_{timestamp}.yaml")
        
        results = {
            "repository_url": repo_url,
            "profile": result["profile"],
        }
        configs = generate_openshift_config(results, config_path)
        return f"Azure configuration generated at {configs}."

class CloudConfigFeedbackTool(BaseTool):
    name: str = "Cloud Config Feedback"
    description: str = "Store and retrieve feedback about generated cloud configurations."

    def _run(self, query: str) -> str:
        parts = query.split()
        if len(parts) < 3:
            return "Invalid query format. Use: [store/get] [repo_url] [platform] [score] [notes]"
        
        action = parts[0].lower()
        repo_url = parts[1]
        platform = parts[2]
        
        if action == "store":
            if len(parts) < 4:
                return "Missing score for feedback"
            try:
                score = int(parts[3])
                notes = " ".join(parts[4:]) if len(parts) > 4 else ""
                conn = init_database()
                store_cloud_config_feedback(conn, repo_url, platform, "", score, notes)
                conn.close()
                return f"Stored feedback for {platform} configuration"
            except ValueError:
                return "Score must be a number"
        elif action == "get":
            feedback = get_cloud_config_feedback(repo_url, platform if platform != "all" else None)
            if not feedback:
                return f"No feedback found for {repo_url}"
            output = f"Feedback for {repo_url}:\n"
            for fb in feedback:
                output += f"- {fb['platform']} ({fb['timestamp']}): Score {fb['feedback_score']}"
                if fb['feedback_notes']:
                    output += f" - {fb['feedback_notes']}"
                output += "\n"
            return output
        else:
            return "Invalid action. Use 'store' or 'get'"

class SummarizeAnalysisTool(BaseTool):
    name: str = "Summarize Analysis"
    description: str = "Summarizes the latest analysis results for a given repository URL."

    def _run(self, repo_url: str) -> str:
        return summarize_analysis(repo_url)

def create_analysis_agent(model: str):
    """Create an analysis agent with detailed, verbose responses."""
    return Agent(
        role="Resource Analyzer",
        goal="Provide the resource analysis and cloud configuration recommendations with clear short explanations",
        backstory=(
            "Expert in analyzing repository resource requirements and cloud configurations. "
            "I provide thorough explanations and detailed insights about resource usage patterns, "
            "scaling considerations, and cloud deployment options."
        ),
        verbose=True, 
        allow_delegation=False,
        llm=model,
        tools=[
            GetLatestAnalysisTool(),
            GetChangeLogsTool(),
            GenerateKubernetesConfigTool(),
            GenerateAllCloudConfigsTool(),
            GenerateAWSECSConfigTool(),
            GenerateAWSLambdaConfigTool(),
            GenerateGCPCloudRunConfigTool(),
            GenerateAzureContainerConfigTool(),
            GenerateOpenShiftConfigTool(),
            CloudConfigFeedbackTool(),
            GenerateTerraformConfigTool(),
            SummarizeAnalysisTool(),
        ],
    )



def run_conversational_agent():
    
    load_dotenv("../../.env")
    github_token = os.getenv("GITHUB_TOKEN")
    llm_api_key = os.getenv("OPENAI_API_KEY")
    model = os.getenv("OPEN_MODEL")
    
    if not all([github_token, llm_api_key, model]):
        missing = []
        if not github_token: missing.append("GITHUB_TOKEN")
        if not llm_api_key: missing.append("OPENAI_API_KEY")
        if not model: missing.append("OPEN_MODEL")
        print(f"Error: Missing required environment variables: {', '.join(missing)}")
        return

    
    conversation_state = {
        "repo_url": None,
        "last_analysis": None,
        "agent": None,
        "crew": None
    }
    
    def analyze_repository():
        """Analyze the repository and update conversation state."""
        repo_url = input("Enter the GitHub repository .git URL: ").strip()
        if not repo_url:
            print("Error: No URL provided.")
            return False
            
        print("\nAnalyzing repository...")
        try:
            result = analyzer_main(repo_url, github_token, llm_api_key)
            if "error" in result:
                print(f"Error: {result['error']}")
                return False
                
            conversation_state["repo_url"] = repo_url
            conversation_state["last_analysis"] = result
            
            estimated = result["estimated"]
            print(f"\nResources Analysis:")
            print(f"Memory: {estimated['estimated_Memory']}")
            print(f"CPU Cores: {estimated['estimated_CPU_cores']}")
            print(f"Network: {estimated['estimated_network_bandwidth']}")
            
            if estimated["comparison"]["changes"]:
                print("\nChanges from previous analysis:")
                for change in estimated["comparison"]["changes"]:
                    print(f"- {change}")
            return True
            
        except Exception as e:
            print(f"Error analyzing repository: {str(e)}")
            return False
    
    def setup_agent():
        try:
            agent = create_analysis_agent(model)
            conversation_state["agent"] = agent
            
            print("\nAvailable commands:")
            print("- 'analyze': Analyze a new repository")
            print("- 'help': Show commands")
            print("- 'exit': Exit")
            
            print("\nExample queries:")
            print("- Show memory requirements for repository")
            print("- Why did CPU usage change?")
            print("- Generate all cloud configurations")
            print("- Generate AWS ECS config")
           
            return True
            
        except Exception as e:
            print(f"Error setting up agent: {str(e)}")
            return False
    
    def process_query(user_input: str):
        """Process a user query with focused responses and evaluate the quality."""
        if not conversation_state["repo_url"]:
            print("Please analyze a repository first using the 'analyze' command.")
            return

        try:
            task = Task(
                description=(
                    f"Query: '{user_input}'\n"
                    f"Repository: '{conversation_state['repo_url']}'\n"
                    "Provide a concise response focusing only on the requested information. "
                    "If discussing resource changes, briefly explain the scaling reason."
                ),
                agent=conversation_state["agent"],
                verbose=True,
                expected_output="Concise technical response with specific data points.",
            )
            
            crew = Crew(
                agents=[conversation_state["agent"]], 
                tasks=[task], 
                process=Process.sequential,
                verbose=True
            )
            conversation_state["crew"] = crew
            
            result = crew.kickoff()
            response = str(result.raw)
            print("\n" + response)
            
            # Evaluation with Deep
            # if conversation_state["last_analysis"]:
            #     evaluation_results = evaluate_response(
            #         user_input, 
            #         response, 
            #         conversation_state["last_analysis"]
            #     )
            #     print("\n--- Response Quality Evaluation ---")
            #     print(f"Overall Score: {evaluation_results.get('overall_score', 'N/A'):.2f}/1.0")
                
                
            #     if os.getenv("SHOW_DETAILED_EVALUATION", "false").lower() == "true":
            #         for metric_name, metric_result in evaluation_results.items():
            #             if metric_name != "overall_score":
            #                 print(f"{metric_name}: {metric_result['score']:.2f} - {'✓' if metric_result['passed'] else '✗'}")
            
        except Exception as e:
            print(f"Error processing query: {str(e)}")
    
    # Main conversation loop
    if not analyze_repository() or not setup_agent():
        return
        
    while True:
        try:
            user_input = input("\nQuery: ").strip().lower()
            
            if user_input == "exit":
                print("Exiting.")
                break
            elif user_input == "analyze":
                if not analyze_repository() or not setup_agent():
                    continue
            elif user_input == "help":
                setup_agent()
            else:
                process_query(user_input)
                
        except KeyboardInterrupt:
            print("\nExiting.")
            break
        except Exception as e:
            print(f"Error: {str(e)}")
            print("Type 'help' for commands or 'exit' to quit.")
