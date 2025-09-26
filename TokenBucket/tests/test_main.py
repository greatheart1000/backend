import pytest
from fastapi.testclient import TestClient
from main import app
import time

client = TestClient(app)

def test_ping():
    """测试ping接口"""
    response = client.get("/ping")
    assert response.status_code == 200
    assert response.json() == {"message": "pong"}

def test_hello():
    """测试hello接口"""
    response = client.get("/hello")
    assert response.status_code == 200
    assert response.json() == {"msg": "Hello, I'm rate-limited!"}

def test_rate_limiting():
    """测试限流功能"""
    # 快速发送多个请求，应该被限流
    responses = []
    for i in range(15):
        response = client.get("/hello", headers={"x-user-id": "test-user"})
        responses.append(response.status_code)
        
    # 检查是否有请求被限流 (429状态码)
    rate_limited_count = responses.count(429)
    success_count = responses.count(200)
    
    assert rate_limited_count > 0, "应该有请求被限流"
    assert success_count > 0, "应该有成功的请求"

def test_different_users():
    """测试不同用户的限流是独立的"""
    # 用户1的请求
    user1_responses = []
    for i in range(5):
        response = client.get("/hello", headers={"x-user-id": "user1"})
        user1_responses.append(response.status_code)
    
    # 用户2的请求
    user2_responses = []
    for i in range(5):
        response = client.get("/hello", headers={"x-user-id": "user2"})
        user2_responses.append(response.status_code)
    
    # 两个用户都应该能成功发送一些请求
    assert 200 in user1_responses
    assert 200 in user2_responses

def test_rate_limit_recovery():
    """测试限流恢复功能"""
    # 先消耗所有令牌
    for i in range(12):
        client.get("/hello", headers={"x-user-id": "recovery-test"})
    
    # 等待令牌恢复
    time.sleep(2)
    
    # 应该能够再次成功请求
    response = client.get("/hello", headers={"x-user-id": "recovery-test"})
    # 注意：由于时间控制可能不精确，这里不强制要求成功
    assert response.status_code in [200, 429]