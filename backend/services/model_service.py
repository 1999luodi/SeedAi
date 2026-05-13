from models import db, AIModelConfig
from werkzeug.exceptions import BadRequest
import glob
import os
import re


class AIModelService:
    @staticmethod
    def _strip_identifier(value):
        return str(value or '').strip()

    @staticmethod
    def _validate_model_name(model_name):
        cleaned_name = str(model_name or '').strip()
        if not cleaned_name:
            raise BadRequest('model_name is required')

        # model_name rule: <model>-<variety>, e.g. yolov5-soybean
        if not re.fullmatch(r'[A-Za-z0-9_]+-[A-Za-z0-9_]+', cleaned_name):
            raise BadRequest('model_name must be <model>-<variety>, e.g. yolov5-soybean')
        return cleaned_name

    @staticmethod
    def _build_service_model_path(model_name):
        variety = str(model_name).split('-', 1)[1]
        return f"/workspace/online/models/service/{variety}/{model_name}.onnx"

    @staticmethod
    def _normalize_model_path(model_name, model_path):
        expected = AIModelService._build_service_model_path(model_name)
        cleaned_path = str(model_path or '').strip()
        if cleaned_path and cleaned_path != expected:
            raise BadRequest(f'model_path must match naming rule: {expected}')
        return expected

    @staticmethod
    def list_models():
        rows = AIModelConfig.query.order_by(AIModelConfig.created_at.desc()).all()
        return [item.to_dict() for item in rows]

    @staticmethod
    def get_model_by_id(model_id):
        row = AIModelConfig.query.get(model_id)
        return row.to_dict() if row else None

    @staticmethod
    def get_model_by_name(model_name):
        if not model_name:
            return None
        return AIModelConfig.query.filter_by(model_name=str(model_name).strip()).first()

    @staticmethod
    def get_model_by_identifier(model_identifier):
        """Resolve model by model_name or ONNX filename (e.g. faster-rcnn.onnx)."""
        cleaned = AIModelService._strip_identifier(model_identifier)
        if not cleaned:
            return None

        exact = AIModelService.get_model_by_name(cleaned)
        if exact:
            return exact

        file_name = os.path.basename(cleaned)
        if file_name.lower().endswith('.onnx'):
            by_path = AIModelConfig.query.filter(AIModelConfig.model_path.ilike(f"%/{file_name}")).first()
            if by_path:
                return by_path

            stem = file_name[:-5]
            # Support naming variants like faster-rcnn <-> faster-rcnn-soybean.
            by_prefix = AIModelConfig.query.filter(AIModelConfig.model_name.like(f"{stem}-%")).first()
            if by_prefix:
                return by_prefix

        return None

    @staticmethod
    def resolve_workspace_model_path(model_identifier):
        """Resolve ai_worker model path for filename identifiers.

        1) Try filesystem lookup when backend mounts /workspace.
        2) If backend cannot see /workspace, infer a service path so ai_worker can still load it.
        """
        cleaned = AIModelService._strip_identifier(model_identifier)
        if not cleaned:
            return None

        file_name = os.path.basename(cleaned)
        if not file_name.lower().endswith('.onnx'):
            file_name = f"{file_name}.onnx"

        model_root = os.environ.get('AI_WORKER_MODEL_ROOT', '/workspace/online/models/service').rstrip('/')
        pattern = f"{model_root}/**/{file_name}"
        matched = sorted(glob.glob(pattern, recursive=True))
        if matched:
            return matched[0]

        # Backend container may not mount model files; infer ai_worker-visible path.
        default_variety = os.environ.get('AI_MODEL_DEFAULT_VARIETY', 'soybean').strip() or 'soybean'
        return f"{model_root}/{default_variety}/{file_name}"

    @staticmethod
    def get_active_model():
        return AIModelConfig.query.filter_by(is_active=True).first()

    @staticmethod
    def create_model(model_name, model_path, class_list, is_active=False):
        cleaned_name = AIModelService._validate_model_name(model_name)
        cleaned_path = AIModelService._normalize_model_path(cleaned_name, model_path)

        exists = AIModelConfig.query.filter_by(model_name=cleaned_name).first()
        if exists:
            raise BadRequest('model_name already exists')

        row = AIModelConfig(model_name=cleaned_name, model_path=cleaned_path, is_active=bool(is_active))
        row.set_class_list(class_list or [])

        if row.is_active:
            AIModelConfig.query.update({'is_active': False})

        db.session.add(row)
        db.session.commit()
        return row.to_dict()

    @staticmethod
    def update_model(model_id, model_name=None, model_path=None, class_list=None, is_active=None):
        row = AIModelConfig.query.get(model_id)
        if not row:
            raise BadRequest('Model not found')

        target_name = row.model_name

        if model_name is not None:
            cleaned_name = AIModelService._validate_model_name(model_name)
            duplicate = AIModelConfig.query.filter(
                AIModelConfig.model_name == cleaned_name,
                AIModelConfig.id != model_id,
            ).first()
            if duplicate:
                raise BadRequest('model_name already exists')
            target_name = cleaned_name
            row.model_name = cleaned_name

        if model_path is not None or model_name is not None:
            row.model_path = AIModelService._normalize_model_path(target_name, model_path)

        if class_list is not None:
            row.set_class_list(class_list)

        if is_active is not None:
            flag = bool(is_active)
            row.is_active = flag
            if flag:
                AIModelConfig.query.filter(AIModelConfig.id != model_id).update({'is_active': False})

        db.session.commit()
        return row.to_dict()

    @staticmethod
    def activate_model(model_id):
        row = AIModelConfig.query.get(model_id)
        if not row:
            raise BadRequest('Model not found')

        AIModelConfig.query.update({'is_active': False})
        row.is_active = True
        db.session.commit()
        return row.to_dict()
