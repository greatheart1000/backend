"""
限流器模块
实现多种限流算法：令牌桶、滑动窗口、漏桶等
"""

import time
import threading
from typing import Dict, Any, Optional, List
from collections import deque
from abc import ABC, abstractmethod


class RateLimiter(ABC):
    """限流器抽象基类"""
    
    @abstractmethod
    def allow_request(self, key: str = "default") -> bool:
        """
        检查是否允许请求
        
        Args:
            key: 限流key，用于区分不同的限流对象
            
        Returns:
            True表示允许，False表示被限流
        """
        pass
    
    @abstractmethod
    def get_stats(self) -> Dict[str, Any]:
        """获取限流统计信息"""
        pass


class TokenBucketRateLimiter(RateLimiter):
    """令牌桶限流器"""
    
    def __init__(self, capacity: int, refill_rate: float):
        """
        初始化令牌桶限流器
        
        Args:
            capacity: 桶容量（最大令牌数）
            refill_rate: 令牌补充速率（令牌/秒）
        """
        self.capacity = capacity
        self.refill_rate = refill_rate
        self.buckets: Dict[str, Dict[str, Any]] = {}
        self.lock = threading.Lock()
        
        # 统计信息
        self.total_requests = 0
        self.allowed_requests = 0
        self.rejected_requests = 0
    
    def allow_request(self, key: str = "default") -> bool:
        """检查是否允许请求"""
        with self.lock:
            current_time = time.time()
            self.total_requests += 1
            
            # 获取或创建桶
            if key not in self.buckets:
                self.buckets[key] = {
                    'tokens': self.capacity,
                    'last_refill': current_time
                }
            
            bucket = self.buckets[key]
            
            # 补充令牌
            time_passed = current_time - bucket['last_refill']
            tokens_to_add = time_passed * self.refill_rate
            bucket['tokens'] = min(self.capacity, bucket['tokens'] + tokens_to_add)
            bucket['last_refill'] = current_time
            
            # 检查是否有可用令牌
            if bucket['tokens'] >= 1:
                bucket['tokens'] -= 1
                self.allowed_requests += 1
                return True
            else:
                self.rejected_requests += 1
                return False
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        with self.lock:
            bucket_stats = {}
            for key, bucket in self.buckets.items():
                bucket_stats[key] = {
                    'tokens': bucket['tokens'],
                    'last_refill': bucket['last_refill']
                }
            
            return {
                'type': 'token_bucket',
                'capacity': self.capacity,
                'refill_rate': self.refill_rate,
                'total_requests': self.total_requests,
                'allowed_requests': self.allowed_requests,
                'rejected_requests': self.rejected_requests,
                'success_rate': self.allowed_requests / self.total_requests * 100 if self.total_requests > 0 else 0,
                'buckets': bucket_stats
            }


class SlidingWindowRateLimiter(RateLimiter):
    """滑动窗口限流器"""
    
    def __init__(self, max_requests: int, window_size: int):
        """
        初始化滑动窗口限流器
        
        Args:
            max_requests: 窗口内最大请求数
            window_size: 窗口大小（秒）
        """
        self.max_requests = max_requests
        self.window_size = window_size
        self.windows: Dict[str, deque] = {}
        self.lock = threading.Lock()
        
        # 统计信息
        self.total_requests = 0
        self.allowed_requests = 0
        self.rejected_requests = 0
    
    def allow_request(self, key: str = "default") -> bool:
        """检查是否允许请求"""
        with self.lock:
            current_time = time.time()
            self.total_requests += 1
            
            # 获取或创建窗口
            if key not in self.windows:
                self.windows[key] = deque()
            
            window = self.windows[key]
            
            # 清理过期请求
            cutoff_time = current_time - self.window_size
            while window and window[0] <= cutoff_time:
                window.popleft()
            
            # 检查是否超过限制
            if len(window) < self.max_requests:
                window.append(current_time)
                self.allowed_requests += 1
                return True
            else:
                self.rejected_requests += 1
                return False
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        with self.lock:
            current_time = time.time()
            window_stats = {}
            
            for key, window in self.windows.items():
                # 清理过期请求
                cutoff_time = current_time - self.window_size
                while window and window[0] <= cutoff_time:
                    window.popleft()
                
                window_stats[key] = {
                    'current_requests': len(window),
                    'max_requests': self.max_requests,
                    'utilization': len(window) / self.max_requests * 100
                }
            
            return {
                'type': 'sliding_window',
                'max_requests': self.max_requests,
                'window_size': self.window_size,
                'total_requests': self.total_requests,
                'allowed_requests': self.allowed_requests,
                'rejected_requests': self.rejected_requests,
                'success_rate': self.allowed_requests / self.total_requests * 100 if self.total_requests > 0 else 0,
                'windows': window_stats
            }


class LeakyBucketRateLimiter(RateLimiter):
    """漏桶限流器"""
    
    def __init__(self, capacity: int, leak_rate: float):
        """
        初始化漏桶限流器
        
        Args:
            capacity: 桶容量
            leak_rate: 漏水速率（请求/秒）
        """
        self.capacity = capacity
        self.leak_rate = leak_rate
        self.buckets: Dict[str, Dict[str, Any]] = {}
        self.lock = threading.Lock()
        
        # 统计信息
        self.total_requests = 0
        self.allowed_requests = 0
        self.rejected_requests = 0
    
    def allow_request(self, key: str = "default") -> bool:
        """检查是否允许请求"""
        with self.lock:
            current_time = time.time()
            self.total_requests += 1
            
            # 获取或创建桶
            if key not in self.buckets:
                self.buckets[key] = {
                    'level': 0,
                    'last_leak': current_time
                }
            
            bucket = self.buckets[key]
            
            # 漏水
            time_passed = current_time - bucket['last_leak']
            leak_amount = time_passed * self.leak_rate
            bucket['level'] = max(0, bucket['level'] - leak_amount)
            bucket['last_leak'] = current_time
            
            # 检查是否可以添加请求
            if bucket['level'] < self.capacity:
                bucket['level'] += 1
                self.allowed_requests += 1
                return True
            else:
                self.rejected_requests += 1
                return False
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        with self.lock:
            bucket_stats = {}
            for key, bucket in self.buckets.items():
                bucket_stats[key] = {
                    'level': bucket['level'],
                    'capacity': self.capacity,
                    'utilization': bucket['level'] / self.capacity * 100,
                    'last_leak': bucket['last_leak']
                }
            
            return {
                'type': 'leaky_bucket',
                'capacity': self.capacity,
                'leak_rate': self.leak_rate,
                'total_requests': self.total_requests,
                'allowed_requests': self.allowed_requests,
                'rejected_requests': self.rejected_requests,
                'success_rate': self.allowed_requests / self.total_requests * 100 if self.total_requests > 0 else 0,
                'buckets': bucket_stats
            }


class CompositeRateLimiter(RateLimiter):
    """组合限流器 - 可以组合多个限流器"""
    
    def __init__(self, limiters: List[RateLimiter], strategy: str = "all"):
        """
        初始化组合限流器
        
        Args:
            limiters: 限流器列表
            strategy: 组合策略 - "all"表示所有限流器都必须通过，"any"表示任一限流器通过即可
        """
        self.limiters = limiters
        self.strategy = strategy
        
        # 统计信息
        self.total_requests = 0
        self.allowed_requests = 0
        self.rejected_requests = 0
    
    def allow_request(self, key: str = "default") -> bool:
        """检查是否允许请求"""
        self.total_requests += 1
        
        if self.strategy == "all":
            # 所有限流器都必须允许
            for limiter in self.limiters:
                if not limiter.allow_request(key):
                    self.rejected_requests += 1
                    return False
            self.allowed_requests += 1
            return True
        
        elif self.strategy == "any":
            # 任一限流器允许即可
            for limiter in self.limiters:
                if limiter.allow_request(key):
                    self.allowed_requests += 1
                    return True
            self.rejected_requests += 1
            return False
        
        else:
            raise ValueError(f"Unknown strategy: {self.strategy}")
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        limiter_stats = []
        for i, limiter in enumerate(self.limiters):
            limiter_stats.append({
                'index': i,
                'type': limiter.__class__.__name__,
                'stats': limiter.get_stats()
            })
        
        return {
            'type': 'composite',
            'strategy': self.strategy,
            'limiter_count': len(self.limiters),
            'total_requests': self.total_requests,
            'allowed_requests': self.allowed_requests,
            'rejected_requests': self.rejected_requests,
            'success_rate': self.allowed_requests / self.total_requests * 100 if self.total_requests > 0 else 0,
            'limiters': limiter_stats
        }


class RateLimiterManager:
    """限流器管理器"""
    
    def __init__(self):
        self.limiters: Dict[str, RateLimiter] = {}
        self.lock = threading.Lock()
    
    def create_token_bucket(self, name: str, capacity: int, refill_rate: float) -> TokenBucketRateLimiter:
        """创建令牌桶限流器"""
        with self.lock:
            limiter = TokenBucketRateLimiter(capacity, refill_rate)
            self.limiters[name] = limiter
            return limiter
    
    def create_sliding_window(self, name: str, max_requests: int, window_size: int) -> SlidingWindowRateLimiter:
        """创建滑动窗口限流器"""
        with self.lock:
            limiter = SlidingWindowRateLimiter(max_requests, window_size)
            self.limiters[name] = limiter
            return limiter
    
    def create_leaky_bucket(self, name: str, capacity: int, leak_rate: float) -> LeakyBucketRateLimiter:
        """创建漏桶限流器"""
        with self.lock:
            limiter = LeakyBucketRateLimiter(capacity, leak_rate)
            self.limiters[name] = limiter
            return limiter
    
    def create_composite(self, name: str, limiters: List[RateLimiter], strategy: str = "all") -> CompositeRateLimiter:
        """创建组合限流器"""
        with self.lock:
            limiter = CompositeRateLimiter(limiters, strategy)
            self.limiters[name] = limiter
            return limiter
    
    def get_limiter(self, name: str) -> Optional[RateLimiter]:
        """获取指定名称的限流器"""
        with self.lock:
            return self.limiters.get(name)
    
    def remove_limiter(self, name: str):
        """移除指定的限流器"""
        with self.lock:
            self.limiters.pop(name, None)
    
    def get_all_stats(self) -> Dict[str, Dict[str, Any]]:
        """获取所有限流器的统计信息"""
        with self.lock:
            return {name: limiter.get_stats() 
                   for name, limiter in self.limiters.items()}


# 全局限流器管理器实例
limiter_manager = RateLimiterManager()

# 创建默认的限流器实例 (为了兼容HTTP代理中的直接使用)
default_rate_limiter = TokenBucketRateLimiter(capacity=100, refill_rate=10.0)