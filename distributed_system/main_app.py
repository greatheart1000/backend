# main_app.py
# 导入必要的模块
import time
import random
from data_generator import simulated_users
from tasks import send_welcome_email, upload_image, process_order

def register_user_with_simulated_data():
    """使用模拟数据注册用户并发送欢迎邮件"""
    user = random.choice(simulated_users)  # 随机选择一个模拟用户
    print(f"Simulating registration for user {user['username']} with email {user['email']}...")
    print(f"User {user['username']} registered successfully.")
    # 调用Celery任务发送欢迎邮件
    task = send_welcome_email.delay(user['email'], user['username'])
    print(f"Scheduling welcome email for {user['email']}... (Task ID: {task.id})")
    return user

def simulate_image_upload(image_url):
    """模拟图片上传并处理"""
    print(f"Uploading image from {image_url}...")
    # 调用Celery任务处理图片
    task = upload_image.delay(image_url)
    print(f"Image processing task submitted. (Task ID: {task.id})")
    return task.id

def simulate_order_processing(order_data):
    """模拟订单处理"""
    print(f"Processing order {order_data['id']}...")
    # 调用Celery任务处理订单
    task = process_order.delay(order_data)
    print(f"Order processing task submitted. (Task ID: {task.id})")
    return task.id

if __name__ == "__main__":
    print("--- Simulating User Registration with Generated Data ---")
    for _ in range(3):  # 模拟3次注册
        register_user_with_simulated_data()

    print("\n--- Simulating Image Upload ---")
    task_id = simulate_image_upload("http://example.com/image_raw.jpg")
    print(f"Image processing task {task_id} submitted.")
    
    # 模拟订单处理
    print("\n--- Simulating Order Processing ---")
    if simulated_users and len(simulated_users) > 0:
        # 创建一个简单的订单数据
        order_data = {
            "id": f"order_{random.randint(1000, 9999)}",
            "user_id": simulated_users[0]["id"],
            "items": ["product1", "product2"],
            "total": 99.99
        }
        order_task_id = simulate_order_processing(order_data)
        print(f"Order processing task {order_task_id} submitted.")

    print("\nMain application continues to run without blocking...")
    time.sleep(2)
    print("Main application finished its immediate tasks.")