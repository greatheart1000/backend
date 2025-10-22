from fastapi import FastAPI, UploadFile, File, Form, HTTPException, status
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
import subprocess
import asyncio
from openai import OpenAI, APIError, RateLimitError, AuthenticationError

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 初始化OpenAI客户端
client = OpenAI(
    base_url='https://api-inference.modelscope.cn/v1',
    api_key='ms-3e77e144-197b-44f3-93be-87c5d0f0ce16', # ModelScope Token
)

# 创建FastAPI应用
app = FastAPI(title="Enhanced Code Analysis Agent", 
              description="AI Agent that analyzes code, generates structured reports, and provides dynamic verification with test generation",
              version="2.0.0")

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

@app.get("/")
async def root():
    logger.info("Root endpoint accessed")
    return {"message": "Enhanced Code Analysis Agent is running"}

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
        with open(zip_path, "wb") as buffer:
            content = await code_zip.read()
            buffer.write(content)
        logger.info(f"Saved uploaded file to: {zip_path}")
        
        # 检查文件大小（限制为50MB）
        file_size = os.path.getsize(zip_path)
        if file_size > 50 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="File size exceeds 50MB limit")
        logger.info(f"File size: {file_size} bytes")
        
        # 解压文件
        extracted_files = await extract_zip(zip_path, temp_dir)
        logger.info(f"Extracted {len(extracted_files)} files")
        
        # 收集代码上下文
        code_context = await collect_code_context(extracted_files)
        logger.info(f"Collected code context, length: {len(code_context)} characters")
        
        # 调用大模型API进行分析
        logger.info("Calling LLM API for analysis")
        analysis_result = await analyze_with_llm(problem_description, code_context)
        logger.info("LLM API call completed")
        
        # 验证结果格式
        validated_result = await validate_and_format_result(analysis_result)
        logger.info("Result validation completed")
        
        # 如果启用验证，进行动态验证
        functional_verification = None
        if enable_verification:
            logger.info("Starting functional verification")
            functional_verification = await perform_functional_verification(
                problem_description, 
                code_context, 
                extracted_files,
                temp_dir
            )
            logger.info("Functional verification completed")
        
        # 构建最终响应
        response = {
            "feature_analysis": validated_result.get("feature_analysis", []),
            "execution_plan_suggestion": validated_result.get("execution_plan_suggestion", ""),
            "functional_verification": functional_verification
        }
        
        return response
        
    except HTTPException:
        # 重新抛出HTTP异常
        raise
    except Exception as e:
        logger.error(f"Error during analysis: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # 清理临时目录
        logger.info(f"Cleaning up temporary directory: {temp_dir}")
        shutil.rmtree(temp_dir, ignore_errors=True)

async def extract_zip(zip_path: str, temp_dir: str) -> List[str]:
    """
    解压ZIP文件到指定目录
    """
    logger.info(f"Extracting ZIP file: {zip_path}")
    extracted_files = []
    
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            for file_info in zip_ref.infolist():
                # 提取文件名并防止路径遍历漏洞
                filename = os.path.basename(file_info.filename)
                if filename and not filename.startswith('.') and not filename.startswith('__'):
                    # 构造安全的文件路径
                    file_path = os.path.join(temp_dir, filename)
                    # 确保父目录存在
                    os.makedirs(os.path.dirname(file_path), exist_ok=True)
                    # 提取文件
                    with zip_ref.open(file_info) as source, open(file_path, 'wb') as target:
                        shutil.copyfileobj(source, target)
                    extracted_files.append(file_path)
                    logger.debug(f"Extracted file: {file_path}")
    except zipfile.BadZipFile:
        logger.error("Invalid ZIP file provided")
        raise HTTPException(status_code=400, detail="Invalid ZIP file")
    except Exception as e:
        logger.error(f"Error extracting ZIP file: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error extracting ZIP file: {str(e)}")
    
    logger.info(f"Successfully extracted {len(extracted_files)} files")
    return extracted_files

async def collect_code_context(file_paths: List[str]) -> str:
    """
    收集代码文件的内容作为上下文
    """
    logger.info(f"Collecting code context from {len(file_paths)} files")
    context_parts = []
    
    for file_path in file_paths:
        try:
            # 只读取文本文件，避免二进制文件
            if is_text_file(file_path):
                file_size = os.path.getsize(file_path)
                # 限制单个文件大小（500KB）
                if file_size > 500 * 1024:
                    logger.warning(f"Skipping large file {file_path} ({file_size} bytes)")
                    continue
                
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    # 限制内容长度以避免超出API限制
                    if len(content) > 50000:  # 限制每个文件最多50000字符
                        content = content[:50000] + "\n... (content truncated)"
                    context_parts.append(f"File: {file_path}\nContent:\n{content}\n")
                    logger.debug(f"Collected content from {file_path}, length: {len(content)}")
        except Exception as e:
            logger.warning(f"Could not read file {file_path}: {str(e)}")
    
    # 限制总内容长度
    full_context = "\n".join(context_parts)
    if len(full_context) > 200000:  # 限制总内容最多200000字符
        full_context = full_context[:200000] + "\n... (context truncated)"
    
    logger.info(f"Collected code context, total length: {len(full_context)} characters")
    return full_context

def is_text_file(file_path: str) -> bool:
    """
    判断是否为文本文件
    """
    text_extensions = {'.py', '.js', '.ts', '.java', '.cpp', '.h', '.cs', '.go', '.rb', '.php', '.html', '.css', '.xml', '.json', '.yaml', '.yml', '.md', '.txt'}
    _, ext = os.path.splitext(file_path)
    return ext.lower() in text_extensions

async def analyze_with_llm(problem_description: str, code_context: str) -> Dict[Any, Any]:
    """
    使用大模型API分析代码并生成报告
    """
    logger.info("Starting LLM analysis")
    
    # 构造提示词
    prompt = f"""
    你是一个代码分析专家。请分析以下代码并根据问题描述生成一份结构化的分析报告。
    
    问题描述:
    {problem_description}
    
    代码内容:
    {code_context}
    
    请按照以下JSON格式输出报告:
    {{
      "feature_analysis": [
        {{
          "feature_description": "功能描述",
          "implementation_location": [
            {{
              "file": "文件路径",
              "function": "函数名",
              "lines": "行号范围"
            }}
          ]
        }}
      ],
      "execution_plan_suggestion": "执行计划建议"
    }}
    
    重要说明：
    1. 请严格按照上述JSON格式输出，不要包含任何额外的文本或解释
    2. feature_analysis数组中应包含问题描述中提到的所有功能点
    3. implementation_location数组中应包含实现每个功能点的关键代码位置
    4. 执行计划建议应包括如何运行该项目的基本指导
    
    请只输出有效的JSON，不要包含其他内容。
    """
    
    try:
        # 调用大模型API
        logger.info("Calling ModelScope API")
        response = client.chat.completions.create(
            model='Qwen/Qwen3-VL-30B-A3B-Instruct',
            messages=[
                {
                    'role': 'user',
                    'content': prompt
                }
            ],
            temperature=0.3,
            max_tokens=4000
        )
        
        # 解析响应
        result_text = response.choices[0].message.content
        logger.info(f"Received response from ModelScope API, length: {len(result_text)} characters")
        
        # 尝试解析JSON
        try:
            result_json = json.loads(result_text)
            logger.info("Successfully parsed JSON response from LLM")
            return result_json
        except json.JSONDecodeError:
            # 如果解析失败，尝试修复常见的JSON格式问题
            logger.warning(f"Failed to parse JSON from LLM response, attempting to fix: {result_text[:100]}...")
            fixed_json = await fix_json_format(result_text)
            return fixed_json
    except RateLimitError as e:
        logger.error(f"Rate limit exceeded when calling LLM API: {str(e)}")
        return {
            "error": "Rate limit exceeded",
            "details": "Too many requests, please try again later"
        }
    except AuthenticationError as e:
        logger.error(f"Authentication error when calling LLM API: {str(e)}")
        return {
            "error": "Authentication failed",
            "details": "Invalid API key or authentication credentials"
        }
    except APIError as e:
        logger.error(f"API error when calling LLM API: {str(e)}")
        return {
            "error": "API error",
            "details": str(e)
        }
    except Exception as e:
        logger.error(f"Unexpected error calling LLM API: {str(e)}", exc_info=True)
        return {
            "error": "Error calling LLM API",
            "details": str(e)
        }

async def fix_json_format(text: str) -> Dict[Any, Any]:
    """
    尝试修复LLM返回的JSON格式问题
    """
    logger.info("Attempting to fix JSON format")
    try:
        # 移除可能的markdown代码块标记
        if text.startswith("```json"):
            text = text[7:]
        if text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        
        # 去除首尾空白字符
        text = text.strip()
        
        # 尝试解析
        result_json = json.loads(text)
        logger.info("Successfully fixed JSON format")
        return result_json
    except Exception as e:
        logger.error(f"Failed to fix JSON format: {str(e)}")
        # 返回默认结构
        return {
            "feature_analysis": [],
            "execution_plan_suggestion": "无法生成执行计划建议"
        }

async def validate_and_format_result(result: Dict[Any, Any]) -> Dict[Any, Any]:
    """
    验证并格式化结果，确保符合预期的JSON结构
    """
    logger.info("Validating and formatting result")
    
    # 检查是否有错误
    if "error" in result:
        # 如果有错误，返回默认结构
        logger.warning(f"Error in analysis result: {result.get('details', result.get('error', 'Unknown error'))}")
        return {
            "feature_analysis": [],
            "execution_plan_suggestion": f"分析过程中出现错误: {result.get('details', result.get('error', 'Unknown error'))}"
        }
    
    # 确保必要的字段存在
    formatted_result = {
        "feature_analysis": result.get("feature_analysis", []),
        "execution_plan_suggestion": result.get("execution_plan_suggestion", "未提供执行计划建议")
    }
    
    # 验证feature_analysis结构
    if not isinstance(formatted_result["feature_analysis"], list):
        formatted_result["feature_analysis"] = []
    
    # 验证每个feature_analysis项
    for feature in formatted_result["feature_analysis"]:
        if not isinstance(feature, dict):
            continue
        if "feature_description" not in feature:
            feature["feature_description"] = "未提供功能描述"
        if "implementation_location" not in feature or not isinstance(feature["implementation_location"], list):
            feature["implementation_location"] = []
        
        # 验证每个implementation_location项
        for location in feature["implementation_location"]:
            if not isinstance(location, dict):
                continue
            if "file" not in location:
                location["file"] = "未知文件"
            if "function" not in location:
                location["function"] = "未知函数"
            if "lines" not in location:
                location["lines"] = "未知行号"
    
    logger.info("Result validation and formatting completed")
    return formatted_result

async def perform_functional_verification(
    problem_description: str, 
    code_context: str, 
    extracted_files: List[str],
    temp_dir: str
) -> Optional[Dict[str, Any]]:
    """
    执行功能验证，生成测试代码并执行
    """
    logger.info("Starting functional verification")
    
    try:
        # 1. 生成测试代码
        test_code = await generate_test_code(problem_description, code_context, extracted_files)
        logger.info(f"Generated test code, length: {len(test_code)} characters")
        
        # 2. 执行测试代码
        execution_result = await execute_test_code(test_code, temp_dir)
        logger.info(f"Test execution completed: {execution_result.get('tests_passed', False)}")
        
        return {
            "generated_test_code": test_code,
            "execution_result": execution_result
        }
        
    except Exception as e:
        logger.error(f"Error during functional verification: {str(e)}", exc_info=True)
        return {
            "generated_test_code": "// 测试代码生成失败",
            "execution_result": {
                "tests_passed": False,
                "log": f"验证失败: {str(e)}"
            }
        }

async def generate_test_code(problem_description: str, code_context: str, extracted_files: List[str]) -> str:
    """
    生成测试代码
    """
    logger.info("Generating test code")
    
    # 分析项目类型
    project_type = detect_project_type(extracted_files)
    logger.info(f"Detected project type: {project_type}")
    
    # 构造测试代码生成提示词
    prompt = f"""
    你是一个测试代码生成专家。请根据以下信息生成可执行的测试代码。
    
    问题描述: {problem_description}
    
    代码内容: {code_context}
    
    项目类型: {project_type}
    
    请生成适合的测试代码，要求：
    1. 测试代码必须是可执行的
    2. 测试应该验证主要功能是否正常工作
    3. 使用合适的测试框架
    4. 包含断言来验证结果
    5. 测试代码应该简洁但完整
    
    请只输出测试代码，不要包含其他解释。
    """
    
    try:
        response = client.chat.completions.create(
            model='Qwen/Qwen3-VL-30B-A3B-Instruct',
            messages=[
                {
                    'role': 'user',
                    'content': prompt
                }
            ],
            temperature=0.3,
            max_tokens=2000
        )
        
        test_code = response.choices[0].message.content
        logger.info("Test code generated successfully")
        return test_code
        
    except Exception as e:
        logger.error(f"Error generating test code: {str(e)}")
        return f"// 测试代码生成失败: {str(e)}"

def detect_project_type(extracted_files: List[str]) -> str:
    """
    检测项目类型
    """
    file_extensions = set()
    for file_path in extracted_files:
        _, ext = os.path.splitext(file_path)
        file_extensions.add(ext.lower())
    
    if '.py' in file_extensions:
        return "Python"
    elif '.js' in file_extensions or '.ts' in file_extensions:
        return "Node.js/TypeScript"
    elif '.java' in file_extensions:
        return "Java"
    elif '.cs' in file_extensions:
        return "C#"
    elif '.go' in file_extensions:
        return "Go"
    else:
        return "Unknown"

async def execute_test_code(test_code: str, temp_dir: str) -> Dict[str, Any]:
    """
    执行测试代码
    """
    logger.info("Executing test code")
    
    try:
        # 保存测试代码到文件
        test_file_path = os.path.join(temp_dir, "generated_test.js")
        with open(test_file_path, 'w', encoding='utf-8') as f:
            f.write(test_code)
        
        # 尝试执行测试
        result = await run_test_command(test_file_path, temp_dir)
        return result
        
    except Exception as e:
        logger.error(f"Error executing test code: {str(e)}")
        return {
            "tests_passed": False,
            "log": f"测试执行失败: {str(e)}"
        }

async def run_test_command(test_file_path: str, temp_dir: str) -> Dict[str, Any]:
    """
    运行测试命令
    """
    try:
        # 检查是否有package.json，如果有则安装依赖
        package_json_path = os.path.join(temp_dir, "package.json")
        if os.path.exists(package_json_path):
            # 安装依赖
            install_process = await asyncio.create_subprocess_exec(
                "npm", "install",
                cwd=temp_dir,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await install_process.wait()
        
        # 尝试运行测试
        process = await asyncio.create_subprocess_exec(
            "node", test_file_path,
            cwd=temp_dir,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        return {
            "tests_passed": process.returncode == 0,
            "log": stdout.decode() + stderr.decode()
        }
        
    except Exception as e:
        return {
            "tests_passed": False,
            "log": f"无法执行测试: {str(e)}"
        }

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting Enhanced Code Analysis Agent server")
    uvicorn.run(app, host="0.0.0.0", port=8000)
