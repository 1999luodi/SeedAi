import json
import os
from PIL import Image
from tqdm import tqdm
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def process_annotations(json_file, images_folder, labels_folder):
    """
    处理COCO格式的标注文件，将其转换为YOLO格式
    """
    logger.info(f"开始处理JSON文件: {json_file}")
    
    # 读取JSON文件
    with open(json_file, 'r') as file:
        data = json.load(file)
    
    # 创建图片ID到图片信息的映射
    image_info = {img['id']: img for img in data['images']}
    
    annotations = data['annotations']
    logger.info(f"总共有 {len(annotations)} 个标注")

    # 按图片ID分组标注
    annotations_by_image = {}
    for annotation in annotations:
        image_id = annotation['image_id']
        if image_id not in annotations_by_image:
            annotations_by_image[image_id] = []
        annotations_by_image[image_id].append(annotation)
    
    logger.info(f"涉及 {len(annotations_by_image)} 张不同的图片")
    
    processed_count = 0
    for image_id, image_annotations in tqdm(annotations_by_image.items(), desc="Processing images"):
        # 获取图片信息
        if image_id not in image_info:
            logger.warning(f"图片ID {image_id} 在images部分找不到")
            continue
            
        img_info = image_info[image_id]
        image_filename = img_info['file_name']
        width = img_info['width']
        height = img_info['height']
        
        # 验证图片是否存在
        file_path = os.path.join(images_folder, image_filename)
        if not os.path.exists(file_path):
            logger.warning(f"图片文件不存在: {file_path}")
            continue
        
        # 准备标签内容
        label_contents = []
        for annotation in image_annotations:
            category_id = annotation['category_id']
            bbox = annotation['bbox']
            
            # 计算归一化的坐标
            x_center = (bbox[0] + bbox[2] / 2) / width
            y_center = (bbox[1] + bbox[3] / 2) / height
            w_norm = bbox[2] / width
            h_norm = bbox[3] / height
            
            # 确保坐标在有效范围内
            x_center = max(0, min(1, x_center))
            y_center = max(0, min(1, y_center))
            w_norm = max(0, min(1, w_norm))
            h_norm = max(0, min(1, h_norm))
            
            # 写入标签文件，标签编号减1（因为COCO的类别ID从1开始，YOLO从0开始）
            label = category_id - 1
            label_content = f"{label} {x_center:.6f} {y_center:.6f} {w_norm:.6f} {h_norm:.6f}"
            label_contents.append(label_content)
        
        # 如果有有效的标注，写入标签文件
        if label_contents:
            # 使用原始图片文件名但改变扩展名为.txt
            label_file_name = os.path.splitext(os.path.basename(image_filename))[0] + '.txt'
            label_file_path = os.path.join(labels_folder, label_file_name)
            
            with open(label_file_path, 'w') as file:  # 使用'w'模式，覆盖写入
                file.write('\n'.join(label_contents) + '\n')
            
            processed_count += 1
        else:
            logger.warning(f"图片 {image_filename} 没有有效的标注")
    
    logger.info(f"成功处理了 {processed_count} 张图片的标注")


def create_labels_folder(labels_folder):
    """
    创建labels文件夹及其子文件夹
    """
    train_labels_folder = os.path.join(labels_folder, 'train')
    val_labels_folder = os.path.join(labels_folder, 'val')
    test_labels_folder = os.path.join(labels_folder, 'test')  # 添加测试集文件夹
    os.makedirs(train_labels_folder, exist_ok=True)
    os.makedirs(val_labels_folder, exist_ok=True)
    os.makedirs(test_labels_folder, exist_ok=True)  # 创建测试集文件夹
    logger.info(f"创建了标签文件夹: {train_labels_folder}, {val_labels_folder}, {test_labels_folder}")
    return train_labels_folder, val_labels_folder, test_labels_folder


def main():
    # 检查数据文件是否存在
    base_path = 'D:\\ai-projects\\SeedAi\\data\\uploads\\soybean'
    
    train_annotation_path = os.path.join(base_path, 'annotations', 'train.json')
    val_annotation_path = os.path.join(base_path, 'annotations', 'val.json')
    test_annotation_path = os.path.join(base_path, 'annotations', 'test.json')  # 添加测试集路径
    
    if not os.path.exists(train_annotation_path):
        logger.error(f"训练标注文件不存在: {train_annotation_path}")
        return
    if not os.path.exists(val_annotation_path):
        logger.error(f"验证标注文件不存在: {val_annotation_path}")
        return
    # 注意：测试集可能不存在，所以不强制要求
    
    train_images_path = os.path.join(base_path, 'train')
    val_images_path = os.path.join(base_path, 'val')
    test_images_path = os.path.join(base_path, 'test')  # 添加测试集路径
    
    if not os.path.exists(train_images_path):
        logger.error(f"训练图片文件夹不存在: {train_images_path}")
        return
    if not os.path.exists(val_images_path):
        logger.error(f"验证图片文件夹不存在: {val_images_path}")
        return
    # 测试集可能不存在，所以不强制要求
    
    train_labels_folder, val_labels_folder, test_labels_folder = create_labels_folder(os.path.join(base_path, 'labels'))

    # 处理训练和验证数据
    logger.info("开始处理训练数据")
    process_annotations(train_annotation_path, train_images_path, train_labels_folder)
    
    logger.info("开始处理验证数据")
    process_annotations(val_annotation_path, val_images_path, val_labels_folder)
    
    # 处理测试集（如果存在）
    if os.path.exists(test_annotation_path) and os.path.exists(test_images_path):
        logger.info("开始处理测试数据")
        process_annotations(test_annotation_path, test_images_path, test_labels_folder)
    else:
        logger.info("测试集文件不存在，跳过处理")

    logger.info("完成处理。")


if __name__ == "__main__":
    main()