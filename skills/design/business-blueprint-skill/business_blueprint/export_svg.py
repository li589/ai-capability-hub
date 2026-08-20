"""SVG exporter with container-based layout and semantic arrows.

Follows the fireworks-tech-graph pattern:
- layered containers with grid-based component layout
- semantic arrow system (solid/dashed/labelled) with SVG markers
- engineering-style title block
- clean vertical data flow, no crossing arrows
- proper z-ordering: bg → containers → arrows → label bg → nodes → text
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import Any
from xml.sax.saxutils import escape


# ─── Design tokens ───────────────────────────────────────────────

# Light theme (default) — warm, professional, matches DESIGN.md
C_LIGHT = {
    "bg": "#F8FAFC",
    "canvas": "#FFFFFF",
    "border": "#CBD5E1",
    "text_main": "#0F172A",
    "text_sub": "#64748B",
    "layer_header_bg": "#F1F5F9",
    "layer_border": "#E2E8F0",
    "cap_fill": "#E8F5F5",
    "cap_stroke": "#0B6E6E",
    "sys_fill": "#EFF6FF",
    "sys_stroke": "#3B82F6",
    "actor_fill": "#FFF7ED",
    "actor_stroke": "#F97316",
    "flow_fill": "#FEFCE8",
    "flow_stroke": "#CA8A04",
    "arrow": "#0B6E6E",
    "arrow_muted": "#94A3B8",
    "arrow_label": "#475569",
    "arrow_label_bg": "#FFFFFF",
}

# Dark theme — deep slate with vibrant accent colors
C_DARK = {
    "bg": "#020617",
    "canvas": "#0F172A",
    "border": "#1E293B",
    "text_main": "#E2E8F0",
    "text_sub": "#94A3B8",
    "layer_header_bg": "#0F172A",
    "layer_border": "#1E293B",
    "cap_fill": "#064E3B",
    "cap_stroke": "#34D399",
    "sys_fill": "#1E3A5F",
    "sys_stroke": "#60A5FA",
    "actor_fill": "#451A03",
    "actor_stroke": "#FB923C",
    "flow_fill": "#422006",
    "flow_stroke": "#FBBF24",
    "arrow": "#34D399",
    "arrow_muted": "#475569",
    "arrow_label": "#CBD5E1",
    "arrow_label_bg": "#1E293B",
}

# Backward compatibility alias
C = C_LIGHT


def _resolve_theme(name: str = "light") -> dict:
    """Return the color palette for the given theme."""
    return C_DARK if name == "dark" else C_LIGHT


# ─── Semantic colors by system category ──────────────────────────
# Maps system.category to (fill, stroke) for light and dark themes.
# When a system has no category, falls back to sys_fill/sys_stroke.
SYSTEM_CATEGORY_COLORS: dict[str, dict[str, dict[str, str]]] = {
    "frontend": {
        "light": {"fill": "#ECFEFF", "stroke": "#0891B2"},
        "dark": {"fill": "#083344", "stroke": "#22D3EE"},
    },
    "backend": {
        "light": {"fill": "#ECFDF5", "stroke": "#10B981"},
        "dark": {"fill": "#064E3B", "stroke": "#34D399"},
    },
    "database": {
        "light": {"fill": "#F5F3FF", "stroke": "#8B5CF6"},
        "dark": {"fill": "#2E1065", "stroke": "#A78BFA"},
    },
    "cloud": {
        "light": {"fill": "#FFFBEB", "stroke": "#F59E0B"},
        "dark": {"fill": "#451A03", "stroke": "#FBBF24"},
    },
    "security": {
        "light": {"fill": "#FFF1F2", "stroke": "#F43F5E"},
        "dark": {"fill": "#4C0519", "stroke": "#FB7185"},
    },
    "external": {
        "light": {"fill": "#F8FAFC", "stroke": "#64748B"},
        "dark": {"fill": "#1E293B", "stroke": "#94A3B8"},
    },
}

# Category alias mapping: maps common category values to canonical keys
CATEGORY_ALIASES: dict[str, str] = {
    "web": "frontend",
    "mobile": "frontend",
    "ui": "frontend",
    "api": "backend",
    "service": "backend",
    "microservice": "backend",
    "storage": "database",
    "infra": "cloud",
    "infrastructure": "cloud",
    "devops": "cloud",
    "auth": "security",
    "third-party": "external",
    "third_party": "external",
    "saas": "external",
}


def _resolve_system_colors(category: str | None, theme: str) -> tuple[str, str]:
    """Get (fill, stroke) for a system node based on its category."""
    canonical = CATEGORY_ALIASES.get(category, category) if category else None
    palette = SYSTEM_CATEGORY_COLORS.get(canonical)
    if palette:
        colors = palette.get(theme, palette.get("light", {}))
        return colors.get("fill", ""), colors.get("stroke", "")
    return "", ""


FONT = "system-ui, -apple-system, sans-serif"
FONT_MONO = "'JetBrains Mono', 'SF Mono', monospace"

# Layout constants
NODE_W = 150
NODE_H = 44
NODE_RX = {"capability": 8, "system": 4, "actor": 22, "flowStep": 6}
LAYER_PAD = 28
LAYER_HEADER_H = 32
LAYER_GAP = 36
CANVAS_X = 40
CANVAS_PAD_TOP = 110  # room for title block
COL_GAP = 20


def _esc(s: str) -> str:
    return escape(str(s))


# ─── Node rendering ──────────────────────────────────────────────
def _node_svg(nid: str, label: str, x: int, y: int, kind: str,
              colors: dict | None = None, fill_override: str | None = None,
              stroke_override: str | None = None) -> str:
    c = colors if colors is not None else C
    kind_defaults = {
        "capability": (c["cap_fill"], c["cap_stroke"], NODE_RX["capability"]),
        "system": (c["sys_fill"], c["sys_stroke"], NODE_RX["system"]),
        "actor": (c["actor_fill"], c["actor_stroke"], NODE_RX["actor"]),
        "flowStep": (c["flow_fill"], c["flow_stroke"], NODE_RX["flowStep"]),
    }
    if fill_override is not None and stroke_override is not None:
        fill, stroke = fill_override, stroke_override
    else:
        fill, stroke, _ = kind_defaults.get(kind, kind_defaults["capability"])
    rx = NODE_RX.get(kind, 8)
    return (
        f'<g class="node node-{kind}" id="{nid}">'
        f'<rect class="node-rect" x="{x}" y="{y}" width="{NODE_W}" height="{NODE_H}" '
        f'rx="{rx}" fill="{fill}" stroke="{stroke}" stroke-width="1.5"/>'
        f'<text class="node-label" x="{x + NODE_W // 2}" y="{y + NODE_H // 2 + 5}" '
        f'text-anchor="middle" font-size="12.5" fill="{c["text_main"]}" '
        f'font-family="{FONT}" font-weight="500">{_esc(label)}</text>'
        f'</g>'
    )


# ─── Arrow rendering with SVG markers ────────────────────────────
def _arrow_line(x1: int, y1: int, x2: int, y2: int,
                dashed: bool = False, color: str | None = None,
                colors: dict | None = None) -> str:
    """Draw just the arrow line + marker (no label)."""
    c = colors if colors is not None else C
    if color is None:
        color = c["arrow"] if not dashed else c["arrow_muted"]
    dash = f' stroke-dasharray="5,4"' if dashed else ""
    marker_id = "arrow-solid" if not dashed else "arrow-dashed"
    return (
        f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" '
        f'stroke="{color}" stroke-width="1.5"{dash} '
        f'marker-end="url(#{marker_id})"/>'
    )


def _arrow_label(mx: int, my: int, label: str,
                 colors: dict | None = None) -> str:
    """Draw arrow label with background rect for readability."""
    c = colors if colors is not None else C
    label_w = len(label) * 6 + 12
    return (
        f'<rect x="{mx - label_w // 2}" y="{my - 9}" '
        f'width="{label_w}" height="18" rx="3" '
        f'fill="{c["arrow_label_bg"]}" fill-opacity="0.9"/>'
        f'<text x="{mx}" y="{my + 4}" text-anchor="middle" '
        f'font-size="10" fill="{c["arrow_label"]}" font-family="{FONT}">{_esc(label)}</text>'
    )


def _node_center(n: dict) -> tuple[int, int]:
    return n["x"] + NODE_W // 2, n["y"] + NODE_H // 2


def _edge_point(n: dict, tx: int, ty: int) -> tuple[int, int]:
    """Calculate where the arrow should connect on the node's edge.

    For vertical connections (same column), connect to bottom/top center.
    For diagonal connections, compute the intersection with the node border.
    """
    cx, cy = _node_center(n)
    dx, dy = tx - cx, ty - cy
    if dx == 0 and dy == 0:
        return cx, cy
    hw, hh = NODE_W / 2, NODE_H / 2
    t = min(hw / abs(dx) if dx else 1e9, hh / abs(dy) if dy else 1e9)
    return int(cx + dx * t), int(cy + dy * t)


# ─── Column-based layout ─────────────────────────────────────────
def _layout_architecture(blueprint: dict[str, Any]) -> dict:
    """Position nodes in columns so arrows flow vertically without crossing.

    Strategy (fireworks-tech-graph pattern):
    1. Layer 0: Systems (top)
    2. Layer 1: Capabilities (middle)
    3. Layer 2: Flow Steps (bottom)
    4. Align columns by capability-support relationship so arrows go straight down.
    """
    lib = blueprint.get("library", {})
    systems = lib.get("systems", [])
    capabilities = lib.get("capabilities", [])
    flow_steps = lib.get("flowSteps", [])
    actors = lib.get("actors", [])

    # Build capability → systems map
    cap_to_systems: dict[str, list[str]] = {c["id"]: [] for c in capabilities}
    for s in systems:
        for cid in s.get("capabilityIds", []):
            if cid in cap_to_systems:
                cap_to_systems[cid].append(s["id"])

    # Build columns: each column = (system, capability it supports)
    # A system can span multiple columns if it supports multiple capabilities
    used_systems: set[str] = set()
    used_caps: set[str] = set()
    columns: list[tuple[str | None, str | None]] = []

    # First pass: pair systems with their capabilities
    for cap in capabilities:
        cid = cap["id"]
        supporting = cap_to_systems.get(cid, [])
        if supporting:
            for sid in supporting:
                columns.append((sid, cid))
                used_systems.add(sid)
                used_caps.add(cid)
        else:
            # Capability with no system support → standalone column
            columns.append((None, cid))
            used_caps.add(cid)

    # Add orphan systems (no capability linkage)
    for s in systems:
        if s["id"] not in used_systems:
            columns.append((s["id"], None))
            used_systems.add(s["id"])

    # Add orphan capabilities
    for c in capabilities:
        if c["id"] not in used_caps:
            columns.append((None, c["id"]))
            used_caps.add(c["id"])

    # Deduplicate columns by system (one column per system, with all its caps)
    # Group by system
    sys_columns: dict[str, list[str | None]] = {}  # sys_id → [cap_ids]
    standalone_caps: list[str] = []
    for sid, cid in columns:
        if sid:
            sys_columns.setdefault(sid, []).append(cid)
        elif cid:
            standalone_caps.append(cid)

    # Build ordered column list
    ordered_columns: list[dict] = []
    for sid in sys_columns:
        ordered_columns.append({"system": sid, "caps": sys_columns[sid]})
    for cid in standalone_caps:
        ordered_columns.append({"system": None, "caps": [cid]})

    n_cols = len(ordered_columns)
    if n_cols == 0:
        return {"nodes": {}, "arrows": [], "layers": [], "width": 500, "height": 300}

    total_w = n_cols * NODE_W + max(0, n_cols - 1) * COL_GAP
    start_x = CANVAS_X + (max(600, total_w) - total_w) // 2 + LAYER_PAD

    nodes: dict[str, dict] = {}
    arrows_list: list[dict] = []

    # ── Vertical layout model ──
    # Pass 1: place all nodes with fixed content_y per layer
    # Pass 2: compute border_h from actual content extents
    layer_y = 72  # below title block (y=10, h=52) + 10px gap

    # Phase: layer index for each node
    node_layer: dict[str, int] = {}

    # Layer metadata (filled in pass 2)
    layer_metas: list[dict] = []

    # ── Row 0: Systems ──
    if systems:
        li = len(layer_metas)
        content_y = layer_y + LAYER_HEADER_H + LAYER_PAD
        for col_idx, col in enumerate(ordered_columns):
            x = start_x + col_idx * (NODE_W + COL_GAP)
            if col["system"]:
                sys_node = next((s for s in systems if s["id"] == col["system"]), None)
                if sys_node:
                    nodes[sys_node["id"]] = {
                        "x": x, "y": content_y,
                        "kind": "system",
                        "label": sys_node.get("name", sys_node["id"]),
                    }
                    node_layer[sys_node["id"]] = li
        layer_metas.append({
            "label": "Application Systems",
            "header_y": layer_y,
            "content_y": content_y,
        })
        layer_y = layer_y + LAYER_HEADER_H + LAYER_PAD + NODE_H + LAYER_PAD + LAYER_GAP

    # ── Actors: always placed to the right in 2 columns ──
    if actors:
        first_meta = layer_metas[0] if layer_metas else None
        if first_meta:
            content_y = first_meta["content_y"]
            actor_col_count = 2 if len(actors) > 4 else 1
            actor_gap = 12
            actor_w = NODE_W
            total_actor_w = actor_col_count * actor_w + max(0, actor_col_count - 1) * actor_gap
            x_actor_start = start_x + n_cols * (NODE_W + COL_GAP) + COL_GAP
            y_actor_start = content_y

            for ai, a in enumerate(actors):
                col = ai // actor_col_count
                row = ai % actor_col_count
                nodes[a["id"]] = {
                    "x": int(x_actor_start + row * (actor_w + actor_gap)),
                    "y": y_actor_start + col * (NODE_H + 12),
                    "kind": "actor",
                    "label": a.get("name", a["id"]),
                }
                node_layer[a["id"]] = 0

    # ── Row 1: Capabilities ──
    if capabilities:
        li = len(layer_metas)
        content_y = layer_y + LAYER_HEADER_H + LAYER_PAD
        col_cap_count: dict[int, int] = {}
        for col_idx, col in enumerate(ordered_columns):
            x = start_x + col_idx * (NODE_W + COL_GAP)
            for cid in col["caps"]:
                cap_node = next((c for c in capabilities if c["id"] == cid), None)
                if cap_node:
                    row_in_col = col_cap_count.get(col_idx, 0)
                    col_cap_count[col_idx] = row_in_col + 1
                    nodes[cid] = {
                        "x": x, "y": content_y + row_in_col * (NODE_H + 10),
                        "kind": "capability",
                        "label": cap_node.get("name", cid),
                    }
                    node_layer[cid] = li
                    sid = col["system"]
                    if sid and sid in nodes:
                        arrows_list.append({
                            "from": sid, "to": cid, "label": "supports", "dashed": False,
                        })
        layer_metas.append({
            "label": "Business Capabilities",
            "header_y": layer_y,
            "content_y": content_y,
        })
        max_cap_rows = max(col_cap_count.values(), default=1)
        layer_y = layer_y + LAYER_HEADER_H + LAYER_PAD + max_cap_rows * (NODE_H + 10) + LAYER_GAP

    # ── Row 2: Flow Steps ──
    if flow_steps:
        flow_nodes: list[dict] = list(flow_steps)

        col_flow_count: dict[int, int] = {}
        cap_col_map: dict[str, int] = {}
        for col_idx, col in enumerate(ordered_columns):
            for cid in col["caps"]:
                if cid:
                    cap_col_map[cid] = col_idx

        li = len(layer_metas)
        content_y = layer_y + LAYER_HEADER_H + LAYER_PAD
        for i, fs in enumerate(flow_nodes):
            best_col = i % max(n_cols, 1)
            for cid in fs.get("capabilityIds", []):
                if cid in cap_col_map:
                    best_col = cap_col_map[cid]
                    break
            row_in_col = col_flow_count.get(best_col, 0)
            col_flow_count[best_col] = row_in_col + 1
            x = start_x + best_col * (NODE_W + COL_GAP)
            y = content_y + row_in_col * (NODE_H + 10)
            nodes[fs["id"]] = {
                "x": x, "y": y,
                "kind": "flowStep",
                "label": fs.get("name", fs["id"]),
            }
            node_layer[fs["id"]] = li
            for cid in fs.get("capabilityIds", []):
                if cid in nodes:
                    arrows_list.append({
                        "from": cid, "to": fs["id"], "label": "", "dashed": True,
                    })

        layer_metas.append({
            "label": "Process Flows",
            "header_y": layer_y,
            "content_y": content_y,
        })

    # ── Pass 2: compute border_h from actual node extents, reposition nodes ──
    for i, meta in enumerate(layer_metas):
        # Step 2a: compute border_h from current node extents
        content_y = meta["content_y"]
        max_bottom = content_y
        for nid, n in nodes.items():
            if node_layer.get(nid) == i:
                bottom = n["y"] + NODE_H
                if bottom > max_bottom:
                    max_bottom = bottom
        content_h = max_bottom - content_y
        meta["border_h"] = LAYER_HEADER_H + LAYER_PAD + content_h + LAYER_PAD

    # Step 2b: recompute layer positions and reposition all nodes
    current_y = 72
    for i, meta in enumerate(layer_metas):
        meta["border_y"] = current_y
        meta["header_y"] = current_y
        new_content_y = current_y + LAYER_HEADER_H + LAYER_PAD
        # Shift nodes in this layer
        y_delta = new_content_y - meta["content_y"]
        for nid, n in nodes.items():
            if node_layer.get(nid) == i:
                n["y"] += y_delta
        meta["content_y"] = new_content_y
        current_y += meta["border_h"] + LAYER_GAP

    # ── Build layer boxes from layer_metas ──
    layers = []
    for lm in layer_metas:
        layers.append({
            "label": lm["label"],
            "header_y": lm["header_y"],
            "y": lm["border_y"],
            "h": lm["border_h"],
        })

    # Calculate height (add room for legend at bottom)
    legend_h = 180  # space for legend
    max_y = max((n["y"] + NODE_H for n in nodes.values()), default=300)
    height = max_y + LAYER_PAD + 40 + legend_h

    # Width: fit all content + padding, accounting for actors if present
    content_max_x = max(
        max((n["x"] + NODE_W for n in nodes.values()), default=0),
        n_cols * (NODE_W + COL_GAP),
    )
    width = max(600, content_max_x + CANVAS_X * 2 + LAYER_PAD * 2)

    return {
        "nodes": nodes,
        "arrows": arrows_list,
        "layers": layers,
        "width": width,
        "height": height,
        "start_x": start_x,
    }


# ─── Content router ──────────────────────────────────────────────
def _content_router(blueprint: dict[str, Any]) -> list[dict[str, Any]]:
    """Analyze blueprint content and decide which views to generate.

    Returns a list of view specs, each with:
        - type: "architecture" | "capability_map" | "swimlane" | "process_chain"
        - title: display title for the view
        - include: set of entity ids to render in this view
        - groups: optional grouping hints (domains, lanes, etc.)
        - arrows: list of {from, to, label, dashed} for this view

    Routing rules:
        - Systems + capabilities → architecture view
        - Capabilities with domains → capability map (domain-grouped)
        - Actors + relations → swimlane view
        - Flow steps with nextStepIds → process chain view
    """
    lib = blueprint.get("library", {})
    systems = lib.get("systems", [])
    capabilities = lib.get("capabilities", [])
    actors = lib.get("actors", [])
    flow_steps = lib.get("flowSteps", [])
    relations = blueprint.get("relations", [])

    views: list[dict[str, Any]] = []

    # ── Architecture view: systems → capabilities ──
    if systems and capabilities:
        sys_ids = {s["id"] for s in systems}
        cap_ids = {c["id"] for c in capabilities}
        # Include actors that support any capability in this view
        actor_ids = set()
        for rel in relations:
            from_id = rel.get("from", "")
            to_id = rel.get("to", "")
            if from_id.startswith("actor-") and to_id in cap_ids:
                actor_ids.add(from_id)

        arrows = []
        for s in systems:
            for cid in s.get("capabilityIds", []):
                if cid in cap_ids:
                    arrows.append({"from": s["id"], "to": cid, "label": "supports", "dashed": False})

        views.append({
            "type": "architecture",
            "title": "Application Architecture",
            "include": sys_ids | cap_ids | actor_ids,
            "groups": [],
            "arrows": arrows,
        })

    # ── Capability map: domain-grouped capabilities ──
    if capabilities:
        domain_caps: dict[str, list[str]] = {}
        for cap in capabilities:
            domain = cap.get("domain", cap.get("category", "Uncategorized"))
            domain_caps.setdefault(domain, []).append(cap["id"])

        views.append({
            "type": "capability_map",
            "title": "Capability Map",
            "include": {c["id"] for c in capabilities},
            "groups": [{"label": d, "ids": cids} for d, cids in domain_caps.items()],
            "arrows": [],
        })

    # ── Swimlane view: actors with their capabilities ──
    if actors and relations:
        actor_cap_map: dict[str, list[str]] = {}
        for rel in relations:
            from_id = rel.get("from", "")
            to_ids = [t.strip() for t in str(rel.get("to", "")).split(",") if t.strip()]
            if from_id.startswith("actor-"):
                actor_cap_map.setdefault(from_id, []).extend(to_ids)

        if actor_cap_map:
            include_ids: set[str] = set()
            for aid, cids in actor_cap_map.items():
                include_ids.add(aid)
                include_ids.update(cids)

            views.append({
                "type": "swimlane",
                "title": "Actor-Capability Swimlane",
                "include": include_ids,
                "groups": [{"label": a.get("name", a["id"]), "ids": actor_cap_map.get(a["id"], [])} for a in actors if a["id"] in actor_cap_map],
                "arrows": [],
            })

    # ── Process chain: flow steps with sequencing ──
    if flow_steps:
        chained = [fs for fs in flow_steps if fs.get("nextStepIds") or fs.get("prevStepIds")]
        if chained or len(flow_steps) > 1:
            step_ids = {fs["id"] for fs in flow_steps}
            arrows = []
            for fs in flow_steps:
                for next_id in fs.get("nextStepIds", []):
                    if next_id in step_ids:
                        arrows.append({"from": fs["id"], "to": next_id, "label": fs.get("processName", ""), "dashed": False})
                # Also from actor to first step
                actor_id = fs.get("actorId", "")
                if actor_id and actor_id not in [a["from"] for a in arrows]:
                    arrows.append({"from": actor_id, "to": fs["id"], "label": "", "dashed": True})

            views.append({
                "type": "process_chain",
                "title": "Process Flow Chain",
                "include": step_ids | {fs.get("actorId", "") for fs in flow_steps if fs.get("actorId")},
                "groups": [],
                "arrows": arrows,
            })

    # Fallback: if nothing matched, generate a basic capability-only view
    if not views and capabilities:
        views.append({
            "type": "capability_map",
            "title": "Capabilities",
            "include": {c["id"] for c in capabilities},
            "groups": [{"label": "All", "ids": [c["id"] for c in capabilities]}],
            "arrows": [],
        })

    return views


# ─── Free-flow layout engine ─────────────────────────────────────
def _layout_free_flow(
    blueprint: dict[str, Any],
    view_spec: dict[str, Any],
    colors: dict | None = None,
) -> dict:
    """Compute free-form positions for nodes based on view spec.

    Unlike _layout_architecture() which uses rigid columns, this engine:
        - Groups nodes by domain/lane from view_spec["groups"]
        - Auto-wraps groups when they exceed canvas width
        - Positions nodes in a grid within each group
        - Returns positioned nodes, arrows, group bounding boxes, and canvas size

    Returns:
        {
            "nodes": {id: {x, y, kind, label, group}},
            "arrows": [{from, to, label, dashed}],
            "groups": [{label, x, y, w, h}],
            "width": int,
            "height": int,
        }
    """
    c = colors if colors is not None else C
    lib = blueprint.get("library", {})
    include = view_spec.get("include", set())

    # Build full entity lookup
    entity_map: dict[str, dict] = {}
    for s in lib.get("systems", []):
        entity_map[s["id"]] = {**s, "kind": "system"}
    for cap in lib.get("capabilities", []):
        entity_map[cap["id"]] = {**cap, "kind": "capability"}
    for actor in lib.get("actors", []):
        entity_map[actor["id"]] = {**actor, "kind": "actor"}
    for fs in lib.get("flowSteps", []):
        entity_map[fs["id"]] = {**fs, "kind": "flowStep"}

    # Filter to included entities
    entities = {eid: entity_map[eid] for eid in include if eid in entity_map}
    if not entities:
        return {"nodes": {}, "arrows": [], "groups": [], "width": 400, "height": 200}

    view_type = view_spec.get("type", "capability_map")
    groups = view_spec.get("groups", [])
    arrows = list(view_spec.get("arrows", []))

    # Layout parameters by view type
    layouts = {
        "architecture": {"card_w": NODE_W, "card_h": NODE_H, "gap": COL_GAP, "pad": LAYER_PAD, "cols_per_group": 0},
        "capability_map": {"card_w": 180, "card_h": 52, "gap": 14, "pad": 24, "cols_per_group": 0},
        "swimlane": {"card_w": 160, "card_h": 42, "gap": 12, "pad": 20, "cols_per_group": 0},
        "process_chain": {"card_w": 140, "card_h": 40, "gap": 20, "pad": 20, "cols_per_group": 0},
    }
    lp = layouts.get(view_type, layouts["capability_map"])
    card_w, card_h, gap, pad = lp["card_w"], lp["card_h"], lp["gap"], lp["pad"]

    # Max canvas width — auto-wrap groups that exceed this
    max_w = 1200
    content_w = max_w - CANVAS_X * 2

    nodes: dict[str, dict] = {}
    group_boxes: list[dict] = []
    current_y = 0

    if groups:
        # ── Group-based layout ──
        # Calculate group widths to determine wrapping
        group_widths: list[int] = []
        for g in groups:
            g_ids = [eid for eid in g.get("ids", []) if eid in entities]
            if not g_ids:
                group_widths.append(0)
                continue
            n = len(g_ids)
            # Estimate cols: fit as many as possible within a reasonable group width
            cols = max(1, min(n, int(content_w / (card_w + gap))))
            rows = math.ceil(n / cols) if cols > 0 else n
            gw = cols * (card_w + gap) - gap + pad * 2
            group_widths.append(gw)

        # Wrap groups into rows
        group_rows: list[list[int]] = [[]]
        row_w = 0
        for gi, gw in enumerate(group_widths):
            if gw == 0:
                continue
            if row_w + gw > content_w and group_rows[-1]:
                group_rows.append([])
                row_w = 0
            group_rows[-1].append(gi)
            row_w += gw + gap

        # Calculate row heights
        row_heights: list[int] = []
        for row in group_rows:
            max_h = 0
            for gi in row:
                g = groups[gi]
                g_ids = [eid for eid in g.get("ids", []) if eid in entities]
                n = len(g_ids)
                if view_type == "swimlane":
                    cols = max(1, min(n, 4))
                elif view_type == "process_chain":
                    cols = max(1, min(n, 6))
                else:
                    cols = max(1, min(n, int((content_w / len(group_rows[0]) if group_rows[0] else content_w) / (card_w + gap))))
                rows_count = math.ceil(n / cols) if cols > 0 else n
                gh = 28 + pad + rows_count * (card_h + gap) + pad  # header + pad + cards + pad
                if gh > max_h:
                    max_h = gh
            row_heights.append(max_h + gap)

        # Render groups
        y = 0
        for ri, row in enumerate(group_rows):
            row_start_y = y
            # Calculate available width for this row
            row_total_w = sum(group_widths[gi] for gi in row) + (len(row) - 1) * gap
            x_start = CANVAS_X + (content_w - row_total_w) / 2

            for gi in row:
                g = groups[gi]
                g_label = g.get("label", "")
                g_ids = [eid for eid in g.get("ids", []) if eid in entities]
                if not g_ids:
                    continue

                n = len(g_ids)
                if view_type == "swimlane":
                    cols = max(1, min(n, 4))
                elif view_type == "process_chain":
                    cols = max(1, min(n, min(6, n)))
                else:
                    row_group_count = len(row)
                    available_w = content_w / row_group_count - gap
                    cols = max(1, min(n, int(available_w / (card_w + gap))))

                rows_count = math.ceil(n / cols) if cols > 0 else n
                gw = cols * (card_w + gap) - gap + pad * 2
                gh = 28 + pad + rows_count * (card_h + gap) + pad

                gx = x_start
                group_boxes.append({"label": g_label, "x": gx, "y": row_start_y, "w": gw, "h": gh})

                # Place cards within group
                cx = gx + pad
                cy = row_start_y + 28 + pad
                for ci, eid in enumerate(g_ids):
                    col = ci % cols
                    row_in_group = ci // cols
                    nx = cx + col * (card_w + gap)
                    ny = cy + row_in_group * (card_h + gap)
                    ent = entities[eid]
                    nodes[eid] = {
                        "x": int(nx),
                        "y": int(ny),
                        "kind": ent["kind"],
                        "label": ent.get("name", eid),
                        "group": g_label,
                    }

                x_start += gw + gap
            y += row_heights[ri] if ri < len(row_heights) else gh + gap
    else:
        # ── Ungrouped layout: simple grid with auto-wrap ──
        ids = list(entities.keys())
        n = len(ids)
        cols = max(1, min(n, int(content_w / (card_w + gap))))
        rows = math.ceil(n / cols) if cols > 0 else n

        for i, eid in enumerate(ids):
            col = i % cols
            row = i // cols
            ent = entities[eid]
            nodes[eid] = {
                "x": CANVAS_X + col * (card_w + gap),
                "y": col * (card_h + gap),
                "kind": ent["kind"],
                "label": ent.get("name", eid),
                "group": "",
            }
        y = rows * (card_h + gap)

    # Calculate canvas size
    max_node_y = max((n["y"] + card_h for n in nodes.values()), default=0)
    max_group_bottom = max((g["y"] + g["h"] for g in group_boxes), default=0)
    height = max(max_node_y, max_group_bottom) + CANVAS_PAD_TOP + 60

    return {
        "nodes": nodes,
        "arrows": arrows,
        "groups": group_boxes,
        "width": max_w,
        "height": height,
    }


def _layer_svg(label: str, header_y: int, border_y: int, w: int, h: int,
               colors: dict | None = None) -> str:
    """Layer: border wraps header + content, header has its own bg color."""
    c = colors if colors is not None else C
    return (
        f'<g class="layer" id="layer-{_esc(label)}">'
        f'<rect class="layer-border" x="{CANVAS_X}" y="{border_y}" width="{w}" height="{h}" '
        f'rx="8" fill="none" stroke="{c["layer_border"]}" stroke-width="1"/>'
        f'<rect class="layer-header" x="{CANVAS_X}" y="{header_y}" width="{w}" height="{LAYER_HEADER_H}" '
        f'fill="{c["layer_header_bg"]}"/>'
        f'<text class="layer-label" x="{CANVAS_X + 16}" y="{header_y + LAYER_HEADER_H // 2 + 4}" '
        f'font-size="12" fill="{c["text_sub"]}" font-family="{FONT}" '
        f'font-weight="600" letter-spacing="0.4">{_esc(label)}</text>'
        f'</g>'
    )


def _title_svg(title: str, subtitle: str, w: int,
               colors: dict | None = None) -> str:
    c = colors if colors is not None else C
    ty = 10
    return (
        f'<g class="title-block">'
        f'<rect x="{CANVAS_X}" y="{ty}" width="{w}" height="52" '
        f'rx="6" fill="{c["canvas"]}" stroke="{c["border"]}" stroke-width="1"/>'
        f'<text x="{CANVAS_X + 16}" y="{ty + 24}" '
        f'font-size="16" fill="{c["text_main"]}" font-family="{FONT}" '
        f'font-weight="700">{_esc(title)}</text>'
        f'<text x="{CANVAS_X + 16}" y="{ty + 42}" '
        f'font-size="11" fill="{c["text_sub"]}" font-family="{FONT_MONO}">'
        f'{_esc(subtitle)}</text>'
        f'</g>'
    )


def _legend_svg(x: int, y: int, colors: dict | None = None) -> str:
    """Legend showing node types and arrow meanings (fireworks-tech-graph pattern)."""
    c = colors if colors is not None else C
    items = [
        ("System", c["sys_fill"], c["sys_stroke"], 4),
        ("Capability", c["cap_fill"], c["cap_stroke"], 8),
        ("Flow Step", c["flow_fill"], c["flow_stroke"], 6),
        ("Actor", c["actor_fill"], c["actor_stroke"], 22),
    ]
    legend_total_h = 30 + len(items) * 22 + 4 + 2 * 22 + 8  # items + gap + arrows + padding
    parts = [
        f'<g class="legend" transform="translate({x}, {y})">',
        f'<rect x="0" y="0" width="130" height="{legend_total_h}" '
        f'rx="6" fill="{c["canvas"]}" stroke="{c["border"]}" stroke-width="1" opacity="0.95"/>',
        f'<text x="12" y="20" font-size="10" fill="{c["text_sub"]}" '
        f'font-family="{FONT}" font-weight="600" letter-spacing="0.3">LEGEND</text>',
    ]
    for i, (label, fill, stroke, rx) in enumerate(items):
        ly = 38 + i * 22
        parts.append(
            f'<rect x="12" y="{ly}" width="18" height="14" rx="{rx}" '
            f'fill="{fill}" stroke="{stroke}" stroke-width="1"/>'
            f'<text x="38" y="{ly + 11}" font-size="9.5" fill="{c["text_sub"]}" '
            f'font-family="{FONT}">{label}</text>'
        )
    # Arrow styles
    arrow_y = 38 + len(items) * 22 + 4
    parts.append(
        f'<line x1="12" y1="{arrow_y}" x2="30" y2="{arrow_y}" '
        f'stroke="{c["arrow"]}" stroke-width="1.5" marker-end="url(#arrow-solid)"/>'
        f'<text x="38" y="{arrow_y + 4}" font-size="9.5" fill="{c["text_sub"]}" '
        f'font-family="{FONT}">supports</text>'
    )
    parts.append(
        f'<line x1="12" y1="{arrow_y + 22}" x2="30" y2="{arrow_y + 22}" '
        f'stroke="{c["arrow_muted"]}" stroke-width="1.5" stroke-dasharray="5,4" '
        f'marker-end="url(#arrow-dashed)"/>'
        f'<text x="38" y="{arrow_y + 26}" font-size="9.5" fill="{c["text_sub"]}" '
        f'font-family="{FONT}">flow-to</text>'
    )
    parts.append('</g>')
    return "\n".join(parts)


# ─── SVG defs (markers) ──────────────────────────────────────────
def _svg_defs(colors: dict | None = None, theme: str = "light") -> str:
    """SVG marker definitions for arrowheads.

    For dark theme, also includes a grid pattern definition.
    """
    c = colors if colors is not None else C
    grid_pattern = ""
    if theme == "dark":
        grid_pattern = (
            f'<pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">'
            f'<path d="M 40 0 L 0 0 0 40" fill="none" stroke="#1E293B" stroke-width="0.5"/>'
            f'</pattern>'
        )
    return (
        '<defs>'
        f'{grid_pattern}'
        f'<marker id="arrow-solid" markerWidth="10" markerHeight="8" '
        f'refX="9" refY="4" orient="auto" markerUnits="userSpaceOnUse">'
        f'<polygon points="0 0, 10 4, 0 8" fill="{c["arrow"]}"/>'
        f'</marker>'
        f'<marker id="arrow-dashed" markerWidth="10" markerHeight="8" '
        f'refX="9" refY="4" orient="auto" markerUnits="userSpaceOnUse">'
        f'<polygon points="0 0, 10 4, 0 8" fill="{c["arrow_muted"]}"/>'
        f'</marker>'
        '</defs>'
    )


# ─── Main export ─────────────────────────────────────────────────
def export_svg(blueprint: dict[str, Any], target: Path, theme: str = "light") -> None:
    """Export architecture diagram to SVG.

    Args:
        blueprint: The canonical blueprint JSON.
        target: Output file path.
        theme: Color theme — "light" (default) or "dark".
    """
    colors = _resolve_theme(theme)
    title = blueprint.get("meta", {}).get("title", "Business Blueprint")
    industry = blueprint.get("meta", {}).get("industry", "")
    subtitle = f"Industry: {industry}" if industry else "Application Architecture"

    layout = _layout_architecture(blueprint)
    w, h = layout["width"], layout["height"]

    # Background: solid for light, grid for dark
    if theme == "dark":
        bg_rect = (
            f'<rect width="{w}" height="{h}" fill="{colors["bg"]}"/>'
            f'<rect width="{w}" height="{h}" fill="url(#grid)"/>'
        )
    else:
        bg_rect = f'<rect width="{w}" height="{h}" fill="{colors["bg"]}"/>'

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
        f'font-family="{FONT}">',
        _svg_defs(colors=colors, theme=theme),
        bg_rect,
        _title_svg(title, subtitle, w, colors=colors),
    ]

    # Layer backgrounds (z-order: behind arrows and nodes)
    for layer in layout["layers"]:
        parts.append(_layer_svg(
            layer["label"], layer["header_y"], layer["y"],
            w - CANVAS_X * 2, layer["h"], colors=colors
        ))

    # Build semantic color lookup for systems
    systems_by_id = {}
    for s in blueprint.get("library", {}).get("systems", []):
        systems_by_id[s["id"]] = s

    # Arrows (z-order: behind nodes, above layer backgrounds)
    # Pass 1: draw all lines
    arrow_labels: list[tuple[int, int, str]] = []
    for arrow in layout["arrows"]:
        src = layout["nodes"].get(arrow["from"])
        tgt = layout["nodes"].get(arrow["to"])
        if not src or not tgt:
            continue
        # Skip arrows between different columns that would cross
        start_x = layout.get("start_x", CANVAS_X + LAYER_PAD)
        src_col = (src["x"] - start_x) // (NODE_W + COL_GAP) if COL_GAP else 0
        tgt_col = (tgt["x"] - start_x) // (NODE_W + COL_GAP) if COL_GAP else 0
        if abs(src_col - tgt_col) > 0 and arrow.get("label") == "supports":
            continue
        sx, sy = _node_center(src)
        tx, ty = _node_center(tgt)
        sx, sy = _edge_point(src, tx, ty)
        tx, ty = _edge_point(tgt, sx, sy)
        parts.append(
            _arrow_line(sx, sy, tx, ty,
                        dashed=arrow.get("dashed", False), colors=colors)
        )
        if arrow.get("label"):
            mx = (sx + tx) // 2
            my = (sy + ty) // 2
            arrow_labels.append((mx, my, arrow["label"]))

    # Pass 2: draw all labels on top of arrows (background masks the line)
    for mx, my, label in arrow_labels:
        parts.append(_arrow_label(mx, my, label, colors=colors))

    # Nodes (z-order: on top of arrows)
    for nid, n in layout["nodes"].items():
        kind = n["kind"]
        # Apply semantic colors for system nodes
        fill_ov, stroke_ov = None, None
        if kind == "system":
            sys_data = systems_by_id.get(nid, {})
            category = sys_data.get("category", "")
            if category:
                fill_ov, stroke_ov = _resolve_system_colors(category, theme)
        parts.append(_node_svg(
            nid, n["label"], n["x"], n["y"], kind,
            colors=colors, fill_override=fill_ov, stroke_override=stroke_ov
        ))

    # Legend (bottom-left, fireworks-tech-graph pattern)
    parts.append(_legend_svg(CANVAS_X + 10, h - 180 - 10, colors=colors))

    # Summary cards (bottom-center)
    lib_summary = blueprint.get("library", {})
    n_systems = len(lib_summary.get("systems", []))
    n_capabilities = len(lib_summary.get("capabilities", []))
    n_actors = len(lib_summary.get("actors", []))
    n_flow_steps = len(lib_summary.get("flowSteps", []))
    systems_with_caps = sum(1 for s in lib_summary.get("systems", []) if s.get("capabilityIds"))
    sys_coverage = f"{int(systems_with_caps / n_systems * 100)}%" if n_systems else "N/A"

    card_y = h - 50
    card_data = [
        ("SYSTEMS", str(n_systems)),
        ("CAPABILITIES", str(n_capabilities)),
        ("ACTORS", str(n_actors)),
        ("FLOW STEPS", str(n_flow_steps)),
        ("COVERAGE", sys_coverage),
    ]
    card_w = 110
    card_h = 38
    total_cards_w = len(card_data) * card_w + (len(card_data) - 1) * 12
    cards_start_x = (w - total_cards_w) / 2
    for ci, (label, value) in enumerate(card_data):
        cx = cards_start_x + ci * (card_w + 12)
        parts.append(
            f'<g class="summary-card">'
            f'<rect x="{cx}" y="{card_y}" width="{card_w}" height="{card_h}" '
            f'rx="6" fill="{colors["canvas"]}" stroke="{colors["border"]}" stroke-width="1"/>'
            f'<text x="{cx + card_w / 2}" y="{card_y + 17}" text-anchor="middle" '
            f'font-size="13" fill="{colors["text_main"]}" font-family="{FONT_MONO}" '
            f'font-weight="700">{value}</text>'
            f'<text x="{cx + card_w / 2}" y="{card_y + 32}" text-anchor="middle" '
            f'font-size="7.5" fill="{colors["text_sub"]}" font-family="{FONT}" '
            f'letter-spacing="0.3">{label}</text>'
            f'</g>'
        )

    parts.append("</svg>")
    target.write_text("\n".join(parts), encoding="utf-8")


# ─── Free-flow SVG renderer ──────────────────────────────────────
def _render_free_flow_svg(
    layout: dict[str, Any],
    title: str,
    subtitle: str,
    colors: dict,
    theme: str = "light",
    view_type: str = "capability_map",
) -> str:
    """Render a free-flow layout dict into an SVG string.

    Handles group backgrounds, node rendering, and arrow routing.
    """
    w = layout["width"]
    h = layout["height"]
    nodes = layout["nodes"]
    arrows = layout["arrows"]
    groups = layout["groups"]

    card_h_by_kind = {
        "capability": 52,
        "system": NODE_H,
        "actor": NODE_H,
        "flowStep": 40,
    }

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" font-family="{FONT}">',
        _svg_defs(colors=colors, theme=theme),
    ]

    # Background
    if theme == "dark":
        parts.append(f'<rect width="{w}" height="{h}" fill="{colors["bg"]}"/>')
        parts.append(f'<rect width="{w}" height="{h}" fill="url(#grid)"/>')
    else:
        parts.append(f'<rect width="{w}" height="{h}" fill="{colors["bg"]}"/>')

    # Title
    parts.append(_title_svg(title, subtitle, w, colors=colors))

    # Group backgrounds (z-order: behind nodes)
    for g in groups:
        label = g["label"]
        gx, gy, gw, gh = g["x"], g["y"] + CANVAS_PAD_TOP, g["w"], g["h"]
        stroke = colors.get("cap_stroke", "#0B6E6E")
        fill = colors.get("cap_fill", "#E8F5F5")
        parts.append(
            f'<rect x="{gx}" y="{gy}" width="{gw}" height="{gh}" '
            f'rx="10" fill="{fill}" stroke="{stroke}" stroke-width="1" opacity="0.3"/>'
        )
        parts.append(
            f'<text x="{gx + gw / 2}" y="{gy + 18}" '
            f'text-anchor="middle" font-size="11" fill="{stroke}" '
            f'font-weight="600">{_esc(label)}</text>'
        )

    # Arrows
    arrow_labels: list[tuple[int, int, str]] = []
    for arrow in arrows:
        src = nodes.get(arrow["from"])
        tgt = nodes.get(arrow["to"])
        if not src or not tgt:
            continue
        sx = src["x"] + NODE_W // 2
        sy = src["y"] + NODE_H
        tx = tgt["x"] + NODE_W // 2
        ty = tgt["y"]
        parts.append(
            _arrow_line(sx, sy, tx, ty,
                        dashed=arrow.get("dashed", False), colors=colors)
        )
        if arrow.get("label"):
            arrow_labels.append(((sx + tx) // 2, (sy + ty) // 2, arrow["label"]))
    for mx, my, label in arrow_labels:
        parts.append(_arrow_label(mx, my, label, colors=colors))

    # Nodes
    for nid, n in nodes.items():
        kind = n["kind"]
        ch = card_h_by_kind.get(kind, NODE_H)
        parts.append(
            _node_svg(nid, n["label"], n["x"], n["y"], kind, colors=colors)
        )

    parts.append("</svg>")
    return "\n".join(parts)


# ─── Auto-export: content router + free flow layout ──────────────
def export_svg_auto(blueprint: dict[str, Any], target: Path, theme: str = "light") -> None:
    """Export using content routing and free-flow layout.

    Automatically decides which views to generate based on blueprint content,
    computes free-form positions, and renders all views into a single SVG.

    Args:
        blueprint: The canonical blueprint JSON.
        target: Output file path.
        theme: Color theme — "light" (default) or "dark".
    """
    colors = _resolve_theme(theme)
    views = _content_router(blueprint)

    if not views:
        # Fallback to the classic layout
        export_svg(blueprint, target, theme=theme)
        return

    title = blueprint.get("meta", {}).get("title", "Business Blueprint")
    industry = blueprint.get("meta", {}).get("industry", "")

    # If there's only one view, render it directly
    if len(views) == 1:
        view = views[0]
        layout = _layout_free_flow(blueprint, view, colors=colors)
        subtitle = view["title"]
        svg_str = _render_free_flow_svg(layout, title, subtitle, colors, theme, view["type"])
        target.write_text(svg_str, encoding="utf-8")
        return

    # Multiple views: stack them vertically into a single SVG
    all_parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="0" height="0" font-family="{FONT}">',
        _svg_defs(colors=colors, theme=theme),
    ]

    if theme == "dark":
        all_parts.append('<rect width="0" height="0" fill="url(#grid)"/>')
    else:
        all_parts.append('<rect width="0" height="0" fill="{colors["bg"]}"/>')

    current_y = 0
    max_w = 0

    for vi, view in enumerate(views):
        layout = _layout_free_flow(blueprint, view, colors=colors)
        subtitle = view["title"]
        view_svg = _render_free_flow_svg(layout, title, subtitle, colors, theme, view["type"])

        # Extract content between <svg> and </svg>
        content_start = view_svg.find(">") + 1
        content_end = view_svg.rfind("</svg>")
        view_content = view_svg[content_start:content_end]

        # Remove the inner svg header/defs from sub-views (keep only first)
        if vi == 0:
            all_parts.append(view_content)
        else:
            # Skip defs and bg rect, just add the content
            lines = view_content.split("\n")
            for line in lines:
                if "<defs>" in line or "</defs>" in line:
                    continue
                if line.strip().startswith("<rect") and ("width=" in line and "height=" in line and "fill=" in line and "url(#grid)" not in line):
                    # This is likely the bg rect — skip for sub-views
                    if view_content.count("<rect") > len(view.get("groups", [])) * 2:
                        continue
                all_parts.append(line)

        current_y = max(current_y, layout["height"])
        max_w = max(max_w, layout["width"])

    # Fix SVG dimensions
    total_h = sum(_layout_free_flow(blueprint, v, colors=colors)["height"] for v in views) + CANVAS_PAD_TOP
    all_parts[0] = f'<svg xmlns="http://www.w3.org/2000/svg" width="{max_w}" height="{total_h}" font-family="{FONT}">'

    # Fix the bg rect size
    for i, part in enumerate(all_parts):
        if '<rect width="0"' in part:
            all_parts[i] = f'<rect width="{max_w}" height="{total_h}" fill="{colors["bg"]}"/>'
            break

    all_parts.append("</svg>")
    target.write_text("\n".join(all_parts), encoding="utf-8")


# ─── Export: Product Tree / Genealogy ────────────────────────────
def export_product_tree_svg(blueprint: dict[str, Any], target: Path, theme: str = "light") -> None:
    """Product family tree: root → market segments → products with capability badges."""
    colors = _resolve_theme(theme)
    title = blueprint.get("meta", {}).get("title", "Product Family")
    lib = blueprint.get("library", {})
    systems = lib.get("systems", [])
    capabilities = lib.get("capabilities", [])
    relations = blueprint.get("relations", [])

    cap_by_id = {c["id"]: c for c in capabilities}
    sys_by_id = {s["id"]: s for s in systems}

    # Build evolution map: from_id → to_id
    evolve_map: dict[str, list[str]] = {}
    platform_powers: dict[str, list[str]] = {}
    for r in relations:
        if r["type"] == "powers":
            platform_powers.setdefault(r["from"], []).append(r["to"])
        elif r["type"] == "evolves-to" or r["label"] == "演进":
            evolve_map.setdefault(r["from"], []).append(r["to"])

    # Market segments — known system IDs for Kingdee products
    segments = [
        {"label": "PaaS平台", "ids": ["sys-cosmic"]},
        {"label": "大型企业", "ids": ["sys-galaxy", "sys-eas", "sys-shr"]},
        {"label": "中型企业", "ids": ["sys-cosmic-star"]},
        {"label": "小型企业", "ids": ["sys-star"]},
        {"label": "微小型", "ids": ["sys-jingdou", "sys-kis"]},
    ]

    # Filter to actual systems
    active_segments: list[dict] = []
    for seg in segments:
        matched = [s for s in systems if s["id"] in seg["ids"]]
        if matched:
            active_segments.append({"label": seg["label"], "sys_ids": [s["id"] for s in matched]})

    # Fallback
    if not active_segments and systems:
        active_segments = [{"label": "Products", "sys_ids": [s["id"] for s in systems]}]

    PAD_X = 50
    PAD_Y = 30
    NODE_H = 44
    CAP_H = 20
    COL_W = 220
    SEG_GAP = 16  # gap between segment group boxes
    SEG_INNER_PAD = 18  # inside group box
    ROOT_W = 160
    ROOT_H = 44

    # Color palette per segment
    seg_colors = {
        "PaaS平台": ("#4338CA", "#EEF2FF"),
        "大型企业": ("#0B6E6E", "#E8F5F5"),
        "中型企业": ("#0F7B6C", "#E8F5F5"),
        "小型企业": ("#059669", "#ECFDF5"),
        "微小型": ("#D97706", "#FEFCE8"),
    }

    # Pass 1: compute layout
    max_cols = 0
    total_seg_h = 0
    seg_layouts: list[dict] = []
    for seg in active_segments:
        n_cols = len(seg["sys_ids"])
        max_cols = max(max_cols, n_cols)
        # Compute max badge count across systems in this segment
        max_badges = 0
        for sid in seg["sys_ids"]:
            sys = sys_by_id.get(sid)
            if sys:
                max_badges = max(max_badges, len(sys.get("capabilityIds", [])))
        # Segment group height = label + pad + node row + badges
        seg_h = 24 + SEG_INNER_PAD + NODE_H + max(0, max_badges) * (CAP_H + 4) + 4
        total_seg_h += seg_h + SEG_GAP
        seg_layouts.append({"label": seg["label"], "sys_ids": seg["sys_ids"], "h": seg_h})

    canvas_w = PAD_X * 2 + max_cols * COL_W + (max_cols - 1) * 20
    root_y = PAD_Y + 92
    seg_y = root_y + ROOT_H + SEG_GAP + 30  # arrow space + gap

    parts: list[str] = []  # will prepend svg header after layout

    # Title block
    parts.append(
        f'<g class="title-block">'
        f'<rect x="{PAD_X}" y="{PAD_Y}" width="{canvas_w - PAD_X * 2}" height="52" '
        f'rx="6" fill="{colors["canvas"]}" stroke="{colors["border"]}" stroke-width="1"/>'
        f'<text x="{PAD_X + 16}" y="{PAD_Y + 24}" '
        f'font-size="16" fill="{colors["text_main"]}" font-family="{FONT}" '
        f'font-weight="700">{_esc(title)} — 产品谱系</text>'
        f'<text x="{PAD_X + 16}" y="{PAD_Y + 42}" '
        f'font-size="11" fill="{colors["text_sub"]}" font-family="{FONT_MONO}">'
        f'Kingdee Product Family</text></g>'
    )

    cx = canvas_w / 2

    # Root node
    parts.append(
        f'<rect class="node-rect" x="{cx - ROOT_W / 2}" y="{root_y}" width="{ROOT_W}" height="{ROOT_H}" '
        f'rx="8" fill="#1E293B" stroke="#0F172A" stroke-width="1.5"/>'
        f'<text class="node-label" x="{cx}" y="{root_y + ROOT_H / 2 + 5}" '
        f'text-anchor="middle" font-size="15" fill="#FFFFFF" '
        f'font-weight="700">金蝶 Kingdee</text>'
    )

    node_positions: dict[str, tuple[int, int]] = {}
    seg_top_y: dict[str, int] = {}  # for arrows

    current_y = seg_y
    for sl in seg_layouts:
        seg_label = sl["label"]
        stroke, fill = seg_colors.get(seg_label, ("#64748B", "#F8FAFC"))
        sys_ids = sl["sys_ids"]
        n = len(sys_ids)
        seg_w = n * COL_W + max(0, n - 1) * 20
        seg_start_x = cx - seg_w / 2

        seg_top_y[seg_label] = current_y

        # Segment group bg
        parts.append(
            f'<rect x="{seg_start_x - SEG_INNER_PAD}" y="{current_y}" '
            f'width="{seg_w + SEG_INNER_PAD * 2}" height="{sl["h"]}" '
            f'rx="10" fill="{fill}" stroke="{stroke}" stroke-width="1" opacity="0.6"/>'
        )
        # Segment label
        parts.append(
            f'<text x="{cx}" y="{current_y + 16}" text-anchor="middle" '
            f'font-size="11" fill="{stroke}" font-weight="600" letter-spacing="0.5">'
            f'{_esc(seg_label)}</text>'
        )

        ny = current_y + 28
        for ci, sid in enumerate(sys_ids):
            sys = sys_by_id.get(sid)
            if not sys:
                continue
            nx = int(seg_start_x + ci * (COL_W + 20))
            node_positions[sid] = (nx + COL_W // 2, ny + NODE_H // 2)

            parts.append(
                f'<rect class="node-rect" x="{nx}" y="{ny}" width="{COL_W}" height="{NODE_H}" '
                f'rx="6" fill="{colors["canvas"]}" stroke="{stroke}" stroke-width="1.5"/>'
                f'<text class="node-label" x="{nx + COL_W // 2}" y="{ny + NODE_H // 2 + 5}" '
                f'text-anchor="middle" font-size="12" fill="{colors["text_main"]}" '
                f'font-weight="600">{_esc(sys["name"])}</text>'
            )

            # Capability badges
            cap_ids = sys.get("capabilityIds", [])
            badge_y = ny + NODE_H + 6
            for j, cid in enumerate(cap_ids[:4]):
                cap = cap_by_id.get(cid, {})
                cap_name = cap.get("name", cid)
                bw = max(len(cap_name) * 7 + 12, 50)
                bx = nx + COL_W // 2 - bw // 2
                parts.append(
                    f'<rect x="{bx}" y="{badge_y + j * (CAP_H + 4)}" width="{bw}" height="{CAP_H}" '
                    f'rx="3" fill="{stroke}" opacity="0.15"/>'
                    f'<text x="{bx + bw // 2}" y="{badge_y + j * (CAP_H + 4) + CAP_H // 2 + 5}" '
                    f'text-anchor="middle" font-size="9" fill="{stroke}">{_esc(cap_name)}</text>'
                )

        current_y += sl["h"] + SEG_GAP

    canvas_h = current_y + PAD_Y  # bottom padding after last segment

    # Prepend SVG header
    header = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{canvas_w}" height="{canvas_h}" '
        f'font-family="{FONT}">',
        _svg_defs(colors=colors, theme=theme),
        f'<rect width="{canvas_w}" height="{canvas_h}" fill="{colors["bg"]}"/>',
    ]
    if theme == "dark":
        header.append(f'<rect width="{canvas_w}" height="{canvas_h}" fill="url(#grid)"/>')
    parts[0:0] = header

    # Arrows: root to each segment group
    for seg in active_segments:
        ry2 = seg_top_y[seg["label"]] + 14
        parts.append(
            f'<line x1="{cx}" y1="{root_y + ROOT_H}" x2="{cx}" y2="{ry2}" '
            f'stroke="{colors["arrow_muted"]}" stroke-width="1" stroke-dasharray="4,3" '
            f'marker-end="url(#arrow-dashed)"/>'
        )

    # Evolution arrows (EAS → 星瀚, etc.)
    for from_id, to_ids in evolve_map.items():
        for to_id in to_ids:
            if from_id in node_positions and to_id in node_positions:
                fx, fy = node_positions[from_id]
                tx, ty = node_positions[to_id]
                if abs(tx - fx) > 30:  # not in same column
                    dy = (fy + ty) / 2
                    parts.append(
                        f'<path d="M{fx},{fy} C{fx},{dy} {tx},{dy} {tx},{ty}" '
                        f'fill="none" stroke="#DC2626" stroke-width="1.5" stroke-dasharray="6,3" '
                        f'marker-end="url(#arrow-dashed)" opacity="0.6"/>'
                    )
                    # Label
                    mx, my = (fx + tx) // 2, dy
                    parts.append(
                        f'<rect x="{mx - 22}" y="{my - 8}" width="44" height="16" '
                        f'rx="3" fill="{colors["arrow_label_bg"]}"/>'
                        f'<text x="{mx}" y="{my + 4}" text-anchor="middle" '
                        f'font-size="9" fill="#DC2626" font-weight="500">演进</text>'
                    )

    # Platform arrows (苍穹 → 星瀚)
    for plat_id, targets in platform_powers.items():
        if plat_id in node_positions:
            px, py = node_positions[plat_id]
            for tgt_id in targets:
                if tgt_id in node_positions:
                    tx, ty = node_positions[tgt_id]
                    dy = (py + ty) / 2
                    parts.append(
                        f'<path d="M{px},{py + 22} C{px},{dy} {tx},{dy} {tx},{ty - 22}" '
                        f'fill="none" stroke="#4338CA" stroke-width="2" '
                        f'marker-end="url(#arrow-solid)" opacity="0.7"/>'
                    )
                    mx = (px + tx) // 2
                    my = dy
                    parts.append(
                        f'<rect x="{mx - 22}" y="{my - 8}" width="44" height="16" '
                        f'rx="3" fill="{colors["arrow_label_bg"]}"/>'
                        f'<text x="{mx}" y="{my + 4}" text-anchor="middle" '
                        f'font-size="9" fill="#4338CA" font-weight="500">支撑</text>'
                    )

    parts.append("</svg>")
    target.write_text("\n".join(parts), encoding="utf-8")


# ─── Export: Capability Matrix ───────────────────────────────────
def export_matrix_svg(blueprint: dict[str, Any], target: Path, theme: str = "light") -> None:
    colors = _resolve_theme(theme)
    """Matrix view: products as rows, capabilities as columns, coverage as cells."""
    title = blueprint.get("meta", {}).get("title", "Product Family")
    lib = blueprint.get("library", {})
    systems = lib.get("systems", [])
    capabilities = lib.get("capabilities", [])

    # Market segments for row grouping
    segments = [
        {"label": "PaaS平台", "ids": ["sys-cosmic"]},
        {"label": "大型企业", "ids": ["sys-galaxy", "sys-eas", "sys-shr"]},
        {"label": "中型企业", "ids": ["sys-cosmic-star"]},
        {"label": "小型企业", "ids": ["sys-star"]},
        {"label": "微小型", "ids": ["sys-jingdou", "sys-kis"]},
    ]

    cap_by_id = {c["id"]: c for c in capabilities}
    sys_by_id = {s["id"]: s for s in systems}
    cap_ids = [c["id"] for c in capabilities]
    n_cols = len(cap_ids)

    # Build ordered product list grouped by segment
    ordered_products: list[tuple[str, str | None]] = []
    for seg in segments:
        for sid in seg["ids"]:
            if sid in sys_by_id:
                ordered_products.append((sid, seg["label"]))
    # Fallback: all systems in one group
    if not ordered_products and systems:
        ordered_products = [(s["id"], None) for s in systems]

    PAD_X = 40
    PAD_Y = 30
    SEG_LABEL_W = 80
    PROD_NAME_W = 110
    CAP_COL_W = 100
    ROW_H = 40
    HEADER_H = 44
    ROW_GAP = 1
    n_rows = len(ordered_products)

    canvas_w = PAD_X * 2 + SEG_LABEL_W + PROD_NAME_W + n_cols * CAP_COL_W
    canvas_h = PAD_Y * 2 + HEADER_H + n_rows * ROW_H + (n_rows - 1) * ROW_GAP + 80

    seg_colors = {
        "PaaS平台": "#4338CA",
        "大型企业": "#0B6E6E",
        "中型企业": "#0F7B6C",
        "小型企业": "#059669",
        "微小型": "#D97706",
    }

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{canvas_w}" height="{canvas_h}" '
        f'font-family="{FONT}">',
        _svg_defs(colors=colors, theme=theme),
        f'<rect width="{canvas_w}" height="{canvas_h}" fill="{colors["bg"]}"/>',
    ]

    # Title
    parts.append(
        f'<g class="title-block">'
        f'<rect x="{PAD_X}" y="{PAD_Y}" width="{canvas_w - PAD_X * 2}" height="52" '
        f'rx="6" fill="{colors["canvas"]}" stroke="{colors["border"]}" stroke-width="1"/>'
        f'<text x="{PAD_X + 16}" y="{PAD_Y + 24}" '
        f'font-size="16" fill="{colors["text_main"]}" font-family="{FONT}" '
        f'font-weight="700">{_esc(title)} — 能力矩阵</text>'
        f'<text x="{PAD_X + 16}" y="{PAD_Y + 42}" '
        f'font-size="11" fill="{colors["text_sub"]}" font-family="{FONT_MONO}">'
        f'Capability Coverage Matrix</text></g>'
    )

    base_y = PAD_Y + 100
    left_w = SEG_LABEL_W + PROD_NAME_W

    # Header row
    parts.append(
        f'<rect x="{PAD_X}" y="{base_y}" width="{left_w}" height="{HEADER_H}" '
        f'rx="6" fill="{colors["canvas"]}" stroke="{colors["border"]}" stroke-width="1"/>'
    )
    parts.append(
        f'<text x="{PAD_X + left_w // 2}" y="{base_y + HEADER_H // 2 + 5}" '
        f'text-anchor="middle" font-size="13" fill="{colors["text_main"]}" '
        f'font-weight="600">产品 / 能力</text>'
    )

    for ci, cid in enumerate(cap_ids):
        cap = cap_by_id[cid]
        cx = PAD_X + left_w + ci * CAP_COL_W
        parts.append(
            f'<rect x="{cx}" y="{base_y}" width="{CAP_COL_W}" height="{HEADER_H}" '
            f'rx="0" fill="{colors["canvas"]}" stroke="{colors["border"]}" stroke-width="1"/>'
            f'<text x="{cx + CAP_COL_W // 2}" y="{base_y + HEADER_H // 2 + 5}" '
            f'text-anchor="middle" font-size="11" fill="{colors["text_main"]}" '
            f'font-weight="500">{_esc(cap["name"])}</text>'
        )

    # Data rows
    prev_seg: str | None = None
    for ri, (sid, seg_label) in enumerate(ordered_products):
        sys = sys_by_id[sid]
        row_y = base_y + HEADER_H + ri * (ROW_H + ROW_GAP)
        sys_cap_ids = set(sys.get("capabilityIds", []))

        stroke = seg_colors.get(seg_label or "", "#64748B")

        # Row bg
        parts.append(
            f'<rect x="{PAD_X}" y="{row_y}" width="{canvas_w - PAD_X * 2}" height="{ROW_H}" '
            f'rx="0" fill="{colors["canvas"]}" stroke="{colors["border"]}" stroke-width="0.5"/>'
        )

        # Segment label (first row of each group)
        if seg_label != prev_seg:
            parts.append(
                f'<text x="{PAD_X + 8}" y="{row_y + ROW_H // 2 + 5}" '
                f'font-size="10" fill="{stroke}" font-weight="600" '
                f'transform="rotate(-45, {PAD_X + 8}, {row_y + ROW_H // 2 + 5})">'
                f'{_esc(seg_label or "")}</text>'
            )
            prev_seg = seg_label

        # Product name
        parts.append(
            f'<text x="{PAD_X + SEG_LABEL_W + 8}" y="{row_y + ROW_H // 2 + 5}" '
            f'font-size="12" fill="{colors["text_main"]}" font-weight="500">'
            f'{_esc(sys["name"])}</text>'
        )

        # Capability cells
        for ci, cid in enumerate(cap_ids):
            cx = PAD_X + left_w + ci * CAP_COL_W
            if cid in sys_cap_ids:
                parts.append(
                    f'<rect x="{cx + 2}" y="{row_y + 2}" width="{CAP_COL_W - 4}" height="{ROW_H - 4}" '
                    f'rx="4" fill="{stroke}" opacity="0.2"/>'
                    f'<text x="{cx + CAP_COL_W // 2}" y="{row_y + ROW_H // 2 + 5}" '
                    f'text-anchor="middle" font-size="14" fill="{stroke}">✓</text>'
                )
            else:
                parts.append(
                    f'<text x="{cx + CAP_COL_W // 2}" y="{row_y + ROW_H // 2 + 5}" '
                    f'text-anchor="middle" font-size="14" fill="#E2E8F0">—</text>'
                )

    # Legend
    legend_y = base_y + HEADER_H + n_rows * (ROW_H + ROW_GAP) + 30
    parts.append(
        f'<text x="{PAD_X}" y="{legend_y}" font-size="10" fill="{colors["text_sub"]}">'
        f'■ 覆盖  — 未覆盖  | 颜色 = 市场分层</text>'
    )

    parts.append("</svg>")
    target.write_text("\n".join(parts), encoding="utf-8")


# ─── Export: Capability Map ──────────────────────────────────────
def export_capability_map_svg(blueprint: dict[str, Any], target: Path, theme: str = "light") -> None:
    colors = _resolve_theme(theme)
    """Capability map: grouped cards showing business capabilities and their supporting systems."""
    title = blueprint.get("meta", {}).get("title", "Business Blueprint")
    industry = blueprint.get("meta", {}).get("industry", "")
    lib = blueprint.get("library", {})
    capabilities = lib.get("capabilities", [])
    systems = lib.get("systems", [])
    actors = lib.get("actors", [])

    sys_by_id = {s["id"]: s for s in systems}
    actor_by_id = {a["id"]: a for a in actors}

    PAD_X = 50
    PAD_Y = 30
    CARD_W = 200
    CARD_H = 80
    CARD_GAP = 16

    # Dynamic grid calculation: adjust columns based on capability count
    n = len(capabilities)
    if n <= 4:
        COLS = min(n, 2)
    elif n <= 9:
        COLS = 3
    elif n <= 16:
        COLS = 4
    elif n <= 25:
        COLS = 5
    else:
        COLS = 6

    COL_W = CARD_W + CARD_GAP
    canvas_w = PAD_X * 2 + COLS * COL_W - CARD_GAP

    parts: list[str] = []

    # Title block
    subtitle = f"Industry: {industry}" if industry else "Capability Map"
    parts.extend([
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{canvas_w}" height="0" '
        f'font-family="{FONT}">',
        _svg_defs(colors=colors, theme=theme),
        f'<rect width="{canvas_w}" height="0" fill="{colors["bg"]}"/>',
    ])

    parts.append(
        f'<g class="title-block">'
        f'<rect x="{PAD_X}" y="{PAD_Y}" width="{canvas_w - PAD_X * 2}" height="52" '
        f'rx="6" fill="{colors["canvas"]}" stroke="{colors["border"]}" stroke-width="1"/>'
        f'<text x="{PAD_X + 16}" y="{PAD_Y + 24}" '
        f'font-size="16" fill="{colors["text_main"]}" font-family="{FONT}" '
        f'font-weight="700">{_esc(title)} — 能力地图</text>'
        f'<text x="{PAD_X + 16}" y="{PAD_Y + 42}" '
        f'font-size="11" fill="{colors["text_sub"]}" font-family="{FONT_MONO}">'
        f'{_esc(subtitle)}</text></g>'
    )

    # Color palette for capability levels
    level_colors = {
        0: ("#1E293B", "#F1F5F9"),
        1: ("#0B6E6E", "#E8F5F5"),
        2: ("#059669", "#ECFDF5"),
    }

    # Group capabilities by level
    by_level: dict[int, list[dict]] = {}
    for cap in capabilities:
        lvl = cap.get("level", 1)
        by_level.setdefault(lvl, []).append(cap)

    current_y = PAD_Y + 72
    canvas_h = current_y

    level_labels = {0: "战略层", 1: "核心层", 2: "支撑层"}

    for lvl in sorted(by_level.keys()):
        caps = by_level[lvl]
        stroke, fill = level_colors.get(lvl, ("#64748B", "#F8FAFC"))
        level_label = level_labels.get(lvl, f"L{lvl}")

        # Level header
        parts.append(
            f'<text x="{PAD_X}" y="{current_y}" font-size="13" fill="{stroke}" '
            f'font-weight="700" font-family="{FONT}">{level_label} ({len(caps)})</text>'
        )
        current_y += 14

        # Cards in grid
        n = len(caps)
        n_rows = math.ceil(n / COLS) if COLS > 0 else n
        card_block_h = n_rows * CARD_H + max(0, n_rows - 1) * CARD_GAP

        for i, cap in enumerate(caps):
            col = i % COLS
            row = i // COLS
            cx = PAD_X + col * COL_W
            cy = current_y + row * (CARD_H + CARD_GAP)

            sys_names = []
            for sid in cap.get("supportingSystemIds", []):
                s = sys_by_id.get(sid)
                if s:
                    sys_names.append(s["name"])

            parts.append(
                f'<rect x="{cx}" y="{cy}" width="{CARD_W}" height="{CARD_H}" '
                f'rx="6" fill="{fill}" stroke="{stroke}" stroke-width="1.5"/>'
                f'<text x="{cx + 12}" y="{cy + 20}" font-size="12" fill="{stroke}" '
                f'font-weight="600">{_esc(cap["name"])}</text>'
            )

            # Description (truncated)
            desc = cap.get("description", "")[:40]
            if desc:
                parts.append(
                    f'<text x="{cx + 12}" y="{cy + 36}" font-size="9" fill="{colors["text_sub"]}">'
                    f'{_esc(desc)}</text>'
                )

            # Supporting systems
            for j, sname in enumerate(sys_names[:3]):
                parts.append(
                    f'<rect x="{cx + 12}" y="{cy + 46 + j * 16}" width="{CARD_W - 24}" height="14" '
                    f'rx="3" fill="{colors["canvas"]}"/>'
                    f'<text x="{cx + 18}" y="{cy + 57 + j * 16}" font-size="8.5" fill="{colors["text_main"]}">'
                    f'{_esc(sname)}</text>'
                )

        current_y += card_block_h + 24
        canvas_h = current_y

    canvas_h += PAD_Y
    # Fix SVG header with computed height
    parts[0] = f'<svg xmlns="http://www.w3.org/2000/svg" width="{canvas_w}" height="{canvas_h}" font-family="{FONT}">'
    parts[2] = f'<rect width="{canvas_w}" height="{canvas_h}" fill="{colors["bg"]}"/>'

    parts.append("</svg>")
    target.write_text("\n".join(parts), encoding="utf-8")


# ─── Export: Swimlane Flow ───────────────────────────────────────
def export_swimlane_flow_svg(blueprint: dict[str, Any], target: Path, theme: str = "light") -> None:
    colors = _resolve_theme(theme)
    """Swimlane flow diagram: actors as lanes, flow steps as connected cards."""
    title = blueprint.get("meta", {}).get("title", "Business Blueprint")
    industry = blueprint.get("meta", {}).get("industry", "")
    lib = blueprint.get("library", {})
    actors = lib.get("actors", [])
    flow_steps = lib.get("flowSteps", [])
    capabilities = lib.get("capabilities", [])

    cap_by_id = {c["id"]: c for c in capabilities}
    actor_by_id = {a["id"]: a for a in actors}

    PAD_X = 50
    PAD_Y = 30
    LANE_HEADER_H = 36
    LANE_GAP = 16
    STEP_W = 160
    STEP_H = 40
    STEP_GAP = 14
    ARROW_GAP = 12

    # Group flow steps by actor
    steps_by_actor: dict[str, list[dict]] = {}
    for step in flow_steps:
        aid = step.get("actorId", "")
        steps_by_actor.setdefault(aid, []).append(step)

    actor_order: list[str] = [a["id"] for a in actors]

    canvas_w = 900
    content_w = canvas_w - PAD_X * 2

    parts: list[str] = []

    subtitle = f"Industry: {industry}" if industry else "Swimlane Flow"
    parts.extend([
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{canvas_w}" height="0" '
        f'font-family="{FONT}">',
        _svg_defs(colors=colors, theme=theme),
        f'<rect width="{canvas_w}" height="0" fill="{colors["bg"]}"/>',
    ])

    parts.append(
        f'<g class="title-block">'
        f'<rect x="{PAD_X}" y="{PAD_Y}" width="{content_w}" height="52" '
        f'rx="6" fill="{colors["canvas"]}" stroke="{colors["border"]}" stroke-width="1"/>'
        f'<text x="{PAD_X + 16}" y="{PAD_Y + 24}" '
        f'font-size="16" fill="{colors["text_main"]}" font-family="{FONT}" '
        f'font-weight="700">{_esc(title)} — 泳道流程</text>'
        f'<text x="{PAD_X + 16}" y="{PAD_Y + 42}" '
        f'font-size="11" fill="{colors["text_sub"]}" font-family="{FONT_MONO}">'
        f'{_esc(subtitle)}</text></g>'
    )

    lane_palette = [
        ("#0B6E6E", "#E8F5F5"),
        ("#059669", "#ECFDF5"),
        ("#4338CA", "#EEF2FF"),
        ("#D97706", "#FEFCE8"),
        ("#DC2626", "#FEF2F2"),
        ("#7C3AED", "#F5F3FF"),
        ("#0891B2", "#ECFEFF"),
        ("#65A30D", "#F7FEE7"),
        ("#C2410C", "#FFF7ED"),
        ("#475569", "#F8FAFC"),
        ("#9333EA", "#FAF5FF"),
    ]

    # First pass: compute lane heights and step positions for arrow drawing
    lane_positions: dict[str, dict] = {}  # actor_id → {"y": top_y, "steps": {step_id: (cx, cy)}}
    current_y = PAD_Y + 72

    for lane_idx, actor_id in enumerate(actor_order):
        actor = actor_by_id.get(actor_id)
        if not actor:
            continue
        stroke, fill = lane_palette[lane_idx % len(lane_palette)]
        steps = steps_by_actor.get(actor_id, [])
        lane_h = LANE_HEADER_H + LANE_GAP + len(steps) * (STEP_H + STEP_GAP) + LANE_GAP

        lane_positions[actor_id] = {
            "y": current_y,
            "h": lane_h,
            "stroke": stroke,
            "fill": fill,
            "steps": {},
        }

        step_y = current_y + LANE_HEADER_H + LANE_GAP
        for si, step in enumerate(steps):
            cx = PAD_X + 14 + STEP_W // 2
            cy = step_y + si * (STEP_H + STEP_GAP) + STEP_H // 2
            lane_positions[actor_id]["steps"][step["id"]] = (cx, cy)

        current_y += lane_h + LANE_GAP

    # Arrows layer (drawn before cards)
    arrow_parts: list[str] = []
    # Intra-lane arrows (sequential flow within same actor)
    for actor_id, steps in steps_by_actor.items():
        pos_data = lane_positions.get(actor_id)
        if not pos_data:
            continue
        stroke = pos_data["stroke"]
        for i in range(len(steps) - 1):
            _, from_cy = pos_data["steps"][steps[i]["id"]]
            to_cx, to_cy = pos_data["steps"][steps[i + 1]["id"]]
            from_y = from_cy + STEP_H // 2 + 4
            to_y = to_cy - STEP_H // 2 - 2

            if from_y < to_y:
                mid_y = (from_y + to_y) / 2
                arrow_parts.append(
                    f'<path d="M{PAD_X + 14 + STEP_W // 2},{from_y} '
                    f'C{PAD_X + 14 + STEP_W // 2},{mid_y} {to_cx},{mid_y} {to_cx},{to_y}" '
                    f'fill="none" stroke="{stroke}" stroke-width="1.5" opacity="0.4" '
                    f'marker-end="url(#arrow-solid)"/>'
                )

    # Cross-lane arrows: capability overlap implies connection
    for i, aid1 in enumerate(steps_by_actor):
        for j, aid2 in enumerate(steps_by_actor):
            if j <= i:
                continue
            p1 = lane_positions.get(aid1)
            p2 = lane_positions.get(aid2)
            if not p1 or not p2:
                continue
            s1 = steps_by_actor[aid1]
            s2 = steps_by_actor[aid2]
            # Connect first step of each lane
            if s1 and s2 and s1[0]["id"] in p1["steps"] and s2[0]["id"] in p2["steps"]:
                _, cy1 = p1["steps"][s1[0]["id"]]
                _, cy2 = p2["steps"][s2[0]["id"]]
                x1 = PAD_X + 14 + STEP_W + 4
                x2 = PAD_X + 14 + STEP_W + 4
                my = (cy1 + cy2) / 2
                arrow_parts.append(
                    f'<path d="M{x1},{cy1} C{x1 + 30},{my} {x2 + 30},{my} {x2},{cy2}" '
                    f'fill="none" stroke="#94A3B8" stroke-width="1" stroke-dasharray="4,3" opacity="0.3" '
                    f'marker-end="url(#arrow-dashed)"/>'
                )

    # Second pass: render lanes and cards
    current_y = PAD_Y + 72
    for lane_idx, actor_id in enumerate(actor_order):
        actor = actor_by_id.get(actor_id)
        if not actor:
            continue
        stroke, fill = lane_palette[lane_idx % len(lane_palette)]

        steps = steps_by_actor.get(actor_id, [])
        lane_h = LANE_HEADER_H + LANE_GAP + len(steps) * (STEP_H + STEP_GAP) + LANE_GAP

        # Lane background
        parts.append(
            f'<rect x="{PAD_X}" y="{current_y}" width="{content_w}" height="{lane_h}" '
            f'rx="6" fill="{fill}" stroke="{stroke}" stroke-width="0.5" opacity="0.5"/>'
        )
        # Lane label with step count
        parts.append(
            f'<text x="{PAD_X + 14}" y="{current_y + LANE_HEADER_H // 2 + 5}" '
            f'font-size="12" fill="{stroke}" font-weight="600">{_esc(actor["name"])} '
            f'<tspan font-size="10" fill="{colors["text_sub"]}">({len(steps)}步)</tspan></text>'
        )
        # Right side: capability tags summary
        all_caps = set()
        for s in steps:
            for cid in s.get("capabilityIds", []):
                all_caps.add(cid)
        cap_x = PAD_X + content_w - 14
        for ci, cid in enumerate(list(all_caps)[:4]):
            cap = cap_by_id.get(cid, {})
            tag_w = len(cap.get("name", "")) * 7 + 10
            tx = cap_x - ci * (tag_w + 4) - tag_w
            parts.append(
                f'<rect x="{tx}" y="{current_y + 8}" width="{tag_w}" height="18" '
                f'rx="3" fill="{stroke}" opacity="0.15"/>'
                f'<text x="{tx + tag_w // 2}" y="{current_y + 21}" '
                f'text-anchor="middle" font-size="8" fill="{stroke}">'
                f'{_esc(cap.get("name", ""))}</text>'
            )

        step_y = current_y + LANE_HEADER_H + LANE_GAP
        for si, step in enumerate(steps):
            sx = PAD_X + 14
            sy = step_y + si * (STEP_H + STEP_GAP)

            # Step number badge
            step_num = si + 1
            parts.append(
                f'<rect x="{sx}" y="{sy}" width="{STEP_W}" height="{STEP_H}" '
                f'rx="5" fill="{colors["canvas"]}" stroke="{stroke}" stroke-width="1.5"/>'
                f'<rect x="{sx + 2}" y="{sy + 2}" width="22" height="{STEP_H - 4}" '
                f'rx="4" fill="{stroke}" opacity="0.12"/>'
                f'<text x="{sx + 13}" y="{sy + STEP_H // 2 + 5}" '
                f'text-anchor="middle" font-size="12" fill="{stroke}" font-weight="700">{step_num}</text>'
                f'<text x="{sx + 32}" y="{sy + STEP_H // 2 + 5}" '
                f'font-size="11" fill="{colors["text_main"]}" font-weight="500">'
                f'{_esc(step["name"])}</text>'
            )

            # Capability tags
            cap_ids = step.get("capabilityIds", [])
            for j, cid in enumerate(cap_ids[:2]):
                cap = cap_by_id.get(cid, {})
                tag_x = sx + STEP_W + 8 + j * 80
                cap_name = cap.get("name", "")
                if cap_name:
                    tw = len(cap_name) * 7 + 10
                    parts.append(
                        f'<rect x="{tag_x}" y="{sy + 10}" width="{tw}" height="18" '
                        f'rx="3" fill="{stroke}" opacity="0.15"/>'
                        f'<text x="{tag_x + tw // 2}" y="{sy + 23}" '
                        f'text-anchor="middle" font-size="8" fill="{stroke}">'
                        f'{_esc(cap_name)}</text>'
                    )

        current_y += lane_h + LANE_GAP

    # Insert arrows before the card elements
    parts[3:3] = arrow_parts

    canvas_h = current_y + PAD_Y
    parts[0] = f'<svg xmlns="http://www.w3.org/2000/svg" width="{canvas_w}" height="{canvas_h}" font-family="{FONT}">'
    parts[2] = f'<rect width="{canvas_w}" height="{canvas_h}" fill="{colors["bg"]}"/>'

    parts.append("</svg>")
    target.write_text("\n".join(parts), encoding="utf-8")
