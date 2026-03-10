"""Export Ultralytics model weights to ONNX for online inference."""

import argparse
import sys
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parents[2]
LOCAL_ULTRA_ROOT = WORKSPACE_ROOT / "offline" / "third_party" / "ultralytics-src"
if (LOCAL_ULTRA_ROOT / "ultralytics" / "__init__.py").exists():
    sys.path.insert(0, str(LOCAL_ULTRA_ROOT))

from ultralytics import YOLO


def main() -> None:
    parser = argparse.ArgumentParser(description="Export model to ONNX")
    parser.add_argument("--weights", required=True, help="Path to source .pt weights")
    parser.add_argument("--output", required=True, help="Path to target .onnx")
    parser.add_argument("--imgsz", type=int, default=640, help="Export image size")
    args = parser.parse_args()

    weights = Path(args.weights)
    output = Path(args.output)

    if not weights.exists():
        raise FileNotFoundError(f"weights not found: {weights}")

    output.parent.mkdir(parents=True, exist_ok=True)

    model = YOLO(str(weights))
    exported_path = Path(str(model.export(format="onnx", imgsz=args.imgsz, simplify=True)))

    if not exported_path.exists():
        raise FileNotFoundError(f"exported onnx not found: {exported_path}")

    output.write_bytes(exported_path.read_bytes())
    print(f"[OK] ONNX exported to: {output}")


if __name__ == "__main__":
    main()
