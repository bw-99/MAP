import time
import logging
from typing import Callable, Any

log = logging.getLogger(__name__)

def with_latency_logger(tag: str):
    def decorator(fn: Callable[..., Any]) -> Callable[..., Any]:
        def wrapper(*args, **kwargs):
            start = time.time()
            result = fn(*args, **kwargs)
            elapsed = time.time() - start
            log.info(f"[latency] {tag} took {elapsed:.2f}s")
            return result
        return wrapper
    return decorator
