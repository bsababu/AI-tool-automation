import random

from implem.Read_git_files import RepoMemoryAnalyzer
from implem.analyzer.Analyzing_file_codes import LLMAnalyzer_1, StaticFileAnalyzer, DynamicAnalyzer, CodeStructureAnalyzer,LLMAnalyzer

fayi = "codes_as_param.py"

if __name__ == "__main__":
    print("--------Static----------------")
    static_analyzer = StaticFileAnalyzer(fayi)
    metrics = static_analyzer.analyze()


    print("\n-----------LLM-------------")
    llm = LLMAnalyzer(static_analyzer)
    result = llm.analyze_code()
    print(result)

    print("\n-----------Data Structure-------------")
    with open(static_analyzer.file_path, 'r', encoding='utf-8') as f:
        code = f.read()
    structure_analyzer = CodeStructureAnalyzer(code)
    print(structure_analyzer.analyze())

    print("\n-----------read from Git-------------")
    git_analyzer = RepoMemoryAnalyzer()
    git_analyzer.analyze_repo()

    