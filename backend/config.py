import os
from datetime import timedelta

class Config:
    """应用配置类"""
    # 基础配置
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # 数据库配置
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'mysql+pymysql://root:123456@127.0.0.1:3306/internship_db?charset=utf8mb4'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = False
    
    # JWT配置
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or SECRET_KEY
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)
    JWT_ALGORITHM = 'HS256'
    
    # 文件上传配置
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'txt', 'jpg', 'jpeg', 'png'}
    
    # 签到配置
    CHECKIN_NORMAL_DISTANCE = 200  # 兼容旧逻辑，默认200米
    CHECKIN_ABNORMAL_DISTANCE = 500  # 兼容旧逻辑
    CHECKIN_WORKDAY_START = '09:00'  # 签到开始时间
    CHECKIN_WORKDAY_END = '18:00'    # 签到结束时间
    CHECKIN_ALLOW_MULTIPLE = False   # 每日是否允许多次签到

    # 论坛配置
    FORUM_PAGE_SIZE = 20
    FORUM_MAX_IMAGES = 3
    FORUM_MAX_IMAGE_SIZE_MB = 5
    FORUM_SENSITIVE_CHECK_ENABLED = False  # 可接入敏感词服务时置为True
    FORUM_SENSITIVE_WORDS = []
    
    # 微信小程序配置
    WX_APPID = os.environ.get('WX_APPID') or ''
    WX_SECRET = os.environ.get('WX_SECRET') or ''
    
    # 日志配置
    LOG_FILE = 'app.log'
    LOG_LEVEL = 'INFO'

