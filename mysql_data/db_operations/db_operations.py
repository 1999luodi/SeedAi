"""
SeedAI 数据库操作脚本
用于管理和操作SeedAI项目的数据库
"""

import os
import sys
from pathlib import Path
import subprocess
import platform

def run_mysql_command(command, database="ai_dataset"):
    """
    执行MySQL命令
    """
    mysql_cmd = [
        "docker", "exec", "-i", "seedai-mysql-1",
        "mysql", "-u", "root", "-prootpass", database
    ]
    
    try:
        result = subprocess.run(
            mysql_cmd,
            input=command,
            text=True,
            capture_output=True,
            check=True
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"MySQL命令执行失败: {e}")
        print(f"错误输出: {e.stderr}")
        return None

def check_and_add_role_column():
    """
    检查并添加role列到用户表
    """
    print("正在检查用户表的role列...")
    
    # 检查role列是否存在
    check_column_query = """
    SELECT COLUMN_NAME 
    FROM INFORMATION_SCHEMA.COLUMNS 
    WHERE TABLE_SCHEMA = 'ai_dataset' AND TABLE_NAME = 'users' AND COLUMN_NAME = 'role';
    """
    
    result = run_mysql_command(check_column_query)
    
    if result and "role" in result:
        print("role列已存在")
    else:
        print("role列不存在，正在添加...")
        alter_table_query = """
        ALTER TABLE users ADD COLUMN role INT DEFAULT 0;
        """
        result = run_mysql_command(alter_table_query)
        
        if result is not None:
            print("role列添加成功")
        else:
            print("role列添加失败")

def ensure_default_users():
    """
    确保默认用户存在
    """
    print("正在检查默认用户...")
    
    # 检查admin用户
    check_admin_query = "SELECT id, username, role FROM users WHERE username='admin';"
    admin_result = run_mysql_command(check_admin_query)
    
    if admin_result and "admin" in admin_result:
        print("admin用户已存在，正在更新其角色为超级管理员...")
        update_admin_role_query = "UPDATE users SET role=2 WHERE username='admin';"
        run_mysql_command(update_admin_role_query)
        print("admin用户角色已更新为超级管理员")
    else:
        print("admin用户不存在，需要通过应用创建")
    
    # 检查user1用户
    check_user1_query = "SELECT id, username FROM users WHERE username='user1';"
    user1_result = run_mysql_command(check_user1_query)
    
    if user1_result and "user1" in user1_result:
        print("user1用户已存在")
    else:
        print("user1用户不存在，需要通过应用创建")

def list_all_users():
    """
    列出所有用户
    """
    print("正在获取所有用户...")
    query = "SELECT id, username, email, role, is_active FROM users;"
    result = run_mysql_command(query)
    
    if result:
        print("用户列表:")
        print(result)
    else:
        print("无法获取用户列表")

def create_index_on_users():
    """
    为用户表创建索引以提高查询性能
    """
    print("正在为用户表创建索引...")
    
    # 为username创建索引
    index_query = "CREATE INDEX IF NOT EXISTS idx_username ON users (username);"
    result = run_mysql_command(index_query)
    
    if result is not None:
        print("username索引创建成功")
    else:
        print("username索引创建失败")
    
    # 为email创建索引
    index_query = "CREATE INDEX IF NOT EXISTS idx_email ON users (email);"
    result = run_mysql_command(index_query)
    
    if result is not None:
        print("email索引创建成功")
    else:
        print("email索引创建失败")

def update_user_role(username, role):
    """
    更新用户角色
    """
    print(f"正在更新{username}的用户角色为{role}...")
    query = f"UPDATE users SET role={role} WHERE username='{username}';"
    result = run_mysql_command(query)
    
    if result is not None:
        print(f"{username}的用户角色已更新")
    else:
        print(f"{username}的用户角色更新失败")

def show_database_stats():
    """
    显示数据库统计信息
    """
    print("正在获取数据库统计信息...")
    
    queries = {
        "用户数量": "SELECT COUNT(*) AS count FROM users;",
        "数据集数量": "SELECT COUNT(*) AS count FROM datasets;",
        "图片数量": "SELECT COUNT(*) AS count FROM images;"
    }
    
    for desc, query in queries.items():
        result = run_mysql_command(query)
        if result:
            print(f"{desc}: {result.strip()}")

def main():
    """
    主函数，提供交互式菜单
    """
    print("=" * 50)
    print("SeedAI 数据库操作工具")
    print("=" * 50)
    print("功能列表:")
    print("1. 检查并添加role列")
    print("2. 确保默认用户存在")
    print("3. 列出所有用户")
    print("4. 创建用户表索引")
    print("5. 更新用户角色 (admin: 2, user1: 1, 普通用户: 0)")
    print("6. 显示数据库统计")
    print("7. 执行完整设置 (1, 2, 4)")
    print("q. 退出")
    print("-" * 50)
    
    while True:
        choice = input("请选择功能 (1-7, q): ").strip()
        
        if choice == '1':
            check_and_add_role_column()
        elif choice == '2':
            ensure_default_users()
        elif choice == '3':
            list_all_users()
        elif choice == '4':
            create_index_on_users()
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
            show_database_stats()
        elif choice == '7':
            check_and_add_role_column()
            ensure_default_users()
            create_index_on_users()
        elif choice.lower() == 'q':
            print("退出脚本")
            break
        else:
            print("无效选择，请重试")
        
        print("-" * 50)

if __name__ == "__main__":
    main()