import time
import random
from functools import wraps
from typing import TypeVar, Callable, Any

T = TypeVar('T')

class RetryConfig:
    def __init__(self, max_attempts: int = 3, base_delay: float = 1.0, max_delay: float = 60.0, backoff_factor: float = 2.0, jitter: bool = True):
        self.max_attempts = max_attempts
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.backoff_factor = backoff_factor
        self.jitter = jitter

def retry(exceptions: tuple = (Exception,), config: RetryConfig = None):
    """Decorator to retry a function with exponential backoff."""
    if config is None:
        config = RetryConfig()

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            last_exception = None
            for attempt in range(1, config.max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt == config.max_attempts:
                        break
                    delay = min(config.base_delay * (config.backoff_factor ** (attempt - 1)), config.max_delay)
                    if config.jitter:
                        delay *= random.uniform(0.8, 1.2)
                    time.sleep(delay)
            raise last_exception
        return wrapper
    return decorator