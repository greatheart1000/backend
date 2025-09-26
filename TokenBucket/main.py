# main.py
from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from fastapi import HTTPException
import os

# 选择启用哪种限流方式
USE_REDIS = os.getenv("USE_REDIS", "false").lower() == "true"
print('USE_REDIS' ,USE_REDIS )

if USE_REDIS:#方案B：Redis 令牌桶
    from limiter.redis_bucket import allow_user
else: # 方案A：纯内存令牌桶
    from limiter.in_memory import get_bucket

app = FastAPI()

@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    # 提取用户标识：优先 header 中的 user-id，否则用客户端 IP
    user_id = request.headers.get("x-user-id") or request.client.host

    # 设置限流规则（可按接口动态调整）
    capacity = 10      # 桶容量
    refill_rate = 2.0  # 每秒补充 2 个令牌

    if USE_REDIS:
        allowed = allow_user(user_id, capacity=capacity, refill_rate=refill_rate)
    else:
        bucket = get_bucket(user_id, capacity=capacity, refill_rate=refill_rate)
        allowed = bucket.allow()

    if not allowed:
        return JSONResponse(
            status_code=429,
            content={"detail": "Too Many Requests. Please try again later."}
        )

    response = await call_next(request)
    return response

# --- 测试接口 ---
@app.get("/ping")
def ping():
    return {"message": "pong"}

@app.get("/hello")
def hello():
    return {"msg": "Hello, I'm rate-limited!"}