import os
import shutil
import random
import json

# 配置参数
input_dir = 'process-data/data'      # 输入路径，包含图片和标注的各子文件夹
output_dir = 'process-data/soybean'  # 输出路径，保存划分和合并结果

img_exts = ['.jpg', '.png', '.jpeg']
train_ratio = 0.8
val_ratio = 0.1
test_ratio = 0.1

# 目标文件夹
split_dirs = {
    'train': os.path.join(output_dir, 'train'),
    'val': os.path.join(output_dir, 'val'),
    'test': os.path.join(output_dir, 'test')
}

# 标注合并文件
split_jsons = {
    'train': os.path.join(output_dir, 'annotations/train.json'),
    'val': os.path.join(output_dir, 'annotations/val.json'),
    'test': os.path.join(output_dir, 'annotations/test.json')
}

# 收集所有图片路径
def collect_images(root):
    img_paths = []
    for dirpath, _, filenames in os.walk(root):
        for fname in filenames:
            if any(fname.lower().endswith(ext) for ext in img_exts):
                img_paths.append(os.path.join(dirpath, fname))
    return img_paths

# 划分数据
def split_list(lst, ratios):
    random.shuffle(lst)
    n = len(lst)
    n_train = int(n * ratios[0])
    n_val = int(n * ratios[1])
    n_test = n - n_train - n_val
    return lst[:n_train], lst[n_train:n_train+n_val], lst[n_train+n_val:]

# 复制图片
def copy_images(img_list, target_dir):
    os.makedirs(target_dir, exist_ok=True)
    for img_path in img_list:
        shutil.copy(img_path, target_dir)

# 合并标注
def merge_annotations(img_list, out_json):
    merged = {
        "info": {
            "description": "Soybean split",
            "version": "1.0"
        },
        "licenses": [],
        "images": [],
        "annotations": [],
        "categories": []
    }
    img_id = 1
    ann_id = 1
    category_set = set()
    img_id_map = {}  # 原始文件名 -> 新id
    
    for img_path in img_list:
        base = os.path.splitext(os.path.basename(img_path))[0]
        ann_path = os.path.join(os.path.dirname(img_path), base + '.json')
        if os.path.exists(ann_path):
            with open(ann_path, 'r', encoding='utf-8') as f:
                ann = json.load(f)
                
                # 处理图片
                if 'images' in ann and len(ann['images']) > 0:
                    for img in ann['images']:
                        old_id = img.get('id', 1)
                        img['id'] = img_id
                        img['file_name'] = os.path.basename(img_path)  # 确保文件名正确
                        img_id_map[(base, old_id)] = img_id
                        merged['images'].append(img)
                        img_id += 1
                else:
                    # 如果没有图片信息，创建新的图片条目
                    merged['images'].append({
                        'id': img_id,
                        'file_name': os.path.basename(img_path),
                        'width': 0,  # 如果有宽度信息可以从图片中读取
                        'height': 0  # 如果有高度信息可以从图片中读取
                    })
                    img_id_map[(base, 1)] = img_id
                    img_id += 1
                
                # 处理标注
                if 'annotations' in ann and len(ann['annotations']) > 0:
                    for annotation in ann['annotations']:
                        old_img_id = annotation.get('image_id', 1)
                        
                        # 尝试使用映射，如果找不到则使用当前图片ID
                        new_img_id = img_id_map.get((base, old_img_id), img_id - 1)
                        annotation['id'] = ann_id
                        annotation['image_id'] = new_img_id
                        
                        merged['annotations'].append(annotation)
                        ann_id += 1
                        
                        if 'category_id' in annotation:
                            category_set.add(annotation['category_id'])
                # 处理类别
                if 'categories' in ann and len(ann['categories']) > 0:
                    for cat in ann['categories']:
                        category_set.add(cat['id'])
                        merged['categories'].append(cat)
        else:
            # 如果没有对应的标注文件，仍然需要添加图片信息
            merged['images'].append({
                'id': img_id,
                'file_name': os.path.basename(img_path)
            })
            # 注意：没有标注的图片不会有任何annotations条目，这是正常的
            img_id += 1
    
    # 去重类别
    if merged['categories']:
        cats = {cat['id']: cat for cat in merged['categories']}
        merged['categories'] = list(cats.values())
    elif category_set:
        merged['categories'] = [{'id': cid, 'name': str(cid)} for cid in sorted(category_set)]
    
    # 确保输出目录存在
    os.makedirs(os.path.dirname(out_json), exist_ok=True)
    
    with open(out_json, 'w', encoding='utf-8') as f:
        json.dump(merged, f, ensure_ascii=False, indent=2)

if __name__ == '__main__':
    imgs = collect_images(input_dir)
    train, val, test = split_list(imgs, [train_ratio, val_ratio, test_ratio])

    copy_images(train, split_dirs['train'])
    copy_images(val, split_dirs['val'])
    copy_images(test, split_dirs['test'])

    merge_annotations(train, split_jsons['train'])
    merge_annotations(val, split_jsons['val'])
    merge_annotations(test, split_jsons['test'])

    print(f"划分完成，图片数量：train={len(train)}, val={len(val)}, test={len(test)}")
    print("标注文件已合并。")