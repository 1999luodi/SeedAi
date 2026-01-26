from models import db, Dataset, Image
from werkzeug.exceptions import BadRequest

class DatasetService:
    @staticmethod
    def create_dataset(name, description, created_by):
        dataset = Dataset(name=name, description=description, created_by=created_by)
        db.session.add(dataset)
        db.session.commit()
        return dataset.to_dict()

    @staticmethod
    def get_dataset_by_id(dataset_id):
        dataset = Dataset.query.get(dataset_id)
        return dataset.to_dict() if dataset else None

    @staticmethod
    def get_datasets_by_user(user_id):
        datasets = Dataset.query.filter_by(created_by=user_id).all()
        return [dataset.to_dict() for dataset in datasets]

    @staticmethod
    def get_public_datasets():
        datasets = Dataset.query.filter_by(is_public=True).all()
        return [dataset.to_dict() for dataset in datasets]

    @staticmethod
    def update_dataset(dataset_id, user_id, data):
        dataset = Dataset.query.get(dataset_id)
        if not dataset or dataset.created_by != user_id:
            raise BadRequest("Dataset not found or access denied")
        
        for key, value in data.items():
            if hasattr(dataset, key):
                setattr(dataset, key, value)
        
        db.session.commit()
        return dataset.to_dict()

    @staticmethod
    def delete_dataset(dataset_id, user_id):
        dataset = Dataset.query.get(dataset_id)
        if not dataset or dataset.created_by != user_id:
            raise BadRequest("Dataset not found or access denied")
        
        db.session.delete(dataset)
        db.session.commit()
        return True

    @staticmethod
    def add_image_to_dataset(dataset_id, filename, original_filename, uploaded_by, file_path):
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
        db.session.commit()
        return image.to_dict()

    @staticmethod
    def get_images_in_dataset(dataset_id):
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
