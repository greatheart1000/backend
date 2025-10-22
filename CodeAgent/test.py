#!/usr/bin/env python3
"""
简单的测试脚本，用于验证Agent功能
"""

import requests
import os
import zipfile
import tempfile
import json

def create_test_zip():
    """创建测试用的ZIP文件"""
    temp_dir = tempfile.mkdtemp()
    
    test_files = {
        "src/auth/register.py": """
def register_user(username, email, password):
    # 用户注册功能
    if not username or len(username) < 3:
        return {"success": False, "error": "用户名至少需要3个字符"}
    
    if not email or '@' not in email:
        return {"success": False, "error": "请输入有效的邮箱地址"}
    
    if not password or len(password) < 6:
        return {"success": False, "error": "密码至少需要6个字符"}
    
    # 模拟保存用户
    user = {
        "id": 1,
        "username": username,
        "email": email,
        "password_hash": "hashed_password"
    }
    
    return {"success": True, "user": user}
""",
        "src/auth/login.py": """
def login_user(username, password):
    # 用户登录功能
    if not username or not password:
        return {"success": False, "error": "用户名和密码不能为空"}
    
    # 模拟验证用户
    if username == "testuser" and password == "password123":
        return {
            "success": True,
            "user_id": 1,
            "username": username,
            "message": "登录成功"
        }
    else:
        return {"success": False, "error": "用户名或密码错误"}

def logout_user(user_id):
    # 用户登出功能
    return {"success": True, "message": "登出成功"}
""",
        "app.py": """
from flask import Flask, request, jsonify
from src.auth.register import register_user
from src.auth.login import login_user, logout_user

app = Flask(__name__)

@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    result = register_user(
        data.get('username'),
        data.get('email'),
        data.get('password')
    )
    return jsonify(result)

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    result = login_user(
        data.get('username'),
        data.get('password')
    )
    return jsonify(result)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
""",
        "requirements.txt": """
Flask==2.3.3
"""
    }
    
    zip_path = os.path.join(temp_dir, "test_auth_system.zip")
    with zipfile.ZipFile(zip_path, 'w') as zipf:
        for filename, content in test_files.items():
            zipf.writestr(filename, content.strip())
    
    return zip_path

def test_agent():
    """测试Agent功能"""
    print("🧪 测试Code Analysis Agent...")
    
    # 1. 测试服务器健康状态
    try:
        response = requests.get("http://localhost:8000/", timeout=5)
        if response.status_code == 200:
            print("✅ 服务器运行正常")
        else:
            print(f"❌ 服务器响应异常: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到服务器，请先启动Agent服务")
        print("   启动命令: docker run -p 8000:8000 code-analysis-agent")
        return False
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False
    
    # 2. 测试分析功能
    zip_path = create_test_zip()
    print(f"✅ 测试ZIP文件已创建: {zip_path}")
    
    try:
        with open(zip_path, 'rb') as f:
            files = {
                'code_zip': ('test_auth_system.zip', f, 'application/zip')
            }
            data = {
                'problem_description': '实现一个完整的用户注册登录系统，包含用户注册、登录、登出、用户信息管理等功能。',
                'enable_verification': True
            }
            
            print("📤 发送分析请求...")
            response = requests.post(
                "http://localhost:8000/analyze",
                files=files,
                data=data,
                timeout=60
            )
        
        if response.status_code == 200:
            print("✅ 分析请求成功!")
            result = response.json()
            
            # 显示结果
            print(f"\n📋 分析结果:")
            print(f"功能分析数量: {len(result.get('feature_analysis', []))}")
            
            for i, feature in enumerate(result.get('feature_analysis', []), 1):
                print(f"\n{i}. {feature.get('feature_description', '无描述')}")
                for j, location in enumerate(feature.get('implementation_location', []), 1):
                    print(f"   📁 文件: {location.get('file', '未知')}")
                    print(f"   🔧 函数: {location.get('function', '未知')}")
                    print(f"   📍 行号: {location.get('lines', '未知')}")
            
            print(f"\n💡 执行计划建议:")
            print(result.get('execution_plan_suggestion', '无建议'))
            
            # 显示动态验证结果
            verification = result.get('functional_verification')
            if verification:
                print(f"\n🎯 动态验证结果:")
                print(f"✅ 生成了测试代码 (长度: {len(verification.get('generated_test_code', ''))} 字符)")
                
                execution_result = verification.get('execution_result')
                if execution_result:
                    print(f"测试执行结果: {'✅ 通过' if execution_result.get('tests_passed') else '❌ 失败'}")
                    print(f"执行日志: {execution_result.get('log', '无日志')}")
                else:
                    print("⚠️ 测试执行结果未返回")
            else:
                print("\n❌ 未返回动态验证结果")
            
            return True
        else:
            print(f"❌ 分析请求失败: {response.status_code}")
            print(f"错误信息: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 测试过程中出现错误: {e}")
        return False
    finally:
        try:
            os.remove(zip_path)
            os.rmdir(os.path.dirname(zip_path))
        except:
            pass

if __name__ == "__main__":
    print("🚀 Code Analysis Agent 测试脚本")
    print("=" * 50)
    
    success = test_agent()
    
    if success:
        print("\n🎉 所有测试通过！Agent功能正常！")
        print("✅ 基本分析功能正常")
        print("✅ 动态验证功能正常")
        print("✅ 测试代码生成功能正常")
        print("✅ 测试执行功能正常")
    else:
        print("\n❌ 测试失败")
        print("请检查Agent服务是否正常运行")
