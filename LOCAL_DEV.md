# SeedAI 本地开发指南

## 前提条件

1. 安装 Python 3.9+
2. 安装 MySQL 8.0
3. 安装必要的 Python 依赖

## 安装依赖

```bash
cd backend
pip install -r requirements.txt
pip install mysql-connector-python
```

## 数据库设置

1. 启动 MySQL 服务
2. 创建数据库 `ai_dataset`:
   ```sql
   CREATE DATABASE ai_dataset CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
   ```
3. 确保 root 用户密码为 `rootpass`，或修改配置文件中的密码

## 启动后端服务

```bash
cd backend
python dev_run.py
```

这将启动 Flask 应用在 `http://localhost:5000`

## 访问前端

直接在浏览器中打开 `frontend/login.html` 或通过以下方式:

1. 使用 VS Code Live Server 扩展打开 `frontend/index.html`
2. 或者使用 Python 内置服务器:
   ```bash
   cd frontend
   python -m http.server 8080
   ```
   然后访问 `http://localhost:8080/login.html`

## 测试注册功能

1. 访问登录页面
2. 点击"立即注册"
3. 填写注册表单
4. 提交表单

如果一切正常，您应该看到"注册成功！请登录"的消息。

## 故障排除

### 数据库连接问题

如果遇到数据库连接问题，请检查:

1. MySQL 服务是否正在运行
2. 数据库名称是否为 `ai_dataset`
3. 用户名和密码是否正确 (默认: root/rootpass)

### API 请求失败

如果前端无法连接到后端API，请确保:

1. 后端服务正在运行 (`http://localhost:5000`)
2. 前端页面是通过 HTTP 服务器访问的，而不是直接打开 HTML 文件
3. 检查浏览器开发者工具中的网络请求，查看具体错误

### CORS 错误

如果遇到 CORS 错误，请确保后端已正确配置 CORS:

```python
from flask_cors import CORS
CORS(app)
```

这已经在代码中配置好了。