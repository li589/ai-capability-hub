#!/usr/bin/env python3
"""
pdf_parse_structured.py — 结构化文档解析工具

利用 docling 进行版面分析, 输出结构化的 Markdown 和 JSON,
保留文档的标题层级、表格、列表等逻辑结构。

用法：
  pip install docling

  # 结构化解析为 Markdown + JSON
  python pdf_parse_structured.py input.pdf -o ./output

  # 输出包含: output/input.md + output/input.json + output/input_images/
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Any


# ── 文档解析引擎 ──────────────────────────────────────────────

def parse_document(input_path: str, do_ocr: bool = True,
                   do_table: bool = True, pages: str | None = None) -> dict[str, Any]:
    """
    使用 docling 解析文档, 返回结构化结果。

    参数:
        input_path: PDF 或图片路径
        do_ocr: 是否启用 OCR (扫描件需要)
        do_table: 是否检测表格结构
        pages: 页码范围, 如 "1-5,10" (None = 全部)
    """
    from docling.document_converter import DocumentConverter
    from docling.datamodel.pipeline_options import PdfPipelineOptions

    pipeline_opts = PdfPipelineOptions()
    pipeline_opts.do_ocr = do_ocr
    pipeline_opts.do_table_structure = do_table

    # 启用图片生成 (用于可视化)
    pipeline_opts.generate_page_images = True
    pipeline_opts.generate_table_images = True

    # 高级版面分析
    pipeline_opts.do_picture_classification = True
    pipeline_opts.do_formula_enrichment = True

    converter = DocumentConverter()
    result = converter.convert(input_path, pipeline_options=pipeline_opts)

    doc = result.document

    # ── 提取元数据 ──
    metadata = {
        "file": os.path.basename(input_path),
        "pages": len(doc.pages),
        "has_ocr": do_ocr,
    }

    # ── 提取各页内容 ──
    pages_data = []
    for page_num, page in doc.pages.items():
        page_info = {
            "page": page_num,
            "width": page.size.width if page.size else 0,
            "height": page.size.height if page.size else 0,
        }
        pages_data.append(page_info)

    # ── 提取文本内容（保留版面顺序） ──
    items = []
    # 遍历 docling 的 item 层级
    for item in doc.iterate_items():
        item_data = {
            "type": item.label.value if hasattr(item.label, 'value') else str(item.label),
            "text": item.text.strip() if item.text else "",
            "bbox": {
                "x": item.bbox.x if item.bbox else 0,
                "y": item.bbox.y if item.bbox else 0,
                "w": item.bbox.width if item.bbox else 0,
                "h": item.bbox.height if item.bbox else 0,
            } if item.bbox else None,
            "page": item.page_num if hasattr(item, 'page_num') else 0,
        }
        items.append(item_data)

    # ── 提取表格 ──
    tables = []
    for table in doc.tables:
        table_data = {
            "page": table.prov[0].page_no if table.prov else 0,
            "bbox": {
                "x": table.bbox.x if table.bbox else 0,
                "y": table.bbox.y if table.bbox else 0,
                "w": table.bbox.width if table.bbox else 0,
                "h": table.bbox.height if table.bbox else 0,
            } if table.bbox else None,
        }

        # 提取表格数据为二维数组
        grid = []
        for row in table.data:
            grid.append([cell.text if cell.text else "" for cell in row])
        table_data["grid"] = grid

        # 生成 Markdown 表格
        md_lines = []
        if grid:
            # 表头
            header = "| " + " | ".join(grid[0]) + " |"
            md_lines.append(header)
            # 分隔线
            sep = "| " + " | ".join(["---"] * len(grid[0])) + " |"
            md_lines.append(sep)
            # 数据行
            for row in grid[1:]:
                md_lines.append("| " + " | ".join(row) + " |")

        table_data["markdown"] = "\n".join(md_lines)
        tables.append(table_data)

    return {
        "metadata": metadata,
        "pages": pages_data,
        "items": items,
        "tables": tables,
        "text": doc.text if hasattr(doc, 'text') else "",
    }


# ── Markdown 生成 ──────────────────────────────────────────────

def generate_markdown(result: dict[str, Any], include_tables: bool = True) -> str:
    """将 docling 解析结果转为带结构的 Markdown"""
    lines = []

    # 文档信息
    meta = result["metadata"]
    lines.append(f"# 文档解析结果 — {meta['file']}")
    lines.append(f"> 页数: {meta['pages']} | OCR: {'是' if meta['has_ocr'] else '否'}")
    lines.append("")

    # 按页组织
    current_page = 0
    page_counter = 0

    for item in result["items"]:
        item_page = item.get("page", 0)

        if item_page != current_page:
            if current_page > 0:
                lines.append("---\n")
            page_counter += 1
            lines.append(f"\n## 第 {page_counter} 页\n")
            current_page = item_page

        item_type = item["type"]
        text = item["text"]

        if not text:
            continue

        # 根据类型输出
        if item_type in ("heading", "title", "section-heading"):
            # 检测标题层级 (基于字体大小/位置)
            level = 3  # 默认 h3
            lines.append(f"{'#' * level} {text}\n")
        elif item_type == "paragraph":
            lines.append(f"{text}\n")
        elif item_type == "list":
            lines.append(f"- {text}")
        elif item_type == "caption":
            lines.append(f"*{text}*\n")
        elif item_type == "page-header":
            lines.append(f"*{text}*  \n")
        elif item_type == "page-footer":
            lines.append(f"--- *{text}*\n")
        else:
            lines.append(f"{text}\n")

    # 表格
    if include_tables and result["tables"]:
        lines.append("\n## 表格\n")
        for i, table in enumerate(result["tables"]):
            if table["markdown"]:
                lines.append(f"### 表格 {i+1} (第 {table['page']} 页)\n")
                lines.append(table["markdown"])
                lines.append("")

    return "\n".join(lines)


# ── 工具函数 ───────────────────────────────────────────────────

def save_json(data: dict, output_path: str):
    """保存 JSON 结果"""
    os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def save_markdown(md: str, output_path: str):
    """保存 Markdown 结果"""
    os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(md)


def format_duration(seconds: float) -> str:
    if seconds < 1:
        return f"{seconds*1000:.0f}ms"
    elif seconds < 60:
        return f"{seconds:.1f}s"
    else:
        m, s = divmod(seconds, 60)
        return f"{int(m)}m{int(s)}s"


# ── CLI ────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="结构化文档解析 — 版面分析 + 表格提取 + 结构化输出",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s input.pdf -o ./output                  # 默认: OCR + 表格
  %(prog)s input.pdf -o ./output --no-ocr          # 文本层 PDF (更快)
  %(prog)s input.pdf -o ./output --no-table        # 跳过表格提取
  %(prog)s input.pdf -o ./output --pages "1-3"     # 仅前3页
  %(prog)s input.pdf -o ./output --json-only       # 仅输出 JSON
  %(prog)s input.pdf -o ./output --md-only         # 仅输出 Markdown

工作流集成:
  # 预处理 → 结构化解析
  python scripts/pdf_preprocess.py input.pdf -o ./preprocessed --all
  python scripts/pdf_parse_structured.py ./preprocessed/input_p001.jpg -o ./output

  # 直接解析 (平整扫描件)
  python scripts/pdf_parse_structured.py input.pdf -o ./output
        """
    )
    parser.add_argument('input', help='输入文件 (PDF / 图片)')
    parser.add_argument('-o', '--output', default='./output',
                        help='输出目录 (默认: ./output)')

    parser.add_argument('--no-ocr', action='store_true',
                        help='禁用 OCR (适用于文本层 PDF)')
    parser.add_argument('--no-table', action='store_true',
                        help='跳过表格结构检测')
    parser.add_argument('--pages', type=str, default=None,
                        help='页码范围, 如 "1-5,10" (默认: 全部)')
    parser.add_argument('--json-only', action='store_true',
                        help='仅输出 JSON')
    parser.add_argument('--md-only', action='store_true',
                        help='仅输出 Markdown')

    args = parser.parse_args()

    input_path = args.input
    if not os.path.exists(input_path):
        print(f"❌ 文件不存在: {input_path}")
        sys.exit(1)

    output_dir = args.output
    basename = os.path.splitext(os.path.basename(input_path))[0]

    print(f"📄 输入: {input_path}")
    print(f"   OCR: {'禁用' if args.no_ocr else '启用'}")
    print(f"   表格: {'跳过' if args.no_table else '检测'}")

    t0 = time.time()

    result = parse_document(
        input_path,
        do_ocr=not args.no_ocr,
        do_table=not args.no_table,
        pages=args.pages,
    )

    elapsed = time.time() - t0

    # 输出统计
    print(f"\n📊 解析统计:")
    print(f"   页数: {result['metadata']['pages']}")
    print(f"   元素: {len(result['items'])} 个")
    print(f"   表格: {len(result['tables'])} 个")
    print(f"   耗时: {format_duration(elapsed)}")

    # 保存结果
    os.makedirs(output_dir, exist_ok=True)

    if not args.md_only:
        json_path = os.path.join(output_dir, f"{basename}.json")
        save_json(result, json_path)
        print(f"\n   ✅ JSON: {json_path}")

    if not args.json_only:
        md = generate_markdown(result, include_tables=not args.no_table)
        md_path = os.path.join(output_dir, f"{basename}.md")
        save_markdown(md, md_path)
        print(f"   ✅ Markdown: {md_path}")

    print(f"\n✅ 结构化解析完成!")


if __name__ == '__main__':
    main()
