# Backend 模块说明

`backend/` 负责 API、鉴权、业务编排和数据访问控制。

## 1. 模块职责

- `app.py`：路由注册与应用入口
- `models.py`：ORM 模型定义
- `services/`：业务逻辑层（用户、数据集、图片、标注）
- `config.py`：配置项
- `api_endpoints.json`：接口目录定义

## 2. 设计原则

- 路由层只做参数校验和响应组装。
- 业务逻辑放在 `services/`，避免在路由中堆积逻辑。
- 数据库结构由 `mysql_data` 管理，后端不直接承担迁移职责。

## 3. 主要功能

- JWT 登录注册与权限控制
- 数据集 CRUD
- 图片上传、查询、删除
- 标注增删改查
- 管理员后台基础接口

## 4. 数据集文件存储规则（当前实现）

- 上传接口：`POST /api/datasets/<dataset_id>/upload`
- 文件落盘目录：`data/datasets/<用户名>/<数据集名>_<dataset_id>/`
- 文件命名规则：`<unix时间戳>_<原始文件名>`
- 上传权限：仅数据集拥有者或可访问该公开数据集的用户

示例路径：`data/datasets/user3/soybean_4/1741421234_image.jpg`

说明：`config.py` 中 `DATASETS_FOLDER`（容器内 `/app/datasets`）在宿主机映射到 `data/datasets/`。

Docker Compose 挂载约定：`D:/ai-projects/SeedAi/data/datasets:/app/datasets`。

## 5. 数据集相关前端行为（与后端配合）

- 创建数据集后前端不自动跳转。
- 点击“打开”后进入 `dataset-workspace.html` 执行上传。
- 前端对上传批次有约束：最多 `1000` 个文件，单次总大小 `< 5GB`。

## 6. 可扩展点

- 新增业务能力时，优先新增 `services/<domain>_service.py`。
- 若新增数据库表：
  - 先在 `mysql_data/migrations/` 新增迁移 SQL
  - 再同步更新 `models.py` 和 service
- 若新增 API：
  - 在 `app.py` 注册路由
  - 更新 `api_endpoints.json`
  - 运行 `python backend/sync_api_contract.py` 同步前端与测试契约文件

## 7. 接口契约单点维护

- 唯一接口源文件：`backend/api_endpoints.json`
- 自动生成目标：
  - `frontend/js/api-contract.js`
  - `tests/utils/api_contract.py`
- 同步命令：`python backend/sync_api_contract.py`

## 8. 与其他模块的边界

- 对前端：只暴露 HTTP API
- 对模型模块：通过服务调用/任务触发，不与前端共享内部对象
- 对数据库：仅连接使用，不在本目录维护迁移历史

## 9. 维护建议

- 统一错误响应格式
- 为每个新增接口补充一条最小测试用例
- 将“长函数”拆分到 service，保持路由简洁
