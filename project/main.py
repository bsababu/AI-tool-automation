import json
import os
from dotenv import load_dotenv
import times

from project.githubRepo.fetch_repo import RepoFetcher
from project.githubRepo.resource_analyzer import ResourceAnalyzer
from project.githubRepo.resource_profiler import ResourceProfiler


class GithubResourceAnalyzer:
    def __init__(self, github_token=None, llm_api_key=None):
        self.repo_fetcher = RepoFetcher(github_token)
        self.resource_analyzer = ResourceAnalyzer(llm_api_key)
        self.profiler = ResourceProfiler(self.resource_analyzer)
    
    def analyze_repository(self, repo_url):
        """Complete analysis workflow for a GitHub repository"""
        repo_path = self.repo_fetcher.fetch_repo(repo_url)
        repo_structure = self.repo_fetcher.get_repo_structure(repo_path)
        resource_profile = self.profiler.profile_repository(repo_path)
        return {
            "repository_url": repo_url,
            "structure": repo_structure,
            "profile": resource_profile,
        }

def analyzer_main():
    load_dotenv(".env")
    
    repo_url = input("Enter the GitHub repository .git URL: ").strip()

    if not repo_url.endswith(".git"):
        print("Invalid URL. Please enter a valid GitHub .git URL.")
        return

    github_token = None
    llm_api_key = os.getenv("OPEN_api_KEYS")

    analyzer = GithubResourceAnalyzer(github_token=github_token, llm_api_key=llm_api_key)
    results = analyzer.analyze_repository(repo_url)

    results_dir = f"./Results/"
    os.makedirs(results_dir, exist_ok=True)
    out_path = os.path.join(results_dir, f"analyzed{times.now()}.json")

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print(f"Full JSON written to {out_path}")

    try:
        estimated = {
        "estimated_Memory": results["profile"]["recommendations"]["memory"]["recommended_allocation"],
        "estimated_CPU_cores":   results["profile"]["recommendations"]["cpu"]["recommended_cores"],
        "estimated_network_bandwidth_kbps": results["profile"]["recommendations"]["bandwidth"]["peak_requirement"],
        }
        print("\nestimated:", json.dumps(estimated, indent=2))
    except KeyError as e:
        print(f"KeyError: {e}. keys were not found ")
