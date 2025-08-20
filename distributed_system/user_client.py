# user_client.py
# gRPC客户端 - 用户订单客户端

import time
import grpc
import random
import logging

# 导入生成的gRPC代码（假设已经定义）
# 在实际项目中，这些会由protobuf编译器生成

# 模拟的gRPC消息类型（与服务端保持一致）
class OrderRequest:
    def __init__(self, user_id, items):
        self.user_id = user_id
        self.items = items

class OrderItem:
    def __init__(self, product_id, quantity, price):
        self.product_id = product_id
        self.quantity = quantity
        self.price = price

class OrderIdRequest:
    def __init__(self, order_id):
        self.order_id = order_id

class StatusUpdateRequest:
    def __init__(self, order_id, status):
        self.order_id = order_id
        self.status = status

class UserOrdersRequest:
    def __init__(self, user_id):
        self.user_id = user_id

class OrderClient:
    """订单服务客户端"""
    
    def __init__(self, server_address="localhost:50051"):
        # 创建gRPC通道
        self.channel = grpc.insecure_channel(server_address)
        
        # 创建存根（stub）
        # self.stub = order_pb2_grpc.OrderServiceStub(self.channel)
        
        logging.info(f"已连接到订单服务: {server_address}")
    
    def create_order(self, user_id, items):
        """创建订单"""
        try:
            # 构建请求
            request = OrderRequest(user_id=user_id, items=items)
            
            # 调用远程方法
            # response = self.stub.CreateOrder(request)
            
            # 模拟响应
            order_id = f"ORD-{random.randint(1000, 9999)}"
            response = type('OrderResponse', (), {
                'order_id': order_id,
                'success': True,
                'message': "订单创建成功"
            })
            
            logging.info(f"订单创建成功: {response.order_id}")
            return response
        except Exception as e:
            logging.error(f"创建订单失败: {e}")
            return None
    
    def get_order(self, order_id):
        """获取订单详情"""
        try:
            # 构建请求
            request = OrderIdRequest(order_id=order_id)
            
            # 调用远程方法
            # response = self.stub.GetOrder(request)
            
            # 模拟响应
            response = type('OrderDetails', (), {
                'order_id': order_id,
                'user_id': f"user_{random.randint(100, 999)}",
                'items': [
                    type('OrderItem', (), {
                        'product_id': f"prod_{random.randint(1, 100)}",
                        'quantity': random.randint(1, 5),
                        'price': round(random.uniform(10, 100), 2)
                    }) for _ in range(random.randint(1, 3))
                ],
                'total': round(random.uniform(50, 500), 2),
                'status': random.choice(["pending", "processing", "shipped", "delivered"]),
                'created_at': time.time() - random.randint(0, 86400)
            })
            
            logging.info(f"获取订单成功: {order_id}")
            return response
        except Exception as e:
            logging.error(f"获取订单失败: {e}")
            return None
    
    def update_order_status(self, order_id, new_status):
        """更新订单状态"""
        try:
            # 构建请求
            request = StatusUpdateRequest(order_id=order_id, status=new_status)
            
            # 调用远程方法
            # response = self.stub.UpdateOrderStatus(request)
            
            # 模拟响应
            response = type('StatusResponse', (), {
                'success': True,
                'message': f"订单状态已更新为 {new_status}"
            })
            
            logging.info(f"更新订单状态成功: {order_id} -> {new_status}")
            return response
        except Exception as e:
            logging.error(f"更新订单状态失败: {e}")
            return None
    
    def list_user_orders(self, user_id):
        """列出用户的所有订单"""
        try:
            # 构建请求
            request = UserOrdersRequest(user_id=user_id)
            
            # 调用远程方法
            # response = self.stub.ListOrders(request)
            
            # 模拟响应
            orders = [
                type('OrderSummary', (), {
                    'order_id': f"ORD-{random.randint(1000, 9999)}",
                    'total': round(random.uniform(50, 500), 2),
                    'status': random.choice(["pending", "processing", "shipped", "delivered"]),
                    'created_at': time.time() - random.randint(0, 86400)
                }) for _ in range(random.randint(2, 5))
            ]
            
            response = type('OrderList', (), {'orders': orders})
            
            logging.info(f"获取用户订单列表成功: {user_id}, 共 {len(orders)} 个订单")
            return response
        except Exception as e:
            logging.error(f"获取用户订单列表失败: {e}")
            return None
    
    def close(self):
        """关闭gRPC通道"""
        self.channel.close()
        logging.info("已关闭与订单服务的连接")

# 客户端使用示例
def run_client_demo():
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # 创建客户端
    client = OrderClient()
    
    try:
        # 模拟用户ID
        user_id = f"user_{random.randint(100, 999)}"
        
        # 创建订单
        items = [
            OrderItem(
                product_id=f"prod_{random.randint(1, 100)}",
                quantity=random.randint(1, 5),
                price=round(random.uniform(10, 100), 2)
            ) for _ in range(random.randint(1, 3))
        ]
        
        print(f"\n=== 创建订单 (用户: {user_id}) ===")
        create_response = client.create_order(user_id, items)
        if create_response and create_response.success:
            order_id = create_response.order_id
            print(f"订单创建成功: {order_id}")
            
            # 获取订单详情
            print(f"\n=== 获取订单详情 (订单: {order_id}) ===")
            order_details = client.get_order(order_id)
            if order_details:
                print(f"订单ID: {order_details.order_id}")
                print(f"用户ID: {order_details.user_id}")
                print(f"订单状态: {order_details.status}")
                print(f"订单总额: ${order_details.total:.2f}")
                print("订单项:")
                for i, item in enumerate(order_details.items, 1):
                    print(f"  {i}. 产品: {item.product_id}, 数量: {item.quantity}, 单价: ${item.price:.2f}")
            
            # 更新订单状态
            new_status = "processing"
            print(f"\n=== 更新订单状态 (订单: {order_id}, 新状态: {new_status}) ===")
            update_response = client.update_order_status(order_id, new_status)
            if update_response and update_response.success:
                print(f"状态更新成功: {update_response.message}")
        
        # 列出用户订单
        print(f"\n=== 获取用户订单列表 (用户: {user_id}) ===")
        orders_response = client.list_user_orders(user_id)
        if orders_response:
            print(f"用户 {user_id} 的订单列表:")
            for i, order in enumerate(orders_response.orders, 1):
                print(f"  {i}. 订单: {order.order_id}, 状态: {order.status}, 总额: ${order.total:.2f}")
    
    finally:
        # 关闭客户端
        client.close()

# 主函数
if __name__ == "__main__":
    run_client_demo()