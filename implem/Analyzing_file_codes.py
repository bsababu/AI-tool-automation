import os
import sys
import math
import radon.complexity as rc
import radon.metrics as rm
from memory_profiler import memory_usage
from dotenv import load_dotenv
import anthropic
import ast
from collections import defaultdict
from implem.codes_as_param import merge_sort

class StaticFileAnalyzer:
    def __init__(self, file_path):
        self.file_path = os.path.join(os.path.dirname(__file__), str(file_path))

        if not os.path.exists(self.file_path):
            raise FileNotFoundError(f"File not found at {self.file_path}")

        self.file_size = self.get_file_size()
        self.loc = self.line_of_codes()
        self.overhead = self.calculate_overhead_per_line()
        self.complexity_metrics = self.complexity_analysis()
        self.memory_usage = self.estimate_memory_usage()

    def get_file_size(self):
        return os.path.getsize(self.file_path)

    def line_of_codes(self):
        with open(self.file_path, 'r', encoding='utf-8') as f:
            return sum(1 for _ in f)

    def calculate_overhead_per_line(self):
        with open(self.file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        if not lines:
            return 0
        return sum(sys.getsizeof(line) for line in lines) / len(lines)

    def comment_ratio(self):
        with open(self.file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        if not lines:
            return 0
        comment_lines = [line for line in lines if line.strip().startswith('#')]
        return len(comment_lines) / len(lines)

    def complexity_analysis(self):
        with open(self.file_path, 'r', encoding='utf-8') as f:
            code = f.read()

        complexity_scores = rc.cc_visit(code)
        maintainability_index = rm.mi_visit(code, True)
        halstead_metrics = rm.h_visit(code)
        cyclomatic_complexity = sum(c.complexity for c in complexity_scores)

        return {
            "cyclomatic_complexity": cyclomatic_complexity,
            "halstead_metrics": halstead_metrics,
            "maintainability_index": maintainability_index
        }

    def estimate_memory_usage(self):
        cc = self.complexity_metrics["cyclomatic_complexity"]
        complexity_factor = math.log2(2 + cc)
        return (self.file_size + (self.loc * self.overhead)) * complexity_factor

    def analyze(self):
        print(f"Analyzing......\n: {self.file_path} ---")
        print(f"File Size: {self.file_size} bytes")
        print(f"Lines of Code: {self.loc}")
        print(f"Estimated Memory Usage: {self.memory_usage / 1000:.2f} KB")

        return {
            "file_path": self.file_path,
            "file_size": self.file_size,
            "lines_of_code": self.loc,
            "overhead_per_line": self.overhead,
            "memory_usage": self.memory_usage,
            "complexity_metrics": self.complexity_metrics
        }

class DynamicAnalyzer:
    def __init__(self, array, static_file_analyzer: StaticFileAnalyzer):
        self.array = array
        self.sorted_array = None
        self.memory_used = None
        self.static_file_analyzer = static_file_analyzer
        self._load_code_directly()

    def _load_code_directly(self):
        with open(self.static_file_analyzer.file_path, 'r', encoding='utf-8') as f:
            code = f.read()
            exec(code, globals())

    def run_with_memory_profile(self):
        if 'merge_sort' not in globals():
            raise RuntimeError("merge_sort is not defined in loaded file.")

        self.memory_used = memory_usage((merge_sort, (self.array,)), max_usage=True)
        self.sorted_array = self.array
        return self.memory_used

class LLMAnalyzer:
    def __init__(self, file_analyzer, api_key_env_var="api_keys", model="claude-3-7-sonnet-20250219"):
        load_dotenv()
        self.api_key = os.getenv(api_key_env_var)
        self.client = anthropic.Anthropic(api_key=self.api_key)
        self.model = model
        self.file_analyzer = file_analyzer

    def analyze_code(self):
        with open(self.file_analyzer.file_path, 'r', encoding='utf-8') as f:
            code = f.read()

        prompt = (
            "You are an expert software analyzer. Estimate the dynamic memory usage of this Python code.\
            Assume input size n = 1000 where applicable. Consider data structures, algorithm behavior,\
            memory growth over time, and expected peak memory usage:\n" + code
        )
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1024,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text
        except Exception as e:
            return f"Error analyzing: {e}"

class CodeStructureAnalyzer:
    def __init__(self, code: str):
        self.code = code
        self.tree = ast.parse(code)
        self.analysis = {
            "variables": defaultdict(list),
            "functions": {},
            "imports": [],
            "naming_conventions": defaultdict(list),
            "control_flow": defaultdict(int),
        }

    class _Analyzer(ast.NodeVisitor):
        def __init__(self, analysis):
            self.analysis = analysis

        def visit_Assign(self, node):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    self.analysis["variables"][target.id].append(type(node.value).__name__)
            self.generic_visit(node)

        def visit_FunctionDef(self, node):
            params = [arg.arg for arg in node.args.args]
            returns = getattr(node.returns, "id", None)
            self.analysis["functions"][node.name] = {"params": params, "returns": returns}
            self.generic_visit(node)

        def visit_Import(self, node):
            for alias in node.names:
                self.analysis["imports"].append(alias.name)

        def visit_ImportFrom(self, node):
            for alias in node.names:
                self.analysis["imports"].append(f"{node.module}.{alias.name}")

        def visit_Name(self, node):
            name = node.id.lower()
            if any(keyword in name for keyword in ["stack", "queue", "graph", "heap", "tree"]):
                self.analysis["naming_conventions"]["data_structures"].append(node.id)
            self.generic_visit(node)

        def visit_For(self, node):
            self.analysis["control_flow"]["loops"] += 1
            self.generic_visit(node)

        def visit_While(self, node):
            self.analysis["control_flow"]["loops"] += 1
            self.generic_visit(node)

        def visit_If(self, node):
            self.analysis["control_flow"]["conditionals"] += 1
            self.generic_visit(node)

        def visit_Call(self, node):
            if isinstance(node.func, ast.Name):
                func_name = node.func.id.lower()
                if any(keyword in func_name for keyword in ["dfs", "bfs", "sort", "search"]):
                    self.analysis["naming_conventions"]["algorithms"].append(node.func.id)
            self.generic_visit(node)

    def analyze(self):
        self._Analyzer(self.analysis).visit(self.tree)
        return self.analysis

