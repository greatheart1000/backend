"""
API 测试脚本 - 用于测试所有服务接口
"""
import requests
import json
import time

class APITester:
    def __init__(self):
        self.base_urls = {
            'user': 'http://localhost:5001',
            'order': 'http://localhost:5002'
        }
        self.token = None
    
    def test_health_checks(self):
        """测试健康检查接口"""
        print("=== 测试健康检查接口 ===")
        
        for service, url in self.base_urls.items():
            try:
                response = requests.get(f"{url}/health", timeout=5)
                if response.status_code == 200:
                    print(f"✓ {service} 服务健康检查通过")
                else:
                    print(f"✗ {service} 服务健康检查失败: {response.status_code}")
            except Exception as e:
                print(f"✗ {service} 服务连接失败: {str(e)}")
        print()
    
    def test_user_registration(self):
        """测试用户注册"""
        print("=== 测试用户注册 ===")
        
        data = {
            "username": "test_user_" + str(int(time.time())),
            "password": "test123456",
            "email": "test@example.com"
        }
        
        try:
            response = requests.post(
                f"{self.base_urls['user']}/api/users/register",
                json=data,
                timeout=10
            )
            
            if response.status_code == 201:
                result = response.json()
                print(f"✓ 用户注册成功: {result['username']}")
                return data
            else:
                print(f"✗ 用户注册失败: {response.text}")
                return None
        except Exception as e:
            print(f"✗ 用户注册请求失败: {str(e)}")
            return None
    
    def test_user_login(self, user_data):
        """测试用户登录"""
        print("=== 测试用户登录 ===")
        
        if not user_data:
            print("✗ 跳过登录测试（注册失败）")
            return None
        
        login_data = {
            "username": user_data["username"],
            "password": user_data["password"]
        }
        
        try:
            response = requests.post(
                f"{self.base_urls['user']}/api/users/login",
                json=login_data,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                self.token = result['token']
                print(f"✓ 用户登录成功，获取到 token")
                return self.token
            else:
                print(f"✗ 用户登录失败: {response.text}")
                return None
        except Exception as e:
            print(f"✗ 用户登录请求失败: {str(e)}")
            return None
    
    def test_get_profile(self):
        """测试获取用户信息"""
        print("=== 测试获取用户信息 ===")
        
        if not self.token:
            print("✗ 跳过获取用户信息测试（未登录）")
            return
        
        headers = {"Authorization": f"Bearer {self.token}"}
        
        try:
            response = requests.get(
                f"{self.base_urls['user']}/api/users/profile",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✓ 获取用户信息成功: {result['user']['username']}")
            else:
                print(f"✗ 获取用户信息失败: {response.text}")
        except Exception as e:
            print(f"✗ 获取用户信息请求失败: {str(e)}")
    
    def test_create_order(self):
        """测试创建订单"""
        print("=== 测试创建订单 ===")
        
        if not self.token:
            print("✗ 跳过创建订单测试（未登录）")
            return None
        
        order_data = {
            "product_name": "测试产品",
            "quantity": 2,
            "price": 99.99
        }
        
        headers = {"Authorization": f"Bearer {self.token}"}
        
        try:
            response = requests.post(
                f"{self.base_urls['order']}/api/orders",
                json=order_data,
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 201:
                result = response.json()
                order_id = result['order']['order_id']
                print(f"✓ 订单创建成功: {order_id}")
                return order_id
            else:
                print(f"✗ 订单创建失败: {response.text}")
                return None
        except Exception as e:
            print(f"✗ 订单创建请求失败: {str(e)}")
            return None
    
    def test_get_orders(self):
        """测试获取订单列表"""
        print("=== 测试获取订单列表 ===")
        
        if not self.token:
            print("✗ 跳过获取订单列表测试（未登录）")
            return
        
        headers = {"Authorization": f"Bearer {self.token}"}
        
        try:
            response = requests.get(
                f"{self.base_urls['order']}/api/orders",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                orders_count = len(result['orders'])
                print(f"✓ 获取订单列表成功，共 {orders_count} 个订单")
            else:
                print(f"✗ 获取订单列表失败: {response.text}")
        except Exception as e:
            print(f"✗ 获取订单列表请求失败: {str(e)}")
    
    def run_all_tests(self):
        """运行所有测试"""
        print("开始 API 接口测试...\n")
        
        # 健康检查
        self.test_health_checks()
        
        # 用户相关测试
        user_data = self.test_user_registration()
        print()
        
        self.test_user_login(user_data)
        print()
        
        self.test_get_profile()
        print()
        
        # 订单相关测试
        order_id = self.test_create_order()
        print()
        
        self.test_get_orders()
        print()
        
        print("=== 测试完成 ===")

if __name__ == '__main__':
    tester = APITester()
    tester.run_all_tests()