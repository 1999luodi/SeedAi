# SeedAI 数据库操作工具

此目录包含用于管理SeedAI项目数据库的各种操作脚本。

## 文件说明

- `db_operations.py`: 数据库管理脚本，用于执行各种数据库操作
  - 检查并添加role列到用户表
  - 确保默认用户存在
  - 列出所有用户
  - 创建用户表索引
  - 更新用户角色
  - 显示数据库统计信息

## 使用方法

### 1. 运行数据库管理脚本

```bash
cd d:\ai-projects\SeedAi\mysql_data\db_operations
python db_operations.py
```

### 2. 确保Docker容器正在运行

在运行脚本前，请确保SeedAI的Docker容器正在运行：

```bash
cd d:\ai-projects\SeedAi
docker-compose up -d
```

## 功能说明

### 检查并添加role列
- 检查用户表中是否存在role列
- 如果不存在，则添加role列，默认值为0

### 确保默认用户存在
- 检查admin用户是否存在，如果存在则确保其角色为超级管理员(2)
- 检查user1用户是否存在

### 列出所有用户
- 显示数据库中所有用户的信息

### 创建用户表索引
- 为username和email字段创建索引以提高查询性能

### 更新用户角色
- 更新指定用户的权限级别
  - 0: 普通用户
  - 1: 管理员
  - 2: 超级管理员

### 显示数据库统计
- 显示用户、数据集和图片的数量

## 注意事项

1. 此脚本依赖Docker容器，需要seedai-mysql-1容器正在运行
2. 脚本会直接修改数据库，操作前请确保已备份重要数据
3. 默认连接到ai_dataset数据库
4. 操作前请确认MySQL服务正在运行