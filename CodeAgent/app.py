"""
优化版代码分析Agent
主要优化点：
1. 修复ZIP解压逻辑，保留目录结构
2. 使用异步文件IO
3. 添加配置管理和环境变量支持
4. 优化LLM提示词
5. 添加超时保护
6. 添加速率限制
7. 改进测试执行支持多语言
8. 优化代码结构和模块化
"""
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, status, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel
import zipfile
import os
import tempfile
import shutil
import logging
from typing import List, Dict, Any, Optional
import json
import asyncio
from openai import OpenAI, APIError, RateLimitError, AuthenticationError
import aiofiles
from datetime import datetime, timedelta
from collections import defaultdict
import traceback

# 导入配置
from config import settings

# 配置日志
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 初始化OpenAI客户端
# 内置API密钥以便快速部署
client = OpenAI(
    base_url=settings.openai_base_url,
    api_key=settings.openai_api_key,
)

# 创建FastAPI应用
app = FastAPI(
    title="Enhanced Code Analysis Agent", 
    description="AI Agent that analyzes code, generates structured reports, and provides dynamic verification with test generation",
    version="2.1.0"
)

# 简单的速率限制器
class RateLimiter:
    def __init__(self, max_requests: int, time_window: int = 60):
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests = defaultdict(list)
    
    def check_rate_limit(self, client_id: str) -> bool:
        now = datetime.now()
        # 清理过期的请求记录
        self.requests[client_id] = [
            req_time for req_time in self.requests[client_id]
            if now - req_time < timedelta(seconds=self.time_window)
        ]
        
        # 检查是否超过限制
        if len(self.requests[client_id]) >= self.max_requests:
            return False
        
        # 记录新请求
        self.requests[client_id].append(now)
        return True

rate_limiter = RateLimiter(max_requests=settings.rate_limit_per_minute)

# 中间件：速率限制
@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    client_id = request.client.host
    if not rate_limiter.check_rate_limit(client_id):
        return JSONResponse(
            status_code=429,
            content={"detail": "Too many requests. Please try again later."}
        )
    response = await call_next(request)
    return response

# 自定义异常处理器
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    logger.error(f"Validation error: {exc}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": exc.errors(), "body": exc.body},
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An unexpected error occurred"},
    )

# Pydantic模型
class ImplementationLocation(BaseModel):
    file: str
    function: str
    lines: str

class FeatureAnalysis(BaseModel):
    feature_description: str
    implementation_location: List[ImplementationLocation]

class FunctionalVerification(BaseModel):
    generated_test_code: str
    execution_result: Optional[Dict[str, Any]] = None

class EnhancedAnalysisReport(BaseModel):
    feature_analysis: List[FeatureAnalysis]
    execution_plan_suggestion: str
    functional_verification: Optional[FunctionalVerification] = None

class FileInfo(BaseModel):
    """文件信息模型"""
    path: str
    relative_path: str
    size: int
    extension: str

@app.get("/")
async def root():
    logger.info("Root endpoint accessed")
    return {
        "message": "Enhanced Code Analysis Agent is running",
        "version": "2.1.0",
        "status": "healthy"
    }

@app.get("/health")
async def health_check():
    """健康检查端点"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "api_configured": client is not None
    }

@app.post("/analyze", response_model=EnhancedAnalysisReport)
async def analyze_code(
    problem_description: str = Form(...),
    code_zip: UploadFile = File(...),
    enable_verification: bool = Form(False)
):
    """
    接收问题描述和代码压缩包，生成代码功能定位报告，并可选择进行动态验证
    """
    logger.info(f"Analysis request received. Problem description length: {len(problem_description)}")
    logger.info(f"Verification enabled: {enable_verification}")
    
    # 验证API配置
    if not client:
        raise HTTPException(
            status_code=503,
            detail="Service not configured. Please configure OPENAI_API_KEY."
        )
    
    # 验证输入
    if not problem_description.strip():
        logger.warning("Empty problem description provided")
        raise HTTPException(status_code=400, detail="Problem description cannot be empty")
    
    if not code_zip:
        logger.warning("No code zip file provided")
        raise HTTPException(status_code=400, detail="Code zip file is required")
    
    # 检查文件类型
    if not code_zip.filename.endswith('.zip'):
        logger.warning(f"Invalid file type provided: {code_zip.filename}")
        raise HTTPException(status_code=400, detail="Only ZIP files are accepted")
    
    # 创建临时目录用于解压文件
    temp_dir = tempfile.mkdtemp()
    logger.info(f"Created temporary directory: {temp_dir}")
    
    try:
        # 保存上传的文件
        zip_path = os.path.join(temp_dir, code_zip.filename)
        async with aiofiles.open(zip_path, "wb") as buffer:
            content = await code_zip.read()
            await buffer.write(content)
        logger.info(f"Saved uploaded file to: {zip_path}")
        
        # 检查文件大小
        file_size = os.path.getsize(zip_path)
        max_size = settings.max_file_size_mb * 1024 * 1024
        if file_size > max_size:
            raise HTTPException(
                status_code=400, 
                detail=f"File size exceeds {settings.max_file_size_mb}MB limit"
            )
        logger.info(f"File size: {file_size} bytes")
        
        # 解压文件（修复后的版本，保留目录结构）
        extracted_files = await extract_zip_with_structure(zip_path, temp_dir)
        logger.info(f"Extracted {len(extracted_files)} files")
        
        # 收集代码上下文（使用异步IO）
        code_context = await collect_code_context_async(extracted_files)
        logger.info(f"Collected code context, length: {len(code_context)} characters")
        
        # 调用大模型API进行分析（添加超时保护）
        logger.info("Calling LLM API for analysis")
        analysis_result = await asyncio.wait_for(
            analyze_with_llm_optimized(problem_description, code_context, extracted_files),
            timeout=settings.llm_api_timeout
        )
        logger.info("LLM API call completed")
        
        # 验证结果格式
        validated_result = await validate_and_format_result(analysis_result)
        logger.info("Result validation completed")
        
        # 如果启用验证，进行动态验证
        functional_verification = None
        if enable_verification:
            logger.info("Starting functional verification")
            try:
                functional_verification = await asyncio.wait_for(
                    perform_functional_verification_optimized(
                        problem_description, 
                        code_context, 
                        extracted_files,
                        temp_dir
                    ),
                    timeout=settings.test_execution_timeout
                )
                logger.info("Functional verification completed")
            except asyncio.TimeoutError:
                logger.warning("Functional verification timed out")
                functional_verification = {
                    "generated_test_code": "// Verification timed out",
                    "execution_result": {
                        "tests_passed": False,
                        "log": f"Verification exceeded timeout of {settings.test_execution_timeout} seconds"
                    }
                }
        
        # 构建最终响应
        response = {
            "feature_analysis": validated_result.get("feature_analysis", []),
            "execution_plan_suggestion": validated_result.get("execution_plan_suggestion", ""),
            "functional_verification": functional_verification
        }
        
        return response
        
    except asyncio.TimeoutError:
        logger.error("Request timed out")
        raise HTTPException(status_code=504, detail="Request timed out")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during analysis: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # 清理临时目录
        logger.info(f"Cleaning up temporary directory: {temp_dir}")
        shutil.rmtree(temp_dir, ignore_errors=True)

async def extract_zip_with_structure(zip_path: str, temp_dir: str) -> List[FileInfo]:
    """
    解压ZIP文件到指定目录，保留完整的目录结构
    
    修复：之前使用os.path.basename()丢失了目录结构
    """
    logger.info(f"Extracting ZIP file: {zip_path}")
    extracted_files = []
    
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            # 获取根目录名称（如果有）
            extract_root = os.path.join(temp_dir, "extracted")
            os.makedirs(extract_root, exist_ok=True)
            
            for file_info in zip_ref.infolist():
                # 跳过目录项和隐藏文件
                if file_info.is_dir():
                    continue
                
                # 获取完整的相对路径
                relative_path = file_info.filename
                
                # 过滤不需要的文件
                if should_skip_file(relative_path):
                    continue
                
                # 构造安全的文件路径（防止路径遍历）
                safe_path = os.path.normpath(relative_path)
                if safe_path.startswith('..') or os.path.isabs(safe_path):
                    logger.warning(f"Skipping potentially unsafe path: {relative_path}")
                    continue
                
                full_path = os.path.join(extract_root, safe_path)
                
                # 确保父目录存在
                os.makedirs(os.path.dirname(full_path), exist_ok=True)
                
                # 提取文件
                with zip_ref.open(file_info) as source, open(full_path, 'wb') as target:
                    shutil.copyfileobj(source, target)
                
                # 获取文件信息
                file_size = os.path.getsize(full_path)
                _, ext = os.path.splitext(full_path)
                
                file_obj = FileInfo(
                    path=full_path,
                    relative_path=relative_path,
                    size=file_size,
                    extension=ext.lower()
                )
                
                extracted_files.append(file_obj)
                logger.debug(f"Extracted file: {relative_path} -> {full_path}")
                
    except zipfile.BadZipFile:
        logger.error("Invalid ZIP file provided")
        raise HTTPException(status_code=400, detail="Invalid ZIP file")
    except Exception as e:
        logger.error(f"Error extracting ZIP file: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error extracting ZIP file: {str(e)}")
    
    logger.info(f"Successfully extracted {len(extracted_files)} files")
    return extracted_files

def should_skip_file(relative_path: str) -> bool:
    """判断是否应该跳过某个文件"""
    skip_patterns = [
        '__MACOSX',  # Mac压缩文件
        '.DS_Store',  # Mac文件系统
        'node_modules',  # Node依赖
        '.git',  # Git目录
        '__pycache__',  # Python缓存
        '.pyc',  # Python编译文件
        'venv', 'env',  # Python虚拟环境
        '.idea', '.vscode',  # IDE配置
        'dist', 'build',  # 构建输出
        '.class', '.jar',  # Java编译文件
    ]
    
    path_lower = relative_path.lower()
    for pattern in skip_patterns:
        if pattern in path_lower:
            return True
    
    # 跳过隐藏文件（以.开头）
    filename = os.path.basename(relative_path)
    if filename.startswith('.') and filename not in ['.gitignore', '.env.example']:
        return True
    
    return False

async def collect_code_context_async(file_infos: List[FileInfo]) -> str:
    """
    使用异步IO收集代码文件的内容
    """
    logger.info(f"Collecting code context from {len(file_infos)} files")
    context_parts = []
    
    # 过滤文本文件
    text_files = [f for f in file_infos if is_text_file_by_extension(f.extension)]
    logger.info(f"Found {len(text_files)} text files to process")
    
    # 并发读取文件
    tasks = []
    for file_info in text_files:
        if file_info.size > settings.max_single_file_size_kb * 1024:
            logger.warning(f"Skipping large file {file_info.relative_path} ({file_info.size} bytes)")
            continue
        tasks.append(read_file_async(file_info))
    
    # 等待所有文件读取完成
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    for result in results:
        if isinstance(result, Exception):
            logger.warning(f"Error reading file: {result}")
            continue
        if result:
            context_parts.append(result)
    
    # 限制总内容长度
    full_context = "\n".join(context_parts)
    if len(full_context) > settings.max_total_context_chars:
        full_context = full_context[:settings.max_total_context_chars] + "\n... (context truncated)"
    
    logger.info(f"Collected code context, total length: {len(full_context)} characters")
    return full_context

async def read_file_async(file_info: FileInfo) -> Optional[str]:
    """异步读取单个文件"""
    try:
        async with aiofiles.open(file_info.path, 'r', encoding='utf-8', errors='ignore') as f:
            content = await f.read()
            
            # 限制内容长度
            if len(content) > settings.max_file_content_chars:
                content = content[:settings.max_file_content_chars] + "\n... (content truncated)"
            
            return f"File: {file_info.relative_path}\nContent:\n{content}\n"
    except Exception as e:
        logger.warning(f"Could not read file {file_info.relative_path}: {str(e)}")
        return None

def is_text_file_by_extension(extension: str) -> bool:
    """判断是否为文本文件"""
    text_extensions = {
        '.py', '.js', '.ts', '.jsx', '.tsx',
        '.java', '.cpp', '.c', '.h', '.hpp', '.cs', '.go', '.rb', '.php',
        '.html', '.css', '.scss', '.sass', '.less',
        '.xml', '.json', '.yaml', '.yml', '.toml', '.ini',
        '.md', '.txt', '.rst',
        '.sql', '.sh', '.bash', '.zsh',
        '.vue', '.svelte', '.dart', '.kt', '.swift',
        '.rs', '.scala', '.r',
    }
    return extension in text_extensions

async def analyze_with_llm_optimized(
    problem_description: str, 
    code_context: str, 
    file_infos: List[FileInfo]
) -> Dict[Any, Any]:
    """
    优化版LLM分析函数
    改进：
    1. 更好的提示词结构
    2. 包含few-shot示例
    3. 提供文件结构概览
    """
    logger.info("Starting optimized LLM analysis")
    
    # 生成文件结构概览
    file_structure = generate_file_structure_overview(file_infos)
    
    # 优化的提示词
    prompt = f"""
你是一个专业的代码分析专家。请仔细分析以下代码并生成一份详细的功能定位报告。

## 项目概览
文件数量: {len(file_infos)}
文件结构:
{file_structure}

## 需求描述
{problem_description}

## 代码内容
{code_context}

## 任务要求
请按照以下JSON格式输出分析报告。注意：
1. 仔细阅读需求描述，识别所有提到的功能点
2. 对每个功能点，找出实现它的关键代码位置
3. 提供准确的文件路径、函数名和行号范围
4. 给出清晰的项目执行指导

## 输出格式示例
{{
  "feature_analysis": [
    {{
      "feature_description": "实现用户登录功能",
      "implementation_location": [
        {{
          "file": "src/auth/login.ts",
          "function": "handleLogin",
          "lines": "15-42"
        }},
        {{
          "file": "src/auth/auth.service.ts",
          "function": "validateCredentials",
          "lines": "67-89"
        }}
      ]
    }}
  ],
  "execution_plan_suggestion": "1. 运行 npm install 安装依赖\\n2. 配置环境变量\\n3. 运行 npm start 启动服务"
}}

## 注意事项
- 只输出有效的JSON，不要包含任何其他文本
- 确保所有字符串都正确转义
- feature_analysis数组应包含所有识别出的功能点
- 行号范围格式：起始行-结束行（如 "15-42"）

请开始分析并输出JSON报告：
"""
    
    try:
        response = client.chat.completions.create(
            model=settings.openai_model,
            messages=[
                {
                    'role': 'system',
                    'content': '你是一个专业的代码分析专家，擅长理解代码结构和功能实现。你总是输出格式正确的JSON。'
                },
                {
                    'role': 'user',
                    'content': prompt
                }
            ],
            temperature=0.2,  # 降低温度以获得更确定的输出
            max_tokens=4000
        )
        
        result_text = response.choices[0].message.content
        logger.info(f"Received response from LLM, length: {len(result_text)} characters")
        
        # 解析JSON
        try:
            result_json = json.loads(result_text)
            logger.info("Successfully parsed JSON response")
            return result_json
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse JSON: {e}, attempting to fix")
            fixed_json = await fix_json_format(result_text)
            return fixed_json
            
    except RateLimitError as e:
        logger.error(f"Rate limit exceeded: {str(e)}")
        return {
            "error": "Rate limit exceeded",
            "details": "Too many requests, please try again later"
        }
    except AuthenticationError as e:
        logger.error(f"Authentication error: {str(e)}")
        return {
            "error": "Authentication failed",
            "details": "Invalid API key"
        }
    except APIError as e:
        logger.error(f"API error: {str(e)}")
        return {
            "error": "API error",
            "details": str(e)
        }
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        return {
            "error": "Error calling LLM API",
            "details": str(e)
        }

def generate_file_structure_overview(file_infos: List[FileInfo]) -> str:
    """生成文件结构概览"""
    structure = []
    
    # 按目录组织文件
    dir_files = defaultdict(list)
    for file_info in file_infos:
        dir_name = os.path.dirname(file_info.relative_path) or "."
        dir_files[dir_name].append(os.path.basename(file_info.relative_path))
    
    # 限制输出长度
    count = 0
    for dir_name in sorted(dir_files.keys()):
        if count > 50:  # 限制最多显示50个目录
            structure.append("... (更多文件)")
            break
        files = dir_files[dir_name][:10]  # 每个目录最多显示10个文件
        structure.append(f"{dir_name}/")
        for file_name in files:
            structure.append(f"  - {file_name}")
        if len(dir_files[dir_name]) > 10:
            structure.append(f"  ... ({len(dir_files[dir_name]) - 10} more files)")
        count += 1
    
    return "\n".join(structure)

async def fix_json_format(text: str) -> Dict[Any, Any]:
    """尝试修复LLM返回的JSON格式问题"""
    logger.info("Attempting to fix JSON format")
    try:
        # 移除markdown代码块标记
        text = text.strip()
        if text.startswith("```json"):
            text = text[7:]
        elif text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        
        text = text.strip()
        
        # 尝试解析
        result_json = json.loads(text)
        logger.info("Successfully fixed JSON format")
        return result_json
    except Exception as e:
        logger.error(f"Failed to fix JSON format: {str(e)}")
        return {
            "feature_analysis": [],
            "execution_plan_suggestion": "无法生成执行计划建议"
        }

async def validate_and_format_result(result: Dict[Any, Any]) -> Dict[Any, Any]:
    """验证并格式化结果"""
    logger.info("Validating and formatting result")
    
    if "error" in result:
        logger.warning(f"Error in analysis result: {result.get('details', 'Unknown error')}")
        return {
            "feature_analysis": [],
            "execution_plan_suggestion": f"分析错误: {result.get('details', result.get('error', 'Unknown'))}"
        }
    
    formatted_result = {
        "feature_analysis": result.get("feature_analysis", []),
        "execution_plan_suggestion": result.get("execution_plan_suggestion", "未提供执行计划")
    }
    
    # 验证结构
    if not isinstance(formatted_result["feature_analysis"], list):
        formatted_result["feature_analysis"] = []
    
    for feature in formatted_result["feature_analysis"]:
        if not isinstance(feature, dict):
            continue
        feature.setdefault("feature_description", "未提供功能描述")
        feature.setdefault("implementation_location", [])
        
        if not isinstance(feature["implementation_location"], list):
            feature["implementation_location"] = []
        
        for location in feature["implementation_location"]:
            if not isinstance(location, dict):
                continue
            location.setdefault("file", "未知文件")
            location.setdefault("function", "未知函数")
            location.setdefault("lines", "未知行号")
    
    logger.info("Validation completed")
    return formatted_result

async def perform_functional_verification_optimized(
    problem_description: str, 
    code_context: str, 
    file_infos: List[FileInfo],
    temp_dir: str
) -> Optional[Dict[str, Any]]:
    """
    优化版功能验证
    改进：
    1. 根据项目类型生成对应的测试
    2. 更好的错误处理
    3. 超时保护
    """
    logger.info("Starting optimized functional verification")
    
    try:
        # 检测项目类型
        project_type = detect_project_type_optimized(file_infos)
        logger.info(f"Detected project type: {project_type}")
        
        # 生成测试代码
        test_code = await generate_test_code_optimized(
            problem_description, 
            code_context, 
            file_infos,
            project_type
        )
        logger.info(f"Generated test code, length: {len(test_code)} characters")
        
        # 执行测试
        execution_result = await execute_test_code_optimized(
            test_code, 
            temp_dir, 
            project_type
        )
        logger.info(f"Test execution completed: {execution_result.get('tests_passed', False)}")
        
        return {
            "generated_test_code": test_code,
            "execution_result": execution_result
        }
        
    except Exception as e:
        logger.error(f"Error during verification: {str(e)}", exc_info=True)
        return {
            "generated_test_code": f"// 测试生成失败\n// Error: {str(e)}",
            "execution_result": {
                "tests_passed": False,
                "log": f"验证失败: {str(e)}"
            }
        }

def detect_project_type_optimized(file_infos: List[FileInfo]) -> str:
    """优化的项目类型检测"""
    extensions = {f.extension for f in file_infos}
    
    # 检查特定的配置文件
    filenames = {os.path.basename(f.relative_path) for f in file_infos}
    
    if 'package.json' in filenames:
        if '.ts' in extensions or '.tsx' in extensions:
            return "typescript"
        return "nodejs"
    elif 'requirements.txt' in filenames or 'setup.py' in filenames:
        return "python"
    elif 'pom.xml' in filenames or 'build.gradle' in filenames:
        return "java"
    elif 'go.mod' in filenames:
        return "go"
    elif 'Cargo.toml' in filenames:
        return "rust"
    elif '.csproj' in str(extensions):
        return "csharp"
    
    # 基于文件扩展名判断
    if '.py' in extensions:
        return "python"
    elif '.js' in extensions or '.ts' in extensions:
        return "nodejs"
    elif '.java' in extensions:
        return "java"
    elif '.go' in extensions:
        return "go"
    elif '.rs' in extensions:
        return "rust"
    elif '.cs' in extensions:
        return "csharp"
    
    return "unknown"

async def generate_test_code_optimized(
    problem_description: str,
    code_context: str,
    file_infos: List[FileInfo],
    project_type: str
) -> str:
    """优化的测试代码生成"""
    logger.info(f"Generating test code for {project_type} project")
    
    # 根据项目类型定制提示词
    test_frameworks = {
        "python": "pytest或unittest",
        "nodejs": "jest或mocha",
        "typescript": "jest with ts-jest",
        "java": "JUnit",
        "go": "testing package",
        "rust": "cargo test",
        "csharp": "NUnit或xUnit"
    }
    
    framework = test_frameworks.get(project_type, "适合的测试框架")
    
    prompt = f"""
你是一个测试代码生成专家。请为以下项目生成可执行的测试代码。

项目类型: {project_type}
推荐测试框架: {framework}

需求描述:
{problem_description}

代码概览:
{code_context[:5000]}  # 限制长度避免超出token限制

请生成测试代码，要求：
1. 使用 {framework} 编写测试
2. 测试应该验证需求描述中提到的主要功能
3. 包含必要的导入和设置
4. 测试应该可以独立运行
5. 包含清晰的断言来验证结果

只输出测试代码，不要包含解释：
"""
    
    try:
        response = client.chat.completions.create(
            model=settings.openai_model,
            messages=[
                {
                    'role': 'system',
                    'content': f'你是一个{project_type}测试专家，擅长编写高质量的测试代码。'
                },
                {
                    'role': 'user',
                    'content': prompt
                }
            ],
            temperature=0.3,
            max_tokens=2000
        )
        
        test_code = response.choices[0].message.content
        
        # 移除可能的markdown标记
        test_code = test_code.strip()
        if test_code.startswith("```"):
            lines = test_code.split("\n")
            test_code = "\n".join(lines[1:-1]) if len(lines) > 2 else test_code
        
        logger.info("Test code generated successfully")
        return test_code
        
    except Exception as e:
        logger.error(f"Error generating test code: {str(e)}")
        return f"// 测试代码生成失败: {str(e)}"

async def execute_test_code_optimized(
    test_code: str,
    temp_dir: str,
    project_type: str
) -> Dict[str, Any]:
    """
    优化的测试代码执行
    支持多种语言和测试框架
    """
    logger.info(f"Executing test code for {project_type} project")
    
    try:
        # 根据项目类型选择执行方式
        if project_type in ["nodejs", "typescript"]:
            return await execute_nodejs_test(test_code, temp_dir)
        elif project_type == "python":
            return await execute_python_test(test_code, temp_dir)
        elif project_type == "java":
            return await execute_java_test(test_code, temp_dir)
        else:
            return {
                "tests_passed": False,
                "log": f"暂不支持 {project_type} 项目的测试执行"
            }
    except Exception as e:
        logger.error(f"Error executing test: {str(e)}")
        return {
            "tests_passed": False,
            "log": f"测试执行失败: {str(e)}\n{traceback.format_exc()}"
        }

async def execute_nodejs_test(test_code: str, temp_dir: str) -> Dict[str, Any]:
    """执行Node.js测试"""
    try:
        # 保存测试文件
        test_file = os.path.join(temp_dir, "extracted", "generated_test.js")
        async with aiofiles.open(test_file, 'w', encoding='utf-8') as f:
            await f.write(test_code)
        
        # 检查是否有package.json
        package_json = os.path.join(temp_dir, "extracted", "package.json")
        if os.path.exists(package_json):
            # 安装依赖
            logger.info("Installing npm dependencies...")
            install_proc = await asyncio.create_subprocess_exec(
                "npm", "install",
                cwd=os.path.dirname(package_json),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await asyncio.wait_for(install_proc.wait(), timeout=60)
        
        # 运行测试
        logger.info("Running Node.js test...")
        process = await asyncio.create_subprocess_exec(
            "node", test_file,
            cwd=os.path.dirname(test_file),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await asyncio.wait_for(
            process.communicate(),
            timeout=30
        )
        
        output = stdout.decode() + stderr.decode()
        return {
            "tests_passed": process.returncode == 0,
            "log": output
        }
        
    except asyncio.TimeoutError:
        return {
            "tests_passed": False,
            "log": "测试执行超时"
        }
    except Exception as e:
        return {
            "tests_passed": False,
            "log": f"Node.js测试执行失败: {str(e)}"
        }

async def execute_python_test(test_code: str, temp_dir: str) -> Dict[str, Any]:
    """执行Python测试"""
    try:
        # 保存测试文件
        test_file = os.path.join(temp_dir, "extracted", "test_generated.py")
        async with aiofiles.open(test_file, 'w', encoding='utf-8') as f:
            await f.write(test_code)
        
        # 尝试运行pytest
        logger.info("Running Python test with pytest...")
        process = await asyncio.create_subprocess_exec(
            "python", "-m", "pytest", test_file, "-v",
            cwd=os.path.dirname(test_file),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await asyncio.wait_for(
            process.communicate(),
            timeout=30
        )
        
        output = stdout.decode() + stderr.decode()
        return {
            "tests_passed": process.returncode == 0,
            "log": output
        }
        
    except asyncio.TimeoutError:
        return {
            "tests_passed": False,
            "log": "测试执行超时"
        }
    except Exception as e:
        return {
            "tests_passed": False,
            "log": f"Python测试执行失败: {str(e)}"
        }

async def execute_java_test(test_code: str, temp_dir: str) -> Dict[str, Any]:
    """执行Java测试"""
    return {
        "tests_passed": False,
        "log": "Java测试执行暂未实现"
    }

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting Enhanced Code Analysis Agent")
    logger.info(f"Configuration: {settings.dict()}")
    uvicorn.run(
        app, 
        host=settings.host, 
        port=settings.port,
        log_level=settings.log_level.lower()
    )
