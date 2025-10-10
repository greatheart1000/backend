from flask_jwt_extended import create_access_token, create_refresh_token, get_jwt_identity, get_jwt
from flask_jwt_extended import decode_token
from models import User

# JWT错误处理
def init_jwt_handlers(jwt):
    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        return {'message': 'Token has expired'}, 401

    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        return {'message': 'Invalid token'}, 401

    @jwt.unauthorized_loader
    def missing_token_callback(error):
        return {'message': 'Missing token'}, 401

# 创建token
def create_tokens(user_id):
    access_token = create_access_token(identity=user_id)
    refresh_token = create_refresh_token(identity=user_id)
    return access_token, refresh_token

# 验证token
def verify_token(token):
    try:
        decoded_token = decode_token(token)
        return decoded_token
    except Exception as e:
        return None

# 获取当前用户
def get_current_user():
    from app import db
    user_id = get_jwt_identity()
    return User.query.get(user_id)