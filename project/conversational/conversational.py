import datetime
import os
from dotenv import load_dotenv
from crewai import Agent, Process, Task, Crew
from langchain.tools import BaseTool
from crewai.tools import BaseTool
from RL.db_feedback import get_change_logs, get_latest_analysis, summarize_analysis
from container.kubernates import generate_kubernetes_config, generate_terraform_config
from conversational.run_convo import analyzer_main




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
        
        results_dir = "./Results/"
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
        
        results_dir = "./Results/"
        os.makedirs(results_dir, exist_ok=True)
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        config_path = os.path.join(results_dir, f"config_terraform_{timestamp}.tf")
        
        results = {
            "repository_url": repo_url,
            "profile": result["profile"],
        }
        config_path = generate_terraform_config(results, config_path)
        return f"Terraform configuration generated at {config_path}."

class SummarizeAnalysisTool(BaseTool):
    name: str = "Summarize Analysis"
    description: str = "Summarizes the latest analysis results for a given repository URL."

    def _run(self, repo_url: str) -> str:
        return summarize_analysis(repo_url)

# CrewAI Agent Setup

def create_analysis_agent():

    return Agent(
        role="Analyser",
        goal="Assist users by answering queries about repository analysis results and generating cloud configurations.",
        backstory=(
            "You are a DevOps assistant specialized in analyzing software repositories to estimate resource requirements "
            "and generate cloud configurations. You can query a database to retrieve analysis results, explain changes, "
            "and generate Kubernetes or Terraform configurations on demand."
        ),
        verbose=True,
        allow_delegation=False,
        tools=[
            GetLatestAnalysisTool(),
            GetChangeLogsTool(),
            GenerateKubernetesConfigTool(),
            GenerateTerraformConfigTool(),
            SummarizeAnalysisTool(),
        ],
    )


def run_conversational_agent():
    load_dotenv("../.env")
    github_token = os.getenv("GITHUB_TOKEN")
    llm_api_key = os.getenv("OPENAI_API_KEY")
    if not llm_api_key:
        print("Error: LLM errors failing")
        return
    repo_url = input("Enter the GitHub repository .git URL: ").strip()
    if not repo_url:
        print("Error: No URL provided.")
        return
    
    print("Analyzing repository...")
    result = analyzer_main(repo_url, github_token, llm_api_key)
    if "error" in result:
        print(f"Error: {result['error']}")
        return
    
    estimated = result["estimated"]
    print(f"\nFull JSON written to {estimated['json_path']}")
    print(f"Kubernetes config written to {estimated['config_path']}")
    print("\nComparison with previous analysis:", estimated["comparison"]["message"])
    if estimated["comparison"]["changes"]:
        print("Changes detected:")
        for change in estimated["comparison"]["changes"]:
            print(f"- {change}")
    print("\nAnalysis Summary:")
    print(summarize_analysis(repo_url))
    
    
    agent = create_analysis_agent()
    print("\nConversational AI Agent started. Type your query or 'exit' to quit.")
    print("Example queries you can refer on:")
    print(f"- Show memory requirements for repository")
    print(f"- Why did CPU usage change for repository: '{repo_url}?")
    print(f"- Generate Kubernetes config for repository: '{repo_url}")
    print(f"- Generate Terraform config for repository: '{repo_url}")
    
    while True:
        try:
            user_input = input("\nEnter your query: ").strip()
            if user_input.lower() == "exit":
                print("Exiting Conversational AI Agent.")
                break
            
            # Create a dynamic task based on user input
            task = Task(
                description=(
                    f"Answer the user's query: '{user_input}' for repository: '{repo_url}'. "
                    "Use the available tools to retrieve analysis results, change logs, or generate Kubernetes or Terraform configurations. "
                    "Provide a clear, short and concise response in natural language."
                ),
                agent=agent,
                expected_output="A specific natural language response answering the user's query",
            )
            
            # Execute the task
            crew = Crew(
                agents=[agent], 
                tasks=[task], 
                process=Process.sequential,
                verbose=True)
            result = crew.kickoff()
            print("\nResponse:", result)
            
        except KeyboardInterrupt:
            print("\nExiting Conversational AI Agent.")
            break
        except Exception as e:
            print(f"Error processing query: {str(e)}")


# if __name__ == "__main__":
#     run_conversational_agent()