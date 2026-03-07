"""
SeedAI 集成测试 - 后台管理
测试用户列表显示和管理操作
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from tests.utils.api_client import APIClient
from tests.utils.test_helpers import (
    print_section, log_test, generate_unique_username,
    generate_unique_email
)

class TestAdminDashboard:
    """后台管理测试"""
    
    @classmethod
    def setup_class(cls):
        """测试初始化"""
        cls.client = APIClient()
        cls.users = []
    
    def test_dashboard_load(self):
        """测试1: 仪表板加载"""
        print_section("测试管理仪表板加载")
        
        try:
            response = self.client.get_admin_dashboard()
            
            assert response.status_code == 200, f"仪表板加载失败: {response.status_code}"
            assert '总用户数' in response.text or 'stat-value' in response.text
            
            log_test("仪表板加载", True, "仪表板成功加载")
            
        except Exception as e:
            log_test("仪表板加载", False, str(e))
            raise
    
    def test_users_list_page(self):
        """测试2: 用户列表页面"""
        print_section("测试用户列表页面")
        
        try:
            response = self.client.get_users_admin()
            
            assert response.status_code == 200, f"用户列表页面加载失败: {response.status_code}"
            assert '用户' in response.text or 'username' in response.text.lower()
            
            log_test("用户列表页面", True, "用户列表页面成功加载")
            
        except Exception as e:
            log_test("用户列表页面", False, str(e))
            raise
    
    def test_register_and_display(self):
        """测试3: 注册用户并在后台显示"""
        print_section("测试注册和显示")
        
        try:
            # 注册一个新用户
            username = generate_unique_username("admintest")
            email = generate_unique_email("admintest")
            password = "TestPassword123"
            
            reg_response = self.client.register(username, email, password)
            assert reg_response.get('success') is True
            
            self.users.append({
                'username': username,
                'email': email,
                'id': reg_response.get('data', {}).get('id')
            })
            
            # 检查用户是否在后台列表中
            list_response = self.client.get_users_admin()
            assert username in list_response.text, f"用户 {username} 不在列表中"
            
            log_test("注册和显示", True, f"用户 {username} 成功显示在后台")
            
        except Exception as e:
            log_test("注册和显示", False, str(e))
            raise

def run_admin_tests():
    """运行所有管理后台测试"""
    print("\n" + "="*70)
    print(" " * 15 + "👨‍💼 SeedAI 后台管理集成测试")
    print("="*70)
    
    test_class = TestAdminDashboard()
    test_class.setup_class()
    
    tests = [
        ("仪表板加载", test_class.test_dashboard_load),
        ("用户列表页面", test_class.test_users_list_page),
        ("注册和显示", test_class.test_register_and_display),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            test_func()
            passed += 1
        except Exception as e:
            print(f"\n❌ 测试失败: {test_name}")
            print(f"   错误: {str(e)}\n")
            failed += 1
    
    print("\n" + "="*70)
    print(f"📊 测试总结: {passed} 通过, {failed} 失败")
    print("="*70 + "\n")
    
    return passed, failed

if __name__ == '__main__':
    passed, failed = run_admin_tests()
    exit(0 if failed == 0 else 1)
