#!/usr/bin/env python3
"""Render a UTF-8 Markdown bidder reference report to a polished PDF."""

from __future__ import annotations

import argparse
import html
import re
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.platypus import (
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


FONT_NAME = "STSong-Light"
PAGE_WIDTH, PAGE_HEIGHT = A4
ACCENT = colors.HexColor("#0F766E")
ACCENT_DARK = colors.HexColor("#17324D")
ACCENT_SOFT = colors.HexColor("#EEF7F6")
TEXT = colors.HexColor("#202832")
MUTED = colors.HexColor("#66717C")
LINE = colors.HexColor("#D9E3E7")
PAPER = colors.HexColor("#FAFBFC")
WARNING = colors.HexColor("#FFF7E6")
RISK = colors.HexColor("#FFF0F0")


def register_fonts() -> None:
    pdfmetrics.registerFont(UnicodeCIDFont(FONT_NAME))


def clean_inline(text: str) -> str:
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r"\1 (\2)", text)
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"(\*\*|__)(.+?)\1", r"\2", text)
    text = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"\1", text)
    text = re.sub(r"`([^`]+)`", r"\1", text)
    return html.escape(text.strip())


def build_styles() -> dict[str, ParagraphStyle]:
    common = {
        "fontName": FONT_NAME,
        "wordWrap": "CJK",
        "splitLongWords": True,
    }
    return {
        "cover_title": ParagraphStyle(
            "CoverTitle",
            alignment=TA_LEFT,
            fontSize=23,
            leading=30,
            spaceAfter=2 * mm,
            textColor=ACCENT_DARK,
            **common,
        ),
        "cover_subtitle": ParagraphStyle(
            "CoverSubtitle",
            alignment=TA_LEFT,
            fontSize=13,
            leading=18,
            spaceAfter=7 * mm,
            textColor=ACCENT,
            **common,
        ),
        "cover_meta": ParagraphStyle(
            "CoverMeta",
            alignment=TA_LEFT,
            fontSize=9.4,
            leading=15,
            textColor=MUTED,
            **common,
        ),
        "cover_kicker": ParagraphStyle(
            "CoverKicker",
            alignment=TA_LEFT,
            fontSize=8.5,
            leading=12,
            textColor=ACCENT,
            **common,
        ),
        "h1": ParagraphStyle(
            "Heading1",
            fontSize=16,
            leading=22,
            spaceBefore=5 * mm,
            spaceAfter=3 * mm,
            textColor=ACCENT_DARK,
            borderColor=ACCENT,
            borderWidth=0,
            borderPadding=0,
            **common,
        ),
        "h2": ParagraphStyle(
            "Heading2",
            fontSize=12.8,
            leading=18,
            spaceBefore=4 * mm,
            spaceAfter=2 * mm,
            textColor=ACCENT_DARK,
            **common,
        ),
        "h3": ParagraphStyle(
            "Heading3",
            fontSize=11.5,
            leading=17,
            spaceBefore=3 * mm,
            spaceAfter=1.5 * mm,
            textColor=ACCENT,
            **common,
        ),
        "body": ParagraphStyle(
            "Body",
            fontSize=9.1,
            leading=14.2,
            alignment=TA_LEFT,
            spaceAfter=2.2 * mm,
            textColor=TEXT,
            **common,
        ),
        "small": ParagraphStyle(
            "Small",
            fontSize=8,
            leading=11,
            textColor=MUTED,
            **common,
        ),
        "bullet": ParagraphStyle(
            "Bullet",
            fontSize=9.0,
            leading=14.0,
            leftIndent=6 * mm,
            firstLineIndent=-3 * mm,
            spaceAfter=1.4 * mm,
            textColor=TEXT,
            **common,
        ),
        "callout": ParagraphStyle(
            "Callout",
            fontSize=9.1,
            leading=14.2,
            leftIndent=3 * mm,
            rightIndent=3 * mm,
            borderColor=colors.HexColor("#D8C28E"),
            borderWidth=0.45,
            borderPadding=5,
            backColor=WARNING,
            textColor=colors.HexColor("#433415"),
            spaceAfter=3 * mm,
            **common,
        ),
        "table_header": ParagraphStyle(
            "TableHeader",
            fontSize=7.8,
            leading=10.4,
            textColor=ACCENT_DARK,
            alignment=TA_CENTER,
            **common,
        ),
        "table_cell": ParagraphStyle(
            "TableCell",
            fontSize=7.45,
            leading=10.5,
            textColor=TEXT,
            **common,
        ),
        "url_cell": ParagraphStyle(
            "UrlCell",
            fontSize=6.1,
            leading=8.4,
            textColor=colors.HexColor("#38536A"),
            **common,
        ),
    }


def split_table_row(line: str) -> list[str]:
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def is_table_separator(line: str) -> bool:
    cells = split_table_row(line)
    return bool(cells) and all(re.fullmatch(r":?-{3,}:?", cell) for cell in cells)


def make_table(rows: list[list[str]], styles: dict[str, ParagraphStyle]) -> Table:
    column_count = max(len(row) for row in rows)
    normalized = [row + [""] * (column_count - len(row)) for row in rows]
    data = []
    for row_index, row in enumerate(normalized):
        rendered = []
        for col_index, cell in enumerate(row):
            if row_index == 0:
                style = styles["table_header"]
            elif is_url_column(normalized[0], col_index):
                style = styles["url_cell"]
            else:
                style = styles["table_cell"]
            rendered.append(Paragraph(clean_inline(cell) or " ", style))
        data.append(rendered)

    available_width = PAGE_WIDTH - 32 * mm
    col_widths = table_col_widths(normalized[0], column_count, available_width)
    table = Table(
        data,
        colWidths=col_widths,
        repeatRows=1,
        hAlign="LEFT",
        splitByRow=1,
    )
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), ACCENT),
                ("TEXTCOLOR", (0, 0), (-1, 0), ACCENT_DARK),
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E8F3F1")),
                ("BACKGROUND", (0, 1), (-1, -1), colors.white),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, PAPER]),
                ("LINEABOVE", (0, 0), (-1, 0), 0.7, ACCENT),
                ("LINEBELOW", (0, 0), (-1, 0), 0.6, colors.HexColor("#B9D6D2")),
                ("INNERGRID", (0, 0), (-1, -1), 0.25, LINE),
                ("BOX", (0, 0), (-1, -1), 0.35, LINE),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    return table


def is_url_column(header: list[str], index: int) -> bool:
    if index >= len(header):
        return False
    return "网址" in header[index] or "地址" in header[index]


def table_col_widths(header: list[str], column_count: int, available_width: float) -> list[float]:
    joined = "|".join(header)
    if "机会方向" in joined and "切入动作" in joined and column_count == 5:
        return [25 * mm, 43 * mm, 32 * mm, 61 * mm, available_width - 161 * mm]
    if "主体" in joined and "建议策略" in joined and column_count == 4:
        return [34 * mm, 45 * mm, 49 * mm, available_width - 128 * mm]
    if "时间窗口" in joined and "可能机会" in joined and column_count == 5:
        return [28 * mm, 38 * mm, 38 * mm, 36 * mm, available_width - 140 * mm]
    if "准备事项" in joined and "交付材料建议" in joined and column_count == 3:
        return [34 * mm, 56 * mm, available_width - 90 * mm]
    if "原始公示网址" in joined and column_count == 5:
        return [43 * mm, 22 * mm, 25 * mm, 38 * mm, available_width - 128 * mm]
    if "项目名称" in joined and "建议动作" in joined and column_count == 6:
        return [35 * mm, 24 * mm, 23 * mm, 28 * mm, 35 * mm, available_width - 145 * mm]
    if "优先级" in joined and "行动" in joined and "核实资料" in joined and column_count == 4:
        return [20 * mm, 45 * mm, 72 * mm, available_width - 137 * mm]
    if column_count == 4:
        return [available_width * 0.25, available_width * 0.15, available_width * 0.30, available_width * 0.30]
    return [available_width / column_count] * column_count


def make_metric_cards(items: list[str], styles: dict[str, ParagraphStyle]) -> Table:
    cells = []
    for item in items[:6]:
        label, value = parse_metric(item)
        value_style = ParagraphStyle(
            "MetricValue",
            parent=styles["h2"],
            fontSize=12.3 if len(value) <= 14 else 9.8,
            leading=16 if len(value) <= 14 else 13.2,
            spaceAfter=0.7 * mm,
            textColor=ACCENT_DARK,
        )
        label_style = ParagraphStyle(
            "MetricLabel",
            parent=styles["small"],
            fontSize=7.7,
            leading=10.2,
            textColor=MUTED,
        )
        cell = [
            Paragraph(label, label_style),
            Spacer(1, 1.2 * mm),
            Paragraph(value, value_style),
        ]
        cells.append(cell)
    while len(cells) % 3:
        cells.append([Paragraph(" ", styles["h2"]), Paragraph(" ", styles["small"])])

    rows = [cells[index : index + 3] for index in range(0, len(cells), 3)]
    table = Table(rows, colWidths=[(PAGE_WIDTH - 32 * mm) / 3] * 3, hAlign="LEFT")
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.white),
                ("BOX", (0, 0), (-1, -1), 0.35, LINE),
                ("LINEABOVE", (0, 0), (-1, 0), 1.2, ACCENT),
                ("INNERGRID", (0, 0), (-1, -1), 2, colors.HexColor("#F2F6F7")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 7),
                ("RIGHTPADDING", (0, 0), (-1, -1), 7),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    return table


def make_decision_brief(items: list[str], styles: dict[str, ParagraphStyle]) -> Table:
    rows = []
    for item in items:
        label, value = parse_metric(item)
        label_style = ParagraphStyle(
            "DecisionLabel",
            parent=styles["small"],
            alignment=TA_RIGHT,
            textColor=ACCENT_DARK,
            fontSize=8.3,
            leading=11,
        )
        value_style = ParagraphStyle(
            "DecisionValue",
            parent=styles["body"],
            fontSize=9.0,
            leading=13.5,
            spaceAfter=0,
        )
        rows.append([Paragraph(label, label_style), Paragraph(value, value_style)])
    table = Table(rows, colWidths=[24 * mm, PAGE_WIDTH - 56 * mm], hAlign="LEFT")
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#F0F6F5")),
                ("BACKGROUND", (1, 0), (1, -1), colors.white),
                ("LINEBEFORE", (0, 0), (0, -1), 1.1, ACCENT),
                ("INNERGRID", (0, 0), (-1, -1), 0.25, LINE),
                ("BOX", (0, 0), (-1, -1), 0.35, LINE),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    return table


def parse_metric(text: str) -> tuple[str, str]:
    cleaned = clean_inline(text)
    if "：" in cleaned:
        label, value = cleaned.split("：", 1)
    elif ":" in cleaned:
        label, value = cleaned.split(":", 1)
    else:
        label, value = "关键指标", cleaned
    return label.strip(), value.strip() or "-"


def heading_level(line: str) -> tuple[int, str] | None:
    match = re.match(r"^(#{1,4})\s+(.+)$", line.strip())
    if not match:
        return None
    return len(match.group(1)), match.group(2).strip()


def extract_title(markdown_text: str, fallback: str) -> str:
    first_heading = re.search(r"^#\s+(.+)$", markdown_text, flags=re.MULTILINE)
    return first_heading.group(1).strip() if first_heading else fallback


def build_cover(title: str, markdown_text: str, styles: dict[str, ParagraphStyle]) -> list:
    meta_lines = []
    for line in markdown_text.splitlines()[1:18]:
        stripped = line.strip().lstrip("-").strip()
        if any(key in stripped for key in ("报告对象", "报告周期", "生成时间", "投标人", "数据支持")):
            meta_lines.append(clean_inline(stripped))
    if not meta_lines:
        meta_lines = ["投标参考报告", "数据支持：世舶科技招投标数据服务"]

    report_suffix = "投标人参考报告"
    if title.endswith(report_suffix) and len(title) > len(report_suffix):
        cover_title = title[: -len(report_suffix)]
        cover_title_flowables = [
            Paragraph(clean_inline(cover_title), styles["cover_title"]),
            Paragraph(report_suffix, styles["cover_subtitle"]),
        ]
    else:
        cover_title_flowables = [Paragraph(clean_inline(title), styles["cover_title"])]

    cover_table = Table(
        [
            [
                "",
                [
                    Paragraph("投标参考 / Bidder Reference", styles["cover_kicker"]),
                    Spacer(1, 5 * mm),
                    *cover_title_flowables,
                    Spacer(1, 2 * mm),
                    Paragraph("<br/>".join(meta_lines[:6]), styles["cover_meta"]),
                ],
            ]
        ],
        colWidths=[5 * mm, PAGE_WIDTH - 37 * mm],
    )
    cover_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (0, 0), ACCENT),
                ("BACKGROUND", (1, 0), (1, 0), colors.white),
                ("BOX", (0, 0), (-1, -1), 0.35, LINE),
                ("LEFTPADDING", (0, 0), (0, 0), 0),
                ("RIGHTPADDING", (0, 0), (0, 0), 0),
                ("LEFTPADDING", (1, 0), (1, 0), 12),
                ("RIGHTPADDING", (1, 0), (1, 0), 12),
                ("TOPPADDING", (0, 0), (-1, -1), 12),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
            ]
        )
    )
    return [cover_table, Spacer(1, 5 * mm)]


def markdown_to_story(markdown_text: str, styles: dict[str, ParagraphStyle], title: str) -> list:
    lines = markdown_text.splitlines()
    story: list = build_cover(title, markdown_text, styles)
    paragraph_lines: list[str] = []
    index = 0
    skip_first_h1 = True
    before_first_section = True
    current_section = ""

    def flush_paragraph() -> None:
        if paragraph_lines:
            text = " ".join(part.strip() for part in paragraph_lines if part.strip())
            if text:
                story.append(Paragraph(clean_inline(text), styles["body"]))
            paragraph_lines.clear()

    while index < len(lines):
        line = lines[index].rstrip()
        stripped = line.strip()

        if stripped == "<!-- pagebreak -->":
            flush_paragraph()
            story.append(PageBreak())
            index += 1
            continue

        if stripped.startswith("|") and index + 1 < len(lines) and is_table_separator(lines[index + 1]):
            flush_paragraph()
            rows = [split_table_row(stripped)]
            index += 2
            while index < len(lines) and lines[index].strip().startswith("|"):
                rows.append(split_table_row(lines[index]))
                index += 1
            story.append(make_table(rows, styles))
            story.append(Spacer(1, 3 * mm))
            continue

        heading = heading_level(stripped)
        if heading:
            flush_paragraph()
            level, heading_text = heading
            if level == 1 and skip_first_h1:
                skip_first_h1 = False
                index += 1
                continue
            before_first_section = False
            current_section = heading_text
            style_name = "h1" if level == 1 else "h2" if level == 2 else "h3"
            block = [
                Table(
                    [[Paragraph(clean_inline(heading_text), styles[style_name])]],
                    colWidths=[PAGE_WIDTH - 32 * mm],
                    hAlign="LEFT",
                )
            ]
            block[0].keepWithNext = True
            block[0].setStyle(
                TableStyle(
                    [
                        ("LINEBELOW", (0, 0), (-1, -1), 1.0 if level <= 2 else 0.4, ACCENT if level <= 2 else LINE),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                    ]
                )
            )
            story.append(KeepTogether(block))
            index += 1
            continue

        bullet = re.match(r"^[-*+]\s+(.+)$", stripped)
        ordered = re.match(r"^(\d+)\.\s+(.+)$", stripped)
        if bullet or ordered:
            flush_paragraph()
            content = bullet.group(1) if bullet else ordered.group(2)
            marker = "•" if bullet else f"{ordered.group(1)}."
            if before_first_section and is_cover_meta(content):
                index += 1
                continue

            next_items = collect_metric_block(lines, index)
            if current_section == "一页式投标决策摘要" and len(next_items) >= 3:
                story.append(make_decision_brief(next_items, styles))
                story.append(Spacer(1, 3 * mm))
                index += len(next_items)
                continue
            if current_section == "关键指标看板" and len(next_items) >= 3 and looks_like_metrics(next_items):
                story.append(make_metric_cards(next_items, styles))
                story.append(Spacer(1, 3 * mm))
                index += len(next_items)
                continue

            if current_section not in ("投标准备建议", "风险与不确定性", "下一步跟进清单") and any(
                word in content for word in ("风险", "建议", "注意", "核实", "机会等级", "推荐动作")
            ):
                story.append(Paragraph(clean_inline(content), styles["callout"]))
            else:
                story.append(Paragraph(f"{marker} {clean_inline(content)}", styles["bullet"]))
            index += 1
            continue

        if stripped == "":
            flush_paragraph()
            index += 1
            continue

        paragraph_lines.append(stripped)
        index += 1

    flush_paragraph()
    return story


def is_cover_meta(text: str) -> bool:
    return any(key in text for key in ("报告对象", "报告周期", "生成时间", "投标人关注方向", "数据支持"))


def collect_metric_block(lines: list[str], start: int) -> list[str]:
    items = []
    index = start
    while index < len(lines):
        stripped = lines[index].strip()
        match = re.match(r"^[-*+]\s+(.+)$", stripped)
        if not match:
            break
        items.append(match.group(1))
        index += 1
    return items


def looks_like_metrics(items: list[str]) -> bool:
    metric_words = ("数量", "金额", "地区", "品类", "项目", "企业", "机构", "合同", "机会", "风险")
    return sum(any(word in item for word in metric_words) for item in items[:6]) >= 3


def make_page_callback(watermark: str, document_title: str):
    def draw_page(canvas, document) -> None:
        canvas.saveState()
        canvas.setAuthor("世舶科技")
        canvas.setTitle(document_title)
        canvas.setStrokeColor(LINE)
        canvas.setLineWidth(0.35)
        canvas.line(16 * mm, PAGE_HEIGHT - 11 * mm, PAGE_WIDTH - 16 * mm, PAGE_HEIGHT - 11 * mm)
        canvas.setFont(FONT_NAME, 8)
        canvas.setFillColor(MUTED)
        canvas.drawString(16 * mm, PAGE_HEIGHT - 7 * mm, "世舶科技投标人参考报告")
        canvas.setFillColor(MUTED)
        canvas.drawRightString(PAGE_WIDTH - 16 * mm, 9 * mm, f"第 {document.page} 页")
        canvas.restoreState()

        canvas.saveState()
        canvas.translate(PAGE_WIDTH / 2, PAGE_HEIGHT / 2)
        canvas.rotate(35)
        canvas.setFont(FONT_NAME, 46)
        canvas.setFillColor(colors.HexColor("#9CA8AD"))
        if hasattr(canvas, "setFillAlpha"):
            canvas.setFillAlpha(0.045)
        canvas.drawCentredString(0, 0, watermark)
        canvas.restoreState()

    return draw_page


def render_pdf(input_path: Path, output_path: Path, watermark: str) -> None:
    register_fonts()
    markdown_text = input_path.read_text(encoding="utf-8")
    title = extract_title(markdown_text, input_path.stem)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    document = SimpleDocTemplate(
        str(output_path),
        pagesize=A4,
        rightMargin=16 * mm,
        leftMargin=16 * mm,
        topMargin=18 * mm,
        bottomMargin=16 * mm,
        title=title,
        author="世舶科技",
        subject="投标人参考报告",
    )
    styles = build_styles()
    story = markdown_to_story(markdown_text, styles, title)
    if not story:
        story = [Paragraph("报告内容为空。", styles["body"])]
    page_callback = make_page_callback(watermark, title)
    document.build(story, onFirstPage=page_callback, onLaterPages=page_callback)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path, help="UTF-8 Markdown report path")
    parser.add_argument("--output", type=Path, help="Output PDF path; defaults to the input basename")
    parser.add_argument("--watermark", default="世舶科技", help="Watermark text for every page")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    input_path = args.input.resolve()
    if not input_path.is_file():
        raise SystemExit(f"Input Markdown file not found: {input_path}")
    output_path = (args.output or input_path.with_suffix(".pdf")).resolve()
    render_pdf(input_path, output_path, args.watermark)
    print(output_path)


if __name__ == "__main__":
    main()
