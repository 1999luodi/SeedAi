# SeedAI 后端快速启动指南

## 环境要求

- Docker & Docker Compose
- Python 3.9+
- MySQL 8.0 (如果不用Docker)

## 快速启动

### 使用Docker Compose (推荐)

```bash
# 进入项目根目录
cd d:\ai-projects\SeedAi

# 设置镜像版本号（全部服务统一使用）
# PowerShell:
$env:SEEDAI_IMAGE_TAG="202603101436"

# 拉取已发布镜像
docker compose pull

# 启动基础服务（前端+后端+推理+数据库）
docker compose up -d mysql backend ai_worker frontend

# 如需训练容器（GPU）
docker compose --profile train up -d ai_trainer
```

说明：`docker-compose.yml` 已使用 `SEEDAI_IMAGE_TAG` 变量管理镜像版本。
后续发布新镜像时，只需要更新这个版本号并重新 `pull + up -d`。

访问 `http://localhost` 即可看到登录页面。

## 项目使用方法（前台/后台）

### 前台使用（数据与标注/检测）

1. 打开前台登录页：`http://localhost/login`
2. 使用普通用户登录：`user1 / 123456`
3. 进入前台页面后，常用入口：
  - 数据集列表：`http://localhost/dataset.html`
  - 标注页面：`http://localhost/annotate.html`
  - 检测页面：`http://localhost/detection.html`
4. 检测流程：
  - 选择数据集和图片
  - 点击检测按钮发起推理
  - 查看检测框、类别和置信度结果

### 后台使用（管理用户与数据）

1. 打开后台入口：`http://localhost/admin`
2. 使用管理员或超级管理员登录：
  - 超级管理员：`admin / 123456`
3. 常用后台页面：
  - 用户管理：`http://localhost/admin/users`
  - 数据集管理：`http://localhost/admin/datasets`
  - 图片管理：`http://localhost/admin/images`
  - 统计页面：`http://localhost/admin/stats`
4. 常见管理操作：
  - 新增/禁用用户
  - 管理数据集可见性
  - 查看与维护图片数据

### 训练容器使用（可选）

1. 启动训练容器：`docker compose --profile train up -d ai_trainer`
2. 进入训练容器：`docker compose --profile train exec ai_trainer bash`
3. 在容器内执行训练脚本或导出脚本（按 `pytorch_model/offline/training` 目录组织）。

### 手动启动

```bash
# 进入后端目录
cd d:\ai-projects\SeedAi/backend

# 安装依赖
pip install -r requirements.txt

# 初始化数据库
python init_system.py

# 启动应用
python app.py
```

访问 `http://localhost:5000` 即可看到登录页面。

## 默认账户

- **超级管理员**: 
  - 用户名: `admin`
  - 密码: `123456`
  - 权限: 可访问管理后台，管理所有用户和数据

- **普通用户**:
  - 用户名: `user1`
  - 密码: `123456`
  - 权限: 基本功能权限

## 功能导航

- **登录页面**: `http://localhost/` 或 `http://localhost/login`
- **管理后台**: `http://localhost/admin` (需要管理员或超级管理员权限)
- **用户管理**: `http://localhost/admin/users`
- **数据集管理**: `http://localhost/admin/datasets`
- **图片管理**: `http://localhost/admin/images`
- **统计信息**: `http://localhost/admin/stats`

## API测试

- **API测试工具**: `http://localhost/tests/api-test.html`

## 常见问题

### 1. 数据库连接失败
检查 `.env` 文件中的数据库配置，或确保 MySQL 服务已启动。

### 2. 无法访问管理后台
确认登录账户的角色为管理员(1)或超级管理员(2)。

### 3. 文件上传失败
检查 `uploads` 目录权限，确保有足够的磁盘空间。

### 4. 登录失败
确认用户名和密码是否正确，初始账户为：
- admin / 123456 (超级管理员)
- user1 / 123456 (普通用户)

## 服务管理

```bash
# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs backend

# 重启服务
docker-compose restart

# 停止服务
docker-compose down
```

## 开发说明

### 添加新功能
1. 在 `services/` 目录中创建新的服务模块
2. 在 `app.py` 中添加相应路由
3. 如需要新模型，在 `models.py` 中定义
4. 更新 `api_endpoints.json` 中的API定义
5. 如需要管理界面，在 `templates/admin/` 中添加新模板

### 权限控制
- 使用 `@token_required` 装饰器保护需要认证的路由
- 检查用户角色以控制访问权限
- 超级管理员角色值为2，管理员为1，普通用户为0