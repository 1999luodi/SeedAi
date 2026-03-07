
# SeedAI - AI图像标注与数据集管理平台

SeedAI 是一个基于AI的图像标注与数据集管理平台，支持用户上传图片、创建数据集、进行可视化标注，并通过AI模型（如YOLOv5）辅助目标检测任务。系统结合前后端分离架构与Docker部署，适用于机器学习数据准备场景。

## 项目架构

```
d:\ai-projects\SeedAi\
├── docker-compose.yml        # Docker服务编排
├── nginx.conf                # Nginx配置（端口代理、静态资源）
├── mysql_data\               # MySQL持久化数据
├── uploads\                  # 用户上传图片存储
├── datasets\                 # 原始数据集存储
├── backend\                  # Flask后端
│   ├── app.py                # 主应用入口
│   ├── config.py             # 配置管理
│   ├── models.py             # ORM模型定义
│   ├── services\             # 业务逻辑层
│   │   ├── user_service.py
│   │   ├── dataset_service.py
│   │   └── image_service.py
│   ├── templates\            # Flask模板
│   │   └── login.html
│   ├── utils.py              # 工具函数
│   └── requirements.txt      # Python依赖
├── frontend\                 # 前端页面
│   ├── index.html
│   ├── login.html
│   ├── dataset.html
│   ├── annotate.html
│   ├── style.css
│   └── js\
│       ├── main.js
│       ├── login.js
│       ├── dataset.js
│       └── annotate.js
├── tests\                    # 测试相关
│   └── api-test.html         # API测试页面
└── pytorch_model\            # AI模型模块
    ├── model.py
    ├── utils.py
    ├── weights\
    │   └── yolov5s.pt         # YOLOv5s预训练权重
    └── inference.py           # 推理逻辑
```

## 功能特性

- 用户注册/登录与JWT认证
- 数据集创建与管理
- 图片上传与存储（支持拖拽）
- 图像标注工具（前端可视化）
- 标注数据持久化到数据库
- AI模型推理支持（目标检测）
- 完整的RBAC基础架构（基于JWT）

## 系统入口

- **前端系统入口**：`http://localhost/login`
- **后端管理系统入口**：`http://localhost/backend/login`
- **API测试页面**：`http://localhost/tests/api-test.html`

## 默认账户

- **超级管理员**：admin / 123456（角色为2）
- **普通用户**：user1 / 123456（角色为0）

## 权限管理

- 超级管理员 (role=2)：可访问所有管理功能，可修改所有用户数据
- 普通管理员 (role=1)：仅可访问基础管理页面，仅可查看数据，无修改权限
- 普通用户 (role=0)：仅拥有基本功能权限

## 技术栈

- 前端：HTML5 / CSS3 / Vanilla JavaScript (ES6+)
- 后端：Python Flask 2.3.2
- 数据库：MySQL 8.0
- AI模型：PyTorch YOLOv5
- 部署：Docker + Docker Compose + Nginx

## 容器化部署

使用Docker容器部署，数据持久化通过Docker卷实现：

- MySQL数据持久化至 `./mysql_data/data`
- 用户上传文件存储于 `./uploads`
- 数据集文件存储于 `./datasets`

**注意：** 容器重启不会丢失数据，因为数据已通过Docker卷映射到宿主机目录。但应用配置和安装的软件包会保留，除非重建镜像。

## 快速开始

1. 克隆仓库并进入项目目录
2. 确保已安装Docker和Docker Compose
3. 运行以下命令启动服务：
   ```bash
   docker-compose up -d --build
   ```
4. 等待服务启动完成（大约需要几分钟）
5. 访问 `http://localhost` 进入前端系统
6. 访问 `http://localhost/backend/login` 进入后端管理系统

## API接口

所有API接口定义都从后端的[api_endpoints.json](file://d:\ai-projects\SeedAi\backend\api_endpoints.json)文件动态加载，便于API测试页面和其他工具使用。

```
graph LR
    A[前端] -->|上传图片| B(后端)
    B -->|保存图片| C[uploads]
    B -->|触发AI| D[AI 工作者]
    D -->|返回结果| B
    B -->|保存结果| E[数据库]
    A -->|获取结果| B
```

## 架构设计原则

### 数据库与后端分离
- **数据库初始化**：在 [mysql_data/](file:///d:/ai-projects/SeedAi/mysql_data) 目录下独立管理
- **后端服务**：仅负责数据库连接和业务逻辑，不包含数据库初始化代码
- **职责分离**：数据库容器独立管理数据，后端容器仅处理业务逻辑

### 技术栈

#### 后端
- **框架**: Flask 2.3.2 + Flask-SQLAlchemy 3.1.1
- **数据库**: MySQL 8.0 + PyMySQL 1.1.0
- **认证**: JWT (PyJWT 2.8.0) + bcrypt 4.0.1
- **ORM**: SQLAlchemy 2.0.23
- **其他**: Flask-CORS, cryptography, python-dotenv

#### 前端
- **HTML5**: 语义化结构和响应式设计
- **CSS3**: 现代化样式和动画效果
- **Vanilla JavaScript**: 原生ES6+，无框架依赖
- **Fetch API**: 现代HTTP请求处理
- **LocalStorage**: 客户端数据存储
- **Canvas API**: 检测框和标注框的绘制
- **Nginx**: 静态文件服务和API代理

#### AI推理
- **框架**: PyTorch
- **模型**: YOLOv5s (目标检测)
- **推理方式**: 实时推理与批处理

## 部署说明

### 1. 环境要求
- Docker & Docker Compose
- VS Code (推荐插件: Docker, Python)

### 2. 初始化数据库
```bash
# 启动MySQL服务
docker-compose up -d mysql

# 运行数据库初始化脚本
docker exec -w /app seedai-backend-1 python /app/init_database.py
```

### 3. 启动所有服务
```bash
# 构建并启动所有服务
docker-compose up -d --build

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs backend
```

### 4. 服务端口
- 前端: http://localhost:80
- 后端: http://localhost:5000
- MySQL: localhost:3306

### 5. 停止服务
```bash
docker-compose down
```

## 默认凭据

- **超级管理员**: admin / 123456 (角色: 2)
- **普通用户**: user1 / 123456 (角色: 0)

## 访问路径

- 首页: `http://localhost/`
- 登录页: `http://localhost/login`
- 管理后台: `http://localhost/admin`
- 统一测试页面: `http://localhost/tests/api-test.html`

## 安全特性

- **密码加密**: 使用bcrypt进行密码哈希
- **JWT认证**: 无状态令牌认证
- **CORS支持**: 跨域资源共享
- **文件验证**: 上传文件类型和大小限制
- **SQL注入防护**: 使用ORM参数化查询

## 测试

项目包含完整的测试体系：

- API测试: `http://localhost/tests/api-test.html`
- 单元测试: 位于 `tests/` 目录
- 集成测试: 位于 `tests/` 目录

运行API测试：
```bash
python tests/api_test.py
```

