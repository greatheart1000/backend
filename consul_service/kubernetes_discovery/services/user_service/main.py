"""
基于 Etcd 服务发现的用户服务
"""
from flask import Flask, request, jsonify
import jwt
import bcrypt
import uuid
import logging
import atexit
from datetime import datetime, timedelta
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

# 模拟用户数据库
users_db = {}

def generate_jwt_token(user_id, username):
    """
    生成 JWT token
    """
    payload = {
        'user_id': user_id,
        'username': username,
        'exp': datetime.utcnow() + timedelta(hours=24)
    }
    return jwt.encode(payload, Config.JWT_SECRET_KEY, algorithm='HS256')

def verify_jwt_token(token):
    """
    验证 JWT token
    """
    try:
        payload = jwt.decode(token, Config.JWT_SECRET_KEY, algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

@app.route('/health', methods=['GET'])
def health_check():
    """
    健康检查接口
    """
    return jsonify({
        'status': 'healthy', 
        'service': 'user-service-etcd',
        'timestamp': datetime.utcnow().isoformat()
    }), 200

@app.route('/api/users/register', methods=['POST'])
def register():
    """
    用户注册接口
    """
    try:
        data = request.get_json()
        
        if not data or not data.get('username') or not data.get('password'):
            return jsonify({'error': '用户名和密码是必需的'}), 400
        
        username = data['username']
        password = data['password']
        email = data.get('email', '')
        
        if username in users_db:
            return jsonify({'error': '用户名已存在'}), 409
        
        # 密码加密
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        
        # 创建用户
        user_id = str(uuid.uuid4())
        users_db[username] = {
            'user_id': user_id,
            'username': username,
            'password': hashed_password,
            'email': email,
            'created_at': datetime.utcnow().isoformat()
        }
        
        logger.info(f"User {username} registered successfully")
        
        return jsonify({
            'message': '用户注册成功',
            'user_id': user_id,
            'username': username
        }), 201
    
    except Exception as e:
        logger.error(f"Registration error: {str(e)}")
        return jsonify({'error': '注册过程中发生错误'}), 500

@app.route('/api/users/login', methods=['POST'])
def login():
    """
    用户登录接口
    """
    try:
        data = request.get_json()
        
        if not data or not data.get('username') or not data.get('password'):
            return jsonify({'error': '用户名和密码是必需的'}), 400
        
        username = data['username']
        password = data['password']
        
        if username not in users_db:
            return jsonify({'error': '用户名或密码错误'}), 401
        
        user = users_db[username]
        
        if not bcrypt.checkpw(password.encode('utf-8'), user['password']):
            return jsonify({'error': '用户名或密码错误'}), 401
        
        # 生成 JWT token
        token = generate_jwt_token(user['user_id'], username)
        
        logger.info(f"User {username} logged in successfully")
        
        return jsonify({
            'message': '登录成功',
            'token': token,
            'user': {
                'user_id': user['user_id'],
                'username': user['username'],
                'email': user['email']
            }
        }), 200
    
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        return jsonify({'error': '登录过程中发生错误'}), 500

@app.route('/api/users/profile', methods=['GET'])
def get_profile():
    """
    获取用户信息接口（需要认证）
    """
    try:
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'error': '缺少认证token'}), 401
        
        token = auth_header.split(' ')[1]
        payload = verify_jwt_token(token)
        
        if not payload:
            return jsonify({'error': '无效或过期的token'}), 401
        
        username = payload['username']
        
        if username not in users_db:
            return jsonify({'error': '用户不存在'}), 404
        
        user = users_db[username]
        
        return jsonify({
            'user': {
                'user_id': user['user_id'],
                'username': user['username'],
                'email': user['email'],
                'created_at': user['created_at']
            }
        }), 200
    
    except Exception as e:
        logger.error(f"Get profile error: {str(e)}")
        return jsonify({'error': '获取用户信息时发生错误'}), 500

@app.route('/api/services/discovery', methods=['GET'])
def service_discovery_info():
    """
    获取服务发现信息（调试接口）
    """
    try:
        all_services = etcd_service.get_all_services()
        return jsonify({
            'discovery_type': 'etcd',
            'services': all_services
        }), 200
    except Exception as e:
        logger.error(f"Service discovery info error: {str(e)}")
        return jsonify({'error': '获取服务发现信息时发生错误'}), 500

def register_to_etcd():
    """
    注册服务到 Etcd
    """
    service_name = "user-service"
    service_id = f"user-service-etcd-{uuid.uuid4().hex[:8]}"
    address = etcd_service.get_local_ip()
    port = 5001
    
    metadata = {
        'version': '1.0.0',
        'framework': 'flask',
        'discovery': 'etcd'
    }
    
    tags = ["user", "authentication", "api", "etcd"]
    
    success = etcd_service.register_service(
        service_name=service_name,
        service_id=service_id,
        address=address,
        port=port,
        metadata=metadata,
        tags=tags
    )
    
    if success:
        logger.info(f"User service registered to Etcd with ID: {service_id}")
        # 注册退出时的清理函数
        atexit.register(lambda: etcd_service.deregister_service(service_id))
        
        # 启动服务监听（可选）
        def service_change_callback(event, service_name):
            logger.info(f"Service {service_name} changed: {event.type}")
        
        etcd_service.watch_service("user-service", service_change_callback)
        
    else:
        logger.error("Failed to register user service to Etcd")

if __name__ == '__main__':
    # 注册服务到 Etcd
    register_to_etcd()
    
    # 启动 Flask 应用
    app.run(host='0.0.0.0', port=5001, debug=True)