from flask import Flask, jsonify, request, send_from_directory, render_template, redirect, url_for, flash
from flask_cors import CORS
import logging
import os
from models import db
from config import Config
from utils import decode_token, create_response, save_uploaded_file
from services.user_service import UserService
from services.dataset_service import DatasetService
from services.image_service import ImageService
from werkzeug.exceptions import BadRequest

app = Flask(__name__,
            template_folder='templates',
            static_folder=os.path.join(os.path.dirname(__file__), '..', 'frontend'),
            static_url_path='/static')
app.config.from_object(Config)
app.secret_key = 'seedai-admin-secret-key-2024'  # 用于session管理
CORS(app)

db.init_app(app)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create upload directories
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['DATASETS_FOLDER'], exist_ok=True)

def token_required(f):
    def decorated_function(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return create_response(False, "Token is missing", status_code=401)
        user_id = decode_token(token.replace('Bearer ', ''))
        if not user_id:
            return create_response(False, "Token is invalid", status_code=401)
        request.user_id = user_id
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return create_response(True, "Service is healthy")

# User routes
@app.route('/api/auth/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        user = UserService.register_user(data['username'], data['email'], data['password'])
        return create_response(True, "User registered successfully", user, 201)
    except BadRequest as e:
        return create_response(False, str(e), status_code=400)
    except Exception as e:
        logger.error(f"Registration error: {str(e)}")
        return create_response(False, "Internal server error", status_code=500)

@app.route('/api/auth/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        result = UserService.authenticate_user(data['username_or_email'], data['password'])
        if result:
            return create_response(True, "Login successful", result)
        return create_response(False, "Invalid credentials", status_code=401)
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        return create_response(False, "Internal server error", status_code=500)

@app.route('/api/users/profile', methods=['GET'])
@token_required
def get_profile():
    try:
        user = UserService.get_user_by_id(request.user_id)
        if user:
            return create_response(True, "Profile retrieved", user)
        return create_response(False, "User not found", status_code=404)
    except Exception as e:
        logger.error(f"Get profile error: {str(e)}")
        return create_response(False, "Internal server error", status_code=500)

# Dataset routes
@app.route('/api/datasets', methods=['POST'])
@token_required
def create_dataset():
    try:
        data = request.get_json()
        dataset = DatasetService.create_dataset(data['name'], data.get('description', ''), request.user_id)
        return create_response(True, "Dataset created", dataset, 201)
    except BadRequest as e:
        return create_response(False, str(e), status_code=400)
    except Exception as e:
        logger.error(f"Create dataset error: {str(e)}")
        return create_response(False, "Internal server error", status_code=500)

@app.route('/api/datasets', methods=['GET'])
@token_required
def get_datasets():
    try:
        datasets = DatasetService.get_datasets_by_user(request.user_id)
        return create_response(True, "Datasets retrieved", datasets)
    except Exception as e:
        logger.error(f"Get datasets error: {str(e)}")
        return create_response(False, "Internal server error", status_code=500)

@app.route('/api/datasets/<int:dataset_id>', methods=['GET'])
@token_required
def get_dataset(dataset_id):
    try:
        dataset = DatasetService.get_dataset_by_id(dataset_id)
        if dataset:
            return create_response(True, "Dataset retrieved", dataset)
        return create_response(False, "Dataset not found", status_code=404)
    except Exception as e:
        logger.error(f"Get dataset error: {str(e)}")
        return create_response(False, "Internal server error", status_code=500)

@app.route('/api/datasets/<int:dataset_id>/images', methods=['GET'])
@token_required
def get_dataset_images(dataset_id):
    try:
        images = DatasetService.get_images_in_dataset(dataset_id)
        return create_response(True, "Images retrieved", images)
    except Exception as e:
        logger.error(f"Get dataset images error: {str(e)}")
        return create_response(False, "Internal server error", status_code=500)

@app.route('/api/datasets/<int:dataset_id>/upload', methods=['POST'])
@token_required
def upload_image(dataset_id):
    try:
        if 'file' not in request.files:
            return create_response(False, "No file provided", status_code=400)
        
        file = request.files['file']
        if file.filename == '':
            return create_response(False, "No file selected", status_code=400)
        
        filename, file_path = save_uploaded_file(file, 'UPLOAD_FOLDER')
        image = DatasetService.add_image_to_dataset(
            dataset_id, filename, file.filename, request.user_id, file_path
        )
        return create_response(True, "Image uploaded", image, 201)
    except BadRequest as e:
        return create_response(False, str(e), status_code=400)
    except Exception as e:
        logger.error(f"Upload image error: {str(e)}")
        return create_response(False, "Internal server error", status_code=500)

# Image routes
@app.route('/api/images/<int:image_id>', methods=['GET'])
@token_required
def get_image(image_id):
    try:
        image = ImageService.get_image_by_id(image_id)
        if image:
            return create_response(True, "Image retrieved", image)
        return create_response(False, "Image not found", status_code=404)
    except Exception as e:
        logger.error(f"Get image error: {str(e)}")
        return create_response(False, "Internal server error", status_code=500)

@app.route('/api/images/<int:image_id>/annotations', methods=['PUT'])
@token_required
def update_annotations(image_id):
    try:
        data = request.get_json()
        image = ImageService.update_image_annotations(image_id, data['annotations'])
        return create_response(True, "Annotations updated", image)
    except BadRequest as e:
        return create_response(False, str(e), status_code=400)
    except Exception as e:
        logger.error(f"Update annotations error: {str(e)}")
        return create_response(False, "Internal server error", status_code=500)

@app.route('/admin_test.html')
def admin_test_page():
    """管理后台测试页面"""
    return send_from_directory(os.path.join(app.root_path), 'admin_test.html')

@app.route('/admin')
def admin_dashboard():
    """管理后台首页"""
    try:
        stats = {
            'total_users': UserService.get_user_count(),
            'total_datasets': DatasetService.get_dataset_count(),
            'total_images': ImageService.get_image_count(),
            'public_datasets': DatasetService.get_public_dataset_count()
        }
        return render_template('admin/dashboard.html', stats=stats)
    except Exception as e:
        logger.error(f"Get dashboard stats error: {str(e)}")
        return render_template('admin/dashboard.html', stats={})

@app.route('/admin/users')
def admin_users():
    """用户管理页面"""
    try:
        users = UserService.get_all_users()
        return render_template('admin/users.html', users=users)
    except Exception as e:
        logger.error(f"Get users error: {str(e)}")
        flash('获取用户列表失败', 'error')
        return render_template('admin/users.html', users=[])

@app.route('/admin/datasets')
def admin_datasets():
    """数据集管理页面"""
    try:
        datasets = DatasetService.get_all_datasets()
        return render_template('admin/datasets.html', datasets=datasets)
    except Exception as e:
        logger.error(f"Get datasets error: {str(e)}")
        flash('获取数据集列表失败', 'error')
        return render_template('admin/datasets.html', datasets=[])

@app.route('/admin/images')
def admin_images():
    """图片管理页面"""
    try:
        images = ImageService.get_all_images()
        return render_template('admin/images.html', images=images)
    except Exception as e:
        logger.error(f"Get images error: {str(e)}")
        flash('获取图片列表失败', 'error')
        return render_template('admin/images.html', images=[])

@app.route('/admin/stats')
def admin_stats():
    """统计信息页面"""
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
        flash('获取统计信息失败', 'error')
        return render_template('admin/stats.html', stats={})

# API routes for admin operations
@app.route('/api/admin/users/<int:user_id>/toggle-status', methods=['POST'])
@token_required
def toggle_user_status(user_id):
    """切换用户状态（需要管理员权限）"""
    try:
        # 这里应该检查当前用户是否为管理员
        # 暂时跳过权限检查
        user = UserService.toggle_user_status(user_id)
        return create_response(True, "User status updated", user)
    except Exception as e:
        logger.error(f"Toggle user status error: {str(e)}")
        return create_response(False, "Internal server error", status_code=500)

@app.route('/api/admin/datasets/<int:dataset_id>/toggle-public', methods=['POST'])
@token_required
def toggle_dataset_public(dataset_id):
    """切换数据集公开状态"""
    try:
        dataset = DatasetService.toggle_dataset_public(dataset_id)
        return create_response(True, "Dataset visibility updated", dataset)
    except Exception as e:
        logger.error(f"Toggle dataset public error: {str(e)}")
        return create_response(False, "Internal server error", status_code=500)

@app.route('/api/admin/images/<int:image_id>/delete', methods=['DELETE'])
@token_required
def delete_image_admin(image_id):
    """删除图片（管理员）"""
    try:
        result = ImageService.delete_image(image_id)
        return create_response(True, "Image deleted", result)
    except Exception as e:
        logger.error(f"Delete image error: {str(e)}")
        return create_response(False, "Internal server error", status_code=500)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, host='0.0.0.0', port=5000)