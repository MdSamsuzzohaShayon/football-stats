import redis.asyncio as redis
from redis.asyncio.client import Redis
from redis.asyncio.connection import ConnectionPool

redis_conn = redis.from_url("redis://localhost", encoding="utf-8", decode_responses=True)

# Create a Redis connection pool
redis_pool = ConnectionPool.from_url("redis://localhost:6379", db=0)


async def redis_connection() -> Redis:
    return redis_conn


# Function to get Redis client
async def get_redis() -> Redis:
    return redis.Redis(connection_pool=redis_pool)
