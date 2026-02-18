from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Callable, Any

def parallel_map(func: Callable[[Any], Any], items: List[Any], max_workers: int = 4) -> List[Any]:
    """Execute func on each item in parallel using threads. Returns results in order."""
    results = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_index = {executor.submit(func, item): idx for idx, item in enumerate(items)}
        for future in as_completed(future_to_index):
            idx = future_to_index[future]
            try:
                result = future.result()
                results.append((idx, result))
            except Exception as e:
                results.append((idx, None))
    # Sort by original index
    results.sort(key=lambda x: x[0])
    return [r[1] for r in results]