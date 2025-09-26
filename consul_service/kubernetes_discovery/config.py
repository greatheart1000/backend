"""
配置文件
"""
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key'
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'jwt-dev-secret-key'
    CONSUL_HOST = os.environ.get('CONSUL_HOST') or 'localhost'
    CONSUL_PORT = int(os.environ.get('CONSUL_PORT') or 8500)