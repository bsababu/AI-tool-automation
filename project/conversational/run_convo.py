import json
import os
import datetime
import time
import git


from project.RL.db_feedback import compare_and_log_changes, init_database, store_analysis
from project.container.cloud_configs import generate_all_cloud_configs
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
    
def generate_kubernetes_config(results, output_path):
    pass

def analyzer_main(repo_url, github_token, llm_api_key):
    if not repo_url.endswith(".git"):
        print("Invalid URL. Please enter a valid GitHub .git URL.")
        return {"error": "Invalid URL. Please enter a valid GitHub .git URL."}
    
    try:
        start = time.time()
        conn = init_database()
        if not conn:
            return {"error": "Failed to connect to the database."}
        analyzer = GithubResourceAnalyzer(github_token, llm_api_key)
        results = analyzer.analyze_repository(repo_url)
        
        store_analysis(conn, results)
        
        results_dir = "./Results/Configs"
        if not os.path.exists(results_dir):
            os.makedirs(results_dir, exist_ok=True)
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        
        cloud_configs = generate_all_cloud_configs(results, results_dir)
        results["cloud_configs"] = cloud_configs


        json_path = os.path.join(results_dir, f"analysis_{timestamp}.json")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2)
        
        comparison = compare_and_log_changes(conn, results)
        
        try:
            estimated = {
                "estimated_Memory": results["profile"]["recommendations"]["memory"]["recommended_allocation"],
                "estimated_CPU_cores": results["profile"]["recommendations"]["cpu"]["recommended_cores"],
                "estimated_network_bandwidth": results["profile"]["recommendations"]["bandwidth"]["peak_requirement"],
                "json_path": json_path,
                "cloud_configs": cloud_configs,
                "comparison": comparison,
            }
            return {
                "results": results,
                "estimated": estimated
            }
        except KeyError as e:
            return {"error": f"Error processing results: {str(e)}"}
    
    except Exception as e:
        return {"error": f"Analysis failed: {str(e)}"}
    
    finally:
        if 'conn' in locals():
            conn.close()
        end = time.time()
        print(f"Time taken for analysis: {end - start:.2f} seconds")
