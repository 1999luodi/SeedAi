from models import db, User
from utils import generate_token
from werkzeug.exceptions import BadRequest

class UserService:
    @staticmethod
    def register_user(username, email, password):
        if User.query.filter_by(username=username).first():
            raise BadRequest("Username already exists")
        if User.query.filter_by(email=email).first():
            raise BadRequest("Email already exists")
        
        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        return user.to_dict()

    @staticmethod
    def authenticate_user(username_or_email, password):
        user = User.query.filter(
            (User.username == username_or_email) | (User.email == username_or_email)
        ).first()
        if user and user.check_password(password):
            token = generate_token(user.id)
            return {'user': user.to_dict(), 'token': token}
        return None

    @staticmethod
    def get_user_by_id(user_id):
        user = User.query.get(user_id)
        return user.to_dict() if user else None

    @staticmethod
    def update_user(user_id, data):
        user = User.query.get(user_id)
        if not user:
            raise BadRequest("User not found")
        
        for key, value in data.items():
            if key == 'password':
                user.set_password(value)
            elif hasattr(user, key):
                setattr(user, key, value)
        
        db.session.commit()
        return user.to_dict()

    @staticmethod
    def delete_user(user_id):
        user = User.query.get(user_id)
        if not user:
            raise BadRequest("User not found")
        
        db.session.delete(user)
        db.session.commit()
        return True

    @staticmethod
    def get_all_users():
        """获取所有用户（管理后台使用）"""
        users = User.query.all()
        return [user.to_admin_dict() for user in users]

    @staticmethod
    def get_user_count():
        """获取用户总数"""
        return User.query.count()

    @staticmethod
    def toggle_user_status(user_id):
        """切换用户状态（启用/禁用）"""
        user = User.query.get(user_id)
        if not user:
            raise BadRequest("User not found")
        
        user.is_active = not user.is_active
        db.session.commit()
        return user.to_admin_dict()

    @staticmethod
    def create_super_admin(username, email, password):
        """创建超级管理员"""
        if User.query.filter_by(username=username).first():
            print(f"Super admin {username} already exists.")
            return None
        
        super_admin = User(username=username, email=email, role=2)  # 2表示超级管理员
        super_admin.set_password(password)
        db.session.add(super_admin)
        db.session.commit()
        print(f"Super admin {username} created successfully.")
        return super_admin.to_dict()

    @staticmethod
    def create_user(username, email, password, role=0):
        """创建用户，role: 0-普通用户, 1-管理员, 2-超级管理员"""
        if User.query.filter_by(username=username).first():
            print(f"User {username} already exists.")
            return None
        
        user = User(username=username, email=email, role=role)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        print(f"User {username} created successfully with role {role}.")
        return user.to_dict()