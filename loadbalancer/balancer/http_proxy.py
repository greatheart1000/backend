from flask import Flask, request, Response, jsonify, g
import requests
import logging
from typing import Dict, List, Optional, Any, Callable
from urllib.parse import urljoin, urlparse
import time
import threading
from flask import Flask, request, Response, jsonify
from algorithms.base import LoadBalancer, Backend
from discovery.registry import ServiceRegistry
from middleware.session import SessionManager
from middleware.circuit_breaker import CircuitBreaker
from middleware.rate_limiter import TokenBucketRateLimiter

logger = logging.getLogger(__name__)

class HTTPProxy:
    """HTTP反向代理负载均衡器"""
    
    def __init__(self, app: Flask, load_balancer: LoadBalancer):
        self.app = app
        self.load_balancer = load_balancer
        self.registry: Optional[ServiceRegistry] = None
        self.service_name: Optional[str] = None
        
        # 路由配置
        self.routes: Dict[str, 'RouteConfig'] = {}
        self.default_route: Optional['RouteConfig'] = None
        
        # 统计信息
        self.total_requests = 0
        self.successful_requests = 0
        self.failed_requests = 0
        self.total_response_time = 0
        self.stats_lock = threading.Lock()
        
        # 配置选项
        self.request_timeout = 30
        self.access_log_enabled = True
        self.session_timeout = 3600  # 1小时
        
        # HTTP会话
        self.session = requests.Session()
        self.session.timeout = self.request_timeout
        
        # 初始化中间件
        self.session_manager = SessionManager()
        self.circuit_breaker = CircuitBreaker()
        self.rate_limiter = TokenBucketRateLimiter(capacity=100, refill_rate=10.0)
        
        # 注册Flask路由处理器
        self._register_routes()
    
    def set_registry(self, registry: ServiceRegistry, service_name: str):
        """设置服务注册表"""
        self.registry = registry
        self.service_name = service_name
    
    def add_route(self, path: str, config: 'RouteConfig'):
        """添加路由规则"""
        config.path = path
        self.routes[path] = config
        logger.info(f"Added route: {path} -> {config.service_name}")
    
    def set_default_route(self, config: 'RouteConfig'):
        """设置默认路由"""
        self.default_route = config
        logger.info("Set default route")
    
    def set_request_timeout(self, timeout: int):
        """设置请求超时时间"""
        self.request_timeout = timeout
        self.session.timeout = timeout
    
    def enable_access_log(self, enable: bool):
        """启用/禁用访问日志"""
        self.access_log_enabled = enable
    
    def _register_routes(self):
        """注册Flask路由处理器"""
        # 代理所有路径
        @self.app.route('/', defaults={'path': ''}, methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS'])
        @self.app.route('/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS'])
        def proxy_handler(path):
            return self._handle_request(path)
        
        # 健康检查端点
        @self.app.route('/lb/health')
        def health_check():
            return jsonify({
                'status': 'healthy',
                'load_balancer': self.load_balancer.__class__.__name__,
                'timestamp': time.time()
            })
        
        # 统计信息端点
        @self.app.route('/lb/stats')
        def stats():
            return jsonify(self.get_stats())
        
        # 后端状态端点
        @self.app.route('/lb/backends')
        def backends():
            backends_info = []
            for backend in self.load_balancer.get_all_backends():
                backends_info.append(backend.to_dict())
            return jsonify(backends_info)
    
    def _handle_request(self, path: str) -> Response:
        """处理HTTP请求"""
        start_time = time.time()
        
        # 更新请求计数
        with self.stats_lock:
            self.total_requests += 1
        
        try:
            # 获取客户端IP
            client_ip = self._get_client_ip()
            
            # 应用限流
            if not self.rate_limiter.allow_request(client_ip):
                return Response("Rate limit exceeded", status=429)
            
            # 检查熔断器
            if not self.circuit_breaker.can_execute():
                return Response("Service temporarily unavailable", status=503)
            
            # 选择路由和负载均衡器
            route_config, lb = self._select_route(request.path)
            
            # 选择后端服务
            backend = lb.next_backend(client_ip)
            if not backend:
                self.circuit_breaker.record_failure()
                return Response("No healthy backend available", status=503)
            
            # 处理会话保持
            if route_config and route_config.enable_session_affinity:
                session_backend = self.session_manager.get_backend_for_session(
                    request, self.load_balancer
                )
                if session_backend and session_backend.is_healthy:
                    backend = session_backend
            
            # 增加后端活跃连接数
            backend.increment_active()
            
            try:
                # 构建目标URL
                target_url = self._build_target_url(backend, path, route_config)
                
                # 准备请求头
                headers = self._prepare_headers(route_config)
                
                # 发起代理请求
                response = self._make_proxy_request(target_url, headers, backend)
                
                # 应用响应处理
                flask_response = self._create_flask_response(response, route_config, backend)
                
                # 更新会话绑定
                if route_config and route_config.enable_session_affinity:
                    self.session_manager.bind_session_to_backend(request, backend)
                
                # 记录成功
                self.circuit_breaker.record_success()
                
                # 更新响应时间统计
                response_time = (time.time() - start_time) * 1000  # 毫秒
                if hasattr(self.load_balancer, 'update_response_time'):
                    self.load_balancer.update_response_time(backend.id, response_time)
                
                with self.stats_lock:
                    self.successful_requests += 1
                    self.total_response_time += response_time
                
                return flask_response
                
            finally:
                backend.decrement_active()
        
        except Exception as e:
            logger.error(f"Error handling request {request.path}: {e}")
            self.circuit_breaker.record_failure()
            
            with self.stats_lock:
                self.failed_requests += 1
            
            return Response("Internal server error", status=500)
        
        finally:
            # 记录访问日志
            if self.access_log_enabled:
                response_time = (time.time() - start_time) * 1000
                logger.info(f"{request.method} {request.path} {client_ip} {response_time:.2f}ms")
    
    def _get_client_ip(self) -> str:
        """获取客户端真实IP"""
        # 检查X-Forwarded-For头部
        xff = request.headers.get('X-Forwarded-For')
        if xff:
            return xff.split(',')[0].strip()
        
        # 检查X-Real-IP头部
        xri = request.headers.get('X-Real-IP')
        if xri:
            return xri
        
        # 使用remote_addr
        return request.remote_addr or '127.0.0.1'
    
    def _select_route(self, path: str) -> tuple:
        """选择路由和负载均衡器"""
        # 精确匹配
        if path in self.routes:
            route = self.routes[path]
            return route, route.load_balancer or self.load_balancer
        
        # 前缀匹配
        best_match = None
        max_len = 0
        
        for route_path, route in self.routes.items():
            if path.startswith(route_path) and len(route_path) > max_len:
                best_match = route
                max_len = len(route_path)
        
        if best_match:
            return best_match, best_match.load_balancer or self.load_balancer
        
        # 使用默认路由
        if self.default_route:
            return self.default_route, self.default_route.load_balancer or self.load_balancer
        
        # 使用全局负载均衡器
        return None, self.load_balancer
    
    def _build_target_url(self, backend: Backend, path: str, route_config: Optional['RouteConfig']) -> str:
        """构建目标URL"""
        # 应用路径重写
        if route_config and route_config.rewrite_path:
            path = route_config.rewrite_path
        
        # 保持查询参数
        if request.query_string:
            path += '?' + request.query_string.decode()
        
        return f"http://{backend.address}/{path.lstrip('/')}"
    
    def _prepare_headers(self, route_config: Optional['RouteConfig']) -> Dict[str, str]:
        """准备请求头"""
        headers = dict(request.headers)
        
        # 移除hop-by-hop头部
        hop_by_hop = {
            'connection', 'keep-alive', 'proxy-authenticate',
            'proxy-authorization', 'te', 'trailers', 'upgrade'
        }
        headers = {k: v for k, v in headers.items() if k.lower() not in hop_by_hop}
        
        # 设置代理相关头部
        headers['X-Forwarded-For'] = self._get_client_ip()
        headers['X-Forwarded-Host'] = request.host
        headers['X-Forwarded-Proto'] = request.scheme
        headers['X-Real-IP'] = self._get_client_ip()
        
        # 应用路由头部配置
        if route_config:
            # 添加头部
            if route_config.add_headers:
                headers.update(route_config.add_headers)
            
            # 移除头部
            if route_config.remove_headers:
                for header in route_config.remove_headers:
                    headers.pop(header, None)
        
        return headers
    
    def _make_proxy_request(self, target_url: str, headers: Dict[str, str], backend: Backend) -> requests.Response:
        """发起代理请求"""
        try:
            response = self.session.request(
                method=request.method,
                url=target_url,
                headers=headers,
                data=request.get_data(),
                allow_redirects=False,
                timeout=self.request_timeout
            )
            return response
            
        except requests.RequestException as e:
            logger.error(f"Proxy request failed to {backend.address}: {e}")
            # 标记后端为不健康
            if 'connection' in str(e).lower():
                backend.set_healthy(False)
            raise
    
    def _create_flask_response(self, proxy_response: requests.Response, 
                             route_config: Optional['RouteConfig'], backend: Backend) -> Response:
        """创建Flask响应"""
        # 准备响应头
        response_headers = dict(proxy_response.headers)
        
        # 移除hop-by-hop头部
        hop_by_hop = {
            'connection', 'keep-alive', 'proxy-authenticate',
            'proxy-authorization', 'te', 'trailers', 'upgrade',
            'transfer-encoding'
        }
        response_headers = {k: v for k, v in response_headers.items() if k.lower() not in hop_by_hop}
        
        # 添加负载均衡器信息
        response_headers['X-Load-Balancer'] = 'FlaskLB/1.0'
        response_headers['X-Backend-Server'] = backend.address
        
        # 应用CORS配置
        if route_config and route_config.enable_cors:
            response_headers.update({
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type, Authorization'
            })
        
        # 创建Flask响应
        flask_response = Response(
            proxy_response.content,
            status=proxy_response.status_code,
            headers=response_headers
        )
        
        return flask_response
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        with self.stats_lock:
            avg_response_time = (
                self.total_response_time / self.successful_requests 
                if self.successful_requests > 0 else 0
            )
            
            return {
                'load_balancer': self.load_balancer.__class__.__name__,
                'total_requests': self.total_requests,
                'successful_requests': self.successful_requests,
                'failed_requests': self.failed_requests,
                'success_rate': (
                    self.successful_requests / self.total_requests 
                    if self.total_requests > 0 else 0
                ),
                'average_response_time': avg_response_time,
                'circuit_breaker': self.circuit_breaker.get_stats(),
                'rate_limiter': self.rate_limiter.get_stats(),
                'backends': self.load_balancer.get_stats()
            }

class RouteConfig:
    """路由配置"""
    
    def __init__(self,
                 service_name: str,
                 load_balancer: Optional[LoadBalancer] = None,
                 rewrite_path: Optional[str] = None,
                 add_headers: Optional[Dict[str, str]] = None,
                 remove_headers: Optional[List[str]] = None,
                 enable_cors: bool = False,
                 enable_session_affinity: bool = False):
        self.service_name = service_name
        self.load_balancer = load_balancer
        self.rewrite_path = rewrite_path
        self.add_headers = add_headers or {}
        self.remove_headers = remove_headers or []
        self.enable_cors = enable_cors
        self.enable_session_affinity = enable_session_affinity
        self.path: Optional[str] = None  # 由add_route方法设置