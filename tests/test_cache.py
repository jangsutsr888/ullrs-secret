import time
from unittest.mock import MagicMock


from ullrs_secret.cache import LRUMemoryCacheBackend, cached


def test_lru_cache_backend_set_get():
    cache = LRUMemoryCacheBackend(maxsize=3)
    
    cache.set("a", 1)
    cache.set("b", 2)
    cache.set("c", 3)
    
    assert cache.get("a") == 1
    assert cache.get("b") == 2
    assert cache.get("c") == 3

def test_lru_cache_backend_eviction():
    cache = LRUMemoryCacheBackend(maxsize=2)
    
    cache.set("a", 1)
    cache.set("b", 2)
    cache.set("c", 3)
    
    assert cache.get("a") is None  # 'a' should be evicted
    assert cache.get("b") == 2
    assert cache.get("c") == 3

def test_lru_cache_backend_lru_order():
    cache = LRUMemoryCacheBackend(maxsize=2)
    
    cache.set("a", 1)
    cache.set("b", 2)
    
    # Access 'a' to make it recently used
    cache.get("a")
    
    # Add 'c', this should evict 'b' instead of 'a'
    cache.set("c", 3)
    
    assert cache.get("b") is None
    assert cache.get("a") == 1
    assert cache.get("c") == 3

def test_lru_cache_backend_ttl():
    cache = LRUMemoryCacheBackend(maxsize=2)
    
    # Set with 1 second TTL
    cache.set("a", 1, ttl=1)
    
    assert cache.get("a") == 1
    
    # Sleep past the TTL
    time.sleep(1.1)
    
    assert cache.get("a") is None

def test_cached_decorator():
    mock_func = MagicMock(return_value="result")
    
    @cached("test_prefix", maxsize=2)
    def my_func(x, y):
        return mock_func(x, y)
    
    # First call
    res1 = my_func(1, 2)
    assert res1 == "result"
    assert mock_func.call_count == 1
    
    # Second call with same args, should use cache
    res2 = my_func(1, 2)
    assert res2 == "result"
    assert mock_func.call_count == 1  # Still 1
    
    # Call with different args, should call function again
    res3 = my_func(3, 4)
    assert res3 == "result"
    assert mock_func.call_count == 2

def test_cached_decorator_with_ttl():
    mock_func = MagicMock(return_value="result")
    
    @cached("test_prefix_ttl", maxsize=2, ttl=1)
    def my_func_ttl(x, y):
        return mock_func(x, y)
        
    res1 = my_func_ttl(1, 2)
    assert res1 == "result"
    assert mock_func.call_count == 1
    
    # Should hit cache
    res2 = my_func_ttl(1, 2)
    assert mock_func.call_count == 1
    
    # Wait for expiry
    time.sleep(1.1)
    
    res3 = my_func_ttl(1, 2)
    assert mock_func.call_count == 2
