import random

from implem.Read_git_files import RepoMemoryAnalyzer
from implem.Analyzing_file_codes import StaticFileAnalyzer, DynamicAnalyzer, CodeStructureAnalyzer,LLMAnalyzer

if __name__ == "__main__":
    print("--------Static----------------")
    static_analyzer = StaticFileAnalyzer("codes_as_param.py")
    metrics = static_analyzer.analyze()

    # print("\n-----------Dynamic-------------")
    # arr = [random.randint(1, 100) for _ in range(10)]
    # profiler = DynamicAnalyzer(arr, static_analyzer)
    # mem = profiler.run_with_memory_profile()
    # print(f"memory usage w/ memory_usage: {mem} MB")

    # print("\n-----------LLM-------------")
    # llm = LLMAnalyzer(static_analyzer)
    # result = llm.analyze_code()
    # print(result)

    # print("\n-----------Data Structure-------------")
    # with open(static_analyzer.file_path, 'r', encoding='utf-8') as f:
    #     code = f.read()
    # structure_analyzer = CodeStructureAnalyzer(code)
    # print(structure_analyzer.analyze())

    print("\n-----------read from Git-------------")
    git_analyzer = RepoMemoryAnalyzer()
    git_analyzer.analyze_repo()

    