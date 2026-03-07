import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'hard to guess string'
    
    # 从环境变量获取数据库配置，默认为本地开发配置
    @staticmethod
    def get_database_uri():
        return os.environ.get('DATABASE_URL') or \
               'mysql+pymysql://root:rootpass@mysql:3306/ai_dataset'
    
    # 设置SQLALCHEMY_DATABASE_URI
    SQLALCHEMY_DATABASE_URI = get_database_uri.__func__()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # 确保上传目录存在
    UPLOAD_FOLDER = os.path.join(basedir, '..', 'uploads')
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    
    # 限制上传文件大小 (100MB)
    MAX_CONTENT_LENGTH = 100 * 1024 * 1024
    
    # 允许的文件扩展名
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'tiff', 'webp'}
    
    # JWT配置
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'jwt-secret-string'
    JWT_ACCESS_TOKEN_EXPIRES = 3600  # 1小时