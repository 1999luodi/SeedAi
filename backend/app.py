from flask import Flask, render_template, request, jsonify, session, redirect, send_from_directory, send_file, g
from flask_cors import CORS
from config import Config
import sys
import os

# 添加当前目录到Python路径，确保能导入同目录下的模块
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from models import db, User, Dataset, Image
from services.user_service import UserService
from services.dataset_service import DatasetService
from services.image_service import ImageService
import os
import jwt
from functools import wraps
from werkzeug.utils import secure_filename
from werkzeug.exceptions import BadRequest
import logging
from datetime import datetime, timedelta
from PIL import Image as PILImage, UnidentifiedImageError

def create_app():
    app = Flask(__name__, template_folder='templates')
    app.config.from_object(Config)
    
    # 初始化扩展
    db.init_app(app)
    
    # 启用CORS，允许来自前端的请求
    CORS(app, resources={r"/api/*": {"origins": "*"}})
    
    # 设置日志
    logging.basicConfig(level=logging.INFO)
    
    return app

# 创建应用实例
app = create_app()
logger = logging.getLogger(__name__)

def create_response(success, message, data=None, status_code=200):
    """创建标准响应格式"""
    response = {
        'success': success,
        'message': message
    }
    if data is not None:
        if hasattr(data, 'to_dict'):
            response['data'] = data.to_dict()
        elif isinstance(data, list) and len(data) > 0 and hasattr(data[0], 'to_dict'):
            response['data'] = [item.to_dict() for item in data]
        else:
            response['data'] = data
            
    return jsonify(response), status_code if success else status_code

# 确保上传目录存在
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            try:
                token = auth_header.split(" ")[1]  # Bearer <token>
            except IndexError:
                return jsonify({'success': False, 'message': 'Token is missing!'}), 401
        
        if not token:
            return jsonify({'success': False, 'message': 'Token is missing!'}), 401

        try:
            data = jwt.decode(token, app.config['JWT_SECRET_KEY'], algorithms=["HS256"])
            current_user = User.query.get(data['user_id'])
        except jwt.ExpiredSignatureError:
            return jsonify({'success': False, 'message': 'Token is expired!'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'success': False, 'message': 'Token is invalid!'}), 401

        return f(current_user, *args, **kwargs)
    
    return decorated

# 专门为管理页面创建的装饰器，会在未登录时重定向到登录页面
def login_required_html(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        # 首先检查请求头中的Authorization（前端JavaScript会自动添加）
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            try:
                token = auth_header.split(" ")[1]  # Bearer <token>
            except IndexError:
                pass  # 如果格式不对，继续检查其他来源
        # 然后检查session中的token
        elif 'auth_token' in session:
            token = session['auth_token']
        
        if not token:
            # 如果是HTML页面请求，重定向到后端登录页
            if request.endpoint and 'admin' in request.endpoint:
                return redirect('/backend/login'), 302
            return jsonify({'success': False, 'message': 'Token is missing!'}), 401

        try:
            data = jwt.decode(token, app.config['JWT_SECRET_KEY'], algorithms=["HS256"])
            current_user = User.query.get(data['user_id'])
            if not current_user:
                return redirect('/backend/login'), 401
        except jwt.ExpiredSignatureError:
            return redirect('/backend/login'), 401
        except jwt.InvalidTokenError:
            return redirect('/backend/login'), 401

        return f(current_user, *args, **kwargs)
    
    return decorated

@app.route('/')
def index():
    # 重定向到前端首页
    return redirect('http://localhost/')  # Nginx代理在localhost

@app.route('/login')
def login_page():
    # 重定向到前端登录页面
    return redirect('http://localhost/login')

# 后端管理系统相关路由
@app.route('/backend')
def backend_index():
    # 后端管理系统首页
    return redirect('/backend/login')

@app.route('/backend/login')
def backend_login_page():
    # 后端管理系统登录页面，使用Flask模板
    return render_template('login.html')

@app.route('/backend/admin')
@login_required_html
def backend_admin_page(current_user):
    # 后端管理系统管理页面，需要登录
    if current_user.role < 1:
        return jsonify({'success': False, 'message': 'Insufficient permissions'}), 403
    
    # 获取统计数据
    stats = {
        'total_users': User.query.count(),
        'total_datasets': Dataset.query.count(),
        'total_images': Image.query.count(),
        'public_datasets': Dataset.query.filter_by(is_public=True).count()
    }
    
    # 渲染管理后台模板
    return render_template('admin/dashboard.html', current_user=current_user, stats=stats)

@app.route('/backend/admin/users')
@login_required_html
def admin_users(current_user):
    if current_user.role < 2:  # 只有超级管理员可以访问用户管理
        return jsonify({'success': False, 'message': 'Insufficient permissions'}), 403
    # 获取用户数据和统计信息
    users = User.query.all()
    for user in users:
        user.dataset_count = Dataset.query.filter_by(created_by=user.id).count()
    return render_template('admin/users.html', current_user=current_user, users=users)

@app.route('/backend/admin/datasets')
@login_required_html
def admin_datasets(current_user):
    if current_user.role < 1:  # 管理员及以上可访问
        return jsonify({'success': False, 'message': 'Insufficient permissions'}), 403

    datasets = Dataset.query.all()
    for dataset in datasets:
        dataset.owner_username = dataset.creator.username if dataset.creator else 'Unknown'
        dataset.image_count = len(dataset.images) if dataset.images is not None else 0

    return render_template('admin/datasets.html', current_user=current_user, datasets=datasets)

@app.route('/backend/admin/images')
@login_required_html
def admin_images(current_user):
    if current_user.role < 1:  # 管理员及以上可访问
        return jsonify({'success': False, 'message': 'Insufficient permissions'}), 403

    try:
        images = ImageService.get_all_images()
        return render_template('admin/images.html', current_user=current_user, images=images)
    except Exception as e:
        logger.error(f"Get admin images error: {str(e)}")
        return render_template('admin/images.html', current_user=current_user, images=[])

@app.route('/backend/admin/stats')
@login_required_html
def admin_stats(current_user):
    if current_user.role < 1:  # 管理员及以上可访问
        return jsonify({'success': False, 'message': 'Insufficient permissions'}), 403
    # 获取统计数据
    stats = {
        'total_users': User.query.count(),
        'total_datasets': Dataset.query.count(),
        'total_images': Image.query.count(),
        'public_datasets': Dataset.query.filter_by(is_public=True).count(),
        'private_datasets': Dataset.query.filter_by(is_public=False).count()
    }
    return render_template('admin/stats.html', current_user=current_user, stats=stats)

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return create_response(True, "Service is healthy")

# Authentication routes
@app.route('/api/auth/register', methods=['POST'])
def register():
    try:
        data = request.get_json() or {}
        username = (data.get('username') or '').strip()
        email = (data.get('email') or '').strip()
        password = data.get('password') or ''

        if not username or not email or not password:
            return create_response(False, 'Username, email and password are required', status_code=400)

        UserService.register_user(username, email, password)
        return create_response(True, 'User registered successfully')
    except BadRequest as e:
        # 返回业务可读错误（如用户名或邮箱已存在）
        return create_response(False, str(e.description or e), status_code=400)
    except Exception as e:
        app.logger.error(f'Register error: {str(e)}')
        return create_response(False, 'Registration failed', status_code=500)

@app.route('/api/auth/login', methods=['POST'])
def login():
    """用户登录"""
    try:
        data = request.get_json()
        username_or_email = data.get('username_or_email')
        password = data.get('password')
        
        # 直接使用User模型查询和验证
        user = User.query.filter(
            (User.username == username_or_email) | (User.email == username_or_email)
        ).first()
        
        if user and user.check_password(password):
            # 检查用户是否被禁用
            if not user.is_active:
                return create_response(False, 'Account is disabled', status_code=401)
            
            # 生成JWT token
            token = jwt.encode({
                'user_id': user.id,
                'exp': datetime.utcnow() + timedelta(hours=24)
            }, app.config['JWT_SECRET_KEY'], algorithm="HS256")
            
            return create_response(True, 'Login successful', {
                'token': token,
                'user': user.to_dict()
            })
        else:
            return create_response(False, 'Invalid credentials', status_code=401)
    except Exception as e:
        app.logger.error(f'Login error: {str(e)}')
        return create_response(False, 'Login failed', status_code=500)

@app.route('/api/auth/logout', methods=['POST'])
@token_required
def logout(current_user):
    """用户登出"""
    # 在JWT系统中，服务器端通常不做特殊处理，客户端只需删除token
    # 但我们仍可以做一些清理工作
    try:
        # 可以在这里添加一些登出相关的日志记录等
        return create_response(True, 'Logout successful')
    except Exception as e:
        app.logger.error(f'Logout error: {str(e)}')
        return create_response(False, 'Logout failed', status_code=500)

@app.route('/api/users/profile', methods=['GET'])
@token_required
def get_user_profile(current_user):
    return jsonify({
        'success': True,
        'data': current_user.to_dict()
    })

@app.route('/api/users/<int:user_id>', methods=['GET'])
@token_required
def get_user(current_user, user_id):
    """获取用户信息"""
    try:
        # 用户可以获取自己的信息，管理员可以获取任意用户信息
        if current_user.id != user_id and current_user.role < 1:
            return create_response(False, 'Insufficient permissions', status_code=403)
        
        user = UserService.get_user_by_id(user_id)
        if user:
            return create_response(True, 'User retrieved', user)
        else:
            return create_response(False, 'User not found', status_code=404)
    except Exception as e:
        logger.error(f"Get user error: {str(e)}")
        return create_response(False, 'Internal server error', status_code=500)

@app.route('/api/users/<int:user_id>', methods=['PUT'])
@token_required
def update_user(current_user, user_id):
    """修改用户信息"""
    try:
        # 用户可以修改自己的信息，管理员可以修改任意用户信息
        if current_user.id != user_id and current_user.role < 1:
            return create_response(False, 'Insufficient permissions', status_code=403)
        
        data = request.get_json()
        if not data:
            return create_response(False, 'No data provided', status_code=400)
        
        # 验证可更新的字段
        allowed_fields = ['email', 'username']
        update_data = {k: v for k, v in data.items() if k in allowed_fields}
        
        # 不允许修改密码，需要单独的接口
        if 'password' in data:
            return create_response(False, 'Password update requires separate endpoint', status_code=400)
        
        user = UserService.update_user(user_id, update_data)
        return create_response(True, 'User updated successfully', user)
    except Exception as e:
        logger.error(f"Update user error: {str(e)}")
        return create_response(False, 'Internal server error', status_code=500)

# Dataset routes
@app.route('/api/datasets', methods=['POST'])
@token_required
def create_dataset(current_user):
    try:
        data = request.get_json()
        name = data.get('name')
        description = data.get('description')
        category = data.get('category', 'detection')
        
        # 修复参数顺序：name, description, created_by, category
        dataset = DatasetService.create_dataset(name, description, current_user.id, category)
        if dataset:
            return jsonify({
                'success': True,
                'message': 'Dataset created successfully',
                'data': dataset
            }), 201
        else:
            return jsonify({'success': False, 'message': 'Failed to create dataset'}), 500
    except Exception as e:
        app.logger.error(f'Create dataset error: {str(e)}')
        return jsonify({'success': False, 'message': 'Failed to create dataset'}), 500

@app.route('/api/datasets', methods=['GET'])
@token_required
def get_datasets(current_user):
    try:
        datasets = DatasetService.get_datasets_by_user(current_user.id)
        return jsonify({
            'success': True,
            'data': datasets  # 直接返回，因为DatasetService已经返回了字典列表
        })
    except Exception as e:
        app.logger.error(f'Get datasets error: {str(e)}')
        return jsonify({'success': False, 'message': 'Failed to get datasets'})

@app.route('/api/datasets/<int:dataset_id>', methods=['GET'])
@token_required
def get_dataset(current_user, dataset_id):
    try:
        dataset = DatasetService.get_dataset_by_id(dataset_id)
        if dataset:
            # 仅创建者、管理员或公开数据集可查看
            if dataset['created_by'] != current_user.id and not dataset.get('is_public', False) and current_user.role < 1:
                return create_response(False, "Permission denied", status_code=403)
            return create_response(True, "Dataset retrieved", dataset)
        return create_response(False, "Dataset not found", status_code=404)
    except Exception as e:
        logger.error(f"Get dataset error: {str(e)}")
        return create_response(False, "Internal server error", status_code=500)

@app.route('/api/datasets/<int:dataset_id>', methods=['PUT'])
@token_required
def update_dataset(current_user, dataset_id):
    """修改数据集"""
    try:
        data = request.get_json()
        if not data:
            return create_response(False, 'No data provided', status_code=400)
        
        dataset = DatasetService.update_dataset(dataset_id, current_user.id, data)
        return create_response(True, "Dataset updated", dataset)
    except Exception as e:
        logger.error(f"Update dataset error: {str(e)}")
        return create_response(False, "Internal server error", status_code=500)

@app.route('/api/datasets/<int:dataset_id>', methods=['DELETE'])
@token_required
def delete_dataset(current_user, dataset_id):
    """删除数据集"""
    try:
        success = DatasetService.delete_dataset(dataset_id, current_user.id)
        if success:
            return create_response(True, "Dataset deleted")
        else:
            return create_response(False, "Dataset not found or access denied", status_code=403)
    except BadRequest as e:
        return create_response(False, str(e), status_code=400)
    except Exception as e:
        logger.error(f"Delete dataset error: {str(e)}")
        return create_response(False, "Internal server error", status_code=500)


@app.route('/api/datasets/<int:dataset_id>/label-categories', methods=['GET'])
@token_required
def get_dataset_label_categories(current_user, dataset_id):
    try:
        dataset = Dataset.query.get(dataset_id)
        if not dataset:
            return create_response(False, "Dataset not found", status_code=404)

        if dataset.created_by != current_user.id and not dataset.is_public and current_user.role < 1:
            return create_response(False, "Permission denied", status_code=403)

        categories = DatasetService.get_label_categories(dataset_id)
        return create_response(True, "Label categories retrieved", {
            'dataset_id': dataset_id,
            'categories': categories
        })
    except Exception as e:
        logger.error(f"Get dataset label categories error: {str(e)}")
        return create_response(False, "Internal server error", status_code=500)


@app.route('/api/datasets/<int:dataset_id>/label-categories', methods=['POST'])
@token_required
def add_dataset_label_category(current_user, dataset_id):
    try:
        dataset = Dataset.query.get(dataset_id)
        if not dataset:
            return create_response(False, "Dataset not found", status_code=404)

        if dataset.created_by != current_user.id and current_user.role < 1:
            return create_response(False, "Permission denied", status_code=403)

        data = request.get_json() or {}
        name = data.get('name')
        if not name or not str(name).strip():
            return create_response(False, "name is required", status_code=400)

        categories = DatasetService.add_label_category(dataset_id, name)
        return create_response(True, "Label category added", {
            'dataset_id': dataset_id,
            'categories': categories
        }, status_code=201)
    except BadRequest as e:
        return create_response(False, str(e), status_code=400)
    except Exception as e:
        logger.error(f"Add dataset label category error: {str(e)}")
        return create_response(False, "Internal server error", status_code=500)


@app.route('/api/datasets/<int:dataset_id>/label-categories', methods=['DELETE'])
@token_required
def delete_dataset_label_category(current_user, dataset_id):
    try:
        dataset = Dataset.query.get(dataset_id)
        if not dataset:
            return create_response(False, "Dataset not found", status_code=404)

        if dataset.created_by != current_user.id and current_user.role < 1:
            return create_response(False, "Permission denied", status_code=403)

        data = request.get_json(silent=True) or {}
        name = data.get('name')
        if not name or not str(name).strip():
            return create_response(False, "name is required", status_code=400)

        categories = DatasetService.remove_label_category(dataset_id, name)
        return create_response(True, "Label category deleted", {
            'dataset_id': dataset_id,
            'categories': categories
        })
    except BadRequest as e:
        return create_response(False, str(e), status_code=400)
    except Exception as e:
        logger.error(f"Delete dataset label category error: {str(e)}")
        return create_response(False, "Internal server error", status_code=500)

@app.route('/api/datasets/<int:dataset_id>/images', methods=['GET'])
@token_required
def get_dataset_images(current_user, dataset_id):
    try:
        dataset = Dataset.query.get(dataset_id)
        if not dataset:
            return create_response(False, "Dataset not found", status_code=404)

        if dataset.created_by != current_user.id and not dataset.is_public and current_user.role < 1:
            return create_response(False, "Permission denied", status_code=403)

        images = DatasetService.get_images_in_dataset(dataset_id)
        return create_response(True, "Images retrieved", images)
    except Exception as e:
        logger.error(f"Get dataset images error: {str(e)}")
        return create_response(False, "Internal server error", status_code=500)

@app.route('/api/datasets/<int:dataset_id>/upload', methods=['POST'])
@token_required
def upload_image(current_user, dataset_id):
    try:
        # 检查数据集是否属于当前用户或公开
        dataset = Dataset.query.get(dataset_id)
        if not dataset or (dataset.created_by != current_user.id and not dataset.is_public):
            return jsonify({'success': False, 'message': 'Access denied'}), 403

        if 'file' not in request.files and 'image' not in request.files:
            return jsonify({'success': False, 'message': 'No file part'}), 400

        file = request.files.get('file') or request.files.get('image')
        
        if file.filename == '':
            return jsonify({'success': False, 'message': 'No selected file'}), 400
            
        if file and allowed_file(file.filename):
            raw_filename = str(file.filename or '').replace('\\', '/')
            base_filename = os.path.basename(raw_filename)
            filename = secure_filename(base_filename)
            timestamp = int(datetime.utcnow().timestamp())
            unique_filename = f"{timestamp}_{filename}"

            safe_username = secure_filename(current_user.username) or f"user_{current_user.id}"
            safe_dataset_name = secure_filename(dataset.name) or f"dataset_{dataset.id}"
            dataset_folder = os.path.join(app.config['DATASETS_FOLDER'], safe_username, f"{safe_dataset_name}_{dataset.id}")
            os.makedirs(dataset_folder, exist_ok=True)

            file_path = os.path.join(dataset_folder, unique_filename)
            file.save(file_path)

            try:
                with PILImage.open(file_path) as uploaded_image:
                    width, height = uploaded_image.size
            except (UnidentifiedImageError, OSError):
                if os.path.exists(file_path):
                    os.remove(file_path)
                return jsonify({'success': False, 'message': 'Failed to read image dimensions'}), 400

            try:
                image = ImageService.create_image(
                    original_filename=filename,
                    filename=unique_filename,
                    dataset_id=dataset_id,
                    uploaded_by=current_user.id,
                    file_path=file_path,
                    file_size=os.path.getsize(file_path),
                    width=width,
                    height=height
                )
            except Exception:
                # Keep filesystem and DB consistent when metadata persistence fails.
                if os.path.exists(file_path):
                    os.remove(file_path)
                raise
            
            if image:
                return jsonify({
                    'success': True,
                    'message': 'File uploaded successfully',
                    'data': image.to_dict()
                }), 201
            else:
                if os.path.exists(file_path):
                    os.remove(file_path)
                return jsonify({'success': False, 'message': 'Failed to save image record'}), 500
        else:
            return jsonify({'success': False, 'message': 'File type not allowed'}), 400
    except Exception as e:
        app.logger.error(f'Upload image error: {str(e)}')
        return jsonify({'success': False, 'message': 'Upload failed'}), 500

# Image routes
@app.route('/api/images/<int:image_id>', methods=['GET'])
@token_required
def get_image(current_user, image_id):
    try:
        image = ImageService.get_image_by_id(image_id)
        if image:
            return create_response(True, "Image retrieved", image)
        return create_response(False, "Image not found", status_code=404)
    except Exception as e:
        logger.error(f"Get image error: {str(e)}")
        return create_response(False, "Internal server error", status_code=500)


@app.route('/api/images/<int:image_id>/content', methods=['GET'])
@token_required
def get_image_content(current_user, image_id):
    """按鉴权返回图片二进制内容，供手工标注页加载。"""
    try:
        image = Image.query.get(image_id)
        if not image:
            return create_response(False, "Image not found", status_code=404)

        dataset = Dataset.query.get(image.dataset_id)
        if not dataset:
            return create_response(False, "Dataset not found", status_code=404)

        if image.uploaded_by != current_user.id and dataset.created_by != current_user.id and not dataset.is_public:
            return create_response(False, "Permission denied", status_code=403)

        if not image.file_path or not os.path.exists(image.file_path):
            return create_response(False, "Image file not found", status_code=404)

        return send_file(image.file_path)
    except Exception as e:
        logger.error(f"Get image content error: {str(e)}")
        return create_response(False, "Internal server error", status_code=500)

@app.route('/api/images/<int:image_id>', methods=['PUT'])
@token_required
def update_image(current_user, image_id):
    """修改图片信息"""
    try:
        image = Image.query.get(image_id)
        if not image:
            return create_response(False, "Image not found", status_code=404)
        
        # 检查权限
        if image.uploaded_by != current_user.id and current_user.role < 2:
            return create_response(False, "Permission denied", status_code=403)
        
        data = request.get_json()
        if not data:
            return create_response(False, "No data provided", status_code=400)
        
        # 允许更新的字段
        allowed_fields = ['original_filename']
        for key, value in data.items():
            if key in allowed_fields and hasattr(image, key):
                setattr(image, key, value)
        
        db.session.commit()
        return create_response(True, "Image updated", image.to_dict())
    except Exception as e:
        logger.error(f"Update image error: {str(e)}")
        return create_response(False, "Internal server error", status_code=500)

@app.route('/api/images/<int:image_id>', methods=['DELETE'])
@token_required
def delete_image(current_user, image_id):
    """删除图片"""
    try:
        image = Image.query.get(image_id)
        if not image:
            return create_response(False, "Image not found", status_code=404)

        dataset = Dataset.query.get(image.dataset_id)
        if not dataset:
            return create_response(False, "Dataset not found", status_code=404)
        
        # 检查权限
        if image.uploaded_by != current_user.id and dataset.created_by != current_user.id and current_user.role < 2:
            return create_response(False, "Permission denied", status_code=403)
        
        result = ImageService.delete_image_admin(image_id)
        return create_response(True, "Image deleted", result)
    except BadRequest as e:
        return create_response(False, str(e), status_code=400)
    except Exception as e:
        logger.error(f"Delete image error: {str(e)}")
        return create_response(False, "Internal server error", status_code=500)

@app.route('/api/images/<int:image_id>/annotations', methods=['PUT'])
@token_required
def update_annotations(current_user, image_id):
    try:
        image_row = Image.query.get(image_id)
        if not image_row:
            return create_response(False, "Image not found", status_code=404)

        dataset = Dataset.query.get(image_row.dataset_id)
        if not dataset:
            return create_response(False, "Dataset not found", status_code=404)

        if image_row.uploaded_by != current_user.id and dataset.created_by != current_user.id and current_user.role < 1:
            return create_response(False, "Permission denied", status_code=403)

        data = request.get_json() or {}
        if 'annotations' not in data:
            return create_response(False, "annotations is required", status_code=400)

        image = ImageService.update_image_annotations(image_id, data['annotations'])
        return create_response(True, "Annotations updated", image)
    except BadRequest as e:
        return create_response(False, str(e), status_code=400)
    except Exception as e:
        logger.error(f"Update annotations error: {str(e)}")
        return create_response(False, "Internal server error", status_code=500)

# New annotation routes
@app.route('/api/images/<int:image_id>/annotations', methods=['GET'])
@token_required
def get_annotations(current_user, image_id):
    try:
        image_row = Image.query.get(image_id)
        if not image_row:
            return create_response(False, "Image not found", status_code=404)

        dataset = Dataset.query.get(image_row.dataset_id)
        if not dataset:
            return create_response(False, "Dataset not found", status_code=404)

        if image_row.uploaded_by != current_user.id and dataset.created_by != current_user.id and not dataset.is_public and current_user.role < 1:
            return create_response(False, "Permission denied", status_code=403)

        annotations = ImageService.get_annotations_by_image(image_id)
        return create_response(True, "Annotation file retrieved", annotations)
    except Exception as e:
        logger.error(f"Get annotations error: {str(e)}")
        return create_response(False, "Internal server error", status_code=500)

@app.route('/api/images/<int:image_id>/annotations', methods=['POST'])
@token_required
def add_annotation(current_user, image_id):
    try:
        image_row = Image.query.get(image_id)
        if not image_row:
            return create_response(False, "Image not found", status_code=404)

        dataset = Dataset.query.get(image_row.dataset_id)
        if not dataset:
            return create_response(False, "Dataset not found", status_code=404)

        if image_row.uploaded_by != current_user.id and dataset.created_by != current_user.id and current_user.role < 1:
            return create_response(False, "Permission denied", status_code=403)

        data = request.get_json() or {}
        required_fields = ['label', 'x_min', 'y_min', 'x_max', 'y_max']
        missing = [field for field in required_fields if field not in data]
        if missing:
            return create_response(False, f"Missing fields: {', '.join(missing)}", status_code=400)

        annotation = ImageService.add_annotation(
            image_id=image_id,
            label=data['label'],
            x_min=data['x_min'],
            y_min=data['y_min'],
            x_max=data['x_max'],
            y_max=data['y_max'],
            confidence=data.get('confidence', 1.0)
        )
        return create_response(True, "Annotation added", annotation, status_code=201)
    except BadRequest as e:
        return create_response(False, str(e), status_code=400)
    except Exception as e:
        logger.error(f"Add annotation error: {str(e)}")
        return create_response(False, "Internal server error", status_code=500)


@app.route('/api/images/<int:image_id>/label-file', methods=['POST'])
@token_required
def save_image_label_file(current_user, image_id):
    """将当前图片标注导出为COCO文件并写入 images.annotations_path。"""
    try:
        image_row = Image.query.get(image_id)
        if not image_row:
            return create_response(False, "Image not found", status_code=404)

        dataset = Dataset.query.get(image_row.dataset_id)
        if not dataset:
            return create_response(False, "Dataset not found", status_code=404)

        # 仅上传者、数据集创建者或管理员可写标签文件。
        if image_row.uploaded_by != current_user.id and dataset.created_by != current_user.id and current_user.role < 1:
            return create_response(False, "Permission denied", status_code=403)

        data = request.get_json(silent=True) or {}
        classes = data.get('classes', [])
        annotations = data.get('annotations')
        if classes is not None and not isinstance(classes, list):
            return create_response(False, "classes must be a list", status_code=400)
        if annotations is not None and not isinstance(annotations, list):
            return create_response(False, "annotations must be a list", status_code=400)

        result = ImageService.save_label_file(image_id, classes=classes, annotations=annotations)
        return create_response(True, "Label file saved", result)
    except BadRequest as e:
        return create_response(False, str(e), status_code=400)
    except Exception as e:
        logger.error(f"Save image label file error: {str(e)}")
        return create_response(False, "Internal server error", status_code=500)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

# Admin routes
@app.route('/admin')
@login_required_html
def admin_dashboard(current_user):
    if current_user.role < 1:  # 至少是管理员才能访问
        return jsonify({'success': False, 'message': 'Access denied'}), 403
    
    try:
        stats = {
            'total_users': UserService.get_user_count(),
            'total_datasets': DatasetService.get_dataset_count(),
            'total_images': ImageService.get_image_count(),
            'public_datasets': DatasetService.get_public_dataset_count()
        }
        return render_template('admin/dashboard.html', stats=stats, current_user=current_user)
    except Exception as e:
        app.logger.error(f'Get dashboard stats error: {str(e)}')
        stats = {}
        return render_template('admin/dashboard.html', stats=stats, current_user=current_user)

@app.route('/admin/users')
@login_required_html
def admin_users_page(current_user):
    if current_user.role < 2:  # 超级管理员才能访问
        return jsonify({'success': False, 'message': 'Access denied'}), 403
    
    users = UserService.get_all_users()
    return render_template('admin/users.html', users=[user.to_admin_dict() for user in users], current_user=current_user)

@app.route('/admin/datasets')
@login_required_html
def admin_datasets_page(current_user):
    if current_user.role < 2:  # 超级管理员才能访问
        return jsonify({'success': False, 'message': 'Access denied'}), 403

    datasets = Dataset.query.all()
    for dataset in datasets:
        dataset.owner_username = dataset.creator.username if dataset.creator else 'Unknown'
        dataset.image_count = len(dataset.images) if dataset.images is not None else 0

    return render_template('admin/datasets.html', datasets=datasets, current_user=current_user)

@app.route('/admin/images')
@login_required_html
def admin_images_page(current_user):
    """图片管理页面"""
    if current_user.role < 2:  # 超级管理员才能访问
        return jsonify({'success': False, 'message': 'Access denied'}), 403
    
    try:
        images = ImageService.get_all_images()
        return render_template('admin/images.html', images=images)
    except Exception as e:
        logger.error(f"Get images error: {str(e)}")
        return render_template('admin/images.html', images=[])

@app.route('/admin/stats')
@login_required_html
def admin_stats_page(current_user):
    """统计信息页面"""
    if current_user.role < 2:  # 超级管理员才能访问
        return jsonify({'success': False, 'message': 'Access denied'}), 403
    
    try:
        stats = {
            'total_users': UserService.get_user_count(),
            'total_datasets': DatasetService.get_dataset_count(),
            'total_images': ImageService.get_image_count(),
            'public_datasets': DatasetService.get_public_dataset_count()
        }
        return render_template('admin/stats.html', stats=stats)
    except Exception as e:
        logger.error(f"Get stats error: {str(e)}")
        return render_template('admin/stats.html', stats={})

# API routes for admin operations
@app.route('/api/admin/users', methods=['GET'])
@token_required
def get_admin_users(current_user):
    """获取用户列表（管理员）"""
    try:
        if current_user.role < 1:
            return create_response(False, "Insufficient permissions", status_code=403)

        users = UserService.get_all_users()
        return create_response(True, "Users retrieved", users)
    except Exception as e:
        logger.error(f"Get admin users error: {str(e)}")
        return create_response(False, "Internal server error", status_code=500)

@app.route('/api/admin/users/<int:user_id>/toggle-status', methods=['POST'])
@token_required
def toggle_user_status(current_user, user_id):
    """切换用户状态（需要管理员权限）"""
    try:
        # 检查当前用户是否为管理员或超级管理员
        if current_user.role < 1:
            return create_response(False, "Insufficient permissions", status_code=403)
        
        user = UserService.toggle_user_status(user_id)
        return create_response(True, "User status updated", user)
    except Exception as e:
        logger.error(f"Toggle user status error: {str(e)}")
        return create_response(False, "Internal server error", status_code=500)

@app.route('/api/admin/datasets/<int:dataset_id>/toggle-public', methods=['POST'])
@token_required
def toggle_dataset_public(current_user, dataset_id):
    """切换数据集公开状态"""
    try:
        if current_user.role < 1:
            return create_response(False, "Insufficient permissions", status_code=403)
        dataset = DatasetService.toggle_dataset_public(dataset_id)
        return create_response(True, "Dataset visibility updated", dataset)
    except Exception as e:
        logger.error(f"Toggle dataset public error: {str(e)}")
        return create_response(False, "Internal server error", status_code=500)

@app.route('/api/admin/images/<int:image_id>/delete', methods=['DELETE'])
@token_required
def delete_image_admin(current_user, image_id):
    """删除图片（管理员）"""
    try:
        if current_user.role < 1:
            return create_response(False, "Insufficient permissions", status_code=403)
        result = ImageService.delete_image_admin(image_id)
        return create_response(True, "Image deleted", result)
    except Exception as e:
        logger.error(f"Delete image error: {str(e)}")
        return create_response(False, "Internal server error", status_code=500)

# User management API routes (增删改查)
@app.route('/api/admin/users/<int:user_id>', methods=['GET'])
@token_required
def get_user_admin(current_user, user_id):
    """获取用户详情（管理员）"""
    try:
        # 检查当前用户是否为管理员或超级管理员
        if current_user.role < 1:
            return create_response(False, "Insufficient permissions", status_code=403)
        
        user = UserService.get_user_by_id(user_id)
        if user:
            return create_response(True, "User retrieved", user)
        return create_response(False, "User not found", status_code=404)
    except Exception as e:
        logger.error(f"Get user error: {str(e)}")
        return create_response(False, "Internal server error", status_code=500)

@app.route('/api/admin/users/<int:user_id>', methods=['PUT'])
@token_required
def update_user_admin(current_user, user_id):
    """更新用户信息（管理员）"""
    try:
        # 检查当前用户是否为管理员或超级管理员
        if current_user.role < 1:
            return create_response(False, "Insufficient permissions", status_code=403)
        
        data = request.get_json()
        if not data:
            return create_response(False, "No data provided", status_code=400)
        
        # 只允许更新这些字段
        allowed_fields = ['email', 'username', 'is_active']
        update_data = {k: v for k, v in data.items() if k in allowed_fields}
        
        user = UserService.update_user(user_id, update_data)
        return create_response(True, "User updated successfully", user)
    except BadRequest as e:
        return create_response(False, str(e), status_code=400)
    except Exception as e:
        logger.error(f"Update user error: {str(e)}")
        return create_response(False, "Internal server error", status_code=500)

@app.route('/api/admin/users/<int:user_id>', methods=['DELETE'])
@token_required
def delete_user_admin(current_user, user_id):
    """删除用户（管理员）"""
    try:
        # 检查当前用户是否为管理员或超级管理员
        if current_user.role < 1:
            return create_response(False, "Insufficient permissions", status_code=403)
        
        # 防止删除自己
        if current_user.id == user_id:
            return create_response(False, "Cannot delete yourself", status_code=400)
        
        UserService.delete_user(user_id)
        return create_response(True, "User deleted successfully")
    except BadRequest as e:
        return create_response(False, str(e), status_code=400)
    except Exception as e:
        logger.error(f"Delete user error: {str(e)}")
        return create_response(False, "Internal server error", status_code=500)

@app.route('/api/ai/inference', methods=['POST'])
@token_required
def ai_inference(current_user):
    """AI推理接口：对上传的图片进行目标检测并返回标注结果"""
    try:
        # 这里需要集成AI推理服务
        # 为了演示目的，我们返回模拟的结果
        # 在实际实现中，需要调用pytorch_model/inference.py中的推理逻辑
        if 'image' not in request.files:
            return create_response(False, "No image provided", status_code=400)
        
        file = request.files['image']
        if file.filename == '':
            return create_response(False, "No image selected", status_code=400)
        
        if file and allowed_file(file.filename):
            # 临时保存文件用于推理
            temp_filename = secure_filename(f"temp_{datetime.utcnow().timestamp()}_{file.filename}")
            temp_path = os.path.join(app.config['UPLOAD_FOLDER'], temp_filename)
            file.save(temp_path)
            
            # 在实际实现中，这里会调用AI模型进行推理
            # from pytorch_model.inference import InferenceEngine
            # engine = InferenceEngine(model_path="/app/pytorch_model/weights/yolov5s.pt")
            # results = engine.inference_image(temp_path)
            
            # 模拟AI推理结果
            simulated_results = [
                {
                    'label': 'person',
                    'bbox': [100, 100, 200, 300],
                    'confidence': 0.95,
                    'class_id': 0
                },
                {
                    'label': 'car',
                    'bbox': [300, 200, 500, 400],
                    'confidence': 0.89,
                    'class_id': 2
                }
            ]
            
            # 删除临时文件
            os.remove(temp_path)
            
            return create_response(True, "Inference completed", simulated_results)
        else:
            return create_response(False, "Invalid file type", status_code=400)
    except Exception as e:
        logger.error(f"AI inference error: {str(e)}")
        return create_response(False, "Internal server error", status_code=500)

@app.route('/api/endpoints')
def api_endpoints():
    endpoints = {
        "认证": [
            {"method": "POST", "path": "/api/auth/register", "description": "用户注册"},
            {"method": "POST", "path": "/api/auth/login", "description": "用户登录"},
            {"method": "GET", "path": "/api/users/profile", "description": "获取用户资料"}
        ],
        "用户管理": [
            {"method": "GET", "path": "/api/users/{id}", "description": "查看用户信息"},
            {"method": "PUT", "path": "/api/users/{id}", "description": "修改用户信息"},
            {"method": "POST", "path": "/api/auth/logout", "description": "用户退出"}
        ],
        "数据集管理": [
            {"method": "GET", "path": "/api/datasets", "description": "查看用户数据集列表"},
            {"method": "POST", "path": "/api/datasets", "description": "创建新数据集"},
            {"method": "GET", "path": "/api/datasets/{id}", "description": "查看指定数据集"},
            {"method": "PUT", "path": "/api/datasets/{id}", "description": "修改数据集"},
            {"method": "DELETE", "path": "/api/datasets/{id}", "description": "删除数据集"}
        ],
        "数据管理": [
            {"method": "GET", "path": "/api/images/{id}", "description": "查看指定图片"},
            {"method": "PUT", "path": "/api/images/{id}", "description": "修改图片信息"},
            {"method": "DELETE", "path": "/api/images/{id}", "description": "删除图片"},
            {"method": "POST", "path": "/api/datasets/{id}/upload", "description": "上传图片到指定数据集"}
        ],
        "数据标注": [
            {"method": "GET", "path": "/api/images/{id}/annotations", "description": "查看图片标注"},
            {"method": "POST", "path": "/api/images/{id}/annotations", "description": "添加标注"},
            {"method": "PUT", "path": "/api/images/{id}/annotations", "description": "覆盖图片标注"},
            {"method": "POST", "path": "/api/images/{id}/label-file", "description": "生成COCO标注文件并记录路径"}
        ],
        "AI推理": [
            {"method": "POST", "path": "/api/ai/inference", "description": "AI推理接口，接收图片返回标注结果"}
        ]
    }
    return jsonify(endpoints)

@app.route('/backend/api_endpoints.json')
def api_endpoints_json():
    """提供API端点定义的JSON文件"""
    return send_from_directory(app.root_path, 'api_endpoints.json')

@app.route('/backend/login', methods=['POST'])
def backend_login():
    """后端管理系统登录接口"""
    try:
        data = request.get_json()
        username_or_email = data.get('username_or_email')
        password = data.get('password')
        
        # 首先验证用户身份
        user = User.query.filter(
            (User.username == username_or_email) | (User.email == username_or_email)
        ).first()
        
        if user and user.check_password(password):
            # 检查用户是否具有管理员权限 (role >= 1)
            if user.role < 1:
                return create_response(False, 'Insufficient permissions for backend access', status_code=403)
            
            token = jwt.encode({
                'user_id': user.id,
                'exp': datetime.utcnow() + timedelta(hours=24)
            }, app.config['JWT_SECRET_KEY'], algorithm="HS256")
            
            return create_response(True, 'Backend login successful', {
                'token': token,
                'user': user.to_dict()
            })
        else:
            return create_response(False, 'Invalid credentials', status_code=401)
    except Exception as e:
        app.logger.error(f'Backend login error: {str(e)}')
        return create_response(False, 'Login failed', status_code=500)

@app.route('/backend/set-session-token', methods=['POST'])
@token_required
def set_session_token(current_user):
    """将JWT token存储到session中，供HTML页面使用"""
    try:
        # 将用户的token存储到session中
        session['auth_token'] = request.headers.get('Authorization').split(' ')[1]
        return create_response(True, 'Session token set successfully')
    except Exception as e:
        logger.error(f"Set session token error: {str(e)}")
        return create_response(False, 'Failed to set session token', status_code=500)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)