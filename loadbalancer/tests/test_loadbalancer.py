"""
负载均衡器测试脚本
测试各种功能和性能
"""

import requests
import time
import json
import threading
import statistics
from typing import List, Dict, Any
import argparse
import concurrent.futures


class LoadBalancerTester:
    """负载均衡器测试类"""
    
    def __init__(self, lb_url: str = "http://localhost:8080"):
        self.lb_url = lb_url
        self.session = requests.Session()
        self.results = []
        self.results_lock = threading.Lock()
    
    def test_basic_connectivity(self) -> bool:
        """测试基本连通性"""
        print("Testing basic connectivity...")
        try:
            response = self.session.get(f"{self.lb_url}/lb/health", timeout=5)
            if response.status_code == 200:
                print("✓ Load balancer is accessible")
                return True
            else:
                print(f"✗ Load balancer returned status {response.status_code}")
                return False
        except Exception as e:
            print(f"✗ Failed to connect to load balancer: {e}")
            return False
    
    def test_backend_distribution(self, num_requests: int = 50) -> Dict[str, Any]:
        """测试请求在后端之间的分布"""
        print(f"Testing backend distribution with {num_requests} requests...")
        
        backend_counts = {}
        failed_requests = 0
        
        for i in range(num_requests):
            try:
                response = self.session.get(f"{self.lb_url}/", timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    server_id = data.get('server_info', {}).get('id', 'unknown')
                    backend_counts[server_id] = backend_counts.get(server_id, 0) + 1
                else:
                    failed_requests += 1
            except Exception as e:
                failed_requests += 1
                print(f"Request {i+1} failed: {e}")
        
        print("Backend distribution:")
        for server_id, count in backend_counts.items():
            percentage = (count / num_requests) * 100
            print(f"  {server_id}: {count} requests ({percentage:.1f}%)")
        
        if failed_requests > 0:
            print(f"  Failed requests: {failed_requests}")
        
        return {
            'backend_counts': backend_counts,
            'failed_requests': failed_requests,
            'total_requests': num_requests
        }
    
    def test_session_affinity(self, num_requests: int = 20) -> Dict[str, Any]:
        """测试会话保持功能"""
        print(f"Testing session affinity with {num_requests} requests...")
        
        # 使用固定的会话
        session_id = "test-session-123"
        headers = {"X-Session-ID": session_id}
        
        backend_servers = set()
        failed_requests = 0
        
        for i in range(num_requests):
            try:
                response = self.session.get(f"{self.lb_url}/admin/dashboard", 
                                          headers=headers, timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    server_id = data.get('server_id', 'unknown')
                    backend_servers.add(server_id)
                else:
                    failed_requests += 1
            except Exception as e:
                failed_requests += 1
        
        print(f"Session affinity test results:")
        print(f"  Unique servers used: {len(backend_servers)}")
        print(f"  Servers: {list(backend_servers)}")
        print(f"  Failed requests: {failed_requests}")
        
        # 理想情况下应该只使用一个服务器
        affinity_success = len(backend_servers) == 1
        print(f"  Session affinity: {'✓ Working' if affinity_success else '✗ Not working'}")
        
        return {
            'unique_servers': len(backend_servers),
            'servers_used': list(backend_servers),
            'failed_requests': failed_requests,
            'affinity_working': affinity_success
        }
    
    def test_performance(self, num_requests: int = 100, concurrency: int = 10) -> Dict[str, Any]:
        """测试性能"""
        print(f"Testing performance with {num_requests} requests, concurrency: {concurrency}")
        
        response_times = []
        successful_requests = 0
        failed_requests = 0
        
        def make_request(request_id):
            start_time = time.time()
            try:
                response = self.session.get(f"{self.lb_url}/", timeout=10)
                end_time = time.time()
                response_time = (end_time - start_time) * 1000  # 毫秒
                
                with self.results_lock:
                    if response.status_code == 200:
                        response_times.append(response_time)
                        return True
                    else:
                        return False
            except Exception as e:
                return False
        
        start_time = time.time()
        
        # 使用线程池进行并发测试
        with concurrent.futures.ThreadPoolExecutor(max_workers=concurrency) as executor:
            futures = [executor.submit(make_request, i) for i in range(num_requests)]
            
            for future in concurrent.futures.as_completed(futures):
                if future.result():
                    successful_requests += 1
                else:
                    failed_requests += 1
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # 计算统计数据
        if response_times:
            avg_response_time = statistics.mean(response_times)
            median_response_time = statistics.median(response_times)
            min_response_time = min(response_times)
            max_response_time = max(response_times)
            p95_response_time = sorted(response_times)[int(len(response_times) * 0.95)]
        else:
            avg_response_time = median_response_time = min_response_time = max_response_time = p95_response_time = 0
        
        requests_per_second = successful_requests / total_time if total_time > 0 else 0
        
        print("Performance test results:")
        print(f"  Total time: {total_time:.2f}s")
        print(f"  Successful requests: {successful_requests}")
        print(f"  Failed requests: {failed_requests}")
        print(f"  Requests per second: {requests_per_second:.2f}")
        print(f"  Average response time: {avg_response_time:.2f}ms")
        print(f"  Median response time: {median_response_time:.2f}ms")
        print(f"  Min response time: {min_response_time:.2f}ms")
        print(f"  Max response time: {max_response_time:.2f}ms")
        print(f"  95th percentile: {p95_response_time:.2f}ms")
        
        return {
            'total_time': total_time,
            'successful_requests': successful_requests,
            'failed_requests': failed_requests,
            'requests_per_second': requests_per_second,
            'avg_response_time': avg_response_time,
            'median_response_time': median_response_time,
            'min_response_time': min_response_time,
            'max_response_time': max_response_time,
            'p95_response_time': p95_response_time
        }
    
    def test_health_checks(self) -> Dict[str, Any]:
        """测试健康检查功能"""
        print("Testing health check endpoints...")
        
        endpoints = [
            '/lb/health',
            '/lb/stats',
            '/lb/backends',
            '/lb/config'
        ]
        
        results = {}
        
        for endpoint in endpoints:
            try:
                response = self.session.get(f"{self.lb_url}{endpoint}", timeout=5)
                results[endpoint] = {
                    'status_code': response.status_code,
                    'success': response.status_code == 200,
                    'response_size': len(response.content)
                }
                print(f"  {endpoint}: {'✓' if response.status_code == 200 else '✗'} ({response.status_code})")
            except Exception as e:
                results[endpoint] = {
                    'status_code': None,
                    'success': False,
                    'error': str(e)
                }
                print(f"  {endpoint}: ✗ (Error: {e})")
        
        return results
    
    def test_error_handling(self) -> Dict[str, Any]:
        """测试错误处理"""
        print("Testing error handling...")
        
        # 测试不存在的路径
        try:
            response = self.session.get(f"{self.lb_url}/nonexistent", timeout=5)
            print(f"  Non-existent path: {response.status_code}")
        except Exception as e:
            print(f"  Non-existent path: Error - {e}")
        
        # 测试错误端点（如果后端服务器有实现）
        try:
            response = self.session.get(f"{self.lb_url}/error", timeout=5)
            print(f"  Error endpoint: {response.status_code}")
        except Exception as e:
            print(f"  Error endpoint: Error - {e}")
        
        return {}
    
    def run_all_tests(self, num_requests: int = 50, concurrency: int = 10) -> Dict[str, Any]:
        """运行所有测试"""
        print("=" * 60)
        print("Load Balancer Test Suite")
        print("=" * 60)
        
        all_results = {}
        
        # 基本连通性测试
        all_results['connectivity'] = self.test_basic_connectivity()
        
        if not all_results['connectivity']:
            print("Connectivity test failed. Skipping other tests.")
            return all_results
        
        print()
        
        # 后端分布测试
        all_results['distribution'] = self.test_backend_distribution(num_requests)
        print()
        
        # 会话保持测试
        all_results['session_affinity'] = self.test_session_affinity(20)
        print()
        
        # 性能测试
        all_results['performance'] = self.test_performance(num_requests, concurrency)
        print()
        
        # 健康检查测试
        all_results['health_checks'] = self.test_health_checks()
        print()
        
        # 错误处理测试
        all_results['error_handling'] = self.test_error_handling()
        
        print("=" * 60)
        print("Test Suite Completed")
        print("=" * 60)
        
        return all_results


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='Load Balancer Tester')
    parser.add_argument('--url', default='http://localhost:8080',
                       help='Load balancer URL')
    parser.add_argument('--requests', type=int, default=50,
                       help='Number of requests for testing')
    parser.add_argument('--concurrency', type=int, default=10,
                       help='Concurrency level for performance testing')
    parser.add_argument('--output', help='Output file for results (JSON format)')
    
    args = parser.parse_args()
    
    tester = LoadBalancerTester(args.url)
    results = tester.run_all_tests(args.requests, args.concurrency)
    
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"Results saved to {args.output}")


if __name__ == '__main__':
    main()