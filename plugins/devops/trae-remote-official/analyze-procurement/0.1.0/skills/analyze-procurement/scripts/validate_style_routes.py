#!/usr/bin/env python3
"""Validate the six procurement style routes and their complete SVG kits."""

from __future__ import annotations

import importlib.util
import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


REQUIRED_KIT_IDS = {"route-pattern", "route-marker", "route-focus-field", "route-chart-mark"}
REQUIRED_TOKENS = {
    "--bg",
    "--bg2",
    "--ink",
    "--muted",
    "--rule",
    "--accent",
    "--accent2",
}
REQUIRED_ROUTE_FIELDS = {
    "id",
    "name",
    "preview",
    "kit",
    "dynamic_ui_companion",
    "dynamic_ui_manifest",
    "tokens",
    "corners",
    "depth",
    "composition",
    "chart",
    "edge_treatment",
    "emphasis",
}


def load_routes(script_path: Path) -> tuple[dict[str, str], ...]:
    spec = importlib.util.spec_from_file_location("style_selector", script_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load style selector")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.ROUTES


def svg_ids(path: Path) -> set[str]:
    root = ET.parse(path).getroot()
    return {
        value
        for element in root.iter()
        if (value := element.attrib.get("id"))
    }


def main() -> int:
    skill_root = Path(__file__).resolve().parent.parent
    visual_root = skill_root / "assets" / "procurement-visual-kit"
    routes = load_routes(Path(__file__).with_name("select_style_route.py"))
    errors: list[str] = []

    if len(routes) != 6:
        errors.append(f"expected 6 routes, found {len(routes)}")
    route_ids = [route["id"] for route in routes]
    if len(set(route_ids)) != len(route_ids):
        errors.append("route IDs are not unique")

    for route in routes:
        missing_fields = sorted(REQUIRED_ROUTE_FIELDS - set(route))
        if missing_fields:
            errors.append(f"{route.get('id', 'unknown')} missing fields: {', '.join(missing_fields)}")
            continue
        missing_tokens = sorted(REQUIRED_TOKENS - set(route["tokens"]))
        extra_tokens = sorted(set(route["tokens"]) - REQUIRED_TOKENS)
        if missing_tokens:
            errors.append(f"{route['id']} missing tokens: {', '.join(missing_tokens)}")
        if extra_tokens:
            errors.append(f"{route['id']} has extra tokens: {', '.join(extra_tokens)}")
        edge_treatment = route["edge_treatment"].lower()
        for required_phrase in ("single-edge", "pseudo-element", "inset shadow", "bounded surface"):
            if required_phrase not in edge_treatment:
                errors.append(
                    f"{route['id']} edge_treatment missing required phrase: {required_phrase}"
                )
        emphasis = route["emphasis"].lower()
        for required_phrase in ("complete neutral border", "full-surface", "inset"):
            if required_phrase not in emphasis:
                errors.append(
                    f"{route['id']} emphasis missing required phrase: {required_phrase}"
                )
        preview = visual_root / route["preview"]
        kit = visual_root / route["kit"]
        companion = visual_root / route["dynamic_ui_companion"]
        for label, path in (("preview", preview), ("kit", kit), ("companion", companion)):
            if not path.is_file():
                errors.append(f"{route['id']} missing {label}: {path}")
                continue
            try:
                ids = svg_ids(path)
            except ET.ParseError as exc:
                errors.append(f"{route['id']} invalid {label} SVG: {exc}")
                continue
            if label == "kit":
                missing = sorted(REQUIRED_KIT_IDS - ids)
                if missing:
                    errors.append(f"{route['id']} kit missing IDs: {', '.join(missing)}")

    manifest_paths = {str((visual_root / route["dynamic_ui_manifest"]).resolve()) for route in routes}
    if len(manifest_paths) != 1:
        errors.append("routes do not share one Dynamic UI companion manifest")
    else:
        manifest_path = Path(next(iter(manifest_paths)))
        if not manifest_path.is_file():
            errors.append(f"missing Dynamic UI companion manifest: {manifest_path}")
        else:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            layouts = manifest.get("layout_families", [])
            companion_routes = manifest.get("routes", [])
            if len(layouts) != 6:
                errors.append(f"expected 6 Dynamic UI layout families, found {len(layouts)}")
            panel_slots = {layout.get("panel_slot") for layout in layouts}
            if panel_slots != {"01", "02", "03", "04", "05", "06"}:
                errors.append("Dynamic UI panel slots must be exactly 01 through 06")
            manifest_route_ids = {route.get("route_id") for route in companion_routes}
            if manifest_route_ids != set(route_ids):
                errors.append("Dynamic UI manifest route IDs do not match style route IDs")
            boundary = manifest.get("system_boundary", {})
            if not boundary.get("ready_material_first"):
                errors.append("Dynamic UI manifest must preserve ready-material-first routing")
            if boundary.get("embed_companion_svg_in_widget") is not False:
                errors.append("Dynamic UI companions must never be embedded in widgets")
            if boundary.get("create_new_template_id") is not False:
                errors.append("Dynamic UI companions must not create procurement template IDs")
            for required_true in (
                "preserve_host_light_dark",
                "preserve_system_typography_spacing_radius",
                "preserve_system_root_selector_and_tool_protocol",
            ):
                if boundary.get(required_true) is not True:
                    errors.append(f"Dynamic UI boundary must set {required_true}=true")

    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print("PASS: 6 equal-weight routes; every preview, kit, companion, and Dynamic UI layout family is valid")
    return 0


if __name__ == "__main__":
    sys.exit(main())
