import os
import sys
import radon.complexity as rc
import radon.metrics as rm

def get_file_size(file_path):
    fp_sum = os.path.getsize(file_path)
    # print(f"file size{fp_sum}")
    return fp_sum

def line_of_codes(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        return sum(1 for _ in f)

def calculate_overhead_per_line(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    if not lines:
        return 0
    
    sam = sum(sys.getsizeof(line) for line in lines)
    # print(f"OH summary: {sam}")
    return sam / len(lines)


def complexity_Analy(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        code = f.read()
    
    complexity_scores = rc.cc_visit(code)
    maintainability_index = rm.mi_visit(code, True)
    halstead_metrics = rm.h_visit(code)
    
    cyclomatic_complexity = sum(c.complexity for c in complexity_scores)
    
    print("\nComplexity Metrics:")
    print(f"Cyclomatic complexity: {cyclomatic_complexity}\n")
    print(f"Halstead metrics: {halstead_metrics}\n")
    print(f"Maintainability index: {maintainability_index}\n")
    
    return {
        "cyclomatic_complexity": cyclomatic_complexity,
        "halstead_metrics": halstead_metrics,
        "maintainability_index": maintainability_index
    }

def estimate_memory_usage(file_size, loc, overhead_per_line, complexity_metrics):
    complexity_factor = 1 + (complexity_metrics["cyclomatic_complexity"] / 100)
    return (file_size + (loc * overhead_per_line)) * complexity_factor


def analyze_file(file_path):
    file_size = get_file_size(file_path)
    loc = line_of_codes(file_path)
    overhead_per_line = calculate_overhead_per_line(file_path)
    complexity_metrics = complexity_Analy(file_path)
    memory_usage = estimate_memory_usage(file_size, loc, overhead_per_line, complexity_metrics)
    
    # print(f"\nFile: {file_path}")
    print(f"File Size: {file_size} bytes\n")
    print(f"Lines of Code: {loc} lines \n")
    print(f"Overhead per Line: {overhead_per_line:.2f} bytes\n")
    print(f"Estimated Memory Usage: {memory_usage/1000} KB")
    
    return {
        "file_size": file_size,
        "lines_of_code": loc,
        "memory_usage": memory_usage,
        "overhead_per_line": overhead_per_line,
        "complexity_metrics": complexity_metrics
    }

if __name__ == "__main__":
    file_path = "./implem/exerc_static_allo.py" 
    metrics = analyze_file(file_path)
    print("------------------------")