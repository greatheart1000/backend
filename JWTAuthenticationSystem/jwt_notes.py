from flask import Flask, request, jsonify
from flask_jwt_extended import (
    JWTManager, create_access_token, create_refresh_token,
    jwt_required, get_jwt_identity, get_jwt
)
from datetime import timedelta
from functools import wraps

app = Flask(__name__)

# —— 配置 —— 
app.config['JWT_SECRET_KEY'] = 'your_secret_key'
app.config['JWT_ALGORITHM'] = 'HS256'
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(minutes=15)
app.config['JWT_REFRESH_TOKEN_EXPIRES'] = timedelta(days=7)
app.config['JWT_TOKEN_LOCATION'] = ['headers']
app.config['JWT_HEADER_NAME'] = 'Authorization'
app.config['JWT_HEADER_TYPE'] = 'Bearer'
# 启用黑名单
app.config['JWT_BLACKLIST_ENABLED'] = True
app.config['JWT_BLACKLIST_TOKEN_CHECKS'] = ['access', 'refresh']

jwt = JWTManager(app)

# —— 模拟存储 & 黑名单 —— 
fake_users_db = {
    "alice": {"username":"alice","password":"secret1","role":"admin","tenant_id":"tenant_a"},
    "bob":   {"username":"bob",  "password":"secret2","role":"user", "tenant_id":"tenant_b"}
}
ROLE_PERMISSIONS = {
    "admin": {"read","write","delete"},
    "user":  {"read"}
}
blocklist = set()

@jwt.token_in_blocklist_loader
def check_if_token_revoked(jwt_header, jwt_payload):
    return jwt_payload['jti'] in blocklist

# —— 装饰器：多租户+RBAC 校验 —— 
def require_scopes(required_scopes):
    def wrapper(fn):
        @wraps(fn)
        @jwt_required()
        def decorated(*args, **kwargs):
            payload = get_jwt()
            # 多租户隔离
            tenant = request.headers.get('X-Tenant-ID')
            if tenant is None or tenant != payload.get('tenant_id'):
                return jsonify({"msg":"租户不匹配"}), 403
            # RBAC 权限校验
            user_scopes = set(payload.get('scopes', []))
            if not set(required_scopes).issubset(user_scopes):
                return jsonify({"msg":"权限不足"}), 403
            return fn(*args, **kwargs)
        return decorated
    return wrapper

# —— 登录 & 下发 Token —— 
@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    user = fake_users_db.get(username)
    if not user or user['password'] != password:
        return jsonify({"msg":"用户名或密码错误"}), 401

    additional_claims = {
        "role": user['role'],
        "tenant_id": user['tenant_id'],
        "scopes": list(ROLE_PERMISSIONS[user['role']])
    }
    access_token = create_access_token(identity=username, additional_claims=additional_claims)
    refresh_token = create_refresh_token(identity=username, additional_claims=additional_claims)
    return jsonify(access_token=access_token, refresh_token=refresh_token)

# —— 刷新 Token —— 
@app.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    jti = get_jwt()['jti']
    # 将旧 Refresh Token 加入黑名单
    blocklist.add(jti)

    identity = get_jwt_identity()
    claims = get_jwt()
    common_claims = {
        "role": claims['role'],
        "tenant_id": claims['tenant_id'],
        "scopes": claims['scopes']
    }
    new_access = create_access_token(identity=identity, additional_claims=common_claims)
    new_refresh = create_refresh_token(identity=identity, additional_claims=common_claims)
    return jsonify(access_token=new_access, refresh_token=new_refresh)

# —— 示例受保护接口 —— 
@app.route('/items', methods=['GET'])
@require_scopes(['read'])
def read_items():
    user = get_jwt_identity()
    tenant = get_jwt()['tenant_id']
    return jsonify(msg=f"Hello {user}, you have READ access in tenant {tenant}")

@app.route('/items', methods=['POST'])
@require_scopes(['write'])
def create_item():
    user = get_jwt_identity()
    return jsonify(msg=f"Item created by {user}")

@app.route('/items', methods=['DELETE'])
@require_scopes(['delete'])
def delete_item():
    user = get_jwt_identity()
    return jsonify(msg=f"Item deleted by {user}")

# —— 运行 —— 
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)