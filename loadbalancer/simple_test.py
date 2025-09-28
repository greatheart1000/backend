#!/usr/bin/env python3
"""
简单的Flask负载均衡器测试
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from flask import Flask
from algorithms.round_robin import RoundRobinBalancer
from algorithms.base import Backend

def test_basic_components():
    """测试基础组件"""
    print("Testing basic components...")
    
    # 测试Backend
    backend = Backend('test1', 'localhost', 8001, weight=1)
    print(f"✓ Backend created: {backend.address}")
    
    # 测试负载均衡器
    lb = RoundRobinBalancer()
    lb.add_backend(backend)
    print(f"✓ Load balancer created with {len(lb.get_all_backends())} backends")
    
    # 测试Flask应用
    app = Flask(__name__)
    
    @app.route('/')
    def index():
        return {'message': 'Hello from simple load balancer!'}
    
    @app.route('/health')
    def health():
        return {'status': 'healthy'}
    
    print("✓ Flask app created")
    return app

def main():
    app = test_basic_components()
    print("Starting simple Flask app...")
    app.run(host='127.0.0.1', port=8080, debug=True)

if __name__ == '__main__':
    main()