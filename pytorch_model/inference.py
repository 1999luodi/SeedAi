"""
AI推理服务
用于处理图像检测和识别任务
"""
import torch
import cv2
import numpy as np
import os
from PIL import Image
import json
import logging
from typing import List, Dict, Tuple
import sys
import time

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class InferenceEngine:
    def __init__(self, model_path: str = None, conf_threshold: float = 0.25):
        """
        初始化推理引擎
        
        Args:
            model_path: 模型路径
            conf_threshold: 置信度阈值
        """
        self.conf_threshold = conf_threshold
        self.model = self.load_model(model_path)
        
    def load_model(self, model_path: str = None):
        """
        加载预训练模型
        """
        logger.info("正在加载模型...")
        try:
            # 检查是否可以导入YOLOv5
            if model_path and os.path.exists(model_path):
                # 尝试加载本地模型
                model = torch.hub.load('ultralytics/yolov5', 'custom', path=model_path, force_reload=True)
                logger.info(f"从 {model_path} 加载模型成功")
            else:
                # 加载预训练模型
                model = torch.hub.load('ultralytics/yolov5', 'yolov5s', pretrained=True)
                logger.info("加载默认YOLOv5s模型成功")
            
            # 设置模型为评估模式
            model.eval()
            return model
        except Exception as e:
            logger.error(f"模型加载失败: {str(e)}")
            return None

    def inference_image(self, image_path: str) -> List[Dict]:
        """
        对单张图像进行推理
        
        Args:
            image_path: 图像路径
            
        Returns:
            检测结果列表
        """
        if not self.model:
            raise ValueError("模型未加载")
        
        try:
            # 加载图像
            img = cv2.imread(image_path)
            if img is None:
                raise FileNotFoundError(f"无法加载图像: {image_path}")
            
            # 转换颜色空间
            img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            
            # 进行推理
            results = self.model(img_rgb)
            
            # 解析结果
            detections = []
            for *xyxy, conf, cls in results.xyxy[0].tolist():
                if conf >= self.conf_threshold:
                    detection = {
                        'label': self.model.names[int(cls)],
                        'bbox': [int(coord) for coord in xyxy],
                        'confidence': round(conf, 2),
                        'class_id': int(cls)
                    }
                    detections.append(detection)
            
            logger.info(f"图像 {image_path} 检测到 {len(detections)} 个对象")
            return detections
            
        except Exception as e:
            logger.error(f"图像推理失败: {str(e)}")
            raise e

    def inference_batch(self, image_paths: List[str]) -> Dict[str, List[Dict]]:
        """
        批量推理
        
        Args:
            image_paths: 图像路径列表
            
        Returns:
            包含每个图像检测结果的字典
        """
        results = {}
        for path in image_paths:
            try:
                results[path] = self.inference_image(path)
            except Exception as e:
                logger.error(f"处理图像 {path} 时出错: {str(e)}")
                results[path] = []
        return results

    def draw_detections(self, image_path: str, detections: List[Dict], output_path: str = None) -> np.ndarray:
        """
        在图像上绘制检测结果
        
        Args:
            image_path: 原始图像路径
            detections: 检测结果
            output_path: 输出路径（可选）
            
        Returns:
            绘制后的图像
        """
        img = cv2.imread(image_path)
        
        for detection in detections:
            bbox = detection['bbox']
            label = detection['label']
            conf = detection['confidence']
            
            # 绘制边界框
            cv2.rectangle(img, (bbox[0], bbox[1]), (bbox[2], bbox[3]), (0, 255, 0), 2)
            
            # 绘制标签
            text = f'{label}: {conf}'
            cv2.putText(img, text, (bbox[0], bbox[1]-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
        
        if output_path:
            cv2.imwrite(output_path, img)
        
        return img


def main():
    """
    主函数，用于测试推理引擎
    """
    # 检查命令行参数
    if len(sys.argv) < 2:
        # 如果没有提供参数，则启动服务模式
        logger.info("启动AI推理服务模式...")
        logger.info("要进行推理，请使用命令: python inference.py <image_path> [model_path]")
        # 在服务模式下，我们可以等待一段时间或者监听某些信号
        try:
            while True:
                time.sleep(60)  # 每分钟检查一次
                logger.info("AI推理服务正在运行...")
        except KeyboardInterrupt:
            logger.info("收到停止信号，正在关闭AI推理服务...")
            return
    else:
        image_path = sys.argv[1]
        model_path = sys.argv[2] if len(sys.argv) > 2 else None
        
        # 初始化推理引擎
        engine = InferenceEngine(model_path=model_path)
        
        if engine.model is None:
            print("无法初始化推理引擎")
            return
        
        # 执行推理
        try:
            results = engine.inference_image(image_path)
            print(json.dumps(results, indent=2))
        except Exception as e:
            print(f"推理过程中出现错误: {str(e)}")


if __name__ == "__main__":
    main()