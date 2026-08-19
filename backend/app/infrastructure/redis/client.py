from redis.asyncio import from_url
from app.core.config import settings
r = from_url(settings.redis_url,decode_responses= True)
