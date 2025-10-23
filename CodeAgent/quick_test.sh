#!/bin/bash
# 快速测试脚本 - 验证服务是否正常运行

echo "=========================================="
echo "Code Analysis Agent 快速测试"
echo "=========================================="
echo ""

# 测试1: 健康检查
echo "1. 测试健康检查..."
response=$(curl -s http://localhost:8000/health)
if echo "$response" | grep -q "healthy"; then
    echo "✓ 健康检查通过"
else
    echo "✗ 健康检查失败"
    echo "响应: $response"
    exit 1
fi
echo ""

# 测试2: 根端点
echo "2. 测试根端点..."
response=$(curl -s http://localhost:8000/)
if echo "$response" | grep -q "Enhanced Code Analysis Agent"; then
    echo "✓ 根端点访问成功"
else
    echo "✗ 根端点访问失败"
    exit 1
fi
echo ""

# 测试3: API文档
echo "3. 测试API文档..."
response=$(curl -s http://localhost:8000/docs)
if echo "$response" | grep -q "swagger"; then
    echo "✓ API文档可访问"
else
    echo "✗ API文档访问失败"
fi
echo ""

echo "=========================================="
echo "✓ 基础测试全部通过！"
echo "=========================================="
echo ""
echo "下一步："
echo "- 运行完整测试: python test_agent.py"
echo "- 访问API文档: http://localhost:8000/docs"
echo ""
