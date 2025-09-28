from algorithms.base import LoadBalancer
from algorithms.round_robin import RoundRobinBalancer
from algorithms.weighted import WeightedRoundRobinBalancer, SmoothWeightedRoundRobinBalancer
from algorithms.ip_hash import IPHashBalancer, ConsistentHashBalancer
from algorithms.least_connections import (
    LeastConnectionsBalancer, 
    WeightedLeastConnectionsBalancer, 
    FastestResponseBalancer
)
from typing import Dict, Type

class LoadBalancerFactory:
    """负载均衡器工厂类"""
    
    _algorithms: Dict[str, Type[LoadBalancer]] = {
        'round_robin': RoundRobinBalancer,
        'weighted_round_robin': WeightedRoundRobinBalancer,
        'smooth_weighted_round_robin': SmoothWeightedRoundRobinBalancer,
        'ip_hash': IPHashBalancer,
        'consistent_hash': ConsistentHashBalancer,
        'least_connections': LeastConnectionsBalancer,
        'weighted_least_connections': WeightedLeastConnectionsBalancer,
        'fastest_response': FastestResponseBalancer,
    }
    
    @classmethod
    def create(cls, algorithm: str, **kwargs) -> LoadBalancer:
        """创建负载均衡器实例
        
        Args:
            algorithm: 算法名称
            **kwargs: 算法特定参数
        
        Returns:
            LoadBalancer实例
        
        Raises:
            ValueError: 未知的算法类型
        """
        if algorithm not in cls._algorithms:
            available = ', '.join(cls._algorithms.keys())
            raise ValueError(f"Unknown algorithm '{algorithm}'. Available: {available}")
        
        algorithm_class = cls._algorithms[algorithm]
        
        # 为特定算法传递参数
        if algorithm == 'consistent_hash':
            virtual_nodes = kwargs.get('virtual_nodes', 150)
            return algorithm_class(virtual_nodes=virtual_nodes)
        elif algorithm == 'ip_hash':
            hash_function = kwargs.get('hash_function', 'md5')
            return algorithm_class(hash_function=hash_function)
        elif algorithm == 'fastest_response':
            connection_weight = kwargs.get('connection_weight', 0.6)
            response_time_weight = kwargs.get('response_time_weight', 0.4)
            return algorithm_class(
                connection_weight=connection_weight,
                response_time_weight=response_time_weight
            )
        else:
            return algorithm_class()
    
    @classmethod
    def get_available_algorithms(cls) -> list:
        """获取所有可用的算法列表"""
        return list(cls._algorithms.keys())
    
    @classmethod
    def get_algorithm_description(cls, algorithm: str) -> str:
        """获取算法描述"""
        descriptions = {
            'round_robin': '轮询 - 请求依次分发到各个后端服务器',
            'weighted_round_robin': '加权轮询 - 根据权重分发请求',
            'smooth_weighted_round_robin': '平滑加权轮询 - 更平滑的权重分发',
            'ip_hash': 'IP哈希 - 基于客户端IP哈希选择后端',
            'consistent_hash': '一致性哈希 - 节点变化时影响最小',
            'least_connections': '最少连接 - 选择连接数最少的后端',
            'weighted_least_connections': '加权最少连接 - 结合权重的最少连接',
            'fastest_response': '最快响应 - 综合连接数和响应时间选择'
        }
        return descriptions.get(algorithm, '未知算法')
    
    @classmethod
    def register_algorithm(cls, name: str, algorithm_class: Type[LoadBalancer]):
        """注册新的算法类"""
        cls._algorithms[name] = algorithm_class