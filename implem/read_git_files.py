import os
import sys
import tempfile
import subprocess
import git
import re
from dotenv import load_dotenv
from memory_profiler import profile, memory_usage
import anthropic


load_dotenv()

client = anthropic.Anthropic(api_key=os.getenv("api_keys"))

def clone_repo_from_input():
    repo_url = input("❯ Enter Git repo URL (must end with .git): ").strip()
    if not repo_url.endswith(".git"):
        raise ValueError("Invalid Git URL. Must end with .git")
    clone_dir = tempfile.mkdtemp()
    print(f"\n❯ Cloning into: {clone_dir}")
    git.Repo.clone_from(repo_url, clone_dir)
    return clone_dir

def fetch_py_files(root_path):
    code_files = {}
    for root, _, files in os.walk(root_path):
        for file in files:
            if file.endswith(".py"):
                path = os.path.join(root, file)
                with open(path, "r", encoding="utf-8", errors="ignore") as f:
                    code_files[path] = f.read()
    return code_files

def estimate_static_memory(code: str) -> int:
    return sum(sys.getsizeof(line) for line in code.splitlines())

def estimate_dynamic_memory_llm(code: str) -> str:
    prompt = f"""
You are an expert software analyzer. Estimate the dynamic memory usage of this Python code.
Assume input size n = 1000 where applicable. Consider data structures, algorithm behavior,
memory growth over time, and expected peak memory usage.

```python
{code}
```"""
    try:
        res = client.messages.create(
            model="claude-3-7-sonnet-20250219",
            max_tokens=1024,
            messages=[
                {"role": "user", "content": f"You are a memory estimation assistant.: {prompt}"}
            ]
        )
        return res.content[0].text.strip()
    except Exception as e:
        return f"LLM error: {e}"

def extract_llm_memory_estimate(text: str) -> int:
    match = re.search(r"(\d+(?:\.\d+)?)\s*(KB|MB|GB)", text, re.I)
    if not match:
        return 0
    value, unit = float(match[1]), match[2].upper()
    multiplier = {"KB": 1024, "MB": 1024**2, "GB": 1024**3}.get(unit, 1)
    return int(value * multiplier)

# def dynamic_analy(code: str) -> str:
   
#     lines = code.splitlines()
#     new_lines = ["from memory_profiler import profile\n"]
#     for i, line in enumerate(lines):
#         if line.strip().startswith("def ") and (i == 0 or not lines[i - 1].strip().startswith("@")):
#             new_lines.append("@profile")
#         new_lines.append(line)
#     return "\n".join(new_lines)

# def run_memory_profile(profiled_code: str) -> int:
    

    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as temp_file:
        temp_file.write(profiled_code)
        temp_path = temp_file.name

    print(f"\n❯ Running memory_profiler on: {temp_path}\n")

    try:
        result = subprocess.run(
            [sys.executable, "-m", "memory_profiler", temp_path],
            capture_output=True,
            text=True,
            check=True
        )
        output = result.stdout
        print(output)

        match = re.search(r"^.*?Peak memory:\s+([\d.]+)\s+MiB", output, re.MULTILINE)
        if match:
            peak_mib = float(match.group(1))
            print(f"Peak memory usage: {peak_mib} MiB")
            return int(peak_mib * 1024 * 1024)  # Convert MiB to bytes
        else:
            print("Could not find peak memory information in output")
            return 0
    finally:
        # Clean up the temporary file
        if os.path.exists(temp_path):
            os.remove(temp_path)

def dy_with_mem_usage(code: str):
    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as temp_file:
        temp_file.write(code)
        temp_path = temp_file.name

    print(f"\n❯ Running memory usage....: {temp_path}\n")
    try:
        def run_code():
            exec(open(temp_path).read())
        mem_usage = memory_usage(run_code, max_usage=True)

        peak_memory_usage = max(mem_usage)
        print(f"Peak memory usage: {peak_memory_usage} MB")

        return int(peak_memory_usage * 1024 * 1024)
    finally:
        # remove the temp
        if os.path.exists(temp_path):
            os.remove(temp_path)

def main():
    repo_path = clone_repo_from_input()
    all_files = fetch_py_files(repo_path)

    total_static = 0
    max_llm_est = 0
    dy_mem=0

    for path, code in all_files.items():
        total_static += estimate_static_memory(code)
        short_code = code[:4000]
        llm_result = estimate_dynamic_memory_llm(short_code)
        llm_bytes = extract_llm_memory_estimate(llm_result)
        max_llm_est = max(max_llm_est, llm_bytes)
        # dy_mem += dy_with_mem_usage(code)
        

    print(f"Static Memory (sum of code structure): {total_static:,} bytes")
    print(f"LLM Estimated memory: {max_llm_est:,} bytes")
    # print(f"Dynamic Profiler Peak (ENTRY_FILE): {dynamic_peak:,} bytes")
    # print(f"memory_usage mod: {dy_mem}")

if __name__ == "__main__":
    main()

# https://github.com/bsababu/summarized-news-tool.git