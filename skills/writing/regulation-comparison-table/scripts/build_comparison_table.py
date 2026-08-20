#!/usr/bin/env python3
"""
新旧条文对比表生成脚本。

输入：结构化 JSON 文件（描述若干个 sheet，每个 sheet 对应一部法规/合同的逐条对比数据）
输出：Excel 对比表，自动完成新旧条文的词语级差异高亮渲染：
  - 旧条文列：与新条文不同的片段加删除线，相同片段黑色普通
  - 新条文列：与旧条文不同的片段标红加粗，相同片段黑色普通
  - 纯新增条款（无旧文对应）：旧条文列写"（无对应条款）"，新条文列全文标红加粗
  - 纯删除条款（无新文对应）：旧条文列全文删除线，新条文列留空

差异比对采用词语级 diff（依赖 jieba 分词库，先分词再比较词语序列），而非逐字符比对，
避免"工商行政管理部门"与"负责商标执法的部门"因共享单字"商"被误判局部未变、
或"恶意"与"故意"这类整词含义完全不同却只标出单字差异的误导性渲染。
若运行环境未安装 jieba，会自动降级为字符级 diff 并打印警告，建议执行
`pip install jieba`（见 requirements.txt）以获得准确的词语级高亮。

用法：
    python3 build_comparison_table.py <input.json> <output.xlsx>

输入 JSON 结构说明见 references/table-format-spec.md。
"""
import sys
import json
import difflib
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from openpyxl.cell.rich_text import CellRichText, TextBlock
from openpyxl.cell.text import InlineFont
from openpyxl.utils import get_column_letter

# ---------- 样式常量 ----------
NORMAL_INLINE = InlineFont(color="000000", b=False, i=False, strike=False, sz="11")
CHANGED_OLD_INLINE = InlineFont(color="808080", b=False, i=False, strike=True, sz="11")   # 旧文中被改动/删除的片段：灰色删除线
CHANGED_NEW_INLINE = InlineFont(color="C00000", b=True, i=False, strike=False, sz="11")   # 新文中新增/修改的片段：红色加粗

TITLE_FONT = Font(bold=True, size=13)
LEGEND_FONT = Font(size=9, italic=True, color="666666")
HEADER_FONT = Font(bold=True, size=11, color="FFFFFF")
HEADER_LINK_FONT = Font(bold=True, size=11, color="FFFFFF", underline="single")
HEADER_FILL = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
SECTION_FONT = Font(bold=True, size=11, color="C00000")
SECTION_FILL = PatternFill(start_color="FCE4D6", end_color="FCE4D6", fill_type="solid")

THIN = Side(style="thin", color="BFBFBF")
CELL_BORDER = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)

WRAP_TOP_LEFT = Alignment(wrap_text=True, vertical="top", horizontal="left")
WRAP_TOP_CENTER = Alignment(wrap_text=True, vertical="top", horizontal="center")

COLUMN_HEADERS = ["对应旧条次", "旧条文原文", "新条次", "新条文", "变更说明"]
COLUMN_WIDTHS = [14, 55, 14, 55, 30]

LEGEND_TEXT = "说明：红色加粗文字＝新增或修改内容；灰色删除线文字＝被删除或改写内容；黑色普通文字＝保留一致内容。"


CN_DIGIT = {"零": 0, "一": 1, "二": 2, "三": 3, "四": 4, "五": 5, "六": 6, "七": 7, "八": 8, "九": 9, "十": 10}


def cn_number_to_int(cn):
    """将中文数字（十以内的条次场景，如“十一”“二十三”“三十”）转换为整数，无法解析返回 None。"""
    if not cn:
        return None
    if cn == "十":
        return 10
    total = 0
    if "十" in cn:
        parts = cn.split("十")
        tens = CN_DIGIT.get(parts[0], 1) if parts[0] else 1
        total += tens * 10
        if len(parts) > 1 and parts[1]:
            units = CN_DIGIT.get(parts[1])
            if units is None:
                return None
            total += units
        return total
    if len(cn) == 1:
        return CN_DIGIT.get(cn)
    return None


def extract_article_number(no_text):
    """从条次文本（如“第十一条”“第九条 + 第十条”）中提取首个条次编号，用于连续性校验。"""
    if not no_text:
        return None
    import re
    m = re.search(r"第([一二三四五六七八九十零]+)条", no_text)
    if not m:
        return None
    return cn_number_to_int(m.group(1))


def check_new_no_continuity(sheet_name, rows):
    """检查 rows 中 new_no 的条次编号是否从 1 开始连续、无跳号无重复，仅打印警告不阻断生成。"""
    numbers = []
    for row in rows:
        n = extract_article_number(row.get("new_no"))
        if n is not None:
            numbers.append(n)
    if not numbers:
        return
    expected = list(range(1, len(numbers) + 1))
    if numbers != expected:
        print(f"⚠️  警告：sheet「{sheet_name}」的新条次序列可能不连续或存在跳号/重复，请人工核对对齐是否有遗漏！")
        print(f"    实际序列：{numbers}")
        print(f"    期望序列：{expected}")


try:
    import jieba
    jieba.setLogLevel(60)  # 抑制jieba初始化时的日志输出，避免污染终端
    _JIEBA_AVAILABLE = True
except ImportError:
    _JIEBA_AVAILABLE = False
    print("⚠️  警告：未安装 jieba 分词库，将降级为字符级差异比对。机构名称、专有名词整体替换等场景可能出现误导性的\"共享单字未变\"渲染。建议执行 `pip install jieba` 后重新生成，以获得更准确的词语级差异高亮。")


def _tokenize(text):
    """将文本分词为 token 列表；jieba 不可用时按单字符切分（等价于原字符级 diff）。"""
    if _JIEBA_AVAILABLE:
        return list(jieba.cut(text))
    return list(text)


def diff_runs(old_text, new_text):
    """对旧、新文本做词语级 diff（基于 jieba 分词后按词序列比较，而非按单字符比较），
    返回 (old_runs, new_runs)，每个 run 为 (text, is_changed)。

    词语级 diff 相比字符级 diff 的关键差异：以完整词语为最小比较单元，避免机构名称、
    专有名词整体替换时因偶然共享单字（如"国务院工商行政管理部门商标局"与"国务院商标
    管理部门"共享"国务院""商标"）被误判为局部未变；也避免"恶意""故意"这类仅一字之
    差但语义完全不同的词被拆开只标注单字差异、掩盖了整词都变了的事实。
    """
    old_tokens = _tokenize(old_text)
    new_tokens = _tokenize(new_text)
    sm = difflib.SequenceMatcher(a=old_tokens, b=new_tokens, autojunk=False)
    old_runs, new_runs = [], []
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            seg = "".join(old_tokens[i1:i2])
            if seg:
                old_runs.append((seg, False))
                new_runs.append((seg, False))
        elif tag == "delete":
            seg = "".join(old_tokens[i1:i2])
            if seg:
                old_runs.append((seg, True))
        elif tag == "insert":
            seg = "".join(new_tokens[j1:j2])
            if seg:
                new_runs.append((seg, True))
        elif tag == "replace":
            seg_old = "".join(old_tokens[i1:i2])
            seg_new = "".join(new_tokens[j1:j2])
            if seg_old:
                old_runs.append((seg_old, True))
            if seg_new:
                new_runs.append((seg_new, True))
    return _merge_adjacent_runs(old_runs), _merge_adjacent_runs(new_runs)


def _merge_adjacent_runs(runs):
    """合并相邻且 is_changed 状态相同的 run，减少富文本 TextBlock 数量、避免视觉上的碎片化断裂。"""
    if not runs:
        return runs
    merged = [runs[0]]
    for text, changed in runs[1:]:
        last_text, last_changed = merged[-1]
        if changed == last_changed:
            merged[-1] = (last_text + text, changed)
        else:
            merged.append((text, changed))
    return merged


def build_rich_text(runs, changed_inline):
    """将 run 列表渲染为 CellRichText。仅一个 run 且未改动时返回纯字符串，减小文件复杂度。"""
    if not runs:
        return ""
    if len(runs) == 1 and not runs[0][1]:
        return runs[0][0]
    blocks = []
    for text, changed in runs:
        font = changed_inline if changed else NORMAL_INLINE
        blocks.append(TextBlock(font, text))
    return CellRichText(*blocks)


def render_pair(old_text, new_text):
    """返回 (old_cell_value, new_cell_value)，已完成差异高亮渲染。"""
    old_text = (old_text or "").strip()
    new_text = (new_text or "").strip()

    if old_text and not new_text:
        # 纯删除：旧文整体删除线，新文留空
        old_val = build_rich_text([(old_text, True)], CHANGED_OLD_INLINE)
        return old_val, ""
    if new_text and not old_text:
        # 纯新增：旧文列写占位说明，新文整体标红加粗
        new_val = build_rich_text([(new_text, True)], CHANGED_NEW_INLINE)
        return "（无对应条款）", new_val
    if not old_text and not new_text:
        return "", ""

    old_runs, new_runs = diff_runs(old_text, new_text)
    old_val = build_rich_text(old_runs, CHANGED_OLD_INLINE)
    new_val = build_rich_text(new_runs, CHANGED_NEW_INLINE)
    return old_val, new_val


def write_row(ws, row_idx, old_no, old_text, new_no, new_text, change_note):
    old_val, new_val = render_pair(old_text, new_text)
    values = [old_no or "", old_val, new_no or "", new_val, change_note or ""]
    for col_idx, val in enumerate(values, start=1):
        cell = ws.cell(row=row_idx, column=col_idx, value=val)
        cell.border = CELL_BORDER
        cell.alignment = WRAP_TOP_CENTER if col_idx in (1, 3) else WRAP_TOP_LEFT


def build_sheet(wb, sheet_def):
    sheet_name = sheet_def["sheet_name"][:31]  # Excel sheet 名称长度上限 31
    ws = wb.create_sheet(title=sheet_name)

    n_cols = len(COLUMN_HEADERS)

    # 第1行：标题
    ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=n_cols)
    title_cell = ws.cell(row=1, column=1, value=sheet_def.get("title", sheet_name))
    title_cell.font = TITLE_FONT
    title_cell.alignment = Alignment(horizontal="center", vertical="center")
    ws.row_dimensions[1].height = 26

    # 第2行：图例说明
    ws.merge_cells(start_row=2, start_column=1, end_row=2, end_column=n_cols)
    legend_cell = ws.cell(row=2, column=1, value=sheet_def.get("legend", LEGEND_TEXT))
    legend_cell.font = LEGEND_FONT
    legend_cell.alignment = Alignment(horizontal="left", vertical="center")

    # 第3行：表头
    headers = list(COLUMN_HEADERS)
    if sheet_def.get("old_column_header"):
        headers[1] = sheet_def["old_column_header"]
    if sheet_def.get("new_column_header"):
        headers[3] = sheet_def["new_column_header"]
    header_urls = {2: sheet_def.get("old_source_url"), 4: sheet_def.get("new_source_url")}
    for col_idx, text in enumerate(headers, start=1):
        cell = ws.cell(row=3, column=col_idx, value=text)
        url = header_urls.get(col_idx)
        if url:
            cell.hyperlink = url
            cell.font = HEADER_LINK_FONT
        else:
            cell.font = HEADER_FONT
        cell.fill = HEADER_FILL
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        cell.border = CELL_BORDER

    row_idx = 4
    for row in sheet_def.get("rows", []):
        write_row(
            ws, row_idx,
            row.get("old_no"), row.get("old_text"),
            row.get("new_no"), row.get("new_text"),
            row.get("change_note"),
        )
        row_idx += 1

    check_new_no_continuity(sheet_name, sheet_def.get("rows", []))

    unretained = sheet_def.get("unretained_clauses") or []
    if unretained:
        ws.merge_cells(start_row=row_idx, start_column=1, end_row=row_idx, end_column=n_cols)
        section_cell = ws.cell(row=row_idx, column=1, value="旧文中未被保留的条款（内容已并入其他条款或删除，未在上表单独列出）")
        section_cell.font = SECTION_FONT
        section_cell.fill = SECTION_FILL
        section_cell.alignment = Alignment(horizontal="left", vertical="center")
        row_idx += 1
        for item in unretained:
            old_no = item.get("old_no", "")
            old_text = item.get("old_text", "")
            disposition = item.get("disposition", "")
            values = [old_no, old_text, "—", "", disposition]
            for col_idx, val in enumerate(values, start=1):
                cell = ws.cell(row=row_idx, column=col_idx, value=val)
                cell.border = CELL_BORDER
                cell.alignment = WRAP_TOP_CENTER if col_idx in (1, 3) else WRAP_TOP_LEFT
            row_idx += 1

    for col_idx, width in enumerate(COLUMN_WIDTHS, start=1):
        ws.column_dimensions[get_column_letter(col_idx)].width = width

    ws.freeze_panes = "A4"


def main():
    if len(sys.argv) != 3:
        print("用法：python3 build_comparison_table.py <input.json> <output.xlsx>")
        sys.exit(1)

    input_path, output_path = sys.argv[1], sys.argv[2]
    with open(input_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    sheets = data.get("sheets")
    if not sheets:
        print("错误：输入 JSON 中未找到 sheets 数组")
        sys.exit(1)

    wb = Workbook()
    wb.remove(wb.active)
    for sheet_def in sheets:
        build_sheet(wb, sheet_def)

    wb.save(output_path)
    print(f"已生成对比表：{output_path}（共 {len(sheets)} 个 sheet）")


if __name__ == "__main__":
    main()
