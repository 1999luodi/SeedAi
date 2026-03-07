# SeedAI 后端服务

SeedAI 是一个基于AI的图像标注与数据集管理平台的后端服务部分。

## 功能特性

- 用户注册/登录与JWT认证
- 数据集创建与管理
- 图片上传与存储
- AI模型推理支持（目标检测）
- 完整的RBAC基础架构（基于JWT）

## 系统架构

后端采用Flask框架，配合MySQL数据库存储用户、数据集和图像信息。

### 目录结构

```
backend/
├── app.py                # 主应用入口
├── config.py             # 配置管理
├── models.py             # ORM模型定义
├── utils.py              # 工具函数
├── services/             # 业务逻辑层
│   ├── user_service.py   # 用户服务
│   ├── dataset_service.py # 数据集服务
│   └── image_service.py  # 图像服务
├── templates/            # Flask模板
│   └── login.html        # 登录页面
├── api_endpoints.json    # API端点定义
└── requirements.txt      # Python依赖
```

## 容器化部署

使用Docker容器部署，数据持久化通过Docker卷实现：

- MySQL数据持久化至 `./mysql_data/data`
- 用户上传文件存储于 `./uploads`
- 数据集文件存储于 `./datasets`

**注意：** 容器重启不会丢失数据，因为数据已通过Docker卷映射到宿主机目录。但应用配置和安装的软件包会保留，除非重建镜像。

## 系统入口

- **后端管理系统入口**：`http://localhost/backend/login`
- **API测试页面**：`http://localhost/tests/api-test.html`

## 默认账户

- **超级管理员**：admin / 123456（角色为2）
- **普通用户**：user1 / 123456（角色为0）

## API接口

所有API接口定义都从后端的[api_endpoints.json](file:///d:/ai-projects/SeedAi/backend/api_endpoints.json)文件动态加载，便于API测试页面和其他工具使用。

## 技术栈

- Python 3.9+
- Flask 2.3.2
- Flask-SQLAlchemy 3.1.1
- PyMySQL 1.1.0
- PyJWT 2.8.0
- bcrypt 4.0.1
- SQLAlchemy 2.0.23

## 权限管理

- 超级管理员 (role=2)：可访问所有管理功能，可修改所有用户数据
- 普通管理员 (role=1)：仅可访问基础管理页面，仅可查看数据，无修改权限
- 普通用户 (role=0)：仅拥有基本功能权限


## API 接口

### 认证 API

#### 用户登录
```bash
POST /api/auth/login
Content-Type: application/json

{
  "username_or_email": "admin",
  "password": "123456"
}
```

**响应示例：**
```json
{
  "success": true,
  "message": "Login successful",
  "data": {
    "user": {
      "id": 1,
      "username": "admin",
      "email": "admin@admin.com",
      "created_at": "2026-03-07T11:32:25",
      "role": 2
    },
    "token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
  }
}
```

#### 后端管理系统登录（使用不同接口，需要管理权限）
```bash
POST /backend/login
Content-Type: application/json

{
  "username_or_email": "admin",
  "password": "123456"
}
```

#### 用户注册
```bash
POST /api/auth/register
Content-Type: application/json

{
  "username": "newuser",
  "email": "newuser@example.com",
  "password": "SecurePassword123"
}
```

### 用户管理 API

#### 获取当前用户信息
```bash
GET /api/users/profile
Authorization: Bearer {token}
```

#### 查看用户信息
```bash
GET /api/users/{user_id}
Authorization: Bearer {token}
```

#### 修改用户信息
```bash
PUT /api/users/{user_id}
Authorization: Bearer {token}
Content-Type: application/json

{
  "username": "updated_username",
  "email": "updated@example.com"
}
```

#### 用户退出
```bash
POST /api/auth/logout
Authorization: Bearer {token}
```

### 数据集管理 API

#### 创建数据集
```bash
POST /api/datasets
Authorization: Bearer {token}
Content-Type: application/json

{
  "name": "My Dataset",
  "description": "A sample dataset for testing",
  "category": "detection"
}
```

#### 获取用户数据集列表
```bash
GET /api/datasets
Authorization: Bearer {token}
```

#### 查看指定数据集
```bash
GET /api/datasets/{dataset_id}
Authorization: Bearer {token}
```

#### 修改数据集
```bash
PUT /api/datasets/{dataset_id}
Authorization: Bearer {token}
Content-Type: application/json

{
  "name": "Updated Dataset Name",
  "description": "Updated description",
  "category": "classification"
}
```

#### 删除数据集
```bash
DELETE /api/datasets/{dataset_id}
Authorization: Bearer {token}
```

### 图片管理 API

#### 上传图片到数据集
```bash
POST /api/datasets/{dataset_id}/upload
Authorization: Bearer {token}
Content-Type: multipart/form-data
```

#### 查看指定图片
```bash
GET /api/images/{image_id}
Authorization: Bearer {token}
```

#### 修改图片信息
```bash
PUT /api/images/{image_id}
Authorization: Bearer {token}
Content-Type: application/json

{
  "original_filename": "new_filename.jpg"
}
```

#### 删除图片
```bash
DELETE /api/images/{image_id}
Authorization: Bearer {token}
```

### 数据标注 API

#### 查看图片标注
```bash
GET /api/images/{image_id}/annotations
Authorization: Bearer {token}
```

#### 添加标注
```bash
POST /api/images/{image_id}/annotations
Authorization: Bearer {token}
Content-Type: application/json

{
  "label": "person",
  "x_min": 0.1,
  "y_min": 0.2,
  "x_max": 0.8,
  "y_max": 0.9,
  "confidence": 0.95
}
```

#### 修改标注
```bash
PUT /api/annotations/{annotation_id}
Authorization: Bearer {token}
Content-Type: application/json

{
  "label": "updated_label",
  "confidence": 0.98
}
```

#### 删除标注
```bash
DELETE /api/annotations/{annotation_id}
Authorization: Bearer {token}
```

### AI推理 API

#### AI推理接口，接收图片返回标注结果
```bash
POST /api/ai/inference
Authorization: Bearer {token}
Content-Type: multipart/form-data

image: <file>
```

**响应示例：**
```json
{
  "success": true,
  "message": "Inference completed",
  "data": [
    {
      "label": "person",
      "bbox": [100, 100, 200, 300],
      "confidence": 0.95,
      "class_id": 0
    },
    {
      "label": "car",
      "bbox": [300, 200, 500, 400],
      "confidence": 0.89,
      "class_id": 2
    }
  ]
}
```

### 管理员 API

#### 切换用户状态（管理员）
```bash
POST /api/admin/users/{user_id}/toggle-status
Authorization: Bearer {token}
```

## 安全特性

### 1. 身份验证
- JWT Token 认证
- 密码哈希存储
- 会话管理

### 2. 权限控制
- 用户角色管理
- API 访问控制
- 文件上传安全检查

### 3. 数据验证
- 输入数据验证
- SQL 注入防护
- XSS 防护

## 部署说明

### Docker 部署
项目已配置完整的 Docker 环境：
```bash
# 构建和启动
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs backend
```

### 手动部署
```bash
# 安装依赖
pip install -r requirements.txt

# 初始化数据库
python db_init.py

# 启动应用
python app.py
```

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