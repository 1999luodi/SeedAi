"""
SeedAI 系统初始化脚本

此脚本用于初始化SeedAI系统，包括：
1. 创建数据库表
2. 创建默认用户（超级管理员和普通用户）
"""

from db_init import init_db

def main():
    print("=" * 50)
    print("SeedAI 系统初始化")
    print("=" * 50)
    
    print("\n开始初始化...")
    init_db()
    
    print("\n" + "=" * 50)
    print("初始化完成！")
    print("=" * 50)
    print("\n默认账户信息:")
    print("- 超级管理员: admin / 123456")
    print("- 普通用户: user1 / 123456")
    print("\n请使用以上账户信息登录系统。")
    print("注意：超级管理员可访问管理后台并管理所有用户和数据。")

if __name__ == '__main__':
    main()