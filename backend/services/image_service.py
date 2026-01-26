from models import db, Image
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
