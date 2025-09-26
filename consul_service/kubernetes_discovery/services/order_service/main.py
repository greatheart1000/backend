"""
基于 Etcd 服务发现的订单服务
"""
from flask import Flask, request, jsonify
import uuid
import logging
import atexit
import requests
from datetime import datetime
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from etcd_service import EtcdService
from config import Config

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config.from_object(Config)

# 初始化 Etcd 服务
etcd_service = EtcdService(host='localhost', port=2379)

# 模拟订单数据库
orders_db = {}

def verify_user_token(token):
    """
    通过 Etcd 发现用户服务并验证token
    """
    try:
        # 通过 Etcd 发现用户服务
        user_service_url = etcd_service.get_service_url("user-service")
        if not user_service_url:
            logger.error("User service not available in Etcd")
            return None
        
        logger.info(f"Found user service at: {user_service_url}")
        
        # 调用用户服务验证token
        headers = {'Authorization': f'Bearer {token}'}
        response = requests.get(
            f"{user_service_url}/api/users/profile", 
            headers=headers, 
            timeout=5
        )
        
        if response.status_code == 200:
            return response.json()['user']
        else:
            logger.warning(f"Token verification failed: {response.status_code}")
            return None
            
    except Exception as e:
        logger.error(f"Error verifying token: {str(e)}")
        return None

@app.route('/health', methods=['GET'])
def health_check():
    """
    健康检查接口
    """
    return jsonify({
        'status': 'healthy', 
        'service': 'order-service-etcd',
        'timestamp': datetime.utcnow().isoformat()
    }), 200

@app.route('/api/orders', methods=['POST'])
def create_order():
    """
    创建订单接口
    """
    try:
        # 验证认证
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'error': '缺少认证token'}), 401
        
        token = auth_header.split(' ')[1]
        user = verify_user_token(token)
        
        if not user:
            return jsonify({'error': '无效或过期的token'}), 401
        
        data = request.get_json()
        
        if not data or not data.get('product_name') or not data.get('quantity'):
            return jsonify({'error': '产品名称和数量是必需的'}), 400
        
        # 创建订单
        order_id = str(uuid.uuid4())
        order = {
            'order_id': order_id,
            'user_id': user['user_id'],
            'username': user['username'],
            'product_name': data['product_name'],
            'quantity': int(data['quantity']),
            'price': float(data.get('price', 0)),
            'total_amount': float(data.get('price', 0)) * int(data['quantity']),
            'status': 'pending',
            'discovery_method': 'etcd',
            'created_at': datetime.utcnow().isoformat()
        }
        
        orders_db[order_id] = order
        
        logger.info(f"Order {order_id} created for user {user['username']} via Etcd")
        
        return jsonify({
            'message': '订单创建成功',
            'order': order
        }), 201
    
    except Exception as e:
        logger.error(f"Create order error: {str(e)}")
        return jsonify({'error': '创建订单时发生错误'}), 500

@app.route('/api/orders', methods=['GET'])
def get_orders():
    """
    获取用户订单列表接口
    """
    try:
        # 验证认证
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'error': '缺少认证token'}), 401
        
        token = auth_header.split(' ')[1]
        user = verify_user_token(token)
        
        if not user:
            return jsonify({'error': '无效或过期的token'}), 401
        
        # 获取用户的订单
        user_orders = []
        for order_id, order in orders_db.items():
            if order['user_id'] == user['user_id']:
                user_orders.append(order)
        
        # 按创建时间倒序排列
        user_orders.sort(key=lambda x: x['created_at'], reverse=True)
        
        return jsonify({'orders': user_orders}), 200
    
    except Exception as e:
        logger.error(f"Get orders error: {str(e)}")
        return jsonify({'error': '获取订单列表时发生错误'}), 500

@app.route('/api/orders/<order_id>', methods=['GET'])
def get_order(order_id):
    """
    获取订单详情接口
    """
    try:
        # 验证认证
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'error': '缺少认证token'}), 401
        
        token = auth_header.split(' ')[1]
        user = verify_user_token(token)
        
        if not user:
            return jsonify({'error': '无效或过期的token'}), 401
        
        # 检查订单是否存在
        if order_id not in orders_db:
            return jsonify({'error': '订单不存在'}), 404
        
        order = orders_db[order_id]
        
        # 检查订单是否属于当前用户
        if order['user_id'] != user['user_id']:
            return jsonify({'error': '无权访问此订单'}), 403
        
        return jsonify({'order': order}), 200
    
    except Exception as e:
        logger.error(f"Get order error: {str(e)}")
        return jsonify({'error': '获取订单详情时发生错误'}), 500

@app.route('/api/services/discovery', methods=['GET'])
def service_discovery_info():
    """
    获取服务发现信息（调试接口）
    """
    try:
        all_services = etcd_service.get_all_services()
        
        # 测试服务发现功能
        user_services = etcd_service.discover_service("user-service")
        
        return jsonify({
            'discovery_type': 'etcd',
            'all_services': all_services,
            'user_service_instances': user_services
        }), 200
    except Exception as e:
        logger.error(f"Service discovery info error: {str(e)}")
        return jsonify({'error': '获取服务发现信息时发生错误'}), 500

def register_to_etcd():
    """
    注册服务到 Etcd
    """
    service_name = "order-service"
    service_id = f"order-service-etcd-{uuid.uuid4().hex[:8]}"
    address = etcd_service.get_local_ip()
    port = 5002
    
    metadata = {
        'version': '1.0.0',
        'framework': 'flask',
        'discovery': 'etcd',
        'dependencies': ['user-service']
    }
    
    tags = ["order", "commerce", "api", "etcd"]
    
    success = etcd_service.register_service(
        service_name=service_name,
        service_id=service_id,
        address=address,
        port=port,
        metadata=metadata,
        tags=tags
    )
    
    if success:
        logger.info(f"Order service registered to Etcd with ID: {service_id}")
        # 注册退出时的清理函数
        atexit.register(lambda: etcd_service.deregister_service(service_id))
        
        # 启动服务监听
        def service_change_callback(event, service_name):
            logger.info(f"Service {service_name} changed: {event.type}")
            if service_name == "user-service":
                logger.info("User service topology changed, may need to update cache")
        
        # 监听用户服务变化
        etcd_service.watch_service("user-service", service_change_callback)
        
    else:
        logger.error("Failed to register order service to Etcd")

if __name__ == '__main__':
    # 注册服务到 Etcd
    register_to_etcd()
    
    # 启动 Flask 应用
    app.run(host='0.0.0.0', port=5002, debug=True)