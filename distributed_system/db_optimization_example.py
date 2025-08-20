# db_optimization_example.py
# 导入必要的模块
from datetime import datetime
import os
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey, Text, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, relationship, sessionmaker
from data_generator import simulated_users, simulated_orders

# 创建SQLAlchemy基类
Base = declarative_base()

# 定义数据库模型
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), nullable=False, unique=True)
    email = Column(String(100), nullable=False)
    registered_at = Column(DateTime, nullable=False)
    
    # 创建索引以加速查询
    __table_args__ = (
        Index('idx_user_username', 'username'),
        Index('idx_user_email', 'email'),
    )
    
    # 关系定义
    orders = relationship("Order", back_populates="user")

class Order(Base):
    __tablename__ = "orders"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    order_date = Column(DateTime, nullable=False)
    total_amount = Column(Float, nullable=False)
    description = Column(Text)
    status = Column(String(20), nullable=False)
    
    # 创建索引以加速查询
    __table_args__ = (
        Index('idx_order_user_id', 'user_id'),
        Index('idx_order_date', 'order_date'),
        Index('idx_order_status', 'status'),
    )
    
    # 关系定义
    user = relationship("User", back_populates="orders")

# 数据库连接配置
DATABASE_URL = "sqlite:///./test.db"

# 创建数据库引擎，配置连接池
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},  # 仅用于SQLite
    pool_size=5,  # 连接池大小
    max_overflow=10,  # 最大溢出连接数
    pool_timeout=30,  # 连接超时时间（秒）
    pool_recycle=1800,  # 连接回收时间（秒）
)

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def add_sample_data_from_simulated():
    """从模拟数据添加样本数据到数据库"""
    db = SessionLocal()
    try:
        # 检查数据库是否已有数据
        if db.query(User).first() is None:
            # 批量添加用户
            db_users = []
            user_id_map = {}  # 用于映射模拟ID到数据库实际ID
            for user_data in simulated_users:
                new_user = User(
                    username=user_data["username"],
                    email=user_data["email"],
                    registered_at=datetime.fromisoformat(user_data["registered_at"])
                )
                db_users.append(new_user)
                # 暂时不 commit，先收集

            db.add_all(db_users)
            db.flush()  # 刷新会话，以便获取新插入记录的ID

            for i, user_data in enumerate(simulated_users):
                user_id_map[user_data["id"]] = db_users[i].id  # 建立映射

            # 批量添加订单
            db_orders = []
            for order_data in simulated_orders:
                # 查找对应的数据库用户ID
                db_user_id = user_id_map.get(order_data["user_id"])
                if db_user_id:
                    new_order = Order(
                        user_id=db_user_id,
                        order_date=datetime.fromisoformat(order_data["order_date"]),
                        total_amount=order_data["total_amount"],
                        description=f"Order with items: {', '.join([item['name'] for item in order_data['items']])}",
                        status=order_data["status"]
                    )
                    db_orders.append(new_order)

            db.add_all(db_orders)
            db.commit()
            print(f"Added {len(db_users)} users and {len(db_orders)} orders from simulated data.")
        else:
            print("Database already contains data, skipping simulated data insertion.")
    except Exception as e:
        db.rollback()
        print(f"Error adding simulated data: {e}")
    finally:
        db.close()

# 数据库初始化函数
def create_db_and_tables():
    """创建数据库和表结构"""
    print("创建数据库和表结构...")
    # 使用SQLAlchemy创建所有定义的表
    Base.metadata.create_all(bind=engine)
    print("数据库和表结构创建完成")

# 示例用法
if __name__ == "__main__":
    # 如果数据库文件已存在，先删除它以便重新创建
    if os.path.exists("./test.db"):
        os.remove("./test.db")
        
    create_db_and_tables()
    add_sample_data_from_simulated()  # 使用模拟数据填充数据库

    # 执行一些查询测试
    db = SessionLocal()
    try:
        # 查询用户数量
        user_count = db.query(User).count()
        print(f"数据库中共有 {user_count} 个用户")
        
        # 查询订单数量
        order_count = db.query(Order).count()
        print(f"数据库中共有 {order_count} 个订单")
        
        # 执行一些复杂查询
        first_user = db.query(User).first()
        if first_user:
            print(f"第一个用户: {first_user.username}, 邮箱: {first_user.email}")
            
            # 查找该用户的所有订单
            user_orders = db.query(Order).filter(Order.user_id == first_user.id).all()
            print(f"用户 {first_user.username} 有 {len(user_orders)} 个订单")
            
            # 使用关系查询
            related_orders = first_user.orders
            print(f"通过关系查询，用户 {first_user.username} 有 {len(related_orders)} 个订单")
    finally:
        db.close()