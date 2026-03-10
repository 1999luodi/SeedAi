"""AI inference service using ONNXRuntime only."""

import json
import logging
import os
import sys
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

            shape = self.session.get_inputs()[0].shape
            h = shape[2]
            w = shape[3]
            if isinstance(h, int) and isinstance(w, int):
                self.input_size = (w, h)
            else:
                self.input_size = (640, 640)

            logger.info("ONNX model loaded: %s", model_path)
            return self.session
        except Exception as error:
            logger.error("Model load failed: %s", error)
            self.session = None
            self.input_name = None
            return None

    def _preprocess(self, image_bgr: np.ndarray) -> Tuple[np.ndarray, Tuple[int, int]]:
        orig_h, orig_w = image_bgr.shape[:2]
        in_w, in_h = self.input_size

        resized = cv2.resize(image_bgr, (in_w, in_h), interpolation=cv2.INTER_LINEAR)
        rgb = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)

        tensor = rgb.astype(np.float32) / 255.0
        tensor = np.transpose(tensor, (2, 0, 1))[None, ...]

        return tensor, (orig_w, orig_h)

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

    def inference_bgr_image(
        self,
        image_bgr: np.ndarray,
        conf_threshold: Optional[float] = None,
        class_names: Optional[List[str]] = None,
    ) -> List[Dict]:
        if self.session is None or self.input_name is None:
            raise ValueError("model not loaded")

        threshold = self.conf_threshold if conf_threshold is None else float(conf_threshold)
        tensor, image_size = self._preprocess(image_bgr)
        outputs = self.session.run(None, {self.input_name: tensor})
        pred = self._extract_predictions(outputs)
        return self._postprocess_yolov5(pred, threshold, image_size, class_names)


MODEL_PATH = os.environ.get("MODEL_PATH", "")
DEFAULT_CONF = float(os.environ.get("DEFAULT_CONF_THRESHOLD", "0.25"))
PORT = int(os.environ.get("AI_WORKER_PORT", "8000"))
HOST = os.environ.get("AI_WORKER_HOST", "0.0.0.0")

engine = InferenceEngine(model_path=MODEL_PATH or None, conf_threshold=DEFAULT_CONF)
model_cache: Dict[str, InferenceEngine] = {"default": engine}
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


def get_engine_for_request(model_name: str, model_path: Optional[str]) -> InferenceEngine:
    key = f"{model_name}:{model_path or ''}"
    if key in model_cache:
        return model_cache[key]

    if model_path and os.path.exists(model_path):
        logger.info("Loading model by request: name=%s path=%s", model_name, model_path)
        new_engine = InferenceEngine(model_path=model_path, conf_threshold=DEFAULT_CONF)
        if new_engine.session is not None:
            model_cache[key] = new_engine
            return new_engine
    return model_cache["default"]


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
        model_path = request.form.get("model_path")
        class_names = parse_class_names(request.form.get("class_names"))

        raw = np.frombuffer(file.read(), dtype=np.uint8)
        image = cv2.imdecode(raw, cv2.IMREAD_COLOR)
        if image is None:
            return jsonify({"success": False, "message": "invalid image data"}), 400

        height, width = image.shape[:2]
        selected_engine = get_engine_for_request(model_name, model_path)
        detections = selected_engine.inference_bgr_image(
            image,
            conf_threshold=conf_threshold,
            class_names=class_names,
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
