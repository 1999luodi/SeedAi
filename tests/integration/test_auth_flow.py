"""
SeedAI 集成测试 - 认证流程
测试用户注册、登录和Token生成
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from tests.utils.api_client import APIClient
from tests.utils.assertions import assert_api_success, assert_user_registered, assert_user_logged_in
from tests.utils.test_helpers import (
    print_section, log_test, generate_unique_username, 
    generate_unique_email, format_response
)

class TestAuthFlow:
    """认证流程测试"""
    
    @classmethod
    def setup_class(cls):
        """测试类初始化"""
        cls.client = APIClient()
        cls.test_username = generate_unique_username()
        cls.test_email = generate_unique_email()
        cls.test_password = "TestPassword123"
    
    def test_user_registration(self):
        """测试1: 用户注册"""
        print_section("测试用户注册")
        
        try:
            response = self.client.register(
                username=self.test_username,
                email=self.test_email,
                password=self.test_password
            )
            
            assert response.get('success') is True, "注册失败"
            assert response.get('data', {}).get('username') == self.test_username
            
            log_test("用户注册", True, 
                    f"用户 {self.test_username} 已创建 (ID: {response.get('data', {}).get('id')})")
            
            # 保存用户ID用于后续测试
            self.__class__.test_user_id = response.get('data', {}).get('id')
            
        except Exception as e:
            log_test("用户注册", False, str(e))
            raise
    
    def test_duplicate_username(self):
        """测试2: 重复用户名检查"""
        print_section("测试重复用户名检查")
        
        try:
            # 尝试用相同用户名注册第二个账号
            response = self.client._request('POST', '/api/auth/register', {
                'username': self.test_username,  # 重复的用户名
                'email': generate_unique_email(),
                'password': 'DifferentPassword123'
            })
            
            assert response.status_code == 400, "应该返回400错误"
            assert response.json().get('success') is False
            
            log_test("重复用户名检查", True, "系统正确拒绝重复用户名")
            
        except Exception as e:
            log_test("重复用户名检查", False, str(e))
            raise
    
    def test_user_login(self):
        """测试3: 用户登录"""
        print_section("测试用户登录")
        
        try:
            response = self.client.login(
                username_or_email=self.test_username,
                password=self.test_password
            )
            
            assert response.get('success') is True, "登录失败"
            assert response.get('data', {}).get('token') is not None, "未获得Token"
            
            log_test("用户登录", True, f"已获得Token: {self.client.token[:20]}...")
            
        except Exception as e:
            log_test("用户登录", False, str(e))
            raise
    
    def test_wrong_password(self):
        """测试5: 错误密码登录"""
        print_section("测试错误密码处理")
        
        try:
            response = self.client._request('POST', '/api/auth/login', {
                'username_or_email': self.test_username,
                'password': 'WrongPassword123'  # 错误的密码
            })
            
            assert response.status_code == 401, "应该返回401错误"
            assert response.json().get('success') is False
            
            log_test("错误密码检查", True, "系统正确拒绝错误密码")
            
        except Exception as e:
            log_test("错误密码检查", False, str(e))
            raise
    
    def test_login_with_email(self):
        """测试6: 用邮箱登录"""
        print_section("测试用邮箱登录")
        
        try:
            # 创建新客户端实例
            client = APIClient()
            
            response = client.login(
                username_or_email=self.test_email,  # 用邮箱而不是用户名
                password=self.test_password
            )
            
            assert response.get('success') is True, "邮箱登录失败"
            assert response.get('data', {}).get('token') is not None
            
            log_test("邮箱登录", True, "已用邮箱成功登录")
            
        except Exception as e:
            log_test("邮箱登录", False, str(e))
            raise

def run_auth_tests():
    """运行所有认证测试"""
    print("\n" + "="*70)
    print(" " * 15 + "🔐 SeedAI 认证流程集成测试")
    print("="*70)
    
    test_class = TestAuthFlow()
    test_class.setup_class()
    
    tests = [
        ("后端健康检查", test_class.test_backend_health),
        ("用户注册", test_class.test_user_registration),
        ("重复用户名检查", test_class.test_duplicate_username),
        ("用户登录", test_class.test_user_login),
        ("错误密码处理", test_class.test_wrong_password),
        ("邮箱登录", test_class.test_login_with_email),
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
    
    # 打印总结
    print("\n" + "="*70)
    print(f"📊 测试总结: {passed} 通过, {failed} 失败")
    print("="*70 + "\n")
    
    return passed, failed

if __name__ == '__main__':
    passed, failed = run_auth_tests()
    exit(0 if failed == 0 else 1)
