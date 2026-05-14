# SeedAI 项目总览

SeedAI 是一个面向图像数据集管理与标注的工程化项目，核心目标是：
- 统一数据集入口
- 支持手工标注与检测结果管理
- 为模型训练与推理提供标准数据资产

视频说明：
<video src="SeedAI.mp4" controls="controls" width="100%" height="100%"></video>






## 1. 总体技术路线

- 前端：多页面 Web UI（数据集管理、标注、检测、光谱）
- 后端：Flask API + 服务层
- 数据库：MySQL（结构化业务数据）
- 模型：PyTorch 推理模块
- 部署：Docker Compose + Nginx

## 2. 子项目边界

- `backend/`：业务 API、鉴权、数据服务
- `frontend/`：页面交互与可视化工具
- `mysql_data/`：数据库初始化、迁移、运维脚本
- `pytorch_model/`：模型加载与推理逻辑
- `tests/`：接口、集成与回归测试

每个子目录包含自己的 `README.md`，描述其职责、扩展方式与运行方法。

## 3. 项目治理规则

- 总 README 只写总览、边界、技术路线，不写实现细节。
- 实现细节写在子项目 README，优先解释设计与流程，尽量少放长代码段。
- 跨项目能力通过接口对接，不直接跨目录耦合调用内部实现。
- 数据库结构迭代使用 `mysql_data/migrations/*.sql`，不直接改历史迁移。

## 4. 当前解耦状态（已完成）

- 前端标注流程已改为：先选数据集，再进入标注。
- 数据库已支持增量迁移：`mysql_data/migrate.py` + `mysql_data/migrations/`。
- 新增表可通过“单个 SQL 文件”执行，不需修改 `init_db.sql`。

## 5. 你最常用的入口

- 前端：`http://localhost/`  账号： user1 密码： 123456<PASSWORD>
- 后台管理页面：`http://localhost/admin`
- 数据集操作页（从数据集列表点击“打开”进入）：`http://localhost/dataset-workspace.html?dataset=<id>`
- API 测试页面：`http://localhost/tests/api-test.html`

## 6. 数据集上传当前行为

- 在 `dataset.html` 创建数据集后，不会自动跳转，仍停留在列表页。
- 点击数据集“打开”会进入独立操作页 `dataset-workspace.html`。
- 操作页支持：拖拽上传、选择文件上传、选择目录上传。
- 前端上传限制：最多 `1000` 个文件，且单次总大小必须 `< 5GB`。

## 7. Docker 挂载约定（数据集文件）

- 后端容器挂载目录：`D:/ai-projects/SeedAi/data/datasets:/app/datasets`
- 业务文件实际写入：`data/datasets/<用户名>/<数据集名>_<id>/`
- 统一使用项目根目录下的 `data/datasets/`。

## 8. 数据库迁移

- 数据库迁移状态：`python mysql_data/migrate.py --status`

## 9. 推荐扩展顺序

1. 数据结构：先写 migration 文件。
2. 后端：补 model/service/api。
3. 前端：接入 API 与页面状态。
4. 测试：补最小回归用例。

## 10. Docker 镜像源与环境版本

### 10.1 服务镜像命名约定

- 本项目约定：自建服务镜像名不带序号，容器名带序号（如 `-1`）。
- 当前自建镜像：`seedai-backend`、`seedai-ai_worker`、`seedai-ai_trainer`。
- 当前容器命名：`seedai-mysql-1`、`seedai-backend-1`、`seedai-ai_worker-1`、`seedai-ai_trainer-1`、`seedai-frontend-1`。

### 10.2 Docker 基础镜像源地址

- `mysql`：`docker.io/mysql:8.0`
- `frontend`：`docker.io/nginx:alpine`
- `backend` 基础镜像：`docker.m.daocloud.io/library/python:3.11-slim`
- `ai_worker` 基础镜像：`docker.m.daocloud.io/library/python:3.11-slim`
- `ai_trainer` 基础镜像：`docker.io/pytorch/pytorch:2.0.1-cuda11.7-cudnn8-runtime`

### 10.3 各服务运行环境版本

- `mysql`
	- MySQL: `8.0`
- `frontend`
	- Nginx: `alpine`（随官方标签更新）
- `backend`
	- Python: `3.11-slim`
	- Flask: 由 `backend/requirements.txt` 管理
	- pip 源: `https://pypi.tuna.tsinghua.edu.cn/simple/`
- `ai_worker`
	- Python: `3.11-slim`
	- Flask: `2.3.2`
	- numpy: `1.26.4`
	- opencv-python-headless: `4.8.1.78`
	- onnxruntime: `1.18.1`
- `ai_trainer`
	- Base Runtime: `pytorch/pytorch:2.0.1-cuda11.7-cudnn8-runtime`
	- torch: `2.0.1`
	- torchvision: `0.15.2`
	- torchaudio: `2.0.2`
	- numpy: `1.24.3`
	- pip 源: `https://pypi.tuna.tsinghua.edu.cn/simple/`
