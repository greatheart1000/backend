"""
Consul 服务注册和发现工具类
"""
import consul
import requests
import socket
import logging
from config import Config

logger = logging.getLogger(__name__)

class ConsulService:
    def __init__(self):
        self.consul = consul.Consul(host=Config.CONSUL_HOST, port=Config.CONSUL_PORT)
        
    def register_service(self, service_name, service_id, address, port, health_check_url=None, tags=None):
        """
        注册服务到 Consul
        """
        try:
            # 健康检查配置
            check = None
            if health_check_url:
                check = consul.Check.http(health_check_url, interval="10s", timeout="5s")
            
            # 注册服务
            self.consul.agent.service.register(
                name=service_name,
                service_id=service_id,
                address=address,
                port=port,
                tags=tags or [],
                check=check
            )
            logger.info(f"Service {service_name} registered successfully with ID: {service_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to register service {service_name}: {str(e)}")
            return False
    
    def deregister_service(self, service_id):
        """
        注销服务
        """
        try:
            self.consul.agent.service.deregister(service_id)
            logger.info(f"Service {service_id} deregistered successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to deregister service {service_id}: {str(e)}")
            return False
    
    def discover_service(self, service_name):
        """
        发现服务
        """
        try:
            services = self.consul.health.service(service_name, passing=True)[1]
            healthy_services = []
            
            for service in services:
                service_info = service['Service']
                healthy_services.append({
                    'id': service_info['ID'],
                    'address': service_info['Address'],
                    'port': service_info['Port'],
                    'tags': service_info['Tags']
                })
            
            logger.info(f"Found {len(healthy_services)} healthy instances of service {service_name}")
            return healthy_services
        except Exception as e:
            logger.error(f"Failed to discover service {service_name}: {str(e)}")
            return []
    
    def get_service_url(self, service_name):
        """
        获取服务URL（负载均衡：简单轮询）
        """
        services = self.discover_service(service_name)
        if not services:
            return None
        
        # 简单的轮询负载均衡
        import random
        service = random.choice(services)
        return f"http://{service['address']}:{service['port']}"
    
    def get_local_ip(self):
        """
        获取本机IP地址
        """
        try:
            # 连接到外部地址获取本机IP
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return "127.0.0.1"