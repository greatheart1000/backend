"""
Code Analysis Agent 测试脚本

测试所有主要功能：
1. 服务健康检查
2. 基本代码分析
3. 带验证的代码分析
4. 错误处理
"""

import requests
import json
import os
import zipfile
import tempfile
import time
from pathlib import Path

# 配置
BASE_URL = "http://localhost:8000"
TIMEOUT = 60  # 请求超时时间（秒）


class Colors:
    """终端颜色"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'
    BOLD = '\033[1m'


def print_success(msg):
    print(f"{Colors.GREEN}✓{Colors.END} {msg}")


def print_error(msg):
    print(f"{Colors.RED}✗{Colors.END} {msg}")


def print_info(msg):
    print(f"{Colors.BLUE}ℹ{Colors.END} {msg}")


def print_warning(msg):
    print(f"{Colors.YELLOW}⚠{Colors.END} {msg}")


def print_header(msg):
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{msg}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.END}\n")


def create_test_project():
    """创建测试用的示例项目"""
    print_info("创建测试项目...")
    
    # 创建临时目录
    temp_dir = tempfile.mkdtemp()
    project_dir = os.path.join(temp_dir, "test_project")
    os.makedirs(project_dir)
    
    # 创建示例Python项目
    # 1. app.py
    with open(os.path.join(project_dir, "app.py"), "w", encoding="utf-8") as f:
        f.write("""
from flask import Flask, request, jsonify

app = Flask(__name__)

# 用户数据存储（简化版）
users = {}

@app.route('/register', methods=['POST'])
def register():
    '''用户注册功能'''
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    if username in users:
        return jsonify({'error': '用户已存在'}), 400
    
    users[username] = password
    return jsonify({'message': '注册成功', 'username': username}), 201

@app.route('/login', methods=['POST'])
def login():
    '''用户登录功能'''
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    if username not in users:
        return jsonify({'error': '用户不存在'}), 404
    
    if users[username] != password:
        return jsonify({'error': '密码错误'}), 401
    
    return jsonify({'message': '登录成功', 'username': username}), 200

@app.route('/users', methods=['GET'])
def get_users():
    '''获取所有用户列表'''
    return jsonify({'users': list(users.keys())}), 200

if __name__ == '__main__':
    app.run(debug=True, port=5000)
""")
    
    # 2. requirements.txt
    with open(os.path.join(project_dir, "requirements.txt"), "w") as f:
        f.write("flask>=2.0.0\n")
    
    # 3. README.md
    with open(os.path.join(project_dir, "README.md"), "w") as f:
        f.write("""# Test Project

一个简单的用户管理系统。

## 功能
- 用户注册
- 用户登录
- 获取用户列表
""")
    
    # 创建ZIP文件
    zip_path = os.path.join(temp_dir, "test_project.zip")
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(project_dir):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, temp_dir)
                zipf.write(file_path, arcname)
    
    print_success(f"测试项目已创建: {zip_path}")
    return zip_path


def test_health_check():
    """测试1: 健康检查"""
    print_header("测试1: 服务健康检查")
    
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            print_success("服务健康检查通过")
            print(f"  状态: {data.get('status')}")
            print(f"  时间: {data.get('timestamp')}")
            print(f"  API配置: {data.get('api_configured')}")
            return True
        else:
            print_error(f"健康检查失败: HTTP {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print_error("无法连接到服务，请确保服务正在运行")
        print_info("启动服务: docker-compose up -d")
        return False
    except Exception as e:
        print_error(f"健康检查异常: {str(e)}")
        return False


def test_root_endpoint():
    """测试2: 根端点"""
    print_header("测试2: 根端点")
    
    try:
        response = requests.get(f"{BASE_URL}/", timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            print_success("根端点访问成功")
            print(f"  消息: {data.get('message')}")
            print(f"  版本: {data.get('version')}")
            return True
        else:
            print_error(f"根端点访问失败: HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print_error(f"根端点测试异常: {str(e)}")
        return False


def test_basic_analysis(zip_path):
    """测试3: 基本代码分析"""
    print_header("测试3: 基本代码分析（不含验证）")
    
    try:
        print_info("上传测试项目进行分析...")
        
        with open(zip_path, 'rb') as f:
            files = {
                'code_zip': ('test_project.zip', f, 'application/zip')
            }
            data = {
                'problem_description': '''
                实现以下功能：
                1. 用户注册功能：接收用户名和密码，验证用户是否已存在
                2. 用户登录功能：验证用户名和密码是否正确
                3. 获取用户列表功能：返回所有注册用户
                ''',
                'enable_verification': 'false'
            }
            
            print_info("等待分析结果...")
            response = requests.post(
                f"{BASE_URL}/analyze",
                files=files,
                data=data,
                timeout=TIMEOUT
            )
        
        if response.status_code == 200:
            result = response.json()
            print_success("代码分析成功")
            
            # 显示功能分析结果
            features = result.get('feature_analysis', [])
            print(f"\n发现 {len(features)} 个功能点:")
            
            for i, feature in enumerate(features, 1):
                print(f"\n  {i}. {Colors.BOLD}{feature['feature_description']}{Colors.END}")
                locations = feature.get('implementation_location', [])
                for loc in locations:
                    print(f"     → 文件: {loc['file']}")
                    print(f"       函数: {loc['function']} (行 {loc['lines']})")
            
            # 显示执行计划
            plan = result.get('execution_plan_suggestion', '')
            if plan:
                print(f"\n  {Colors.BOLD}执行计划:{Colors.END}")
                for line in plan.split('\n'):
                    if line.strip():
                        print(f"    • {line.strip()}")
            
            return True
        else:
            print_error(f"分析失败: HTTP {response.status_code}")
            print(f"  错误信息: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print_error(f"请求超时（超过{TIMEOUT}秒）")
        print_warning("代码分析可能需要较长时间，请增加TIMEOUT值")
        return False
    except Exception as e:
        print_error(f"分析异常: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return False


def test_analysis_with_verification(zip_path):
    """测试4: 带验证的代码分析"""
    print_header("测试4: 带测试验证的代码分析")
    
    print_warning("此测试可能需要较长时间（生成并执行测试代码）")
    user_input = input("是否继续？(y/n): ").strip().lower()
    
    if user_input != 'y':
        print_info("跳过验证测试")
        return None
    
    try:
        print_info("上传测试项目进行带验证的分析...")
        
        with open(zip_path, 'rb') as f:
            files = {
                'code_zip': ('test_project.zip', f, 'application/zip')
            }
            data = {
                'problem_description': '实现用户注册和登录功能',
                'enable_verification': 'true'
            }
            
            print_info("等待分析和测试执行...")
            response = requests.post(
                f"{BASE_URL}/analyze",
                files=files,
                data=data,
                timeout=TIMEOUT * 2  # 验证需要更长时间
            )
        
        if response.status_code == 200:
            result = response.json()
            print_success("带验证的分析成功")
            
            # 显示验证结果
            verification = result.get('functional_verification')
            if verification:
                print(f"\n  {Colors.BOLD}测试验证结果:{Colors.END}")
                
                test_result = verification.get('execution_result', {})
                tests_passed = test_result.get('tests_passed', False)
                
                if tests_passed:
                    print_success(f"  测试通过")
                else:
                    print_error(f"  测试失败")
                
                log = test_result.get('log', '')
                if log:
                    print(f"\n  {Colors.BOLD}测试日志:{Colors.END}")
                    for line in log.split('\n')[:10]:  # 只显示前10行
                        print(f"    {line}")
                
                # 显示生成的测试代码（前几行）
                test_code = verification.get('generated_test_code', '')
                if test_code:
                    print(f"\n  {Colors.BOLD}生成的测试代码（前10行）:{Colors.END}")
                    for line in test_code.split('\n')[:10]:
                        print(f"    {line}")
            
            return True
        else:
            print_error(f"带验证的分析失败: HTTP {response.status_code}")
            print(f"  错误信息: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print_error(f"请求超时（超过{TIMEOUT * 2}秒）")
        return False
    except Exception as e:
        print_error(f"分析异常: {str(e)}")
        return False


def test_error_handling():
    """测试5: 错误处理"""
    print_header("测试5: 错误处理")
    
    tests_passed = 0
    total_tests = 3
    
    # 测试5.1: 空描述
    print_info("5.1 测试空描述...")
    try:
        # 创建一个临时ZIP文件
        with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as tmp:
            with zipfile.ZipFile(tmp.name, 'w') as zipf:
                zipf.writestr('test.py', 'print("hello")')
            tmp_path = tmp.name
        
        with open(tmp_path, 'rb') as f:
            files = {'code_zip': ('test.zip', f, 'application/zip')}
            data = {'problem_description': ''}
            response = requests.post(f"{BASE_URL}/analyze", files=files, data=data, timeout=10)
        
        os.unlink(tmp_path)
        
        if response.status_code == 400:
            print_success("  正确处理空描述错误")
            tests_passed += 1
        else:
            print_error(f"  未正确处理空描述: HTTP {response.status_code}")
    except Exception as e:
        print_error(f"  测试异常: {str(e)}")
    
    # 测试5.2: 非ZIP文件
    print_info("5.2 测试非ZIP文件...")
    try:
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as tmp:
            tmp.write(b"This is not a zip file")
            tmp_path = tmp.name
        
        with open(tmp_path, 'rb') as f:
            files = {'code_zip': ('test.txt', f, 'text/plain')}
            data = {'problem_description': 'Test'}
            response = requests.post(f"{BASE_URL}/analyze", files=files, data=data, timeout=10)
        
        os.unlink(tmp_path)
        
        if response.status_code == 400:
            print_success("  正确处理非ZIP文件错误")
            tests_passed += 1
        else:
            print_error(f"  未正确处理非ZIP文件: HTTP {response.status_code}")
    except Exception as e:
        print_error(f"  测试异常: {str(e)}")
    
    # 测试5.3: 缺少文件
    print_info("5.3 测试缺少文件...")
    try:
        data = {'problem_description': 'Test'}
        response = requests.post(f"{BASE_URL}/analyze", data=data, timeout=10)
        
        if response.status_code == 422:  # FastAPI validation error
            print_success("  正确处理缺少文件错误")
            tests_passed += 1
        else:
            print_error(f"  未正确处理缺少文件: HTTP {response.status_code}")
    except Exception as e:
        print_error(f"  测试异常: {str(e)}")
    
    print(f"\n错误处理测试: {tests_passed}/{total_tests} 通过")
    return tests_passed == total_tests


def test_api_documentation():
    """测试6: API文档访问"""
    print_header("测试6: API文档访问")
    
    try:
        response = requests.get(f"{BASE_URL}/docs", timeout=5)
        
        if response.status_code == 200 and 'swagger' in response.text.lower():
            print_success("API文档可访问")
            print_info(f"  访问地址: {BASE_URL}/docs")
            return True
        else:
            print_error("API文档访问失败")
            return False
            
    except Exception as e:
        print_error(f"API文档测试异常: {str(e)}")
        return False


def run_all_tests():
    """运行所有测试"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}")
    print("╔═══════════════════════════════════════════════════════════╗")
    print("║          Code Analysis Agent 功能测试套件                ║")
    print("╚═══════════════════════════════════════════════════════════╝")
    print(f"{Colors.END}")
    
    print_info(f"测试目标: {BASE_URL}")
    print_info(f"超时设置: {TIMEOUT}秒\n")
    
    results = {}
    zip_path = None
    
    # 运行测试
    results['health'] = test_health_check()
    
    if not results['health']:
        print_error("\n服务未运行，停止测试")
        print_info("请先启动服务: docker-compose up -d")
        return
    
    results['root'] = test_root_endpoint()
    
    # 创建测试项目
    try:
        zip_path = create_test_project()
    except Exception as e:
        print_error(f"创建测试项目失败: {str(e)}")
        return
    
    results['basic_analysis'] = test_basic_analysis(zip_path)
    results['verification'] = test_analysis_with_verification(zip_path)
    results['error_handling'] = test_error_handling()
    results['api_docs'] = test_api_documentation()
    
    # 清理临时文件
    if zip_path and os.path.exists(zip_path):
        import shutil
        shutil.rmtree(os.path.dirname(zip_path), ignore_errors=True)
        print_info("已清理临时文件")
    
    # 显示测试总结
    print_header("测试总结")
    
    passed = sum(1 for v in results.values() if v is True)
    total = sum(1 for v in results.values() if v is not None)
    
    print(f"\n总计: {passed}/{total} 测试通过\n")
    
    for test_name, result in results.items():
        if result is None:
            status = f"{Colors.YELLOW}⊘ 跳过{Colors.END}"
        elif result:
            status = f"{Colors.GREEN}✓ 通过{Colors.END}"
        else:
            status = f"{Colors.RED}✗ 失败{Colors.END}"
        
        test_display = test_name.replace('_', ' ').title()
        print(f"  {status}  {test_display}")
    
    print(f"\n{Colors.BOLD}", end='')
    if passed == total:
        print(f"{Colors.GREEN}🎉 所有测试通过！{Colors.END}")
    elif passed > 0:
        print(f"{Colors.YELLOW}⚠️  部分测试失败{Colors.END}")
    else:
        print(f"{Colors.RED}❌ 所有测试失败{Colors.END}")
    
    print()


if __name__ == "__main__":
    try:
        run_all_tests()
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}测试被用户中断{Colors.END}")
    except Exception as e:
        print(f"\n\n{Colors.RED}测试过程发生异常: {str(e)}{Colors.END}")
        import traceback
        print(traceback.format_exc())
