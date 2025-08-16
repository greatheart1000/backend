from flask import Flask, render_template, request, redirect, url_for, jsonify, session
import random
import time
from datetime import datetime
import json

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'  # 用于session加密

# 模拟用户数据库
users = {}

# 数据结构定义
class MarketData:
    def __init__(self, name, code, price, change, change_pct):
        self.name = name
        self.code = code
        self.price = price
        self.change = change
        self.change_pct = change_pct
    
    def to_dict(self):
        return {
            'name': self.name,
            'code': self.code,
            'price': self.price,
            'change': self.change,
            'changePct': self.change_pct
        }

class NewsItem:
    def __init__(self, id, title, summary, time, is_vip):
        self.id = id
        self.title = title
        self.summary = summary
        self.time = time
        self.isVIP = is_vip
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'summary': self.summary,
            'time': self.time,
            'isVIP': self.isVIP
        }

class FuturesData:
    def __init__(self, name, code, price, change, change_pct):
        self.name = name
        self.code = code
        self.price = price
        self.change = change
        self.change_pct = change_pct
    
    def to_dict(self):
        return {
            'name': self.name,
            'code': self.code,
            'price': self.price,
            'change': self.change,
            'changePct': self.change_pct
        }

class StockData:
    def __init__(self, name, code, price, change, change_pct):
        self.name = name
        self.code = code
        self.price = price
        self.change = change
        self.change_pct = change_pct
    
    def to_dict(self):
        return {
            'name': self.name,
            'code': self.code,
            'price': self.price,
            'change': self.change,
            'changePct': self.change_pct
        }

class VideoItem:
    def __init__(self, id, title, thumbnail, views, time):
        self.id = id
        self.title = title
        self.thumbnail = thumbnail
        self.views = views
        self.time = time
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'thumbnail': self.thumbnail,
            'views': self.views,
            'time': self.time
        }

class VIPContent:
    def __init__(self, id, type, title, desc):
        self.id = id
        self.type = type
        self.title = title
        self.desc = desc
    
    def to_dict(self):
        return {
            'id': self.id,
            'type': self.type,
            'title': self.title,
            'desc': self.desc
        }

class MarketCalendar:
    def __init__(self, id, event, date, status):
        self.id = id
        self.event = event
        self.date = date
        self.status = status
    
    def to_dict(self):
        return {
            'id': self.id,
            'event': self.event,
            'date': self.date,
            'status': self.status
        }

def generate_market_data():
    """生成模拟市场数据"""
    return [
        MarketData("上证指数", "SH000001", 3245.67 + random.random() * 100, 1.23, 1.23),
        MarketData("深证成指", "SZ399001", 12456.78 + random.random() * 200, -0.45, -0.45),
        MarketData("恒生指数", "HSI", 18234.56 + random.random() * 300, 0.78, 0.78),
        MarketData("道琼斯", "DJI", 34567.89 + random.random() * 500, 0.92, 0.92)
    ]

def generate_news_data():
    """生成模拟新闻数据"""
    return [
        NewsItem(1, "央行宣布降准0.25个百分点，释放长期资金约5000亿元", 
                "此举旨在支持实体经济发展，保持流动性合理充裕...", "10分钟前", True),
        NewsItem(2, "美联储官员暗示可能暂停加息，市场预期转向", 
                "多位美联储官员表示，当前利率水平可能已经足够限制性...", "25分钟前", False),
        NewsItem(3, "新能源汽车销量再创新高，产业链公司业绩亮眼", 
                "数据显示，新能源汽车渗透率持续提升，相关公司股价表现强劲...", "1小时前", False),
        NewsItem(4, "A股三大指数集体收涨，科技股领涨", 
                "今日A股市场表现活跃，科技板块涨幅居前...", "2小时前", False)
    ]

def generate_futures_data():
    """生成模拟期货数据"""
    return [
        FuturesData("螺纹钢", "RB2405", 3456 + random.random() * 100, 2.1, 2.1),
        FuturesData("铁矿石", "I2405", 789 + random.random() * 50, -1.2, -1.2),
        FuturesData("原油", "SC2405", 567 + random.random() * 30, 0.8, 0.8),
        FuturesData("黄金", "AU2406", 2345 + random.random() * 100, 1.5, 1.5)
    ]

def generate_stock_data():
    """生成模拟股票数据"""
    return [
        StockData("贵州茅台", "600519", 1856.00 + random.random() * 50, 2.3, 2.3),
        StockData("宁德时代", "300750", 234.50 + random.random() * 20, -1.1, -1.1),
        StockData("比亚迪", "002594", 198.80 + random.random() * 30, 3.2, 3.2),
        StockData("腾讯控股", "00700", 345.60 + random.random() * 40, 1.8, 1.8)
    ]

def generate_video_data():
    """生成模拟视频数据"""
    return [
        VideoItem(1, "今日市场分析：A股震荡上行，关注这些板块", 
                "https://via.placeholder.com/300x200/1e3a8a/ffffff?text=市场分析", 23000, "15分钟前"),
        VideoItem(2, "投资策略分享：如何把握市场节奏", 
                "https://via.placeholder.com/300x200/f59e0b/ffffff?text=投资策略", 18000, "1小时前"),
        VideoItem(3, "期货交易技巧：风险控制要点", 
                "https://via.placeholder.com/300x200/10b981/ffffff?text=期货技巧", 15000, "2小时前")
    ]

def generate_vip_content():
    """生成模拟VIP内容"""
    return [
        VIPContent(1, "report", "《2024年投资策略报告》", "独家深度分析，把握投资机会"),
        VIPContent(2, "alert", "实时预警", "重要市场信号提醒"),
        VIPContent(3, "analysis", "《行业深度研究报告》", "专业分析师团队出品")
    ]

def generate_market_calendar():
    """生成模拟市场日历"""
    return [
        MarketCalendar(1, "美联储议息会议", "今日", "primary"),
        MarketCalendar(2, "中国CPI数据公布", "明日", "secondary"),
        MarketCalendar(3, "欧央行利率决议", "本周四", "info"),
        MarketCalendar(4, "美国非农数据", "下周五", "warning")
    ]

# 页面路由
@app.route('/')
def index():
    """首页重定向到登录"""
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    """注册页面"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if not username or not password:
            return "用户名和密码不能为空", 400
        
        if username in users:
            return "用户已存在", 400
        
        # 简单密码存储（实际应用中应该使用加密）
        users[username] = password
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """登录页面"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if username in users and users[username] == password:
            session['username'] = username
            return redirect(url_for('home'))
        else:
            return "用户名或密码错误", 401
    
    return render_template('login.html')

@app.route('/home')
def home():
    """主页"""
    if 'username' not in session:
        return redirect(url_for('login'))
    
    return render_template('home.html', username=session['username'])

@app.route('/logout')
def logout():
    """退出登录"""
    session.pop('username', None)
    return redirect(url_for('login'))

# API接口路由
@app.route('/api/market-data')
def api_market_data():
    """市场数据API"""
    data = generate_market_data()
    return jsonify([item.to_dict() for item in data])

@app.route('/api/news')
def api_news():
    """新闻资讯API"""
    data = generate_news_data()
    return jsonify([item.to_dict() for item in data])

@app.route('/api/futures')
def api_futures():
    """期货行情API"""
    data = generate_futures_data()
    return jsonify([item.to_dict() for item in data])

@app.route('/api/stocks')
def api_stocks():
    """股票数据API"""
    data = generate_stock_data()
    return jsonify([item.to_dict() for item in data])

@app.route('/api/videos')
def api_videos():
    """视频内容API"""
    data = generate_video_data()
    return jsonify([item.to_dict() for item in data])

@app.route('/api/vip-content')
def api_vip_content():
    """VIP内容API"""
    data = generate_vip_content()
    return jsonify([item.to_dict() for item in data])

@app.route('/api/market-calendar')
def api_market_calendar():
    """市场日历API"""
    data = generate_market_calendar()
    return jsonify([item.to_dict() for item in data])

if __name__ == '__main__':
    print("启动于 http://localhost:5000 …")
    print("API接口:")
    print("  GET /api/market-data     - 市场数据")
    print("  GET /api/news           - 新闻资讯")
    print("  GET /api/futures        - 期货行情")
    print("  GET /api/stocks         - 股票数据")
    print("  GET /api/videos         - 视频内容")
    print("  GET /api/vip-content    - VIP内容")
    print("  GET /api/market-calendar - 市场日历")
    app.run(debug=True, host='0.0.0.0', port=5000) 