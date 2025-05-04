import os
from dotenv import load_dotenv

from githubRepo.fetch_repo import RepoFetcher
from githubRepo.resource_analyzer import ResourceAnalyzer
from githubRepo.resource_profiler import ResourceProfiler
from pprint import pprint


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

def main():
    load_dotenv(".env")
    repo_url = input("Enter the GitHub repository .git URL: ").strip()

    if not repo_url.endswith(".git"):
        print("Invalid URL. Please enter a valid GitHub .git URL.")
        return

    github_token = None
    llm_api_key = os.getenv("OPEN_api_KEYS")

    analyzer = GithubResourceAnalyzer(github_token=github_token, llm_api_key=llm_api_key)
    results = analyzer.analyze_repository(repo_url)

    print("Repository structure analysis")
    for folder, files in results["structure"].items():
        print(f"{folder}: {files}")

    print("\nResource Profile Summary:")
    pprint(results["profile"])


if __name__ == "__main__":
    main()