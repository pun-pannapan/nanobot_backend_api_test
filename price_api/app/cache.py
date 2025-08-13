import os
import redis
import json

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
TTL = int(os.getenv("CACHE_TTL_SECONDS", "55"))
r = redis.Redis.from_url(REDIS_URL, decode_responses=True)

KEY_PREFIX = "price:"

def get_cached_price(symbol: str):
    data = r.get(KEY_PREFIX + symbol)
    return json.loads(data) if data else None

def set_cached_price(symbol: str, payload: dict):
    r.setex(KEY_PREFIX + symbol, TTL, json.dumps(payload))