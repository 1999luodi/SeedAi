"""
SeedAI API测试脚本
用于测试后端API接口的功能和性能
"""

import requests
import json
import time
from datetime import datetime

BASE_URL = "http://localhost:5000"

def load_api_endpoints():
    """从后端加载API端点定义"""
    print("Loading API endpoints from backend...")
    try:
        response = requests.get(f"{BASE_URL}/backend/api_endpoints.json")
        if response.status_code == 200:
            endpoints_data = response.json()
            # 将端点数据转换为易于使用的字典格式
            endpoints_map = {}
            for category in endpoints_data.get("categories", []):
                for endpoint in category.get("endpoints", []):
                    name = endpoint["name"]
                    endpoints_map[name] = {
                        "method": endpoint["method"],
                        "endpoint": endpoint["endpoint"],
                        "example": endpoint.get("example", {})
                    }
            print("✓ API endpoints loaded successfully")
            return endpoints_map
        else:
            print(f"✗ Failed to load API endpoints: {response.status_code}")
            return {}
    except Exception as e:
        print(f"✗ Error loading API endpoints: {str(e)}")
        return {}

# 加载API端点定义
API_ENDPOINTS = load_api_endpoints()

def test_api_login(username, password):
    """测试登录API"""
    print("Testing login API...")
    endpoint_info = API_ENDPOINTS.get("用户登录") or API_ENDPOINTS.get("Backend Admin Login")
    if not endpoint_info:
        # 如果无法从API定义加载，则使用默认值
        endpoint_info = {"method": "POST", "endpoint": "/api/auth/login"}
    
    url = f"{BASE_URL}{endpoint_info['endpoint']}"
    response = requests.post(url, json={
        "username_or_email": username,
        "password": password
    })
    
    if response.status_code == 200:
        data = response.json()
        if data.get("success"):
            print("✓ Login successful")
            return data["data"]["token"]
        else:
            print(f"✗ Login failed: {data.get('message')}")
            return None
    else:
        print(f"✗ Login request failed: {response.status_code}")
        return None

def test_backend_login(username, password):
    """测试后端管理员登录API"""
    print("Testing backend admin login API...")
    endpoint_info = API_ENDPOINTS.get("后端管理员登录")
    if not endpoint_info:
        # 如果无法从API定义加载，则使用默认值
        endpoint_info = {"method": "POST", "endpoint": "/backend/login"}
    
    url = f"{BASE_URL}{endpoint_info['endpoint']}"
    response = requests.post(url, json={
        "username_or_email": username,
        "password": password
    })
    
    if response.status_code == 200:
        data = response.json()
        if data.get("success"):
            print("✓ Backend admin login successful")
            return data["data"]["token"]
        else:
            print(f"✗ Backend admin login failed: {data.get('message')}")
            return None
    else:
        print(f"✗ Backend admin login request failed: {response.status_code}")
        return None

def test_get_user_profile(token):
    """测试获取用户信息API"""
    print("Testing get user profile API...")
    endpoint_info = API_ENDPOINTS.get("获取个人资料")
    if not endpoint_info:
        # 如果无法从API定义加载，则使用默认值
        endpoint_info = {"method": "GET", "endpoint": "/api/users/profile"}
    
    headers = {"Authorization": f"Bearer {token}"}
    url = f"{BASE_URL}{endpoint_info['endpoint']}"
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        if data.get("success"):
            print("✓ Get user profile successful")
            print(f"  User: {data['data']['username']} (Role: {data['data']['role']})")
            return True
        else:
            print(f"✗ Get user profile failed: {data.get('message')}")
            return False
    else:
        print(f"✗ Get user profile request failed: {response.status_code}")
        return False

def test_create_dataset(token):
    """测试创建数据集API"""
    print("Testing create dataset API...")
    endpoint_info = API_ENDPOINTS.get("创建数据集")
    if not endpoint_info:
        # 如果无法从API定义加载，则使用默认值
        endpoint_info = {
            "method": "POST", 
            "endpoint": "/api/datasets",
            "example": {
                "name": "Test Dataset",
                "description": "A sample dataset for testing"
            }
        }
    
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    example_data = endpoint_info.get("example", {})
    payload = {
        "name": example_data.get("name", "Test Dataset API"),
        "description": example_data.get("description", f"Test dataset created at {datetime.now().isoformat()}"),
        "category": "detection"
    }
    
    url = f"{BASE_URL}{endpoint_info['endpoint']}"
    response = requests.post(url, headers=headers, json=payload)
    
    if response.status_code == 201:
        data = response.json()
        if data.get("success"):
            print(f"✓ Dataset created successfully with ID: {data['data']['id']}")
            return data["data"]["id"]
        else:
            print(f"✗ Dataset creation failed: {data.get('message')}")
            return None
    else:
        print(f"✗ Dataset creation request failed: {response.status_code}")
        return None

def test_get_datasets(token):
    """测试获取数据集列表API"""
    print("Testing get datasets API...")
    endpoint_info = API_ENDPOINTS.get("获取数据集列表")
    if not endpoint_info:
        # 如果无法从API定义加载，则使用默认值
        endpoint_info = {"method": "GET", "endpoint": "/api/datasets"}
    
    headers = {"Authorization": f"Bearer {token}"}
    url = f"{BASE_URL}{endpoint_info['endpoint']}"
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        if data.get("success"):
            print(f"✓ Get datasets successful, found {len(data['data'])} datasets")
            return data["data"]
        else:
            print(f"✗ Get datasets failed: {data.get('message')}")
            return None
    else:
        print(f"✗ Get datasets request failed: {response.status_code}")
        return None

def test_admin_access(token):
    """测试管理员访问权限"""
    print("Testing admin access...")
    # 由于admin访问可能是页面而不是API，我们使用用户管理接口来测试管理员权限
    endpoint_info = API_ENDPOINTS.get("获取用户列表")
    if not endpoint_info:
        # 如果无法从API定义加载，则使用默认值
        endpoint_info = {"method": "GET", "endpoint": "/api/admin/users"}
    
    headers = {"Authorization": f"Bearer {token}"}
    url = f"{BASE_URL}{endpoint_info['endpoint']}"
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        if data.get("success"):
            print("✓ Admin access successful")
            print(f"  Found {len(data['data'])} users")
            return True
        else:
            print(f"✗ Admin access failed: {data.get('message')}")
            return False
    elif response.status_code == 403:
        print("✗ Admin access denied (expected for non-admin users)")
        return False
    else:
        print(f"✗ Admin access failed: {response.status_code}")
        return False

def run_tests():
    """运行所有测试"""
    print("=" * 60)
    print("SeedAI API 测试开始")
    print("=" * 60)
    
    # 检查是否成功加载了API端点定义
    if not API_ENDPOINTS:
        print("⚠ 未能加载API端点定义，将使用默认值进行测试")
    
    # 测试1: 使用超级管理员登录
    print("\n【测试1: 超级管理员登录】")
    admin_token = test_api_login("admin", "123456")
    if not admin_token:
        print("✗ 超级管理员登录失败，终止测试")
        return
    
    # 测试2: 获取用户信息
    print("\n【测试2: 获取用户信息】")
    test_get_user_profile(admin_token)
    
    # 测试3: 创建数据集
    print("\n【测试3: 创建数据集】")
    dataset_id = test_create_dataset(admin_token)
    
    # 测试4: 获取数据集列表
    print("\n【测试4: 获取数据集列表】")
    test_get_datasets(admin_token)
    
    # 测试5: 管理员访问
    print("\n【测试5: 管理员访问权限】")
    test_admin_access(admin_token)
    
    # 测试6: 后端管理员登录
    print("\n【测试6: 后端管理员登录】")
    backend_token = test_backend_login("admin", "123456")
    if backend_token:
        print("✓ Backend admin login test passed")
    
    # 测试7: 普通用户登录
    print("\n【测试7: 普通用户登录】")
    user_token = test_api_login("user1", "123456")
    if user_token:
        test_get_user_profile(user_token)
        test_get_datasets(user_token)
        test_admin_access(user_token)
    
    print("\n" + "=" * 60)
    print("SeedAI API 测试完成")
    print("=" * 60)

if __name__ == "__main__":
    run_tests()