# PyTorch Model Layout (Strict Two-Area Split)

本目录只保留两类内容，避免误操作：

- `offline/`：线下训练与导出相关代码及训练数据。
- `online/`：线上接口服务代码与当前在线模型数据。

## 1. Offline Area

用途：
- 模型训练
- 模型导出（PT -> ONNX）
- 管理训练产物与训练过程文件

主要路径：
- `offline/training/train_from_config.py`
- `offline/training/export_to_onnx.py`
- `offline/training/model_configs/yolov5-soybean.json`
- `offline/models/training/`
- `offline/third_party/ultralytics-src`

离线训练命令：

```bash
docker compose --profile train up -d --build ai_trainer
docker exec -it seedai-ai_trainer-1 python offline/training/train_from_config.py --config offline/training/model_configs/yolov5-soybean.json
```

## 2. Online Area

用途：
- 提供 AI 检测接口服务
- 加载当前在线 ONNX 模型执行推理

主要路径：
- `online/infer_service/inference.py`
- `online/infer_service/Dockerfile`
- `online/infer_service/requirements.txt`
- `online/models/service/yolov5-soybean.onnx`

线上服务命令：

```bash
docker compose up -d --build ai_worker backend frontend
```

## 3. Model Data Rule

- 训练模型与中间权重：只放 `offline/models/training/`
- 在线推理模型：只放 `online/models/service/`

## 4. Container Binding Rule

- `ai_worker` 只使用 `online/` 下的服务代码与模型。
- `ai_trainer` 只执行 `offline/` 下的训练与导出流程。

## 5. Current Service Model

当前线上默认模型路径：

- `/workspace/online/models/service/yolov5-soybean.onnx`
