import json
import os
import datetime
import git
from dotenv import load_dotenv


from project.RL.db_feedback import compare_and_log_changes, init_database, store_analysis
from project.container.kubernates import generate_kubernetes_config
from project.githubRepo.fetch_repo import RepoFetcher
from project.githubRepo.resource_analyzer import ResourceAnalyzer
from project.githubRepo.resource_profiler import ResourceProfiler

class GithubResourceAnalyzer:
    def __init__(self, github_token=None, llm_api_key=None):
        self.repo_fetcher = RepoFetcher(github_token)
        self.resource_analyzer = ResourceAnalyzer(llm_api_key)
        self.profiler = ResourceProfiler(self.resource_analyzer)

    def analyze_repository(self, repo_url):
        repo_path = self.repo_fetcher.fetch_repo(repo_url)
        repo_structure = self.repo_fetcher.get_repo_structure(repo_path)
        resource_profile = self.profiler.profile_repository(repo_path, repo_structure)
        repo = git.Repo(repo_path)
        commit_hash = repo.head.commit.hexsha
        return {
            "repository_url": repo_url,
            "structure": repo_structure,
            "profile": resource_profile,
            "commit_hash": commit_hash,
        }

def analyzer_main():
    load_dotenv(".env")
    repo_url = input("Enter the GitHub repository .git URL: ").strip()
    if not repo_url.endswith(".git"):
        print("Invalid URL. Please enter a valid GitHub .git URL.")
        return
    
    github_token = os.getenv("GITHUB_TOKEN")
    llm_api_key = os.getenv("OPENAI_API_KEY")
    conn = init_database()
    
    try:
        analyzer = GithubResourceAnalyzer(github_token=github_token, llm_api_key=llm_api_key)
        results = analyzer.analyze_repository(repo_url)
        
        results_json = "./Results/JSON/"
        os.makedirs(results_json, exist_ok=True)
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        json_path = os.path.join(results_json, f"analyzed{timestamp}.json")
        
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2)
        print(f"Full JSON report saved....")
        
        store_analysis(conn, results)
        comparison = compare_and_log_changes(conn, results)
        print("\nComparison with previous analysis:", comparison["message"])
        if comparison["changes"]:
            print("Changes detected:")
            for change in comparison["changes"]:
                print(f"- {change}")
        
        results_yaml = "./Results/YAML/"
        os.makedirs(results_yaml, exist_ok=True)
        config_path = os.path.join(results_yaml, f"config{timestamp}.yaml")
        #generate_kubernetes_config(results, config_path) 
        
        try:
            estimated = {
                "estimated_Memory": results["profile"]["recommendations"]["memory"]["recommended_allocation"],
                "estimated_CPU_cores": results["profile"]["recommendations"]["cpu"]["recommended_cores"],
                "estimated_network_bandwidth_kbps": results["profile"]["recommendations"]["bandwidth"]["peak_requirement"],
            }
            print("\nestimated:", json.dumps(estimated, indent=2))
        except KeyError as e:
            print(f"KeyError: {e}. keys were not found ")
    
    finally:
        conn.close()
