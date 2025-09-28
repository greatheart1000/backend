from abc import ABC, abstractmethod
from typing import List, Callable, Dict
import threading
import time
import logging
from discovery.registry import ServiceInstance, ServiceRegistry

logger = logging.getLogger(__name__)

class ServiceWatcher(ABC):
    """服务观察者抽象基类"""
    
    @abstractmethod
    def watch(self, service_name: str, callback: Callable[[List[ServiceInstance]], None]):
        """监听服务变化"""
        pass
    
    @abstractmethod
    def stop(self):
        """停止监听"""
        pass

class SimpleServiceWatcher(ServiceWatcher):
    """简单服务观察者实现"""
    
    def __init__(self, registry: ServiceRegistry, check_interval: int = 5):
        self.registry = registry
        self.check_interval = check_interval
        self.watchers: Dict[str, List[Callable]] = {}  # service_name -> callbacks
        self.last_states: Dict[str, List[ServiceInstance]] = {}  # service_name -> instances
        
        self.is_running = False
        self.watch_thread = None
        self.stop_event = threading.Event()
        self._lock = threading.Lock()
    
    def watch(self, service_name: str, callback: Callable[[List[ServiceInstance]], None]):
        """监听服务变化"""
        with self._lock:
            if service_name not in self.watchers:
                self.watchers[service_name] = []
            
            self.watchers[service_name].append(callback)
            
            # 如果还没开始监听，启动监听
            if not self.is_running:
                self._start_watching()
        
        logger.info(f"Started watching service: {service_name}")
    
    def stop(self):
        """停止监听"""
        with self._lock:
            if not self.is_running:
                return
            
            self.is_running = False
            self.stop_event.set()
            
            if self.watch_thread and self.watch_thread.is_alive():
                self.watch_thread.join(timeout=5)
        
        logger.info("Service watcher stopped")
    
    def _start_watching(self):
        """启动监听"""
        self.is_running = True
        self.stop_event.clear()
        self.watch_thread = threading.Thread(target=self._watch_loop, daemon=True)
        self.watch_thread.start()
        logger.info("Service watcher started")
    
    def _watch_loop(self):
        """监听循环"""
        while not self.stop_event.wait(self.check_interval):
            try:
                self._check_changes()
            except Exception as e:
                logger.error(f"Error in service watch loop: {e}")
    
    def _check_changes(self):
        """检查服务变化"""
        with self._lock:
            watched_services = list(self.watchers.keys())
        
        for service_name in watched_services:
            try:
                current_instances = self.registry.discover(service_name)
                last_instances = self.last_states.get(service_name, [])
                
                # 检查是否有变化
                if not self._instances_equal(last_instances, current_instances):
                    self.last_states[service_name] = current_instances
                    
                    # 通知所有回调
                    with self._lock:
                        callbacks = self.watchers.get(service_name, [])
                    
                    for callback in callbacks:
                        try:
                            # 异步调用回调
                            threading.Thread(
                                target=callback,
                                args=(current_instances,),
                                daemon=True
                            ).start()
                        except Exception as e:
                            logger.error(f"Error calling service change callback: {e}")
                    
                    logger.info(f"Service {service_name} changed: {len(current_instances)} instances")
            
            except Exception as e:
                logger.error(f"Error checking changes for service {service_name}: {e}")
    
    def _instances_equal(self, instances1: List[ServiceInstance], instances2: List[ServiceInstance]) -> bool:
        """比较两个服务实例列表是否相等"""
        if len(instances1) != len(instances2):
            return False
        
        # 转换为字典进行比较
        dict1 = {inst.id: (inst.host, inst.port, inst.status, inst.weight) for inst in instances1}
        dict2 = {inst.id: (inst.host, inst.port, inst.status, inst.weight) for inst in instances2}
        
        return dict1 == dict2
    
    def get_watched_services(self) -> List[str]:
        """获取正在监听的服务列表"""
        with self._lock:
            return list(self.watchers.keys())
    
    def get_stats(self) -> dict:
        """获取观察者统计信息"""
        with self._lock:
            return {
                'is_running': self.is_running,
                'watched_services': len(self.watchers),
                'check_interval': self.check_interval,
                'services': list(self.watchers.keys())
            }