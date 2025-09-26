

我来帮你生成测试每个接口的curl命令。首先让我查看一下你的项目结构，了解有哪些接口。

Read file: routes/auth_routes.go
Read file: handlers/auth_handler.go
Read file: main.go
现在让我查看一下用户模型，了解注册接口需要的字段：

Read file: models/user.go
基于你的代码分析，我为你生成测试每个接口的curl命令。你的项目有以下3个接口：

## 1. 用户注册接口

```bash
# 注册新用户
curl -X POST http://localhost:8080/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com",
    "password": "password123"
  }'
```

```
cd /mnt/d/project/go_learn/go-echo && sqlite3 data/development.db "SELECT * FROM users;"
1|alice|alice@example.com|$2a$10$1oVtNZHlJrAamNgc9sA88OMEJbR/CjbMOZu1kx5QRzlbqnTXpfShq
2|testuser|test@example.com|$2a$10$UWg4t2A4vlxFCx21GUVntu8Fao8cJTbXyOhagP5wo6R5jVE1N/wmq
```





## 2. 用户登录接口

```bash
# 用户登录
curl -X POST http://localhost:8080/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "$2a$10$UWg4t2A4vlxFCx21GUVntu8Fao8cJTbXyOhagP5wo6R5jVE1N/wmq"
  }'
```

## 3. 获取用户信息接口（需要JWT认证）

```bash
# 获取用户信息（需要先登录获取token）
curl -X GET http://localhost:8080/protected/profile \
  -H "Authorization: Bearer YOUR_JWT_TOKEN_HERE"
```

## 完整的测试流程

### 步骤1：启动服务器
```bash
go run main.go
```

### 步骤2：注册用户
```bash
curl -X POST http://localhost:8080/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com",
    "password": "password123"
  }'
```

### 步骤3：登录获取token
```bash
curl -X POST http://localhost:8080/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "password123"
  }'
```

### 步骤4：使用token访问受保护的接口
```bash
# 将上面登录返回的token替换到下面的YOUR_JWT_TOKEN_HERE
curl -X GET http://localhost:8080/protected/profile \
  -H "Authorization: Bearer YOUR_JWT_TOKEN_HERE"
```

## 测试不同场景的curl命令

### 测试注册接口的各种情况：

```bash
# 1. 正常注册
curl -X POST http://localhost:8080/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "newuser",
    "email": "newuser@example.com",
    "password": "password123"
  }'

# 2. 测试重复邮箱注册
curl -X POST http://localhost:8080/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "anotheruser",
    "email": "test@example.com",
    "password": "password123"
  }'

# 3. 测试无效邮箱格式
curl -X POST http://localhost:8080/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser2",
    "email": "invalid-email",
    "password": "password123"
  }'

# 4. 测试密码太短
curl -X POST http://localhost:8080/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser3",
    "email": "test3@example.com",
    "password": "123"
  }'
```

### 测试登录接口的各种情况：

```bash
# 1. 正常登录
curl -X POST http://localhost:8080/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "password123"
  }'

# 2. 测试错误密码
curl -X POST http://localhost:8080/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "wrongpassword"
  }'

# 3. 测试不存在的用户
curl -X POST http://localhost:8080/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "nonexistent@example.com",
    "password": "password123"
  }'
```

### 测试受保护接口的各种情况：

```bash
# 1. 使用有效token
curl -X GET http://localhost:8080/protected/profile \
  -H "Authorization: Bearer YOUR_JWT_TOKEN_HERE"

# 2. 不使用token（应该返回401）
curl -X GET http://localhost:8080/protected/profile

# 3. 使用无效token
curl -X GET http://localhost:8080/protected/profile \
  -H "Authorization: Bearer invalid_token_here"
```

## 注意事项

1. **端口号**：默认是8080，如果你的服务器运行在不同端口，请修改URL中的端口号
2. **JWT Token**：登录成功后，响应中会包含token，复制这个token用于访问受保护的接口
3. **Content-Type**：POST请求需要设置正确的Content-Type头
4. **Authorization头**：访问受保护接口时，需要在Authorization头中包含Bearer token

你可以先启动服务器，然后按顺序执行这些curl命令来测试你的API接口。

---

# API 测试 Curl 命令集合

本文档包含了完整的 API 测试 curl 命令，涵盖了用户注册、登录、忘记密码、重置密码等所有功能的测试场景。

## 启动服务器

```bash
cd /mnt/d/project/go_learn/go-echo
go run main.go
```

## 1. 用户注册功能测试

### 1.1 正常注册
```bash
curl -X POST http://localhost:8080/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com", 
    "password": "123456"
  }'
```

### 1.2 测试用户名太短（应该失败）
```bash
curl -X POST http://localhost:8080/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "te",
    "email": "test@example.com", 
    "password": "123456"
  }'
```

### 1.3 测试密码太短（应该失败）
```bash
curl -X POST http://localhost:8080/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com", 
    "password": "12345"
  }'
```

### 1.4 测试无效邮箱格式（应该失败）
```bash
curl -X POST http://localhost:8080/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "invalid-email", 
    "password": "123456"
  }'
```

### 1.5 测试重复邮箱注册（应该失败）
```bash
curl -X POST http://localhost:8080/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser2",
    "email": "test@example.com", 
    "password": "123456"
  }'
```

### 1.6 测试重复用户名（应该失败）
```bash
curl -X POST http://localhost:8080/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test2@example.com", 
    "password": "123456"
  }'
```

## 2. 用户登录功能测试

### 2.1 正常登录
```bash
curl -X POST http://localhost:8080/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com", 
    "password": "123456"
  }'
```

### 2.2 测试不存在的用户（应该失败）
```bash
curl -X POST http://localhost:8080/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "nonexistent@example.com", 
    "password": "123456"
  }'
```

### 2.3 测试错误密码（应该失败）
```bash
curl -X POST http://localhost:8080/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com", 
    "password": "wrongpassword"
  }'
```

### 2.4 测试无效邮箱格式（应该失败）
```bash
curl -X POST http://localhost:8080/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "invalid-email", 
    "password": "123456"
  }'
```

### 2.5 测试空密码（应该失败）
```bash
curl -X POST http://localhost:8080/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com", 
    "password": ""
  }'
```

## 3. 忘记密码功能测试

### 3.1 正常请求密码重置（存在的邮箱）
```bash
curl -X POST http://localhost:8080/forgot-password \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com"
  }'
```

### 3.2 请求密码重置（不存在的邮箱，为了安全也返回成功）
```bash
curl -X POST http://localhost:8080/forgot-password \
  -H "Content-Type: application/json" \
  -d '{
    "email": "nonexistent@example.com"
  }'
```

### 3.3 测试无效邮箱格式（应该失败）
```bash
curl -X POST http://localhost:8080/forgot-password \
  -H "Content-Type: application/json" \
  -d '{
    "email": "invalid-email"
  }'
```

## 4. 重置密码功能测试

### 4.1 使用有效令牌重置密码
```bash
# 注意：需要先通过忘记密码接口获取重置令牌
curl -X POST http://localhost:8080/reset-password \
  -H "Content-Type: application/json" \
  -d '{
    "token": "YOUR_RESET_TOKEN_HERE",
    "new_password": "newpassword123"
  }'
```

### 4.2 测试无效令牌（应该失败）
```bash
curl -X POST http://localhost:8080/reset-password \
  -H "Content-Type: application/json" \
  -d '{
    "token": "invalid-token",
    "new_password": "newpassword123"
  }'
```

### 4.3 测试新密码太短（应该失败）
```bash
curl -X POST http://localhost:8080/reset-password \
  -H "Content-Type: application/json" \
  -d '{
    "token": "YOUR_RESET_TOKEN_HERE",
    "new_password": "12345"
  }'
```

### 4.4 测试空令牌（应该失败）
```bash
curl -X POST http://localhost:8080/reset-password \
  -H "Content-Type: application/json" \
  -d '{
    "token": "",
    "new_password": "newpassword123"
  }'
```

## 5. 受保护路由测试

### 5.1 使用有效JWT令牌访问用户信息
```bash
# 注意：需要先登录获取JWT令牌，然后替换YOUR_JWT_TOKEN_HERE
curl -X GET http://localhost:8080/protected/profile \
  -H "Authorization: Bearer YOUR_JWT_TOKEN_HERE"
```

### 5.2 无令牌访问（应该失败）
```bash
curl -X GET http://localhost:8080/protected/profile
```

### 5.3 使用无效令牌访问（应该失败）
```bash
curl -X GET http://localhost:8080/protected/profile \
  -H "Authorization: Bearer invalid_token_here"
```

## 6. 完整测试流程示例

### 场景1：完整的用户注册和登录流程
```bash
# 1. 注册用户
curl -X POST http://localhost:8080/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "newuser",
    "email": "newuser@example.com", 
    "password": "123456"
  }'

# 2. 登录用户
curl -X POST http://localhost:8080/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "newuser@example.com", 
    "password": "123456"
  }'

# 3. 使用获得的token访问用户信息
# （将登录响应中的token替换到下面命令中）
curl -X GET http://localhost:8080/protected/profile \
  -H "Authorization: Bearer YOUR_JWT_TOKEN_HERE"
```

### 场景2：完整的密码重置流程
```bash
# 1. 请求密码重置
curl -X POST http://localhost:8080/forgot-password \
  -H "Content-Type: application/json" \
  -d '{
    "email": "newuser@example.com"
  }'

# 2. 使用重置令牌重置密码
# （将上面响应中的reset_token替换到下面命令中）
curl -X POST http://localhost:8080/reset-password \
  -H "Content-Type: application/json" \
  -d '{
    "token": "YOUR_RESET_TOKEN_HERE",
    "new_password": "newpassword123"
  }'

# 3. 使用新密码登录
curl -X POST http://localhost:8080/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "newuser@example.com", 
    "password": "newpassword123"
  }'

# 4. 确认旧密码不能使用
curl -X POST http://localhost:8080/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "newuser@example.com", 
    "password": "123456"
  }'
```

## 7. 实用工具命令

### 查看数据库内容
```bash
# 查看所有用户
sqlite3 /mnt/d/project/go_learn/go-echo/data/development.db "SELECT id, username, email, created_at FROM users;"

# 查看重置令牌（仅用于调试）
sqlite3 /mnt/d/project/go_learn/go-echo/data/development.db "SELECT id, username, reset_token, reset_token_expiry FROM users WHERE reset_token IS NOT NULL;"
```

### 清理数据库（重新开始测试）
```bash
# 删除数据库文件重新开始
rm -f /mnt/d/project/go_learn/go-echo/data/development.db
```

### 停止服务器进程
```bash
# 如果端口被占用，强制停止占用8080端口的进程
lsof -ti:8080 | xargs kill -9
```

## 8. 预期响应示例

### 成功注册响应
```json
{
  "message": "用户注册成功",
  "user": {
    "email": "test@example.com",
    "id": 1,
    "username": "testuser"
  }
}
```

### 成功登录响应
```json
{
  "message": "登录成功",
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": {
    "email": "test@example.com",
    "id": 1,
    "username": "testuser"
  }
}
```

### 忘记密码响应
```json
{
  "message": "如果该邮箱已注册，您将收到密码重置邮件",
  "reset_token": "99d744531b42c6a3a7b29df01c03bfeb4d9697502a7e1748d59b516180f7304e"
}
```

### 密码重置成功响应
```json
{
  "message": "密码重置成功"
}
```

### 错误响应示例
```json
{
  "error": "密码长度至少需要6个字符"
}
```

---

## 注意事项

1. **开发模式**：当前忘记密码功能会在响应中返回重置令牌，这仅用于开发测试。生产环境中应该通过邮件发送。

2. **JWT令牌**：登录成功后获得的JWT令牌有过期时间（24小时），过期后需要重新登录。

3. **重置令牌**：密码重置令牌有效期为1小时，使用后会自动清除。

4. **安全考虑**：为了安全，即使邮箱不存在，忘记密码接口也会返回成功消息，不会泄露用户信息。

5. **数据库**：项目使用SQLite数据库，数据存储在`data/development.db`文件中。

```

```

