"""
熔断器模块
实现熔断器模式，防止系统雪崩
"""

import time
import threading
from typing import Dict, Any, Optional
from enum import Enum


class CircuitState(Enum):
    """熔断器状态"""
    CLOSED = "closed"      # 关闭状态 - 正常处理请求
    OPEN = "open"          # 开启状态 - 拒绝所有请求
    HALF_OPEN = "half_open"  # 半开状态 - 允许少量请求测试


class CircuitBreaker:
    """熔断器实现"""
    
    def __init__(self, 
                 failure_threshold: int = 5,        # 失败阈值
                 success_threshold: int = 3,        # 成功阈值
                 timeout: int = 60,                 # 超时时间（秒）
                 window_size: int = 60):            # 滑动窗口大小（秒）
        """
        初始化熔断器
        
        Args:
            failure_threshold: 失败次数阈值，达到此值时开启熔断器
            success_threshold: 半开状态下连续成功次数阈值，达到此值时关闭熔断器
            timeout: 熔断器开启后的超时时间，超时后转为半开状态
            window_size: 统计窗口大小（秒）
        """
        self.failure_threshold = failure_threshold
        self.success_threshold = success_threshold
        self.timeout = timeout
        self.window_size = window_size
        
        # 熔断器状态
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = 0
        self.last_success_time = 0
        self.next_attempt_time = 0
        
        # 统计信息
        self.total_requests = 0
        self.total_failures = 0
        self.total_successes = 0
        
        # 滑动窗口统计
        self.request_history = []  # (timestamp, success)的元组列表
        
        # 线程锁
        self.lock = threading.Lock()
    
    def can_execute(self) -> bool:
        """
        检查是否可以执行请求
        
        Returns:
            True表示可以执行，False表示被熔断
        """
        with self.lock:
            current_time = time.time()
            
            # 清理过期的历史记录
            self._cleanup_history(current_time)
            
            if self.state == CircuitState.CLOSED:
                return True
            
            elif self.state == CircuitState.OPEN:
                # 检查是否到达重试时间
                if current_time >= self.next_attempt_time:
                    self.state = CircuitState.HALF_OPEN
                    self.success_count = 0
                    return True
                return False
            
            elif self.state == CircuitState.HALF_OPEN:
                return True
            
            return False
    
    def record_success(self):
        """记录成功的请求"""
        with self.lock:
            current_time = time.time()
            self.last_success_time = current_time
            self.total_requests += 1
            self.total_successes += 1
            
            # 添加到历史记录
            self.request_history.append((current_time, True))
            self._cleanup_history(current_time)
            
            if self.state == CircuitState.HALF_OPEN:
                self.success_count += 1
                if self.success_count >= self.success_threshold:
                    self._close_circuit()
            
            elif self.state == CircuitState.CLOSED:
                # 在关闭状态下，成功请求可以重置失败计数
                self.failure_count = max(0, self.failure_count - 1)
    
    def record_failure(self):
        """记录失败的请求"""
        with self.lock:
            current_time = time.time()
            self.last_failure_time = current_time
            self.total_requests += 1
            self.total_failures += 1
            
            # 添加到历史记录
            self.request_history.append((current_time, False))
            self._cleanup_history(current_time)
            
            if self.state == CircuitState.CLOSED:
                self.failure_count += 1
                
                # 检查是否需要开启熔断器
                recent_failures = self._count_recent_failures(current_time)
                if recent_failures >= self.failure_threshold:
                    self._open_circuit(current_time)
            
            elif self.state == CircuitState.HALF_OPEN:
                # 半开状态下的失败会立即开启熔断器
                self._open_circuit(current_time)
    
    def get_state(self) -> CircuitState:
        """获取当前熔断器状态"""
        return self.state
    
    def get_stats(self) -> Dict[str, Any]:
        """
        获取熔断器统计信息
        
        Returns:
            统计信息字典
        """
        with self.lock:
            current_time = time.time()
            self._cleanup_history(current_time)
            
            recent_requests = len(self.request_history)
            recent_failures = self._count_recent_failures(current_time)
            recent_successes = recent_requests - recent_failures
            
            failure_rate = (recent_failures / recent_requests * 100) if recent_requests > 0 else 0
            
            return {
                'state': self.state.value,
                'failure_threshold': self.failure_threshold,
                'success_threshold': self.success_threshold,
                'timeout': self.timeout,
                'window_size': self.window_size,
                'failure_count': self.failure_count,
                'success_count': self.success_count,
                'total_requests': self.total_requests,
                'total_failures': self.total_failures,
                'total_successes': self.total_successes,
                'recent_requests': recent_requests,
                'recent_failures': recent_failures,
                'recent_successes': recent_successes,
                'failure_rate': failure_rate,
                'last_failure_time': self.last_failure_time,
                'last_success_time': self.last_success_time,
                'next_attempt_time': self.next_attempt_time if self.state == CircuitState.OPEN else None
            }
    
    def force_open(self):
        """强制开启熔断器"""
        with self.lock:
            self._open_circuit(time.time())
    
    def force_close(self):
        """强制关闭熔断器"""
        with self.lock:
            self._close_circuit()
    
    def reset(self):
        """重置熔断器状态"""
        with self.lock:
            self.state = CircuitState.CLOSED
            self.failure_count = 0
            self.success_count = 0
            self.last_failure_time = 0
            self.last_success_time = 0
            self.next_attempt_time = 0
            self.total_requests = 0
            self.total_failures = 0
            self.total_successes = 0
            self.request_history.clear()
    
    def _open_circuit(self, current_time: float):
        """开启熔断器"""
        self.state = CircuitState.OPEN
        self.next_attempt_time = current_time + self.timeout
        print(f"Circuit breaker opened at {time.ctime(current_time)}, "
              f"next attempt at {time.ctime(self.next_attempt_time)}")
    
    def _close_circuit(self):
        """关闭熔断器"""
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        print(f"Circuit breaker closed at {time.ctime()}")
    
    def _cleanup_history(self, current_time: float):
        """清理过期的历史记录"""
        cutoff_time = current_time - self.window_size
        self.request_history = [
            (timestamp, success) for timestamp, success in self.request_history
            if timestamp > cutoff_time
        ]
    
    def _count_recent_failures(self, current_time: float) -> int:
        """统计最近窗口内的失败次数"""
        cutoff_time = current_time - self.window_size
        return sum(1 for timestamp, success in self.request_history
                  if timestamp > cutoff_time and not success)


class CircuitBreakerManager:
    """熔断器管理器 - 管理多个熔断器实例"""
    
    def __init__(self):
        self.breakers: Dict[str, CircuitBreaker] = {}
        self.lock = threading.Lock()
    
    def get_breaker(self, name: str, **kwargs) -> CircuitBreaker:
        """
        获取指定名称的熔断器，如果不存在则创建
        
        Args:
            name: 熔断器名称
            **kwargs: 熔断器配置参数
            
        Returns:
            熔断器实例
        """
        with self.lock:
            if name not in self.breakers:
                self.breakers[name] = CircuitBreaker(**kwargs)
            return self.breakers[name]
    
    def remove_breaker(self, name: str):
        """移除指定的熔断器"""
        with self.lock:
            self.breakers.pop(name, None)
    
    def get_all_stats(self) -> Dict[str, Dict[str, Any]]:
        """获取所有熔断器的统计信息"""
        with self.lock:
            return {name: breaker.get_stats() 
                   for name, breaker in self.breakers.items()}
    
    def reset_all(self):
        """重置所有熔断器"""
        with self.lock:
            for breaker in self.breakers.values():
                breaker.reset()


# 全局熔断器管理器实例
breaker_manager = CircuitBreakerManager()