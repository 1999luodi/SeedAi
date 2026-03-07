from models import db, Image, Annotation
from werkzeug.exceptions import BadRequest

class ImageService:
    @staticmethod
    def get_image_by_id(image_id):
        image = Image.query.get(image_id)
        return image.to_dict() if image else None

    @staticmethod
    def update_image_annotations(image_id, annotations):
        image = Image.query.get(image_id)
        if not image:
            raise BadRequest("Image not found")
        
        image.annotations = annotations
        db.session.commit()
        return image.to_dict()

    @staticmethod
    def delete_image(image_id, user_id):
        image = Image.query.get(image_id)
        if not image or image.uploaded_by != user_id:
            raise BadRequest("Image not found or access denied")
        
        # Remove file from filesystem
        import os
        if os.path.exists(image.file_path):
            os.remove(image.file_path)
        
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
        
        annotation = Annotation(
            image_id=image_id,
            label=label,
            x_min=x_min,
            y_min=y_min,
            x_max=x_max,
            y_max=y_max,
            confidence=confidence
        )
        db.session.add(annotation)
        db.session.commit()
        return annotation.to_dict()

    @staticmethod
    def get_annotations_by_image(image_id):
        """获取图片的所有标注"""
        annotations = Annotation.query.filter_by(image_id=image_id).all()
        return [annotation.to_dict() for annotation in annotations]

    @staticmethod
    def update_annotation(annotation_id, **kwargs):
        """更新标注"""
        annotation = Annotation.query.get(annotation_id)
        if not annotation:
            raise BadRequest("Annotation not found")
        
        for key, value in kwargs.items():
            if hasattr(annotation, key):
                setattr(annotation, key, value)
        
        db.session.commit()
        return annotation.to_dict()

    @staticmethod
    def delete_annotation(annotation_id):
        """删除标注"""
        annotation = Annotation.query.get(annotation_id)
        if not annotation:
            raise BadRequest("Annotation not found")
        
        db.session.delete(annotation)
        db.session.commit()
        return True

    @staticmethod
    def delete_image_admin(image_id):
        """删除图片（管理员）"""
        image = Image.query.get(image_id)
        if not image:
            raise BadRequest("Image not found")
        
        # Remove file from filesystem
        import os
        if os.path.exists(image.file_path):
            os.remove(image.file_path)
        
        db.session.delete(image)
        db.session.commit()
        return True
