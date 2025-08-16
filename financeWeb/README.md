# 金十数据 - 多版本支持

这是一个支持Go和Python双后端的金融资讯网站，提供实时市场数据、新闻资讯、期货行情等功能。

## 🚀 功能特性

### 页面功能
- **用户认证**: 注册、登录、退出登录
- **主页**: 实时市场数据展示
- **新闻资讯**: 时事新闻和VIP内容
- **期货行情**: 实时期货价格数据
- **股票数据**: 热门股票实时信息
- **视频专区**: 投资分析视频内容
- **VIP专区**: 独家研报和预警
- **市场日历**: 重要经济事件提醒

### API接口
- `GET /api/market-data` - 市场数据
- `GET /api/news` - 新闻资讯
- `GET /api/futures` - 期货行情
- `GET /api/stocks` - 股票数据
- `GET /api/videos` - 视频内容
- `GET /api/vip-content` - VIP内容
- `GET /api/market-calendar` - 市场日历

## 📦 环境准备

### 1. 安装Go环境 (Go版本)
```bash
# 下载并安装Go: https://golang.org/dl/
# 验证安装
go version

# 安装依赖
go mod tidy
```

### 2. 安装Python环境 (Python版本)
```bash
# 下载并安装Python: https://www.python.org/downloads/
# 验证安装
python --version

# 安装依赖
pip install -r requirements.txt
```

## 🎯 运行指南

### 选择运行版本

你可以选择运行Go版本或Python版本，两个版本功能完全相同：

#### 🐹 Go版本 (推荐用于生产环境)
```bash
# 启动Go版本
go run main.go

# 访问网站
http://localhost:8080
```

#### 🐍 Python版本 (推荐用于开发环境)
```bash
# 启动Python版本
python app.py

# 访问网站
http://localhost:5000
```

### 版本切换说明

#### 同时运行两个版本
```bash
# 终端1: 启动Go版本
go run main.go

# 终端2: 启动Python版本
python app.py

# 访问地址
# Go版本: http://localhost:8080
# Python版本: http://localhost:5000
```

#### 停止服务
```bash
# 停止Go版本: Ctrl+C
# 停止Python版本: Ctrl+C
```

## 🏗️ 项目结构

```
golangLogin/
├── main.go                 # Go版本主文件
├── app.py                  # Python版本主文件
├── go.mod                  # Go依赖管理
├── go.sum                  # Go依赖校验
├── requirements.txt        # Python依赖
├── README.md              # 项目说明
└── templates/             # HTML模板
    ├── home.html          # 主页模板 (Go版本)
    ├── home_universal.html # 通用主页模板
    ├── login.html         # 登录页面
    └── register.html      # 注册页面
```

## 🔧 技术栈对比

| 特性 | Go版本 | Python版本 |
|------|--------|------------|
| **后端框架** | Go标准库 | Flask |
| **模板引擎** | Go Template | Jinja2 |
| **端口** | 8080 | 5000 |
| **性能** | 高 | 中等 |
| **开发速度** | 中等 | 快 |
| **学习曲线** | 陡峭 | 平缓 |
| **生产部署** | 推荐 | 适合 |
| **开发调试** | 一般 | 优秀 |

## 🎯 使用说明

### 首次使用
1. 选择要运行的版本 (Go或Python)
2. 启动对应的服务
3. 访问对应的地址
4. 点击"立即注册"创建账号
5. 使用注册的账号登录
6. 进入主页查看金融数据

### 版本选择建议

#### 选择Go版本的情况：
- 需要高性能和并发处理
- 团队熟悉Go语言
- 生产环境部署
- 对内存使用要求严格

#### 选择Python版本的情况：
- 快速原型开发
- 团队熟悉Python
- 需要频繁修改和调试
- 学习Web开发

## 📊 API调用示例

### 通用API调用 (两个版本都支持)

#### Python示例
```python
import requests

# 获取市场数据 (Go版本)
response = requests.get('http://localhost:8080/api/market-data')
market_data = response.json()
print(market_data)

# 获取市场数据 (Python版本)
response = requests.get('http://localhost:5000/api/market-data')
market_data = response.json()
print(market_data)
```

#### JavaScript示例
```javascript
// 获取市场数据 (Go版本)
fetch('http://localhost:8080/api/market-data')
  .then(response => response.json())
  .then(data => console.log(data));

// 获取市场数据 (Python版本)
fetch('http://localhost:5000/api/market-data')
  .then(response => response.json())
  .then(data => console.log(data));
```

#### cURL示例
```bash
# Go版本API调用
curl http://localhost:8080/api/market-data
curl http://localhost:8080/api/news
curl http://localhost:8080/api/futures

# Python版本API调用
curl http://localhost:5000/api/market-data
curl http://localhost:5000/api/news
curl http://localhost:5000/api/futures
```

## 🔄 版本切换步骤

### 从Go版本切换到Python版本
```bash
# 1. 停止Go服务 (Ctrl+C)

# 2. 启动Python服务
python app.py

# 3. 访问新地址
# 从 http://localhost:8080 切换到 http://localhost:5000
```

### 从Python版本切换到Go版本
```bash
# 1. 停止Python服务 (Ctrl+C)

# 2. 启动Go服务
go run main.go

# 3. 访问新地址
# 从 http://localhost:5000 切换到 http://localhost:8080
```

## 🎨 界面特色

- **现代化设计**: 浅色主题，专业金融风格
- **响应式布局**: 适配桌面和移动设备
- **实时更新**: 数据动态刷新
- **交互体验**: 悬停动画和过渡效果
- **加载动画**: 优雅的加载状态显示
- **版本兼容**: 前端完全兼容两个后端版本

## 🔒 安全特性

- **Session管理**: 两个版本都支持session
- **表单验证**: 前后端双重验证
- **路由保护**: 登录状态检查
- **密码加密**: Go版本使用bcrypt，Python版本使用明文（开发环境）

## 🚀 部署建议

### Go版本部署
```bash
# 编译
go build -o financial-app main.go

# 运行
./financial-app

# 或使用Docker
docker build -t financial-app-go .
docker run -p 8080:8080 financial-app-go
```

### Python版本部署
```bash
# 开发环境
python app.py

# 生产环境 (使用Gunicorn)
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app

# 或使用uWSGI
pip install uwsgi
uwsgi --http :5000 --module app:app
```

## 🔧 开发调试

### Go版本调试
```bash
# 启用详细日志
go run main.go

# 查看API接口
curl http://localhost:8080/api/market-data
```

### Python版本调试
```bash
# 启用调试模式 (自动)
python app.py

# 查看API接口
curl http://localhost:5000/api/market-data
```

## 📝 注意事项

1. **数据模拟**: 当前所有数据都是模拟生成，实际应用中需要连接真实数据源
2. **密码安全**: Go版本使用bcrypt加密，Python版本使用明文存储（仅开发环境）
3. **数据库**: 当前使用内存存储，生产环境应使用数据库
4. **API限流**: 生产环境应添加API访问限制
5. **端口冲突**: 确保8080和5000端口未被占用
6. **版本切换**: 切换版本时记得停止当前服务

## 🤝 贡献

欢迎提交Issue和Pull Request来改进这个项目！

## �� 许可证

MIT License 