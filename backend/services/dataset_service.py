import json
import os
import shutil

from models import db, Dataset, Image, DatasetLabelCategory
from config import Config
from werkzeug.exceptions import BadRequest


class DatasetService:
    """数据集相关服务层：封装数据集、图片与标签类别配置的核心读写逻辑。"""

    @staticmethod
    def _to_dict_with_live_count(dataset):
        """序列化数据集，并用实时图片数量覆盖 item_count。"""
        payload = dataset.to_dict()
        live_count = len(dataset.images) if dataset and dataset.images is not None else 0
        payload['item_count'] = live_count
        payload['image_count'] = live_count
        return payload

    @staticmethod
    def create_dataset(name, description, created_by, category='detection'):
        """创建数据集并返回字典结构。"""
        dataset = Dataset(
            name=name,
            description=description,
            category=category,
            created_by=created_by
        )
        db.session.add(dataset)
        db.session.commit()
        return dataset.to_dict()

    @staticmethod
    def get_dataset_by_id(dataset_id):
        """按 ID 获取单个数据集。"""
        dataset = Dataset.query.get(dataset_id)
        return DatasetService._to_dict_with_live_count(dataset) if dataset else None

    @staticmethod
    def get_datasets_by_user(user_id):
        """获取指定用户创建的全部数据集。"""
        datasets = Dataset.query.filter_by(created_by=user_id).all()
        return [DatasetService._to_dict_with_live_count(dataset) for dataset in datasets]

    @staticmethod
    def get_public_datasets():
        """获取公开数据集列表。"""
        datasets = Dataset.query.filter_by(is_public=True).all()
        return [DatasetService._to_dict_with_live_count(dataset) for dataset in datasets]

    @staticmethod
    def update_dataset(dataset_id, user_id, data):
        """更新数据集；仅允许创建者更新。"""
        dataset = Dataset.query.get(dataset_id)
        if not dataset or dataset.created_by != user_id:
            raise BadRequest("Dataset not found or access denied")
        
        # 允许更新类别字段
        for key, value in data.items():
            if hasattr(dataset, key):
                setattr(dataset, key, value)
        
        db.session.commit()
        return DatasetService._to_dict_with_live_count(dataset)

    @staticmethod
    def delete_dataset(dataset_id, user_id):
        """删除数据集；仅允许创建者删除。"""
        dataset = Dataset.query.get(dataset_id)
        if not dataset or dataset.created_by != user_id:
            raise BadRequest("Dataset not found or access denied")

        images = Image.query.filter_by(dataset_id=dataset_id).all()
        datasets_root = os.path.abspath(Config.DATASETS_FOLDER)

        def _is_under_datasets_root(path):
            if not path:
                return False
            try:
                abs_path = os.path.abspath(path)
                return os.path.commonpath([abs_path, datasets_root]) == datasets_root
            except ValueError:
                return False

        # Collect paths before DB deletion so filesystem cleanup can run afterwards.
        image_file_paths = [item.file_path for item in images if _is_under_datasets_root(item.file_path)]
        annotation_file_paths = [item.annotations_path for item in images if _is_under_datasets_root(item.annotations_path)]

        # Also try to remove dataset-level folders after file cleanup.
        candidate_dirs = set()
        for file_path in image_file_paths:
            parent_dir = os.path.dirname(file_path)
            if parent_dir:
                candidate_dirs.add(parent_dir)
        for annotation_path in annotation_file_paths:
            ann_parent = os.path.dirname(annotation_path)
            if ann_parent:
                candidate_dirs.add(ann_parent)
            ann_root = os.path.dirname(ann_parent)
            if ann_root:
                candidate_dirs.add(ann_root)

        try:
            DatasetLabelCategory.query.filter_by(dataset_id=dataset_id).delete(synchronize_session=False)
            Image.query.filter_by(dataset_id=dataset_id).delete(synchronize_session=False)
            db.session.delete(dataset)
            db.session.commit()
        except Exception:
            db.session.rollback()
            raise

        # Cleanup files after successful DB transaction.
        for file_path in image_file_paths + annotation_file_paths:
            try:
                if _is_under_datasets_root(file_path) and os.path.isfile(file_path):
                    os.remove(file_path)
            except OSError:
                continue

        # Cleanup empty directories and dataset folder leftovers.
        for dir_path in sorted(candidate_dirs, key=len, reverse=True):
            try:
                if _is_under_datasets_root(dir_path) and os.path.isdir(dir_path):
                    shutil.rmtree(dir_path, ignore_errors=True)
            except OSError:
                continue

        return True

    @staticmethod
    def add_image_to_dataset(dataset_id, filename, original_filename, uploaded_by, file_path):
        """向数据集新增图片记录，并同步更新 item_count。"""
        dataset = Dataset.query.get(dataset_id)
        if not dataset:
            raise BadRequest("Dataset not found")
        
        image = Image(
            filename=filename,
            original_filename=original_filename,
            dataset_id=dataset_id,
            uploaded_by=uploaded_by,
            file_path=file_path
        )
        db.session.add(image)
        # 上传新文件后更新数据集项目计数
        dataset.item_count = (dataset.item_count or 0) + 1
        db.session.commit()
        return image.to_dict()

    @staticmethod
    def get_images_in_dataset(dataset_id):
        """获取数据集下的全部图片。"""
        images = Image.query.filter_by(dataset_id=dataset_id).all()
        return [image.to_dict() for image in images]

    @staticmethod
    def get_all_datasets():
        """获取所有数据集（管理后台使用）"""
        datasets = Dataset.query.all()
        return [dataset.to_admin_dict() for dataset in datasets]

    @staticmethod
    def get_dataset_count():
        """获取数据集总数"""
        return Dataset.query.count()

    @staticmethod
    def get_public_dataset_count():
        """获取公开数据集数量"""
        return Dataset.query.filter_by(is_public=True).count()

    @staticmethod
    def toggle_dataset_public(dataset_id):
        """切换数据集公开状态"""
        dataset = Dataset.query.get(dataset_id)
        if not dataset:
            raise BadRequest("Dataset not found")
        
        dataset.is_public = not dataset.is_public
        db.session.commit()
        return dataset.to_admin_dict()

    @staticmethod
    def get_label_categories(dataset_id):
        """读取数据集标签类别配置，返回清洗后的类别数组。"""
        config = DatasetLabelCategory.query.filter_by(dataset_id=dataset_id).first()
        if not config:
            return []

        try:
            # categories 在表中是 JSON 字符串；容错处理脏数据。
            categories = json.loads(config.categories or '[]')
            if not isinstance(categories, list):
                categories = []
        except (TypeError, ValueError):
            categories = []

        # 去除空白项，确保前端拿到的是纯净字符串列表。
        categories = [str(item).strip() for item in categories if str(item).strip()]
        return categories

    @staticmethod
    def add_label_category(dataset_id, name):
        """新增单个标签类别；若已存在则保持幂等。"""
        cleaned = str(name or '').strip()
        if not cleaned:
            raise BadRequest('Category name is required')

        dataset = Dataset.query.get(dataset_id)
        if not dataset:
            raise BadRequest('Dataset not found')

        config = DatasetLabelCategory.query.filter_by(dataset_id=dataset_id).first()
        if not config:
            # 首次新增类别时自动初始化配置行。
            config = DatasetLabelCategory(
                dataset_id=dataset_id,
                task_type=dataset.category or 'detection',
                categories='[]'
            )
            db.session.add(config)

        try:
            categories = json.loads(config.categories or '[]')
            if not isinstance(categories, list):
                categories = []
        except (TypeError, ValueError):
            categories = []

        if cleaned not in categories:
            categories.append(cleaned)
            config.categories = json.dumps(categories, ensure_ascii=False)
            db.session.commit()
        else:
            # 保持会话一致，不重复写库。
            db.session.flush()

        return categories

    @staticmethod
    def remove_label_category(dataset_id, name):
        """删除单个标签类别；若不存在则直接返回当前类别列表。"""
        cleaned = str(name or '').strip()
        if not cleaned:
            raise BadRequest('Category name is required')

        dataset = Dataset.query.get(dataset_id)
        if not dataset:
            raise BadRequest('Dataset not found')

        config = DatasetLabelCategory.query.filter_by(dataset_id=dataset_id).first()
        if not config:
            return []

        try:
            categories = json.loads(config.categories or '[]')
            if not isinstance(categories, list):
                categories = []
        except (TypeError, ValueError):
            categories = []

        categories = [str(item).strip() for item in categories if str(item).strip()]
        if cleaned in categories:
            # 仅删除完全匹配项，避免误删相似名称。
            categories = [item for item in categories if item != cleaned]
            config.categories = json.dumps(categories, ensure_ascii=False)
            db.session.commit()
        else:
            db.session.flush()

        return categories
