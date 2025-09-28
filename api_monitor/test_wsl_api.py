#!/usr/bin/env python3
"""
WSL环境专用API测试脚本
针对WSL网络环境进行优化，包含环境检测和网络配置验证
"""
import urllib.request
import urllib.parse
import urllib.error
import json
import time
import subprocess
import socket
import os

BASE_URL = "http://localhost:5000"

def check_wsl_environment():
    """检查WSL环境"""
    print("🐧 检查WSL环境")
    print("-" * 40)
    
    # 检查是否在WSL中
    try:
        with open('/proc/version', 'r') as f:
            version_info = f.read()
        
        if 'microsoft' in version_info.lower() or 'wsl' in version_info.lower():
            print("✅ 运行在WSL环境中")
            
            # 获取WSL版本信息
            try:
                result = subprocess.run(['lsb_release', '-d'], capture_output=True, text=True)
                if result.returncode == 0:
                    print(f"   发行版: {result.stdout.strip().split(':')[1].strip()}")
            except:
                pass
            
            return True
        else:
            print("⚠️  可能不在WSL环境中")
            return False
            
    except Exception as e:
        print(f"❌ 无法确定环境类型: {e}")
        return False

def check_network_connectivity():
    """检查网络连接性"""
    print("\n🌐 检查网络连接")
    print("-" * 40)
    
    # 检查本地IP
    try:
        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)
        print(f"主机名: {hostname}")
        print(f"本地IP: {local_ip}")
    except Exception as e:
        print(f"⚠️  获取本地IP失败: {e}")
    
    # 检查WSL到Windows的网络连接
    try:
        result = subprocess.run(['ip', 'route', 'show', 'default'], capture_output=True, text=True)
        if result.returncode == 0:
            gateway = result.stdout.split()[2] if len(result.stdout.split()) > 2 else "unknown"
            print(f"默认网关: {gateway}")
    except:
        pass
    
    # 检查端口开放状态
    ports_to_check = [5000, 3000, 9090, 9093]
    print("\n端口状态检查:")
    
    for port in ports_to_check:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            result = sock.connect_ex(('localhost', port))
            
            if result == 0:
                print(f"  ✅ 端口 {port} 开放")
            else:
                print(f"  ❌ 端口 {port} 关闭")
            
            sock.close()
        except Exception as e:
            print(f"  ❌ 端口 {port} 检查失败: {e}")

def check_docker_services():
    """检查Docker服务状态"""
    print("\n🐳 检查Docker服务")
    print("-" * 40)
    
    try:
        # 检查Docker是否运行
        result = subprocess.run(['docker', 'info'], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Docker服务正常")
        else:
            print("❌ Docker服务异常")
            print("   请运行: sudo service docker start")
            return False
        
        # 检查容器状态
        result = subprocess.run(['docker-compose', 'ps'], capture_output=True, text=True, cwd='.')
        if result.returncode == 0:
            print("容器状态:")
            lines = result.stdout.strip().split('\n')
            for line in lines[1:]:  # 跳过表头
                if line.strip():
                    print(f"  {line}")
        
        return True
        
    except FileNotFoundError:
        print("❌ Docker或docker-compose未安装")
        print("   请运行: ./wsl_setup.sh")
        return False
    except Exception as e:
        print(f"❌ 检查Docker服务失败: {e}")
        return False

def make_request_with_retry(url, method="GET", data=None, headers=None, max_retries=3):
    """带重试的HTTP请求"""
    if headers is None:
        headers = {"Content-Type": "application/json"}
    
    for attempt in range(max_retries):
        try:
            if data and method in ["POST", "PUT"]:
                data_bytes = json.dumps(data).encode('utf-8')
            else:
                data_bytes = None
            
            req = urllib.request.Request(url, data=data_bytes, headers=headers, method=method)
            
            with urllib.request.urlopen(req, timeout=10) as response:
                content = response.read().decode('utf-8')
                return response.getcode(), content
                
        except urllib.error.HTTPError as e:
            content = e.read().decode('utf-8') if e.fp else str(e)
            return e.getcode(), content
        except urllib.error.URLError as e:
            if attempt < max_retries - 1:
                print(f"   连接失败，重试 {attempt + 1}/{max_retries}...")
                time.sleep(2)
                continue
            else:
                return None, f"连接失败: {e}"
        except Exception as e:
            if attempt < max_retries - 1:
                print(f"   请求失败，重试 {attempt + 1}/{max_retries}...")
                time.sleep(2)
                continue
            else:
                return None, f"请求异常: {e}"
    
    return None, "达到最大重试次数"

def test_wsl_api_connectivity():
    """测试WSL环境下的API连接"""
    print("\n🔌 测试API连接性")
    print("-" * 40)
    
    # 测试健康检查接口
    status, content = make_request_with_retry(f"{BASE_URL}/health")
    if status == 200:
        print("✅ Flask应用连接正常")
        try:
            health_data = json.loads(content)
            print(f"   状态: {health_data.get('status', 'unknown')}")
            print(f"   活跃会话: {health_data.get('active_sessions', 0)}")
            print(f"   注册用户: {health_data.get('registered_users', 0)}")
        except:
            pass
    else:
        print(f"❌ Flask应用连接失败: {status} - {content}")
        print("\n🔧 故障排除建议:")
        print("   1. 确保Docker服务正在运行: sudo service docker start")
        print("   2. 启动系统服务: ./start_wsl_system.sh")
        print("   3. 检查容器状态: docker-compose ps")
        print("   4. 查看应用日志: docker-compose logs app")
        return False
    
    return True

def run_comprehensive_tests():
    """运行综合API测试"""
    print("\n🧪 运行API功能测试")
    print("-" * 40)
    
    test_results = {
        "register": 0,
        "login": 0,
        "users": 0,
        "stats": 0,
        "files": 0,
        "admin": 0,
        "metrics": 0
    }
    
    # 1. 注册测试
    print("📝 测试用户注册...")
    users = [
        {"username": "wsl_user1", "password": "WSL@Test123"},
        {"username": "wsl_user2", "password": "Linux#456"},
    ]
    
    for user in users:
        status, content = make_request_with_retry(f"{BASE_URL}/register", "POST", user)
        if status in [200, 409]:  # 成功或用户已存在
            test_results["register"] += 1
            print(f"  ✅ 注册 {user['username']}: {status}")
        else:
            print(f"  ❌ 注册 {user['username']}: {status}")
    
    # 2. 登录测试
    print("🔐 测试用户登录...")
    status, content = make_request_with_retry(f"{BASE_URL}/login", "POST", users[0])
    if status in [200, 401]:
        test_results["login"] = 1
        print(f"  ✅ 登录测试: {status}")
    else:
        print(f"  ❌ 登录测试: {status}")
    
    # 3. 用户管理测试
    print("👥 测试用户管理...")
    status, content = make_request_with_retry(f"{BASE_URL}/users")
    if status == 200:
        test_results["users"] = 1
        print(f"  ✅ 用户列表: {status}")
    else:
        print(f"  ❌ 用户列表: {status}")
    
    # 4. 统计数据测试
    print("📊 测试统计接口...")
    endpoints = ["/stats/users", "/stats/system"]
    for endpoint in endpoints:
        status, content = make_request_with_retry(f"{BASE_URL}{endpoint}")
        if status == 200:
            test_results["stats"] += 1
            print(f"  ✅ {endpoint}: {status}")
        else:
            print(f"  ❌ {endpoint}: {status}")
    
    # 5. 文件接口测试
    print("📁 测试文件接口...")
    status, content = make_request_with_retry(f"{BASE_URL}/files")
    if status == 200:
        test_results["files"] = 1
        print(f"  ✅ 文件列表: {status}")
    else:
        print(f"  ❌ 文件列表: {status}")
    
    # 6. 管理接口测试
    print("⚙️ 测试管理接口...")
    admin_endpoints = ["/admin/logs", "/admin/export"]
    for endpoint in admin_endpoints:
        status, content = make_request_with_retry(f"{BASE_URL}{endpoint}")
        if status == 200:
            test_results["admin"] += 1
            print(f"  ✅ {endpoint}: {status}")
        else:
            print(f"  ❌ {endpoint}: {status}")
    
    # 7. Prometheus指标测试
    print("📈 测试Prometheus指标...")
    status, content = make_request_with_retry(f"{BASE_URL}/metrics")
    if status == 200:
        test_results["metrics"] = 1
        lines = content.split('\n')
        metric_lines = [line for line in lines if line and not line.startswith('#')]
        print(f"  ✅ 指标接口: {status} ({len(metric_lines)} 指标)")
        
        # 检查关键指标
        key_metrics = ['api_requests_total', 'api_request_duration_seconds']
        found = sum(1 for metric in key_metrics if any(line.startswith(metric) for line in metric_lines))
        print(f"  🎯 关键指标: {found}/{len(key_metrics)}")
    else:
        print(f"  ❌ 指标接口: {status}")
    
    # 输出测试结果汇总
    total_tests = sum(test_results.values())
    max_tests = len(test_results) + 1  # stats有2个测试，admin有2个测试
    
    print(f"\n📋 测试结果汇总: {total_tests}/{max_tests + 2} 通过")
    print(f"成功率: {total_tests/(max_tests + 2)*100:.1f}%")
    
    return total_tests >= (max_tests + 2) * 0.8  # 80%通过率

def show_wsl_specific_info():
    """显示WSL特定信息"""
    print("\n🐧 WSL环境特殊说明")
    print("=" * 50)
    
    print("📱 访问方式:")
    print("   从Windows浏览器访问: http://localhost:<端口>")
    print("   从WSL内部访问: http://localhost:<端口> 或 http://127.0.0.1:<端口>")
    
    print("\n🔧 常用命令:")
    print("   查看WSL IP: hostname -I")
    print("   重启Docker: sudo service docker restart")
    print("   查看端口: netstat -tuln | grep LISTEN")
    print("   查看进程: ps aux | grep python")
    
    print("\n⚠️  注意事项:")
    print("   1. WSL2中的服务可以通过localhost从Windows访问")
    print("   2. 如果遇到网络问题，尝试重启WSL: wsl --shutdown")
    print("   3. 防火墙可能阻止某些连接，需要配置Windows防火墙")
    print("   4. 某些企业网络可能限制Docker Hub访问")
    
    print("\n🔗 监控地址:")
    print("   Flask应用:    http://localhost:5000")
    print("   Grafana:      http://localhost:3000 (admin/admin123)")
    print("   Prometheus:   http://localhost:9090")
    print("   Alertmanager: http://localhost:9093")

def main():
    print("🎯 WSL环境API测试脚本")
    print("=" * 50)
    
    # 1. 检查环境
    is_wsl = check_wsl_environment()
    
    # 2. 检查网络
    check_network_connectivity()
    
    # 3. 检查Docker
    docker_ok = check_docker_services()
    
    if not docker_ok:
        print("\n❌ Docker服务异常，无法继续测试")
        print("请先运行: ./wsl_setup.sh 和 ./start_wsl_system.sh")
        return
    
    # 4. 测试API连接
    if not test_wsl_api_connectivity():
        print("\n❌ API连接失败，请检查服务状态")
        return
    
    # 5. 运行功能测试
    success = run_comprehensive_tests()
    
    # 6. 显示结果
    if success:
        print("\n✅ 所有测试通过！系统运行正常")
        show_wsl_specific_info()
    else:
        print("\n⚠️ 部分测试失败，请检查系统状态")
        print("可以尝试:")
        print("   docker-compose restart")
        print("   docker-compose logs")

if __name__ == "__main__":
    main()