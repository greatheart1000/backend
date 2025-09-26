"""
订单服务 - 提供订单创建、查询等接口
"""
from flask import Flask, request, jsonify
import uuid
import logging
import atexit
import requests
from datetime import datetime
from consul_service import ConsulService
from config import Config

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config.from_object(Config)

# 初始化 Consul 服务
consul_service = ConsulService()

# 模拟订单数据库
orders_db = {}

def verify_user_token(token):
    """
    通过用户服务验证token
    """
    try:
        # 发现用户服务
        user_service_url = consul_service.get_service_url("user-service")
        if not user_service_url:
            logger.error("User service not available")
            return None
        
        # 调用用户服务验证token
        headers = {'Authorization': f'Bearer {token}'}
        response = requests.get(f"{user_service_url}/api/users/profile", headers=headers, timeout=5)
        
        if response.status_code == 200:
            return response.json()['user']
        else:
            return None
    except Exception as e:
        logger.error(f"Error verifying token: {str(e)}")
        return None

@app.route('/health', methods=['GET'])
def health_check():
    """
    健康检查接口
    """
    return jsonify({'status': 'healthy', 'service': 'order-service'}), 200

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
        
        # 验证必需字段
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
            'created_at': datetime.utcnow().isoformat()
        }
        
        orders_db[order_id] = order
        
        logger.info(f"Order {order_id} created for user {user['username']}")
        
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

@app.route('/api/orders/<order_id>/status', methods=['PUT'])
def update_order_status(order_id):
    """
    更新订单状态接口
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
        
        if not data or not data.get('status'):
            return jsonify({'error': '状态是必需的'}), 400
        
        # 检查订单是否存在
        if order_id not in orders_db:
            return jsonify({'error': '订单不存在'}), 404
        
        order = orders_db[order_id]
        
        # 检查订单是否属于当前用户
        if order['user_id'] != user['user_id']:
            return jsonify({'error': '无权修改此订单'}), 403
        
        # 更新订单状态
        valid_statuses = ['pending', 'confirmed', 'processing', 'shipped', 'delivered', 'cancelled']
        new_status = data['status']
        
        if new_status not in valid_statuses:
            return jsonify({'error': f'无效的状态。有效状态: {", ".join(valid_statuses)}'}), 400
        
        order['status'] = new_status
        order['updated_at'] = datetime.utcnow().isoformat()
        
        logger.info(f"Order {order_id} status updated to {new_status}")
        
        return jsonify({
            'message': '订单状态更新成功',
            'order': order
        }), 200
    
    except Exception as e:
        logger.error(f"Update order status error: {str(e)}")
        return jsonify({'error': '更新订单状态时发生错误'}), 500

@app.route('/api/orders/stats', methods=['GET'])
def get_order_stats():
    """
    获取订单统计信息
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
        
        # 统计用户订单
        user_orders = [order for order in orders_db.values() if order['user_id'] == user['user_id']]
        
        stats = {
            'total_orders': len(user_orders),
            'total_amount': sum(order['total_amount'] for order in user_orders),
            'status_breakdown': {}
        }
        
        # 按状态分组统计
        for order in user_orders:
            status = order['status']
            if status not in stats['status_breakdown']:
                stats['status_breakdown'][status] = 0
            stats['status_breakdown'][status] += 1
        
        return jsonify({'stats': stats}), 200
    
    except Exception as e:
        logger.error(f"Get order stats error: {str(e)}")
        return jsonify({'error': '获取订单统计时发生错误'}), 500

def register_to_consul():
    """
    注册服务到 Consul
    """
    service_name = "order-service"
    service_id = f"order-service-{uuid.uuid4().hex[:8]}"
    address = consul_service.get_local_ip()
    port = 5002
    health_check_url = f"http://{address}:{port}/health"
    tags = ["order", "commerce", "api"]
    
    success = consul_service.register_service(
        service_name=service_name,
        service_id=service_id,
        address=address,
        port=port,
        health_check_url=health_check_url,
        tags=tags
    )
    
    if success:
        logger.info(f"Order service registered to Consul with ID: {service_id}")
        # 注册退出时的清理函数
        atexit.register(lambda: consul_service.deregister_service(service_id))
    else:
        logger.error("Failed to register order service to Consul")

if __name__ == '__main__':
    # 注册服务到 Consul
    register_to_consul()
    
    # 启动 Flask 应用
    app.run(host='0.0.0.0', port=5002, debug=True)