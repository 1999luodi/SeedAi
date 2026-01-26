import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key-here'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or f"mysql+pymysql://{os.environ.get('DB_USER', 'root')}:{os.environ.get('DB_PASSWORD', 'rootpass')}@{os.environ.get('DB_HOST', 'localhost')}/{os.environ.get('DB_NAME', 'ai_dataset')}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'jwt-secret-key'
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER', 'uploads')
    DATASETS_FOLDER = os.environ.get('DATASETS_FOLDER', 'datasets')
    MODEL_PATH = os.environ.get('MODEL_PATH', 'pytorch_model/weights/yolov5s.pt')
