# SeedAI 数据库操作说明

SeedAI使用MySQL 8.0作为数据存储，本目录包含数据库初始化和管理脚本。

## 目录结构

```
mysql_data/
├── README.md                    # 数据库操作说明
├── init_db.sql                  # SQL初始化脚本
├── init_database.py             # Python数据库初始化脚本
└── db_operations/              # 数据库操作脚本目录
    ├── __init__.py             # 初始化文件
    ├── db_operations.py        # 数据库操作工具
    └── README.md               # 操作说明
```

## 数据库初始化

### 方法1: 使用Python脚本（推荐）

在项目根目录下执行：

```bash
# 确保MySQL容器正在运行
docker-compose up -d mysql

# 执行数据库初始化
docker exec -w /app seedai-backend-1 python /app/init_database.py
```

### 方法2: 直接导入SQL文件

```bash
# 将SQL文件复制到MySQL容器
docker cp init_db.sql seedai-mysql-1:/tmp/init_db.sql

# 执行SQL脚本
docker exec -it seedai-mysql-1 mysql -u root -prootpass -e "SOURCE /tmp/init_db.sql;"
```

## 数据库操作脚本

使用 `db_operations/db_operations.py` 脚本来管理数据库：

```bash
cd d:\ai-projects\SeedAi\mysql_data\db_operations
python db_operations.py
```

功能包括：
- 检查并添加role列到用户表
- 确保默认用户存在
- 列出所有用户
- 创建用户表索引
- 更新用户角色
- 显示数据库统计信息

## 数据库备份与恢复

### 备份数据库
```bash
docker exec seedai-mysql-1 mysqldump -u root -prootpass ai_dataset > backup_$(date +%Y%m%d_%H%M%S).sql
```

### 恢复数据库
```bash
docker exec -i seedai-mysql-1 mysql -u root -prootpass ai_dataset < backup_file.sql
```

## 数据库连接信息

- **主机**: localhost 或 mysql (Docker内)
- **端口**: 3306
- **数据库名**: ai_dataset
- **用户名**: root
- **密码**: rootpass

## 默认用户

- **超级管理员**: admin / 123456 (角色: 2)
- **普通用户**: user1 / 123456 (角色: 0)

## 环境变量

在容器中，数据库连接信息通过以下环境变量配置：

- `MYSQL_HOST`: 数据库主机地址
- `MYSQL_PORT`: 数据库端口
- `MYSQL_USER`: 数据库用户名
- `MYSQL_PASSWORD`: 数据库密码
- `MYSQL_DATABASE`: 数据库名称

## 数据库表结构

### users 表
- 用户信息存储表
- 包含用户名、邮箱、密码哈希、角色等字段

### datasets 表
- 数据集信息存储表
- 包含数据集名称、描述、类型、创建者等字段

### images 表
- 图片信息存储表
- 包含文件名、路径、所属数据集、标注信息等字段

### annotations 表
- 标注信息存储表
- 包含标注框坐标、标签、置信度等信息

## 数据库维护

### 为表添加索引
```bash
# 使用数据库操作脚本创建索引
cd d:\ai-projects\SeedAi\mysql_data\db_operations
python db_operations.py
# 选择选项4创建用户表索引
```

### 更新用户角色
```bash
# 使用数据库操作脚本更新用户角色
cd d:\ai-projects\SeedAi\mysql_data\db_operations
python db_operations.py
# 选择选项5更新用户角色
```

### 检查数据库统计
```bash
# 使用数据库操作脚本查看统计信息
cd d:\ai-projects\SeedAi\mysql_data\db_operations
python db_operations.py
# 选择选项6显示数据库统计
```