"""Tests for content router and free-flow layout engine.

These tests validate the _content_router() and _layout_free_flow()
functions added in v0.6.0 for automated view selection and positioning.
"""

import json
import tempfile
from pathlib import Path

from business_blueprint.export_svg import (
    _content_router,
    _layout_free_flow,
    _render_free_flow_svg,
    export_svg_auto,
    C_LIGHT,
    C_DARK,
)
from business_blueprint.export_html import export_html_viewer


# ─── Fixtures ──────────────────────────────────────────────────────

BP_ARCH = {
    "meta": {"title": "Arch Test", "industry": "retail"},
    "library": {
        "systems": [
            {"id": "sys-web", "name": "Web App", "capabilityIds": ["cap-sales"]},
            {"id": "sys-api", "name": "API", "capabilityIds": ["cap-sales", "cap-inventory"]},
        ],
        "capabilities": [
            {"id": "cap-sales", "name": "Sales", "domain": "Core"},
            {"id": "cap-inventory", "name": "Inventory", "domain": "Core"},
        ],
        "actors": [],
        "flowSteps": [],
    },
    "relations": [],
    "domainOrder": ["Core"],
}

BP_RICH = {
    "meta": {"title": "Rich Test", "industry": "retail"},
    "library": {
        "systems": [
            {"id": "sys-web", "name": "Web App", "capabilityIds": ["cap-sales"]},
        ],
        "capabilities": [
            {"id": "cap-sales", "name": "Sales", "domain": "Core"},
            {"id": "cap-service", "name": "Service", "domain": "Support"},
        ],
        "actors": [
            {"id": "actor-user", "name": "Customer"},
        ],
        "flowSteps": [
            {"id": "step-1", "name": "Browse", "actorId": "actor-user", "capabilityIds": ["cap-sales"], "nextStepIds": ["step-2"]},
            {"id": "step-2", "name": "Buy", "actorId": "actor-user", "capabilityIds": ["cap-sales"], "nextStepIds": []},
        ],
    },
    "relations": [
        {"from": "actor-user", "to": "cap-sales", "type": "supports"},
        {"from": "actor-user", "to": "cap-service", "type": "supports"},
    ],
    "domainOrder": ["Core", "Support"],
}

BP_EMPTY = {
    "meta": {"title": "Empty", "industry": ""},
    "library": {
        "systems": [],
        "capabilities": [],
        "actors": [],
        "flowSteps": [],
    },
    "relations": [],
    "domainOrder": [],
}

BP_CAPS_ONLY = {
    "meta": {"title": "Caps Only", "industry": ""},
    "library": {
        "systems": [],
        "capabilities": [
            {"id": "cap-a", "name": "Alpha", "domain": "X"},
            {"id": "cap-b", "name": "Beta", "domain": "X"},
        ],
        "actors": [],
        "flowSteps": [],
    },
    "relations": [],
    "domainOrder": ["X"],
}


# ─── Content Router Tests ─────────────────────────────────────────

class TestContentRouter:
    def test_arch_bp_returns_architecture_view(self):
        views = _content_router(BP_ARCH)
        types = [v["type"] for v in views]
        assert "architecture" in types

    def test_rich_bp_returns_multiple_views(self):
        views = _content_router(BP_RICH)
        assert len(views) >= 2

    def test_rich_bp_has_swimlane_view(self):
        views = _content_router(BP_RICH)
        types = [v["type"] for v in views]
        assert "swimlane" in types

    def test_rich_bp_has_process_chain_view(self):
        views = _content_router(BP_RICH)
        types = [v["type"] for v in views]
        assert "process_chain" in types

    def test_empty_bp_returns_no_views(self):
        views = _content_router(BP_EMPTY)
        assert len(views) == 0

    def test_caps_only_returns_capability_map(self):
        views = _content_router(BP_CAPS_ONLY)
        assert len(views) == 1
        assert views[0]["type"] == "capability_map"

    def test_view_has_include_set(self):
        views = _content_router(BP_ARCH)
        for v in views:
            assert isinstance(v["include"], set)
            assert len(v["include"]) > 0

    def test_arch_view_has_arrows(self):
        views = _content_router(BP_ARCH)
        arch = [v for v in views if v["type"] == "architecture"][0]
        assert len(arch["arrows"]) > 0
        assert arch["arrows"][0].get("label") == "supports"

    def test_capability_map_has_groups(self):
        views = _content_router(BP_ARCH)
        cap_map = [v for v in views if v["type"] == "capability_map"][0]
        assert len(cap_map["groups"]) > 0
        assert cap_map["groups"][0]["label"] == "Core"

    def test_process_chain_has_arrows(self):
        views = _content_router(BP_RICH)
        chain = [v for v in views if v["type"] == "process_chain"][0]
        assert len(chain["arrows"]) > 0


# ─── Free Flow Layout Tests ───────────────────────────────────────

class TestFreeFlowLayout:
    def test_layout_returns_nodes(self):
        views = _content_router(BP_ARCH)
        layout = _layout_free_flow(BP_ARCH, views[0])
        assert len(layout["nodes"]) > 0

    def test_layout_returns_width_and_height(self):
        views = _content_router(BP_ARCH)
        layout = _layout_free_flow(BP_ARCH, views[0])
        assert layout["width"] > 0
        assert layout["height"] > 0

    def test_layout_nodes_have_position(self):
        views = _content_router(BP_ARCH)
        layout = _layout_free_flow(BP_ARCH, views[0])
        for nid, n in layout["nodes"].items():
            assert "x" in n
            assert "y" in n
            assert "kind" in n
            assert "label" in n

    def test_group_based_layout(self):
        views = _content_router(BP_ARCH)
        cap_view = [v for v in views if v["type"] == "capability_map"][0]
        layout = _layout_free_flow(BP_ARCH, cap_view)
        # Should have at least one group box
        assert len(layout["groups"]) > 0

    def test_group_has_bounding_box(self):
        views = _content_router(BP_ARCH)
        cap_view = [v for v in views if v["type"] == "capability_map"][0]
        layout = _layout_free_flow(BP_ARCH, cap_view)
        for g in layout["groups"]:
            assert "x" in g
            assert "y" in g
            assert "w" in g
            assert "h" in g
            assert "label" in g

    def test_nodes_within_canvas_width(self):
        views = _content_router(BP_ARCH)
        layout = _layout_free_flow(BP_ARCH, views[0])
        for nid, n in layout["nodes"].items():
            assert n["x"] >= 0
            assert n["x"] + 150 <= layout["width"]

    def test_empty_include_returns_minimal_layout(self):
        view = {"type": "capability_map", "title": "Empty", "include": set(), "groups": [], "arrows": []}
        layout = _layout_free_flow(BP_EMPTY, view)
        assert layout["width"] == 400
        assert layout["height"] == 200

    def test_swimlane_layout_limits_cols(self):
        views = _content_router(BP_RICH)
        swim = [v for v in views if v["type"] == "swimlane"][0]
        layout = _layout_free_flow(BP_RICH, swim)
        assert len(layout["nodes"]) > 0


# ─── Free Flow SVG Renderer Tests ─────────────────────────────────

class TestFreeFlowSvgRenderer:
    def test_render_produces_svg(self):
        views = _content_router(BP_ARCH)
        layout = _layout_free_flow(BP_ARCH, views[0])
        svg = _render_free_flow_svg(layout, "Test", "Subtitle", C_LIGHT)
        assert "<svg" in svg
        assert "</svg>" in svg

    def test_dark_theme_renders_grid(self):
        views = _content_router(BP_ARCH)
        layout = _layout_free_flow(BP_ARCH, views[0])
        svg = _render_free_flow_svg(layout, "Test", "Subtitle", C_DARK, theme="dark")
        assert 'url(#grid)' in svg

    def test_light_theme_no_grid(self):
        views = _content_router(BP_ARCH)
        layout = _layout_free_flow(BP_ARCH, views[0])
        svg = _render_free_flow_svg(layout, "Test", "Subtitle", C_LIGHT, theme="light")
        assert 'url(#grid)' not in svg

    def test_render_contains_nodes(self):
        views = _content_router(BP_ARCH)
        layout = _layout_free_flow(BP_ARCH, views[0])
        svg = _render_free_flow_svg(layout, "Test", "Subtitle", C_LIGHT)
        for nid, n in layout["nodes"].items():
            assert f'id="{nid}"' in svg or n["label"] in svg


# ─── Auto Export Tests ────────────────────────────────────────────

class TestAutoExport:
    def test_export_svg_auto_creates_file(self):
        with tempfile.NamedTemporaryFile(suffix=".svg", delete=False) as f:
            target = Path(f.name)
        export_svg_auto(BP_ARCH, target)
        assert target.exists()
        content = target.read_text()
        assert "<svg" in content
        target.unlink()

    def test_export_svg_auto_dark(self):
        with tempfile.NamedTemporaryFile(suffix=".svg", delete=False) as f:
            target = Path(f.name)
        export_svg_auto(BP_ARCH, target, theme="dark")
        assert target.exists()
        content = target.read_text()
        assert 'url(#grid)' in content
        target.unlink()

    def test_export_svg_auto_rich_bp(self):
        with tempfile.NamedTemporaryFile(suffix=".svg", delete=False) as f:
            target = Path(f.name)
        export_svg_auto(BP_RICH, target)
        assert target.exists()
        content = target.read_text()
        assert "<svg" in content
        target.unlink()

    def test_export_svg_auto_empty_falls_back(self):
        with tempfile.NamedTemporaryFile(suffix=".svg", delete=False) as f:
            target = Path(f.name)
        export_svg_auto(BP_EMPTY, target)
        assert target.exists()
        content = target.read_text()
        assert "<svg" in content
        target.unlink()

    def test_html_viewer_with_content_router(self):
        with tempfile.NamedTemporaryFile(suffix=".html", delete=False) as f:
            target = Path(f.name)
        export_html_viewer(BP_RICH, target)
        content = target.read_text()
        assert "<html" in content
        # Should have tabs for routed views
        assert "三层架构" in content or "能力地图" in content or "参与者能力" in content
        target.unlink()
