from openai import OpenAI
import anthropic
import os
from dotenv import load_dotenv
from pathlib import Path
import random


dotenv_path = Path('./.env')
load_dotenv(dotenv_path=dotenv_path)

def analyze_with_claude(code):
  client = anthropic.Anthropic(
    # defaults to 
    api_key=os.environ.get("api_key")
  )
  response = client.messages.create(
        model="claude-3-7-sonnet-20250219",
        max_tokens=1024,
        messages=[
            {"role": "user", "content": f"Analyze these Python code and detect the complexity and the algorithm used and then estimate the memory usage:\n{code}"}]
    )
  return response.content

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

print("Memory usage with LLM:\n", analyze_with_claude(code_inp))