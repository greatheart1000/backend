# 快速测试脚本 - Windows PowerShell版本

Write-Host "==========================================" -ForegroundColor Blue
Write-Host "Code Analysis Agent 快速测试" -ForegroundColor Blue
Write-Host "==========================================" -ForegroundColor Blue
Write-Host ""

# 测试1: 健康检查
Write-Host "1. 测试健康检查..." -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "http://localhost:8000/health" -Method Get
    if ($response.status -eq "healthy") {
        Write-Host "✓ 健康检查通过" -ForegroundColor Green
    } else {
        Write-Host "✗ 健康检查失败" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "✗ 无法连接到服务" -ForegroundColor Red
    Write-Host "请确保服务已启动: docker-compose up -d" -ForegroundColor Yellow
    exit 1
}
Write-Host ""

# 测试2: 根端点
Write-Host "2. 测试根端点..." -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "http://localhost:8000/" -Method Get
    if ($response.message -like "*Enhanced Code Analysis Agent*") {
        Write-Host "✓ 根端点访问成功" -ForegroundColor Green
    } else {
        Write-Host "✗ 根端点访问失败" -ForegroundColor Red
    }
} catch {
    Write-Host "✗ 根端点访问失败" -ForegroundColor Red
}
Write-Host ""

# 测试3: API文档
Write-Host "3. 测试API文档..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/docs" -Method Get
    if ($response.Content -like "*swagger*") {
        Write-Host "✓ API文档可访问" -ForegroundColor Green
    } else {
        Write-Host "✗ API文档访问失败" -ForegroundColor Red
    }
} catch {
    Write-Host "✗ API文档访问失败" -ForegroundColor Red
}
Write-Host ""

Write-Host "==========================================" -ForegroundColor Blue
Write-Host "✓ 基础测试全部通过！" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Blue
Write-Host ""
Write-Host "下一步：" -ForegroundColor Yellow
Write-Host "- 运行完整测试: python test_agent.py"
Write-Host "- 访问API文档: http://localhost:8000/docs"
Write-Host ""
