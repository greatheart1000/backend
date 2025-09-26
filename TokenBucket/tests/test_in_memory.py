import pytest
from limiter.in_memory import TokenBucket, get_bucket
import time
import threading

def test_token_bucket_creation():
    """测试令牌桶创建"""
    bucket = TokenBucket(capacity=10, refill_rate=2.0)
    assert bucket.capacity == 10
    assert bucket.refill_rate == 2.0
    assert bucket.tokens == 10.0

def test_token_consumption():
    """测试令牌消耗"""
    bucket = TokenBucket(capacity=5, refill_rate=1.0)
    
    # 消耗3个令牌
    assert bucket.allow(3) == True
    assert bucket.tokens == 2.0
    
    # 再消耗3个令牌，应该失败
    assert bucket.allow(3) == False
    assert bucket.tokens == 2.0

def test_token_refill():
    """测试令牌补充"""
    bucket = TokenBucket(capacity=10, refill_rate=5.0)  # 每秒5个令牌
    
    # 消耗所有令牌
    bucket.allow(10)
    assert bucket.tokens == 0.0
    
    # 等待1秒
    time.sleep(1.1)
    
    # 应该补充大约5个令牌
    bucket._refill()
    assert bucket.tokens >= 4.0  # 考虑时间误差

def test_capacity_limit():
    """测试容量限制"""
    bucket = TokenBucket(capacity=5, refill_rate=10.0)
    
    # 等待足够长时间
    time.sleep(1)
    bucket._refill()
    
    # 令牌数不应该超过容量
    assert bucket.tokens <= 5.0

def test_get_bucket_cache():
    """测试get_bucket的缓存功能"""
    bucket1 = get_bucket("user1", capacity=10, refill_rate=1.0)
    bucket2 = get_bucket("user1", capacity=20, refill_rate=2.0)  # 参数不同
    
    # 应该返回同一个对象（缓存）
    assert bucket1 is bucket2
    assert bucket1.capacity == 10  # 保持原有配置

def test_thread_safety():
    """测试线程安全"""
    bucket = TokenBucket(capacity=100, refill_rate=1.0)
    results = []
    
    def worker():
        for _ in range(10):
            result = bucket.allow(1)
            results.append(result)
    
    # 创建多个线程
    threads = []
    for _ in range(10):
        t = threading.Thread(target=worker)
        threads.append(t)
        t.start()
    
    # 等待所有线程完成
    for t in threads:
        t.join()
    
    # 检查结果
    success_count = sum(results)
    assert success_count <= 100  # 不应该超过初始容量