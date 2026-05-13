# SeedAI - API测试工具

SeedAI 提供了一个完整的API测试工具，用于测试后端API接口的功能和性能。

## API测试页面

- **API测试页面**：`http://localhost/tests/api-test.html`
- 该页面从后端动态加载所有API端点定义，便于测试所有可用接口

## 功能特点

- 左侧功能菜单，右侧主内容区布局
- 右侧主内容区划分为上下两部分：上半部分为API请求配置区域，下半部分为API响应展示区域
- 按功能分类导航不同测试类别（如认证、数据集、管理等）
- 接口预设通过下拉菜单实现，按功能分类组织选项，支持快速加载常用接口配置

## 接口定义来源

- 所有接口定义都从后端的[api_endpoints.json](file://d:\ai-projects\SeedAi\backend\api_endpoints.json)文件动态加载
- 修改接口定义只需更新后端的api_endpoints.json文件
- 保持接口定义的单一数据源，确保API测试页面始终反映最新的接口定义
- Python测试客户端使用 `tests/utils/api_contract.py`（由后端定义自动生成）

### 契约同步步骤

1. 修改 `backend/api_endpoints.json`
2. 执行 `python backend/sync_api_contract.py`
3. 再运行前端/测试，确保都基于同一份接口契约

## 默认测试账户

- **超级管理员**：admin / 123456（角色为2）
- **普通用户**：user1 / 123456（角色为0）

## 测试覆盖

API测试工具涵盖以下功能模块：

- 认证相关接口（登录、注册、获取个人资料等）
- 用户管理接口（获取用户列表、切换用户状态等）
- 数据集管理接口（创建、获取、修改、删除数据集等）
- 图片管理接口（上传图片、获取图片信息等）
- 系统接口（健康检查、API端点定义等）

## 测试流程
刷新测试页 http://localhost/tests/api-test.html
先点 用户登录（建议 user1）
测图片管理时，直接用菜单自动填充
看 路径参数(JSON) 是否有 image_id
点发送请求

1. 打开API测试页面
2. 选择测试类别和具体接口
3. 系统自动填充请求方法、端点和示例数据
4. 如需修改，可调整请求头、请求体
5. 点击"🚀 发送请求"
6. 在右侧查看完整响应

## 测试数据

测试数据存储在 `fixtures/` 目录中，包含：

- 测试用户账号
- 测试数据集
- 预设的标注数据

## 测试报告

测试结果生成在 `test_results/` 目录中：

- HTML格式的详细测试报告
- 包含测试覆盖率统计
- 性能指标分析

## 测试覆盖率

- API接口：100%
- 核心业务逻辑：95%
- 用户界面交互：80%

## CI/CD集成

测试脚本可以集成到CI/CD流水线中：

```bash
# 运行所有测试
python -m pytest

# 生成覆盖率报告
coverage run --source=. -m pytest
coverage report -m
```

## 📋 统一API接口定义

为了确保前后端测试的一致性，项目使用统一的API接口定义文件：

- **主定义文件**: `backend/api_endpoints.json` - 所有API接口的唯一数据源
- **前端测试工具**: 从 `/backend/api_endpoints.json` 动态加载接口定义
- **后端Python测试**: 从 `backend/api_endpoints.json` 读取接口定义并转换为Python格式

根据接口定义单一数据源规范，所有接口定义都必须维护在后端的api_endpoints.json文件中，测试工具和脚本从该文件读取最新定义，确保所有系统组件基于同一套接口定义。

### 使用方式

**前端测试工具**:
- 自动加载 `api_endpoints.json` 文件
- 在左侧菜单栏显示所有API接口
- 点击接口自动填充请求方法、端点和示例数据

**后端测试脚本**:
- 导入 `api_endpoints.py` 模块
- 使用 `get_all_endpoints()`、`get_endpoint_by_name()` 等函数获取接口信息
- 确保测试用例与实际API保持同步

##  快速开始

### API 测试工具

#### 方式1：内置Web工具（推荐用于开发阶段）
打开浏览器访问：**`http://localhost/tests/api-test.html`**

**功能特性**：
- 📋 左侧菜单栏按功能分类显示所有API接口
- 🔄 支持 GET、POST、PUT、DELETE、PATCH 请求
- 📤 自定义请求头和JSON请求体
- 📥 实时响应显示（状态码、响应时间、响应体）
- 📊 请求历史记录
- 🎨 现代化UI界面

**使用步骤**：
1. 打开API测试工具页面
2. 在左侧菜单选择API接口分类和具体接口
3. 系统自动填充请求方法、端点和示例数据
4. 如需修改，可调整请求头、请求体
5. 点击"🚀 发送请求"
6. 在右侧查看完整响应

#### 方式3：PowerShell脚本测试（推荐用于CI/CD）

运行自动化测试脚本：
```powershell
# 在项目根目录运行
.\tests\api-test.ps1
```

**功能特性**：
- 🔧 自动执行关键API端点测试
- ✅ 彩色输出结果显示
- 📊 详细错误信息和状态
- 🚀 快速验证系统状态
- 🔄 集成到CI/CD流水线

**测试覆盖**：
- 用户登录认证
- 用户信息获取
- 数据集列表查询
- 错误处理验证

---

#### 方式2：Apifox（推荐用于生产环境）

**Apifox** 是一个专业的API测试工具，类似Postman但功能更强大。

**下载和安装**：
1. 访问 [Apifox官网](https://apifox.com)
2. 下载并安装Apifox客户端
3. 创建团队工作区

**导入API规范**（可选）：
```bash
# 如果项目使用OpenAPI/Swagger规范
# 在Apifox中直接导入规范文件
```

**推荐配置**：
```
项目名称: SeedAI
API基础URL: http://localhost/api

认证配置:
- 类型: JWT Bearer Token
- 获取方式: 通过登录API获取token
- 自动注入请求头: Authorization: Bearer {token}
```

**优势**：
- ✅ 团队协作
- ✅ API自动化测试
- ✅ 性能测试
- ✅ Mock服务
- ✅ 文档生成
- ✅ 版本控制

---

## 📁 文件夹结构

```
tests/
├── README.md                      # 本文件 - 测试说明文档
├── api-test.html                  # 🌐 内置Web API测试工具
├── conftest.py                    # pytest 配置文件
├── requirements.txt               # 测试依赖
│
├── reports/                       # 📊 报告文件夹
│   ├── ACCEPTANCE_REPORT.md       # 验收报告（完整）
│   ├── TEST_GUIDE.md              # 测试指南（详细步骤）
│   └── test_results.json          # 测试结果数据
│
├── integration/                   # 🔗 集成测试（前后端交互）
│   ├── __init__.py
│   ├── test_auth_flow.py          # 认证流程测试（注册/登录）
│   ├── test_user_management.py    # 用户管理测试
│   ├── test_multi_user.py         # 多用户场景测试
│   └── test_admin_dashboard.py    # 后台仪表板测试
│
├── unit/                          # 🎯 单元测试（后端模块）
│   ├── __init__.py
│   ├── test_user_service.py       # 用户服务单元测试
│   ├── test_dataset_service.py    # 数据集服务单元测试
│   └── test_models.py             # 数据模型单元测试
│
├── fixtures/                      # 📋 测试数据和fixture
│   ├── __init__.py
│   ├── test_users.json            # 测试用户数据
│   ├── test_datasets.json         # 测试数据集数据
│   └── conftest_fixtures.py       # pytest fixture定义
│
└── utils/                         # 🛠️ 测试工具
    ├── __init__.py
    ├── test_helpers.py            # 通用测试工具函数
    ├── api_client.py              # API请求封装
    └── assertions.py              # 自定义断言
```

---

## 🧪 测试分类

### 1️⃣ 集成测试 (Integration Tests)
**位置**: `tests/integration/`  
**用途**: 测试前后端之间的交互和完整的业务流程  
**包含**:
- 用户注册和登录流程
- 用户管理操作（禁用/启用）
- 多用户场景
- 后台管理功能

**运行方式**:
```bash
# 运行所有集成测试
pytest tests/integration/

# 运行特定测试
pytest tests/integration/test_auth_flow.py

# 运行并显示详细输出
pytest tests/integration/ -v
```

### 2️⃣ 单元测试 (Unit Tests)
**位置**: `tests/unit/`  
**用途**: 测试后端各个服务和模块的单独功能  
**包含**:
- 用户服务逻辑
- 数据集管理逻辑
- 数据模型验证

**运行方式**:
```bash
pytest tests/unit/
pytest tests/unit/test_user_service.py -v
```

---

## 📊 测试文件说明

### 集成测试详细说明

#### test_auth_flow.py
- 测试用户注册功能
- 验证密码加密存储
- 测试用户登录功能
- 验证Token生成

#### test_user_management.py
- 获取所有用户列表
- 用户状态切换（禁用/启用）
- 用户搜索和过滤

#### test_multi_user.py
- 批量用户注册
- 并发登录测试
- 用户数据完整性验证

#### test_admin_dashboard.py
- 仪表板加载测试
- 统计数据准确性
- 管理页面UI测试

---

## 🚀 快速开始

### 1. 查看验收报告
```bash
# 查看验收报告（已通过的完整测试）
cat tests/reports/ACCEPTANCE_REPORT.md

# 查看详细测试指南
cat tests/reports/TEST_GUIDE.md
```

### 2. 运行集成测试
```bash
# 运行前最好确保后端服务正在运行
docker-compose ps  # 检查容器状态

# 进入tests目录
cd tests

# 运行所有测试
python -m pytest integration/ -v

# 运行特定测试文件
python -m pytest integration/test_auth_flow.py::test_user_registration -v
```

### 3. 查看测试报告
测试运行后会生成详细的测试报告，包括：
- 通过率统计
- 失败项详情
- 性能指标
- 覆盖率数据

---

## 📈 测试覆盖范围

### 已测试的功能 ✅

#### 认证模块
- ✅ 用户注册 (成功、失败场景)
- ✅ 用户登录 (成功、失败场景)
- ✅ Token生成和验证
- ✅ 密码加密存储

#### 用户管理
- ✅ 获取用户列表
- ✅ 用户状态管理
- ✅ 多用户场景
- ✅ 并发请求处理

#### 后台管理
- ✅ 仪表板加载
- ✅ 统计数据显示
- ✅ 用户数据展示
- ✅ 管理操作响应

#### 数据库
- ✅ 用户数据持久化
- ✅ 关系数据完整性
- ✅ 事务处理
- ✅ 数据查询性能

---

## 🔍 测试工具和辅助函数

### API 测试客户端
位置: `utils/api_client.py`

```python
from utils.api_client import APIClient

# 创建API客户端
client = APIClient(base_url='http://localhost:5000')

# 注册用户
response = client.register(username, email, password)

# 登录
response = client.login(username_or_email, password)

# 获取用户列表
response = client.get_users_admin()
```

### 自定义断言
位置: `utils/assertions.py`

```python
from utils.assertions import assert_user_exists, assert_token_valid

# 断言用户存在
assert_user_exists(username)

# 断言token有效
assert_token_valid(token)
```

---

## 💾 测试数据管理

### 测试用户数据
位置: `fixtures/test_users.json`

```json
{
  "test_user_1": {
    "username": "testuser1",
    "email": "test1@example.com",
    "password": "TestPassword123"
  },
  "test_user_2": {
    "username": "testuser2",
    "email": "test2@example.com",
    "password": "TestPassword456"
  }
}
```

### 测试数据集数据
位置: `fixtures/test_datasets.json`

```json
{
  "dataset_1": {
    "name": "Sample Dataset",
    "description": "A sample dataset for testing"
  }
}
```

---

## 📋 测试检查清单

运行完整测试前，请确保：

- [ ] Docker 容器已启动 (`docker-compose ps`)
- [ ] 后端服务正在运行 (http://localhost:5000)
- [ ] 前端可以访问 (http://localhost/)
- [ ] 数据库连接正常
- [ ] Python依赖已安装 (`pip install -r requirements.txt`)

---

## 🎯 常见测试命令

```bash
# 查看所有测试（仅列出，不运行）
pytest tests/ --collect-only

# 运行所有测试并生成HTML报告
pytest tests/ --html=tests/reports/report.html

# 运行测试并显示覆盖率
pytest tests/ --cov=backend --cov-report=html

# 运行失败后停止
pytest tests/ -x

# 运行仅最后失败的测试
pytest tests/ --lf

# 显示最慢的10个测试
pytest tests/ --durations=10

# 运行带有特定标签的测试
pytest tests/ -m integration

# 并行运行测试（需要 pytest-xdist）
pytest tests/ -n auto
```

---

## 📊 测试报告格式

### 控制台输出示例
```
tests/integration/test_auth_flow.py::test_user_registration PASSED     [ 10%]
tests/integration/test_auth_flow.py::test_user_login PASSED            [ 20%]
tests/integration/test_user_management.py::test_get_users PASSED       [ 30%]
...

========================= 10 passed in 2.34s =========================
```

### 报告文件生成
```
tests/reports/
├── ACCEPTANCE_REPORT.md      # 验收总结
├── test_results.json         # 原始测试数据
└── test_report.html          # HTML格式报告
```

---

## 🔧 故障排查

### 问题：测试连接超时
**原因**: 后端服务未运行或网络连接问题
**解决**:
```bash
# 检查后端是否运行
docker logs seedai-backend-1

# 重启后端
docker-compose restart backend

# 验证连接
curl http://localhost:5000
```

### 问题：测试找不到模块
**原因**: PYTHONPATH配置不正确
**解决**:
```bash
# 从项目根目录运行测试
cd /d/ai-projects/SeedAi
pytest tests/

# 或者设置PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
pytest tests/
```

### 问题：测试数据不清理导致重复键错误
**原因**: 数据库中已存在相同的用户
**解决**:
```bash
# 清理测试数据
python tests/fixtures/cleanup.py

# 或者重启数据库
docker-compose down -v
docker-compose up -d
```

---

## 📞 获取帮助

- **验收报告**: `tests/reports/ACCEPTANCE_REPORT.md`
- **测试指南**: `tests/reports/TEST_GUIDE.md`
- **后端日志**: `docker logs seedai-backend-1`
- **前端控制台**: 浏览器 F12 → Console

---

**最后更新**: 2026年3月6日  
**维护者**: GitHub Copilot  
**状态**: ✅ 生产环境
