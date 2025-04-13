

import os
import tempfile
import git
from dotenv import load_dotenv
import anthropic
import random

from .Analyzing_file_codes import DynamicAnalyzer, LLMAnalyzer, StaticFileAnalyzer

class RepoMemoryAnalyzer:
    def __init__(self):
        load_dotenv()
        self.client = anthropic.Anthropic(api_key=os.getenv("api_keys"))
        self.repo_path = None
        self.code_files = {}

    def clone_repo_from_input(self):
        repo_url = input("❯ Enter Git repo URL (must end with .git): ").strip()
        if not repo_url.endswith(".git"):
            raise ValueError("Invalid Git URL. Must end with .git")
        self.repo_path = tempfile.mkdtemp()
        print(f"\n❯ Cloning into: {self.repo_path}")
        git.Repo.clone_from(repo_url, self.repo_path)

    def fetch_py_files(self):
        for root, _, files in os.walk(self.repo_path):
            for file in files:
                if file.endswith(".py"):
                    path = os.path.join(root, file)
                    self.code_files[path] = path

    def analyze_repo(self):
        self.clone_repo_from_input()
        self.fetch_py_files()

        total_static_mem = 0
        max_llm_mem = 0
        max_dynamic_mem = 0

        for path in self.code_files.values():
            print(f"\nAnalyzing: {path}")

            # Static Analysis
            try:
                static_analyzer = StaticFileAnalyzer(path)
                result = static_analyzer.analyze()
                total_static_mem += result["memory_usage"]
            except Exception as e:
                print(f"[Static] Skipped {path} due to error: {e}")
                continue

            # Dynamic Analysis
            try:
                arr = [random.randint(1, 100) for _ in range(10)]
                dynamic = DynamicAnalyzer(arr, static_analyzer)
                mem_used = dynamic.run_with_memory_profile()
                mem_bytes = int(mem_used[0] * 1024 * 1024)  # Convert MB to bytes
                max_dynamic_mem = max(max_dynamic_mem, mem_bytes)
            except Exception as e:
                print(f"[Dynamic] Skipped {path}: {e}")

            # LLM Analysis
            try:
                llm = LLMAnalyzer(static_analyzer)
                llm_result = llm.analyze_code()
                est_bytes = self.extract_llm_memory_estimate(llm_result)
                max_llm_mem = max(max_llm_mem, est_bytes)
            except Exception as e:
                print(f"[LLM] Skipped {path}: {e}")

        print(f"\n❯ Total Static Memory Estimate: {total_static_mem:,} bytes")
        print(f"❯ Peak Dynamic Memory Estimate: {max_dynamic_mem:,} bytes")
        print(f"❯ LLM Estimated Peak Memory: {max_llm_mem:,} bytes")

    def extract_llm_memory_estimate(self, text: str) -> int:
        import re
        match = re.search(r"(\d+(?:\.\d+)?)\s*(KB|MB|GB)", text, re.I)
        if not match:
            return 0
        value, unit = float(match[1]), match[2].upper()
        multiplier = {"KB": 1024, "MB": 1024 ** 2, "GB": 1024 ** 3}.get(unit, 1)
        return int(value * multiplier)