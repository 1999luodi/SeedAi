# SeedAI 后端项目结构详解

## 项目概览

SeedAI 是一个基于AI的图像标注与数据集管理平台，后端采用Flask框架，提供完整的用户管理、数据集管理和图像标注功能。

## 目录结构

```
backend/
├── app.py                    # Flask主应用入口，包含所有路由定义
├── config.py                 # 配置管理，包含数据库、JWT、安全等配置
├── models.py                 # ORM模型定义，包含User、Dataset、Image、Annotation模型
├── utils.py                  # 工具函数，包含JWT生成、文件保存、响应格式化等
├── requirements.txt          # Python依赖包列表
├── init_system.py            # 系统初始化脚本
├── db_init.py                # 数据库初始化脚本
├── STRUCTURE.md              # 本项目结构文档
├── README.md                 # 项目使用说明
├── api_endpoints.json        # API端点定义文件
├── login.html                # 登录页面模板
├── admin_test.html           # 管理后台测试页面
├── templates/                # Jinja2模板目录
│   ├── login.html            # 登录页面模板
│   └── admin/                # 管理后台模板目录
│       ├── base.html         # 管理后台基础布局模板
│       ├── dashboard.html    # 管理后台仪表板页面
│       ├── users.html        # 用户管理页面
│       ├── datasets.html     # 数据集管理页面
│       ├── images.html       # 图片管理页面
│       └── stats.html        # 统计信息页面
└── services/                 # 业务逻辑层目录
    ├── user_service.py       # 用户服务，包含用户注册、认证、管理等逻辑
    ├── dataset_service.py    # 数据集服务，包含数据集创建、管理等逻辑
    └── image_service.py      # 图片服务，包含图片上传、标注管理等逻辑
```

## 核心模块说明

### 1. app.py - Flask主应用

这是整个后端应用的核心，包含：
- 所有路由定义
- 中间件配置
- 错误处理
- API端点实现

### 2. models.py - 数据模型

定义了四个核心数据模型：
- **User**: 用户模型，包含用户名、邮箱、密码哈希、角色等级等信息
- **Dataset**: 数据集模型，包含数据集名称、描述、创建者等信息
- **Image**: 图片模型，包含图片文件信息、所属数据集、标注信息等
- **Annotation**: 标注模型，包含边界框坐标、标签、置信度等信息

### 3. services/ - 业务逻辑层

封装了业务逻辑，实现控制器与数据操作的解耦：
- **user_service.py**: 用户相关操作，如注册、登录、权限管理等
- **dataset_service.py**: 数据集相关操作，如创建、查询、删除等
- **image_service.py**: 图片相关操作，如上传、标注管理等

### 4. utils.py - 工具函数

提供常用的工具函数：
- JWT令牌生成与验证
- 文件上传处理
- 标准化响应格式
- 密码加密等

### 5. templates/ - 前端模板

包含管理后台的HTML模板：
- 使用Jinja2模板引擎
- 响应式设计
- 统一的样式和布局

## API端点概览

### 认证相关
- `POST /api/auth/login` - 用户登录
- `POST /api/auth/register` - 用户注册
- `GET /api/users/profile` - 获取用户资料

### 数据集相关
- `POST /api/datasets` - 创建数据集
- `GET /api/datasets` - 获取数据集列表
- `GET /api/datasets/<id>` - 获取数据集详情
- `PUT /api/datasets/<id>` - 更新数据集
- `DELETE /api/datasets/<id>` - 删除数据集

### 图片相关
- `POST /api/datasets/<id>/upload` - 上传图片到数据集
- `GET /api/images/<id>` - 获取图片信息
- `PUT /api/images/<id>/annotations` - 更新图片标注

### 管理员相关
- `GET /admin` - 管理后台仪表板
- `GET /admin/users` - 用户管理页面
- `GET /admin/datasets` - 数据集管理页面
- `GET /admin/images` - 图片管理页面
- `GET /admin/stats` - 统计信息页面

## 权限系统

系统实现了三级权限管理：
- **0 - 普通用户**: 基本功能权限
- **1 - 管理员**: 可管理其他用户信息
- **2 - 超级管理员**: 最高权限，可访问管理后台

## 安全措施

- 密码使用bcrypt加密存储
- JWT令牌无状态认证
- 参数化查询防止SQL注入
- 文件上传类型和大小限制
- CORS策略控制

## 部署配置

- 支持Docker和Docker Compose部署
- Nginx反向代理配置
- 环境变量配置管理
- 数据持久化支持