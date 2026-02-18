import time
from typing import Dict, Any, Optional
from threading import Lock

class TTLCache:
    """Simple in-memory TTL cache with thread safety."""
    def __init__(self, ttl_seconds: int = 86400):  # default 24 hours
        self.ttl = ttl_seconds
        self._store: Dict[str, tuple[Any, float]] = {}
        self._lock = Lock()

    def get(self, key: str) -> Optional[Any]:
        with self._lock:
            if key not in self._store:
                return None
            value, expires_at = self._store[key]
            if time.time() > expires_at:
                del self._store[key]
                return None
            return value

    def set(self, key: str, value: Any, ttl: int = None):
        with self._lock:
            expires = time.time() + (ttl if ttl is not None else self.ttl)
            self._store[key] = (value, expires)

    def invalidate(self, key: str):
        with self._lock:
            if key in self._store:
                del self._store[key]

    def clear(self):
        with self._lock:
            self._store.clear()