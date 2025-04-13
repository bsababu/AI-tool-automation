from memory_profiler import memory_usage
import random

class MergeSortProfiler:
    def __init__(self, array):
        self.array = array
        self.sorted_array = None
        self.memory_used = None

    def merge_sort(self, arr):
        if len(arr) > 1:
            mid = len(arr) // 2
            left = arr[:mid]
            right = arr[mid:]
            self.merge_sort(left)
            self.merge_sort(right)
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

    def run_with_memory_profile(self):
        self.memory_used = memory_usage((self.merge_sort, (self.array,)), max_usage=True)
        self.sorted_array = self.array
        return self.memory_used

if __name__ == "__main__":
    arr = [random.randint(1, 100) for _ in range(10)]
    profiler = MergeSortProfiler(arr)
    mem = profiler.run_with_memory_profile()
    print(f"memory usage w/ memory_usage:\n{mem} MB")
