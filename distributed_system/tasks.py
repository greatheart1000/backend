# tasks.py
from celery_app import app
import time
import logging
from datetime import datetime

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@app.task(bind=True, max_retries=3, default_retry_delay=5)
def send_welcome_email(self, email, username):
    """
    发送欢迎邮件的异步任务
    
    参数:
        email (str): 用户邮箱
        username (str): 用户名
    
    返回:
        dict: 包含任务执行结果的字典
    """
    try:
        # 记录开始时间
        start_time = time.time()
        
        # 模拟邮件发送延迟
        logger.info(f"准备向 {email} 发送欢迎邮件")
        time.sleep(2)  # 模拟网络延迟
        
        # 模拟邮件发送
        logger.info(f"向 {username} <{email}> 发送欢迎邮件")
        
        # 记录结束时间和执行时间
        end_time = time.time()
        execution_time = end_time - start_time
        
        return {
            "status": "success",
            "message": f"欢迎邮件已发送至 {email}",
            "execution_time": execution_time,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"发送欢迎邮件失败: {str(e)}")
        # 重试任务
        self.retry(exc=e)

@app.task(bind=True, max_retries=5)
def upload_image(self, image_url, filters=None):
    """
    处理图片上传的异步任务
    
    参数:
        image_url (str): 图片URL
        filters (list, optional): 要应用的滤镜列表
    
    返回:
        dict: 包含任务执行结果的字典
    """
    try:
        # 记录开始时间
        start_time = time.time()
        
        # 默认滤镜
        if filters is None:
            filters = ["resize", "optimize"]
        
        # 模拟下载图片
        logger.info(f"下载图片: {image_url}")
        time.sleep(1.5)  # 模拟下载延迟
        
        # 模拟图片处理
        logger.info(f"处理图片，应用滤镜: {', '.join(filters)}")
        for filter_name in filters:
            logger.info(f"应用滤镜: {filter_name}")
            time.sleep(0.5)  # 模拟处理延迟
        
        # 模拟图片上传到存储
        logger.info("上传处理后的图片到存储")
        time.sleep(1)  # 模拟上传延迟
        
        # 生成处理后的图片URL
        processed_url = f"{image_url.split('.')[0]}_processed.jpg"
        
        # 记录结束时间和执行时间
        end_time = time.time()
        execution_time = end_time - start_time
        
        return {
            "status": "success",
            "message": "图片处理完成",
            "original_url": image_url,
            "processed_url": processed_url,
            "applied_filters": filters,
            "execution_time": execution_time,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"图片处理失败: {str(e)}")
        # 重试任务，指数退避策略
        retry_delay = self.request.retries * 2
        self.retry(exc=e, countdown=retry_delay)

@app.task
def process_order(order_data):
    """
    处理订单的异步任务
    
    参数:
        order_data (dict): 订单数据
    
    返回:
        dict: 包含任务执行结果的字典
    """
    try:
        # 记录开始时间
        start_time = time.time()
        
        # 模拟订单处理
        logger.info(f"处理订单: {order_data.get('id', 'unknown')}")
        time.sleep(1)  # 模拟处理延迟
        
        # 模拟库存检查
        logger.info("检查库存")
        time.sleep(0.5)  # 模拟库存检查延迟
        
        # 模拟支付处理
        logger.info("处理支付")
        time.sleep(1.5)  # 模拟支付处理延迟
        
        # 记录结束时间和执行时间
        end_time = time.time()
        execution_time = end_time - start_time
        
        return {
            "status": "success",
            "message": "订单处理完成",
            "order_id": order_data.get('id', 'unknown'),
            "execution_time": execution_time,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"订单处理失败: {str(e)}")
        raise  # 不重试，直接失败