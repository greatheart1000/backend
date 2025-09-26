好的，这是为你生成的 `README.md` 文件。它包含了你项目的基础信息、如何运行、以及每个 API 接口的详细说明和测试命令。

Markdown

```
# Go Fiber & MySQL API 服务

这是一个使用 Go 语言的 **Fiber** 框架构建的 Web API 服务，集成了 **MySQL** 数据库，并实现了基本的**权限控制**功能。

---

## 🚀 项目启动

### 1. 准备工作

在运行项目之前，请确保你已经安装了以下环境：

* **Go** (版本 1.18+)
* **MySQL** (版本 5.7+)
* **Git**

### 2. 数据库配置

1.  创建一个名为 `testdb` 的数据库：
    ```sql
    CREATE DATABASE testdb;
    ```
2.  进入 `mysql` 数据库并创建 `users` 表，确保包含 `role` 字段：
    ```sql
    USE testdb;

    CREATE TABLE users (
        id INT AUTO_INCREMENT PRIMARY KEY,
        name VARCHAR(255) NOT NULL,
        age INT NOT NULL,
        role VARCHAR(50) NOT NULL DEFAULT 'user'
    );
    ```

### 3. 安装依赖

进入项目根目录，运行以下命令安装 Go 模块依赖：
```bash
go mod tidy
```



### 4. 运行服务



确保你的 MySQL 数据库正在运行，然后执行以下命令启动服务：

Bash

```
go run main.go
```

服务将在本地的 `3000` 端口启动。

------



## 💡 API 接口文档



以下是所有可用的 API 接口及其测试命令。你可以使用 `curl` 或 Postman 等工具进行测试。



### 1. 基础接口





#### 1.1 `GET /`



- **说明**：一个简单的健康检查接口。

- **请求方法**：`GET`

- **示例**：

  Bash

  ```
  curl http://localhost:3000
  ```

- **响应**：`Hello, World!`



#### 1.2 `GET /api/users/:id`



- **说明**：通过 ID 获取用户信息（模拟）。

- **请求方法**：`GET`

- **参数**：`:id` (用户ID)

- **示例**：

  Bash

  ```
  curl http://localhost:3000/api/users/123
  ```

- **响应**：`User ID: 123`



#### 1.3 `POST /api/users`



- **说明**：处理 JSON 格式的用户数据（模拟）。

- **请求方法**：`POST`

- **请求头**：`Content-Type: application/json`

- **请求体**：

  JSON

  ```
  {
    "name": "Alice",
    "age": 30
  }
  ```

- **示例**：

  Bash

  ```
  curl -X POST http://localhost:3000/api/users \
  -H "Content-Type: application/json" \
  -d '{"name": "Alice", "age": 30}'
  ```

------



### 2. 数据库操作与权限接口





#### 2.1 `POST /users`



- **说明**：新增一个用户到数据库，新用户的 `role` 字段默认为 `user`。

- **请求方法**：`POST`

- **请求头**：`Content-Type: application/json`

- **请求体**：

  JSON

  ```
  {
    "name": "Bob",
    "age": 25
  }
  ```

- **示例**：

  Bash

  ```
  curl -X POST http://localhost:3000/users \
  -H "Content-Type: application/json" \
  -d '{"name": "Bob", "age": 25}'
  ```



#### 2.2 `GET /users`



- **说明**：查询数据库中所有用户列表。此接口**仅限管理员访问**。

- **请求方法**：`GET`

- **权限**：需要请求头 `X-User-Role` 为 `admin`。

- **示例**：

  1. **普通用户访问 (会被拒绝)**：

     Bash

     ```
     curl http://localhost:3000/users
     ```

     - **响应**：`{"error":"您没有权限访问此资源"}`

  2. **管理员访问 (需要手动在数据库中插入一个管理员用户)**：

     Bash

     ```
     # 手动插入管理员用户
     mysql> INSERT INTO users (name, age, role) VALUES ('AdminUser', 40, 'admin');
     
     # 使用 curl 命令
     curl -H "X-User-Role: admin" http://localhost:3000/users
     ```

     - **响应**：成功返回所有用户数据的 JSON 数组。