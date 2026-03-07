"""
SeedAI 数据库管理脚本
此脚本用于管理SeedAI项目的数据库操作
注意：此文件位于MySQL数据目录中，用于执行数据库管理任务
"""

import os
import sys
from pathlib import Path
import bcrypt

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "backend"))

try:
    from app import app, db
    from models import User
    from services.user_service import UserService
except ImportError as e:
    print(f"导入模块失败: {e}")
    print("请确保在正确的环境中运行此脚本")
    sys.exit(1)


def ensure_role_column():
    """确保用户表中有role列"""
    from sqlalchemy import inspect
    with app.app_context():
        inspector = inspect(db.engine)
        columns = [col['name'] for col in inspector.get_columns('users')]
        
        if 'role' not in columns:
            print("Adding 'role' column to users table...")
            with db.engine.connect() as conn:
                conn.execute(db.text("ALTER TABLE users ADD COLUMN role INT DEFAULT 0"))
                conn.commit()
                print("'role' column added successfully!")
        else:
            print("'role' column already exists")


def ensure_default_users():
    """确保默认用户存在"""
    with app.app_context():
        # 检查admin用户
        admin_user = User.query.filter_by(username='admin').first()
        if not admin_user:
            print("Creating admin user...")
            UserService.create_super_admin('admin', 'admin@admin.com', '123456')
        else:
            # 更新admin用户的权限为超级管理员
            admin_user.role = 2
            db.session.commit()
            print("Admin user already exists, updated role to super admin (role=2)")
        
        # 检查user1用户
        user1 = User.query.filter_by(username='user1').first()
        if not user1:
            print("Creating user1...")
            UserService.create_user('user1', 'user1@example.com', '123456', role=0)
        else:
            print("user1 already exists with role:", user1.role)


def reset_user_password(username, new_password):
    """重置指定用户的密码"""
    with app.app_context():
        user = User.query.filter_by(username=username).first()
        if user:
            user.set_password(new_password)
            db.session.commit()
            print(f"Password for user {username} has been reset.")
        else:
            print(f"User {username} not found.")


def list_all_users():
    """列出所有用户"""
    with app.app_context():
        users = User.query.all()
        print("Current users in database:")
        for user in users:
            print(f"- ID: {user.id}, Username: {user.username}, Email: {user.email}, Role: {user.role}, Active: {user.is_active}")


def update_user_role(username, new_role):
    """更新用户角色"""
    with app.app_context():
        user = User.query.filter_by(username=username).first()
        if user:
            user.role = new_role
            db.session.commit()
            print(f"Role for user {username} updated to {new_role}")
        else:
            print(f"User {username} not found.")


def create_new_user(username, email, password, role=0):
    """创建新用户"""
    with app.app_context():
        try:
            UserService.register_user(username, email, password)
            # 设置角色
            user = User.query.filter_by(username=username).first()
            if user:
                user.role = role
                db.session.commit()
                print(f"User {username} created with role {role}")
        except Exception as e:
            print(f"Error creating user {username}: {str(e)}")


def main():
    print("="*50)
    print("SeedAI 数据库管理脚本")
    print("="*50)
    print("功能列表:")
    print("1. 确保role列存在于用户表中")
    print("2. 确保默认用户存在")
    print("3. 列出所有用户")
    print("4. 重置用户密码")
    print("5. 更新用户角色")
    print("6. 创建新用户")
    print("7. 执行完整设置（1 + 2）")
    print("q. 退出")
    print("-"*50)
    
    while True:
        choice = input("请选择功能 (1-7, q): ").strip()
        
        if choice == '1':
            ensure_role_column()
        elif choice == '2':
            ensure_default_users()
        elif choice == '3':
            list_all_users()
        elif choice == '4':
            username = input("请输入用户名: ").strip()
            password = input("请输入新密码: ").strip()
            if username and password:
                reset_user_password(username, password)
            else:
                print("用户名和密码不能为空")
        elif choice == '5':
            username = input("请输入用户名: ").strip()
            try:
                role = int(input("请输入角色等级 (0=普通用户, 1=管理员, 2=超级管理员): ").strip())
                if username and role in [0, 1, 2]:
                    update_user_role(username, role)
                else:
                    print("无效输入")
            except ValueError:
                print("角色等级必须是数字")
        elif choice == '6':
            username = input("请输入用户名: ").strip()
            email = input("请输入邮箱: ").strip()
            password = input("请输入密码: ").strip()
            try:
                role = int(input("请输入角色等级 (0=普通用户, 1=管理员, 2=超级管理员): ").strip())
                if username and email and password and role in [0, 1, 2]:
                    create_new_user(username, email, password, role)
                else:
                    print("所有字段都必须填写且角色等级必须是0, 1, 或2")
            except ValueError:
                print("角色等级必须是数字")
        elif choice == '7':
            ensure_role_column()
            ensure_default_users()
        elif choice.lower() == 'q':
            print("退出脚本")
            break
        else:
            print("无效选择，请重试")
        
        print("-"*50)


if __name__ == '__main__':
    main()