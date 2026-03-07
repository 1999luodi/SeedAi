import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app import app, db
from models import User, Dataset, Image, Annotation
from services.user_service import UserService

def init_db():
    """Initialize the database with tables"""
    with app.app_context():
        # Create all tables
        db.create_all()
        print("Database tables created successfully!")
        
        # Create super admin account
        UserService.create_super_admin('admin', 'admin@admin.com', '123456')
        
        # Create a regular user
        UserService.create_user('user1', 'user1@example.com', '123456', role=0)
        
        print("Database initialization completed!")

if __name__ == '__main__':
    init_db()