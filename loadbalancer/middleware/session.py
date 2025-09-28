"""
会话管理器
实现会话保持和亲和性功能
"""

import time
import hashlib
import threading
from typing import Dict, Optional, Any
from flask import Request
from algorithms.base import Backend, LoadBalancer


class SessionManager:
    """会话管理器 - 实现会话保持功能"""
    
    def __init__(self, session_timeout: int = 3600):
        """
        初始化会话管理器
        
        Args:
            session_timeout: 会话超时时间（秒）
        """
        self.session_timeout = session_timeout
        self.sessions: Dict[str, Dict[str, Any]] = {}
        self.lock = threading.RWLock()
        
        # 定期清理过期会话
        self.cleanup_thread = threading.Thread(target=self._cleanup_expired_sessions, daemon=True)
        self.cleanup_thread.start()
    
    def get_session_id(self, request: Request) -> str:
        """
        获取会话ID
        
        Args:
            request: Flask请求对象
            
        Returns:
            会话ID字符串
        """
        # 优先从Cookie中获取会话ID
        session_id = request.cookies.get('LB_SESSION_ID')
        if session_id:
            return session_id
        
        # 从请求头中获取
        session_id = request.headers.get('X-Session-ID')
        if session_id:
            return session_id
        
        # 基于客户端IP和User-Agent生成会话ID
        client_ip = self._get_client_ip(request)
        user_agent = request.headers.get('User-Agent', '')
        
        session_key = f"{client_ip}:{user_agent}"
        session_id = hashlib.md5(session_key.encode()).hexdigest()
        
        return session_id
    
    def get_backend_for_session(self, request: Request, load_balancer: LoadBalancer) -> Optional[Backend]:
        """
        获取会话绑定的后端服务器
        
        Args:
            request: Flask请求对象
            load_balancer: 负载均衡器
            
        Returns:
            绑定的后端服务器，如果没有则返回None
        """
        session_id = self.get_session_id(request)
        
        with self.lock.read_lock():
            session_data = self.sessions.get(session_id)
            if not session_data:
                return None
            
            # 检查会话是否过期
            if time.time() - session_data['created_at'] > self.session_timeout:
                return None
            
            backend_id = session_data.get('backend_id')
            if not backend_id:
                return None
            
            # 查找对应的后端
            for backend in load_balancer.get_all_backends():
                if backend.id == backend_id and backend.is_healthy:
                    # 更新最后访问时间
                    session_data['last_accessed'] = time.time()
                    return backend
            
            return None
    
    def bind_session_to_backend(self, request: Request, backend: Backend) -> str:
        """
        将会话绑定到指定的后端服务器
        
        Args:
            request: Flask请求对象
            backend: 要绑定的后端服务器
            
        Returns:
            会话ID
        """
        session_id = self.get_session_id(request)
        current_time = time.time()
        
        with self.lock.write_lock():
            self.sessions[session_id] = {
                'backend_id': backend.id,
                'backend_address': f"{backend.host}:{backend.port}",
                'created_at': current_time,
                'last_accessed': current_time,
                'request_count': self.sessions.get(session_id, {}).get('request_count', 0) + 1
            }
        
        return session_id
    
    def remove_session(self, session_id: str):
        """
        移除指定的会话
        
        Args:
            session_id: 会话ID
        """
        with self.lock.write_lock():
            self.sessions.pop(session_id, None)
    
    def clear_sessions_for_backend(self, backend_id: str):
        """
        清除绑定到指定后端的所有会话
        
        Args:
            backend_id: 后端服务器ID
        """
        with self.lock.write_lock():
            sessions_to_remove = []
            for session_id, session_data in self.sessions.items():
                if session_data.get('backend_id') == backend_id:
                    sessions_to_remove.append(session_id)
            
            for session_id in sessions_to_remove:
                del self.sessions[session_id]
    
    def get_session_stats(self) -> Dict[str, Any]:
        """
        获取会话统计信息
        
        Returns:
            会话统计数据
        """
        with self.lock.read_lock():
            active_sessions = len(self.sessions)
            backend_distribution = {}
            
            for session_data in self.sessions.values():
                backend_id = session_data.get('backend_id')
                if backend_id:
                    backend_distribution[backend_id] = backend_distribution.get(backend_id, 0) + 1
            
            return {
                'active_sessions': active_sessions,
                'backend_distribution': backend_distribution,
                'session_timeout': self.session_timeout
            }
    
    def _get_client_ip(self, request: Request) -> str:
        """获取客户端真实IP"""
        # 检查X-Forwarded-For头部
        xff = request.headers.get('X-Forwarded-For')
        if xff:
            return xff.split(',')[0].strip()
        
        # 检查X-Real-IP头部
        real_ip = request.headers.get('X-Real-IP')
        if real_ip:
            return real_ip
        
        # 使用远程地址
        return request.remote_addr or '127.0.0.1'
    
    def _cleanup_expired_sessions(self):
        """定期清理过期会话"""
        while True:
            try:
                current_time = time.time()
                expired_sessions = []
                
                with self.lock.read_lock():
                    for session_id, session_data in self.sessions.items():
                        if current_time - session_data['last_accessed'] > self.session_timeout:
                            expired_sessions.append(session_id)
                
                if expired_sessions:
                    with self.lock.write_lock():
                        for session_id in expired_sessions:
                            self.sessions.pop(session_id, None)
                    
                    print(f"Cleaned up {len(expired_sessions)} expired sessions")
                
                # 每5分钟清理一次
                time.sleep(300)
                
            except Exception as e:
                print(f"Error in session cleanup: {e}")
                time.sleep(60)  # 出错时等待1分钟后重试


class ReadWriteLock:
    """读写锁实现"""
    
    def __init__(self):
        self._readers = 0
        self._writers = 0
        self._read_ready = threading.Condition(threading.RLock())
        self._write_ready = threading.Condition(threading.RLock())
    
    def read_lock(self):
        """获取读锁"""
        return self._ReadLock(self)
    
    def write_lock(self):
        """获取写锁"""
        return self._WriteLock(self)
    
    class _ReadLock:
        def __init__(self, rwlock):
            self.rwlock = rwlock
        
        def __enter__(self):
            with self.rwlock._read_ready:
                while self.rwlock._writers > 0:
                    self.rwlock._read_ready.wait()
                self.rwlock._readers += 1
        
        def __exit__(self, exc_type, exc_val, exc_tb):
            with self.rwlock._read_ready:
                self.rwlock._readers -= 1
                if self.rwlock._readers == 0:
                    self.rwlock._read_ready.notifyAll()
    
    class _WriteLock:
        def __init__(self, rwlock):
            self.rwlock = rwlock
        
        def __enter__(self):
            with self.rwlock._write_ready:
                while self.rwlock._writers > 0 or self.rwlock._readers > 0:
                    self.rwlock._write_ready.wait()
                self.rwlock._writers += 1
        
        def __exit__(self, exc_type, exc_val, exc_tb):
            with self.rwlock._write_ready:
                self.rwlock._writers -= 1
                self.rwlock._write_ready.notifyAll()


# 修正threading模块没有RWLock的问题
threading.RWLock = ReadWriteLock