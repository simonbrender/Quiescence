"""
Celerio Scout - Caching Layer
Simple in-memory cache with TTL for API responses
"""
import time
from typing import Dict, Optional, Any
from functools import wraps
import hashlib
import json

# In-memory cache store
_cache: Dict[str, Dict[str, Any]] = {}

# Default TTL in seconds
DEFAULT_TTL = 3600  # 1 hour

def _make_key(prefix: str, *args, **kwargs) -> str:
    """Create a cache key from prefix and arguments"""
    key_data = {
        'prefix': prefix,
        'args': args,
        'kwargs': sorted(kwargs.items())
    }
    key_str = json.dumps(key_data, sort_keys=True)
    return hashlib.md5(key_str.encode()).hexdigest()

def get_cache(key: str) -> Optional[Any]:
    """Get value from cache if not expired"""
    if key not in _cache:
        return None
    
    entry = _cache[key]
    if time.time() > entry['expires_at']:
        # Expired, remove it
        del _cache[key]
        return None
    
    return entry['value']

def set_cache(key: str, value: Any, ttl: int = DEFAULT_TTL) -> None:
    """Set value in cache with TTL"""
    _cache[key] = {
        'value': value,
        'expires_at': time.time() + ttl,
        'created_at': time.time()
    }

def clear_cache(prefix: Optional[str] = None) -> int:
    """Clear cache entries, optionally filtered by prefix"""
    if prefix is None:
        count = len(_cache)
        _cache.clear()
        return count
    
    # Clear entries matching prefix
    keys_to_delete = [k for k in _cache.keys() if k.startswith(prefix)]
    for key in keys_to_delete:
        del _cache[key]
    return len(keys_to_delete)

def cached(ttl: int = DEFAULT_TTL, key_prefix: str = ""):
    """
    Decorator to cache async function results
    Usage:
        @cached(ttl=3600, key_prefix="github")
        async def get_github_stats(org_name: str):
            ...
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            cache_key = _make_key(key_prefix or func.__name__, *args, **kwargs)
            
            # Try to get from cache
            cached_value = get_cache(cache_key)
            if cached_value is not None:
                return cached_value
            
            # Call function and cache result
            result = await func(*args, **kwargs)
            set_cache(cache_key, result, ttl)
            
            return result
        return wrapper
    return decorator

def get_cache_stats() -> Dict[str, Any]:
    """Get cache statistics"""
    total_entries = len(_cache)
    expired_entries = sum(1 for entry in _cache.values() if time.time() > entry['expires_at'])
    active_entries = total_entries - expired_entries
    
    return {
        'total_entries': total_entries,
        'active_entries': active_entries,
        'expired_entries': expired_entries,
        'memory_usage_mb': sum(len(str(v['value']).encode()) for v in _cache.values()) / (1024 * 1024)
    }







