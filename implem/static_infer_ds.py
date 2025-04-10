import ast
from collections import defaultdict

def analyze_code(code):
    tree = ast.parse(code)
    analysis = {
        "variables": defaultdict(list),
        "functions": {},
        "imports": [],
        "naming_conventions": defaultdict(list),
        "control_flow": defaultdict(int),
    }

    class CodeAnalyzer(ast.NodeVisitor):
        def visit_Assign(self, node):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    analysis["variables"][target.id].append(type(node.value).__name__)
            self.generic_visit(node)

        def visit_FunctionDef(self, node):
            params = [arg.arg for arg in node.args.args]
            returns = getattr(node.returns, "id", None)
            analysis["functions"][node.name] = {"params": params, "returns": returns}
            self.generic_visit(node)

        def visit_Import(self, node):
            for alias in node.names:
                analysis["imports"].append(alias.name)

        def visit_ImportFrom(self, node):
            for alias in node.names:
                analysis["imports"].append(f"{node.module}.{alias.name}")

        def visit_Name(self, node):
            name = node.id.lower()
            if any(keyword in name for keyword in ["stack", "queue", "graph", "heap", "tree"]):
                analysis["naming_conventions"]["data_structures"].append(node.id)
            self.generic_visit(node)

        def visit_For(self, node):
            analysis["control_flow"]["loops"] += 1
            self.generic_visit(node)

        def visit_While(self, node):
            analysis["control_flow"]["loops"] += 1
            self.generic_visit(node)

        def visit_If(self, node):
            analysis["control_flow"]["conditionals"] += 1
            self.generic_visit(node)

        def visit_Call(self, node):
            if isinstance(node.func, ast.Name):
                func_name = node.func.id.lower()
                if any(keyword in func_name for keyword in ["dfs", "bfs", "sort", "search"]):
                    analysis["naming_conventions"]["algorithms"].append(node.func.id)
            self.generic_visit(node)

    CodeAnalyzer().visit(tree)
    return analysis

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

print("------------------------------------\n")

if __name__ == "__main__":
    analysis_result = analyze_code(code_example)
    print(analysis_result)
