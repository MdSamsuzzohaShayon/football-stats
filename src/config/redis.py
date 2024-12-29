import os
import redis.asyncio as redis
from redis.asyncio.client import Redis
from redis.asyncio.connection import ConnectionPool

redis_conn = redis.from_url(os.getenv("REDIS_HOST", None), encoding="utf-8", decode_responses=True)

# Create a Redis connection pool
redis_pool = ConnectionPool.from_url(f"{os.getenv('REDIS_HOST', None)}:{os.getenv('REDIS_PORT', None)}", db=0)


async def redis_connection() -> Redis:
    return redis_conn


# Function to get Redis client
async def get_redis() -> Redis:
    return redis.Redis(connection_pool=redis_pool)
