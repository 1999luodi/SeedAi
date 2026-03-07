"""
SeedAI 测试配置和全局设置
"""

import os
import sys

# 设置Python路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
sys.path.insert(0, project_root)

# 设置默认的基础URL
DEFAULT_BASE_URL = 'http://localhost:5000'

# 设置测试超时
DEFAULT_TIMEOUT = 10

# 日志配置
TEST_LOG_FORMAT = '[%(asctime)s] %(levelname)s: %(message)s'
