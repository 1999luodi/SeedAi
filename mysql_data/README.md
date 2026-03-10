# SeedAI MySQL 维护说明

本目录里有两类东西：
- 基线初始化文件：`init_db.sql`
- 增量迁移系统：`migrations/*.sql` + `migrate.py`

## 先回答你关心的问题

1. `init_db.sql` 看起来旧是正常的
- 它只负责“首次建库/建基础表”。
- 后续新增表、字段、索引都不再改它。

2. 数据库迁移在哪实现
- 迁移执行器在：`mysql_data/migrate.py`
- 迁移SQL在：`mysql_data/migrations/*.sql`
- 已执行记录在数据库表：`schema_migrations`

3. `mysql_data/data/` 里的大量文件怎么处理
- 这是 MySQL 运行时产物（数据文件、binlog、临时文件）。
- 不要手动编辑、不要当作迁移脚本维护对象。

## 推荐工作流（唯一正确姿势）

1. 首次初始化（只做一次）
- 用 `init_db.sql` 建基础结构。

2. 后续所有结构变更
- 新建一个迁移文件放在 `migrations/`。
- 文件名规则：`YYYYMMDD_HHMM_description.sql`
- 例如：`20260310_1030_create_ai_models.sql`

3. 执行迁移
```bash
python mysql_data/migrate.py --status
python mysql_data/migrate.py --all
```

## 当前与模型相关的迁移

- `20260310_1030_create_ai_models.sql`
    - 新增 `ai_models` 表
    - 字段包含模型名称、模型路径、类别数量、类别列表、创建/更新时间
    - 默认类别顺序：`["腐烂", "发芽", "未发芽"]` -> `[0, 1, 2]`

## 常用命令

```bash
# 查看迁移状态
python mysql_data/migrate.py --status

# 执行所有未执行迁移
python mysql_data/migrate.py --all

# 执行单个迁移
python mysql_data/migrate.py --file 20260310_1030_create_ai_models.sql
```

## 注意事项

- 不要修改已执行过的迁移文件；有变更请新增一个迁移文件。
- 不要用 `db.create_all()` 管理线上结构。
- `mysql_data/data/` 是运行输出目录，不参与业务版本维护。