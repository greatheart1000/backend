import time
import json
import jieba
import redis

# Redis 连接
r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)

# 热词 Sorted Set 的 key
HOTWORD_ZSET = "nlp:hotwords:zset"
# 缓存热词列表的 key
HOTWORD_CACHE = "nlp:hotwords:cache"
# 缓存 TTL（秒）
HOTWORD_CACHE_TTL = 60
# 保留的热门关键词数量
TOP_N = 10

def extract_keywords(text):
    """
    简单用 jieba 分词并去掉长度<2 的词
    真实场景可接入更复杂的 NLP 提取器
    """
    words = jieba.cut_for_search(text)
    return [w for w in words if len(w) > 1]

def record_query(text):
    """
    处理一条用户提问：
      1) 提取关键词
      2) 更新 zset 计数
      3) 删除热词缓存，让下次 get_hotwords() 重建
    """
    kws = extract_keywords(text)
    pipe = r.pipeline()
    for w in kws:
        pipe.zincrby(HOTWORD_ZSET, 1, w)
    # 标记缓存失效
    pipe.delete(HOTWORD_CACHE)
    pipe.execute()

def get_hotwords(n=TOP_N):
    """
    获取热门关键词列表：
      1) 尝试从缓存读
      2) 缓存未命中，则从 zset 拿 top-n 并缓存
    """
    cached = r.get(HOTWORD_CACHE)
    if cached:
        return json.loads(cached)

    # 缓存 miss，取 top-n（分数最高的 n 个）
    top = r.zrevrange(HOTWORD_ZSET, 0, n-1, withscores=True)
    result = [{"word": w, "count": int(score)} for w, score in top]

    # 写入缓存
    r.set(HOTWORD_CACHE, json.dumps(result, ensure_ascii=False), ex=HOTWORD_CACHE_TTL)
    return result

if __name__ == "__main__":
    # 模拟一批用户提问
    queries = [
        "我想查询订单状态",
        "退货流程怎么走？",
        "订单为什么迟迟未发货",
        "如何修改收货地址",
        "能否帮我查询一下退款进度",
        "订单状态 查询",
    ]
    for q in queries:
        record_query(q)
        time.sleep(0.1)

    # 第一次获取（会走 zset 并缓存）
    print("HotWords:", get_hotwords())

    # 再次获取（走缓存，不再访问 zset，快速响应）
    print("HotWords(cached):", get_hotwords())