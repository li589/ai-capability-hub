"""生成自包含的 HTML 查看器，用内嵌 SVG 展示三层架构（系统层→能力层→参与者层）。

能力层按域（domain）分组，参与者与能力之间有连线。
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from xml.sax.saxutils import escape

from .export_svg import C, C_LIGHT, C_DARK, FONT, FONT_MONO, CANVAS_X as SVG_CANVAS_X, _resolve_theme, _content_router

# ── Design tokens ──
_LAYER_PAD = 28
_LAYER_HEADER_H = 32
_LAYER_GAP = 36
_TITLE_H = 72
_CARD_RX = 6
_SYS_CARD_W = 160
_SYS_CARD_H = 44
_CAP_CARD_W = 170
_CAP_CARD_H = 48
_CAP_CARD_RX = 8
_ACTOR_W = 140
_ACTOR_H = 40
_ACTOR_RX = 20
_CARD_GAP = 12
_ARROW_COLOR = "#0B6E6E"
_MAX_CANVAS_W = 1200  # 安全宽度上限，超出则自动换行


def _esc(s: str) -> str:
    return escape(str(s))


def _calc_cols(n: int) -> int:
    if n <= 0: return 1
    if n <= 3: return 1
    if n <= 6: return 2
    if n <= 12: return 3
    return 4


def _build_three_layer_svg(bp: dict[str, Any], colors: dict | None = None) -> str:
    c = colors if colors is not None else C
    """Build SVG with three explicit layers: systems → capabilities(domains) → actors.

    Width is capped at _MAX_CANVAS_W. If content exceeds this, the layout
    automatically wraps domains and cards into more rows.
    """
    lib = bp.get("library", {})
    systems = lib.get("systems", [])
    capabilities = lib.get("capabilities", [])
    actors = lib.get("actors", [])
    relations = bp.get("relations", [])
    domain_order = bp.get("domainOrder", [])

    PAD_X = SVG_CANVAS_X
    PAD_Y = 30
    content_w = _MAX_CANVAS_W - PAD_X * 2

    # ── Group capabilities by domain ──
    domain_caps: dict[str, list[dict]] = {}
    for cap in capabilities:
        domain = cap.get("domain", cap.get("category", ""))
        domain_caps.setdefault(domain, []).append(cap)
    if not domain_order:
        domain_order = list(domain_caps.keys())

    # ── Canvas width: fixed at safe max ──
    canvas_w = _MAX_CANVAS_W

    parts: list[str] = []
    parts.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{canvas_w}" height="0" '
        f'font-family="{FONT}">'
    )
    parts.append(f'<rect width="{canvas_w}" height="0" fill="{c["bg"]}"/>')

    # Title
    title = bp.get("meta", {}).get("title", "Business Blueprint")
    industry = bp.get("meta", {}).get("industry", "")
    subtitle = f"Industry: {industry}" if industry else "三层架构"
    parts.append(
        f'<g class="title-block">'
        f'<rect x="{PAD_X}" y="{PAD_Y}" width="{content_w}" height="52" '
        f'rx="6" fill="{c["canvas"]}" stroke="{c["border"]}" stroke-width="1"/>'
        f'<text x="{PAD_X + 16}" y="{PAD_Y + 24}" font-size="16" fill="{c["text_main"]}" '
        f'font-family="{FONT}" font-weight="700">{_esc(title)} — 架构总览</text>'
        f'<text x="{PAD_X + 16}" y="{PAD_Y + 42}" font-size="11" fill="{c["text_sub"]}" '
        f'font-family="{FONT_MONO}">{_esc(subtitle)}</text></g>'
    )

    current_y = PAD_Y + _TITLE_H

    # ── Build node position map for arrows ──
    node_pos: dict[str, tuple[float, float]] = {}  # id → (center_x, center_y)

    # ══════════════════════════════════════════
    # Layer 0: 应用系统层 (horizontal, wrap at 5)
    # ══════════════════════════════════════════
    sys_cols = min(len(systems), 5)
    sys_total_w = sys_cols * (_SYS_CARD_W + _CARD_GAP) - _CARD_GAP
    sys_start_x = PAD_X + (content_w - sys_total_w) / 2

    parts.append(
        f'<text x="{PAD_X}" y="{current_y}" font-size="13" fill="{c["sys_stroke"]}" '
        f'font-weight="700">应用系统层 ({len(systems)})</text>'
    )
    current_y += 14 + _LAYER_PAD

    for i, sys in enumerate(systems):
        col = i % sys_cols
        row = i // sys_cols
        sx = sys_start_x + col * (_SYS_CARD_W + _CARD_GAP)
        sy = current_y + row * (_SYS_CARD_H + _CARD_GAP)

        node_pos[sys["id"]] = (sx + _SYS_CARD_W / 2, sy + _SYS_CARD_H / 2)
        parts.append(
            f'<rect x="{sx}" y="{sy}" width="{_SYS_CARD_W}" height="{_SYS_CARD_H}" '
            f'rx="6" fill="{c["sys_fill"]}" stroke="{c["sys_stroke"]}" stroke-width="1.5"/>'
            f'<text x="{sx + _SYS_CARD_W / 2}" y="{sy + _SYS_CARD_H / 2 + 5}" '
            f'text-anchor="middle" font-size="12" fill="{c["text_main"]}" '
            f'font-weight="600">{_esc(sys["name"])}</text>'
        )

    layer0_bottom = current_y + _SYS_CARD_H + _LAYER_PAD
    current_y = layer0_bottom + _LAYER_GAP

    # ══════════════════════════════════════════
    # Layer 1: 业务能力层 (按域分组, 域自动换行)
    # ══════════════════════════════════════════
    parts.append(
        f'<text x="{PAD_X}" y="{current_y}" font-size="13" fill="{c["cap_stroke"]}" '
        f'font-weight="700">业务能力层 ({len(capabilities)} 能力 / {len(domain_caps)} 域)</text>'
    )
    current_y += 14 + _LAYER_PAD

    # Domain layout: calculate how many domains fit per row
    # Each domain needs at least _CAP_CARD_W + _CARD_GAP * 2 width
    min_domain_w = _CAP_CARD_W * 2 + _CARD_GAP * 3  # at least 2 cards wide
    domain_cols = max(1, min(len(domain_order), int(content_w / min_domain_w))) if domain_order else 1
    domain_col_w = content_w / domain_cols

    # Pass 1: calculate each domain's height, find max per row
    row_max_h: dict[int, int] = {}
    domain_heights: dict[str, int] = {}
    for di, domain in enumerate(domain_order):
        caps = domain_caps.get(domain, [])
        if not caps:
            continue
        dr = di // domain_cols
        cols = _calc_cols(len(caps))
        while cols > 1 and cols * (_CAP_CARD_W + _CARD_GAP) - _CARD_GAP > domain_col_w - _CARD_GAP:
            cols -= 1
        rows = -(-len(caps) // cols) if cols > 0 else len(caps)
        h = rows * _CAP_CARD_H + max(0, rows - 1) * _CARD_GAP + _LAYER_PAD * 2
        domain_heights[domain] = h
        row_max_h[dr] = max(row_max_h.get(dr, 0), h)

    # Pre-calculate row start Y positions
    row_start_y: dict[int, float] = {}
    row_y = current_y
    if row_max_h:
        for dr in range(max(row_max_h.keys()) + 1):
            row_start_y[dr] = row_y
            row_y += row_max_h.get(dr, 0) + _CARD_GAP  # 同层内域行间距用 _CARD_GAP，不用 _LAYER_GAP

    layer1_max_bottom = row_y

    # Pass 2: render with uniform row height
    for di, domain in enumerate(domain_order):
        caps = domain_caps.get(domain, [])
        if not caps:
            continue

        dc = di % domain_cols
        dr = di // domain_cols
        domain_y = row_start_y[dr]
        domain_x = PAD_X + dc * domain_col_w + _CARD_GAP / 2
        domain_w = domain_col_w - _CARD_GAP
        domain_inner_h = row_max_h[dr]

        # Calculate card columns for this domain
        cols = _calc_cols(len(caps))
        while cols > 1 and cols * (_CAP_CARD_W + _CARD_GAP) - _CARD_GAP > domain_w:
            cols -= 1
        rows = -(-len(caps) // cols) if cols > 0 else len(caps)
        domain_inner_w = cols * (_CAP_CARD_W + _CARD_GAP) - _CARD_GAP
        domain_inner_x = domain_x + (domain_w - domain_inner_w) / 2

        # Domain background
        parts.append(
            f'<rect x="{domain_x}" y="{domain_y}" width="{domain_w}" height="{domain_inner_h}" '
            f'rx="10" fill="{c["cap_fill"]}" stroke="{c["cap_stroke"]}" stroke-width="1" opacity="0.4"/>'
        )
        # Domain label
        parts.append(
            f'<text x="{domain_x + domain_w / 2}" y="{domain_y + 18}" '
            f'text-anchor="middle" font-size="11" fill="{c["cap_stroke"]}" '
            f'font-weight="600">{_esc(domain)} ({len(caps)})</text>'
        )

        cap_start_y = domain_y + _LAYER_PAD
        cap_start_x = domain_inner_x

        for ci, cap in enumerate(caps):
            cc = ci % cols
            cr = ci // cols
            cx = cap_start_x + cc * (_CAP_CARD_W + _CARD_GAP)
            cy = cap_start_y + cr * (_CAP_CARD_H + _CARD_GAP)

            node_pos[cap["id"]] = (cx + _CAP_CARD_W / 2, cy + _CAP_CARD_H / 2)
            parts.append(
                f'<rect x="{cx}" y="{cy}" width="{_CAP_CARD_W}" height="{_CAP_CARD_H}" '
                f'rx="{_CAP_CARD_RX}" fill="{c["canvas"]}" stroke="{c["cap_stroke"]}" stroke-width="1"/>'
                f'<text x="{cx + _CAP_CARD_W / 2}" y="{cy + _CAP_CARD_H / 2 + 5}" '
                f'text-anchor="middle" font-size="11" fill="{c["text_main"]}" '
                f'font-weight="500">{_esc(cap["name"])}</text>'
            )

    # Layer 1 ends after last domain row
    layer1_bottom = layer1_max_bottom
    current_y = layer1_bottom + _LAYER_GAP

    # ══════════════════════════════════════════
    # Layer 2: 参与者层 (horizontal, wrap at 5)
    # ══════════════════════════════════════════
    current_y = max(layer1_bottom, current_y) + 20
    actor_cols = min(len(actors), 5)
    actor_total_w = actor_cols * (_ACTOR_W + _CARD_GAP) - _CARD_GAP
    actor_start_x = PAD_X + (content_w - actor_total_w) / 2

    parts.append(
        f'<text x="{PAD_X}" y="{current_y}" font-size="13" fill="{c["actor_stroke"]}" '
        f'font-weight="700">参与者层 ({len(actors)})</text>'
    )
    current_y += 14 + _LAYER_PAD

    for i, actor in enumerate(actors):
        col = i % actor_cols
        row = i // actor_cols
        ax = actor_start_x + col * (_ACTOR_W + _CARD_GAP)
        ay = current_y + row * (_ACTOR_H + _CARD_GAP)

        node_pos[actor["id"]] = (ax + _ACTOR_W / 2, ay + _ACTOR_H / 2)
        parts.append(
            f'<rect x="{ax}" y="{ay}" width="{_ACTOR_W}" height="{_ACTOR_H}" '
            f'rx="{_ACTOR_RX}" fill="{c["actor_fill"]}" stroke="{c["actor_stroke"]}" stroke-width="1.5"/>'
            f'<text x="{ax + _ACTOR_W / 2}" y="{ay + _ACTOR_H / 2 + 5}" '
            f'text-anchor="middle" font-size="11.5" fill="{c["text_main"]}" '
            f'font-weight="600">{_esc(actor["name"])}</text>'
        )

    layer2_bottom = current_y + _LAYER_PAD + _ACTOR_H + _LAYER_GAP

    # ══════════════════════════════════════════
    # Arrows: system → capability
    # ══════════════════════════════════════════
    arrow_parts: list[str] = []
    for sys in systems:
        sys_pos = node_pos.get(sys["id"])
        if not sys_pos:
            continue
        for cid in sys.get("capabilityIds", []):
            cap_pos = node_pos.get(cid)
            if not cap_pos:
                continue
            sx, sy = sys_pos
            cx, cy = cap_pos
            if sy < cy:
                arrow_parts.append(
                    f'<line x1="{int(sx)}" y1="{int(sy + _SYS_CARD_H / 2)}" '
                    f'x2="{int(cx)}" y2="{int(cy - _CAP_CARD_H / 2)}" '
                    f'stroke="{c["arrow_muted"]}" stroke-width="1" stroke-dasharray="3,3" '
                    f'opacity="0.3"/>'
                )

    # ══════════════════════════════════════════
    # Arrows: actor → capability (from relations)
    # ══════════════════════════════════════════
    for rel in relations:
        from_id = rel.get("from", "")
        to_id = rel.get("to", "")
        actor_pos = node_pos.get(from_id)
        cap_pos = node_pos.get(to_id)
        if not actor_pos or not cap_pos:
            continue
        ax, ay = actor_pos
        cx, cy = cap_pos
        arrow_parts.append(
            f'<line x1="{int(ax)}" y1="{int(ay - _ACTOR_H / 2)}" '
            f'x2="{int(cx)}" y2="{int(cy + _CAP_CARD_H / 2)}" '
            f'stroke="{c["actor_stroke"]}" stroke-width="1" stroke-dasharray="4,3" '
            f'opacity="0.25"/>'
        )

    # Insert arrows before nodes in z-order
    parts[3:3] = arrow_parts

    canvas_h = layer2_bottom + 30
    parts[0] = f'<svg xmlns="http://www.w3.org/2000/svg" width="{canvas_w}" height="{canvas_h}" font-family="{FONT}">'
    parts[1] = f'<rect width="{canvas_w}" height="{canvas_h}" fill="{c["bg"]}"/>'
    parts.append("</svg>")
    return "\n".join(parts)


def _build_capability_map_svg(bp: dict[str, Any], colors: dict | None = None) -> str:
    c = colors if colors is not None else C
    """Build inline SVG for capability map with domain grouping."""
    lib = bp.get("library", {})
    capabilities = lib.get("capabilities", [])
    systems = lib.get("systems", [])

    sys_by_id = {s["id"]: s for s in systems}
    domain_order = bp.get("domainOrder", [])
    PAD_X = SVG_CANVAS_X
    PAD_Y = 30
    COLS = _calc_cols(len(capabilities))
    COL_W = _CAP_CARD_W + _CARD_GAP

    # Group by domain
    domain_caps: dict[str, list[dict]] = {}
    for cap in capabilities:
        domain = cap.get("domain", cap.get("category", ""))
        domain_caps.setdefault(domain, []).append(cap)
    if not domain_order:
        domain_order = list(domain_caps.keys())

    # Layout: domains as rows, cards within each domain in grid
    parts: list[str] = []
    parts.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" width="0" height="0" font-family="{FONT}">'
    )
    parts.append(f'<rect width="0" height="0" fill="{c["bg"]}"/>')

    title = bp.get("meta", {}).get("title", "Business Blueprint")
    industry = bp.get("meta", {}).get("industry", "")
    subtitle = f"Industry: {industry}" if industry else "Capability Map"

    # Calculate total height first
    current_y = PAD_Y + _TITLE_H
    max_x = 0

    for domain in domain_order:
        caps = domain_caps.get(domain, [])
        if not caps:
            continue
        cols = _calc_cols(len(caps))
        rows = -(-len(caps) // cols) if cols > 0 else len(caps)
        domain_w = cols * COL_W - _CARD_GAP
        domain_h = rows * _CAP_CARD_H + max(0, rows - 1) * _CARD_GAP + _LAYER_PAD + 20
        max_x = max(max_x, PAD_X * 2 + domain_w)
        current_y += domain_h + _CARD_GAP

    canvas_w = max(max_x, 600)
    canvas_h = current_y + PAD_Y

    parts[0] = f'<svg xmlns="http://www.w3.org/2000/svg" width="{canvas_w}" height="{canvas_h}" font-family="{FONT}">'
    parts[1] = f'<rect width="{canvas_w}" height="{canvas_h}" fill="{c["bg"]}"/>'

    current_y = PAD_Y + _TITLE_H

    parts.append(
        f'<g class="title-block">'
        f'<rect x="{PAD_X}" y="{PAD_Y}" width="{canvas_w - PAD_X * 2}" height="52" '
        f'rx="6" fill="{c["canvas"]}" stroke="{c["border"]}" stroke-width="1"/>'
        f'<text x="{PAD_X + 16}" y="{PAD_Y + 24}" font-size="16" fill="{c["text_main"]}" '
        f'font-family="{FONT}" font-weight="700">{_esc(title)} — 能力地图</text>'
        f'<text x="{PAD_X + 16}" y="{PAD_Y + 42}" font-size="11" fill="{c["text_sub"]}" '
        f'font-family="{FONT_MONO}">{_esc(subtitle)}</text></g>'
    )

    current_y = PAD_Y + _TITLE_H + _LAYER_PAD

    for domain in domain_order:
        caps = domain_caps.get(domain, [])
        if not caps:
            continue
        cols = _calc_cols(len(caps))
        rows = -(-len(caps) // cols) if cols > 0 else len(caps)
        domain_w = cols * COL_W - _CARD_GAP
        domain_h = rows * _CAP_CARD_H + max(0, rows - 1) * _CARD_GAP + _LAYER_PAD
        domain_x = PAD_X + (canvas_w - PAD_X * 2 - domain_w) / 2

        # Domain container
        parts.append(
            f'<rect x="{domain_x}" y="{current_y}" width="{domain_w}" height="{domain_h}" '
            f'rx="10" fill="{c["cap_fill"]}" stroke="{c["cap_stroke"]}" stroke-width="1" opacity="0.4"/>'
        )
        # Domain label
        parts.append(
            f'<text x="{domain_x + domain_w / 2}" y="{current_y + 18}" '
            f'text-anchor="middle" font-size="12" fill="{c["cap_stroke"]}" '
            f'font-weight="700">{_esc(domain)} ({len(caps)})</text>'
        )

        cap_start_x = domain_x + _CARD_GAP / 2
        cap_start_y = current_y + _LAYER_PAD

        for i, cap in enumerate(caps):
            cc = i % cols
            cr = i // cols
            cx = cap_start_x + cc * COL_W
            cy = cap_start_y + cr * (_CAP_CARD_H + _CARD_GAP)

            sys_names = [sys_by_id[sid]["name"] for sid in cap.get("supportingSystemIds", []) if sid in sys_by_id]

            parts.append(
                f'<rect x="{cx}" y="{cy}" width="{_CAP_CARD_W}" height="{_CAP_CARD_H}" '
                f'rx="{_CARD_RX}" fill="{c["canvas"]}" stroke="{c["cap_stroke"]}" stroke-width="1.5"/>'
                f'<text x="{cx + _CAP_CARD_W / 2}" y="{cy + _CAP_CARD_H / 2 + 5}" '
                f'text-anchor="middle" font-size="11" fill="{c["text_main"]}" '
                f'font-weight="500">{_esc(cap["name"])}</text>'
            )
            # Supporting systems as small badges
            for j, sname in enumerate(sys_names[:2]):
                tw = len(sname) * 7 + 12
                tx = cx + _CAP_CARD_W - tw - 6
                ty = cy + _CAP_CARD_H - 16
                parts.append(
                    f'<rect x="{tx}" y="{ty}" width="{tw}" height="13" '
                    f'rx="3" fill="{c["sys_fill"]}" stroke="{c["sys_stroke"]}" stroke-width="0.5"/>'
                    f'<text x="{tx + tw / 2}" y="{ty + 10}" '
                    f'text-anchor="middle" font-size="7.5" fill="{c["text_main"]}">{_esc(sname)}</text>'
                )

        current_y += domain_h + _CARD_GAP

    canvas_h = current_y + PAD_Y
    parts[0] = f'<svg xmlns="http://www.w3.org/2000/svg" width="{canvas_w}" height="{canvas_h}" font-family="{FONT}">'
    parts[1] = f'<rect width="{canvas_w}" height="{canvas_h}" fill="{c["bg"]}"/>'
    parts.append("</svg>")
    return "\n".join(parts)


def _build_swimlane_svg(bp: dict[str, Any], colors: dict | None = None) -> str:
    c = colors if colors is not None else C
    """Build inline SVG for actor-capability relationships as swimlane view."""
    lib = bp.get("library", {})
    actors = lib.get("actors", [])
    capabilities = lib.get("capabilities", [])
    relations = bp.get("relations", [])
    domain_order = bp.get("domainOrder", [])

    cap_by_id = {c["id"]: c for c in capabilities}
    PAD_X = SVG_CANVAS_X
    PAD_Y = 30
    CAP_W = 150
    CAP_H = 38
    CAP_RX = 6
    LANE_GAP = 16
    STEP_GAP = 8

    # Group capabilities by what each actor uses (from relations)
    actor_caps: dict[str, list[dict]] = {}
    for rel in relations:
        from_id = rel.get("from", "")
        to_ids = [t.strip() for t in str(rel.get("to", "")).split(",") if t.strip()]
        actor_caps.setdefault(from_id, []).extend(
            [cap_by_id[tid] for tid in to_ids if tid in cap_by_id]
        )

    lane_palette = [
        ("#0B6E6E", "#E8F5F5"), ("#059669", "#ECFDF5"), ("#4338CA", "#EEF2FF"),
        ("#D97706", "#FEFCE8"), ("#DC2626", "#FEF2F2"),
    ]

    max_caps = max((len(c) for c in actor_caps.values()), default=1)
    cols = min(max_caps, 4)

    parts: list[str] = []
    current_y = PAD_Y + _TITLE_H

    for lane_idx, actor in enumerate(actors):
        aid = actor["id"]
        caps = actor_caps.get(aid, [])
        if not caps:
            continue
        stroke, fill = lane_palette[lane_idx % len(lane_palette)]
        lane_rows = -(-len(caps) // cols) if cols > 0 else len(caps)
        lane_h = 32 + LANE_GAP + lane_rows * (CAP_H + STEP_GAP)
        lane_w = cols * (CAP_W + STEP_GAP) - STEP_GAP

        parts.append(
            f'<text x="{PAD_X}" y="{current_y}" font-size="13" fill="{stroke}" '
            f'font-weight="700">{_esc(actor.get("name", aid))} ({len(caps)})</text>'
        )
        current_y += 14 + LANE_GAP

        lane_x = PAD_X + (max(600, lane_w) - lane_w) / 2 + 20
        for i, cap in enumerate(caps):
            cc = i % cols
            cr = i // cols
            cx = lane_x + cc * (CAP_W + STEP_GAP)
            cy = current_y + cr * (CAP_H + STEP_GAP)

            parts.append(
                f'<rect x="{cx}" y="{cy}" width="{CAP_W}" height="{CAP_H}" '
                f'rx="{CAP_RX}" fill="{fill}" stroke="{stroke}" stroke-width="1.5"/>'
                f'<text x="{cx + CAP_W / 2}" y="{cy + CAP_H / 2 + 5}" '
                f'text-anchor="middle" font-size="10.5" fill="{c["text_main"]}" '
                f'font-weight="500">{_esc(cap["name"])}</text>'
            )
            # Domain badge
            domain = cap.get("domain", "")
            if domain:
                tw = len(domain) * 6 + 10
                tx = cx + CAP_W - tw - 6
                parts.append(
                    f'<rect x="{tx}" y="{cy + CAP_H - 14}" width="{tw}" height="11" '
                    f'rx="2" fill="{stroke}" opacity="0.15"/>'
                    f'<text x="{tx + tw / 2}" y="{cy + CAP_H - 5}" '
                    f'text-anchor="middle" font-size="7" fill="{stroke}">{_esc(domain)}</text>'
                )

        current_y += lane_rows * (CAP_H + STEP_GAP) + LANE_GAP + 16

    canvas_w = max(600, cols * (CAP_W + STEP_GAP)) + PAD_X * 2 + 40
    canvas_h = current_y + PAD_Y

    title = bp.get("meta", {}).get("title", "Business Blueprint")
    parts.insert(0,
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{canvas_w}" height="{canvas_h}" font-family="{FONT}">'
        f'<rect width="{canvas_w}" height="{canvas_h}" fill="{c["bg"]}"/>'
        f'<g class="title-block">'
        f'<rect x="{PAD_X}" y="{PAD_Y}" width="{canvas_w - PAD_X * 2}" height="52" '
        f'rx="6" fill="{c["canvas"]}" stroke="{c["border"]}" stroke-width="1"/>'
        f'<text x="{PAD_X + 16}" y="{PAD_Y + 24}" font-size="16" fill="{c["text_main"]}" '
        f'font-family="{FONT}" font-weight="700">{_esc(title)} — 参与者能力</text>'
        f'<text x="{PAD_X + 16}" y="{PAD_Y + 42}" font-size="11" fill="{c["text_sub"]}" '
        f'font-family="{FONT_MONO}">Actor-Capability Matrix</text></g>'
    )
    parts.append("</svg>")
    return "\n".join(parts)


def export_html_viewer(blueprint: dict[str, Any], target: Path, theme: str = "light") -> None:
    """Generate a self-contained HTML viewer with inline SVG diagrams.

    Uses content routing to decide which views to include based on blueprint content.

    Args:
        blueprint: The canonical blueprint JSON.
        target: Output file path.
        theme: Color theme — "light" (default) or "dark".
    """
    colors = _resolve_theme(theme)
    title = blueprint.get("meta", {}).get("title", "Business Blueprint")
    industry = blueprint.get("meta", {}).get("industry", "")
    revision = blueprint.get("meta", {}).get("revisionId", "unknown")
    created_at = blueprint.get("meta", {}).get("createdAt", "")
    created_by = blueprint.get("meta", {}).get("createdBy", "")

    # Use content router to decide which views to generate
    views = _content_router(blueprint)

    # Build SVGs based on routed views; fall back to classic three views if routing found nothing
    if views:
        view_svgs: dict[str, str] = {}
        view_titles: dict[str, str] = {}
        for view in views:
            if view["type"] == "architecture":
                view_svgs["layer"] = _build_three_layer_svg(blueprint, colors=colors)
                view_titles["layer"] = "三层架构"
            elif view["type"] == "capability_map":
                view_svgs["capability"] = _build_capability_map_svg(blueprint, colors=colors)
                view_titles["capability"] = "能力地图"
            elif view["type"] == "swimlane":
                view_svgs["swimlane"] = _build_swimlane_svg(blueprint, colors=colors)
                view_titles["swimlane"] = "参与者能力"
        layer_svg = view_svgs.get("layer", _build_three_layer_svg(blueprint, colors=colors))
        cap_svg = view_svgs.get("capability", _build_capability_map_svg(blueprint, colors=colors))
        swim_svg = view_svgs.get("swimlane", _build_swimlane_svg(blueprint, colors=colors))
    else:
        layer_svg = _build_three_layer_svg(blueprint, colors=colors)
        cap_svg = _build_capability_map_svg(blueprint, colors=colors)
        swim_svg = _build_swimlane_svg(blueprint, colors=colors)

    # Compute summary stats from blueprint
    lib = blueprint.get("library", {})
    n_systems = len(lib.get("systems", []))
    n_capabilities = len(lib.get("capabilities", []))
    n_actors = len(lib.get("actors", []))
    n_flow_steps = len(lib.get("flowSteps", []))

    # Coverage: systems with capabilityIds / total systems
    systems_with_caps = sum(1 for s in lib.get("systems", []) if s.get("capabilityIds"))
    sys_coverage = f"{int(systems_with_caps / n_systems * 100)}%" if n_systems else "N/A"

    safe_json = json.dumps(json.dumps(blueprint, ensure_ascii=False)).replace("</", "<\\/")

    # Theme-aware CSS
    bg_color = colors["bg"]
    text_main = colors["text_main"]
    text_sub = colors["text_sub"]
    border = colors["border"]
    cap_stroke = colors["cap_stroke"]
    canvas = colors["canvas"]
    header_bg = "#020617" if theme == "dark" else "#0F2742"
    header_text = "#E2E8F0" if theme == "dark" else "#fff"
    tab_bg = colors["canvas"]
    card_bg = colors["canvas"]
    card_border = colors["border"]
    card_text = colors["text_main"]
    card_text_sub = colors["text_sub"]
    accent = colors["cap_stroke"]

    # Dark theme CSS extras
    dark_extras = ""
    if theme == "dark":
        dark_extras = f"""
        .header {{ background: {header_bg}; color: {header_text}; }}
        .header .meta {{ font-size: 13px; color: #94A3B8; }}
        .tabs {{ background: {colors["layer_header_bg"]}; border-bottom-color: {border}; }}
        .tab {{ color: {text_sub}; }}
        .tab:hover {{ color: {text_main}; }}
        .tab.active {{ color: {accent}; border-bottom-color: {accent}; }}
        .viewer {{ background: {bg_color}; }}
        .viewer svg {{ box-shadow: 0 2px 12px rgba(0,0,0,0.4); }}
        .summary-cards {{ background: linear-gradient(180deg, {colors["layer_header_bg"]}, {bg_color}); }}
        .summary-card {{ background: {card_bg}; border-color: {card_border}; }}
        .summary-card .card-value {{ color: {text_main}; }}
        .summary-card .card-label {{ color: {text_sub}; }}
        body {{ background: linear-gradient(180deg, {colors["bg"]} 0%, #0F172A 100%); }}
"""
    else:
        dark_extras = f"""
        .summary-cards {{ background: linear-gradient(180deg, {colors["layer_header_bg"]}, {bg_color}); }}
        .summary-card {{ background: {card_bg}; border-color: {card_border}; }}
        .summary-card .card-value {{ color: {text_main}; }}
        .summary-card .card-label {{ color: {text_sub}; }}
"""

    # Dark theme grid background
    grid_bg = ""
    if theme == "dark":
        grid_bg = '<div style="position:fixed;top:0;left:0;width:100%;height:100%;background-image:linear-gradient(rgba(255,255,255,0.03) 1px,transparent 1px),linear-gradient(90deg,rgba(255,255,255,0.03) 1px,transparent 1px);background-size:40px 40px;pointer-events:none;z-index:0;"></div>'

    # Build dynamic tabs and panes based on available views
    view_map = {"layer": layer_svg, "capability": cap_svg, "swimlane": swim_svg}
    view_labels = {"layer": "三层架构", "capability": "能力地图", "swimlane": "参与者能力"}

    # Only include tabs for views that have non-empty SVG content
    active_views = [k for k in ["layer", "capability", "swimlane"] if k in view_map]
    if not active_views:
        active_views = ["layer"]

    tabs_html = ""
    panes_html = ""
    for i, vk in enumerate(active_views):
        active_class = " active" if i == 0 else ""
        tabs_html += f'<button class="tab{active_class}" data-pane="{vk}">{view_labels[vk]}</button>'
        panes_html += f'<div class="viewer-pane{active_class}" id="pane-{vk}"><div class="viewer" id="svg-{vk}">{view_map[vk]}</div></div>'

    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{_esc(title)}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: {FONT}; background: {bg_color}; color: {text_main}; position: relative; }}
        .header {{ background: {header_bg}; color: {header_text}; padding: 12px 24px; display: flex; justify-content: space-between; align-items: center; position: relative; z-index: 1; }}
        .header h1 {{ font-size: 18px; font-weight: 600; }}
        .header .meta {{ font-size: 13px; color: #94A3B8; }}
        .tabs {{ display: flex; padding: 0 24px; background: {tab_bg}; border-bottom: 1px solid {border}; position: relative; z-index: 1; }}
        .tab {{ padding: 12px 20px; font-size: 14px; font-weight: 500; color: {text_sub}; border: none; background: none; cursor: pointer; border-bottom: 2px solid transparent; }}
        .tab:hover {{ color: {text_main}; }}
        .tab.active {{ color: {cap_stroke}; border-bottom-color: {cap_stroke}; }}
        .viewer {{ padding: 24px; overflow: auto; display: flex; justify-content: center; position: relative; z-index: 1; }}
        .viewer svg {{ max-width: 100%; height: auto; border-radius: 8px; }}
        .viewer-pane {{ display: none; }}
        .viewer-pane.active {{ display: flex; }}
        /* Summary cards */
        .summary-cards {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 16px; padding: 24px; margin: 0 24px; position: relative; z-index: 1; }}
        .summary-card {{ border-radius: 8px; border: 1px solid {card_border}; padding: 16px 20px; text-align: center; }}
        .summary-card .card-value {{ font-size: 28px; font-weight: 700; font-family: {FONT_MONO}; line-height: 1; }}
        .summary-card .card-label {{ font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px; margin-top: 6px; font-weight: 500; }}
    </style>
</head>
<body>
    {grid_bg}
    <div class="header">
        <h1 id="page-title">{_esc(title)}</h1>
        <span class="meta" id="page-meta"></span>
    </div>
    <div class="tabs" id="tab-bar">
        {tabs_html}
    </div>
    <div class="summary-cards">
        <div class="summary-card">
            <div class="card-value">{n_systems}</div>
            <div class="card-label">Systems</div>
        </div>
        <div class="summary-card">
            <div class="card-value">{n_capabilities}</div>
            <div class="card-label">Capabilities</div>
        </div>
        <div class="summary-card">
            <div class="card-value">{n_actors}</div>
            <div class="card-label">Actors</div>
        </div>
        <div class="summary-card">
            <div class="card-value">{n_flow_steps}</div>
            <div class="card-label">Flow Steps</div>
        </div>
        <div class="summary-card">
            <div class="card-value">{sys_coverage}</div>
            <div class="card-label">Sys Coverage</div>
        </div>
    </div>
    {panes_html}
    <script>
        const blueprint = JSON.parse({safe_json});
        const m = blueprint.meta || {{}};
        document.getElementById('page-title').textContent = m.title || 'Business Blueprint';
        document.getElementById('page-meta').textContent = 'Rev: ' + (m.revisionId || 'unknown') + ' | ' + (m.industry || '');
        document.querySelectorAll('.tab').forEach(tab => {{
            tab.addEventListener('click', () => {{
                document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
                tab.classList.add('active');
                document.querySelectorAll('.viewer-pane').forEach(p => p.classList.remove('active'));
                document.getElementById('pane-' + tab.dataset.pane).classList.add('active');
            }});
        }});
    </script>
</body>
</html>"""

    target.write_text(html, encoding="utf-8")

