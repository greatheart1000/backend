"""
基于 Etcd 服务发现的客户端示例
演示如何通过 Etcd 发现和调用微服务
"""
import requests
import json
import logging
import time
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from etcd_service import EtcdService

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EtcdServiceClient:
    def __init__(self, etcd_host='localhost', etcd_port=2379):
        self.etcd_service = EtcdService(host=etcd_host, port=etcd_port)
    
    def register_user(self, username, password, email=None):
        """
        通过 Etcd 发现用户服务并注册用户
        """
        try:
            # 通过 Etcd 发现用户服务
            user_service_url = self.etcd_service.get_service_url("user-service")
            if not user_service_url:
                logger.error("User service not available in Etcd")
                return None
            
            logger.info(f"Discovered user service at: {user_service_url}")
            
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
                logger.info(f"User {username} registered successfully via Etcd")
                return response.json()
            else:
                logger.error(f"Registration failed: {response.text}")
                return None
        
        except Exception as e:
            logger.error(f"Error registering user: {str(e)}")
            return None
    
    def login_user(self, username, password):
        """
        通过 Etcd 发现用户服务并登录
        """
        try:
            user_service_url = self.etcd_service.get_service_url("user-service")
            if not user_service_url:
                logger.error("User service not available in Etcd")
                return None
            
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
                logger.info(f"User {username} logged in successfully via Etcd")
                return response.json()
            else:
                logger.error(f"Login failed: {response.text}")
                return None
        
        except Exception as e:
            logger.error(f"Error logging in user: {str(e)}")
            return None
    
    def create_order(self, token, product_name, quantity, price):
        """
        通过 Etcd 发现订单服务并创建订单
        """
        try:
            order_service_url = self.etcd_service.get_service_url("order-service")
            if not order_service_url:
                logger.error("Order service not available in Etcd")
                return None
            
            logger.info(f"Discovered order service at: {order_service_url}")
            
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
                logger.info(f"Order created successfully via Etcd")
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
            order_service_url = self.etcd_service.get_service_url("order-service")
            if not order_service_url:
                logger.error("Order service not available in Etcd")
                return None
            
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
        发现所有注册在 Etcd 中的服务
        """
        try:
            all_services = self.etcd_service.get_all_services()
            
            logger.info("=== Etcd 中已注册的服务 ===")
            for service_name, instances in all_services.items():
                logger.info(f"服务名: {service_name}")
                for instance in instances:
                    logger.info(f"  实例ID: {instance['service_id']}")
                    logger.info(f"  地址: {instance['address']}:{instance['port']}")
                    logger.info(f"  标签: {instance['tags']}")
                    logger.info(f"  元数据: {instance['metadata']}")
                    logger.info("-" * 30)
            
            return all_services
        
        except Exception as e:
            logger.error(f"Error discovering services: {str(e)}")
            return {}
    
    def test_service_discovery_features(self):
        """
        测试 Etcd 服务发现的高级特性
        """
        print("\n=== Etcd 服务发现高级特性测试 ===")
        
        # 1. 测试负载均衡
        print("\n1. 测试负载均衡:")
        for i in range(3):
            url = self.etcd_service.get_service_url("user-service", "random")
            print(f"  第{i+1}次调用: {url}")
        
        # 2. 测试服务监听
        print("\n2. 启动服务监听:")
        def service_change_callback(event, service_name):
            print(f"  检测到服务变化: {service_name} - {event.type}")
        
        # 启动监听线程
        watch_thread = self.etcd_service.watch_service("user-service", service_change_callback)
        print("  服务监听已启动，运行5秒...")
        time.sleep(5)
        
        # 3. 测试健康检查
        print("\n3. 测试服务健康状态:")
        user_services = self.etcd_service.discover_service("user-service")
        for service in user_services:
            healthy = self.etcd_service._is_service_healthy(service)
            print(f"  {service['address']}:{service['port']} - {'健康' if healthy else '不健康'}")

def demo():
    """
    演示基于 Etcd 的服务发现
    """
    client = EtcdServiceClient()
    
    print("=== Flask + Etcd 服务发现演示 ===\n")
    
    # 1. 发现所有服务
    print("1. 发现 Etcd 中所有已注册的服务:")
    services = client.discover_all_services()
    print()
    
    # 2. 测试高级特性
    client.test_service_discovery_features()
    print()
    
    # 3. 注册用户
    print("3. 通过 Etcd 服务发现注册新用户:")
    username = "etcd_testuser"
    password = "testpass123"
    email = "etcd_test@example.com"
    
    register_result = client.register_user(username, password, email)
    if register_result:
        print(f"✓ 用户注册成功: {json.dumps(register_result, indent=2, ensure_ascii=False)}")
    else:
        print("✗ 用户注册失败")
    print()
    
    # 4. 用户登录
    print("4. 通过 Etcd 服务发现登录用户:")
    login_result = client.login_user(username, password)
    if login_result:
        print(f"✓ 登录成功: {json.dumps(login_result, indent=2, ensure_ascii=False)}")
        token = login_result.get('token')
    else:
        print("✗ 登录失败")
        return
    print()
    
    # 5. 创建订单
    print("5. 通过 Etcd 服务发现创建订单:")
    order_result = client.create_order(token, "Etcd测试产品", 3, 199.99)
    if order_result:
        print(f"✓ 订单创建成功: {json.dumps(order_result, indent=2, ensure_ascii=False)}")
    else:
        print("✗ 创建订单失败")
    print()
    
    # 6. 获取订单列表
    print("6. 通过 Etcd 服务发现获取订单列表:")
    orders_result = client.get_orders(token)
    if orders_result:
        print(f"✓ 订单列表: {json.dumps(orders_result, indent=2, ensure_ascii=False)}")
    else:
        print("✗ 获取订单列表失败")
    print()
    
    # 7. 服务发现对比
    print("7. Etcd vs Consul 服务发现对比:")
    print("   Etcd 优势:")
    print("   - 强一致性保证")
    print("   - Kubernetes 原生支持")
    print("   - 高性能，低延迟")
    print("   - 支持事务操作")
    print("   - 内置监听机制")

if __name__ == '__main__':
    demo()