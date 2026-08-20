# -*- coding: utf-8 -*-
"""按持久化锚点给实用新型线稿叠加件号与引出线。

大模型只负责识别部件并给出归一化锚点/标签坐标；本脚本校验件号后，
以 SVG 精确绘制曲线和序号，不让生图模型二次改写结构图。

  python tools/shared/structure_callout_overlay.py \
    --case-dir outputs/case \
    --anchors outputs/case/structure_callout_anchors.yaml
"""
from __future__ import annotations

import argparse
import base64
import html
import json
import math
import struct
import sys
from pathlib import Path
from typing import Any


def load_data(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() in {".yaml", ".yml"}:
        try:
            import yaml  # type: ignore

            data = yaml.safe_load(text)
        except Exception as exc:
            raise ValueError(f"无法读取 YAML {path}: {exc}") from exc
    else:
        data = json.loads(text)
    if not isinstance(data, dict):
        raise ValueError(f"锚点文件根须为对象: {path}")
    return data


def resolve_path(case_dir: Path, raw: str) -> Path:
    path = Path(raw)
    if path.is_absolute():
        return path
    return (case_dir / path).resolve()


def image_size(path: Path) -> tuple[int, int]:
    """不用 Pillow 读取 PNG/JPEG 尺寸。"""
    data = path.read_bytes()
    if data.startswith(b"\x89PNG\r\n\x1a\n") and len(data) >= 24:
        return struct.unpack(">II", data[16:24])
    if data.startswith(b"\xff\xd8"):
        i = 2
        while i + 9 < len(data):
            if data[i] != 0xFF:
                i += 1
                continue
            marker = data[i + 1]
            i += 2
            if marker in {0xD8, 0xD9} or 0xD0 <= marker <= 0xD7:
                continue
            if i + 2 > len(data):
                break
            seg_len = int.from_bytes(data[i : i + 2], "big")
            if marker in {
                0xC0,
                0xC1,
                0xC2,
                0xC3,
                0xC5,
                0xC6,
                0xC7,
                0xC9,
                0xCA,
                0xCB,
                0xCD,
                0xCE,
                0xCF,
            }:
                height = int.from_bytes(data[i + 3 : i + 5], "big")
                width = int.from_bytes(data[i + 5 : i + 7], "big")
                return width, height
            i += max(seg_len, 2)
    raise ValueError(f"仅支持 PNG/JPEG 尺寸读取: {path}")


def _parts_index(structure: dict[str, Any]) -> dict[str, str]:
    return {
        str(p.get("id") or "").strip(): str(p.get("name") or "").strip()
        for p in (structure.get("parts") or [])
        if isinstance(p, dict) and str(p.get("id") or "").strip()
    }


def _point(value: Any) -> tuple[float, float] | None:
    if not isinstance(value, (list, tuple)) or len(value) != 2:
        return None
    try:
        return float(value[0]), float(value[1])
    except (TypeError, ValueError):
        return None


def validate_manifest(
    manifest: dict[str, Any],
    case_dir: Path,
    *,
    structure: dict[str, Any] | None = None,
) -> list[str]:
    errors: list[str] = []
    if int(manifest.get("version") or 0) != 1:
        errors.append("structure_callout_anchors.version 须为 1")
    if (manifest.get("coordinate_system") or "normalized") != "normalized":
        errors.append("coordinate_system 须为 normalized")
    views = manifest.get("views") or []
    if not isinstance(views, list) or not views:
        errors.append("views 为空")
        return errors

    parts = _parts_index(structure or {})
    for vi, view in enumerate(views):
        if not isinstance(view, dict):
            errors.append(f"views[{vi}] 非法")
            continue
        image_raw = str(view.get("image_path") or "").strip()
        output_raw = str(view.get("output_svg_path") or "").strip()
        if not image_raw:
            errors.append(f"views[{vi}] 缺少 image_path")
        elif not resolve_path(case_dir, image_raw).is_file():
            errors.append(f"views[{vi}] 原图不存在: {image_raw}")
        if not output_raw:
            errors.append(f"views[{vi}] 缺少 output_svg_path")

        callouts = view.get("callouts") or []
        if not isinstance(callouts, list) or not callouts:
            errors.append(f"views[{vi}].callouts 为空")
            continue
        seen: set[str] = set()
        labels: list[tuple[float, float]] = []
        for ci, item in enumerate(callouts):
            if not isinstance(item, dict):
                errors.append(f"views[{vi}].callouts[{ci}] 非法")
                continue
            pid = str(item.get("id") or "").strip()
            name = str(item.get("name") or "").strip()
            if not pid:
                errors.append(f"views[{vi}].callouts[{ci}] 缺少 id")
            elif pid in seen:
                errors.append(f"views[{vi}] 件号 {pid} 重复")
            seen.add(pid)
            if parts:
                if pid not in parts:
                    errors.append(f"views[{vi}] 件号 {pid} 不在 structure_schema.parts")
                elif name and parts[pid] and name != parts[pid]:
                    errors.append(f"views[{vi}] 件号 {pid} 名称与 StructureSchema 不一致")

            for key in ("anchor", "label"):
                point = _point(item.get(key))
                if point is None:
                    errors.append(f"views[{vi}] 件号 {pid or '?'} 的 {key} 须为 [x, y]")
                    continue
                if not all(0.0 <= n <= 1.0 for n in point):
                    errors.append(f"views[{vi}] 件号 {pid or '?'} 的 {key} 超出 0..1")
                if key == "label":
                    labels.append(point)
            confidence = item.get("confidence", 1.0)
            try:
                if float(confidence) < 0.60:
                    errors.append(f"views[{vi}] 件号 {pid or '?'} 锚点置信度低于 0.60")
            except (TypeError, ValueError):
                errors.append(f"views[{vi}] 件号 {pid or '?'} confidence 非数字")

        # 归一化距离过小意味着序号会互相覆盖。
        for i, first in enumerate(labels):
            for second in labels[i + 1 :]:
                if math.dist(first, second) < 0.035:
                    errors.append(f"views[{vi}] 存在距离过近的 label 坐标")
                    break
    return errors


def _mime(path: Path) -> str:
    return "image/png" if path.suffix.lower() == ".png" else "image/jpeg"


def _svg_path(
    label: tuple[float, float],
    anchor: tuple[float, float],
    *,
    clearance: float,
    route: str,
) -> str:
    lx, ly = label
    ax, ay = anchor
    dx, dy = ax - lx, ay - ly
    length = max(math.hypot(dx, dy), 1.0)
    sx = lx + dx / length * clearance
    sy = ly + dy / length * clearance
    route = route if route in {"horizontal", "vertical"} else (
        "horizontal" if abs(dx) >= abs(dy) * 0.65 else "vertical"
    )
    if route == "horizontal":
        c1 = (sx + dx * 0.35, sy)
        c2 = (ax - dx * 0.18, ay)
    else:
        c1 = (sx, sy + dy * 0.35)
        c2 = (ax, ay - dy * 0.18)
    return (
        f"M {sx:.2f},{sy:.2f} "
        f"C {c1[0]:.2f},{c1[1]:.2f} {c2[0]:.2f},{c2[1]:.2f} {ax:.2f},{ay:.2f}"
    )


def render_view(view: dict[str, Any], case_dir: Path) -> Path:
    image_path = resolve_path(case_dir, str(view["image_path"]))
    output_path = resolve_path(case_dir, str(view["output_svg_path"]))
    width, height = image_size(image_path)
    style = view.get("style") if isinstance(view.get("style"), dict) else {}
    font_size = float(style.get("font_size") or max(18, min(width, height) * 0.032))
    line_width = float(style.get("line_width") or max(1.5, min(width, height) * 0.0024))
    label_style = str(style.get("label_style") or "plain")
    circle_radius = float(style.get("circle_radius") or font_size * 0.72)

    encoded = base64.b64encode(image_path.read_bytes()).decode("ascii")
    svg: list[str] = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        (
            f'<svg xmlns="http://www.w3.org/2000/svg" '
            f'xmlns:xlink="http://www.w3.org/1999/xlink" '
            f'width="{width}" height="{height}" viewBox="0 0 {width} {height}">'
        ),
        f'<image width="{width}" height="{height}" href="data:{_mime(image_path)};base64,{encoded}"/>',
        (
            '<g id="structure-callouts" fill="none" stroke="#111" '
            f'stroke-width="{line_width:.2f}" stroke-linecap="round" stroke-linejoin="round">'
        ),
    ]
    text_items: list[str] = []
    for item in view.get("callouts") or []:
        pid = str(item["id"])
        anchor_n = _point(item["anchor"])
        label_n = _point(item["label"])
        assert anchor_n is not None and label_n is not None
        anchor = (anchor_n[0] * width, anchor_n[1] * height)
        label = (label_n[0] * width, label_n[1] * height)
        clearance = circle_radius if label_style == "circle" else max(font_size * 0.56, 8.0)
        d = _svg_path(
            label,
            anchor,
            clearance=clearance,
            route=str(item.get("route") or "auto"),
        )
        title = html.escape(f"{pid} {item.get('name') or ''}".strip())
        svg.append(f'<g data-part-id="{html.escape(pid)}"><title>{title}</title><path d="{d}"/>')
        if label_style == "circle":
            svg.append(
                f'<circle cx="{label[0]:.2f}" cy="{label[1]:.2f}" r="{circle_radius:.2f}" fill="white"/>'
            )
        svg.append("</g>")
        text_items.append(
            (
                f'<text x="{label[0]:.2f}" y="{label[1]:.2f}" '
                f'font-family="Arial, Helvetica, sans-serif" font-size="{font_size:.2f}" '
                'font-weight="500" text-anchor="middle" dominant-baseline="central" '
                f'fill="#111">{html.escape(pid)}</text>'
            )
        )
    svg.append("</g>")
    svg.extend(text_items)
    svg.append("</svg>")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(svg) + "\n", encoding="utf-8")
    return output_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="按持久化锚点给结构线稿叠件号（SVG）")
    parser.add_argument("--case-dir", type=Path, required=True)
    parser.add_argument("--anchors", type=Path, required=True)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)

    case_dir = args.case_dir.resolve()
    anchors_path = args.anchors.resolve()
    manifest = load_data(anchors_path)
    structure_path = case_dir / str(manifest.get("structure_ref") or "structure_schema.yaml")
    structure = load_data(structure_path) if structure_path.is_file() else None
    errors = validate_manifest(manifest, case_dir, structure=structure)
    if errors:
        print(json.dumps({"ok": False, "errors": errors}, ensure_ascii=False, indent=2), file=sys.stderr)
        return 2
    outputs: list[str] = []
    if not args.check:
        outputs = [str(render_view(view, case_dir)) for view in manifest.get("views") or []]
    print(json.dumps({"ok": True, "anchors": str(anchors_path), "outputs": outputs}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
