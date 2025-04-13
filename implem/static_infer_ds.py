import ast
from collections import defaultdict

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


if __name__ == "__main__":
    code_example = """
def merge_sort(arr):
    if len(arr) > 1:
        mid = len(arr) // 2
        left = arr[:mid]
        right = arr[mid:]
        merge_sort(left)
        merge_sort(right)
        i = j = k = 0
        while i < len(left) and j < len(right):
            if left[i] < right[j]:
                arr[k] = left[i]
                i += 1
            else:
                arr[k] = right[j]
                j += 1
            k += 1
        while i < len(left):
            arr[k] = left[i]
            i += 1
            k += 1
        while j < len(right):
            arr[k] = right[j]
            j += 1
            k += 1
    return arr
"""

    analyzer = CodeStructureAnalyzer(code_example)
    result = analyzer.analyze()
    print("\n------------------------------------\n")
    print(result)