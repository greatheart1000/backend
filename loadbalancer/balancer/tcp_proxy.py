import socket
import threading
import select
import logging
from typing import Optional, Dict, Any
from algorithms.base import LoadBalancer, Backend
from discovery import ServiceRegistry

logger = logging.getLogger(__name__)

class TCPProxy:
    """TCP代理负载均衡器"""
    
    def __init__(self, 
                 listen_host: str = '0.0.0.0',
                 listen_port: int = 8080, 
                 load_balancer: LoadBalancer = None):
        self.listen_host = listen_host
        self.listen_port = listen_port
        self.load_balancer = load_balancer
        self.registry: Optional[ServiceRegistry] = None
        self.service_name: Optional[str] = None
        
        # 服务器socket
        self.server_socket: Optional[socket.socket] = None
        self.is_running = False
        self.accept_thread: Optional[threading.Thread] = None
        
        # 连接管理
        self.connections: Dict[str, 'TCPConnection'] = {}
        self.connections_lock = threading.Lock()
        
        # 配置选项
        self.idle_timeout = 30 * 60  # 30分钟
        self.max_connections = 1000
        self.buffer_size = 32 * 1024  # 32KB
        
        # 统计信息
        self.total_connections = 0
        self.active_connections = 0
        self.total_bytes_received = 0
        self.total_bytes_sent = 0
        self.stats_lock = threading.Lock()
    
    def set_registry(self, registry: ServiceRegistry, service_name: str):
        """设置服务注册表"""
        self.registry = registry
        self.service_name = service_name
    
    def set_idle_timeout(self, timeout: int):
        """设置空闲超时时间（秒）"""
        self.idle_timeout = timeout
    
    def set_max_connections(self, max_conn: int):
        """设置最大连接数"""
        self.max_connections = max_conn
    
    def set_buffer_size(self, size: int):
        """设置缓冲区大小"""
        self.buffer_size = size
    
    def start(self):
        """启动TCP代理"""
        if self.is_running:
            raise RuntimeError("TCP proxy is already running")
        
        try:
            # 创建服务器socket
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((self.listen_host, self.listen_port))
            self.server_socket.listen(128)
            
            self.is_running = True
            
            # 启动接受连接的线程
            self.accept_thread = threading.Thread(target=self._accept_connections, daemon=True)
            self.accept_thread.start()
            
            # 启动连接清理线程
            cleanup_thread = threading.Thread(target=self._cleanup_connections, daemon=True)
            cleanup_thread.start()
            
            logger.info(f"TCP proxy started on {self.listen_host}:{self.listen_port}")
            
        except Exception as e:
            self.is_running = False
            if self.server_socket:
                self.server_socket.close()
                self.server_socket = None
            raise RuntimeError(f"Failed to start TCP proxy: {e}")
    
    def stop(self):
        """停止TCP代理"""
        if not self.is_running:
            return
        
        self.is_running = False
        
        # 关闭服务器socket
        if self.server_socket:
            self.server_socket.close()
            self.server_socket = None
        
        # 关闭所有活跃连接
        with self.connections_lock:
            for conn in list(self.connections.values()):
                conn.close()
            self.connections.clear()
        
        logger.info("TCP proxy stopped")
    
    def _accept_connections(self):
        """接受新连接"""
        while self.is_running:
            try:
                client_socket, client_addr = self.server_socket.accept()
                
                # 检查连接数限制
                with self.connections_lock:
                    if len(self.connections) >= self.max_connections:
                        logger.warning(f"Max connections reached ({self.max_connections}), rejecting {client_addr}")
                        client_socket.close()
                        continue
                
                # 处理连接
                threading.Thread(
                    target=self._handle_connection,
                    args=(client_socket, client_addr),
                    daemon=True
                ).start()
                
            except socket.error as e:
                if self.is_running:
                    logger.error(f"Error accepting connection: {e}")
                break
    
    def _handle_connection(self, client_socket: socket.socket, client_addr):
        """处理单个连接"""
        conn_id = f"{client_addr[0]}:{client_addr[1]}->{self.listen_host}:{self.listen_port}"
        
        try:
            # 获取客户端IP
            client_ip = client_addr[0]
            
            # 选择后端服务
            backend = self.load_balancer.next_backend(client_ip)
            if not backend:
                logger.warning(f"No healthy backend available for {conn_id}")
                client_socket.close()
                return
            
            # 连接到后端服务
            backend_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            backend_socket.settimeout(10)  # 连接超时
            backend_socket.connect((backend.host, backend.port))
            backend_socket.settimeout(None)  # 清除超时
            
            # 增加后端活跃连接数
            backend.increment_active()
            
            # 创建连接对象
            connection = TCPConnection(
                conn_id, client_socket, backend_socket, backend, self.buffer_size
            )
            
            with self.connections_lock:
                self.connections[conn_id] = connection
            
            # 更新统计信息
            with self.stats_lock:
                self.total_connections += 1
                self.active_connections += 1
            
            logger.info(f"New connection {conn_id} proxied to {backend.address}")
            
            # 开始代理数据
            connection.start_proxy()
            
        except Exception as e:
            logger.error(f"Error handling connection {conn_id}: {e}")
            client_socket.close()
        
        finally:
            # 清理连接
            with self.connections_lock:
                if conn_id in self.connections:
                    del self.connections[conn_id]
            
            with self.stats_lock:
                self.active_connections -= 1
                if hasattr(connection, 'bytes_received'):
                    self.total_bytes_received += connection.bytes_received
                if hasattr(connection, 'bytes_sent'):
                    self.total_bytes_sent += connection.bytes_sent
            
            # 减少后端活跃连接数
            if 'backend' in locals():
                backend.decrement_active()
    
    def _cleanup_connections(self):
        """定期清理超时连接"""
        while self.is_running:
            try:
                current_time = threading.current_thread().ident  # 简化的时间戳
                timeout_connections = []
                
                with self.connections_lock:
                    for conn_id, conn in self.connections.items():
                        if conn.is_idle_timeout(self.idle_timeout):
                            timeout_connections.append(conn_id)
                
                # 关闭超时连接
                for conn_id in timeout_connections:
                    with self.connections_lock:
                        if conn_id in self.connections:
                            conn = self.connections[conn_id]
                            conn.close()
                            logger.info(f"Closed idle connection: {conn_id}")
                
                # 等待一分钟再检查
                threading.Event().wait(60)
                
            except Exception as e:
                logger.error(f"Error in connection cleanup: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        with self.stats_lock:
            return {
                'listen_address': f"{self.listen_host}:{self.listen_port}",
                'is_running': self.is_running,
                'total_connections': self.total_connections,
                'active_connections': self.active_connections,
                'total_bytes_received': self.total_bytes_received,
                'total_bytes_sent': self.total_bytes_sent,
                'max_connections': self.max_connections,
                'idle_timeout': self.idle_timeout,
                'buffer_size': self.buffer_size
            }

class TCPConnection:
    """TCP连接封装"""
    
    def __init__(self, conn_id: str, client_socket: socket.socket, 
                 backend_socket: socket.socket, backend: Backend, buffer_size: int):
        self.conn_id = conn_id
        self.client_socket = client_socket
        self.backend_socket = backend_socket
        self.backend = backend
        self.buffer_size = buffer_size
        
        self.start_time = threading.current_thread().ident  # 简化的时间戳
        self.last_active = self.start_time
        self.bytes_received = 0
        self.bytes_sent = 0
        self.is_closed = False
    
    def start_proxy(self):
        """开始代理数据传输"""
        try:
            # 创建两个线程分别处理双向数据传输
            client_to_backend_thread = threading.Thread(
                target=self._proxy_data,
                args=(self.client_socket, self.backend_socket, "client->backend"),
                daemon=True
            )
            
            backend_to_client_thread = threading.Thread(
                target=self._proxy_data,
                args=(self.backend_socket, self.client_socket, "backend->client"),
                daemon=True
            )
            
            client_to_backend_thread.start()
            backend_to_client_thread.start()
            
            # 等待任一方向的传输结束
            client_to_backend_thread.join()
            backend_to_client_thread.join()
            
        except Exception as e:
            logger.error(f"Error in proxy data for {self.conn_id}: {e}")
        finally:
            self.close()
    
    def _proxy_data(self, source: socket.socket, destination: socket.socket, direction: str):
        """代理数据传输"""
        try:
            while not self.is_closed:
                # 使用select检查socket是否有数据可读
                ready, _, _ = select.select([source], [], [], 1.0)
                if not ready:
                    continue
                
                try:
                    data = source.recv(self.buffer_size)
                    if not data:
                        break
                    
                    destination.sendall(data)
                    
                    # 更新统计信息
                    if direction == "client->backend":
                        self.bytes_received += len(data)
                    else:
                        self.bytes_sent += len(data)
                    
                    self.last_active = threading.current_thread().ident
                    
                except socket.error:
                    break
                    
        except Exception as e:
            logger.error(f"Error proxying data {direction} for {self.conn_id}: {e}")
    
    def close(self):
        """关闭连接"""
        if self.is_closed:
            return
        
        self.is_closed = True
        
        try:
            self.client_socket.close()
        except:
            pass
        
        try:
            self.backend_socket.close()
        except:
            pass
        
        logger.debug(f"Connection {self.conn_id} closed")
    
    def is_idle_timeout(self, timeout: int) -> bool:
        """检查是否空闲超时"""
        # 简化的超时检查
        return False  # 在实际实现中应该检查时间差