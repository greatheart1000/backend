from flask import Flask, request, jsonify, send_file
from prometheus_client import Counter, Histogram, Gauge, Summary, generate_latest, Info
import time
import random
import threading
import json
import hashlib
import os
from datetime import datetime, timedelta
from werkzeug.utils import secure_filename

app = Flask(__name__)

# 基础指标
login_total = Counter("login_total", "Login requests", ["status", "method"])
reg_total = Counter("register_total", "Register requests", ["status"])
latency_hist = Histogram("request_duration_seconds", "Request latency", ["method", "endpoint"])

# API接口监控指标
api_requests_total = Counter("api_requests_total", "Total API requests", ["method", "endpoint", "status_code"])
api_request_duration = Histogram("api_request_duration_seconds", "API request duration", ["method", "endpoint"], buckets=[0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0])
api_request_size = Histogram("api_request_size_bytes", "API request payload size", ["endpoint"], buckets=[100, 1000, 10000, 100000, 1000000])
api_response_size = Histogram("api_response_size_bytes", "API response size", ["endpoint"], buckets=[100, 1000, 10000, 100000, 1000000])

# 新增监控指标
active_sessions = Gauge("active_sessions_total", "Number of active user sessions")
concurrent_requests = Gauge("concurrent_requests", "Number of concurrent requests")
response_size_hist = Histogram("response_size_bytes", "Response size distribution", ["endpoint"])
error_rate = Counter("error_total", "Total errors", ["error_type"])

# 业务指标
user_registrations_daily = Counter("user_registrations_daily_total", "Daily user registrations")
login_attempts_per_user = Histogram("login_attempts_per_user", "Login attempts per user", buckets=[1, 2, 3, 5, 10, 20, 50])
password_strength = Histogram("password_strength_score", "Password strength distribution", buckets=[1, 2, 3, 4, 5])

# 扩展业务指标
user_operations_total = Counter("user_operations_total", "User operations", ["operation", "status"])
file_operations_total = Counter("file_operations_total", "File operations", ["operation", "file_type", "status"])
file_size_hist = Histogram("file_size_bytes", "File size distribution", buckets=[1024, 10240, 102400, 1048576, 10485760])
data_export_size = Histogram("data_export_size_bytes", "Data export size", buckets=[1000, 10000, 100000, 1000000])

# 系统指标
app_info = Info("app_info", "Application information")
app_info.info({"version": "1.0.0", "environment": "development"})

# 响应时间摘要
request_summary = Summary("request_processing_seconds", "Request processing time", ["method"])

# 假装的数据库和会话存储
USER_DB = {}
ACTIVE_SESSIONS = set()
USER_LOGIN_ATTEMPTS = {}
USER_PROFILES = {}  # 用户详细信息
FILE_STORAGE = {}  # 文件存储模拟
OPERATION_LOG = []  # 操作日志
UPLOAD_FOLDER = 'uploads'

# 创建上传目录
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def simulate_password_strength(password):
    """模拟密码强度评分"""
    score = len(password) // 2
    if any(c.isupper() for c in password):
        score += 1
    if any(c.isdigit() for c in password):
        score += 1
    return min(score, 5)

def update_active_sessions():
    """更新活跃会话数"""
    active_sessions.set(len(ACTIVE_SESSIONS))

@app.before_request
def before_request():
    """请求前置处理"""
    concurrent_requests.inc()
    request.start_time = time.time()
    
    # 记录请求大小
    if request.content_length:
        api_request_size.labels(endpoint=request.endpoint or 'unknown').observe(request.content_length)

@app.after_request
def after_request(response):
    """请求后置处理"""
    concurrent_requests.dec()
    
    # 记录API请求指标
    if hasattr(request, 'start_time'):
        duration = time.time() - request.start_time
        endpoint = request.endpoint or 'unknown'
        method = request.method
        status_code = str(response.status_code)
        
        # 记录请求总数和延迟
        api_requests_total.labels(method=method, endpoint=endpoint, status_code=status_code).inc()
        api_request_duration.labels(method=method, endpoint=endpoint).observe(duration)
    
    # 记录响应大小
    if hasattr(response, 'content_length') and response.content_length:
        response_size_hist.labels(endpoint=request.endpoint or 'unknown').observe(response.content_length)
        api_response_size.labels(endpoint=request.endpoint or 'unknown').observe(response.content_length)
    
    return response

@app.route("/login", methods=["POST"])
@request_summary.labels(method='login').time()
def login():
    start = time.time()
    
    try:
        data = request.get_json()
        if not data:
            error_rate.labels(error_type='invalid_json').inc()
            return jsonify({"status": "error", "message": "Invalid JSON"}), 400
            
        username = data.get("username")
        password = data.get("password")
        
        if not username or not password:
            error_rate.labels(error_type='missing_fields').inc()
            return jsonify({"status": "error", "message": "Missing fields"}), 400
        
        # 记录登录尝试
        USER_LOGIN_ATTEMPTS[username] = USER_LOGIN_ATTEMPTS.get(username, 0) + 1
        login_attempts_per_user.observe(USER_LOGIN_ATTEMPTS[username])
        
        # 模拟登录检查
        if USER_DB.get(username) == password:
            login_total.labels(status="200", method="password").inc()
            
            # 更新用户档案
            if username not in USER_PROFILES:
                USER_PROFILES[username] = {
                    "created_at": datetime.now().isoformat(),
                    "last_login": None,
                    "login_count": 0
                }
            
            USER_PROFILES[username]["last_login"] = datetime.now().isoformat()
            USER_PROFILES[username]["login_count"] = USER_PROFILES[username].get("login_count", 0) + 1
            
            # 模拟会话创建
            session_id = f"{username}_{int(time.time())}"
            ACTIVE_SESSIONS.add(session_id)
            update_active_sessions()
            
            # 重置失败计数
            USER_LOGIN_ATTEMPTS[username] = 0
            
            # 记录操作日志
            OPERATION_LOG.append({
                "timestamp": datetime.now().isoformat(),
                "operation": "user_login",
                "username": username,
                "ip": request.remote_addr
            })
            
            status_code = 200
            response_data = {"status": "ok", "session_id": session_id}
        else:
            login_total.labels(status="401", method="password").inc()
            
            # 防暴力破解：太多失败尝试
            if USER_LOGIN_ATTEMPTS[username] > 5:
                error_rate.labels(error_type='too_many_attempts').inc()
                time.sleep(1)  # 模拟限流
                
            status_code = 401
            response_data = {"status": "fail", "message": "Invalid credentials"}
            
    except Exception as e:
        error_rate.labels(error_type='internal_error').inc()
        status_code = 500
        response_data = {"status": "error", "message": "Internal server error"}
    
    finally:
        # 记录请求延迟
        duration = time.time() - start
        latency_hist.labels(method="login", endpoint="/login").observe(duration)
    
    return jsonify(response_data), status_code

@app.route("/register", methods=["POST"])
@request_summary.labels(method='register').time()
def register():
    start = time.time()
    
    try:
        data = request.get_json()
        if not data:
            error_rate.labels(error_type='invalid_json').inc()
            return jsonify({"status": "error", "message": "Invalid JSON"}), 400
            
        username = data.get("username")
        password = data.get("password")
        
        if not username or not password:
            error_rate.labels(error_type='missing_fields').inc()
            return jsonify({"status": "error", "message": "Missing fields"}), 400
        
        if username in USER_DB:
            reg_total.labels(status="409").inc()
            status_code = 409
            response_data = {"status": "exists", "message": "User already exists"}
        else:
            USER_DB[username] = password
            
            # 初始化用户档案
            USER_PROFILES[username] = {
                "created_at": datetime.now().isoformat(),
                "last_login": None,
                "login_count": 0
            }
            
            # 记录密码强度
            strength = simulate_password_strength(password)
            password_strength.observe(strength)
            
            USER_DB[username] = password
            reg_total.labels(status="200").inc()
            user_registrations_daily.inc()
            
            # 记录操作日志
            OPERATION_LOG.append({
                "timestamp": datetime.now().isoformat(),
                "operation": "user_registered",
                "username": username,
                "password_strength": strength,
                "ip": request.remote_addr
            })
            
            status_code = 200
            response_data = {
                "status": "created", 
                "message": "User registered successfully",
                "password_strength": strength
            }
            
    except Exception as e:
        error_rate.labels(error_type='internal_error').inc()
        status_code = 500
        response_data = {"status": "error", "message": "Internal server error"}
    
    finally:
        # 记录请求延迟
        duration = time.time() - start
        latency_hist.labels(method="register", endpoint="/register").observe(duration)
    
    return jsonify(response_data), status_code

@app.route("/logout", methods=["POST"])
def logout():
    """退出登录接口"""
    data = request.get_json() or {}
    session_id = data.get("session_id")
    
    if session_id and session_id in ACTIVE_SESSIONS:
        ACTIVE_SESSIONS.remove(session_id)
        update_active_sessions()
        return jsonify({"status": "ok", "message": "Logged out successfully"})
    
    return jsonify({"status": "error", "message": "Invalid session"}), 400

# ===================
# 用户管理接口
# ===================

@app.route("/users/<username>", methods=["GET"])
def get_user_info(username):
    """获取用户信息"""
    start_time = time.time()
    
    try:
        if username not in USER_DB:
            user_operations_total.labels(operation="get_user", status="not_found").inc()
            return jsonify({"status": "error", "message": "User not found"}), 404
        
        profile = USER_PROFILES.get(username, {})
        user_info = {
            "username": username,
            "created_at": profile.get("created_at", "unknown"),
            "last_login": profile.get("last_login", "never"),
            "login_count": profile.get("login_count", 0),
            "status": "active" if any(username in session for session in ACTIVE_SESSIONS) else "inactive"
        }
        
        user_operations_total.labels(operation="get_user", status="success").inc()
        return jsonify({"status": "ok", "data": user_info})
        
    except Exception as e:
        user_operations_total.labels(operation="get_user", status="error").inc()
        return jsonify({"status": "error", "message": "Internal server error"}), 500
    
    finally:
        duration = time.time() - start_time
        api_request_duration.labels(method="GET", endpoint="/users/<username>").observe(duration)

@app.route("/users/<username>/password", methods=["PUT"])
def change_password(username):
    """修改用户密码"""
    start_time = time.time()
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({"status": "error", "message": "Invalid JSON"}), 400
        
        old_password = data.get("old_password")
        new_password = data.get("new_password")
        
        if not old_password or not new_password:
            user_operations_total.labels(operation="change_password", status="invalid_input").inc()
            return jsonify({"status": "error", "message": "Missing fields"}), 400
        
        if username not in USER_DB:
            user_operations_total.labels(operation="change_password", status="not_found").inc()
            return jsonify({"status": "error", "message": "User not found"}), 404
        
        if USER_DB[username] != old_password:
            user_operations_total.labels(operation="change_password", status="unauthorized").inc()
            return jsonify({"status": "error", "message": "Invalid old password"}), 401
        
        # 更新密码
        USER_DB[username] = new_password
        
        # 记录新密码强度
        strength = simulate_password_strength(new_password)
        password_strength.observe(strength)
        
        # 记录操作日志
        OPERATION_LOG.append({
            "timestamp": datetime.now().isoformat(),
            "operation": "password_changed",
            "username": username,
            "ip": request.remote_addr
        })
        
        user_operations_total.labels(operation="change_password", status="success").inc()
        return jsonify({"status": "ok", "message": "Password changed successfully", "password_strength": strength})
        
    except Exception as e:
        user_operations_total.labels(operation="change_password", status="error").inc()
        return jsonify({"status": "error", "message": "Internal server error"}), 500
    
    finally:
        duration = time.time() - start_time
        api_request_duration.labels(method="PUT", endpoint="/users/<username>/password").observe(duration)

@app.route("/users/<username>", methods=["DELETE"])
def delete_user(username):
    """删除用户"""
    start_time = time.time()
    
    try:
        if username not in USER_DB:
            user_operations_total.labels(operation="delete_user", status="not_found").inc()
            return jsonify({"status": "error", "message": "User not found"}), 404
        
        # 删除用户数据
        del USER_DB[username]
        if username in USER_PROFILES:
            del USER_PROFILES[username]
        if username in USER_LOGIN_ATTEMPTS:
            del USER_LOGIN_ATTEMPTS[username]
        
        # 清理相关会话
        sessions_to_remove = [s for s in ACTIVE_SESSIONS if username in s]
        for session in sessions_to_remove:
            ACTIVE_SESSIONS.remove(session)
        update_active_sessions()
        
        # 记录操作日志
        OPERATION_LOG.append({
            "timestamp": datetime.now().isoformat(),
            "operation": "user_deleted",
            "username": username,
            "ip": request.remote_addr
        })
        
        user_operations_total.labels(operation="delete_user", status="success").inc()
        return jsonify({"status": "ok", "message": "User deleted successfully"})
        
    except Exception as e:
        user_operations_total.labels(operation="delete_user", status="error").inc()
        return jsonify({"status": "error", "message": "Internal server error"}), 500
    
    finally:
        duration = time.time() - start_time
        api_request_duration.labels(method="DELETE", endpoint="/users/<username>").observe(duration)

@app.route("/users", methods=["GET"])
def list_users():
    """获取所有用户列表"""
    start_time = time.time()
    
    try:
        users = []
        for username in USER_DB.keys():
            profile = USER_PROFILES.get(username, {})
            users.append({
                "username": username,
                "created_at": profile.get("created_at", "unknown"),
                "last_login": profile.get("last_login", "never"),
                "login_count": profile.get("login_count", 0),
                "status": "active" if any(username in session for session in ACTIVE_SESSIONS) else "inactive"
            })
        
        user_operations_total.labels(operation="list_users", status="success").inc()
        return jsonify({"status": "ok", "data": users, "total": len(users)})
        
    except Exception as e:
        user_operations_total.labels(operation="list_users", status="error").inc()
        return jsonify({"status": "error", "message": "Internal server error"}), 500
    
    finally:
        duration = time.time() - start_time
        api_request_duration.labels(method="GET", endpoint="/users").observe(duration)

@app.route("/health")
def health():
    """健康检查接口"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "active_sessions": len(ACTIVE_SESSIONS),
        "registered_users": len(USER_DB)
    })

# ===================
# 数据统计接口
# ===================

@app.route("/stats/users", methods=["GET"])
def user_stats():
    """用户统计数据"""
    start_time = time.time()
    
    try:
        # 计算统计数据
        total_users = len(USER_DB)
        active_sessions_count = len(ACTIVE_SESSIONS)
        
        # 计算今日注册用户
        today = datetime.now().date()
        today_registrations = sum(1 for profile in USER_PROFILES.values() 
                                if profile.get("created_at", "").startswith(str(today)))
        
        # 计算平均登录次数
        total_logins = sum(profile.get("login_count", 0) for profile in USER_PROFILES.values())
        avg_logins = total_logins / total_users if total_users > 0 else 0
        
        stats = {
            "total_users": total_users,
            "active_sessions": active_sessions_count,
            "today_registrations": today_registrations,
            "total_logins": total_logins,
            "average_logins_per_user": round(avg_logins, 2),
            "failed_login_attempts": sum(USER_LOGIN_ATTEMPTS.values())
        }
        
        return jsonify({"status": "ok", "data": stats})
        
    except Exception as e:
        return jsonify({"status": "error", "message": "Internal server error"}), 500
    
    finally:
        duration = time.time() - start_time
        api_request_duration.labels(method="GET", endpoint="/stats/users").observe(duration)

@app.route("/stats/system", methods=["GET"])
def system_stats():
    """系统统计数据"""
    start_time = time.time()
    
    try:
        # 计算系统统计
        uptime_seconds = time.time() - app.start_time if hasattr(app, 'start_time') else 0
        
        stats = {
            "uptime_seconds": int(uptime_seconds),
            "total_operations": len(OPERATION_LOG),
            "files_stored": len(FILE_STORAGE),
            "memory_usage_mb": {
                "users": len(str(USER_DB)) / 1024,
                "sessions": len(str(ACTIVE_SESSIONS)) / 1024,
                "files": len(str(FILE_STORAGE)) / 1024,
                "logs": len(str(OPERATION_LOG)) / 1024
            }
        }
        
        return jsonify({"status": "ok", "data": stats})
        
    except Exception as e:
        return jsonify({"status": "error", "message": "Internal server error"}), 500
    
    finally:
        duration = time.time() - start_time
        api_request_duration.labels(method="GET", endpoint="/stats/system").observe(duration)

# ===================
# 文件操作接口
# ===================

@app.route("/files/upload", methods=["POST"])
def upload_file():
    """文件上传接口"""
    start_time = time.time()
    
    try:
        if 'file' not in request.files:
            file_operations_total.labels(operation="upload", file_type="unknown", status="no_file").inc()
            return jsonify({"status": "error", "message": "No file provided"}), 400
        
        file = request.files['file']
        if file.filename == '':
            file_operations_total.labels(operation="upload", file_type="unknown", status="empty_name").inc()
            return jsonify({"status": "error", "message": "No file selected"}), 400
        
        # 安全文件名
        filename = secure_filename(file.filename)
        file_ext = filename.split('.')[-1].lower() if '.' in filename else 'unknown'
        
        # 模拟文件存储
        file_id = hashlib.md5(f"{filename}_{time.time()}".encode()).hexdigest()
        file_content = file.read()
        file_size = len(file_content)
        
        # 记录文件信息
        FILE_STORAGE[file_id] = {
            "filename": filename,
            "size": file_size,
            "type": file_ext,
            "uploaded_at": datetime.now().isoformat(),
            "content": file_content  # 生产环境应该存储在文件系统或对象存储
        }
        
        # 记录指标
        file_operations_total.labels(operation="upload", file_type=file_ext, status="success").inc()
        file_size_hist.observe(file_size)
        
        # 记录操作日志
        OPERATION_LOG.append({
            "timestamp": datetime.now().isoformat(),
            "operation": "file_uploaded",
            "file_id": file_id,
            "filename": filename,
            "size": file_size,
            "ip": request.remote_addr
        })
        
        return jsonify({
            "status": "ok", 
            "message": "File uploaded successfully",
            "file_id": file_id,
            "filename": filename,
            "size": file_size
        })
        
    except Exception as e:
        file_operations_total.labels(operation="upload", file_type="unknown", status="error").inc()
        return jsonify({"status": "error", "message": "Internal server error"}), 500
    
    finally:
        duration = time.time() - start_time
        api_request_duration.labels(method="POST", endpoint="/files/upload").observe(duration)

@app.route("/files/<file_id>/download", methods=["GET"])
def download_file(file_id):
    """文件下载接口"""
    start_time = time.time()
    
    try:
        if file_id not in FILE_STORAGE:
            file_operations_total.labels(operation="download", file_type="unknown", status="not_found").inc()
            return jsonify({"status": "error", "message": "File not found"}), 404
        
        file_info = FILE_STORAGE[file_id]
        file_operations_total.labels(operation="download", file_type=file_info["type"], status="success").inc()
        
        # 记录操作日志
        OPERATION_LOG.append({
            "timestamp": datetime.now().isoformat(),
            "operation": "file_downloaded",
            "file_id": file_id,
            "filename": file_info["filename"],
            "ip": request.remote_addr
        })
        
        # 模拟文件下载（生产环境应该返回实际文件）
        return jsonify({
            "status": "ok",
            "filename": file_info["filename"],
            "size": file_info["size"],
            "download_url": f"/files/{file_id}/content"
        })
        
    except Exception as e:
        file_operations_total.labels(operation="download", file_type="unknown", status="error").inc()
        return jsonify({"status": "error", "message": "Internal server error"}), 500
    
    finally:
        duration = time.time() - start_time
        api_request_duration.labels(method="GET", endpoint="/files/<file_id>/download").observe(duration)

@app.route("/files", methods=["GET"])
def list_files():
    """文件列表接口"""
    start_time = time.time()
    
    try:
        files = []
        for file_id, file_info in FILE_STORAGE.items():
            files.append({
                "file_id": file_id,
                "filename": file_info["filename"],
                "size": file_info["size"],
                "type": file_info["type"],
                "uploaded_at": file_info["uploaded_at"]
            })
        
        # 按上传时间排序
        files.sort(key=lambda x: x["uploaded_at"], reverse=True)
        
        file_operations_total.labels(operation="list", file_type="all", status="success").inc()
        return jsonify({"status": "ok", "data": files, "total": len(files)})
        
    except Exception as e:
        file_operations_total.labels(operation="list", file_type="all", status="error").inc()
        return jsonify({"status": "error", "message": "Internal server error"}), 500
    
    finally:
        duration = time.time() - start_time
        api_request_duration.labels(method="GET", endpoint="/files").observe(duration)

# ===================
# 系统管理接口
# ===================

@app.route("/admin/reset", methods=["POST"])
def reset_system():
    """重置系统数据"""
    start_time = time.time()
    
    try:
        data = request.get_json() or {}
        confirm = data.get("confirm", False)
        
        if not confirm:
            return jsonify({"status": "error", "message": "Please set confirm=true to reset system"}), 400
        
        # 重置所有数据
        USER_DB.clear()
        ACTIVE_SESSIONS.clear()
        USER_LOGIN_ATTEMPTS.clear()
        USER_PROFILES.clear()
        FILE_STORAGE.clear()
        OPERATION_LOG.clear()
        
        update_active_sessions()
        
        # 记录操作日志
        OPERATION_LOG.append({
            "timestamp": datetime.now().isoformat(),
            "operation": "system_reset",
            "ip": request.remote_addr
        })
        
        return jsonify({"status": "ok", "message": "System reset successfully"})
        
    except Exception as e:
        return jsonify({"status": "error", "message": "Internal server error"}), 500
    
    finally:
        duration = time.time() - start_time
        api_request_duration.labels(method="POST", endpoint="/admin/reset").observe(duration)

@app.route("/admin/export", methods=["GET"])
def export_data():
    """导出系统数据"""
    start_time = time.time()
    
    try:
        export_data = {
            "timestamp": datetime.now().isoformat(),
            "users": {username: {
                "profile": USER_PROFILES.get(username, {}),
                "login_attempts": USER_LOGIN_ATTEMPTS.get(username, 0)
            } for username in USER_DB.keys()},
            "active_sessions": list(ACTIVE_SESSIONS),
            "operation_log": OPERATION_LOG[-100:],  # 最近100条操作记录
            "file_metadata": {file_id: {
                "filename": info["filename"],
                "size": info["size"],
                "type": info["type"],
                "uploaded_at": info["uploaded_at"]
            } for file_id, info in FILE_STORAGE.items()}
        }
        
        # 记录导出数据大小
        export_json = json.dumps(export_data, ensure_ascii=False, indent=2)
        export_size = len(export_json.encode('utf-8'))
        data_export_size.observe(export_size)
        
        # 记录操作日志
        OPERATION_LOG.append({
            "timestamp": datetime.now().isoformat(),
            "operation": "data_exported",
            "export_size": export_size,
            "ip": request.remote_addr
        })
        
        return jsonify({"status": "ok", "data": export_data, "export_size": export_size})
        
    except Exception as e:
        return jsonify({"status": "error", "message": "Internal server error"}), 500
    
    finally:
        duration = time.time() - start_time
        api_request_duration.labels(method="GET", endpoint="/admin/export").observe(duration)

@app.route("/admin/logs", methods=["GET"])
def get_operation_logs():
    """获取操作日志"""
    start_time = time.time()
    
    try:
        # 获取查询参数
        limit = int(request.args.get('limit', 50))
        offset = int(request.args.get('offset', 0))
        operation = request.args.get('operation', '')
        
        # 过滤日志
        filtered_logs = OPERATION_LOG
        if operation:
            filtered_logs = [log for log in OPERATION_LOG if log.get('operation') == operation]
        
        # 分页
        total = len(filtered_logs)
        logs = filtered_logs[offset:offset + limit]
        
        return jsonify({
            "status": "ok", 
            "data": logs, 
            "total": total,
            "limit": limit,
            "offset": offset
        })
        
    except Exception as e:
        return jsonify({"status": "error", "message": "Internal server error"}), 500
    
    finally:
        duration = time.time() - start_time
        api_request_duration.labels(method="GET", endpoint="/admin/logs").observe(duration)

@app.route("/metrics")
def metrics():
    """暴露 Prometheus 指标"""
    return generate_latest()

# 模拟后台任务：清理过期会话
def cleanup_sessions():
    """清理过期会话（模拟）"""
    import threading
    timer = threading.Timer(300.0, cleanup_sessions)  # 5分钟清理一次
    timer.daemon = True
    timer.start()
    
    # 模拟随机清理一些会话
    if len(ACTIVE_SESSIONS) > 0:
        sessions_to_remove = random.sample(list(ACTIVE_SESSIONS), 
                                         min(2, len(ACTIVE_SESSIONS)))
        for session in sessions_to_remove:
            ACTIVE_SESSIONS.discard(session)
        update_active_sessions()

if __name__ == "__main__":
    # 记录应用启动时间
    app.start_time = time.time()
    
    # 启动后台任务
    cleanup_sessions()
    
    # 初始化指标
    update_active_sessions()
    
    print("🚀 Login Monitor with Enhanced Metrics is starting...")
    print("📊 Prometheus metrics: http://localhost:5000/metrics")
    print("🛋 Health check: http://localhost:5000/health")
    print("👥 User management: http://localhost:5000/users")
    print("📈 Statistics: http://localhost:5000/stats/users")
    print("📁 File operations: http://localhost:5000/files")
    print("⚙️  Admin panel: http://localhost:5000/admin/logs")
    
    app.run(host="0.0.0.0", port=5000, debug=True)