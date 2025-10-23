"""
配置管理模块
"""
import os
from typing import Optional
from pydantic import BaseModel, Field


class Settings(BaseModel):
    """应用配置"""
    
    # API配置
    openai_base_url: str = Field(
        default=os.getenv("OPENAI_BASE_URL", "https://api-inference.modelscope.cn/v1"),
        description="OpenAI API基础URL"
    )
    openai_api_key: str = Field(
        default=os.getenv("OPENAI_API_KEY", "ms-3e77e144-197b-44f3-93be-87c5d0f0ce16"),
        description="OpenAI API密钥"
    )
    openai_model: str = Field(
        default=os.getenv("OPENAI_MODEL", "Qwen/Qwen3-VL-30B-A3B-Instruct"),
        description="使用的模型名称"
    )
    
    # 文件限制
    max_file_size_mb: int = Field(
        default=int(os.getenv("MAX_FILE_SIZE_MB", "50")),
        description="最大文件大小（MB）"
    )
    max_single_file_size_kb: int = Field(
        default=int(os.getenv("MAX_SINGLE_FILE_SIZE_KB", "500")),
        description="单个文件最大大小（KB）"
    )
    max_file_content_chars: int = Field(
        default=int(os.getenv("MAX_FILE_CONTENT_CHARS", "50000")),
        description="单个文件最大字符数"
    )
    max_total_context_chars: int = Field(
        default=int(os.getenv("MAX_TOTAL_CONTEXT_CHARS", "200000")),
        description="总上下文最大字符数"
    )
    
    # API超时配置
    llm_api_timeout: int = Field(
        default=int(os.getenv("LLM_API_TIMEOUT", "120")),
        description="LLM API超时时间（秒）"
    )
    test_execution_timeout: int = Field(
        default=int(os.getenv("TEST_EXECUTION_TIMEOUT", "300")),
        description="测试执行超时时间（秒）"
    )
    
    # 速率限制
    rate_limit_per_minute: int = Field(
        default=int(os.getenv("RATE_LIMIT_PER_MINUTE", "10")),
        description="每分钟最大请求数"
    )
    
    # 服务器配置
    host: str = Field(
        default=os.getenv("HOST", "0.0.0.0"),
        description="服务器主机地址"
    )
    port: int = Field(
        default=int(os.getenv("PORT", "8000")),
        description="服务器端口"
    )
    
    # 日志配置
    log_level: str = Field(
        default=os.getenv("LOG_LEVEL", "INFO"),
        description="日志级别"
    )
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# 创建全局配置实例
settings = Settings()
