from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .export_drawio import export_drawio
from .export_excalidraw import export_excalidraw
from .export_html import export_html_viewer
from .export_mermaid import export_mermaid
from .export_svg import export_svg, export_svg_auto, export_product_tree_svg, export_matrix_svg, export_capability_map_svg, export_swimlane_flow_svg
from .generate import write_plan_output
from .model import load_json
from .validate import validate_blueprint
from .viewer import write_viewer_package


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="business-blueprint")
    parser.add_argument("--plan", help="Generate only the canonical blueprint JSON.")
    parser.add_argument(
        "--generate",
        help="Generate the canonical blueprint JSON and viewer.",
    )
    parser.add_argument("--edit", help="Refresh the static viewer for an existing blueprint.")
    parser.add_argument("--export", help="Export SVG, draw.io, and Excalidraw artifacts.")
    parser.add_argument("--export-auto", help="Export SVG using content routing + free-flow layout.")
    parser.add_argument("--html", help="Generate self-contained HTML viewer with inline SVG.")
    parser.add_argument("--validate", help="Validate a blueprint and print JSON results.")
    parser.add_argument("--from", dest="from_path", help="Source text or file path.")
    parser.add_argument("--industry", default="common", help="Template pack name.")
    parser.add_argument("--theme", default="light", choices=["light", "dark"],
                        help="Color theme for HTML output (default: light).")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if args.plan:
        source_text = _read_source_text(args.from_path)
        # 如果 --from 未提供且存在 stdin 数据，则从 stdin 读取
        if not source_text and not args.from_path and not sys.stdin.isatty():
            source_text = sys.stdin.read()
        write_plan_output(Path(args.plan), source_text, args.industry, Path.cwd())
        return 0

    if args.generate:
        blueprint_path = Path(args.from_path or "solution.blueprint.json")
        viewer_path = Path(args.generate)
        write_viewer_package(
            blueprint_path=blueprint_path,
            viewer_path=viewer_path,
            handoff_path=viewer_path.with_name("solution.handoff.json"),
            patch_path=viewer_path.with_name("solution.patch.jsonl"),
        )
        # Also generate self-contained HTML viewer with inline SVG
        html_path = viewer_path.with_name("solution.viewer.html")
        export_html_viewer(load_json(blueprint_path), html_path, theme=args.theme)
        return 0

    if args.edit:
        blueprint_path = Path(args.edit)
        viewer_path = blueprint_path.with_suffix(".viewer.html")
        write_viewer_package(
            blueprint_path=blueprint_path,
            viewer_path=viewer_path,
            handoff_path=blueprint_path.with_name("solution.handoff.json"),
            patch_path=blueprint_path.with_name("solution.patch.jsonl"),
        )
        return 0

    if args.export:
        blueprint_path = Path(args.export)
        blueprint = load_json(blueprint_path)
        export_dir = blueprint_path.with_name("solution.exports")
        export_dir.mkdir(parents=True, exist_ok=True)
        export_svg(blueprint, export_dir / "solution.svg", theme=args.theme)
        export_capability_map_svg(blueprint, export_dir / "capability-map.svg", theme=args.theme)
        export_swimlane_flow_svg(blueprint, export_dir / "swimlane-flow.svg", theme=args.theme)
        export_product_tree_svg(blueprint, export_dir / "product-tree.svg", theme=args.theme)
        export_matrix_svg(blueprint, export_dir / "capability-matrix.svg", theme=args.theme)
        export_drawio(blueprint, export_dir / "solution.drawio")
        export_excalidraw(blueprint, export_dir / "solution.excalidraw")
        export_mermaid(blueprint, export_dir / "solution.mermaid.md")
        return 0

    if args.export_auto:
        blueprint_path = Path(args.export_auto)
        blueprint = load_json(blueprint_path)
        export_dir = blueprint_path.with_name("solution.exports")
        export_dir.mkdir(parents=True, exist_ok=True)
        export_svg_auto(blueprint, export_dir / "solution.auto.svg", theme=args.theme)
        return 0

    if args.html:
        blueprint_path = Path(args.from_path or "solution.blueprint.json")
        blueprint = load_json(blueprint_path)
        html_path = Path(args.html)
        html_path.parent.mkdir(parents=True, exist_ok=True)
        export_html_viewer(blueprint, html_path, theme=args.theme)
        return 0

    if args.validate:
        payload = load_json(Path(args.validate))
        print(json.dumps(validate_blueprint(payload), ensure_ascii=False, indent=2))
        return 0

    return 0


def _read_source_text(value: str | None) -> str:
    if not value:
        return ""
    # 内联文本通常较长且包含中文等非 ASCII 字符，不应当作文件路径处理。
    # Linux 文件名上限 255 字节，超过此值传给 stat() 会报 OSError: File name too long。
    # 策略：超过 255 字节直接当内联文本；短字符串才检查是否为文件路径。
    if len(value.encode("utf-8")) > 255:
        return value
    path = Path(value)
    return path.read_text(encoding="utf-8") if path.exists() else value


if __name__ == "__main__":
    raise SystemExit(main())
