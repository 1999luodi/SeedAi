# MySQL 数据持久化配置说明

## 📊 配置现状

SeedAI 项目的 MySQL 数据持久化已经正确配置。以下是详细说明：

### Docker Compose 配置

```yaml
mysql:
  image: mysql:8.0
  volumes:
    - D:/ai-projects/SeedAi/mysql_data:/var/lib/mysql
  restart: unless-stopped
```

### 持久化工作原理

| 项目 | 说明 |
|------|------|
| **容器内路径** | `/var/lib/mysql` (MySQL 数据目录) |
| **宿主机路径** | `D:/ai-projects/SeedAi/mysql_data` (真实存储位置) |
| **状态** | ✅ 已配置并正常工作 |
| **重启策略** | `unless-stopped` (容器重启时数据保留) |

---

## 🗂️ 实际数据存储位置

### 主要数据库目录
```
D:\ai-projects\SeedAi\mysql_data\
├── ai_dataset/                 # 🎯 我们的应用数据库
│   ├── users.ibd               # 用户表 (6 条记录)
│   ├── datasets.ibd            # 数据集表 (3 条记录)
│   ├── images.ibd              # 图片表
│   └── annotations.ibd         # 标注表
├── mysql/                       # MySQL 系统库
├── performance_schema/          # 性能监控数据
└── sys/                         # 系统库
```

### 重要说明
- **ai_dataset/** 目录包含所有应用数据
- **用户表 (users.ibd)** 已包含 6 条用户记录
- **数据集表 (datasets.ibd)** 已包含 3 条数据集记录
- 所有数据都存储在宿主机的 **D 盘** 上，容器停止后不会丢失

---

## ✅ 数据持久化验证

### 当前数据库内容

**用户表 (users) - 6 条记录:**
```
┌────┬─────────────┬──────────────────────────┬──────────┐
│ ID │  用户名      │        邮箱               │ 状态      │
├────┼─────────────┼──────────────────────────┼──────────┤
│  1 │ testuser_*  │ test_*@example.com       │ ✅ 正常   │
│  2 │ admin       │ admin@seedai.com         │ ✅ 正常   │
│  3 │ zhangsan    │ zhangsan@example.com     │ ✅ 正常   │
│  4 │ lisi        │ lisi@example.com         │ ✅ 正常   │
│  5 │ wangwu      │ wangwu@example.com       │ ✅ 正常   │
│  6 │ zhaoliu     │ zhaoliu@example.com      │ ❌ 禁用   │
└────┴─────────────┴──────────────────────────┴──────────┘
```

**数据集表 (datasets) - 3 条记录:**
```
┌────┬──────────────────────────┬────────────┐
│ ID │        数据集名称          │   可见性    │
├────┼──────────────────────────┼────────────┤
│  1 │ 水稻种子活力检测数据集     │ 🔒 私密   │
│  2 │ 小麦病害识别数据集        │ 🔒 私密   │
│  3 │ 玉米产量预测数据集        │ 🔒 私密   │
└────┴──────────────────────────┴────────────┘
```

---

## 🔄 容器重启时的数据保留

### 测试数据持久化

```bash
# 1. 查看当前数据
docker exec seedai-mysql-1 mysql -u root -p ai_dataset -e "SELECT * FROM users;"

# 2. 停止容器
docker-compose down

# 3. 重新启动容器
docker-compose up -d

# 4. 再次查看数据（数据仍然存在！）
docker exec seedai-mysql-1 mysql -u root -p ai_dataset -e "SELECT * FROM users;"
```

### 预期结果
✅ 容器重启前后，所有数据保持不变

---

## 📝 管理数据库数据

### 直接访问数据库

```bash
# 进入 MySQL 容器
docker exec -it seedai-mysql-1 mysql -u root -p ai_dataset

# 在 MySQL 提示符下执行查询
mysql> SELECT * FROM users;
mysql> SELECT * FROM datasets;
mysql> EXIT;
```

### 通过管理后台操作

```
后端管理系统地址: http://localhost:5000/admin
├── /admin            → 仪表板 (统计数据)
├── /admin/users      → 用户管理 (增删改查) ✅
├── /admin/datasets   → 数据集管理
├── /admin/images     → 图片管理
└── /admin/stats      → 统计信息
```

---

## 🛡️ 数据备份建议

### 自动备份脚本

为防止意外数据丢失，建议定期备份 MySQL 数据：

```bash
# 备份脚本 (backup_mysql.sh)
#!/bin/bash
BACKUP_DIR="D:/ai-projects/SeedAi/mysql_backups"
mkdir -p $BACKUP_DIR
docker exec seedai-mysql-1 mysqldump -u root ai_dataset > $BACKUP_DIR/backup_$(date +%Y%m%d_%H%M%S).sql
```

### 手动备份

```bash
# 备份整个数据库目录
Copy-Item "D:/ai-projects/SeedAi/mysql_data" "D:/ai-projects/SeedAi/mysql_backup_$(Get-Date -Format 'yyyyMMdd')"

# 备份单个数据库
docker exec seedai-mysql-1 mysqldump -u root ai_dataset > mysql_backup.sql
```

### 恢复备份

```bash
# 从 SQL 备份恢复
docker exec -i seedai-mysql-1 mysql -u root < mysql_backup.sql
```

---

## 🗑️ 清空数据库（谨慎操作）

```bash
# 方法 1: 删除数据目录后重建
docker-compose down
rm -rf D:/ai-projects/SeedAi/mysql_data/*
docker-compose up -d
docker exec seedai-backend-1 python /app/seed_data.py

# 方法 2: 清空指定表
docker exec seedai-mysql-1 mysql -u root -p ai_dataset -e "TRUNCATE users; TRUNCATE datasets;"
```

---

## 📋 API 接口支持的数据操作

### 用户管理 API

```bash
# 📖 查询用户
curl "http://localhost:5000/api/admin/users/{user_id}"

# ✏️ 修改用户
curl -X PUT "http://localhost:5000/api/admin/users/{user_id}" \
  -H "Content-Type: application/json" \
  -d '{"email": "newemail@example.com", "is_active": true}'

# 🗑️ 删除用户
curl -X DELETE "http://localhost:5000/api/admin/users/{user_id}"

# 🔄 切换用户状态
curl -X POST "http://localhost:5000/api/admin/users/{user_id}/toggle-status"

# 📊 获取所有用户
curl "http://localhost:5000/admin/users" # HTML页面
```

---

## 💾 存储卷配置摘要

### docker-compose.yml 中的所有数据目录

| 容器 | 容器内路径 | 宿主机路径 | 用途 |
|------|-----------|-----------|------|
| **mysql** | `/var/lib/mysql` | `D:/mysql_data` | 📊 数据库持久化 |
| **backend** | `/app` | `D:/backend` | 🐍 后端代码 |
| **backend** | `/app/uploads` | `D:/uploads` | 📁 上传文件 |
| **backend** | `/app/datasets` | `D:/datasets` | 📦 原始数据集 |
| **frontend** | `/usr/share/nginx/html` | `D:/frontend` | 🌐 前端页面 |

---

## ✨ 总结

✅ **MySQL 数据持久化状态: 完全正常**

- 数据存储在宿主机 `D:\ai-projects\SeedAi\mysql_data` 目录
- 容器停止或重启时数据不会丢失
- 所有业务数据都保存在 `ai_dataset` 数据库中
- 支持通过管理后台进行增删改查操作
- 建议定期备份数据库以防意外情况

---

**配置日期**: 2026-03-06  
**验证状态**: ✅ 已验证  
**数据安全**: ✅ 持久化保证
