from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

db = SQLAlchemy()


class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.Integer, default=0, nullable=False)  # 0:普通用户, 1:管理员, 2:超级管理员
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    datasets = db.relationship('Dataset', backref='creator', lazy=True)
    images = db.relationship('Image', backref='uploader', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'role': self.role,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

    def to_admin_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'role': self.role,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'dataset_count': len(self.datasets)
        }

class Dataset(db.Model):
    __tablename__ = 'datasets'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    category = db.Column(db.String(50), default='detection')  # 检测、分割等
    is_public = db.Column(db.Boolean, default=False)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    item_count = db.Column(db.Integer, default=0)  # 数据集中的项目数量

    # 关系
    images = db.relationship('Image', backref='dataset', lazy=True)
    label_category = db.relationship('DatasetLabelCategory', backref='dataset', uselist=False, lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'category': self.category,
            'is_public': self.is_public,
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'item_count': self.item_count
        }

    def to_admin_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'category': self.category,
            'is_public': self.is_public,
            'owner_username': self.creator.username if self.creator else 'Unknown',
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'image_count': len(self.images)
        }

class Image(db.Model):
    __tablename__ = 'images'

    id = db.Column(db.Integer, primary_key=True)
    original_filename = db.Column(db.String(200), nullable=False)
    filename = db.Column(db.String(200), nullable=False)
    dataset_id = db.Column(db.Integer, db.ForeignKey('datasets.id'), nullable=False)
    uploaded_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    file_path = db.Column(db.String(500))
    file_size = db.Column(db.Integer)  # 文件大小（字节）
    width = db.Column(db.Integer)
    height = db.Column(db.Integer)
    upload_date = db.Column(db.DateTime, default=datetime.utcnow)
    annotations_path = db.Column(db.String(500))  # COCO标注文件路径

    def to_dict(self):
        return {
            'id': self.id,
            'original_filename': self.original_filename,
            'filename': self.filename,
            'dataset_id': self.dataset_id,
            'uploaded_by': self.uploaded_by,
            'file_path': self.file_path,
            'file_size': self.file_size,
            'width': self.width,
            'height': self.height,
            'upload_date': self.upload_date.isoformat() if self.upload_date else None,
            'annotations_path': self.annotations_path
        }

    def to_admin_dict(self):
        return {
            'id': self.id,
            'filename': self.filename,
            'dataset_name': self.dataset.name if self.dataset else 'Unknown',
            'uploader_username': self.uploader.username if self.uploader else 'Unknown',
            'file_size': self.file_size,
            'width': self.width,
            'height': self.height,
            'annotations_path': self.annotations_path,
            'created_at': self.upload_date.isoformat() if self.upload_date else None
        }


class DatasetLabelCategory(db.Model):
    __tablename__ = 'dataset_label_categories'

    # 以数据集ID为主键，一对一存储该数据集的标注类别配置
    dataset_id = db.Column(db.Integer, db.ForeignKey('datasets.id'), primary_key=True)
    task_type = db.Column(db.String(50), nullable=False, default='detection')  # detection 或 classification
    categories = db.Column(db.Text, default='[]')  # JSON字符串数组，例如 ["seed", "root"]
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'dataset_id': self.dataset_id,
            'task_type': self.task_type,
            'categories': self.categories,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
