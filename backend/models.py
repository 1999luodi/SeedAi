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
    upload_date = db.Column(db.DateTime, default=datetime.utcnow)
    annotations = db.Column(db.Text)  # 存储标注数据的JSON字符串

    # 关系
    annotations_detail = db.relationship('Annotation', backref='image', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'original_filename': self.original_filename,
            'filename': self.filename,
            'dataset_id': self.dataset_id,
            'uploaded_by': self.uploaded_by,
            'file_path': self.file_path,
            'file_size': self.file_size,
            'upload_date': self.upload_date.isoformat() if self.upload_date else None,
            'annotations': self.annotations
        }

    def to_admin_dict(self):
        return {
            'id': self.id,
            'filename': self.filename,
            'dataset_name': self.dataset.name if self.dataset else 'Unknown',
            'uploader_username': self.uploader.username if self.uploader else 'Unknown',
            'file_size': self.file_size,
            'annotation_count': len(self.annotations_detail),
            'created_at': self.upload_date.isoformat() if self.upload_date else None
        }


class Annotation(db.Model):
    __tablename__ = 'annotations'

    id = db.Column(db.Integer, primary_key=True)
    image_id = db.Column(db.Integer, db.ForeignKey('images.id'), nullable=False)
    label = db.Column(db.String(100), nullable=False)  # 标签名称
    x_min = db.Column(db.Float, nullable=False)  # 边界框左上角x坐标 (0-1之间)
    y_min = db.Column(db.Float, nullable=False)  # 边界框左上角y坐标 (0-1之间)
    x_max = db.Column(db.Float, nullable=False)  # 边界框右下角x坐标 (0-1之间)
    y_max = db.Column(db.Float, nullable=False)  # 边界框右下角y坐标 (0-1之间)
    confidence = db.Column(db.Float, default=1.0)  # 置信度
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'image_id': self.image_id,
            'label': self.label,
            'x_min': self.x_min,
            'y_min': self.y_min,
            'x_max': self.x_max,
            'y_max': self.y_max,
            'confidence': self.confidence,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
