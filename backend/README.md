# SeedAI 后端管理系统

## 概述

SeedAI 后端管理系统是一个基于 Flask 的完整 Web 管理后台，为 AI 图像标注平台提供全面的管理功能。该系统完全独立于前端，提供了用户管理、数据集管理、图片管理、统计信息等核心管理功能。

## 架构特点

- **完全后端实现** - 不依赖前端文件，完全在后端提供管理界面
- **现代化设计** - 使用现代 Web 技术和响应式设计
- **RESTful API** - 提供完整的 API 接口供前端或其他系统调用
- **模块化设计** - 清晰的代码结构，易于维护和扩展
- **安全可靠** - 包含权限验证、错误处理和数据验证

## 技术栈

- **后端框架**: Flask 2.3+
- **数据库**: MySQL 8.0
- **ORM**: SQLAlchemy
- **模板引擎**: Jinja2
- **身份验证**: JWT (JSON Web Token)
- **容器化**: Docker & Docker Compose
- **前端技术**: 纯 HTML/CSS/JavaScript (管理后台)

## 目录结构

```
backend/
├── app.py                 # Flask 应用主文件
├── config.py             # 配置文件
├── models.py             # 数据库模型
├── utils.py              # 工具函数
├── requirements.txt      # Python 依赖
├── templates/            # Jinja2 模板
│   └── admin/           # 管理后台模板
│       ├── base.html    # 基础布局模板
│       ├── dashboard.html   # 仪表板
│       ├── users.html       # 用户管理
│       ├── datasets.html    # 数据集管理
│       ├── images.html      # 图片管理
│       └── stats.html       # 统计信息
├── services/            # 业务逻辑层
│   ├── user_service.py      # 用户服务
│   ├── dataset_service.py   # 数据集服务
│   └── image_service.py     # 图片服务
├── admin_test.html      # 管理后台测试页面
└── ADMIN_README.md      # 管理后台使用说明
```

## 管理后台功能

### 1. 仪表板 (`/admin`)
- 系统统计概览（用户数、数据集数、图片数等）
- 快速操作入口
- 系统状态监控
- 最近活动记录

### 2. 用户管理 (`/admin/users`)
- 查看所有注册用户
- 用户状态管理（启用/禁用）
- 用户数据集统计
- 用户注册时间等信息

### 3. 数据集管理 (`/admin/datasets`)
- 查看所有数据集
- 数据集公开状态切换
- 数据集图片数量统计
- 数据集创建时间和所有者信息

### 4. 图片管理 (`/admin/images`)
- 查看所有上传的图片
- 图片删除功能
- 图片元信息显示（文件名、大小、上传者等）
- 标注状态统计

### 5. 统计信息 (`/admin/stats`)
- 详细的系统使用统计
- 数据存储统计
- 使用情况分析
- 系统状态监控

## API 接口

### 管理 API

#### 用户管理
```http
POST /api/admin/users/{user_id}/toggle-status
```
切换用户状态（启用/禁用）

#### 数据集管理
```http
POST /api/admin/datasets/{dataset_id}/toggle-public
```
切换数据集公开状态

#### 图片管理
```http
DELETE /api/admin/images/{image_id}/delete
```
删除指定图片

### 数据 API

#### 用户 API
```http
GET  /api/auth/register          # 用户注册
POST /api/auth/login             # 用户登录
GET  /api/users/profile          # 获取用户资料
```

#### 数据集 API
```http
POST /api/datasets               # 创建数据集
GET  /api/datasets               # 获取用户数据集
GET  /api/datasets/{id}          # 获取指定数据集
GET  /api/datasets/{id}/images   # 获取数据集图片
POST /api/datasets/{id}/upload   # 上传图片到数据集
```

#### 图片 API
```http
GET  /api/images/{id}            # 获取图片信息
PUT  /api/images/{id}/annotations # 更新图片标注
```

#### 系统 API
```http
GET  /health                     # 健康检查
GET  /api/datasets/public        # 获取公开数据集
```

## 安装和运行

### 1. 环境要求
- Python 3.9+
- Docker & Docker Compose
- MySQL 8.0

### 2. 安装依赖
```bash
cd backend
pip install -r requirements.txt
```

### 3. 配置环境
编辑 `config.py` 文件，设置数据库连接等配置：
```python
class Config:
    SECRET_KEY = 'your-secret-key'
    SQLALCHEMY_DATABASE_URI = 'mysql://user:password@localhost/seedai'
    JWT_SECRET_KEY = 'your-jwt-secret'
    UPLOAD_FOLDER = '/app/uploads'
    DATASETS_FOLDER = '/app/datasets'
```

### 4. 运行应用
```bash
# 使用 Docker Compose（推荐）
docker-compose up -d

# 或直接运行 Flask 应用
python app.py
```

### 5. 访问管理后台
- 管理后台首页: `http://localhost:5000/admin`
- 用户管理: `http://localhost:5000/admin/users`
- 数据集管理: `http://localhost:5000/admin/datasets`
- 图片管理: `http://localhost:5000/admin/images`
- 统计信息: `http://localhost:5000/admin/stats`
- 系统测试: `http://localhost:5000/admin_test.html`

## 数据库模型

### User（用户表）
```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(80) UNIQUE NOT NULL,
    email VARCHAR(120) UNIQUE NOT NULL,
    password_hash VARCHAR(128) NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);
```

### Dataset（数据集表）
```sql
CREATE TABLE datasets (
    id INTEGER PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    created_by INTEGER NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    is_public BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (created_by) REFERENCES users(id)
);
```

### Image（图片表）
```sql
CREATE TABLE images (
    id INTEGER PRIMARY KEY AUTO_INCREMENT,
    filename VARCHAR(255) NOT NULL,
    original_filename VARCHAR(255) NOT NULL,
    dataset_id INTEGER NOT NULL,
    uploaded_by INTEGER NOT NULL,
    uploaded_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    file_path VARCHAR(500) NOT NULL,
    annotations JSON DEFAULT ('[]'),
    FOREIGN KEY (dataset_id) REFERENCES datasets(id),
    FOREIGN KEY (uploaded_by) REFERENCES users(id)
);
```

## 安全特性

### 1. 身份验证
- JWT Token 认证
- 密码哈希存储
- 会话管理

### 2. 权限控制
- 用户角色管理（预留扩展）
- API 访问控制
- 文件上传安全检查

### 3. 数据验证
- 输入数据验证
- SQL 注入防护
- XSS 防护

## 扩展开发

### 添加新的管理页面
1. 在 `templates/admin/` 目录下创建新的 HTML 模板
2. 在 `app.py` 中添加对应的路由
3. 在 `services/` 中实现相应的业务逻辑

### 添加新的 API 接口
1. 在相应的 service 类中实现业务方法
2. 在 `app.py` 中添加路由和处理逻辑
3. 更新 API 文档

### 自定义样式
管理后台使用 CSS 变量，可以通过修改 `templates/admin/base.html` 中的 CSS 来自定义样式。

## 故障排除

### 常见问题

1. **管理页面无法访问**
   - 检查 Flask 应用是否正常运行
   - 确认路由配置正确
   - 查看应用日志

2. **数据库连接错误**
   - 检查数据库服务是否启动
   - 验证数据库连接配置
   - 确认数据库用户权限

3. **文件上传失败**
   - 检查上传目录权限
   - 确认文件大小限制
   - 验证文件类型

### 日志查看
```bash
# 查看 Flask 应用日志
docker logs seedai-backend-1

# 查看数据库日志
docker logs seedai-mysql-1
```

## 性能优化

### 1. 数据库优化
- 添加适当的索引
- 优化查询语句
- 使用连接池

### 2. 缓存策略
- 实现 Redis 缓存
- 静态文件缓存
- API 响应缓存

### 3. 文件存储
- 使用云存储服务
- 实现文件分片上传
- 添加文件压缩

## 部署说明

### 生产环境部署
1. 使用 Gunicorn 或 uWSGI 作为 WSGI 服务器
2. 配置 Nginx 反向代理
3. 设置 HTTPS 证书
4. 配置日志轮转
5. 设置监控和告警

### Docker 部署
项目已配置完整的 Docker 环境：
```bash
# 构建和启动
docker-compose up --build -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f backend
```

## 贡献指南

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

## 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 联系方式

- 项目主页: [https://github.com/your-username/seedai](https://github.com/your-username/seedai)
- 问题反馈: [https://github.com/your-username/seedai/issues](https://github.com/your-username/seedai/issues)
- 邮箱: your-email@example.com

---

**最后更新**: 2024年1月26日