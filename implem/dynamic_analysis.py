from memory_profiler import memory_usage, profile
import random


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


if __name__ == "__main__":
    arr = [random.randint(1, 100) for _ in range(10)]
    mem_usage = memory_usage((merge_sort, (arr,)), max_usage= True)
    print(f"memory usage w/ memory_usage-\n: {mem_usage} MB")