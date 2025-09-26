import pytest
from unittest.mock import Mock, patch
from limiter.redis_bucket import allow_user
import redis

def test_allow_user_success():
    """测试允许请求的情况"""
    with patch('limiter.redis_bucket.r') as mock_redis:
        # 模拟Redis返回1（允许）
        mock_redis.eval.return_value = 1
        
        result = allow_user("test_user", capacity=10, refill_rate=1.0)
        
        assert result == True
        assert mock_redis.eval.called

def test_allow_user_denied():
    """测试拒绝请求的情况"""
    with patch('limiter.redis_bucket.r') as mock_redis:
        # 模拟Redis返回0（拒绝）
        mock_redis.eval.return_value = 0
        
        result = allow_user("test_user", capacity=10, refill_rate=1.0)
        
        assert result == False
        assert mock_redis.eval.called

def test_redis_error_handling():
    """测试Redis错误处理"""
    with patch('limiter.redis_bucket.r') as mock_redis:
        # 模拟Redis错误
        mock_redis.eval.side_effect = redis.RedisError("Connection failed")
        
        result = allow_user("test_user", capacity=10, refill_rate=1.0)
        
        # 失败开放策略：出错时允许请求
        assert result == True

def test_lua_script_parameters():
    """测试Lua脚本参数传递"""
    with patch('limiter.redis_bucket.r') as mock_redis:
        mock_redis.eval.return_value = 1
        
        allow_user("user123", capacity=20, refill_rate=2.5, requested=3)
        
        # 检查调用参数
        args, kwargs = mock_redis.eval.call_args
        assert args[1] == 1  # KEYS数量
        assert args[2] == "tb:user123"  # key
        assert args[3] == 20  # capacity
        assert args[4] == 2.5  # refill_rate
        assert args[6] == 3  # requested tokens

@pytest.mark.integration
def test_redis_integration():
    """集成测试（需要真实Redis）"""
    try:
        # 尝试连接Redis
        test_redis = redis.Redis(host='localhost', port=6379, db=0, 
                                decode_responses=True, socket_connect_timeout=1)
        test_redis.ping()
        
        # 清理测试数据
        test_key = "tb:integration_test"
        test_redis.delete(test_key)
        
        # 测试限流功能
        user_id = "integration_test"
        
        # 前几个请求应该成功
        for i in range(5):
            result = allow_user(user_id, capacity=5, refill_rate=1.0)
            assert result == True
        
        # 超出容量的请求应该失败
        result = allow_user(user_id, capacity=5, refill_rate=1.0)
        assert result == False
        
        # 清理
        test_redis.delete(test_key)
        
    except (redis.ConnectionError, redis.TimeoutError):
        pytest.skip("Redis不可用，跳过集成测试")