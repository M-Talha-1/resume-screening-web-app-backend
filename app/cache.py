from typing import Optional, Dict, Any
from datetime import datetime, timedelta

# Simple in-memory cache with TTL support
_cache: Dict[str, Dict[str, Any]] = {}

def init_cache():
    """Initialize cache"""
    global _cache
    _cache = {}

def set_cache(key: str, value: Any, ttl: int = 300):
    """
    Set a value in the cache with TTL (in seconds)
    Default TTL is 5 minutes
    """
    _cache[key] = {
        'value': value,
        'expires_at': datetime.now() + timedelta(seconds=ttl)
    }

def get_cache(key: str) -> Optional[Any]:
    """
    Get a value from the cache
    Returns None if key doesn't exist or has expired
    """
    if key not in _cache:
        return None
    
    cache_data = _cache[key]
    if datetime.now() > cache_data['expires_at']:
        del _cache[key]
        return None
    
    return cache_data['value']

def clear_cache():
    """Clear all cache entries"""
    global _cache
    _cache = {}

def remove_expired():
    """Remove all expired cache entries"""
    now = datetime.now()
    expired_keys = [
        key for key, data in _cache.items()
        if now > data['expires_at']
    ]
    for key in expired_keys:
        del _cache[key] 