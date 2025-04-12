
def estimate_memory_usage():
    static = estimate_static_memory()
    dynamic = estimate_dynamic_memory()
    llm = estimate_llm_memory()


if __name__ == "__main__" :
    estimate_memory_usage()