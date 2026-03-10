#!/usr/bin/env python3
"""Convert LabelMe-style JSON annotations to COCO format.

Usage examples:
  python process-data/xanylabel-covert_coco.py --input D:\\ai-projects\\SeedAi\\process-data\\data
  python process-data/xanylabel-covert_coco.py --input D:\\ai-projects\\SeedAi\\process-data\\data --overwrite

Default behavior writes a sibling file with suffix `.coco.json`.
Use --overwrite to replace the original JSON file in-place.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple


def parse_args() -> argparse.Namespace:
	parser = argparse.ArgumentParser(description="Convert LabelMe JSON to COCO JSON")
	parser.add_argument("--input", required=True, help="Input JSON file or directory")
	return parser.parse_args()


def find_json_files(input_path: Path) -> Iterable[Path]:
	if input_path.is_file() and input_path.suffix.lower() == ".json":
		yield input_path
		return

	if input_path.is_dir():
		for path in input_path.rglob("*.json"):
			yield path


def to_bbox(points: List[List[float]]) -> Tuple[float, float, float, float]:
	xs = [float(p[0]) for p in points]
	ys = [float(p[1]) for p in points]
	x_min, x_max = min(xs), max(xs)
	y_min, y_max = min(ys), max(ys)
	return x_min, y_min, x_max - x_min, y_max - y_min


def _normalize_segmentation(segmentation_raw: object) -> Optional[List[List[float]]]:
	if not isinstance(segmentation_raw, list) or not segmentation_raw:
		return None

	normalized: List[List[float]] = []
	for seg in segmentation_raw:
		if not isinstance(seg, list) or len(seg) < 6:
			continue
		try:
			normalized.append([float(v) for v in seg])
		except (TypeError, ValueError):
			continue

	return normalized or None


def extract_segmentation(shape: Dict) -> Optional[List[List[float]]]:
	# Keep original segmentation when source explicitly provides it.
	segmentation = _normalize_segmentation(shape.get("segmentation"))
	if segmentation:
		return segmentation

	# For polygon-like shapes, points themselves are segmentation.
	shape_type = str(shape.get("shape_type", "polygon")).lower()
	points = shape.get("points") or []
	if shape_type in {"polygon"} and isinstance(points, list) and len(points) >= 3:
		try:
			return [[float(v) for p in points for v in p]]
		except (TypeError, ValueError):
			return None

	# Rectangle/other types without explicit segmentation should not get one.
	return None


def extract_categories_from_payload(payload: Dict) -> List[str]:
	seen = set()
	ordered: List[str] = []

	def push(name: object) -> None:
		label = str(name or "").strip()
		if not label or label in seen:
			return
		seen.add(label)
		ordered.append(label)

	categories = payload.get("categories")
	if isinstance(categories, list):
		for item in categories:
			if isinstance(item, dict):
				push(item.get("name"))
			else:
				push(item)

	for key in ("labels", "label_list", "classes", "class_list"):
		items = payload.get(key)
		if isinstance(items, list):
			for item in items:
				if isinstance(item, dict):
					push(item.get("name"))
				else:
					push(item)

	shapes = payload.get("shapes") or []
	if isinstance(shapes, list):
		for shape in shapes:
			if isinstance(shape, dict):
				push(shape.get("label", "unknown"))

	return ordered


def shape_to_coco_annotation(
	shape: Dict,
	image_id: int,
	ann_id: int,
	category_id_map: Dict[str, int],
) -> Dict:
	label = str(shape.get("label", "unknown")).strip() or "unknown"
	points = shape.get("points") or []
	if not isinstance(points, list) or len(points) < 2:
		raise ValueError("shape.points must have at least 2 points")

	x, y, w, h = to_bbox(points)
	area = max(0.0, w) * max(0.0, h)

	annotation = {
		"id": ann_id,
		"image_id": image_id,
		"category_id": category_id_map[label],
		"bbox": [x, y, w, h],
		"area": area,
		"iscrowd": 0,
	}

	segmentation = extract_segmentation(shape)
	if segmentation:
		annotation["segmentation"] = segmentation

	return annotation


def build_coco_from_labelme(payload: Dict, src: Path, global_categories: List[str]) -> Dict:
	image_width = int(payload.get("imageWidth") or 0)
	image_height = int(payload.get("imageHeight") or 0)
	image_path = str(payload.get("imagePath") or src.with_suffix(".jpg").name)

	shapes = payload.get("shapes") or []
	if not isinstance(shapes, list):
		raise ValueError("shapes must be a list")

	labels = list(global_categories)
	for label in extract_categories_from_payload(payload):
		if label not in labels:
			labels.append(label)

	category_id_map = {label: idx + 1 for idx, label in enumerate(labels)}

	annotations: List[Dict] = []
	ann_id = 1
	for shape in shapes:
		if not isinstance(shape, dict):
			continue
		try:
			annotations.append(shape_to_coco_annotation(shape, 1, ann_id, category_id_map))
			ann_id += 1
		except ValueError:
			continue

	return {
		"info": {
			"description": "Converted from LabelMe JSON",
			"version": "1.0",
		},
		"licenses": [],
		"images": [
			{
				"id": 1,
				"file_name": image_path,
				"width": image_width,
				"height": image_height,
			}
		],
		"annotations": annotations,
		"categories": [
			{"id": cid, "name": label, "supercategory": "object"}
			for label, cid in category_id_map.items()
		],
	}


def normalize_existing_coco(payload: Dict, global_categories: List[str]) -> Dict:
	if not global_categories:
		return payload

	name_to_new_id = {name: idx + 1 for idx, name in enumerate(global_categories)}
	old_categories = payload.get("categories") or []
	old_id_to_name: Dict[int, str] = {}
	if isinstance(old_categories, list):
		for item in old_categories:
			if not isinstance(item, dict):
				continue
			try:
				old_id = int(item.get("id"))
			except (TypeError, ValueError):
				continue
			name = str(item.get("name") or "").strip()
			if name:
				old_id_to_name[old_id] = name

	annotations = payload.get("annotations") or []
	if isinstance(annotations, list):
		for ann in annotations:
			if not isinstance(ann, dict):
				continue
			try:
				old_cat_id = int(ann.get("category_id"))
			except (TypeError, ValueError):
				continue
			cat_name = old_id_to_name.get(old_cat_id)
			if cat_name and cat_name in name_to_new_id:
				ann["category_id"] = name_to_new_id[cat_name]

	payload["categories"] = [
		{"id": cid, "name": name, "supercategory": "object"}
		for name, cid in name_to_new_id.items()
	]
	return payload


def convert_single_json(src: Path, global_categories: List[str]) -> Path:
	with src.open("r", encoding="utf-8") as f:
		payload = json.load(f)

	if isinstance(payload, dict) and {"images", "annotations", "categories"}.issubset(payload.keys()):
		updated = normalize_existing_coco(payload, global_categories)
	else:
		updated = build_coco_from_labelme(payload, src, global_categories)

	with src.open("w", encoding="utf-8") as f:
		json.dump(updated, f, ensure_ascii=False, indent=2)

	return src


def main() -> None:
	args = parse_args()
	input_path = Path(args.input).expanduser()

	if not input_path.exists():
		raise FileNotFoundError(f"Input path not found: {input_path}")

	files = list(find_json_files(input_path))
	if not files:
		print("No JSON files found.")
		return

	global_categories: List[str] = []
	for src in files:
		try:
			with src.open("r", encoding="utf-8") as f:
				payload = json.load(f)
		except Exception:
			continue

		candidate = extract_categories_from_payload(payload)
		if (
			len(candidate) > len(global_categories)
			or (
				len(candidate) == len(global_categories)
				and sum(len(name) for name in candidate) > sum(len(name) for name in global_categories)
			)
		):
			global_categories = candidate

	converted = 0
	skipped = 0
	for src in files:
		try:
			out = convert_single_json(src, global_categories=global_categories)
			converted += 1
			print(f"OK: {src} -> {out}")
		except Exception as exc:
			skipped += 1
			print(f"SKIP: {src} ({exc})")

	print(f"Done. converted={converted}, skipped={skipped}")


if __name__ == "__main__":
	main()

