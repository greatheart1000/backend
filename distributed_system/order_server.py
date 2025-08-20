# order_server.py
# gRPC服务端 - 订单处理服务

import time
import grpc
import random
from concurrent import futures
import logging

# 导入生成的gRPC代码（假设已经定义）
# 在实际项目中，这些会由protobuf编译器生成
class OrderServicer:
    """订单服务实现"""
    
    def __init__(self):
        self.orders = {}  # 简单的内存存储
        self.order_counter = 1000
        logging.info("订单服务已初始化")
    
    def CreateOrder(self, request, context):
        """创建新订单"""
        # 模拟处理延迟
        time.sleep(0.1)
        
        # 生成订单ID
        order_id = f"ORD-{self.order_counter}"
        self.order_counter += 1
        
        # 存储订单
        self.orders[order_id] = {
            "user_id": request.user_id,
            "items": [{
                "product_id": item.product_id,
                "quantity": item.quantity,
                "price": item.price
            } for item in request.items],
            "total": sum(item.price * item.quantity for item in request.items),
            "status": "pending",
            "created_at": time.time()
        }
        
        logging.info(f"创建订单: {order_id} 用户: {request.user_id} 总金额: {self.orders[order_id]['total']}")
        
        # 返回响应
        return OrderResponse(
            order_id=order_id,
            success=True,
            message="订单创建成功"
        )
    
    def GetOrder(self, request, context):
        """获取订单信息"""
        order_id = request.order_id
        
        # 检查订单是否存在
        if order_id not in self.orders:
            logging.warning(f"订单不存在: {order_id}")
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details(f"订单 {order_id} 不存在")
            return OrderDetails()
        
        # 获取订单信息
        order = self.orders[order_id]
        
        # 构建响应
        items = [OrderItem(
            product_id=item["product_id"],
            quantity=item["quantity"],
            price=item["price"]
        ) for item in order["items"]]
        
        logging.info(f"获取订单: {order_id}")
        
        return OrderDetails(
            order_id=order_id,
            user_id=order["user_id"],
            items=items,
            total=order["total"],
            status=order["status"],
            created_at=order["created_at"]
        )
    
    def UpdateOrderStatus(self, request, context):
        """更新订单状态"""
        order_id = request.order_id
        new_status = request.status
        
        # 检查订单是否存在
        if order_id not in self.orders:
            logging.warning(f"尝试更新不存在的订单: {order_id}")
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details(f"订单 {order_id} 不存在")
            return StatusResponse(success=False, message=f"订单 {order_id} 不存在")
        
        # 更新订单状态
        self.orders[order_id]["status"] = new_status
        
        logging.info(f"更新订单状态: {order_id} -> {new_status}")
        
        return StatusResponse(
            success=True,
            message=f"订单状态已更新为 {new_status}"
        )
    
    def ListOrders(self, request, context):
        """列出用户的所有订单"""
        user_id = request.user_id
        
        # 筛选用户的订单
        user_orders = [{
            "order_id": order_id,
            **order_data
        } for order_id, order_data in self.orders.items() 
          if order_data["user_id"] == user_id]
        
        # 构建响应
        order_list = [OrderSummary(
            order_id=order["order_id"],
            total=order["total"],
            status=order["status"],
            created_at=order["created_at"]
        ) for order in user_orders]
        
        logging.info(f"列出用户订单: {user_id}, 共 {len(order_list)} 个订单")
        
        return OrderList(orders=order_list)

# 模拟的gRPC消息类型
class OrderRequest:
    def __init__(self, user_id, items):
        self.user_id = user_id
        self.items = items


class OrderItem:
    def __init__(self, product_id, quantity, price):
        self.product_id = product_id
        self.quantity = quantity
        self.price = price

class OrderResponse:
    def __init__(self, order_id, success, message):
        self.order_id = order_id
        self.success = success
        self.message = message

class OrderIdRequest:
    def __init__(self, order_id):
        self.order_id = order_id

class OrderDetails:
    def __init__(self, order_id=None, user_id=None, items=None, total=0, status="", created_at=0):
        self.order_id = order_id
        self.user_id = user_id
        self.items = items or []
        self.total = total
        self.status = status
        self.created_at = created_at

class StatusUpdateRequest:
    def __init__(self, order_id, status):
        self.order_id = order_id
        self.status = status

class StatusResponse:
    def __init__(self, success, message):
        self.success = success
        self.message = message

class UserOrdersRequest:
    def __init__(self, user_id):
        self.user_id = user_id

class OrderSummary:
    def __init__(self, order_id, total, status, created_at):
        self.order_id = order_id
        self.total = total
        self.status = status
        self.created_at = created_at

class OrderList:
    def __init__(self, orders):
        self.orders = orders

# 服务器启动函数
def serve():
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # 创建gRPC服务器
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    
    # 注册服务
    # order_pb2_grpc.add_OrderServiceServicer_to_server(OrderServicer(), server)
    
    # 在端口上启动服务器
    port = 50051
    server.add_insecure_port(f'[::]:{port}')
    server.start()
    
    logging.info(f"订单服务器已启动，监听端口 {port}")
    
    try:
        # 保持服务器运行
        server.wait_for_termination()
    except KeyboardInterrupt:
        logging.info("服务器关闭中...")
        server.stop(0)
        logging.info("服务器已关闭")

# 主函数
if __name__ == "__main__":
    serve()