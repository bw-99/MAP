import time
from typing import Callable, Any

def with_latency_logger(tag: str):
    def decorator(fn: Callable[..., Any]):
        def wrapper(*args, **kwargs):
            start = time.time()
            result = fn(*args, **kwargs)
            end = time.time()
            print(f"[latency] {tag} took {end - start:.2f}s")
            return result
        return wrapper
    return decorator