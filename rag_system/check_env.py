#!/usr/bin/env python3
"""
环境检查脚本
用于检查RAG系统运行所需的环境和依赖
"""

import sys
import importlib
import subprocess

def check_python_version():
    """检查Python版本"""
    print("检查Python版本...")
    version = sys.version_info
    if version.major >= 3 and version.minor >= 7:
        print(f"✓ Python版本: {version.major}.{version.minor}.{version.micro}")
        return True
    else:
        print(f"✗ Python版本过低: {version.major}.{version.minor}.{version.micro} (需要 >= 3.7)")
        return False

def check_package(package_name, min_version=None):
    """检查Python包是否安装"""
    print(f"检查 {package_name}...")
    try:
        package = importlib.import_module(package_name)
        if hasattr(package, '__version__'):
            version = package.__version__
            print(f"✓ {package_name} 版本: {version}")
        else:
            print(f"✓ {package_name} 已安装")
        return True
    except ImportError:
        print(f"✗ {package_name} 未安装")
        return False

def check_command(command):
    """检查系统命令是否存在"""
    print(f"检查 {command}...")
    try:
        result = subprocess.run(['which', command], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✓ {command} 可用")
            return True
        else:
            print(f"✗ {command} 不可用")
            return False
    except Exception:
        print(f"✗ {command} 检查失败")
        return False

def check_redis_connection():
    """检查Redis连接"""
    print("检查Redis连接...")
    try:
        import redis
        from config.settings import settings
        
        redis_client = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            password=settings.REDIS_PASSWORD
        )
        
        # 测试连接
        redis_client.ping()
        print(f"✓ Redis连接成功 ({settings.REDIS_HOST}:{settings.REDIS_PORT})")
        return True
    except Exception as e:
        print(f"✗ Redis连接失败: {e}")
        return False

def check_elasticsearch_connection():
    """检查Elasticsearch连接"""
    print("检查Elasticsearch连接...")
    try:
        from elasticsearch import Elasticsearch
        from config.settings import settings
        
        es_client = Elasticsearch(
            [{"host": settings.ELASTICSEARCH_HOST, "port": settings.ELASTICSEARCH_PORT}]
        )
        
        # 测试连接
        if es_client.ping():
            print(f"✓ Elasticsearch连接成功 ({settings.ELASTICSEARCH_HOST}:{settings.ELASTICSEARCH_PORT})")
            return True
        else:
            print("✗ Elasticsearch连接失败")
            return False
    except Exception as e:
        print(f"✗ Elasticsearch连接失败: {e}")
        return False

def check_elasticsearch_index():
    """检查Elasticsearch索引是否存在"""
    print("检查Elasticsearch索引...")
    try:
        from elasticsearch import Elasticsearch
        from config.settings import settings
        
        es_client = Elasticsearch(
            [{"host": settings.ELASTICSEARCH_HOST, "port": settings.ELASTICSEARCH_PORT}]
        )
        
        # 检查索引是否存在
        if es_client.indices.exists(index="rag_documents"):
            print("✓ Elasticsearch索引 rag_documents 存在")
            return True
        else:
            print("⚠ Elasticsearch索引 rag_documents 不存在（请运行初始化脚本）")
            return False
    except Exception as e:
        print(f"✗ Elasticsearch索引检查失败: {e}")
        return False

def main():
    """主函数"""
    print("RAG系统环境检查")
    print("=" * 50)
    
    # 检查Python版本
    checks = []
    checks.append(check_python_version())
    
    # 检查必要的Python包
    required_packages = [
        'torch',
        'transformers',
        'sentence_transformers',
        'redis',
        'elasticsearch',
        'numpy',
        'sklearn',
        'openai',
        'flask'
    ]
    
    for package in required_packages:
        checks.append(check_package(package))
    
    # 检查系统命令
    required_commands = ['pip', 'python']
    for command in required_commands:
        checks.append(check_command(command))
    
    # 检查数据库连接（如果配置了）
    try:
        from config.settings import settings
        if settings.REDIS_HOST and settings.REDIS_PORT:
            checks.append(check_redis_connection())
        
        if settings.ELASTICSEARCH_HOST and settings.ELASTICSEARCH_PORT:
            checks.append(check_elasticsearch_connection())
            checks.append(check_elasticsearch_index())
    except Exception as e:
        print(f"配置检查失败: {e}")
    
    # 统计结果
    passed = sum(checks)
    total = len(checks)
    
    print("\n" + "=" * 50)
    print(f"环境检查完成: {passed}/{total} 项通过")
    
    if passed == total:
        print("✓ 环境检查全部通过，可以运行RAG系统")
        return 0
    else:
        print("✗ 环境检查未通过，请检查上述错误并修复")
        return 1

if __name__ == "__main__":
    sys.exit(main())