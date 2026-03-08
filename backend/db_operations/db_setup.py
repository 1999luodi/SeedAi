"""
SeedAI 数据库初始化脚本
用于创建数据库表结构和初始数据
"""

import os
import sys
from pathlib import Path
import bcrypt

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app import app
from models import User
from services.user_service import UserService


def create_tables():
    """创建数据库表结构"""
    print("[DEPRECATED] 请使用 mysql_data/migrate.py 进行建表和改表。")
    print("示例: python mysql_data/migrate.py --all")


def insert_initial_data():
    """插入初始数据"""
    with app.app_context():
        # 检查是否已有admin用户
        admin_user = User.query.filter_by(username='admin').first()
        
        if admin_user:
            print("⚠ admin用户已存在，跳过创建")
        else:
            # 创建超级管理员
            UserService.create_super_admin('admin', 'admin@admin.com', '123456')
            print("✓ 超级管理员创建成功: admin / 123456")
        
        # 检查是否已有user1用户
        user1 = User.query.filter_by(username='user1').first()
        
        if user1:
            print("⚠ user1用户已存在，跳过创建")
        else:
            # 创建普通用户
            UserService.create_user('user1', 'user1@example.com', '123456', role=0)
            print("✓ 普通用户创建成功: user1 / 123456")


def verify_tables():
    """验证数据库表是否创建成功"""
    with app.app_context():
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        
        expected_tables = ['users', 'datasets', 'images', 'annotations', 'dataset_label_categories']
        existing_tables = inspector.get_table_names()
        
        print("数据库表验证:")
        for table in expected_tables:
            if table in existing_tables:
                print(f"✓ {table} 表存在")
            else:
                print(f"✗ {table} 表不存在")


def main():
    """主函数"""
    print("=" * 50)
    print("SeedAI 数据库初始化工具")
    print("=" * 50)
    
    print("\n开始执行数据库初始化...")
    
    # 1. 创建表结构
    create_tables()
    
    # 2. 插入初始数据
    insert_initial_data()
    
    # 3. 验证表结构
    verify_tables()
    
    print("\n✓ 数据库初始化完成！")
    print("\n现在您可以使用以下凭据登录：")
    print("- 超级管理员: admin / 123456 (角色: 2)")
    print("- 普通用户: user1 / 123456 (角色: 0)")


if __name__ == '__main__':
    main()