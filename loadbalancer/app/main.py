"""
Flask负载均衡器主应用
提供完整的负载均衡功能
"""

from flask import Flask, request, jsonify
import logging
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from balancer.http_proxy import HTTPProxy, RouteConfig
from algorithms.round_robin import RoundRobinBalancer
from algorithms.weighted import WeightedRoundRobinBalancer
from algorithms.ip_hash import IPHashBalancer
from algorithms.least_connections import LeastConnectionsBalancer
from algorithms.base import Backend
from discovery.registry import InMemoryServiceRegistry, ServiceInstance, ServiceStatus
from discovery.health import HTTPHealthChecker

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_app(config=None):
    """创建Flask应用"""
    app = Flask(__name__)
    
    # 默认配置
    default_config = {
        'LOAD_BALANCER_ALGORITHM': 'round_robin',
        'HEALTH_CHECK_INTERVAL': 30,
        'REQUEST_TIMEOUT': 30,
        'ENABLE_ACCESS_LOG': True,
        'SESSION_TIMEOUT': 3600
    }
    
    if config:
        default_config.update(config)
    
    app.config.update(default_config)
    
    # 创建后端服务器列表（示例）
    backends = [
        Backend('backend1', 'localhost', 8001, weight=1),
        Backend('backend2', 'localhost', 8002, weight=2),
        Backend('backend3', 'localhost', 8003, weight=1),
    ]
    
    # 创建负载均衡器
    algorithm = app.config['LOAD_BALANCER_ALGORITHM']
    if algorithm == 'round_robin':
        lb = RoundRobinBalancer()
    elif algorithm == 'weighted_round_robin':
        lb = WeightedRoundRobinBalancer()
    elif algorithm == 'ip_hash':
        lb = IPHashBalancer()
    elif algorithm == 'least_connections':
        lb = LeastConnectionsBalancer()
    else:
        logger.warning(f"Unknown algorithm {algorithm}, using round_robin")
        lb = RoundRobinBalancer()
    
    # 添加后端服务器
    for backend in backends:
        lb.add_backend(backend)
    
    logger.info(f"Created load balancer: {lb.__class__.__name__} with {len(backends)} backends")
    
    # 创建服务注册表和健康检查器
    registry = InMemoryServiceRegistry()
    health_checker = HTTPHealthChecker(registry, check_interval=app.config['HEALTH_CHECK_INTERVAL'])
    
    # 添加实例到健康检查器并启动
    for backend in backends:
        instance = ServiceInstance(
            id=backend.id,
            name='web-service',
            host=backend.host,
            port=backend.port,
            weight=backend.weight,
            status=ServiceStatus.HEALTHY
        )
        registry.register(instance)
        health_checker.add_instance(instance)
    
    # 启动健康检查
    health_checker.start()
    
    # 创建HTTP代理
    http_proxy = HTTPProxy(app, lb)
    http_proxy.set_registry(registry, 'web-service')
    http_proxy.set_request_timeout(app.config['REQUEST_TIMEOUT'])
    http_proxy.enable_access_log(app.config['ENABLE_ACCESS_LOG'])
    
    # 配置路由规则（示例）
    api_route = RouteConfig(
        service_name='api-service',
        rewrite_path='/api/v1/',
        add_headers={'X-Service': 'API'},
        enable_cors=True
    )
    http_proxy.add_route('/api', api_route)
    
    admin_route = RouteConfig(
        service_name='admin-service',
        rewrite_path='/admin/',
        add_headers={'X-Service': 'Admin'},
        enable_session_affinity=True
    )
    http_proxy.add_route('/admin', admin_route)
    
    # 设置默认路由
    default_route = RouteConfig(
        service_name='web-service',
        enable_cors=False
    )
    http_proxy.set_default_route(default_route)
    
    # 添加管理接口
    @app.route('/lb/config')
    def get_config():
        """获取负载均衡器配置"""
        return jsonify({
            'algorithm': lb.__class__.__name__,
            'backend_count': len(lb.get_all_backends()),
            'config': dict(app.config)
        })
    
    @app.route('/lb/backends/add', methods=['POST'])
    def add_backend():
        """添加后端服务器"""
        data = request.json
        if not data or 'host' not in data or 'port' not in data:
            return jsonify({'error': 'Missing host or port'}), 400
        
        backend_id = data.get('id', f"{data['host']}_{data['port']}")
        weight = data.get('weight', 1)
        
        backend = Backend(backend_id, data['host'], data['port'], weight)
        lb.add_backend(backend)
        
        # 注册到服务发现
        instance = ServiceInstance(
            id=backend.id,
            name='web-service',
            host=backend.host,
            port=backend.port,
            weight=backend.weight,
            status=ServiceStatus.HEALTHY
        )
        registry.register(instance)
        
        logger.info(f"Added backend: {backend.address}")
        return jsonify({'message': 'Backend added successfully', 'backend': backend.to_dict()})
    
    @app.route('/lb/backends/<backend_id>/remove', methods=['DELETE'])
    def remove_backend(backend_id):
        """移除后端服务器"""
        removed = lb.remove_backend(backend_id)
        if removed:
            registry.deregister(backend_id)
            logger.info(f"Removed backend: {backend_id}")
            return jsonify({'message': 'Backend removed successfully'})
        else:
            return jsonify({'error': 'Backend not found'}), 404
    
    @app.route('/lb/backends/<backend_id>/enable', methods=['POST'])
    def enable_backend(backend_id):
        """启用后端服务器"""
        backend = lb.get_backend(backend_id)
        if backend:
            backend.set_healthy(True)
            logger.info(f"Enabled backend: {backend_id}")
            return jsonify({'message': 'Backend enabled successfully'})
        else:
            return jsonify({'error': 'Backend not found'}), 404
    
    @app.route('/lb/backends/<backend_id>/disable', methods=['POST'])
    def disable_backend(backend_id):
        """禁用后端服务器"""
        backend = lb.get_backend(backend_id)
        if backend:
            backend.set_healthy(False)
            logger.info(f"Disabled backend: {backend_id}")
            return jsonify({'message': 'Backend disabled successfully'})
        else:
            return jsonify({'error': 'Backend not found'}), 404
    
    return app


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Flask Load Balancer')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind to')
    parser.add_argument('--port', type=int, default=8080, help='Port to bind to')
    parser.add_argument('--algorithm', choices=['round_robin', 'weighted_round_robin', 'ip_hash', 'least_connections'],
                       default='round_robin', help='Load balancing algorithm')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    
    args = parser.parse_args()
    
    # 创建配置
    config = {
        'LOAD_BALANCER_ALGORITHM': args.algorithm,
        'DEBUG': args.debug
    }
    
    # 创建应用
    app = create_app(config)
    
    logger.info(f"Starting Flask Load Balancer on {args.host}:{args.port}")
    logger.info(f"Algorithm: {args.algorithm}")
    
    # 启动应用
    app.run(host=args.host, port=args.port, debug=args.debug, threaded=True)


if __name__ == '__main__':
    main()