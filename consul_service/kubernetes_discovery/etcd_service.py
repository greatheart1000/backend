"""
Etcd 服务注册和发现工具类
"""
import etcd3
import json
import threading
import time
import logging
import socket
from typing import List, Dict, Optional
from config import Config

logger = logging.getLogger(__name__)

class EtcdService:
    def __init__(self, host='localhost', port=2379):
        """
        初始化 Etcd 客户端
        """
        try:
            self.etcd = etcd3.client(host=host, port=port)
            self.service_prefix = "/services/"
            self.lease_ttl = 30  # 租约TTL，30秒
            self.registered_services = {}  # 存储已注册的服务信息
            logger.info(f"Etcd client initialized: {host}:{port}")
        except Exception as e:
            logger.error(f"Failed to connect to Etcd: {str(e)}")
            raise
    
    def register_service(self, service_name: str, service_id: str, address: str, 
                        port: int, metadata: Dict = None, tags: List[str] = None) -> bool:
        """
        注册服务到 Etcd
        使用租约机制实现TTL，定期续约
        """
        try:
            # 创建租约
            lease = self.etcd.lease(self.lease_ttl)
            
            # 构建服务信息
            service_info = {
                'service_id': service_id,
                'service_name': service_name,
                'address': address,
                'port': port,
                'tags': tags or [],
                'metadata': metadata or {},
                'registered_at': time.time()
            }
            
            # 服务在 Etcd 中的键
            service_key = f"{self.service_prefix}{service_name}/{service_id}"
            
            # 注册服务（绑定到租约）
            self.etcd.put(service_key, json.dumps(service_info), lease=lease)
            
            # 保存租约信息用于续约
            self.registered_services[service_id] = {
                'lease': lease,
                'service_key': service_key,
                'service_info': service_info
            }
            
            # 启动续约线程
            self._start_lease_renewal(service_id, lease)
            
            logger.info(f"Service {service_name} registered with ID: {service_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to register service {service_name}: {str(e)}")
            return False
    
    def deregister_service(self, service_id: str) -> bool:
        """
        注销服务
        """
        try:
            if service_id in self.registered_services:
                service_data = self.registered_services[service_id]
                
                # 删除服务键
                self.etcd.delete(service_data['service_key'])
                
                # 撤销租约
                service_data['lease'].revoke()
                
                # 从本地记录中移除
                del self.registered_services[service_id]
                
                logger.info(f"Service {service_id} deregistered successfully")
                return True
            else:
                logger.warning(f"Service {service_id} not found in registered services")
                return False
                
        except Exception as e:
            logger.error(f"Failed to deregister service {service_id}: {str(e)}")
            return False
    
    def discover_service(self, service_name: str) -> List[Dict]:
        """
        发现服务实例
        """
        try:
            service_prefix = f"{self.service_prefix}{service_name}/"
            
            # 获取所有服务实例
            services = []
            for value, metadata in self.etcd.get_prefix(service_prefix):
                if value:
                    try:
                        service_info = json.loads(value.decode('utf-8'))
                        
                        # 检查服务是否健康（可以通过健康检查扩展）
                        if self._is_service_healthy(service_info):
                            services.append(service_info)
                    except json.JSONDecodeError:
                        logger.warning(f"Invalid service data: {value}")
                        continue
            
            logger.info(f"Found {len(services)} healthy instances of service {service_name}")
            return services
            
        except Exception as e:
            logger.error(f"Failed to discover service {service_name}: {str(e)}")
            return []
    
    def get_service_url(self, service_name: str, load_balance_strategy: str = 'round_robin') -> Optional[str]:
        """
        获取服务URL，支持多种负载均衡策略
        """
        services = self.discover_service(service_name)
        if not services:
            return None
        
        # 负载均衡策略
        if load_balance_strategy == 'round_robin':
            # 简单轮询（可以用更复杂的算法）
            import random
            service = random.choice(services)
        elif load_balance_strategy == 'random':
            import random
            service = random.choice(services)
        else:
            # 默认选择第一个
            service = services[0]
        
        return f"http://{service['address']}:{service['port']}"
    
    def watch_service(self, service_name: str, callback):
        """
        监听服务变化
        """
        def watch_thread():
            service_prefix = f"{self.service_prefix}{service_name}/"
            events_iterator, cancel = self.etcd.watch_prefix(service_prefix)
            
            try:
                for event in events_iterator:
                    if event.type == etcd3.events.PutEvent:
                        logger.info(f"Service {service_name} instance added")
                    elif event.type == etcd3.events.DeleteEvent:
                        logger.info(f"Service {service_name} instance removed")
                    
                    # 调用回调函数
                    if callback:
                        callback(event, service_name)
                        
            except Exception as e:
                logger.error(f"Error watching service {service_name}: {str(e)}")
            finally:
                cancel()
        
        # 在后台线程中启动监听
        thread = threading.Thread(target=watch_thread, daemon=True)
        thread.start()
        return thread
    
    def _start_lease_renewal(self, service_id: str, lease):
        """
        启动租约续约线程
        """
        def renewal_thread():
            while service_id in self.registered_services:
                try:
                    # 每隔TTL的1/3时间续约一次
                    time.sleep(self.lease_ttl // 3)
                    
                    if service_id in self.registered_services:
                        lease.refresh()
                        logger.debug(f"Lease renewed for service {service_id}")
                    
                except Exception as e:
                    logger.error(f"Failed to renew lease for {service_id}: {str(e)}")
                    break
        
        # 启动续约线程
        thread = threading.Thread(target=renewal_thread, daemon=True)
        thread.start()
    
    def _is_service_healthy(self, service_info: Dict) -> bool:
        """
        检查服务健康状态（简单的TCP连接检查）
        """
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(3)
            result = sock.connect_ex((service_info['address'], service_info['port']))
            sock.close()
            return result == 0
        except Exception:
            return False
    
    def get_all_services(self) -> Dict[str, List[Dict]]:
        """
        获取所有注册的服务
        """
        try:
            all_services = {}
            
            for value, metadata in self.etcd.get_prefix(self.service_prefix):
                if value:
                    try:
                        service_info = json.loads(value.decode('utf-8'))
                        service_name = service_info['service_name']
                        
                        if service_name not in all_services:
                            all_services[service_name] = []
                        
                        all_services[service_name].append(service_info)
                        
                    except json.JSONDecodeError:
                        continue
            
            return all_services
            
        except Exception as e:
            logger.error(f"Failed to get all services: {str(e)}")
            return {}
    
    def get_local_ip(self) -> str:
        """
        获取本机IP地址
        """
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return "127.0.0.1"