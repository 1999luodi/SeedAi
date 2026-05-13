"""AI inference service using ONNXRuntime only."""

import json
import logging
import os
import sys
import glob
from typing import Dict, List, Optional, Tuple

import cv2
import numpy as np
import onnxruntime as ort
from flask import Flask, jsonify, request

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class InferenceEngine:
    def __init__(self, model_path: Optional[str] = None, conf_threshold: float = 0.25):
        self.conf_threshold = conf_threshold
        self.session: Optional[ort.InferenceSession] = None
        self.input_name: Optional[str] = None
        self.input_size: Tuple[int, int] = (640, 640)  # (width, height)
        self.input_hw: Tuple[Optional[int], Optional[int]] = (None, None)
        self.output_names: List[str] = []
        self.model_family: str = "yolo"
        self.mmdet_mean = np.array([123.675, 116.28, 103.53], dtype=np.float32)
        self.mmdet_std = np.array([58.395, 57.12, 57.375], dtype=np.float32)
        self.mmdet_to_rgb = True
        self.mmdet_pad_divisor = 32
        self.load_model(model_path)

    def load_model(self, model_path: Optional[str] = None) -> Optional[ort.InferenceSession]:
        logger.info("Loading ONNX model...")
        try:
            if not model_path:
                raise ValueError("MODEL_PATH is required and must point to an ONNX model")
            if not os.path.exists(model_path):
                raise FileNotFoundError(f"model file not found: {model_path}")
            if not str(model_path).lower().endswith(".onnx"):
                raise ValueError("online inference only accepts ONNX models (.onnx)")

            self.session = ort.InferenceSession(model_path, providers=["CPUExecutionProvider"])
            self.input_name = self.session.get_inputs()[0].name
            self.output_names = [item.name for item in self.session.get_outputs()]
            self.model_family = self._detect_model_family()

            shape = self.session.get_inputs()[0].shape
            h = shape[2]
            w = shape[3]
            self.input_hw = (h if isinstance(h, int) else None, w if isinstance(w, int) else None)
            if isinstance(h, int) and isinstance(w, int):
                self.input_size = (w, h)
            else:
                self.input_size = (640, 640)

            logger.info("ONNX model loaded: %s", model_path)
            logger.info("Detected model family: %s, outputs=%s", self.model_family, self.output_names)
            return self.session
        except Exception as error:
            logger.error("Model load failed: %s", error)
            self.session = None
            self.input_name = None
            return None

    def _detect_model_family(self) -> str:
        if self.session is None:
            return "yolo"

        outputs = self.session.get_outputs()
        out_names = [str(item.name or "").lower() for item in outputs]
        out_types = [str(item.type or "").lower() for item in outputs]

        # Common Faster-RCNN export: dets(float, Nx5) + labels(int64, N)
        if len(outputs) == 2 and any("label" in name for name in out_names):
            if any("int" in t for t in out_types):
                return "faster_rcnn"

        # Alternative export: boxes/scores/labels
        if len(outputs) >= 3 and any("label" in name for name in out_names):
            if any("score" in name for name in out_names):
                return "faster_rcnn_split"

        first_shape = getattr(outputs[0], "shape", None)
        if isinstance(first_shape, list) and len(first_shape) >= 3:
            last_dim = first_shape[-1]
            if isinstance(last_dim, int) and last_dim == 5:
                return "faster_rcnn"

        return "yolo"

    @staticmethod
    def resolve_runtime_family(model_name: Optional[str], detected_family: str) -> str:
        name = str(model_name or "").strip().lower()
        mmdet_tokens = [
            "faster-rcnn",
            "mask-rcnn",
            "cascade-rcnn",
            "retinanet",
            "ssd",
            "mmdet",
        ]
        yolo_tokens = ["yolo", "yolov5", "yolov8", "yolov11", "yolox"]

        if any(token in name for token in mmdet_tokens):
            return "mmdet"
        if any(token in name for token in yolo_tokens):
            return "yolo"

        # Fallback to schema-based auto detection when model_name is ambiguous.
        if detected_family in {"faster_rcnn", "faster_rcnn_split"}:
            return "mmdet"
        return "yolo"

    def _preprocess_yolo(self, image_bgr: np.ndarray) -> Tuple[np.ndarray, Tuple[int, int]]:
        orig_h, orig_w = image_bgr.shape[:2]
        in_w, in_h = self.input_size

        resized = cv2.resize(image_bgr, (in_w, in_h), interpolation=cv2.INTER_LINEAR)
        rgb = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)

        tensor = rgb.astype(np.float32) / 255.0
        tensor = np.transpose(tensor, (2, 0, 1))[None, ...]

        return tensor, (orig_w, orig_h)

    def _preprocess_mmdet(self, image_bgr: np.ndarray) -> Tuple[np.ndarray, Dict[str, float]]:
        orig_h, orig_w = image_bgr.shape[:2]
        target_w = max(1, MMDET_RESIZE_W)
        target_h = max(1, MMDET_RESIZE_H)

        ratio = min(float(target_w) / float(max(1, orig_w)), float(target_h) / float(max(1, orig_h)))
        proc_w = max(1, int(round(orig_w * ratio)))
        proc_h = max(1, int(round(orig_h * ratio)))
        resized = cv2.resize(image_bgr, (proc_w, proc_h), interpolation=cv2.INTER_LINEAR)
        scale_x = float(proc_w) / float(max(1, orig_w))
        scale_y = float(proc_h) / float(max(1, orig_h))

        img = resized.astype(np.float32)
        if self.mmdet_to_rgb:
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

        img = (img - self.mmdet_mean) / self.mmdet_std

        pad_h = proc_h
        pad_w = proc_w
        if self.mmdet_pad_divisor > 1:
            pad_h = int(np.ceil(proc_h / self.mmdet_pad_divisor) * self.mmdet_pad_divisor)
            pad_w = int(np.ceil(proc_w / self.mmdet_pad_divisor) * self.mmdet_pad_divisor)
            if pad_h != proc_h or pad_w != proc_w:
                padded = np.zeros((pad_h, pad_w, 3), dtype=np.float32)
                padded[:proc_h, :proc_w, :] = img
                img = padded

        # For uncommon static-shape exports, force final tensor shape to model input shape.
        in_h, in_w = self.input_hw
        if isinstance(in_h, int) and isinstance(in_w, int) and (pad_h != in_h or pad_w != in_w):
            img = cv2.resize(img, (in_w, in_h), interpolation=cv2.INTER_LINEAR)
            pad_h, pad_w = in_h, in_w
            proc_h, proc_w = in_h, in_w
            scale_x = float(proc_w) / float(max(1, orig_w))
            scale_y = float(proc_h) / float(max(1, orig_h))

        tensor = np.transpose(img, (2, 0, 1))[None, ...].astype(np.float32)
        tensor = np.ascontiguousarray(tensor)
        meta = {
            "orig_w": float(orig_w),
            "orig_h": float(orig_h),
            "proc_w": float(proc_w),
            "proc_h": float(proc_h),
            "pad_w": float(pad_w),
            "pad_h": float(pad_h),
            "scale_x": float(scale_x),
            "scale_y": float(scale_y),
        }
        return tensor, meta

    @staticmethod
    def _extract_predictions(outputs: List[np.ndarray]) -> np.ndarray:
        pred = outputs[0]
        if isinstance(pred, list):
            pred = pred[0]
        if pred.ndim == 3:
            pred = pred[0]
        return pred

    @staticmethod
    def _postprocess_yolov5(
        pred: np.ndarray,
        conf_threshold: float,
        image_size: Tuple[int, int],
        class_names: Optional[List[str]],
    ) -> List[Dict]:
        img_w, img_h = image_size
        boxes_xyxy: List[List[float]] = []
        scores: List[float] = []
        class_ids: List[int] = []

        for row in pred:
            if row.shape[0] < 6:
                continue

            obj_conf = float(row[4])
            cls_probs = row[5:]
            if cls_probs.size == 0:
                continue

            class_id = int(np.argmax(cls_probs))
            cls_conf = float(cls_probs[class_id])
            score = obj_conf * cls_conf
            if score < conf_threshold:
                continue

            cx, cy, w, h = map(float, row[:4])
            x1 = max(0.0, cx - w / 2.0)
            y1 = max(0.0, cy - h / 2.0)
            x2 = min(float(img_w), cx + w / 2.0)
            y2 = min(float(img_h), cy + h / 2.0)

            if x2 <= x1 or y2 <= y1:
                continue

            boxes_xyxy.append([x1, y1, x2, y2])
            scores.append(score)
            class_ids.append(class_id)

        if not boxes_xyxy:
            return []

        # OpenCV NMS API expects [x, y, width, height].
        nms_boxes = [[x1, y1, x2 - x1, y2 - y1] for x1, y1, x2, y2 in boxes_xyxy]
        idxs = cv2.dnn.NMSBoxes(nms_boxes, scores, conf_threshold, 0.45)
        if idxs is None or len(idxs) == 0:
            return []

        detections: List[Dict] = []
        for i in idxs.flatten().tolist():
            class_id = class_ids[i]
            label = str(class_id)
            if class_names and 0 <= class_id < len(class_names):
                label = str(class_names[class_id])

            detections.append(
                {
                    "label": label,
                    "bbox": [round(float(v), 2) for v in boxes_xyxy[i]],
                    "confidence": round(float(scores[i]), 4),
                    "class_id": class_id,
                }
            )

        return detections

    @staticmethod
    def _postprocess_faster_rcnn_dets_labels(
        dets: np.ndarray,
        labels: np.ndarray,
        conf_threshold: float,
        image_meta: Dict[str, float],
        class_names: Optional[List[str]],
    ) -> List[Dict]:
        if dets.ndim == 3:
            dets = dets[0]
        if labels.ndim == 2:
            labels = labels[0]

        dets = np.asarray(dets)
        labels = np.asarray(labels)
        if dets.ndim != 2 or dets.shape[0] == 0:
            return []

        img_w = float(image_meta.get("orig_w", 1.0))
        img_h = float(image_meta.get("orig_h", 1.0))
        proc_w = float(image_meta.get("proc_w", img_w))
        proc_h = float(image_meta.get("proc_h", img_h))
        pad_w = float(image_meta.get("pad_w", proc_w))
        pad_h = float(image_meta.get("pad_h", proc_h))
        scale_x = float(image_meta.get("scale_x", 1.0))
        scale_y = float(image_meta.get("scale_y", 1.0))

        detections: List[Dict] = []
        count = min(int(dets.shape[0]), int(labels.shape[0]) if labels.ndim == 1 else 0)
        for i in range(count):
            row = dets[i]
            if row.shape[0] < 4:
                continue

            x1 = float(row[0])
            y1 = float(row[1])
            x2 = float(row[2])
            y2 = float(row[3])
            score = float(row[4]) if row.shape[0] >= 5 else 1.0

            if score < conf_threshold:
                continue

            # end2end exports may output normalized, resized-space, padded-space, or original-space boxes.
            max_coord = max(abs(x1), abs(y1), abs(x2), abs(y2))
            proc_max = max(proc_w, proc_h)
            pad_max = max(pad_w, pad_h)
            img_max = max(img_w, img_h)
            has_resize_scale = abs(scale_x - 1.0) > 1e-3 or abs(scale_y - 1.0) > 1e-3

            if max_coord <= 1.0:
                x1 *= img_w
                x2 *= img_w
                y1 *= img_h
                y2 *= img_h
            elif has_resize_scale and max_coord <= proc_max * 1.05:
                x1 /= max(scale_x, 1e-6)
                x2 /= max(scale_x, 1e-6)
                y1 /= max(scale_y, 1e-6)
                y2 /= max(scale_y, 1e-6)
            elif has_resize_scale and max_coord <= pad_max * 1.05:
                x1 = min(x1, proc_w) / max(scale_x, 1e-6)
                x2 = min(x2, proc_w) / max(scale_x, 1e-6)
                y1 = min(y1, proc_h) / max(scale_y, 1e-6)
                y2 = min(y2, proc_h) / max(scale_y, 1e-6)
            elif max_coord <= img_max * 1.05:
                # Already in original image coordinate space.
                pass
            else:
                x1 /= max(scale_x, 1e-6)
                x2 /= max(scale_x, 1e-6)
                y1 /= max(scale_y, 1e-6)
                y2 /= max(scale_y, 1e-6)

            if x2 < x1:
                x1, x2 = x2, x1
            if y2 < y1:
                y1, y2 = y2, y1

            x1 = max(0.0, min(float(img_w), x1))
            x2 = max(0.0, min(float(img_w), x2))
            y1 = max(0.0, min(float(img_h), y1))
            y2 = max(0.0, min(float(img_h), y2))

            if x2 <= x1 or y2 <= y1:
                continue

            class_id = int(labels[i])
            if class_id < 0:
                continue
            label = str(class_id)
            if class_names and 0 <= class_id < len(class_names):
                label = str(class_names[class_id])

            detections.append(
                {
                    "label": label,
                    "bbox": [round(x1, 2), round(y1, 2), round(x2, 2), round(y2, 2)],
                    "confidence": round(score, 4),
                    "class_id": class_id,
                }
            )

        detections.sort(key=lambda item: float(item.get("confidence", 0.0)), reverse=True)
        return detections

    def _postprocess_faster_rcnn_outputs(
        self,
        outputs: List[np.ndarray],
        conf_threshold: float,
        image_meta: Dict[str, float],
        class_names: Optional[List[str]],
    ) -> List[Dict]:
        name_to_output = {}
        for index, value in enumerate(outputs):
            name = self.output_names[index] if index < len(self.output_names) else f"out{index}"
            name_to_output[str(name).lower()] = np.asarray(value)

        # Preferred: dets + labels
        dets = None
        labels = None
        for key, value in name_to_output.items():
            if labels is None and "label" in key:
                labels = value
            if dets is None and ("det" in key or "bbox" in key or "box" in key):
                dets = value

        if dets is None and len(outputs) >= 1:
            dets = np.asarray(outputs[0])
        if labels is None and len(outputs) >= 2:
            labels = np.asarray(outputs[1])

        # Split exports: boxes + scores + labels
        if dets is not None and labels is not None and dets.ndim >= 2 and dets.shape[-1] == 4 and len(outputs) >= 3:
            scores = np.asarray(outputs[1])
            labels = np.asarray(outputs[2])
            if scores.ndim == 2:
                scores = scores[0]
            if labels.ndim == 2:
                labels = labels[0]
            if dets.ndim == 3:
                dets = dets[0]
            dets = np.concatenate([dets, scores[:, None]], axis=1)

        if dets is not None and labels is not None:
            return self._postprocess_faster_rcnn_dets_labels(
                dets=dets,
                labels=labels,
                conf_threshold=conf_threshold,
                image_meta=image_meta,
                class_names=class_names,
            )

        return []

    def inference_bgr_image(
        self,
        image_bgr: np.ndarray,
        conf_threshold: Optional[float] = None,
        class_names: Optional[List[str]] = None,
        model_name: Optional[str] = None,
    ) -> List[Dict]:
        if self.session is None or self.input_name is None:
            raise ValueError("model not loaded")

        threshold = self.conf_threshold if conf_threshold is None else float(conf_threshold)
        runtime_family = self.resolve_runtime_family(model_name=model_name, detected_family=self.model_family)

        if runtime_family == "mmdet":
            tensor, image_meta = self._preprocess_mmdet(image_bgr)
            outputs = self.session.run(None, {self.input_name: tensor})
            return self._postprocess_faster_rcnn_outputs(
                outputs=outputs,
                conf_threshold=threshold,
                image_meta=image_meta,
                class_names=class_names,
            )

        tensor, image_size = self._preprocess_yolo(image_bgr)
        outputs = self.session.run(None, {self.input_name: tensor})
        pred = self._extract_predictions(outputs)
        return self._postprocess_yolov5(pred, threshold, image_size, class_names)


MODEL_PATH = os.environ.get("MODEL_PATH", "")
MODEL_ROOT = os.environ.get("AI_WORKER_MODEL_ROOT", "/workspace/online/models/service")
DEFAULT_CONF = float(os.environ.get("DEFAULT_CONF_THRESHOLD", "0.25"))
MMDET_RESIZE_W = int(os.environ.get("MMDET_RESIZE_W", "800"))
MMDET_RESIZE_H = int(os.environ.get("MMDET_RESIZE_H", "800"))
PORT = int(os.environ.get("AI_WORKER_PORT", "8000"))
HOST = os.environ.get("AI_WORKER_HOST", "0.0.0.0")

engine = InferenceEngine(model_path=MODEL_PATH or None, conf_threshold=DEFAULT_CONF)
model_cache: Dict[str, InferenceEngine] = {"default": engine}
if MODEL_PATH:
    model_cache[os.path.abspath(MODEL_PATH)] = engine
app = Flask(__name__)


def parse_class_names(raw_value: Optional[str]) -> List[str]:
    if raw_value is None or str(raw_value).strip() == "":
        return []
    try:
        parsed = json.loads(raw_value)
    except (TypeError, ValueError):
        return []
    if not isinstance(parsed, list):
        return []
    return [str(item) for item in parsed]


def resolve_model_path(model_name: str, requested_path: Optional[str] = None) -> Optional[str]:
    if requested_path:
        candidate = str(requested_path).strip()
        if candidate and candidate.lower().endswith('.onnx') and os.path.exists(candidate):
            return candidate

    cleaned = str(model_name or 'default').strip()
    if cleaned == '' or cleaned.lower() == 'default':
        return MODEL_PATH or None

    file_name = os.path.basename(cleaned)
    if not file_name.lower().endswith('.onnx'):
        file_name = f"{file_name}.onnx"

    pattern = os.path.join(MODEL_ROOT, '**', file_name)
    matched = sorted(glob.glob(pattern, recursive=True))
    if matched:
        return matched[0]

    return None


def get_engine_for_request(model_name: str, model_path: str) -> InferenceEngine:
    key = os.path.abspath(model_path)
    if key in model_cache:
        return model_cache[key]

    logger.info("Loading model by request: name=%s path=%s", model_name, model_path)
    new_engine = InferenceEngine(model_path=model_path, conf_threshold=DEFAULT_CONF)
    if new_engine.session is None:
        raise FileNotFoundError(f"model cannot be loaded: {model_path}")

    model_cache[key] = new_engine
    return new_engine


@app.route("/infer", methods=["POST"])
def infer():
    if engine.session is None:
        return jsonify({"success": False, "message": "model not loaded"}), 500

    file = request.files.get("image")
    if file is None:
        return jsonify({"success": False, "message": "image file is required"}), 400

    try:
        conf_threshold = request.form.get("conf_threshold", DEFAULT_CONF)
        model_name = str(request.form.get("model_name", "default") or "default")
        request_model_path = request.form.get("model_path")
        class_names = parse_class_names(request.form.get("class_names"))

        raw = np.frombuffer(file.read(), dtype=np.uint8)
        image = cv2.imdecode(raw, cv2.IMREAD_COLOR)
        if image is None:
            return jsonify({"success": False, "message": "invalid image data"}), 400

        model_path = resolve_model_path(model_name=model_name, requested_path=request_model_path)
        if not model_path:
            return jsonify({"success": False, "message": f"model not found: {model_name}"}), 400

        height, width = image.shape[:2]
        selected_engine = get_engine_for_request(model_name, model_path)
        detections = selected_engine.inference_bgr_image(
            image,
            conf_threshold=conf_threshold,
            class_names=class_names,
            model_name=model_name,
        )

        return jsonify(
            {
                "success": True,
                "data": {
                    "model_name": model_name,
                    "model_path": model_path,
                    "image_width": int(width),
                    "image_height": int(height),
                    "count": len(detections),
                    "detections": detections,
                },
            }
        )
    except Exception as error:
        logger.exception("Inference failed")
        return jsonify({"success": False, "message": f"inference failed: {error}"}), 500


def run_cli_once(image_path: str, model_path: Optional[str] = None):
    cli_engine = InferenceEngine(model_path=model_path or MODEL_PATH, conf_threshold=DEFAULT_CONF)
    image = cv2.imread(image_path)
    if image is None:
        raise FileNotFoundError(f"cannot read image: {image_path}")
    result = cli_engine.inference_bgr_image(image)
    print(json.dumps(result, ensure_ascii=False, indent=2))


def main():
    if len(sys.argv) >= 2 and sys.argv[1] not in ["serve", "--serve"]:
        image_path = sys.argv[1]
        model_path = sys.argv[2] if len(sys.argv) > 2 else None
        run_cli_once(image_path, model_path=model_path)
        return

    app.run(host=HOST, port=PORT)


if __name__ == "__main__":
    main()
