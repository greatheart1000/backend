# product_service_with_cache.py
# 带缓存的产品服务 - 演示分布式系统中的缓存应用

import time
import json
import random
import logging
from functools import wraps

# 模拟Redis客户端
class RedisClient:
    """模拟Redis缓存客户端"""
    
    def __init__(self):
        self.cache = {}  # 简单的内存字典作为缓存
        self.ttl = {}    # 存储键的过期时间
        logging.info("Redis缓存客户端已初始化")
    
    def get(self, key):
        """获取缓存值"""
        # 检查键是否存在且未过期
        if key in self.cache and (key not in self.ttl or self.ttl[key] > time.time()):
            logging.info(f"缓存命中: {key}")
            return self.cache[key]
        
        # 如果键已过期，删除它
        if key in self.ttl and self.ttl[key] <= time.time():
            del self.cache[key]
            del self.ttl[key]
        
        logging.info(f"缓存未命中: {key}")
        return None
    
    def set(self, key, value, ex=None):
        """设置缓存值，可选过期时间（秒）"""
        self.cache[key] = value
        
        # 如果设置了过期时间
        if ex is not None:
            self.ttl[key] = time.time() + ex
        
        logging.info(f"缓存已设置: {key}, 过期时间: {ex if ex else '永不过期'}")
    
    def delete(self, key):
        """删除缓存键"""
        if key in self.cache:
            del self.cache[key]
            if key in self.ttl:
                del self.ttl[key]
            logging.info(f"缓存已删除: {key}")
            return True
        return False
    
    def flush(self):
        """清空所有缓存"""
        self.cache.clear()
        self.ttl.clear()
        logging.info("缓存已清空")

# 模拟数据库
class ProductDatabase:
    """模拟产品数据库"""
    
    def __init__(self):
        # 预填充一些产品数据
        self.products = {
            f"prod_{i}": {
                "id": f"prod_{i}",
                "name": f"产品 {i}",
                "description": f"这是产品 {i} 的详细描述",
                "price": round(random.uniform(10, 1000), 2),
                "stock": random.randint(0, 100),
                "category": random.choice(["电子", "服装", "食品", "家居", "玩具"]),
                "rating": round(random.uniform(1, 5), 1)
            } for i in range(1, 21)  # 创建20个产品
        }
        logging.info(f"产品数据库已初始化，共 {len(self.products)} 个产品")
    
    def get_product(self, product_id):
        """从数据库获取产品信息"""
        # 模拟数据库查询延迟
        time.sleep(0.2)  # 200ms延迟
        
        if product_id in self.products:
            logging.info(f"数据库查询: 产品 {product_id}")
            return self.products[product_id]
        
        logging.warning(f"数据库查询: 产品 {product_id} 不存在")
        return None
    
    def get_products_by_category(self, category):
        """从数据库获取指定类别的产品"""
        # 模拟数据库查询延迟
        time.sleep(0.5)  # 500ms延迟
        
        products = [p for p in self.products.values() if p["category"] == category]
        logging.info(f"数据库查询: 类别 {category}, 找到 {len(products)} 个产品")
        return products
    
    def update_product(self, product_id, data):
        """更新产品信息"""
        # 模拟数据库更新延迟
        time.sleep(0.3)  # 300ms延迟
        
        if product_id in self.products:
            # 更新产品数据
            for key, value in data.items():
                if key in self.products[product_id]:
                    self.products[product_id][key] = value
            
            logging.info(f"数据库更新: 产品 {product_id}")
            return self.products[product_id]
        
        logging.warning(f"数据库更新: 产品 {product_id} 不存在")
        return None

# 缓存装饰器
def cache(ttl=60):
    """缓存装饰器，用于自动缓存函数结果"""
    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            # 生成缓存键
            key = f"{func.__name__}:{':'.join(str(arg) for arg in args)}"
            
            # 尝试从缓存获取
            cached_result = self.cache.get(key)
            if cached_result is not None:
                return json.loads(cached_result)
            
            # 如果缓存未命中，调用原始函数
            result = func(self, *args, **kwargs)
            
            # 将结果存入缓存
            if result is not None:
                self.cache.set(key, json.dumps(result), ex=ttl)
            
            return result
        return wrapper
    return decorator

# 产品服务
class ProductService:
    """带缓存的产品服务"""
    
    def __init__(self):
        self.db = ProductDatabase()
        self.cache = RedisClient()
        logging.info("产品服务已初始化")
    
    @cache(ttl=30)  # 缓存30秒
    def get_product(self, product_id):
        """获取产品信息，带缓存"""
        return self.db.get_product(product_id)
    
    @cache(ttl=60)  # 缓存60秒
    def get_products_by_category(self, category):
        """获取指定类别的产品，带缓存"""
        return self.db.get_products_by_category(category)
    
    def update_product(self, product_id, data):
        """更新产品信息并清除相关缓存"""
        # 更新数据库
        updated_product = self.db.update_product(product_id, data)
        
        if updated_product:
            # 清除产品缓存
            self.cache.delete(f"get_product:{product_id}")
            
            # 清除可能包含此产品的类别缓存
            self.cache.delete(f"get_products_by_category:{updated_product['category']}")
            
            # 如果类别已更改，还需要清除旧类别的缓存
            if 'category' in data and data['category'] != updated_product['category']:
                self.cache.delete(f"get_products_by_category:{data['category']}")
        
        return updated_product
    
    def clear_cache(self):
        """清空所有缓存"""
        self.cache.flush()

# 服务使用示例
def run_product_service_demo():
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # 创建产品服务
    service = ProductService()
    
    # 测试产品查询（首次，无缓存）
    print("\n=== 测试产品查询（首次，无缓存）===")
    start_time = time.time()
    product = service.get_product("prod_1")
    query_time = time.time() - start_time
    print(f"查询时间: {query_time:.3f}秒")
    print(f"产品信息: {product['name']}, 价格: ${product['price']}, 库存: {product['stock']}")
    
    # 测试产品查询（第二次，有缓存）
    print("\n=== 测试产品查询（第二次，有缓存）===")
    start_time = time.time()
    product = service.get_product("prod_1")
    query_time = time.time() - start_time
    print(f"查询时间: {query_time:.3f}秒")
    print(f"产品信息: {product['name']}, 价格: ${product['price']}, 库存: {product['stock']}")
    
    # 测试类别查询（首次，无缓存）
    category = "电子"
    print(f"\n=== 测试类别查询: {category}（首次，无缓存）===")
    start_time = time.time()
    products = service.get_products_by_category(category)
    query_time = time.time() - start_time
    print(f"查询时间: {query_time:.3f}秒")
    print(f"找到 {len(products)} 个产品:")
    for i, p in enumerate(products[:3], 1):  # 只显示前3个
        print(f"  {i}. {p['name']}, 价格: ${p['price']}")
    if len(products) > 3:
        print(f"  ... 以及其他 {len(products) - 3} 个产品")
    
    # 测试类别查询（第二次，有缓存）
    print(f"\n=== 测试类别查询: {category}（第二次，有缓存）===")
    start_time = time.time()
    products = service.get_products_by_category(category)
    query_time = time.time() - start_time
    print(f"查询时间: {query_time:.3f}秒")
    print(f"找到 {len(products)} 个产品")
    
    # 测试产品更新和缓存失效
    print("\n=== 测试产品更新和缓存失效 ===")
    update_data = {"price": 888.88, "stock": 50}
    print(f"更新产品 prod_1: {update_data}")
    service.update_product("prod_1", update_data)
    
    # 查询更新后的产品（缓存应已失效）
    print("\n=== 查询更新后的产品（缓存应已失效）===")
    start_time = time.time()
    product = service.get_product("prod_1")
    query_time = time.time() - start_time
    print(f"查询时间: {query_time:.3f}秒")
    print(f"产品信息: {product['name']}, 价格: ${product['price']}, 库存: {product['stock']}")

# 主函数
if __name__ == "__main__":
    run_product_service_demo()