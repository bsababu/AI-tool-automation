import os
import sys
import math
import radon.complexity as rc
import radon.metrics as rm

def get_file_size(file_path):
    return os.path.getsize(file_path)

def line_of_codes(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        return sum(1 for _ in f)

def calculate_overhead_per_line(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    if not lines:
        return 0
    return sum(sys.getsizeof(line) for line in lines) / len(lines)

def comment_ratio(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    if not lines:
        return 0
    comment_lines = [line for line in lines if line.strip().startswith('#')]
    return len(comment_lines) / len(lines)

# Analyze complexity metrics using Radon
def complexity_analysis(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
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

def estimate_memory_usage(file_size, loc, overhead_per_line, complexity_metrics):
    cc = complexity_metrics["cyclomatic_complexity"]
    complexity_factor = math.log2(2 + cc)
    return (file_size + (loc * overhead_per_line)) * complexity_factor


def analyze_file(file_path):
    file_size = get_file_size(file_path)
    loc = line_of_codes(file_path)
    overhead = calculate_overhead_per_line(file_path)
    complexity_metrics = complexity_analysis(file_path)
    memory_usage = estimate_memory_usage(file_size, loc, overhead, complexity_metrics)

    print(f"\n--- Analyzing: {file_path} ---")
    print(f"File Size: {file_size} bytes")
    print(f"Lines of Code: {loc}")
    print(f"Estimated Memory Usage: {memory_usage/1000:.2f} KB")

    return {
        "file_path": file_path,
        "file_size": file_size,
        "lines_of_code": loc,
        "overhead_per_line": overhead,
        "memory_usage": memory_usage,
        "complexity_metrics": complexity_metrics
    }

if __name__ == "__main__":
    file_path = "Thesis/implem/codes_as_param.py"
    metrics = analyze_file(file_path)
    print("------------------------")
