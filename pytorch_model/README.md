# SeedAI AI推理模块

SeedAI的AI推理模块基于PyTorch实现，主要用于目标检测和图像分析任务。

## 目录结构

```
pytorch_model/
├── README.md            # AI推理说明文档
├── model.py            # 模型定义
├── utils.py            # 工具函数
├── inference.py        # 推理逻辑
├── weights/            # 模型权重
│   └── yolov5s.pt      # YOLOv5s预训练权重
└── examples/           # 示例代码
    └── sample_usage.py # 使用示例
```

## 技术栈

- **深度学习框架**: PyTorch
- **模型**: YOLOv5s (目标检测)
- **CUDA支持**: CUDA 11.7 + cuDNN 8
- **图像处理**: OpenCV, PIL/Pillow

## 模型说明

### YOLOv5s

- **类型**: 目标检测模型
- **输入**: RGB图像 (支持JPG, PNG格式)
- **输出**: 边界框坐标、类别标签、置信度分数
- **类别**: 支持COCO数据集的80个类别
- **输入尺寸**: 640x640 (可调整)

### 模型权重

- `yolov5s.pt`: YOLOv5s预训练模型权重
- 来源: Ultralytics官方预训练模型
- 大小: 约27MB
- 性能: 224 FPS, 37.4 mAP@0.5

## 推理接口

### 初始化模型

```python
from inference import InferenceEngine

engine = InferenceEngine(model_path='/path/to/weights/yolov5s.pt')
```

### 图像推理

```python
results = engine.inference_image(image_path)
# 返回: [{'label': 'person', 'bbox': [x1, y1, x2, y2], 'confidence': 0.95}, ...]
```

### 批量推理

```python
results = engine.inference_batch(image_paths)
# 返回: 批量处理结果
```

## 配置参数

- `conf_thres`: 置信度阈值 (默认: 0.25)
- `iou_thres`: IOU阈值 (默认: 0.45)
- `max_det`: 最大检测数 (默认: 1000)
- `img_size`: 输入图像尺寸 (默认: 640)

## API集成

AI推理模块与后端API集成：

- `/api/images/{id}/detect` - 对指定图片执行AI检测
- `/api/datasets/{id}/detect-all` - 批量检测数据集图片

## 使用示例

```python
from inference import InferenceEngine

# 初始化推理引擎
engine = InferenceEngine(model_path='./weights/yolov5s.pt')

# 对图像执行推理
image_path = './uploads/sample.jpg'
detections = engine.inference_image(image_path)

# 输出检测结果
for det in detections:
    print(f"Label: {det['label']}, Confidence: {det['confidence']:.2f}")
```

## 性能优化

- GPU加速支持 (CUDA)
- TensorRT推理优化 (可选)
- 批量处理支持
- 内存管理优化

## 部署

在Docker环境中，AI推理服务作为独立容器运行：

```yaml
ai_worker:
  image: pytorch/pytorch:2.0.1-cuda11.7-cudnn8-runtime
  volumes:
    - ./pytorch_model:/workspace
    - ./uploads:/workspace/uploads
  command: python /workspace/inference.py
  depends_on:
    - backend
  restart: unless-stopped
```

## 扩展支持

未来计划支持更多模型：

- 分类模型 (ResNet, EfficientNet)
- 分割模型 (Segmentation YOLO)
- 自定义训练模型