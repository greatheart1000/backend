"""
客户端服务发现示例 - 演示如何通过 Consul 发现和调用服务
"""
import requests
import json
import logging
from consul_service import ConsulService

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ServiceClient:
    def __init__(self):
        self.consul_service = ConsulService()
    
    def register_user(self, username, password, email=None):
        """
        通过用户服务注册用户
        """
        try:
            # 发现用户服务
            user_service_url = self.consul_service.get_service_url("user-service")
            if not user_service_url:
                logger.error("User service not available")
                return None
            
            # 调用注册接口
            data = {
                'username': username,
                'password': password,
                'email': email or ''
            }
            
            response = requests.post(
                f"{user_service_url}/api/users/register",
                json=data,
                timeout=10
            )
            
            if response.status_code == 201:
                logger.info(f"User {username} registered successfully")
                return response.json()
            else:
                logger.error(f"Registration failed: {response.text}")
                return None
        
        except Exception as e:
            logger.error(f"Error registering user: {str(e)}")
            return None
    
    def login_user(self, username, password):
        """
        通过用户服务登录用户
        """
        try:
            # 发现用户服务
            user_service_url = self.consul_service.get_service_url("user-service")
            if not user_service_url:
                logger.error("User service not available")
                return None
            
            # 调用登录接口
            data = {
                'username': username,
                'password': password
            }
            
            response = requests.post(
                f"{user_service_url}/api/users/login",
                json=data,
                timeout=10
            )
            
            if response.status_code == 200:
                logger.info(f"User {username} logged in successfully")
                return response.json()
            else:
                logger.error(f"Login failed: {response.text}")
                return None
        
        except Exception as e:
            logger.error(f"Error logging in user: {str(e)}")
            return None
    
    def get_user_profile(self, token):
        """
        获取用户信息
        """
        try:
            # 发现用户服务
            user_service_url = self.consul_service.get_service_url("user-service")
            if not user_service_url:
                logger.error("User service not available")
                return None
            
            # 调用获取用户信息接口
            headers = {'Authorization': f'Bearer {token}'}
            response = requests.get(
                f"{user_service_url}/api/users/profile",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Get profile failed: {response.text}")
                return None
        
        except Exception as e:
            logger.error(f"Error getting user profile: {str(e)}")
            return None
    
    def create_order(self, token, product_name, quantity, price):
        """
        通过订单服务创建订单
        """
        try:
            # 发现订单服务
            order_service_url = self.consul_service.get_service_url("order-service")
            if not order_service_url:
                logger.error("Order service not available")
                return None
            
            # 调用创建订单接口
            data = {
                'product_name': product_name,
                'quantity': quantity,
                'price': price
            }
            
            headers = {'Authorization': f'Bearer {token}'}
            response = requests.post(
                f"{order_service_url}/api/orders",
                json=data,
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 201:
                logger.info(f"Order created successfully")
                return response.json()
            else:
                logger.error(f"Create order failed: {response.text}")
                return None
        
        except Exception as e:
            logger.error(f"Error creating order: {str(e)}")
            return None
    
    def get_orders(self, token):
        """
        获取用户订单列表
        """
        try:
            # 发现订单服务
            order_service_url = self.consul_service.get_service_url("order-service")
            if not order_service_url:
                logger.error("Order service not available")
                return None
            
            # 调用获取订单接口
            headers = {'Authorization': f'Bearer {token}'}
            response = requests.get(
                f"{order_service_url}/api/orders",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Get orders failed: {response.text}")
                return None
        
        except Exception as e:
            logger.error(f"Error getting orders: {str(e)}")
            return None
    
    def discover_all_services(self):
        """
        发现所有注册的服务
        """
        try:
            services = self.consul_service.consul.agent.services()
            
            logger.info("=== 已注册的服务 ===")
            for service_id, service_info in services.items():
                logger.info(f"服务ID: {service_id}")
                logger.info(f"服务名: {service_info['Service']}")
                logger.info(f"地址: {service_info['Address']}:{service_info['Port']}")
                logger.info(f"标签: {service_info['Tags']}")
                logger.info("-" * 40)
            
            return services
        
        except Exception as e:
            logger.error(f"Error discovering services: {str(e)}")
            return {}

def demo():
    """
    演示服务发现和调用
    """
    client = ServiceClient()
    
    print("=== Flask Consul 服务发现演示 ===\n")
    
    # 1. 发现所有服务
    print("1. 发现所有已注册的服务:")
    services = client.discover_all_services()
    print()
    
    # 2. 注册用户
    print("2. 注册新用户:")
    username = "testuser"
    password = "testpass123"
    email = "test@example.com"
    
    register_result = client.register_user(username, password, email)
    if register_result:
        print(f"✓ 用户注册成功: {json.dumps(register_result, indent=2, ensure_ascii=False)}")
    else:
        print("✗ 用户注册失败")
    print()
    
    # 3. 用户登录
    print("3. 用户登录:")
    login_result = client.login_user(username, password)
    if login_result:
        print(f"✓ 登录成功: {json.dumps(login_result, indent=2, ensure_ascii=False)}")
        token = login_result.get('token')
    else:
        print("✗ 登录失败")
        return
    print()
    
    # 4. 获取用户信息
    print("4. 获取用户信息:")
    profile_result = client.get_user_profile(token)
    if profile_result:
        print(f"✓ 用户信息: {json.dumps(profile_result, indent=2, ensure_ascii=False)}")
    else:
        print("✗ 获取用户信息失败")
    print()
    
    # 5. 创建订单
    print("5. 创建订单:")
    order_result = client.create_order(token, "测试产品", 2, 99.99)
    if order_result:
        print(f"✓ 订单创建成功: {json.dumps(order_result, indent=2, ensure_ascii=False)}")
    else:
        print("✗ 创建订单失败")
    print()
    
    # 6. 获取订单列表
    print("6. 获取订单列表:")
    orders_result = client.get_orders(token)
    if orders_result:
        print(f"✓ 订单列表: {json.dumps(orders_result, indent=2, ensure_ascii=False)}")
    else:
        print("✗ 获取订单列表失败")
    print()

if __name__ == '__main__':
    demo()