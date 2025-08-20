import uuid
import random
from datetime import datetime, timedelta

# --- 1. 模拟用户信息 ---
def generate_users(num_users: int = 100) -> list[dict]:
    users = []
    for i in range(num_users):
        user_id = str(uuid.uuid4())[:8] # 简化ID
        username = f"user_{user_id}"
        
        # 模拟一些特殊邮箱格式或不常见域名
        if i % 10 == 0: # 每10个用户有一个特殊邮箱
            email = f"{username}_test@{random.choice(['invalid.com', 'example.org', 'mail.co'])}"
        elif i % 7 == 0:
            email = f"{username}+alias@{random.choice(['gmail.com', 'outlook.com'])}"
        else:
            email = f"{username}@{random.choice(['example.com', 'gmail.com', 'yahoo.com', 'outlook.com'])}"
        
        registered_at = datetime.now() - timedelta(days=random.randint(0, 365 * 3)) # 3年内随机注册时间

        users.append({
            "id": user_id,
            "username": username,
            "email": email,
            "registered_at": registered_at.isoformat() # 转换为ISO格式字符串以便存储和传输
        })
    print(f"Generated {len(users)} users.")
    return users

# --- 2. 模拟商品信息 ---
def generate_products(num_products: int = 50) -> list[dict]:
    products = []
    product_names = [
        "Laptop Pro", "Gaming Mouse", "Mechanical Keyboard", "Monitor 4K",
        "USB-C Hub", "External SSD", "Webcam HD", "Noise Cancelling Headphones",
        "Smart Speaker", "E-Reader", "Fitness Tracker", "Smartwatch Ultra",
        "Coffee Maker", "Air Fryer", "Robot Vacuum", "Electric Toothbrush",
        "Drone DJI", "Action Camera", "Portable Projector", "Wireless Charger",
        "Graphic Tablet", "VR Headset", "Smart Thermostat", "Security Camera",
        "Portable Bluetooth Speaker", "Gaming Chair", "Ergonomic Desk",
        "LED Desk Lamp", "Smart Light Bulb", "Smart Plug", "Doorbell Camera",
        "GPS Navigator", "Dash Cam", "Car Charger", "Bluetooth Car Adapter",
        "Travel Backpack", "Water Bottle", "Smart Lock", "Wireless Earbuds",
        "USB Flash Drive", "Router Wi-Fi 6", "Range Extender", "Network Cable",
        "Power Bank", "Printer Ink", "Paper Shredder", "Calculator Scientific",
        "Stylus Pen", "Screen Cleaner Kit"
    ]
    
    for i in range(num_products):
        product_id = str(uuid.uuid4())[:10]
        name = random.choice(product_names) + f" {random.randint(1, 99)}" # 确保名称不重复太多
        price = round(random.uniform(9.99, 1999.99), 2)
        description = f"High quality {name} with advanced features."
        
        # 模拟部分商品库存为0或非常低
        if i % 5 == 0:
            stock = 0 # 模拟售罄
        elif i % 7 == 0:
            stock = random.randint(1, 5) # 模拟低库存
        else:
            stock = random.randint(10, 500)
            
        products.append({
            "id": product_id,
            "name": name,
            "price": price,
            "description": description,
            "stock": stock
        })
    print(f"Generated {len(products)} products.")
    return products

# --- 3. 模拟订单信息 ---
def generate_orders(users: list[dict], products: list[dict], num_orders: int = 500) -> list[dict]:
    orders = []
    
    # 筛选出有库存的商品，以便生成有效订单
    available_products = [p for p in products if p["stock"] > 0]
    if not available_products:
        print("Warning: No available products to create orders.")
        return []

    for i in range(num_orders):
        order_id = str(uuid.uuid4())[:12]
        
        # 随机选择一个用户
        user = random.choice(users)
        user_id = user["id"]
        
        order_date = datetime.now() - timedelta(days=random.randint(0, 365)) # 1年内随机订单时间
        
        # 随机选择1到5个商品作为订单项
        num_items = random.randint(1, 5)
        
        order_items = []
        total_amount = 0.0
        
        selected_products = random.sample(available_products, min(num_items, len(available_products)))
        
        for prod in selected_products:
            quantity = random.randint(1, min(prod["stock"], 3)) # 购买数量不超过库存
            order_items.append({
                "product_id": prod["id"],
                "name": prod["name"],
                "price": prod["price"],
                "quantity": quantity
            })
            total_amount += prod["price"] * quantity
            
        # 模拟不同的订单状态
        status = random.choice(["completed", "pending_payment", "shipped", "cancelled"])
        
        orders.append({
            "id": order_id,
            "user_id": user_id,
            "order_date": order_date.isoformat(),
            "total_amount": round(total_amount, 2),
            "items": order_items,
            "status": status
        })
    print(f"Generated {len(orders)} orders.")
    return orders


simulated_users = generate_users(200) # 200个用户
simulated_products = generate_products(100) # 100个商品
simulated_orders = generate_orders(simulated_users, simulated_products, 1000) # 1000个订单

# 打印一些示例数据来检查
print("\n--- Example User Data ---")
for _ in range(3):
    print(random.choice(simulated_users))

print("\n--- Example Product Data ---")
for _ in range(3):
    print(random.choice(simulated_products))

print("\n--- Example Order Data ---")
for _ in range(3):
    print(random.choice(simulated_orders))