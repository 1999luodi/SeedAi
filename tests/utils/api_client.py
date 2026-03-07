"""
SeedAI 测试工具 - API客户端
提供便捷的API请求封装
"""

import requests
import json
from typing import Dict, Optional, Any

class APIClient:
    """SeedAI API客户端"""
    
    def __init__(self, base_url: str = 'http://localhost:5000'):
        self.base_url = base_url
        self.token = None
        self.headers = {'Content-Type': 'application/json'}
    
    def _request(self, method: str, endpoint: str, data: Optional[Dict] = None,
                 timeout: int = 5) -> requests.Response:
        """发送HTTP请求"""
        url = f"{self.base_url}{endpoint}"
        headers = self.headers.copy()
        
        if self.token:
            headers['Authorization'] = f'Bearer {self.token}'
        
        try:
            if method.upper() == 'GET':
                return requests.get(url, headers=headers, timeout=timeout)
            elif method.upper() == 'POST':
                return requests.post(url, json=data, headers=headers, timeout=timeout)
            elif method.upper() == 'PUT':
                return requests.put(url, json=data, headers=headers, timeout=timeout)
            elif method.upper() == 'DELETE':
                return requests.delete(url, headers=headers, timeout=timeout)
        except requests.exceptions.Timeout:
            raise Exception(f"请求超时: {url}")
        except Exception as e:
            raise Exception(f"请求异常: {e}")
    
    def register(self, username: str, email: str, password: str) -> Dict[str, Any]:
        """用户注册"""
        response = self._request('POST', '/api/auth/register', {
            'username': username,
            'email': email,
            'password': password
        })
        
        if response.status_code == 201:
            return response.json()
        else:
            raise Exception(f"注册失败: {response.status_code} - {response.json()}")
    
    def login(self, username_or_email: str, password: str) -> Dict[str, Any]:
        """用户登录"""
        response = self._request('POST', '/api/auth/login', {
            'username_or_email': username_or_email,
            'password': password
        })
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                self.token = data.get('data', {}).get('token')
            return data
        else:
            raise Exception(f"登录失败: {response.status_code} - {response.json()}")
    
    def get_health(self) -> Dict[str, Any]:
        """获取后端健康状态"""
        response = self._request('GET', '/health')
        return response.json()
    
    def get_users_admin(self) -> requests.Response:
        """获取用户列表（管理后台）"""
        return self._request('GET', '/admin/users')
    
    def get_admin_dashboard(self) -> requests.Response:
        """获取管理仪表板"""
        return self._request('GET', '/admin')
    
    def toggle_user_status(self, user_id: int) -> Dict[str, Any]:
        """切换用户状态"""
        response = self._request('POST', f'/api/admin/users/{user_id}/toggle-status')
        return response.json()
    
    def get_profile(self) -> Dict[str, Any]:
        """获取当前用户信息"""
        response = self._request('GET', '/api/users/profile')
        return response.json()
    
    def clear_token(self):
        """清除Token"""
        self.token = None
