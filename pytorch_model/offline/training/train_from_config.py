"""Train YOLO from per-model JSON config and replace target weights with best.pt."""

import argparse
import json
import os
import shutil
import sys
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parents[2]
LOCAL_ULTRA_ROOT = WORKSPACE_ROOT / "offline" / "third_party" / "ultralytics-src"
if (LOCAL_ULTRA_ROOT / "ultralytics" / "__init__.py").exists():
    sys.path.insert(0, str(LOCAL_ULTRA_ROOT))

from ultralytics import YOLO


def load_config(config_path: Path) -> dict:
    with config_path.open("r", encoding="utf-8") as stream:
        data = json.load(stream)
    if not isinstance(data, dict):
        raise ValueError("Config must be a JSON object")
    required = ["model_name", "base_weights", "data_path", "model_output_path"]
    missing = [key for key in required if key not in data]
    if missing:
        raise ValueError(f"Missing required config fields: {', '.join(missing)}")
    return data


def resolve_path(workspace_root: Path, raw_path: str) -> Path:
    path = Path(str(raw_path))
    return path if path.is_absolute() else (workspace_root / path)


def main() -> None:
    parser = argparse.ArgumentParser(description="Train model from config file")
    parser.add_argument("--config", required=True, help="Path to model config JSON")
    args = parser.parse_args()

    workspace_root = WORKSPACE_ROOT
    config_path = resolve_path(workspace_root, args.config)
    config = load_config(config_path)

    training = config.get("training") or {}
    data_yaml = resolve_path(workspace_root, config["data_path"])
    output_path = resolve_path(workspace_root, config["model_output_path"])
    output_path.parent.mkdir(parents=True, exist_ok=True)

    onnx_output_raw = config.get("service_model_output_path")
    if onnx_output_raw:
        onnx_output_path = resolve_path(workspace_root, str(onnx_output_raw))
    else:
        onnx_output_path = output_path.with_suffix(".onnx")
    onnx_output_path.parent.mkdir(parents=True, exist_ok=True)

    model = YOLO(str(config["base_weights"]))
    result = model.train(
        data=str(data_yaml),
        epochs=int(training.get("epochs", 100)),
        imgsz=int(training.get("imgsz", 640)),
        batch=int(training.get("batch", 16)),
        device=str(training.get("device", "cpu")),
        project=str(training.get("project", "output/train")),
        name=str(config["model_name"]),
    )

    save_dir = Path(getattr(result, "save_dir", ""))
    best_weights = save_dir / "weights" / "best.pt"
    if not best_weights.exists():
        raise FileNotFoundError(f"best.pt not found at {best_weights}")

    shutil.copy2(best_weights, output_path)
    print(f"[OK] Updated model weights: {output_path}")

    # Export ONNX for online inference container.
    export_model = YOLO(str(best_weights))
    exported_path = Path(str(export_model.export(format="onnx", simplify=True)))
    if not exported_path.exists():
        raise FileNotFoundError(f"Exported onnx not found: {exported_path}")
    shutil.copy2(exported_path, onnx_output_path)
    print(f"[OK] Updated service onnx: {onnx_output_path}")


if __name__ == "__main__":
    main()
