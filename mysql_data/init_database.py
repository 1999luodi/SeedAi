"""
SeedAI 数据库初始化脚本
此脚本用于初始化MySQL数据库，创建表结构和初始数据
"""
import os
import sys
import pymysql
import json
from datetime import datetime
import bcrypt
import subprocess

def get_db_connection():
    """获取数据库连接"""
    connection = pymysql.connect(
        host=os.getenv('MYSQL_HOST', 'mysql'),  # 使用容器名而不是localhost
        port=int(os.getenv('MYSQL_PORT', 3306)),
        user=os.getenv('MYSQL_USER', 'root'),
        password=os.getenv('MYSQL_PASSWORD', 'rootpass'),
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor
    )
    return connection

def create_database_and_tables():
    """创建数据库和表结构"""
    print("正在连接数据库...")
    connection = get_db_connection()
    
    try:
        with connection.cursor() as cursor:
            # 读取并执行SQL初始化脚本
            sql_file_path = os.path.join(os.path.dirname(__file__), 'init_db.sql')
            with open(sql_file_path, 'r', encoding='utf-8') as sql_file:
                sql_commands = sql_file.read()
                
            # 分割SQL命令并执行
            commands = sql_commands.split(';')
            for command in commands:
                command = command.strip()
                if command:
                    cursor.execute(command)
                    
        connection.commit()
        print("✓ 数据库和表结构创建成功")
        
    except Exception as e:
        print(f"✗ 数据库初始化失败: {str(e)}")
        connection.rollback()
        raise
    finally:
        connection.close()

def hash_password(password):
    """使用bcrypt哈希密码"""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def verify_initial_data():
    """验证初始数据"""
    print("正在验证数据库表...")
    connection = get_db_connection()
    
    try:
        with connection.cursor() as cursor:
            # 切换到ai_dataset数据库
            cursor.execute("USE ai_dataset;")
            
            expected_tables = [
                'users',
                'datasets',
                'images',
                'dataset_label_categories',
                'ai_models',
                'schema_migrations',
            ]
            
            for table in expected_tables:
                cursor.execute(f"SELECT COUNT(*) as count FROM information_schema.tables WHERE table_schema = 'ai_dataset' AND table_name = '{table}';")
                result = cursor.fetchone()
                
                if result['count'] > 0:
                    print(f"✓ {table} 表存在")
                else:
                    print(f"✗ {table} 表不存在")
                    
            # 检查用户
            cursor.execute("SELECT username, role FROM users WHERE username IN ('admin', 'user1');")
            users = cursor.fetchall()
            
            for user in users:
                print(f"✓ 用户 {user['username']} 存在，角色: {user['role']}")
                
    except Exception as e:
        print(f"✗ 数据验证失败: {str(e)}")
        raise
    finally:
        connection.close()

def main():
    """主函数"""
    print("=" * 50)
    print("SeedAI 数据库初始化工具")
    print("=" * 50)
    
    print("\n开始执行数据库初始化...")
    
    try:
        # 1. 创建数据库和表结构
        create_database_and_tables()

        # 2. 执行增量迁移，补齐所有后续结构（推荐唯一入口）
        migrate_script = os.path.join(os.path.dirname(__file__), 'migrate.py')
        subprocess.run([sys.executable, migrate_script, '--all'], check=True)
        
        # 3. 验证初始数据
        verify_initial_data()
        
        print("\n✓ 数据库初始化完成！")
        print("\n现在您可以使用以下凭据登录：")
        print("- 超级管理员: admin / 123456 (角色: 2)")
        print("- 普通用户: user1 / 123456 (角色: 0)")
        
    except Exception as e:
        print(f"\n✗ 初始化过程发生错误: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    main()