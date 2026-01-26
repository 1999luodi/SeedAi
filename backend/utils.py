import os
import uuid
from werkzeug.utils import secure_filename
from flask import current_app
import jwt
from datetime import datetime, timedelta

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def generate_unique_filename(original_filename):
    ext = original_filename.rsplit('.', 1)[1].lower() if '.' in original_filename else ''
    unique_name = str(uuid.uuid4())
    return f"{unique_name}.{ext}" if ext else unique_name

def save_uploaded_file(file, folder):
    if not allowed_file(file.filename):
        raise ValueError("File type not allowed")
    
    filename = secure_filename(file.filename)
    unique_filename = generate_unique_filename(filename)
    file_path = os.path.join(current_app.config[folder], unique_filename)
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    file.save(file_path)
    return unique_filename, file_path

def generate_token(user_id):
    payload = {
        'user_id': user_id,
        'exp': datetime.utcnow() + timedelta(days=1),
        'iat': datetime.utcnow()
    }
    return jwt.encode(payload, current_app.config['JWT_SECRET_KEY'], algorithm='HS256')

def decode_token(token):
    try:
        payload = jwt.decode(token, current_app.config['JWT_SECRET_KEY'], algorithms=['HS256'])
        return payload['user_id']
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

def create_response(success=True, message="", data=None, status_code=200):
    response = {
        'success': success,
        'message': message
    }
    if data is not None:
        response['data'] = data
    return response, status_code
