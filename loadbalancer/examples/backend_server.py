"""
示例后端服务器
用于测试负载均衡功能
"""

from flask import Flask, jsonify, request
import socket
import time
import random
import threading
import argparse
import os


def create_backend_server(server_id, port):
    """创建后端服务器"""
    app = Flask(__name__)
    
    # 服务器信息
    server_info = {
        'id': server_id,
        'port': port,
        'hostname': socket.gethostname(),
        'started_at': time.time()
    }
    
    # 请求计数器
    request_counter = {'count': 0}
    counter_lock = threading.Lock()
    
    @app.route('/')
    def index():
        """首页"""
        with counter_lock:
            request_counter['count'] += 1
            count = request_counter['count']
        
        return jsonify({
            'message': f'Hello from backend server {server_id}!',
            'server_info': server_info,
            'request_count': count,
            'timestamp': time.time(),
            'client_ip': request.remote_addr
        })
    
    @app.route('/health')
    def health():
        """健康检查端点"""
        return jsonify({
            'status': 'healthy',
            'server_id': server_id,
            'uptime': time.time() - server_info['started_at']
        })
    
    @app.route('/api/users')
    def users():
        """API示例 - 用户列表"""
        with counter_lock:
            request_counter['count'] += 1
        
        users = [
            {'id': 1, 'name': 'Alice', 'email': 'alice@example.com'},
            {'id': 2, 'name': 'Bob', 'email': 'bob@example.com'},
            {'id': 3, 'name': 'Charlie', 'email': 'charlie@example.com'}
        ]
        
        return jsonify({
            'server_id': server_id,
            'users': users,
            'total': len(users)
        })
    
    @app.route('/api/orders')
    def orders():
        """API示例 - 订单列表"""
        with counter_lock:
            request_counter['count'] += 1
        
        orders = [
            {'id': 1, 'user_id': 1, 'amount': 100.0, 'status': 'completed'},
            {'id': 2, 'user_id': 2, 'amount': 250.0, 'status': 'pending'},
            {'id': 3, 'user_id': 3, 'amount': 75.0, 'status': 'shipped'}
        ]
        
        return jsonify({
            'server_id': server_id,
            'orders': orders,
            'total': len(orders)
        })
    
    @app.route('/admin/dashboard')
    def admin_dashboard():
        """管理员仪表板"""
        with counter_lock:
            request_counter['count'] += 1
            count = request_counter['count']
        
        return jsonify({
            'server_id': server_id,
            'dashboard': {
                'total_requests': count,
                'uptime': time.time() - server_info['started_at'],
                'memory_usage': f'{random.randint(40, 80)}%',
                'cpu_usage': f'{random.randint(20, 60)}%'
            }
        })
    
    @app.route('/slow')
    def slow():
        """慢响应端点 - 用于测试"""
        delay = random.uniform(1, 3)
        time.sleep(delay)
        
        with counter_lock:
            request_counter['count'] += 1
        
        return jsonify({
            'server_id': server_id,
            'message': 'This was a slow response',
            'delay': delay
        })
    
    @app.route('/error')
    def error():
        """错误端点 - 用于测试熔断器"""
        if random.random() < 0.7:  # 70%概率返回错误
            return jsonify({'error': 'Simulated error'}), 500
        else:
            return jsonify({
                'server_id': server_id,
                'message': 'Success!'
            })
    
    @app.route('/status')
    def status():
        """状态信息"""
        with counter_lock:
            count = request_counter['count']
        
        return jsonify({
            'server_info': server_info,
            'request_count': count,
            'status': 'running',
            'load': f'{random.randint(10, 90)}%'
        })
    
    @app.route('/echo', methods=['GET', 'POST', 'PUT', 'DELETE'])
    def echo():
        """回显请求信息"""
        with counter_lock:
            request_counter['count'] += 1
        
        return jsonify({
            'server_id': server_id,
            'method': request.method,
            'path': request.path,
            'args': dict(request.args),
            'headers': dict(request.headers),
            'data': request.get_data(as_text=True) if request.data else None,
            'json': request.get_json() if request.is_json else None
        })
    
    return app


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='Backend Server')
    parser.add_argument('--port', type=int, required=True, help='Port to run on')
    parser.add_argument('--id', default=None, help='Server ID')
    parser.add_argument('--host', default='127.0.0.1', help='Host to bind to')
    
    args = parser.parse_args()
    
    server_id = args.id or f'backend-{args.port}'
    
    app = create_backend_server(server_id, args.port)
    
    print(f"Starting backend server {server_id} on {args.host}:{args.port}")
    
    app.run(host=args.host, port=args.port, debug=False, threaded=True)


if __name__ == '__main__':
    main()