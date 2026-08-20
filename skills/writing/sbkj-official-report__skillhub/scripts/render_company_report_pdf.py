#!/usr/bin/env python3
"""Render a UTF-8 Markdown company report to a watermarked PDF."""

from __future__ import annotations

import argparse
import html
import re
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.platypus import (
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


FONT_NAME = "STSong-Light"
PAGE_WIDTH, PAGE_HEIGHT = A4


def register_fonts() -> None:
    pdfmetrics.registerFont(UnicodeCIDFont(FONT_NAME))


def clean_inline(text: str) -> str:
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r"\1 (\2)", text)
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
        "title": ParagraphStyle(
            "Title",
            alignment=TA_CENTER,
            fontSize=22,
            leading=31,
            spaceAfter=12 * mm,
            textColor=colors.HexColor("#123B5D"),
            **common,
        ),
        "h2": ParagraphStyle(
            "Heading2",
            fontSize=16,
            leading=23,
            spaceBefore=7 * mm,
            spaceAfter=3 * mm,
            textColor=colors.HexColor("#123B5D"),
            **common,
        ),
        "h3": ParagraphStyle(
            "Heading3",
            fontSize=13,
            leading=19,
            spaceBefore=5 * mm,
            spaceAfter=2 * mm,
            textColor=colors.HexColor("#245D75"),
            **common,
        ),
        "h4": ParagraphStyle(
            "Heading4",
            fontSize=11,
            leading=17,
            spaceBefore=3 * mm,
            spaceAfter=1.5 * mm,
            textColor=colors.HexColor("#245D75"),
            **common,
        ),
        "body": ParagraphStyle(
            "Body",
            fontSize=9.5,
            leading=15,
            alignment=TA_LEFT,
            spaceAfter=2.5 * mm,
            textColor=colors.HexColor("#20252B"),
            **common,
        ),
        "bullet": ParagraphStyle(
            "Bullet",
            fontSize=9.5,
            leading=15,
            leftIndent=6 * mm,
            firstLineIndent=-3 * mm,
            spaceAfter=1.5 * mm,
            textColor=colors.HexColor("#20252B"),
            **common,
        ),
        "table_header": ParagraphStyle(
            "TableHeader",
            fontSize=8.5,
            leading=12,
            textColor=colors.white,
            alignment=TA_CENTER,
            **common,
        ),
        "table_cell": ParagraphStyle(
            "TableCell",
            fontSize=8,
            leading=12,
            textColor=colors.HexColor("#20252B"),
            **common,
        ),
        "code": ParagraphStyle(
            "Code",
            fontName="Courier",
            fontSize=8,
            leading=12,
            wordWrap="LTR",
            splitLongWords=True,
            leftIndent=4 * mm,
            rightIndent=4 * mm,
            borderColor=colors.HexColor("#D7DEE3"),
            borderWidth=0.5,
            borderPadding=4,
            backColor=colors.HexColor("#F5F7F8"),
            spaceAfter=3 * mm,
            textColor=colors.HexColor("#20252B"),
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
        style = styles["table_header"] if row_index == 0 else styles["table_cell"]
        data.append([Paragraph(clean_inline(cell) or " ", style) for cell in row])

    available_width = PAGE_WIDTH - 36 * mm
    table = Table(
        data,
        colWidths=[available_width / column_count] * column_count,
        repeatRows=1,
        hAlign="LEFT",
        splitByRow=1,
    )
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#245D75")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("BACKGROUND", (0, 1), (-1, -1), colors.white),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F4F7F8")]),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#C6D0D6")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    return table


def markdown_to_story(markdown_text: str, styles: dict[str, ParagraphStyle]) -> list:
    lines = markdown_text.splitlines()
    story: list = []
    paragraph_lines: list[str] = []
    index = 0

    def flush_paragraph() -> None:
        if paragraph_lines:
            text = " ".join(part.strip() for part in paragraph_lines if part.strip())
            if text:
                story.append(Paragraph(clean_inline(text), styles["body"]))
            paragraph_lines.clear()

    while index < len(lines):
        line = lines[index].rstrip()
        stripped = line.strip()

        if stripped.startswith("```"):
            flush_paragraph()
            index += 1
            code_lines = []
            while index < len(lines) and not lines[index].strip().startswith("```"):
                code_lines.append(lines[index])
                index += 1
            code_text = "<br/>".join(html.escape(item) for item in code_lines) or " "
            story.append(Paragraph(code_text, styles["code"]))
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

        heading = re.match(r"^(#{1,4})\s+(.+)$", stripped)
        if heading:
            flush_paragraph()
            level = len(heading.group(1))
            style_name = "title" if level == 1 else f"h{level}"
            story.append(Paragraph(clean_inline(heading.group(2)), styles[style_name]))
            index += 1
            continue

        if re.fullmatch(r"-{3,}", stripped):
            flush_paragraph()
            story.append(Spacer(1, 2 * mm))
            index += 1
            continue

        bullet = re.match(r"^[-*+]\s+(.+)$", stripped)
        ordered = re.match(r"^(\d+)\.\s+(.+)$", stripped)
        if bullet or ordered:
            flush_paragraph()
            marker = "•" if bullet else f"{ordered.group(1)}."
            content = bullet.group(1) if bullet else ordered.group(2)
            story.append(Paragraph(f"{marker} {clean_inline(content)}", styles["bullet"]))
            index += 1
            continue

        if stripped == "":
            flush_paragraph()
            index += 1
            continue

        if stripped == "<!-- pagebreak -->":
            flush_paragraph()
            story.append(PageBreak())
            index += 1
            continue

        paragraph_lines.append(stripped)
        index += 1

    flush_paragraph()
    return story


def make_page_callback(watermark: str, document_title: str):
    def draw_page(canvas, document) -> None:
        canvas.saveState()
        canvas.setAuthor("世舶科技")
        canvas.setTitle(document_title)
        canvas.setFont(FONT_NAME, 8)
        canvas.setFillColor(colors.HexColor("#64727C"))
        canvas.drawString(18 * mm, PAGE_HEIGHT - 12 * mm, "世舶科技企业招投标研究报告")
        canvas.drawRightString(PAGE_WIDTH - 18 * mm, 10 * mm, f"第 {document.page} 页")
        canvas.restoreState()

        canvas.saveState()
        canvas.translate(PAGE_WIDTH / 2, PAGE_HEIGHT / 2)
        canvas.rotate(35)
        canvas.setFont(FONT_NAME, 48)
        canvas.setFillColor(colors.HexColor("#9AA4AA"))
        if hasattr(canvas, "setFillAlpha"):
            canvas.setFillAlpha(0.10)
        canvas.drawCentredString(0, 0, watermark)
        canvas.restoreState()

    return draw_page


def render_pdf(input_path: Path, output_path: Path, watermark: str) -> None:
    register_fonts()
    markdown_text = input_path.read_text(encoding="utf-8")
    first_heading = re.search(r"^#\s+(.+)$", markdown_text, flags=re.MULTILINE)
    document_title = first_heading.group(1).strip() if first_heading else input_path.stem
    output_path.parent.mkdir(parents=True, exist_ok=True)

    document = SimpleDocTemplate(
        str(output_path),
        pagesize=A4,
        rightMargin=18 * mm,
        leftMargin=18 * mm,
        topMargin=20 * mm,
        bottomMargin=18 * mm,
        title=document_title,
        author="世舶科技",
        subject="企业招投标研究报告",
    )
    styles = build_styles()
    story = markdown_to_story(markdown_text, styles)
    if not story:
        story = [Paragraph("报告内容为空。", styles["body"])]
    page_callback = make_page_callback(watermark, document_title)
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
