# limiter/redis_bucket.py
import redis
import time

# 建议通过配置传入 host/port
r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True, socket_connect_timeout=5)

TOKEN_BUCKET_LUA = """
local key = KEYS[1]
local capacity = tonumber(ARGV[1])
local rate     = tonumber(ARGV[2])
local now      = tonumber(ARGV[3])
local requested= tonumber(ARGV[4])

local bucket = redis.call('hmget', key, 'tokens', 'last')
local tokens = tonumber(bucket[1]) or capacity
local last   = tonumber(bucket[2]) or now

tokens = math.min(capacity, tokens + (now - last) * rate)

if tokens >= requested then
    tokens = tokens - requested
    redis.call('hmset', key, 'tokens', tokens, 'last', now)
    redis.call('expire', key, 3600)  -- 自动过期，避免垃圾数据
    return 1
else
    redis.call('hmset', key, 'tokens', tokens, 'last', now)
    redis.call('expire', key, 3600)
    return 0
end
"""

# 缓存 Lua 脚本 SHA（可选优化）
lua_script = r.register_script(TOKEN_BUCKET_LUA)

def allow_user(user_id: str,
               capacity: int = 10,
               refill_rate: float = 1.0,
               requested: int = 1) -> bool:
    key = f"tb:{user_id}"
    now = time.time()
    try:
        result = r.eval(TOKEN_BUCKET_LUA, 1, key, capacity, refill_rate, now, requested)
        return bool(result)
    except redis.RedisError as e:
        print(f"Redis error in rate limit: {e}")
        return True  # 失败开放（fail-open），或改为拒绝（fail-close）根据业务决定