# app/redis_client.py
from redis.asyncio import Redis
from app.config import get_settings

settings = get_settings()

# Initialize Redis Client
redis_client = Redis(
    host="localhost", 
    port=6379, 
    decode_responses=True # automatically convert bytes to strings
)

async def init_redis():
    # Test connection
    await redis_client.ping()
    print("✅ Redis connected")

async def close_redis():
    await redis_client.close()