import json
import os
import shutil
from datetime import datetime

from models import db, Image
from werkzeug.exceptions import BadRequest

class ImageService:
    @staticmethod
    def create_image(original_filename, filename, dataset_id, uploaded_by, file_path=None, file_size=None, width=None, height=None):
        """创建图片记录并持久化到数据库。"""
        image = Image(
            original_filename=original_filename,
            filename=filename,
            dataset_id=dataset_id,
            uploaded_by=uploaded_by,
            file_path=file_path,
            file_size=file_size,
            width=width,
            height=height
        )
        try:
            db.session.add(image)
            db.session.commit()
            return image
        except Exception:
            db.session.rollback()
            raise

    @staticmethod
    def get_image_by_id(image_id):
        image = Image.query.get(image_id)
        return image.to_dict() if image else None

    @staticmethod
    def update_image_annotations(image_id, annotations):
        image = Image.query.get(image_id)
        if not image:
            raise BadRequest("Image not found")
        normalized_rows = ImageService._normalize_annotations_input(annotations)
        result = ImageService.save_label_file(image_id, annotations=normalized_rows)
        return {
            'image_id': image.id,
            'annotation_count': len(normalized_rows),
            'annotations': normalized_rows,
            'annotations_path': result.get('label_file_path')
        }

    @staticmethod
    def delete_image(image_id, user_id):
        image = Image.query.get(image_id)
        if not image or image.uploaded_by != user_id:
            raise BadRequest("Image not found or access denied")

        ImageService._cleanup_image_related_files(image)

        db.session.delete(image)
        db.session.commit()
        return True

    @staticmethod
    def get_images_by_user(user_id):
        images = Image.query.filter_by(uploaded_by=user_id).all()
        return [image.to_dict() for image in images]

    @staticmethod
    def get_all_images():
        """获取所有图片（管理后台使用）"""
        images = Image.query.all()
        return [image.to_admin_dict() for image in images]

    @staticmethod
    def get_image_count():
        """获取图片总数"""
        return Image.query.count()

    @staticmethod
    def add_annotation(image_id, label, x_min, y_min, x_max, y_max, confidence=1.0):
        """添加标注"""
        image = Image.query.get(image_id)
        if not image:
            raise BadRequest("Image not found")

        rows = ImageService._read_annotations_from_file(image)
        rows.append({
            'id': ImageService._next_annotation_id(rows),
            'label': str(label or '').strip(),
            'x_min': float(x_min),
            'y_min': float(y_min),
            'x_max': float(x_max),
            'y_max': float(y_max),
            'confidence': float(confidence)
        })

        save_result = ImageService.save_label_file(image_id, annotations=rows)
        return {
            'annotation': rows[-1],
            'annotations_path': save_result.get('label_file_path')
        }

    @staticmethod
    def get_annotations_by_image(image_id):
        """获取图片的所有标注"""
        image = Image.query.get(image_id)
        if not image:
            raise BadRequest("Image not found")
        rows = ImageService._read_annotations_from_file(image)
        return {
            'annotations_path': image.annotations_path,
            'annotations': rows
        }

    @staticmethod
    def delete_image_admin(image_id):
        """删除图片（管理员）"""
        image = Image.query.get(image_id)
        if not image:
            raise BadRequest("Image not found")

        ImageService._cleanup_image_related_files(image)

        db.session.delete(image)
        db.session.commit()
        return True

    @staticmethod
    def _cleanup_image_related_files(image):
        """删除图片原始文件及其标注文件，并尝试清理空目录。"""
        raw_path = image.file_path
        ann_path = image.annotations_path

        for path in [raw_path, ann_path]:
            try:
                if path and os.path.isfile(path):
                    os.remove(path)
            except OSError:
                continue

        # Try removing now-empty annotation folder and dataset folder.
        for parent in [
            os.path.dirname(ann_path) if ann_path else None,
            os.path.dirname(raw_path) if raw_path else None,
        ]:
            try:
                if parent and os.path.isdir(parent) and not os.listdir(parent):
                    os.rmdir(parent)
            except OSError:
                continue

        dataset_folder = os.path.dirname(raw_path) if raw_path else None
        if dataset_folder and os.path.isdir(dataset_folder):
            # Remove empty nested dirs only; keep shared dataset folder if it still has files.
            try:
                for entry in os.listdir(dataset_folder):
                    full = os.path.join(dataset_folder, entry)
                    if os.path.isdir(full) and not os.listdir(full):
                        shutil.rmtree(full, ignore_errors=True)
            except OSError:
                pass

    @staticmethod
    def save_label_file(image_id, classes=None, annotations=None):
        """将当前图片标注导出为 COCO 格式，并记录到 images.annotations_path。"""
        image = Image.query.get(image_id)
        if not image:
            raise BadRequest("Image not found")

        if not image.file_path:
            raise BadRequest("Image file path not found")

        image_dir = os.path.dirname(image.file_path)
        if not image_dir or not os.path.exists(image_dir):
            raise BadRequest("Image directory not found")

        dataset_dir = image_dir
        annotations_dir = os.path.join(dataset_dir, 'annotations')
        os.makedirs(annotations_dir, exist_ok=True)

        base_name = os.path.splitext(os.path.basename(image.file_path))[0]
        label_file_name = f"{base_name}.coco.json"
        label_file_path = os.path.join(annotations_dir, label_file_name)

        if annotations is None:
            bbox_rows = ImageService._read_annotations_from_file(image)
        else:
            bbox_rows = ImageService._normalize_annotations_input(annotations)

        class_rows = [str(item).strip() for item in (classes or []) if str(item).strip()]
        category_map = {}
        category_id = 1

        for category_name in class_rows + [row.get('label', '') for row in bbox_rows]:
            normalized_name = str(category_name or '').strip()
            if normalized_name and normalized_name not in category_map:
                category_map[normalized_name] = category_id
                category_id += 1

        image_width = int(image.width) if image.width else 1
        image_height = int(image.height) if image.height else 1
        coco_annotations = []
        for index, row in enumerate(bbox_rows, start=1):
            x_min = float(row.get('x_min', 0))
            y_min = float(row.get('y_min', 0))
            x_max = float(row.get('x_max', 0))
            y_max = float(row.get('y_max', 0))
            width = max(0.0, x_max - x_min)
            height = max(0.0, y_max - y_min)
            label_name = str(row.get('label', '')).strip()
            coco_annotations.append({
                'id': index,
                'image_id': image.id,
                'category_id': category_map.get(label_name, 0),
                'bbox': [x_min, y_min, width, height],
                'area': width * height,
                'iscrowd': 0,
                'score': float(row.get('confidence', 1.0))
            })

        coco_payload = {
            'info': {
                'description': 'SeedAI Annotation Export',
                'version': '1.0',
                'date_created': datetime.utcnow().isoformat() + 'Z'
            },
            'licenses': [],
            'images': [
                {
                    'id': image.id,
                    'file_name': image.original_filename or image.filename,
                    'width': image_width,
                    'height': image_height
                }
            ],
            'annotations': coco_annotations,
            'categories': [
                {
                    'id': category_id_value,
                    'name': category_name,
                    'supercategory': 'seedai'
                }
                for category_name, category_id_value in category_map.items()
            ]
        }

        with open(label_file_path, 'w', encoding='utf-8') as handle:
            json.dump(coco_payload, handle, ensure_ascii=False, indent=2)

        image.annotations_path = label_file_path
        try:
            db.session.commit()
        except Exception:
            db.session.rollback()
            raise

        return {
            'label_file_name': label_file_name,
            'label_file_path': label_file_path,
            'annotation_count': len(coco_annotations),
            'class_count': len(category_map)
        }

    @staticmethod
    def _read_annotations_from_file(image):
        label_file_path = image.annotations_path
        if not label_file_path or not os.path.exists(label_file_path):
            return []

        try:
            with open(label_file_path, 'r', encoding='utf-8') as handle:
                payload = json.load(handle)
        except (OSError, ValueError, TypeError, json.JSONDecodeError):
            return []

        coco_annotations = payload.get('annotations', []) if isinstance(payload, dict) else []
        coco_categories = payload.get('categories', []) if isinstance(payload, dict) else []
        coco_images = payload.get('images', []) if isinstance(payload, dict) else []

        if not isinstance(coco_annotations, list):
            return []

        category_map = {}
        for item in coco_categories if isinstance(coco_categories, list) else []:
            if not isinstance(item, dict):
                continue
            category_map[item.get('id')] = str(item.get('name', '')).strip()

        image_width = 1.0
        image_height = 1.0
        if isinstance(coco_images, list) and coco_images:
            first = coco_images[0] if isinstance(coco_images[0], dict) else {}
            try:
                image_width = float(first.get('width') or 1.0)
                image_height = float(first.get('height') or 1.0)
            except (TypeError, ValueError):
                image_width = 1.0
                image_height = 1.0

        normalized = []
        for index, item in enumerate(coco_annotations, start=1):
            if not isinstance(item, dict):
                continue

            label = category_map.get(item.get('category_id')) or str(item.get('label', '')).strip()
            if not label:
                continue

            try:
                bbox = item.get('bbox') or []
                if not isinstance(bbox, (list, tuple)) or len(bbox) < 4:
                    continue

                x_min = float(bbox[0])
                y_min = float(bbox[1])
                width = float(bbox[2])
                height = float(bbox[3])

                # Accept both normalized and pixel-space COCO bbox data.
                if (abs(x_min) > 1 or abs(y_min) > 1 or abs(width) > 1 or abs(height) > 1) and image_width > 1 and image_height > 1:
                    x_min = x_min / image_width
                    y_min = y_min / image_height
                    width = width / image_width
                    height = height / image_height

                normalized.append({
                    'id': int(item.get('id', index)),
                    'label': label,
                    'x_min': x_min,
                    'y_min': y_min,
                    'x_max': x_min + width,
                    'y_max': y_min + height,
                    'confidence': float(item.get('score', 1.0))
                })
            except (TypeError, ValueError):
                continue
        return normalized

    @staticmethod
    def _normalize_annotations_input(annotations):
        if not isinstance(annotations, list):
            raise BadRequest("annotations must be a list")

        normalized_rows = []
        for index, item in enumerate(annotations):
            if not isinstance(item, dict):
                raise BadRequest(f"annotations[{index}] must be an object")

            label = str(item.get('label', '')).strip()
            if not label:
                raise BadRequest(f"annotations[{index}].label is required")

            try:
                x_min = float(item['x_min'])
                y_min = float(item['y_min'])
                x_max = float(item['x_max'])
                y_max = float(item['y_max'])
                confidence = float(item.get('confidence', 1.0))
            except (KeyError, TypeError, ValueError):
                raise BadRequest(f"annotations[{index}] has invalid coordinates")

            raw_id = item.get('id')
            try:
                normalized_id = int(raw_id)
            except (TypeError, ValueError):
                normalized_id = index + 1

            normalized_rows.append({
                'id': normalized_id,
                'label': label,
                'x_min': x_min,
                'y_min': y_min,
                'x_max': x_max,
                'y_max': y_max,
                'confidence': confidence
            })

        return normalized_rows

    @staticmethod
    def _next_annotation_id(rows):
        max_id = 0
        for row in rows:
            try:
                max_id = max(max_id, int(row.get('id', 0)))
            except (TypeError, ValueError):
                continue
        return max_id + 1
