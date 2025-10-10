from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

resources_bp = Blueprint('resources', __name__)

# 受保护的资源示例
@resources_bp.route('/profile', methods=['GET'])
@jwt_required()
def profile():
    from app import db
    from models import User
    
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'message': 'User not found'}), 404
    
    return jsonify({
        'message': 'Profile data retrieved successfully',
        'profile': {
            'username': user.username,
            'email': user.email,
            'role': user.role
        }
    }), 200

# 管理员专用资源示例
@resources_bp.route('/admin', methods=['GET'])
@jwt_required()
def admin():
    from app import db
    from models import User
    
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'message': 'User not found'}), 404
    
    # 检查用户角色
    if user.role != 'admin':
        return jsonify({'message': 'Access denied. Admins only.'}), 403
    
    return jsonify({
        'message': 'Admin data retrieved successfully',
        'data': 'Secret admin data'
    }), 200

# 公开资源示例
@resources_bp.route('/public', methods=['GET'])
def public():
    return jsonify({
        'message': 'This is a public endpoint',
        'data': 'Anyone can access this'
    }), 200