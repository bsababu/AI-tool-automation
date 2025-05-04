import re
import os
import tempfile
import git
import random

from analyzer.Analyzing_file_codes import DynamicAnalyzer, LLMAnalyzer, LLMAnalyzer_1, StaticFileAnalyzer

class RepoMemoryAnalyzer:
    def __init__(self):
        self.repo_path = None
        self.code_files = {}

    def _clone_repo_from_input(self):
        repo_url = input("❯ Enter Git repo URL (must end with .git): ").strip()
        if not repo_url.endswith(".git"):
            raise ValueError("Invalid Git URL. Must end with .git")
        self.repo_path = tempfile.mkdtemp()
        print(f"❯ Cloning into: {self.repo_path}")
        git.Repo.clone_from(repo_url, self.repo_path)

    def _fetch_py_files(self):
        for root, _, files in os.walk(self.repo_path):
            for file in files:
                if file.endswith(".py"):
                    path = os.path.join(root, file)
                    if os.path.getsize(path) > 0:
                        self.code_files[path] = path
                    #self.code_files[path] = path

    def _analyze_repo(self):
        self._clone_repo_from_input()
        self._fetch_py_files()

        total_static_mem = 0
        max_llm_mem = 0
        max_dynamic_mem = 0

        for path in self.code_files.values():
            print(f"Analyzing: {path}")

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
                mem_bytes = int(mem_used[0] * 1024 * 1024)
                max_dynamic_mem = max(max_dynamic_mem, mem_bytes)
            except Exception as e:
                print(f"[Dynamic] Skipped {path}: {e}")

            # LLM Analysis
            try:
                # llm = LLMAnalyzer(static_analyzer)
                llm = LLMAnalyzer_1(static_analyzer)
                llm_result = llm._analyze_code()
                est_bytes = self._extract_llm_memory_estimate(llm_result)
                max_llm_mem = max(max_llm_mem, est_bytes)

                # print("LLM result:\n", llm_result)
                # print("est_bytes:\n", est_bytes)

            except Exception as e:
                print(f"[LLM] Skipped {path}: {e}")

        print(f"❯ Total Static Memory Estimate: {total_static_mem:,} bytes")
        print(f"❯ Peak Dynamic Memory Estimate: {max_dynamic_mem:,} bytes")
        print(f"❯ LLM Estimated Peak Memory: {max_llm_mem:,} bytes")

    def _extract_llm_memory_estimate(self, text: str) -> int:
        match = re.search(r"(\d+(?:\.\d+)?)\s*(KB|MB|GB)", text, re.I)
        if not match:
            return 0
        value, unit = float(match[1]), match[2].upper()
        multiplier = {"KB": 1024, "MB": 1024 ** 2, "GB": 1024 ** 3}.get(unit, 1)
        return int(value * multiplier)
    
    def _extract_cpu_value(self, res):
        match = re.search(r'CPU[^:]*[:\-]\s*([\w\d.%\s]+)', res, re.I)
        return match[1].strip() if match else "unknown"
    
    def _extract_network_value(self, res):
        match = re.search(r'Network[^:]*[:\-]\s*([\w\d.%\s]+)', res, re.I)
        return match[1].strip() if match else "unknown"
    
    def _convert_to_bytes(self, size_in_bytes):
        units = ['B', 'KB', 'MB', 'GB', 'TB', 'PB']
        index = 0
        while size_in_bytes >= 1024 and index < len(units) - 1:
            size_in_bytes /= 1024
            index += 1
        return f"{size_in_bytes:.2f} {units[index]}"
    

if __name__ == "__main__":
    analyzer = RepoMemoryAnalyzer()
    analyzer._analyze_repo()