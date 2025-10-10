# JWT Authentication System

一个基于 Flask 和 React 的完整 JWT 认证系统，实现了用户注册、登录、Token 管理和受保护资源访问功能。

## 功能特性

- 用户注册和登录
- JWT Token 生成与验证
- 访问令牌和刷新令牌机制
- 受保护资源访问控制
- 基于角色的访问控制 (RBAC)
- 前后端分离架构
- 自动 Token 刷新

## 技术栈

### 后端
- Flask (Python Web 框架)
- Flask-JWT-Extended (JWT 认证)
- Flask-SQLAlchemy (ORM)
- Flask-Bcrypt (密码加密)
- SQLite (数据库)

### 前端
- React (JavaScript 库)
- React Router (路由管理)
- Axios (HTTP 客户端)
- Vite (构建工具)

## 项目结构

```
.
├── app.py                 # Flask 应用入口
├── config.py              # 配置文件
├── models.py              # 数据模型
├── auth.py                # 认证相关路由
├── resources.py           # 资源路由
├── jwt_utils.py           # JWT 工具函数
├── requirements.txt       # Python 依赖
├── README.md              # 项目说明文档
├── frontend/              # 前端代码
│   ├── package.json       # npm 配置
│   ├── vite.config.js     # Vite 配置
│   └── src/               # 前端源码
└── venv/                  # Python 虚拟环境
```

## 安装与运行

### 后端设置

1. 创建并激活虚拟环境:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   # 或者 venv\Scripts\activate  # Windows
   ```

2. 安装依赖:
   ```bash
   pip install -r requirements.txt
   ```

3. 初始化数据库:
   ```bash
   python -c "from app import app, db; app.app_context().push(); db.create_all()"
   ```

4. 启动后端服务:
   ```bash
   python app.py
   ```

### 前端设置

1. 安装依赖:
   ```bash
   cd frontend
   npm install
   ```

2. 启动前端服务:
   ```bash
   npm run dev
   ```

## API 接口

### 认证接口
- `POST /auth/register` - 用户注册
- `POST /auth/login` - 用户登录
- `POST /auth/refresh` - 刷新访问令牌
- `GET /auth/me` - 获取当前用户信息

### 资源接口
- `GET /api/profile` - 获取用户资料 (需要认证)
- `GET /api/admin` - 管理员专用接口 (需要认证和管理员权限)
- `GET /api/public` - 公开接口 (无需认证)

## JWT 工作原理

JWT (JSON Web Token) 是一种开放标准 (RFC 7519)，用于在各方之间安全地传输信息。

### Token 结构
JWT 由三部分组成，用点 (.) 分隔：
1. Header (头部)
2. Payload (载荷)
3. Signature (签名)

### 认证流程
1. 用户登录时，服务器验证凭据并生成 JWT
2. 服务器将 JWT 返回给客户端
3. 客户端在后续请求中将 JWT 放在 Authorization 头中
4. 服务器验证 JWT 的有效性并处理请求

### 关于 SECRET_KEY
本系统使用统一的密钥来签名和验证所有用户的 token，而不是每个用户一个密钥。用户的身份信息存储在 token 的 payload 中，这样系统就能区分不同用户。

## 开发说明

### 环境变量
可以在环境变量中设置以下配置：
- `JWT_SECRET_KEY` - JWT 签名密钥
- `DATABASE_URL` - 数据库连接 URL

### 数据库模型
- User: 用户模型，包含用户名、邮箱、密码哈希和角色

## 许可证

MIT License

## 联系方式

如有问题，请提交 Issue 或联系项目维护者。