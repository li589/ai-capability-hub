#!/usr/bin/env python3
"""Statically audit Radar HTML for the enforceable visual contract.

This is the package's deterministic validation gate. Browser and screenshot QA are intentionally
outside this workflow.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date
from html import unescape
from html.parser import HTMLParser
from pathlib import Path


COLOR_TOKEN_NAMES = {
    "--bg",
    "--bg2",
    "--ink",
    "--muted",
    "--rule",
    "--accent",
    "--accent2",
}
REQUIRED_COLOR_TOKENS = {
    "--bg",
    "--bg2",
    "--ink",
    "--muted",
    "--rule",
    "--accent",
}
LEGACY_RADAR_TOKEN_RE = re.compile(r"--radar-(?:bg|fg|muted|accent|surface)\b", re.I)
VALID_FRAMEWORKS = {"exhibit-path", "index-gate", "reading-rail"}
BLUEPRINT_FRAMEWORKS = {
    "verdict-sheet": "index-gate",
    "evidence-object": "reading-rail",
    "swiss-trace": "reading-rail",
    "decision-mosaic": "index-gate",
    "signal-stage": "exhibit-path",
    "alert-cut": "exhibit-path",
}
PURE_WHITE_BLUEPRINTS = {"verdict-sheet", "evidence-object", "decision-mosaic"}
PURE_WHITE_VALUES = {"#fff", "#ffffff", "rgb(255, 255, 255)", "rgb(255 255 255)"}
VALID_CADENCES = {"alert", "daily", "weekly", "monthly", "one-off"}
VALID_CARD_ROLES = {"signal", "evidence", "decision", "index"}
REPORT_NAME_RE = re.compile(
    r"^(?P<topic>.+)-(?P<date>\d{4}-\d{2}-\d{2})(?P<week>-w\d{2})?$",
    re.I,
)
COLOR_LITERAL_RE = re.compile(
    r"#[0-9a-fA-F]{3,8}\b|"
    r"\brgba?\([^)]*\)|"
    r"\bhsla?\([^)]*\)|"
    r"\boklch\([^)]*\)|"
    r"\bcolor\([^)]*\)"
)
EMOJI_RE = re.compile(
    "["
    "\U0001F1E6-\U0001F1FF"
    "\U0001F300-\U0001FAFF"
    "\U00002600-\U000027BF"
    "]"
)


class ReportParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.in_h1 = False
        self.h1_parts: list[str] = []
        self.title_line_count = 0
        self.html_blueprint = ""
        self.html_framework = ""
        self.radar_route = ""
        self.radar_selection_id = ""
        self.radar_style_asset = ""
        self.report_cadence = ""
        self.run_date = ""
        self.signal_count: int | None = None
        self.signal_overviews = 0
        self.signal_cards = 0
        self.signal_triggers = 0
        self.signal_card_roles = 0
        self.signal_trigger_buttons = 0
        self.signal_triggers_with_id = 0
        self.signal_triggers_with_pressed = 0
        self.signal_card_ids: set[str] = set()
        self.signal_trigger_ids: set[str] = set()
        self.signal_detail_ids: set[str] = set()
        self.signal_details = 0
        self.report_navs = 0
        self.report_nav_stack: list[str] = []
        self.report_nav_links: list[str] = []
        self.report_nav_current = 0
        self.report_sections = 0
        self.report_section_ids: set[str] = set()
        self.report_sections_without_id = 0
        self.card_roles: list[str] = []
        self.live_regions = 0
        self.remote_scripts: list[str] = []
        self.script_sources: list[str] = []
        self.interactive_chart_count = 0
        self.chart_containers: list[dict[str, str]] = []
        self.chart_statuses = 0
        self.chart_tables = 0
        self.figure_stack: list[dict[str, bool]] = []
        self.chart_figures: list[dict[str, bool]] = []
        self.static_data_svgs = 0

    def handle_starttag(
        self, tag: str, attrs: list[tuple[str, str | None]]
    ) -> None:
        attributes = {key: value or "" for key, value in attrs}
        if tag == "figure":
            self.figure_stack.append({"chart": False, "caption": False})
        if tag == "html":
            self.html_blueprint = attributes.get("data-radar-blueprint", "")
            self.html_framework = attributes.get("data-radar-framework", "")
            self.radar_route = attributes.get("data-radar-route", "")
            self.radar_selection_id = attributes.get("data-radar-selection-id", "")
            self.radar_style_asset = attributes.get("data-radar-style-asset", "")
            self.report_cadence = attributes.get("data-report-cadence", "")
            self.run_date = attributes.get("data-run-date", "")
            raw_signal_count = attributes.get("data-signal-count")
            if raw_signal_count is not None:
                try:
                    self.signal_count = int(raw_signal_count)
                except ValueError:
                    self.signal_count = -1
        if tag == "h1":
            self.in_h1 = True
        if "data-title-line" in attributes:
            self.title_line_count += 1
        if "data-signal-overview" in attributes:
            self.signal_overviews += 1
        if "data-signal-card" in attributes:
            self.signal_cards += 1
            signal_id = attributes.get("data-signal-id", "")
            if signal_id:
                self.signal_card_ids.add(signal_id)
            if attributes.get("data-card-role") == "signal":
                self.signal_card_roles += 1
        if "data-signal-trigger" in attributes:
            self.signal_triggers += 1
            signal_id = attributes.get("data-signal-id", "")
            if signal_id:
                self.signal_triggers_with_id += 1
                self.signal_trigger_ids.add(signal_id)
            if "aria-pressed" in attributes:
                self.signal_triggers_with_pressed += 1
            if tag == "button":
                self.signal_trigger_buttons += 1
        if "data-signal-detail" in attributes:
            self.signal_details += 1
            signal_id = attributes.get("data-signal-id", "")
            if signal_id:
                self.signal_detail_ids.add(signal_id)
        if "data-report-section" in attributes:
            self.report_sections += 1
            section_id = attributes.get("id", "")
            if section_id:
                self.report_section_ids.add(section_id)
            else:
                self.report_sections_without_id += 1
        if "data-card-role" in attributes:
            self.card_roles.append(attributes["data-card-role"])
        if "data-radar-live" in attributes:
            self.live_regions += 1
        if "data-interactive-chart" in attributes:
            self.interactive_chart_count += 1
            self.chart_containers.append(attributes)
            if self.figure_stack:
                self.figure_stack[-1]["chart"] = True
        if "data-chart-status" in attributes:
            self.chart_statuses += 1
        if "data-chart-table" in attributes:
            self.chart_tables += 1
        if tag == "figcaption" and self.figure_stack:
            self.figure_stack[-1]["caption"] = True
        if "data-report-nav" in attributes:
            self.report_navs += 1
            self.report_nav_stack.append(tag)
        elif self.report_nav_stack and tag == self.report_nav_stack[-1]:
            self.report_nav_stack.append(tag)
        if self.report_nav_stack and tag == "a":
            self.report_nav_links.append(attributes.get("href", ""))
            if attributes.get("aria-current") == "location":
                self.report_nav_current += 1
        if tag == "script":
            source = attributes.get("src", "")
            if source:
                self.script_sources.append(source)
            if source.startswith(("http://", "https://", "//")):
                self.remote_scripts.append(source)
        if tag == "svg":
            marker = " ".join(
                [
                    attributes.get("class", ""),
                    attributes.get("id", ""),
                    attributes.get("role", ""),
                ]
            ).lower()
            if "chart" in marker or "data-viz" in attributes:
                self.static_data_svgs += 1

    def handle_endtag(self, tag: str) -> None:
        if tag == "h1":
            self.in_h1 = False
        if self.report_nav_stack and tag == self.report_nav_stack[-1]:
            self.report_nav_stack.pop()
        if tag == "figure" and self.figure_stack:
            self.chart_figures.append(self.figure_stack.pop())

    def handle_data(self, data: str) -> None:
        if self.in_h1:
            self.h1_parts.append(data)


def normalize_css_value(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip().lower())


def visible_text(fragment: str) -> str:
    without_code = re.sub(
        r"<(?:script|style)\b[^>]*>.*?</(?:script|style)>",
        " ",
        fragment,
        flags=re.I | re.S,
    )
    return re.sub(r"\s+", " ", unescape(re.sub(r"<[^>]+>", " ", without_code))).strip()


def text_volume(text: str) -> tuple[int, int]:
    cjk = len(re.findall(r"[\u3040-\u30ff\u3400-\u9fff]", text))
    words = len(re.findall(r"[A-Za-z0-9][A-Za-z0-9'’-]*", text))
    return cjk, words


def default_visible_html(html: str) -> str:
    result = re.sub(
        r"<details\b[^>]*>.*?</details>", " ", html, flags=re.I | re.S
    )
    result = re.sub(
        r"<([a-z][a-z0-9]*)\b[^>]*data-signal-detail[^>]*>.*?</\1>",
        " ",
        result,
        flags=re.I | re.S,
    )
    return result


def marked_text_blocks(html: str, attribute: str) -> list[str]:
    pattern = re.compile(
        rf"<(?P<tag>[a-z][a-z0-9]*)\b[^>]*{re.escape(attribute)}[^>]*>"
        rf"(?P<body>.*?)</(?P=tag)>",
        flags=re.I | re.S,
    )
    return [visible_text(match.group("body")) for match in pattern.finditer(html)]


def declarations(css: str, property_name: str) -> set[str]:
    pattern = re.compile(
        rf"(?<![-\w]){re.escape(property_name)}\s*:\s*([^;}}{{]+)",
        re.IGNORECASE,
    )
    return {
        normalize_css_value(match.group(1))
        for match in pattern.finditer(css)
        if "var(" not in match.group(1) or property_name == "font-family"
    }


def extract_style_text(html: str, html_path: Path) -> str:
    parts = re.findall(r"<style\b[^>]*>(.*?)</style>", html, flags=re.I | re.S)
    for href in re.findall(
        r"<link\b[^>]*rel=[\"']stylesheet[\"'][^>]*href=[\"']([^\"']+)",
        html,
        flags=re.I,
    ):
        if href.startswith(("http://", "https://", "//", "data:")):
            continue
        css_path = (html_path.parent / href).resolve()
        if css_path.exists() and css_path.is_file():
            parts.append(css_path.read_text(encoding="utf-8"))
    return "\n".join(parts)


def extract_color_tokens(css: str) -> dict[str, str]:
    result: dict[str, str] = {}
    for name, value in re.findall(
        r"(--(?:bg2?|ink|muted|rule|accent2?))\s*:\s*([^;}{]+)",
        css,
        flags=re.I,
    ):
        result[name.lower()] = normalize_css_value(value)
    return result


def accent_edge_violations(css: str) -> list[str]:
    violations: list[str] = []
    for selector, body in re.findall(r"([^{}]+)\{([^{}]*)\}", css, flags=re.S):
        selector_lower = selector.lower()
        if not any(
            marker in selector_lower
            for marker in (
                "[data-card",
                "[data-report-nav",
                "[data-chart-table",
                ".signal-card",
                ".metric-card",
                ".kpi-card",
                ".sidebar",
                ".reading-rail",
                ".topbar",
                ".top-bar",
                "header",
                "nav",
                "table",
                "section",
                "h1",
                "h2",
                "h3",
            )
        ):
            continue
        edge_declarations = re.findall(
            r"(border(?:-(?:left|right|top|bottom|inline(?:-start|-end)?|"
            r"block(?:-start|-end)?))?(?:-color|-width|-style)?)\s*:\s*([^;]+)",
            body,
            flags=re.I,
        )
        for prop, value in edge_declarations:
            if re.search(r"var\(\s*--accent2?\s*\)", value, flags=re.I):
                violations.append(f"{selector.strip()} uses {prop} with an accent token")
        for value in re.findall(r"box-shadow\s*:\s*([^;]+)", body, flags=re.I):
            if "inset" in value.lower() and re.search(
                r"var\(\s*--accent2?\s*\)", value, flags=re.I
            ):
                violations.append(
                    f"{selector.strip()} imitates an accent edge with inset box-shadow"
                )
    return violations


def heading_wrap_violations(css: str) -> list[str]:
    violations: list[str] = []
    for selector, body in re.findall(r"([^{}]+)\{([^{}]*)\}", css, flags=re.S):
        selector_lower = selector.lower()
        if not re.search(r"(?:^|[\s>+~,.:#])(h[1-3]|\.display|\.title)(?:\b|[-_])", selector_lower):
            continue
        if re.search(
            r"(?:word-break\s*:\s*break-all|overflow-wrap\s*:\s*anywhere)",
            body,
            flags=re.I,
        ):
            violations.append(selector.strip())
    return violations


def chart_container_has_height(attributes: dict[str, str], css: str) -> bool:
    style = attributes.get("style", "")
    inline_match = re.search(r"min-height\s*:\s*(\d+(?:\.\d+)?)px", style, flags=re.I)
    if inline_match and float(inline_match.group(1)) >= 320:
        return True
    for class_name in attributes.get("class", "").split():
        pattern = re.compile(
            rf"[^{{}}]*\.{re.escape(class_name)}[^{{}}]*\{{([^{{}}]*)\}}",
            flags=re.I | re.S,
        )
        for body in pattern.findall(css):
            match = re.search(r"min-height\s*:\s*(\d+(?:\.\d+)?)px", body, flags=re.I)
            if match and float(match.group(1)) >= 320:
                return True
    return False


def transition_durations_ms(css: str) -> list[float]:
    durations: list[float] = []
    declaration_values = re.findall(r"--motion-duration\s*:\s*([^;}{]+)", css, flags=re.I)
    for selector, body in re.findall(r"([^{}]+)\{([^{}]*)\}", css, flags=re.S):
        if not any(
            marker in selector.lower()
            for marker in (
                "data-signal",
                "data-report-nav",
                "data-card-role",
                ".signal-card",
            )
        ):
            continue
        declaration_values.extend(
            re.findall(
                r"transition(?:-duration)?\s*:\s*([^;}{]+)",
                body,
                flags=re.I,
            )
        )
    for value in declaration_values:
        for number, unit in re.findall(r"(\d*\.?\d+)\s*(ms|s)\b", value, flags=re.I):
            duration = float(number)
            if unit.lower() == "s":
                duration *= 1000
            durations.append(duration)
    return durations


def audit(
    html_path: Path, chart_paths: list[Path]
) -> tuple[list[str], list[str], dict[str, object]]:
    html = html_path.read_text(encoding="utf-8")
    parser = ReportParser()
    parser.feed(html)
    css = extract_style_text(html, html_path)

    inline_scripts = re.findall(
        r"<script\b[^>]*>(.*?)</script>", html, flags=re.I | re.S
    )
    chart_logic_parts = list(inline_scripts)
    interaction_code_parts = list(inline_scripts)
    local_script_paths: dict[str, Path] = {}
    missing_local_scripts: list[str] = []
    loaded_script_paths: set[Path] = set()
    for source in parser.script_sources:
        if source.startswith(("http://", "https://", "//", "data:")):
            continue
        script_path = (html_path.parent / source).resolve()
        local_script_paths[source] = script_path
        if script_path.exists() and script_path.is_file():
            loaded_script_paths.add(script_path)
            if script_path.name in {"echarts.min.js", "mermaid.min.js"}:
                continue
            script_text = script_path.read_text(encoding="utf-8")
            chart_logic_parts.append(script_text)
            interaction_code_parts.append(script_text)
        else:
            missing_local_scripts.append(source)
    for chart_path in chart_paths:
        if chart_path in loaded_script_paths:
            continue
        chart_script = chart_path.read_text(encoding="utf-8")
        chart_logic_parts.append(chart_script)
        interaction_code_parts.append(chart_script)
    chart_code = "\n".join(chart_logic_parts)
    interaction_code = "\n".join(interaction_code_parts)

    failures: list[str] = []
    warnings: list[str] = []

    report_name_match = REPORT_NAME_RE.fullmatch(html_path.stem)
    if not report_name_match:
        failures.append(
            "Primary report filename must end in -YYYY-MM-DD; weekly reports must end "
            "in -YYYY-MM-DD-wNN."
        )
    elif html_path.parent.name != html_path.stem:
        failures.append(
            "Primary report directory and HTML filename must use the same dated basename."
        )

    if parser.report_cadence not in VALID_CADENCES:
        failures.append(
            "Root <html> must define data-report-cadence as alert, daily, weekly, monthly, "
            "or one-off."
        )
    parsed_run_date: date | None = None
    try:
        parsed_run_date = date.fromisoformat(parser.run_date)
    except ValueError:
        failures.append("Root <html> must define data-run-date in YYYY-MM-DD format.")

    if report_name_match and parsed_run_date:
        if report_name_match.group("date") != parser.run_date:
            failures.append("Filename date must match the root data-run-date.")
        week_suffix = report_name_match.group("week")
        if parser.report_cadence == "weekly":
            expected_week = f"-w{parsed_run_date.isocalendar().week:02d}"
            if (week_suffix or "").lower() != expected_week:
                failures.append(
                    f"Weekly filename must end in {expected_week} for data-run-date "
                    f"{parser.run_date}."
                )
        elif week_suffix:
            failures.append("Only weekly reports may use the -wNN filename suffix.")

    first_line = html.splitlines()[0].strip() if html.splitlines() else ""
    if first_line != "<!-- Generated by Trae Work -->":
        failures.append("Missing the html-report runtime comment on line 1.")
    if missing_local_scripts:
        failures.append(
            "Missing local script file(s): " + ", ".join(missing_local_scripts) + "."
        )

    if not parser.html_blueprint:
        failures.append("Missing html[data-radar-blueprint].")
    elif parser.html_blueprint not in BLUEPRINT_FRAMEWORKS:
        failures.append(
            "html[data-radar-blueprint] must be one of the six manifest styles."
        )
    if not parser.html_framework:
        failures.append("Missing html[data-radar-framework].")
    elif parser.html_framework not in VALID_FRAMEWORKS:
        failures.append(
            "html[data-radar-framework] must be exhibit-path, index-gate, or reading-rail."
        )
    if parser.html_blueprint in BLUEPRINT_FRAMEWORKS:
        expected_framework = BLUEPRINT_FRAMEWORKS[parser.html_blueprint]
        if parser.html_framework != expected_framework:
            failures.append(
                f"Blueprint {parser.html_blueprint} requires framework "
                f"{expected_framework} from the random style manifest."
            )
        expected_asset = f"{parser.html_blueprint}.svg"
        if parser.radar_style_asset != expected_asset:
            failures.append(
                f"Blueprint {parser.html_blueprint} requires "
                f'data-radar-style-asset="{expected_asset}".'
            )
    if parser.radar_route != "uniform-random":
        failures.append('Root <html> must define data-radar-route="uniform-random".')
    if not re.fullmatch(r"[0-9a-f]{16}", parser.radar_selection_id, flags=re.I):
        failures.append(
            "Root <html> must define the 16-hex data-radar-selection-id returned by "
            "select_visual_style.py."
        )
    if parser.signal_count is None:
        failures.append("Missing html[data-signal-count].")
    elif parser.signal_count < 0:
        failures.append("html[data-signal-count] must be a non-negative integer.")

    if parser.report_sections < 1:
        failures.append("Missing analytical chapters marked with [data-report-section].")
    if parser.report_sections_without_id:
        failures.append(
            f"Found {parser.report_sections_without_id} [data-report-section] element(s) "
            "without a stable id."
        )

    if parser.html_framework in {"index-gate", "reading-rail"}:
        if parser.report_navs != 1:
            failures.append(
                f"{parser.html_framework} requires exactly one [data-report-nav]; "
                f"found {parser.report_navs}."
            )
        if parser.report_nav_current != 1:
            failures.append(
                "Framework navigation must expose exactly one aria-current=\"location\" item."
            )
        invalid_nav_links = [
            href
            for href in parser.report_nav_links
            if not href.startswith("#")
            or len(href) == 1
            or href[1:] not in parser.report_section_ids
        ]
        if invalid_nav_links:
            failures.append(
                "Framework navigation contains non-fragment or unmatched links: "
                + ", ".join(invalid_nav_links)
                + "."
            )
        nav_targets = {
            href[1:]
            for href in parser.report_nav_links
            if href.startswith("#") and len(href) > 1
        }
        if nav_targets != parser.report_section_ids:
            failures.append(
                "Framework navigation targets must match the analytical chapter ids."
            )
        if not re.search(r"scroll-margin-top\s*:", css, flags=re.I):
            failures.append("Navigable chapters require scroll-margin-top.")
        if (
            parser.html_framework == "reading-rail"
            and "IntersectionObserver" not in interaction_code
        ):
            failures.append(
                "Reading Rail requires IntersectionObserver-driven active chapter state."
            )
    elif parser.html_framework == "exhibit-path":
        if parser.report_navs:
            failures.append("Exhibit Path must not use persistent [data-report-nav].")
        if parser.report_sections >= 5:
            failures.append(
                "Exhibit Path may contain at most four analytical chapters; "
                "use Index Gate or Reading Rail."
            )

    unknown_card_roles = sorted(set(parser.card_roles) - VALID_CARD_ROLES)
    if unknown_card_roles:
        failures.append("Unknown data-card-role values: " + ", ".join(unknown_card_roles) + ".")

    h1 = re.sub(r"\s+", " ", unescape("".join(parser.h1_parts))).strip()
    if not h1:
        failures.append("Missing a visible H1 display verdict.")
    else:
        cjk_count = len(re.findall(r"[\u3400-\u9fff]", h1))
        japanese_count = len(re.findall(r"[\u3040-\u30ff]", h1))
        english_words = re.findall(r"[A-Za-z0-9][A-Za-z0-9'’-]*", h1)
        if cjk_count and cjk_count > 22:
            failures.append(f"Chinese display title has {cjk_count} characters; maximum is 22.")
        elif japanese_count and japanese_count > 28:
            failures.append(
                f"Japanese display title has {japanese_count} characters; maximum is 28."
            )
        elif not cjk_count and len(english_words) > 8:
            failures.append(
                f"English display title has {len(english_words)} words; maximum is 8."
            )

    if not 1 <= parser.title_line_count <= 3:
        failures.append(
            "Display verdict must contain 1–3 explicit [data-title-line] phrase spans."
        )

    visible_html = default_visible_html(html)
    visible_plain = visible_text(visible_html)
    paragraph_blocks = [
        visible_text(body)
        for body in re.findall(
            r"<p\b[^>]*>(.*?)</p>", visible_html, flags=re.I | re.S
        )
    ]
    long_paragraphs = []
    for paragraph in paragraph_blocks:
        cjk, words = text_volume(paragraph)
        if cjk > 70 or (cjk == 0 and words > 50):
            long_paragraphs.append((cjk, words))
    if long_paragraphs:
        failures.append(
            f"Found {len(long_paragraphs)} over-budget visible paragraph(s); "
            "move detail into visual fields or evidence disclosure."
        )

    signal_summaries = marked_text_blocks(visible_html, "data-signal-summary")
    over_budget_summaries = []
    for summary in signal_summaries:
        cjk, words = text_volume(summary)
        if cjk > 120 or (cjk == 0 and words > 75):
            over_budget_summaries.append((cjk, words))
    if over_budget_summaries:
        failures.append(
            f"Found {len(over_budget_summaries)} over-budget signal summary block(s)."
        )

    stack_labels = (
        "event",
        "evidence",
        "delta",
        "meaning",
        "exposure",
        "move",
        "next trigger",
    )
    visible_lower = visible_plain.lower()
    internal_artifacts = [
        label
        for label in (
            "radar style contract",
            "exhibit path",
            "index gate",
            "reading rail",
            "framework studies",
            "data-radar-framework",
            "data-radar-blueprint",
            "lorem ipsum",
        )
        if label in visible_lower
    ]
    if internal_artifacts:
        failures.append(
            "Internal design/build artifacts are visible: "
            + ", ".join(internal_artifacts)
            + "."
        )
    if all(re.search(rf"\b{re.escape(label)}\b", visible_lower) for label in stack_labels):
        failures.append(
            "Markdown-like seven-field Signal Stack is visible by default."
        )

    if parser.signal_count is not None and parser.signal_count >= 1:
        if parser.signal_details < 1:
            failures.append("Signal report is missing [data-signal-detail].")
        if parser.signal_count <= 6:
            if parser.signal_cards != parser.signal_count:
                failures.append(
                    f"Expected {parser.signal_count} signal card(s); "
                    f"found {parser.signal_cards}."
                )
            if parser.signal_card_roles != parser.signal_count:
                failures.append(
                    f"Expected {parser.signal_count} signal card role declaration(s); "
                    f"found {parser.signal_card_roles}."
                )
            if parser.signal_triggers != parser.signal_count:
                failures.append(
                    f"Expected {parser.signal_count} signal trigger(s); "
                    f"found {parser.signal_triggers}."
                )
        elif parser.signal_count <= 12 and parser.signal_cards > 3:
            failures.append(
                "Reports with 7–12 signals may show at most three detail cards."
            )
        elif parser.signal_count > 12 and parser.signal_cards > 2:
            failures.append(
                "Reports with more than 12 signals may show at most two detail cards."
            )
        if parser.signal_count >= 3 and parser.signal_overviews != 1:
            failures.append(
                f"Expected one [data-signal-overview]; found {parser.signal_overviews}."
            )
        if parser.signal_triggers:
            if parser.signal_trigger_buttons != parser.signal_triggers:
                failures.append("Every [data-signal-trigger] must be a native button.")
            if parser.signal_triggers_with_id != parser.signal_triggers:
                failures.append("Every [data-signal-trigger] requires [data-signal-id].")
            if parser.signal_triggers_with_pressed != parser.signal_triggers:
                failures.append("Every [data-signal-trigger] requires aria-pressed.")
        if parser.signal_card_ids != parser.signal_trigger_ids:
            failures.append("Signal card and trigger ids must use one shared state key.")
        if parser.signal_details and not parser.signal_detail_ids:
            failures.append("Signal evidence disclosure requires [data-signal-id].")
        if parser.signal_detail_ids - parser.signal_trigger_ids:
            failures.append("Signal detail ids must match existing signal trigger ids.")
        if parser.signal_count >= 2 and parser.live_regions != 1:
            failures.append(
                "Multi-signal reports require one [data-radar-live] polite live region."
            )

    if parser.signal_count is not None and parser.signal_count >= 2:
        has_signal_selector = bool(
            re.search(r"data-signal-trigger", interaction_code, flags=re.I)
        )
        has_signal_click = bool(
            re.search(
                r"(?:addEventListener\s*\(\s*[\"']click[\"']|"
                r"\.on\s*\(\s*[\"']click[\"'])",
                interaction_code,
                flags=re.I,
            )
        )
        if not has_signal_selector or not has_signal_click:
            failures.append(
                "Signal cards require scripted click synchronization with chart/detail state."
            )
        if ":focus-visible" not in css:
            failures.append("Interactive signal cards require a visible focus state.")
        if not re.search(
            r"(?:aria-pressed|is-selected|activeSignal)",
            css + "\n" + interaction_code,
            flags=re.I,
        ):
            failures.append("Interactive signal cards require one explicit selected state.")

    has_runtime_gradient = bool(
        re.search(r"\b(?:linear|radial|conic)-gradient\s*\(", css, flags=re.I)
    )
    if has_runtime_gradient:
        warnings.append(
            "Runtime gradient mode detected; verify that the selected html-report style requires it "
            "and that evidence surfaces remain opaque."
        )

    has_motion_css = bool(re.search(r"\b(?:transition|animation)\s*:", css, flags=re.I))
    if has_motion_css and not re.search(
        r"@media\s*\(\s*prefers-reduced-motion\s*:\s*reduce\s*\)",
        css,
        flags=re.I,
    ):
        failures.append("Motion CSS requires a prefers-reduced-motion: reduce override.")
    slow_transitions = [
        duration for duration in transition_durations_ms(css) if duration > 180
    ]
    if slow_transitions:
        failures.append(
            "Interaction transition exceeds 180ms: "
            + ", ".join(f"{duration:g}ms" for duration in slow_transitions)
            + "."
        )

    unsafe_headings = heading_wrap_violations(css)
    if unsafe_headings:
        failures.append(
            "Unsafe heading-wrap rule found in: " + ", ".join(unsafe_headings) + "."
        )

    color_tokens = extract_color_tokens(css)
    missing_tokens = sorted(REQUIRED_COLOR_TOKENS - color_tokens.keys())
    if missing_tokens:
        failures.append(f"Missing required color tokens: {', '.join(missing_tokens)}.")
    if (
        parser.html_blueprint in PURE_WHITE_BLUEPRINTS
        and color_tokens.get("--bg") not in PURE_WHITE_VALUES
    ):
        failures.append(
            f"Blueprint {parser.html_blueprint} requires pure white --bg (#ffffff)."
        )
    if LEGACY_RADAR_TOKEN_RE.search(css):
        failures.append("Legacy --radar-* color aliases found; use html-report canonical tokens.")
    custom_color_tokens = {
        name.lower()
        for name, value in re.findall(r"(--[\w-]+)\s*:\s*([^;}{]+)", css, flags=re.I)
        if COLOR_LITERAL_RE.search(value)
    }
    extra_color_tokens = sorted(custom_color_tokens - COLOR_TOKEN_NAMES)
    if extra_color_tokens:
        message = "Non-canonical color tokens found: " + ", ".join(extra_color_tokens) + "."
        (warnings if has_runtime_gradient else failures).append(message)

    literal_colors = {
        normalize_css_value(value) for value in COLOR_LITERAL_RE.findall(css)
    }
    if len(literal_colors) > 7:
        message = (
            f"Found {len(literal_colors)} literal base colors; canonical runtime maximum is 7."
        )
        (warnings if has_runtime_gradient else failures).append(message)
    css_without_token_values = re.sub(
        r"--(?:bg2?|ink|muted|rule|accent2?)\s*:\s*[^;}{]+;?", "", css, flags=re.I
    )
    raw_colors_outside_tokens = {
        normalize_css_value(value)
        for value in COLOR_LITERAL_RE.findall(css_without_token_values)
    }
    if raw_colors_outside_tokens:
        message = (
            "Raw colors outside html-report canonical token declarations: "
            + ", ".join(sorted(raw_colors_outside_tokens))
            + "."
        )
        (warnings if has_runtime_gradient else failures).append(message)

    font_sizes = declarations(css, "font-size")
    font_weights = declarations(css, "font-weight")
    font_families = declarations(css, "font-family")
    if len(font_sizes) > 8:
        warnings.append(
            f"Found {len(font_sizes)} font-size declarations; verify that runtime styles still "
            "resolve to a small hierarchy."
        )
    if len(font_weights) > 4:
        warnings.append(
            f"Found {len(font_weights)} font weights; verify that runtime typography remains coherent."
        )
    if len(font_families) > 3:
        failures.append(f"Found {len(font_families)} font families; maximum is 3.")

    edge_violations = accent_edge_violations(css)
    if edge_violations:
        failures.extend(f"Colored component edge: {item}." for item in edge_violations)

    if EMOJI_RE.search(h1):
        failures.append("Emoji found in the display verdict.")
    if parser.remote_scripts:
        failures.append(
            "Remote script dependencies found: " + ", ".join(parser.remote_scripts)
        )
    if re.search(
        r"(?:图表(?:加载|渲染)(?:失败|异常|不可用)|"
        r"(?:chart|visuali[sz]ation)\s+(?:failed|unable)\s+to\s+(?:load|render))",
        visible_plain,
        flags=re.I,
    ):
        failures.append(
            "Reader-facing chart failure copy found; replace it with the system-native visual fallback."
        )
    if parser.static_data_svgs:
        warnings.append(
            "Static SVG marked as data visualization; verify it is either a runtime-permitted "
            "minimal graphic or the exact-data native fallback for an interactive chart."
        )

    has_echarts = bool(
        re.search(r"echarts\s*\.\s*init\s*\(", chart_code, flags=re.I)
        or parser.interactive_chart_count
    )
    if has_echarts:
        echarts_sources = [
            source
            for source in parser.script_sources
            if Path(source.split("?", 1)[0]).name == "echarts.min.js"
        ]
        chart_sources = [
            source
            for source in parser.script_sources
            if re.search(
                r"(?:^|/)assets/(?:charts?|chart-[^/]+)\.js(?:\?.*)?$",
                source,
                flags=re.I,
            )
        ]
        if echarts_sources != ["./_shared/js/echarts.min.js"]:
            failures.append(
                "ECharts must load exactly once from ./_shared/js/echarts.min.js."
            )
        else:
            echarts_path = local_script_paths.get(echarts_sources[0])
            if (
                echarts_path is None
                or not echarts_path.is_file()
                or echarts_path.stat().st_size < 500_000
            ):
                failures.append(
                    "Runtime echarts.min.js is missing or does not look like the vendored library."
                )
        if not chart_sources:
            failures.append(
                "Interactive charts require external report-local logic in ./assets/charts.js "
                "or ./assets/chart-*.js."
            )
        elif echarts_sources:
            echarts_index = parser.script_sources.index(echarts_sources[0])
            early_chart_sources = [
                source
                for source in chart_sources
                if parser.script_sources.index(source) < echarts_index
            ]
            if early_chart_sources:
                failures.append(
                    "Chart scripts load before ECharts: "
                    + ", ".join(early_chart_sources)
                    + "."
                )
        last_chart_position = html.rfind("data-interactive-chart")
        early_script_tags = []
        for source in [*echarts_sources, *chart_sources]:
            match = re.search(
                rf"<script\b[^>]*src=[\"']{re.escape(source)}[\"'][^>]*>",
                html,
                flags=re.I,
            )
            if match and match.start() < last_chart_position:
                early_script_tags.append(source)
        if early_script_tags:
            failures.append(
                "ECharts and chart scripts must appear after all chart containers: "
                + ", ".join(early_script_tags)
                + "."
            )
        if any(
            re.search(r"echarts\s*\.\s*init\s*\(", script, flags=re.I)
            for script in inline_scripts
        ):
            failures.append(
                "Inline ECharts initialization found; move all chart logic to ./assets/charts.js."
            )
        missing_chart_ids = [
            index + 1
            for index, attributes in enumerate(parser.chart_containers)
            if not attributes.get("id")
        ]
        if missing_chart_ids:
            failures.append(
                "Interactive chart container(s) missing id: "
                + ", ".join(map(str, missing_chart_ids))
                + "."
            )
        short_chart_containers = [
            attributes.get("id", f"chart-{index + 1}")
            for index, attributes in enumerate(parser.chart_containers)
            if not chart_container_has_height(attributes, css)
        ]
        if short_chart_containers:
            failures.append(
                "Chart container(s) need an explicit min-height of at least 320px: "
                + ", ".join(short_chart_containers)
                + "."
            )
        chart_figures = [figure for figure in parser.chart_figures if figure["chart"]]
        missing_captions = sum(1 for figure in chart_figures if not figure["caption"])
        if len(chart_figures) != parser.interactive_chart_count:
            failures.append("Every interactive chart must be wrapped in its own <figure>.")
        if missing_captions:
            failures.append(
                f"Found {missing_captions} interactive chart figure(s) without <figcaption>."
            )
        if parser.chart_statuses < parser.interactive_chart_count:
            failures.append(
                "Every interactive chart requires an adjacent [data-chart-status] fallback."
            )
        if parser.chart_tables < parser.interactive_chart_count:
            failures.append(
                "Every interactive chart requires an adjacent [data-chart-table] exact fallback."
            )

        interaction_checks = {
            "echarts.init": bool(
                re.search(r"echarts\s*\.\s*init\s*\(", chart_code, flags=re.I)
            ),
            "SVG renderer": bool(
                re.search(
                    r"renderer\s*:\s*[\"']svg[\"']", chart_code, flags=re.I
                )
            ),
            "tooltip": bool(re.search(r"\btooltip\s*:", chart_code, flags=re.I)),
            "tooltip.appendToBody": bool(
                re.search(r"appendToBody\s*:\s*true", chart_code, flags=re.I)
            ),
            "emphasis": bool(re.search(r"\bemphasis\b", chart_code, flags=re.I)),
            "aria": bool(re.search(r"\baria\b", chart_code, flags=re.I)),
            "animation:false": bool(
                re.search(r"\banimation\s*:\s*false", chart_code, flags=re.I)
            ),
            "resize": bool(
                re.search(
                    r"addEventListener\s*\(\s*[\"']resize[\"']", chart_code, flags=re.I
                )
            ),
            "font-ready boot": "document.fonts" in chart_code,
            "ECharts availability guard": bool(
                re.search(r"(?:window\.)?echarts", chart_code, flags=re.I)
                and re.search(
                    r"(?:typeof\s+(?:window\.)?echarts|!window\.echarts|window\.echarts)",
                    chart_code,
                    flags=re.I,
                )
            ),
            "container guard": bool(
                re.search(
                    r"(?:if\s*\(\s*!?\s*(?:el|element|container)\b|getElementById\s*\()",
                    chart_code,
                    flags=re.I,
                )
            ),
            "error fallback": bool(
                re.search(r"\btry\s*\{", chart_code)
                and re.search(r"\bcatch\s*\(", chart_code)
            ),
            "instance reuse/dispose": bool(
                re.search(r"(?:getInstanceByDom|\.dispose\s*\()", chart_code)
            ),
            "canonical CSS colors": all(
                token in chart_code
                for token in ("--accent", "--ink", "--muted", "--rule", "--bg2")
            ),
        }
        if parser.signal_count is not None and parser.signal_count >= 2:
            interaction_checks["click synchronization"] = bool(
                re.search(
                    r"\.on\s*\(\s*[\"']click[\"']", chart_code, flags=re.I
                )
            )
        for name, passed in interaction_checks.items():
            if not passed:
                failures.append(f"Interactive chart is missing {name}.")

    generic_cards = len(
        re.findall(r"(?:kpi|metric|stat)[-_ ]card", html, flags=re.I)
    )
    if generic_cards >= 3:
        failures.append("Generic KPI/metric-card opening detected.")

    if len(h1) < 4:
        warnings.append("Display verdict may be too vague to carry the opening.")

    metrics: dict[str, object] = {
        "framework": parser.html_framework,
        "blueprint": parser.html_blueprint,
        "radar_route": parser.radar_route,
        "radar_selection_id": parser.radar_selection_id,
        "radar_style_asset": parser.radar_style_asset,
        "report_cadence": parser.report_cadence,
        "run_date": parser.run_date,
        "dated_basename": html_path.stem,
        "display_title": h1,
        "title_lines": parser.title_line_count,
        "color_tokens": color_tokens,
        "literal_color_count": len(literal_colors),
        "font_size_count": len(font_sizes),
        "font_weight_count": len(font_weights),
        "font_family_count": len(font_families),
        "has_interactive_chart": has_echarts,
        "interactive_charts": parser.interactive_chart_count,
        "chart_statuses": parser.chart_statuses,
        "chart_tables": parser.chart_tables,
        "script_sources": parser.script_sources,
        "signal_count": parser.signal_count,
        "signal_overviews": parser.signal_overviews,
        "signal_cards": parser.signal_cards,
        "signal_triggers": parser.signal_triggers,
        "signal_details": parser.signal_details,
        "report_sections": parser.report_sections,
        "report_navs": parser.report_navs,
        "card_roles": sorted(set(parser.card_roles)),
        "visible_paragraphs": len(paragraph_blocks),
        "signal_summaries": len(signal_summaries),
    }
    return failures, warnings, metrics


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Statically audit a Market Radar HTML report."
    )
    parser.add_argument("html", help="Path to the report HTML.")
    parser.add_argument(
        "--charts-js",
        action="append",
        default=[],
        help="Local chart script; repeat for multiple files.",
    )
    parser.add_argument("--json", action="store_true", help="Emit JSON.")
    parser.add_argument(
        "--warn-only",
        action="store_true",
        help="Return success even when failures are found.",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    html_path = Path(args.html).expanduser().resolve()
    chart_paths = [Path(path).expanduser().resolve() for path in args.charts_js]

    missing = [str(path) for path in [html_path, *chart_paths] if not path.is_file()]
    if missing:
        print("Missing file(s): " + ", ".join(missing), file=sys.stderr)
        return 2

    failures, warnings, metrics = audit(html_path, chart_paths)
    if args.json:
        print(
            json.dumps(
                {"passed": not failures, "failures": failures, "warnings": warnings, **metrics},
                ensure_ascii=False,
                indent=2,
            )
        )
    else:
        print("PASS" if not failures else "FAIL")
        for failure in failures:
            print(f"ERROR: {failure}")
        for warning in warnings:
            print(f"WARN: {warning}")
        print(
            "METRICS: "
            f"framework={metrics['framework'] or '-'} "
            f"blueprint={metrics['blueprint'] or '-'} "
            f"colors={metrics['literal_color_count']} "
            f"sizes={metrics['font_size_count']} "
            f"weights={metrics['font_weight_count']} "
            f"families={metrics['font_family_count']} "
            f"interactive={metrics['has_interactive_chart']} "
            f"chart_count={metrics['interactive_charts']} "
            f"signals={metrics['signal_count']} "
            f"cards={metrics['signal_cards']} "
            f"sections={metrics['report_sections']}"
        )
    return 0 if not failures or args.warn_only else 1


if __name__ == "__main__":
    raise SystemExit(main())
