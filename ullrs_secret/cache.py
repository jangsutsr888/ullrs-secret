import collections
import functools
import hashlib
import json
import time
from typing import Any, Callable, Optional, Protocol, Tuple


class CacheBackend(Protocol):
    def get(self, key: str) -> Optional[Any]:
        ...

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        ...

class LRUMemoryCacheBackend:
    def __init__(self, maxsize: int = 128):
        # Stores values as (value, expiry_timestamp)
        # If expiry_timestamp is None, it never expires.
        self.cache: collections.OrderedDict[str, Tuple[Any, Optional[float]]] = collections.OrderedDict()
        self.maxsize = maxsize

    def get(self, key: str) -> Optional[Any]:
        if key in self.cache:
            value, expiry = self.cache[key]
            if expiry is not None and time.time() > expiry:
                # Cache expired
                del self.cache[key]
                return None
            
            # Move to end to mark as recently used
            self.cache.move_to_end(key)
            return value
        return None

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        if key in self.cache:
            self.cache.move_to_end(key)
        
        expiry = time.time() + ttl if ttl is not None else None
        self.cache[key] = (value, expiry)
        
        if len(self.cache) > self.maxsize:
            # Pop the first item (least recently used)
            self.cache.popitem(last=False)

# Global default backend
_default_backend = LRUMemoryCacheBackend()

def set_default_backend(backend: CacheBackend):
    global _default_backend
    _default_backend = backend

def _generate_cache_key(prefix: str, *args, **kwargs) -> str:
    """Generate a deterministic cache key from arguments."""
    key_dict = {
        "args": args,
        "kwargs": kwargs
    }
    # Create a stable string representation
    try:
        key_str = json.dumps(key_dict, sort_keys=True, default=str)
    except TypeError:
        # Fallback if arguments aren't JSON serializable (e.g. datetime)
        key_str = str(key_dict)
    
    hashed_key = hashlib.md5(key_str.encode('utf-8')).hexdigest()
    return f"{prefix}:{hashed_key}"

def cached(prefix: str, maxsize: int = 128, ttl: Optional[int] = None):
    """
    Decorator to cache the results of a function using the configured CacheBackend.
    """
    # Create a specific backend for this function's scope if using memory cache
    # to enforce maxsize per-function, otherwise it shares the global one.
    # For now, we use a shared backend for simplicity unless a dedicated one is needed.
    # To strictly respect maxsize per decorator instance using the default memory backend:
    local_backend = LRUMemoryCacheBackend(maxsize=maxsize)

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            key = _generate_cache_key(prefix, *args, **kwargs)
            
            # Allow global override, but fallback to local LRU for isolated sizing
            backend_to_use = _default_backend if not isinstance(_default_backend, LRUMemoryCacheBackend) else local_backend
            
            cached_result = backend_to_use.get(key)
            if cached_result is not None:
                return cached_result
            
            result = func(*args, **kwargs)
            backend_to_use.set(key, result, ttl=ttl)
            return result
        return wrapper
    return decorator
