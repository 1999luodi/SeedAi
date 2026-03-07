"""
SeedAI 测试工具 - 自定义断言
"""

import json
import requests

def assert_api_success(response: requests.Response, expected_status: int = 200):
    """断言API请求成功"""
    assert response.status_code == expected_status, \
        f"期望状态码 {expected_status}，实际 {response.status_code}。响应: {response.text}"
    
    data = response.json()
    assert data.get('success') is True, \
        f"API返回失败。消息: {data.get('message')}"

def assert_user_registered(response: requests.Response, username: str):
    """断言用户已注册"""
    assert response.status_code == 201, f"注册失败: {response.status_code}"
    
    data = response.json()
    assert data.get('success') is True, "注册失败"
    assert data.get('data', {}).get('username') == username, "用户名不匹配"

def assert_user_logged_in(response: requests.Response):
    """断言用户已登录"""
    assert response.status_code == 200, f"登录失败: {response.status_code}"
    
    data = response.json()
    assert data.get('success') is True, "登录失败"
    assert data.get('data', {}).get('token') is not None, "未获得Token"

def assert_user_in_list(html_content: str, username: str):
    """断言用户在列表中"""
    assert username in html_content, f"用户 {username} 不在列表中"

def assert_page_loaded(response: requests.Response, expected_title: str):
    """断言页面已加载"""
    assert response.status_code == 200, f"页面加载失败: {response.status_code}"
    assert expected_title in response.text, f"页面不包含预期的标题: {expected_title}"

def assert_token_valid(token: str):
    """断言Token格式有效"""
    assert token is not None, "Token为空"
    assert isinstance(token, str), "Token必须是字符串"
    # JWT Token应该有三个部分用.分割
    parts = token.split('.')
    assert len(parts) == 3, f"无效的JWT Token格式: {token[:20]}..."
