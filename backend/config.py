import os
import secrets
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or secrets.token_hex(32)
    
    # 从环境变量获取数据库配置，默认为本地开发配置
    @staticmethod
    def get_database_uri():
        return os.environ.get('DATABASE_URL') or \
               'mysql+pymysql://root:rootpass@mysql:3306/ai_dataset'
    
    # 设置SQLALCHEMY_DATABASE_URI
    SQLALCHEMY_DATABASE_URI = get_database_uri.__func__()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # 确保上传目录存在
    UPLOAD_FOLDER = os.path.join(basedir, 'uploads')
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)

    # 数据集原始文件存储目录：backend/datasets/<username>/<dataset_name>_<id>/
    DATASETS_FOLDER = os.path.join(basedir, 'datasets')
    os.makedirs(DATASETS_FOLDER, exist_ok=True)
    
    # Align backend request limit with workspace upload policy (<5GB total).
    MAX_CONTENT_LENGTH = 6 * 1024 * 1024 * 1024
    
    # 允许的文件扩展名
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'tiff', 'webp'}
    
    # JWT配置
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or SECRET_KEY
    JWT_ACCESS_TOKEN_EXPIRES = 3600  # 1小时

    # Comma-separated list, e.g. "http://localhost,http://127.0.0.1".
    CORS_ORIGINS = [
        item.strip() for item in os.environ.get('CORS_ORIGINS', 'http://localhost,http://127.0.0.1').split(',')
        if item.strip()
    ]