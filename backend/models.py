from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'created_at': self.created_at.isoformat(),
            'is_active': self.is_active
        }

    def to_admin_dict(self):
        """管理后台使用的用户数据"""
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'created_at': self.created_at,
            'is_active': self.is_active,
            'dataset_count': len(self.datasets)
        }

class Dataset(db.Model):
    __tablename__ = 'datasets'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_public = db.Column(db.Boolean, default=False)

    user = db.relationship('User', backref=db.backref('datasets', lazy=True))
    images = db.relationship('Image', backref='dataset', lazy=True, cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat(),
            'is_public': self.is_public,
            'image_count': len(self.images)
        }

    def to_admin_dict(self):
        """管理后台使用的数据集数据"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'created_by': self.created_by,
            'owner_username': self.user.username if self.user else None,
            'created_at': self.created_at,
            'is_public': self.is_public,
            'image_count': len(self.images)
        }

class Image(db.Model):
    __tablename__ = 'images'
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    dataset_id = db.Column(db.Integer, db.ForeignKey('datasets.id'), nullable=False)
    uploaded_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    file_path = db.Column(db.String(500), nullable=False)
    annotations = db.Column(db.JSON, default=list)  # Store annotations as JSON

    user = db.relationship('User', backref=db.backref('images', lazy=True))

    def to_dict(self):
        return {
            'id': self.id,
            'filename': self.filename,
            'original_filename': self.original_filename,
            'dataset_id': self.dataset_id,
            'uploaded_by': self.uploaded_by,
            'uploaded_at': self.uploaded_at.isoformat(),
            'file_path': self.file_path,
            'annotations': self.annotations
        }

    def to_admin_dict(self):
        """管理后台使用的图片数据"""
        return {
            'id': self.id,
            'filename': self.filename,
            'original_filename': self.original_filename,
            'dataset_id': self.dataset_id,
            'dataset_name': self.dataset.name if self.dataset else None,
            'uploaded_by': self.uploaded_by,
            'uploader_username': self.user.username if self.user else None,
            'uploaded_at': self.uploaded_at,
            'file_path': self.file_path,
            'file_size': self.get_file_size(),
            'annotation_count': len(self.annotations) if self.annotations else 0
        }

    def get_file_size(self):
        """获取文件大小"""
        try:
            import os
            if os.path.exists(self.file_path):
                return os.path.getsize(self.file_path)
        except:
            pass
        return 0
