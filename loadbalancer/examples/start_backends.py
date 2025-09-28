"""
启动多个后端服务器的脚本
"""

import subprocess
import time
import signal
import sys
import os

class BackendManager:
    """后端服务器管理器"""
    
    def __init__(self):
        self.processes = []
    
    def start_backend(self, port, server_id=None):
        """启动一个后端服务器"""
        if server_id is None:
            server_id = f'backend-{port}'
        
        cmd = [
            sys.executable, 'backend_server.py',
            '--port', str(port),
            '--id', server_id,
            '--host', '127.0.0.1'
        ]
        
        print(f"Starting backend server {server_id} on port {port}")
        
        process = subprocess.Popen(
            cmd,
            cwd=os.path.dirname(__file__),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        self.processes.append((process, server_id, port))
        return process
    
    def start_all(self, ports):
        """启动所有后端服务器"""
        for port in ports:
            self.start_backend(port)
            time.sleep(1)  # 间隔启动
    
    def stop_all(self):
        """停止所有后端服务器"""
        print("Stopping all backend servers...")
        
        for process, server_id, port in self.processes:
            if process.poll() is None:  # 进程还在运行
                print(f"Stopping {server_id} on port {port}")
                process.terminate()
                
                # 等待进程结束
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    print(f"Force killing {server_id}")
                    process.kill()
    
    def status(self):
        """显示所有服务器状态"""
        print("Backend server status:")
        for process, server_id, port in self.processes:
            status = "running" if process.poll() is None else "stopped"
            print(f"  {server_id} (port {port}): {status}")


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Backend Server Manager')
    parser.add_argument('--ports', nargs='+', type=int, 
                       default=[8001, 8002, 8003],
                       help='Ports for backend servers')
    
    args = parser.parse_args()
    
    manager = BackendManager()
    
    def signal_handler(sig, frame):
        print('\nReceived interrupt signal')
        manager.stop_all()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # 启动所有后端服务器
        manager.start_all(args.ports)
        
        print(f"Started {len(args.ports)} backend servers")
        print("Ports:", args.ports)
        print("Press Ctrl+C to stop all servers")
        
        # 监控进程状态
        while True:
            time.sleep(5)
            
            # 检查是否有进程意外退出
            for process, server_id, port in manager.processes:
                if process.poll() is not None:
                    print(f"Warning: {server_id} on port {port} has stopped")
    
    except KeyboardInterrupt:
        pass
    finally:
        manager.stop_all()


if __name__ == '__main__':
    main()