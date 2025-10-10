from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_bcrypt import Bcrypt
from config import Config

app = Flask(__name__)
app.config.from_object(Config)

# 初始化数据库
from models import db, bcrypt
db.init_app(app)
bcrypt.init_app(app)

# 初始化JWT
jwt = JWTManager(app)
from jwt_utils import init_jwt_handlers
init_jwt_handlers(jwt)

def register_blueprints():
    # 注册蓝图
    from auth import auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')

    from resources import resources_bp
    app.register_blueprint(resources_bp, url_prefix='/api')

@app.route('/')
def index():
    return {'message': 'JWT Auth System'}

if __name__ == '__main__':
    register_blueprints()
    app.run(debug=True)