import os
from dotenv import load_dotenv
import anthropic

class ClaudeAnalyzer:
    def __init__(self, api_key_env_var="api_keys", model="claude-3-7-sonnet-20250219"):
        load_dotenv()
        self.api_key = os.getenv(api_key_env_var)
        self.client = anthropic.Anthropic(api_key=self.api_key)
        self.model = model

    def analyze_code(self, code: str):
        prompt = (
            "Analyse and Estimate the dynamic memory usage of this code, "
            "detect the complexity and focus on algorithm/data structures and complexity:\n" + code
        )
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1024,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )
            return response.content
        except Exception as e:
            return [f"Error analyzing code: {e}"]

if __name__ == "__main__":
    code_inp = """
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
    analyzer = ClaudeAnalyzer()
    result = analyzer.analyze_code(code_inp)
    print("Memory usage with LLM:\n", result[0].text if isinstance(result, list) else result)
