import time
import logging
import asyncio
from typing import Callable, Any
from functools import wraps

log = logging.getLogger(__name__)


def with_latency_logger(tag: str):
    def decorator(fn: Callable[..., Any]) -> Callable[..., Any]:
        if asyncio.iscoroutinefunction(fn):

            @wraps(fn)
            async def async_wrapper(*args, **kwargs):
                start = time.time()
                result = await fn(*args, **kwargs)
                elapsed = time.time() - start
                log.info(f"[latency] {tag} took {elapsed:.2f}s")
                return result

            return async_wrapper
        else:

            @wraps(fn)
            def sync_wrapper(*args, **kwargs):
                start = time.time()
                result = fn(*args, **kwargs)
                elapsed = time.time() - start
                log.info(f"[latency] {tag} took {elapsed:.2f}s")
                return result

            return sync_wrapper

    return decorator
