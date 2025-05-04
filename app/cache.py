import os
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import redis
from redis.retry import Retry
from redis.backoff import ExponentialBackoff
import json
import logging
from tenacity import retry, stop_after_attempt, wait_exponential
from dotenv import load_dotenv

from app.config import settings

# Configure logging
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Redis configuration with connection pooling and retry mechanism
redis_client = redis.Redis.from_url(
    settings.REDIS_URL,
    decode_responses=True,
    retry_on_timeout=True,
    retry=Retry(ExponentialBackoff(), 3),
    socket_timeout=5,
    socket_connect_timeout=5,
    health_check_interval=30
)

# Export redis_client as cache
cache = redis_client

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10)
)
def init_cache():
    """Initialize Redis connection with retry mechanism"""
    try:
        redis_client.ping()
        logger.info("Redis connection established successfully")
    except redis.ConnectionError as e:
        logger.error(f"Redis connection error: {str(e)}")
        raise

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10)
)
async def set_cache(key: str, value: Any, expire: int = 300) -> bool:
    """
    Set a value in Redis cache with expiration (in seconds)
    Default expiration is 5 minutes
    """
    try:
        serialized_value = json.dumps(value)
        with redis_client.pipeline() as pipe:
            pipe.setex(key, expire, serialized_value)
            pipe.execute()
        return True
    except Exception as e:
        logger.error(f"Error setting cache: {str(e)}")
        return False

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10)
)
async def get_cache(key: str) -> Optional[Any]:
    """
    Get a value from Redis cache
    Returns None if key doesn't exist or has expired
    """
    try:
        value = redis_client.get(key)
        if value is None:
            return None
        return json.loads(value)
    except Exception as e:
        logger.error(f"Error getting cache: {str(e)}")
        return None

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10)
)
async def clear_cache() -> bool:
    """Clear all cache entries"""
    try:
        return redis_client.flushdb()
    except Exception as e:
        logger.error(f"Error clearing cache: {str(e)}")
        return False

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10)
)
async def delete_cache(key: str) -> bool:
    """Delete a specific cache entry"""
    try:
        return redis_client.delete(key) > 0
    except Exception as e:
        logger.error(f"Error deleting cache: {str(e)}")
        return False

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10)
)
async def get_cache_ttl(key: str) -> Optional[int]:
    """Get remaining TTL for a cache key"""
    try:
        return redis_client.ttl(key)
    except Exception as e:
        logger.error(f"Error getting cache TTL: {str(e)}")
        return None 