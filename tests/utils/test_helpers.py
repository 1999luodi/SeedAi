"""
SeedAI 测试工具 - 通用辅助函数
"""

import time
from datetime import datetime

def log_test(test_name: str, status: bool, message: str = ""):
    """记录测试结果"""
    emoji = "✅" if status else "❌"
    timestamp = datetime.now().strftime('%H:%M:%S')
    print(f"[{timestamp}] {emoji} {test_name}: {message}")

def wait_for_condition(condition_func, max_retries: int = 10, delay: float = 0.5):
    """等待条件满足"""
    for attempt in range(max_retries):
        try:
            if condition_func():
                return True
        except Exception:
            pass
        
        if attempt < max_retries - 1:
            time.sleep(delay)
    
    return False

def generate_unique_username(prefix: str = "testuser") -> str:
    """生成唯一的用户名"""
    timestamp = int(time.time() * 1000)
    return f"{prefix}_{timestamp}"

def generate_unique_email(prefix: str = "test") -> str:
    """生成唯一的邮箱"""
    timestamp = int(time.time() * 1000)
    return f"{prefix}_{timestamp}@example.com"

def print_section(title: str, width: int = 70):
    """打印分隔线和标题"""
    print("\n" + "=" * width)
    print(f"  {title}")
    print("=" * width)

def print_subsection(title: str):
    """打印子标题"""
    print(f"\n📌 {title}")
    print("-" * 50)

def format_response(response_data: dict) -> str:
    """格式化API响应"""
    import json
    return json.dumps(response_data, indent=2, ensure_ascii=False)
