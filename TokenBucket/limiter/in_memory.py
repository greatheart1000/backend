# limiter/in_memory.py
import time
import threading
import weakref

class TokenBucket:
    _lock = threading.Lock()

    def __init__(self, capacity: int, refill_rate: float):
        self.capacity = capacity
        self.refill_rate = refill_rate
        self.tokens = float(capacity)
        self.last = time.time()

    def _refill(self):
        now = time.time()
        delta = now - self.last
        self.tokens = min(self.capacity, self.tokens + delta * self.refill_rate)
        self.last = now

    def allow(self, tokens: int = 1) -> bool:
        with self._lock:
            self._refill()
            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            return False

# 全局弱引用缓存，避免内存泄漏
_buckets = {}

def get_bucket(key: str, capacity: int = 10, refill_rate: float = 1.0) -> TokenBucket:
    if key not in _buckets:
        _buckets[key] = TokenBucket(capacity, refill_rate)
    return _buckets[key]