import os
import git
from github import Github

class RepoFetcher:
    def __init__(self, github_token=None):
        self.token = github_token
        self.github_client = Github(github_token) if github_token else None
    
    def fetch_repo(self, repo_url, local_path=None):
        """Fetch a GitHub repository to analyze"""
        if not local_path:
            repo_name = repo_url.split('/')[-1]
            local_path = f"./AnalyzedRepos/{repo_name}"
        
        print(f"Cloning {repo_url} to {local_path}")
        git.Repo.clone_from(repo_url, local_path)
        return local_path
    
    def get_repo_structure(self, local_path):
        """Get repository file structure"""
        structure = {}
        for root, dirs, files in os.walk(local_path):
            if ".git" in root:
                continue
            rel_path = os.path.relpath(root, local_path)
            if rel_path == ".":
                structure["/"] = [f for f in files if f.endswith(".py")]
            else:
                structure[rel_path] = [f for f in files if f.endswith(".py")]
        return structure