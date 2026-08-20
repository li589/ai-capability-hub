#!/usr/bin/env python3
"""Validate a research report's citations and render self-contained HTML."""

from __future__ import annotations

import argparse
import html
import json
import os
from pathlib import Path
import re
import sys
import tempfile
from typing import Dict, Iterable, List, Optional, Sequence, Tuple
from urllib.parse import urlparse


REFERENCE_HEADING_RE = re.compile(r"^##\s+(参考资料|References)\s*$", re.IGNORECASE)
REFERENCE_RE = re.compile(
    r"^\s*(\d+)\.\s+\[([^\]]+)\]\((https?://[^)\s]+)\)(?:\s*[—-]\s*(.+))?\s*$"
)
CITATION_RE = re.compile(r"(?<!!)\[(\d+)\](?!\()")
REMOTE_IMAGE_RE = re.compile(r"!\[[^\]]*\]\(\s*(?:https?:)?//", re.IGNORECASE)
REMOTE_HTML_RE = re.compile(
    r"<(?:script|iframe|img|link)\b[^>]*(?:src|href)\s*=\s*[\"']?\s*(?:https?:)?//",
    re.IGNORECASE,
)
TRAE_REF_RE = re.compile(r"\$TRAE_REF")
REFERENCE_GATEWAY_MARKER_RE = re.compile(
    r"(?:文件发布(?:页)?|政策列表|新闻索引|首页|栏目页)",
    re.IGNORECASE,
)
WEAK_REFERENCE_MARKER_RE = re.compile(
    r"(?:未直接打开|间接引用|仅供参考|口径待确认|个人作者|个人账号|"
    r"普通账号|自媒体|论坛用户|股吧|无署名|来源不明|聚合转载|营销软文|\bUGC\b)",
    re.IGNORECASE,
)
UNVERIFIED_DOCUMENT_HOSTS = (
    "docin.com",
    "doc88.com",
    "wenku.baidu.com",
    "book118.com",
)
DATE_SUFFIX_RE = re.compile(
    r"\s*[，,、;；]\s*(?:(?:19|20)\d{2}(?:[-/.年]\d{1,2})?(?:[-/.月]\d{1,2}日?)?|日期不详)\s*$",
    re.IGNORECASE,
)
PLATFORM_ONLY_PUBLISHER_RE = re.compile(
    r"^(?:来源\s*[：:]\s*)?(?:今日头条|头条号|百家号|网易号|搜狐号|企鹅号|"
    r"微信公众号|微信公众平台|微博|雪球|CSDN|内容平台|自媒体平台|平台转载)"
    r"(?:\s*[（(].*?[）)])?$",
    re.IGNORECASE,
)
TABLE_DIVIDER_RE = re.compile(r"^\s*\|?(?:\s*:?-{3,}:?\s*\|)+\s*:?-{3,}:?\s*\|?\s*$")
CHART_NUMBER_RE = re.compile(r"^-?\d+(?:\.\d+)?$")
MERMAID_FENCE_RE = re.compile(r"^```\s*mermaid\s*$", re.IGNORECASE | re.MULTILINE)
FORECAST_MARKER_RE = re.compile(
    r"(?:预计|预测|有望|\b(?:19|20)\d{2}\s*[EF]\b)", re.IGNORECASE
)
EXHAUSTIVE_WITH_ETC_RE = re.compile(
    r"(?:仅含|仅包括|只含|只包括)[^。；\n]{0,120}(?:等|等等)"
)
INCOMPARABLE_RANGE_RE = re.compile(
    r"(?:区间|范围|下限|上限|从)[^。；\n]{0,180}"
    r"(?:窄口径|宽口径|不同口径|定义差异|口径差异)[^。；\n]{0,180}"
    r"(?:至|到|—|-|倍)",
    re.IGNORECASE,
)
INCOMPARABLE_RANGE_RE_REVERSED = re.compile(
    r"(?:窄口径|宽口径|不同口径|定义差异|口径差异)[^。；\n]{0,180}"
    r"(?:区间|范围|下限|上限|从)[^。；\n]{0,180}"
    r"(?:至|到|—|-|倍)",
    re.IGNORECASE,
)
NAMED_PRODUCT_TOKEN_RE = re.compile(
    r"\b(?:[A-Z][A-Za-z0-9+._-]*[a-z][A-Za-z0-9+._-]*|"
    r"[a-z][A-Za-z0-9+._-]*[A-Z][A-Za-z0-9+._-]*)\b"
)
COMPANY_CELL_FACT_RE = re.compile(
    r"(?:合作|绑定|旗下|全资|收入|盈利|上市|交付|融资|估值|收购|"
    r"控制权|政策|监管|计划|目标|份额|排名|第一|前十|龙头|领先|居前)"
)
PUE_VALUE_RE = re.compile(
    r"\bPUE(?:值)?\s*(?:可降至|可低至|可达|低至|降至|为|约|达到)?\s*(?:[=≤＜<]\s*)?(\d+(?:\.\d+)?)",
    re.IGNORECASE,
)
PROCESS_DISCLOSURE_RE = re.compile(
    r"(?:\bPASS_WITH_LIMITS\b|\bPASS\b|\bBLOCKED\b|\bSUPPORTED\b|"
    r"\bCORRECTABLE\b|\bUNSUPPORTED\b|\bINSUFFICIENT\b|WebSearch|WebFetch|"
    r"搜索批次|检索上限|页面上限|打开\s*\d+\s*(?:个|页)|校验(?:通过|失败)|"
    r"按要求停止|工具调用|内部状态码|规划候选|规划分配|"
    r"本轮(?:已)?打开(?:的)?页面|本轮(?:两次)?定向搜索|本次搜索(?:中)?|"
    r"本步骤(?:未|没有)取得|按规则舍弃|不纳入本稿)",
    re.IGNORECASE,
)


class ReportError(ValueError):
    """Raised when a report cannot be safely published."""


def looks_like_visual_dsl(lines: Sequence[str]) -> bool:
    """Detect chart/visual data that lost its fenced-block language label."""

    meaningful = [line.strip() for line in lines if line.strip()]
    if meaningful and meaningful[0].lower() in {"chart", "visual"}:
        meaningful = meaningful[1:]
    keys = {
        match.group(1).lower()
        for line in meaningful
        if (match := re.match(r"^([a-z][a-z-]*)\s*:\s*.+$", line, re.IGNORECASE))
    }
    has_records = any(line.lower().startswith("item:") for line in meaningful) or sum(
        1 for line in meaningful if "|" in line and not line.startswith(("#", "|---"))
    ) >= 2
    return {"title", "type", "source"}.issubset(keys) and has_records


def validate_fenced_blocks(markdown: str) -> None:
    """Reject only visualization-shaped unlabeled code, not ordinary code blocks."""

    in_fence = False
    language = ""
    block_lines: List[str] = []
    for line in markdown.splitlines():
        stripped = line.strip()
        if not in_fence:
            if stripped.startswith("```"):
                in_fence = True
                language = stripped[3:].strip().split(maxsplit=1)[0].lower() if stripped[3:].strip() else ""
                block_lines = []
            continue
        if stripped.startswith("```"):
            if language not in {"chart", "visual"} and looks_like_visual_dsl(block_lines):
                raise ReportError(
                    "疑似图表或结构图的数据块缺少 chart/visual 围栏标签，不能作为原始代码交付。"
                )
            in_fence = False
            language = ""
            block_lines = []
            continue
        block_lines.append(line)


def has_platform_only_publisher(details: str) -> bool:
    """Reject a hosting-platform label when no content publisher is named."""

    without_date = DATE_SUFFIX_RE.sub("", details).strip()
    return bool(PLATFORM_ONLY_PUBLISHER_RE.fullmatch(without_date))


def validate_reasoning_guards(body_lines: Sequence[str]) -> None:
    """Reject a few mechanically identifiable, high-impact reasoning errors."""

    for raw_line in body_lines:
        line = re.sub(r"\[(?:\d+)\]", "", raw_line)
        for match in PUE_VALUE_RE.finditer(line):
            if float(match.group(1)) < 1:
                raise ReportError("标准 PUE 是总设施能耗与 IT 设备能耗之比，不能小于 1。")
        if "倍" in line and any(
            term in line for term in ("不可直接比较", "不能直接比较", "不可比")
        ):
            raise ReportError("同一表述不能一边声明口径不可比，一边计算倍数。")
        if "产量" in line and "出货量" in line and "倍" in line:
            raise ReportError("产量与出货量不是同一指标，不能据此计算倍数。")
        if INCOMPARABLE_RANGE_RE.search(line) or INCOMPARABLE_RANGE_RE_REVERSED.search(line):
            raise ReportError("不同定义或口径的预测不能包装成统一区间、上下限或倍数。")
        if EXHAUSTIVE_WITH_ETC_RE.search(line):
            raise ReportError("“仅含/只包括”与“等”不能并用；请按来源改为完整边界或非穷尽列举。")

    index = 0
    while index + 1 < len(body_lines):
        header_line = body_lines[index]
        if "|" not in header_line or not TABLE_DIVIDER_RE.match(body_lines[index + 1]):
            index += 1
            continue

        headers = table_cells(header_line)
        is_company_table = (
            bool(headers)
            and any(keyword in headers[0] for keyword in ("企业", "公司"))
            and any(
                any(keyword in header for keyword in ("定位", "进展", "优势", "风险"))
                for header in headers[1:]
            )
        )
        property_indexes = [
            cell_index
            for cell_index, cell in enumerate(headers)
            if "性质" in cell or "实际/估算/预测" in cell
        ]
        excluded_indexes = {
            cell_index
            for cell_index, cell in enumerate(headers)
            if any(keyword in cell for keyword in ("来源", "发布方", "机构", "报告"))
        }
        row_index = index + 2
        while (
            row_index < len(body_lines)
            and body_lines[row_index].strip()
            and "|" in body_lines[row_index]
        ):
            cells = table_cells(body_lines[row_index])
            if is_company_table:
                for cell in cells[1:]:
                    if CITATION_RE.search(cell):
                        continue
                    visible_cell = re.sub(r"\[([^\]]+)\]\(https?://[^)\s]+\)", r"\1", cell)
                    if NAMED_PRODUCT_TOKEN_RE.search(visible_cell) or COMPANY_CELL_FACT_RE.search(
                        visible_cell
                    ):
                        raise ReportError(
                            "重点企业表中的产品、定位、进展或政策事实必须在同一表格单元格给出引用；不能借用同行其他列的引用。"
                        )
            for property_index in property_indexes:
                if property_index >= len(cells):
                    continue
                data_text = " ".join(
                    cell
                    for cell_index, cell in enumerate(cells)
                    if cell_index != property_index and cell_index not in excluded_indexes
                )
                if FORECAST_MARKER_RE.search(data_text) and "预测" not in cells[property_index]:
                    raise ReportError(
                        "表格数据含“预计/预测/有望”或 E/F 年份，但性质列没有标为预测。"
                    )
            row_index += 1
        index = row_index


def validate_core_findings(body_lines: Sequence[str]) -> None:
    """Require every numbered executive finding to carry its own evidence link."""

    current_section = ""
    found_numbered_item = False
    for line in body_lines:
        heading = re.match(r"^##\s+(.+?)\s*$", line)
        if heading:
            current_section = re.sub(r"[*_`]", "", heading.group(1)).strip()
            continue
        if not any(keyword in current_section for keyword in ("核心结论", "执行摘要")):
            continue
        item = re.match(r"^\s*\d+[.)]\s+(.+)$", line)
        if not item:
            continue
        found_numbered_item = True
        if not CITATION_RE.search(item.group(1)):
            raise ReportError("核心结论中的每一项都必须直接给出引用。")
    if any(
        re.match(r"^##\s+(?:核心结论|执行摘要)\s*$", line)
        for line in body_lines
    ) and not found_numbered_item:
        raise ReportError("核心结论必须使用带直接引用的编号列表。")


def split_references(lines: Sequence[str]) -> Tuple[List[str], int, List[str]]:
    matches = [index for index, line in enumerate(lines) if REFERENCE_HEADING_RE.match(line)]
    if len(matches) != 1:
        raise ReportError("报告必须且只能包含一个“## 参考资料”章节。")
    index = matches[0]
    return list(lines[:index]), index, list(lines[index + 1 :])


def validate_report(markdown: str) -> Tuple[List[str], int, Dict[int, Tuple[str, str, str]]]:
    if not markdown.strip():
        raise ReportError("报告内容为空。")
    if REMOTE_IMAGE_RE.search(markdown) or REMOTE_HTML_RE.search(markdown):
        raise ReportError("报告包含外部图片、脚本或样式依赖；HTML 必须可离线阅读。")
    if TRAE_REF_RE.search(markdown):
        raise ReportError("报告仍包含 $TRAE_REF；请改为连续编号引用并补齐参考资料。")
    if MERMAID_FENCE_RE.search(markdown):
        raise ReportError("报告不使用 Mermaid；请改用 visual 结构图代码块。")
    validate_fenced_blocks(markdown)

    lines = markdown.splitlines()
    body_lines, heading_index, reference_lines = split_references(lines)
    if PROCESS_DISCLOSURE_RE.search("\n".join(body_lines)):
        raise ReportError("报告包含内部执行过程或状态表达；请改为用户可理解的业务内容。")
    validate_reasoning_guards(body_lines)
    validate_core_findings(body_lines)
    references: Dict[int, Tuple[str, str, str]] = {}
    reference_order: List[int] = []
    reference_errors: List[str] = []

    for line in reference_lines:
        if not line.strip():
            continue
        match = REFERENCE_RE.match(line)
        if not match:
            reference_errors.append(f"参考资料格式不正确：{line.strip()}")
            continue
        number = int(match.group(1))
        title = match.group(2).strip()
        url = match.group(3).strip()
        details = (match.group(4) or "").strip()
        if number in references:
            reference_errors.append(f"参考资料编号重复：[{number}]")
            continue
        if not title:
            reference_errors.append(f"参考资料 [{number}] 缺少标题。")
        reference_label = f"{title} {details}"
        if REFERENCE_GATEWAY_MARKER_RE.search(reference_label):
            reference_errors.append(
                f"参考资料 [{number}] 是入口页或列表页；请引用实际包含所述事实的具体正文。"
            )
        elif WEAK_REFERENCE_MARKER_RE.search(reference_label):
            reference_errors.append(
                f"参考资料 [{number}] 标明个人内容、来源不明或未经核实，不能进入最终报告。"
            )
        hostname = (urlparse(url).hostname or "").lower()
        if any(hostname == host or hostname.endswith(f".{host}") for host in UNVERIFIED_DOCUMENT_HOSTS):
            reference_errors.append(
                f"参考资料 [{number}] 来自用户上传或文档预览平台；请改用原始报告正文或可信媒体具体编采稿。"
            )
        elif has_platform_only_publisher(details):
            reference_errors.append(
                f"参考资料 [{number}] 只写了承载平台，没有可识别的实际发布者；请补充发布主体和原始归因。"
            )
        references[number] = (title, url, details)
        reference_order.append(number)

    if reference_errors:
        details = "\n".join(f"- {error}" for error in reference_errors)
        raise ReportError(
            f"参考资料预检发现 {len(reference_errors)} 项问题：\n{details}"
        )

    if not references:
        raise ReportError("参考资料章节没有有效来源。")

    expected = list(range(1, len(references) + 1))
    if reference_order != expected:
        raise ReportError("参考资料编号必须从 1 开始连续排列。")

    citations = [int(value) for value in CITATION_RE.findall("\n".join(body_lines))]
    missing = sorted(set(citations) - set(references))
    if missing:
        joined = ", ".join(f"[{number}]" for number in missing)
        raise ReportError(f"正文引用没有对应的参考资料：{joined}")
    unused = sorted(set(references) - set(citations))
    if unused:
        joined = ", ".join(f"[{number}]" for number in unused)
        raise ReportError(f"参考资料未在正文使用：{joined}")
    if not citations:
        raise ReportError("正文没有任何引用。")

    return lines, heading_index, references


def inline_markdown(value: str) -> str:
    code_values: List[str] = []

    def stash_code(match: re.Match[str]) -> str:
        code_values.append(f"<code>{html.escape(match.group(1), quote=False)}</code>")
        return f"\x00CODE{len(code_values) - 1}\x00"

    value = re.sub(r"`([^`]+)`", stash_code, value)
    value = html.escape(value, quote=False)

    def replace_link(match: re.Match[str]) -> str:
        label = match.group(1)
        url = match.group(2)
        return f'<a href="{html.escape(url, quote=True)}">{label}</a>'

    value = re.sub(r"\[([^\]]+)\]\((https?://[^)\s]+)\)", replace_link, value)
    value = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", value)
    value = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"<em>\1</em>", value)
    value = CITATION_RE.sub(r'<a class="citation" href="#ref-\1">[\1]</a>', value)

    for index, code in enumerate(code_values):
        value = value.replace(f"\x00CODE{index}\x00", code)
    return value


def table_cells(line: str) -> List[str]:
    stripped = line.strip().strip("|")
    return [cell.strip() for cell in stripped.split("|")]


def render_table(header: str, rows: Iterable[str], prominent: bool = False) -> str:
    class_name = "table-wrap table-panel" if prominent else "table-wrap"
    parts = [f'<div class="{class_name}"><table><thead><tr>']
    parts.extend(f"<th>{inline_markdown(cell)}</th>" for cell in table_cells(header))
    parts.append("</tr></thead><tbody>")
    for row in rows:
        parts.append("<tr>")
        parts.extend(f"<td>{inline_markdown(cell)}</td>" for cell in table_cells(row))
        parts.append("</tr>")
    parts.append("</tbody></table></div>")
    return "".join(parts)


def normalize_property(value: str) -> str:
    aliases = {
        "actual": "实际",
        "实际值": "实际",
        "统计": "跟踪统计",
        "跟踪": "跟踪统计",
        "跟踪结果": "跟踪统计",
        "机构统计": "跟踪统计",
        "协会统计": "跟踪统计",
        "联盟统计": "跟踪统计",
        "tracking": "跟踪统计",
        "tracked": "跟踪统计",
        "estimate": "估算",
        "estimated": "估算",
        "测算": "估算",
        "forecast": "预测",
        "predicted": "预测",
        "预计": "预测",
        "mixed": "混合",
    }
    normalized = value.strip().lower()
    return aliases.get(normalized, value.strip())


def property_color(value: str) -> str:
    return {
        "实际": "#2563eb",
        "跟踪统计": "#7c3aed",
        "估算": "#0ea5b7",
        "预测": "#f59e0b",
    }.get(normalize_property(value), "#64748b")


def normalize_chart_purpose(value: str) -> str:
    aliases = {
        "趋势": "trend",
        "时间趋势": "trend",
        "比较": "comparison",
        "对比": "comparison",
        "构成": "composition",
        "份额": "composition",
        "关系": "relationship",
        "相关性": "relationship",
        "区间": "range",
        "情景": "range",
    }
    normalized = value.strip().lower()
    return aliases.get(normalized, normalized)


def chart_type_for(
    purpose: str,
    requested_type: str,
    rows: Sequence[Dict[str, object]],
) -> str:
    """Choose a chart deterministically from business purpose and data shape."""

    allowed = {
        "trend": {"line", "area"},
        "comparison": {"bar"},
        "composition": {"donut", "bar"},
        "relationship": {"scatter"},
        "range": {"range"},
    }
    if purpose not in allowed:
        raise ReportError(
            "图表 purpose 只支持 trend、comparison、composition、relationship 或 range。"
        )
    if requested_type != "auto":
        if requested_type not in allowed[purpose]:
            raise ReportError(
                f"图表 purpose={purpose} 不能使用 type={requested_type}；请选择与 purpose 对应的 type。"
            )
        if requested_type == "donut":
            values = [float(row["value"]) for row in rows]
            total = sum(values)
            if any(value < 0 for value in values) or not (
                98 <= total <= 102 or 0.98 <= total <= 1.02
            ):
                raise ReportError("环形图只适用于同一分母且合计约为 100% 的非负构成数据。")
        return requested_type

    if purpose == "trend":
        properties = {str(row["property"]) for row in rows}
        has_forecast = any(value == "预测" for value in properties)
        return "area" if len(rows) >= 5 and len(properties) == 1 and not has_forecast else "line"
    if purpose == "comparison":
        return "bar"
    if purpose == "composition":
        values = [float(row["value"]) for row in rows]
        total = sum(values)
        if (
            len(rows) <= 6
            and all(value >= 0 for value in values)
            and (98 <= total <= 102 or 0.98 <= total <= 1.02)
        ):
            return "donut"
        return "bar"
    if purpose == "relationship":
        return "scatter"
    return "range"


def render_chart(lines: Sequence[str], chart_index: int) -> Tuple[str, Dict[str, object]]:
    """Render a purpose-driven ECharts figure plus an accessible data fallback."""

    settings: Dict[str, str] = {}
    raw_rows: List[Tuple[str, bool]] = []
    for raw_line in lines:
        line = raw_line.strip()
        if not line:
            continue
        key_match = re.match(
            r"^(title|type|purpose|unit|x-axis|y-axis|x-unit|y-unit|period|geography|property|source)\s*:\s*(.+)$",
            line,
            re.IGNORECASE,
        )
        if key_match:
            key = key_match.group(1).lower()
            value = key_match.group(2).strip()
            if key != "title" and len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
                value = value[1:-1].strip()
            settings[key] = value
            continue
        item_match = re.match(r"^item\s*:\s*(.+)$", line, re.IGNORECASE)
        raw_rows.append((item_match.group(1).strip() if item_match else line, bool(item_match)))

    title = settings.get("title", "")
    requested_type = settings.get("type", "auto" if settings.get("purpose") else "bar").lower()
    purpose = normalize_chart_purpose(settings.get("purpose", ""))
    if not purpose:
        purpose = {
            "line": "trend",
            "area": "trend",
            "bar": "comparison",
            "donut": "composition",
            "scatter": "relationship",
            "range": "range",
        }.get(requested_type, "")
    source = settings.get("source", "")
    unit = settings.get("unit", "")
    x_axis = settings.get("x-axis", "")
    y_axis = settings.get("y-axis", "")
    x_unit = settings.get("x-unit", "")
    y_unit = settings.get("y-unit", "")
    period = settings.get("period", "")
    geography = settings.get("geography", "")
    chart_property = normalize_property(settings.get("property", ""))
    if not title:
        raise ReportError("图表缺少 title。")
    if requested_type not in ("auto", "line", "area", "bar", "donut", "scatter", "range"):
        raise ReportError("图表 type 只支持 auto、line、area、bar、donut、scatter 或 range。")
    if not purpose:
        raise ReportError("图表必须通过 purpose 标明要表达的业务关系。")
    adaptive = bool(settings.get("purpose")) or requested_type == "auto"
    if adaptive and any(not prefixed for _, prefixed in raw_rows):
        raise ReportError("自适应图表数据行必须以 item: 开头；不要写表头或裸数据行。")

    rows: List[Dict[str, object]] = []
    pair_purpose = purpose in {"relationship", "range"}
    for content, prefixed in raw_rows:
        cells = [cell.strip() for cell in content.split("|")]
        if not adaptive and (
            len(cells) in (2, 3, 4)
            and cells[0] in {"企业", "项目", "标签", "年份", "时期"}
            and cells[1] in {"数值", "值"}
        ):
            continue
        if pair_purpose:
            if (
                len(cells) not in (3, 4, 5)
                or not cells[0]
                or not CHART_NUMBER_RE.match(cells[1])
                or not CHART_NUMBER_RE.match(cells[2])
            ):
                raise ReportError(f"{purpose} 图表数据格式不正确：{content}")
            first_value = float(cells[1])
            second_value = float(cells[2])
            if purpose == "range" and first_value > second_value:
                raise ReportError(f"区间图下限不能大于上限：{content}")
            display = cells[3] if len(cells) >= 4 and cells[3] else (
                f"{cells[1]}—{cells[2]}" if purpose == "range" else f"{cells[1]} / {cells[2]}"
            )
            row_property = normalize_property(cells[4]) if len(cells) == 5 else ""
            rows.append(
                {
                    "label": cells[0],
                    "value": first_value,
                    "secondary": second_value,
                    "display": display,
                    "property": row_property,
                }
            )
        else:
            if len(cells) not in (2, 3, 4) or not cells[0] or not CHART_NUMBER_RE.match(cells[1]):
                raise ReportError(f"图表数据格式不正确：{content}")
            display = cells[2] if len(cells) >= 3 and cells[2] else cells[1]
            row_property = normalize_property(cells[3]) if len(cells) == 4 else ""
            rows.append(
                {
                    "label": cells[0],
                    "value": float(cells[1]),
                    "secondary": None,
                    "display": display,
                    "property": row_property,
                }
            )

    if len(rows) < 2 or len(rows) > 12:
        raise ReportError("图表必须包含 2—12 个可比数据点。")
    required_settings = [("period", period), ("geography", geography), ("property", chart_property)]
    if purpose == "relationship":
        required_settings.extend(
            (("x-axis", x_axis), ("y-axis", y_axis), ("x-unit", x_unit), ("y-unit", y_unit))
        )
    else:
        required_settings.append(("unit", unit))
    missing = [label for label, value in required_settings if not value]
    if missing:
        raise ReportError(
            f"图表缺少 {', '.join(missing)}；必须标明单位、时期、地域和数据性质。"
        )
    if chart_property not in ("实际", "跟踪统计", "估算", "预测", "混合"):
        raise ReportError("图表 property 只支持实际、跟踪统计、估算、预测或混合。")
    for row in rows:
        item_property = str(row["property"]) or chart_property
        if chart_property == "混合" and not row["property"]:
            raise ReportError("混合性质图表的每个数据点都必须在最后一列标明实际、跟踪统计、估算或预测。")
        if item_property not in ("实际", "跟踪统计", "估算", "预测"):
            raise ReportError("图表数据点性质只支持实际、跟踪统计、估算或预测。")
        row["property"] = item_property
    if purpose == "trend":
        forecast_seen = False
        for row in rows:
            if row["property"] == "预测":
                forecast_seen = True
            elif forecast_seen:
                raise ReportError("趋势图中的预测点必须连续放在实际、跟踪统计或估算点之后。")
    if not source or not CITATION_RE.search(source):
        raise ReportError("图表必须通过 source: [n] 标明来源。")
    resolved_type = chart_type_for(purpose, requested_type, rows)
    labels = [str(row["label"]) for row in rows]
    values = [
        {
            "value": row["value"],
            "name": row["label"],
            "display": row["display"],
            "property": row["property"],
            "itemStyle": {"color": property_color(str(row["property"]))},
        }
        for row in rows
    ]
    option: Dict[str, object]
    if resolved_type == "bar":
        horizontal = len(rows) > 5 or max(len(label) for label in labels) > 6
        value_axis = {
            "type": "value",
            "name": unit,
            "nameTextStyle": {"color": "#667085"},
            "axisLabel": {"color": "#667085"},
            "splitLine": {"lineStyle": {"color": "#e8edf4"}},
        }
        category_axis = {
            "type": "category",
            "data": labels,
            "axisLabel": {"color": "#334155", "width": 120, "overflow": "truncate"},
            "axisTick": {"show": False},
            "axisLine": {"show": False},
        }
        option = {
            "animationDuration": 650,
            "grid": {"left": 18, "right": 30, "top": 18, "bottom": 20, "containLabel": True},
            "tooltip": {"trigger": "item", "formatter": "{b}<br/>{c} " + unit},
            "xAxis": value_axis if horizontal else category_axis,
            "yAxis": category_axis if horizontal else value_axis,
            "series": [
                {
                    "type": "bar",
                    "data": values,
                    "barMaxWidth": 32,
                    "itemStyle": {"borderRadius": [0, 5, 5, 0] if horizontal else [5, 5, 0, 0]},
                }
            ],
        }
        if horizontal:
            option["yAxis"]["inverse"] = True  # type: ignore[index]
    elif resolved_type in {"line", "area"}:
        line_color = property_color(chart_property) if chart_property != "混合" else "#2563eb"
        forecast_index = next(
            (index for index, row in enumerate(rows) if row["property"] == "预测"), None
        )
        if forecast_index is None or forecast_index == 0:
            single_series: Dict[str, object] = {
                "name": "预测" if forecast_index == 0 else "数据",
                "type": "line",
                "data": values,
                "smooth": 0.22,
                "symbolSize": 9,
                "lineStyle": {
                    "width": 3,
                    "type": "dashed" if forecast_index == 0 else "solid",
                    "color": "#f59e0b" if forecast_index == 0 else line_color,
                },
            }
            if resolved_type == "area":
                single_series["areaStyle"] = {"color": "rgba(37,99,235,.10)"}
            series = [single_series]
        else:
            actual_data: List[Optional[Dict[str, object]]] = [
                values[index] if index < forecast_index else None for index in range(len(values))
            ]
            forecast_data: List[Optional[Dict[str, object]]] = [None] * len(values)
            forecast_data[forecast_index - 1] = values[forecast_index - 1]
            for index in range(forecast_index, len(values)):
                forecast_data[index] = values[index]
            series = [
                {
                    "name": "已确认",
                    "type": "line",
                    "data": actual_data,
                    "smooth": 0.22,
                    "symbolSize": 9,
                    "lineStyle": {"width": 3, "color": line_color},
                },
                {
                    "name": "预测",
                    "type": "line",
                    "data": forecast_data,
                    "smooth": 0.22,
                    "symbolSize": 9,
                    "lineStyle": {"width": 3, "type": "dashed", "color": "#f59e0b"},
                },
            ]
        option = {
            "animationDuration": 650,
            "grid": {"left": 22, "right": 30, "top": 22, "bottom": 24, "containLabel": True},
            "tooltip": {"trigger": "axis", "valueFormatter": "__UNIT__"},
            "xAxis": {
                "type": "category",
                "data": labels,
                "boundaryGap": False,
                "axisLabel": {"color": "#667085"},
                "axisLine": {"lineStyle": {"color": "#cbd5e1"}},
            },
            "yAxis": {
                "type": "value",
                "name": unit,
                "nameTextStyle": {"color": "#667085"},
                "axisLabel": {"color": "#667085"},
                "splitLine": {"lineStyle": {"color": "#e8edf4"}},
            },
            "series": series,
        }
    elif resolved_type == "donut":
        palette = ["#2563eb", "#0ea5b7", "#7c3aed", "#f59e0b", "#16a34a", "#e11d48"]
        pie_values = [
            {
                **value,
                "itemStyle": {"color": palette[index % len(palette)]},
            }
            for index, value in enumerate(values)
        ]
        option = {
            "animationDuration": 650,
            "tooltip": {"trigger": "item", "formatter": "{b}<br/>{c} " + unit + " ({d}%)"},
            "legend": {"type": "scroll", "bottom": 0, "textStyle": {"color": "#526173"}},
            "series": [
                {
                    "type": "pie",
                    "radius": ["44%", "70%"],
                    "center": ["50%", "44%"],
                    "avoidLabelOverlap": True,
                    "label": {"formatter": "{b}\n{d}%", "color": "#334155"},
                    "data": pie_values,
                }
            ],
        }
    elif resolved_type == "scatter":
        scatter_values = [
            {
                "name": row["label"],
                "value": [row["value"], row["secondary"]],
                "display": row["display"],
                "property": row["property"],
                "itemStyle": {"color": property_color(str(row["property"]))},
            }
            for row in rows
        ]
        option = {
            "animationDuration": 650,
            "grid": {"left": 24, "right": 28, "top": 24, "bottom": 25, "containLabel": True},
            "tooltip": {"trigger": "item"},
            "xAxis": {
                "type": "value",
                "name": f"{x_axis}（{x_unit}）",
                "axisLabel": {"color": "#667085"},
                "splitLine": {"lineStyle": {"color": "#e8edf4"}},
            },
            "yAxis": {
                "type": "value",
                "name": f"{y_axis}（{y_unit}）",
                "axisLabel": {"color": "#667085"},
                "splitLine": {"lineStyle": {"color": "#e8edf4"}},
            },
            "series": [
                {
                    "type": "scatter",
                    "data": scatter_values,
                    "symbolSize": 15,
                    "label": {
                        "show": len(rows) <= 6,
                        "position": "top",
                        "formatter": "{b}",
                        "color": "#334155",
                    },
                }
            ],
        }
    else:
        lower_values = [float(row["value"]) for row in rows]
        spans = [float(row["secondary"]) - float(row["value"]) for row in rows]
        option = {
            "animationDuration": 650,
            "grid": {"left": 18, "right": 30, "top": 18, "bottom": 20, "containLabel": True},
            "tooltip": {"trigger": "axis", "axisPointer": {"type": "shadow"}},
            "xAxis": {
                "type": "value",
                "name": unit,
                "axisLabel": {"color": "#667085"},
                "splitLine": {"lineStyle": {"color": "#e8edf4"}},
            },
            "yAxis": {
                "type": "category",
                "inverse": True,
                "data": labels,
                "axisLabel": {"color": "#334155"},
                "axisTick": {"show": False},
                "axisLine": {"show": False},
            },
            "series": [
                {
                    "name": "下限",
                    "type": "bar",
                    "stack": "interval",
                    "data": lower_values,
                    "itemStyle": {"color": "transparent"},
                    "emphasis": {"disabled": True},
                },
                {
                    "name": "区间",
                    "type": "bar",
                    "stack": "interval",
                    "data": spans,
                    "barMaxWidth": 25,
                    "itemStyle": {"color": "#0ea5b7", "borderRadius": 5},
                },
            ],
        }

    chart_id = f"industry-chart-{chart_index}"
    purpose_label = {
        "trend": "趋势",
        "comparison": "比较",
        "composition": "构成",
        "relationship": "关系",
        "range": "区间",
    }[purpose]
    type_label = {
        "line": "折线图",
        "area": "面积图",
        "bar": "条形图",
        "donut": "环形图",
        "scatter": "散点图",
        "range": "区间图",
    }[resolved_type]
    unit_meta = f"{x_unit} / {y_unit}" if purpose == "relationship" else unit
    meta = "".join(
        f'<span>{inline_markdown(label)}：{inline_markdown(value)}</span>'
        for label, value in (
            ("表达", purpose_label),
            ("图形", type_label),
            ("单位", unit_meta),
            ("时期", period),
            ("地域", geography),
            ("性质", chart_property),
        )
    )
    if purpose == "relationship":
        table_header = (
            f"<th>对象</th><th>{inline_markdown(x_axis)}（{inline_markdown(x_unit)}）</th>"
            f"<th>{inline_markdown(y_axis)}（{inline_markdown(y_unit)}）</th><th>性质</th>"
        )
        table_rows = "".join(
            "<tr>"
            f"<td>{inline_markdown(str(row['label']))}</td>"
            f"<td>{inline_markdown(str(row['value']))}</td>"
            f"<td>{inline_markdown(str(row['secondary']))}</td>"
            f"<td><span class=\"data-kind data-kind-{row['property']}\">{inline_markdown(str(row['property']))}</span></td>"
            "</tr>"
            for row in rows
        )
    elif purpose == "range":
        table_header = "<th>对象</th><th>区间</th><th>性质</th>"
        table_rows = "".join(
            "<tr>"
            f"<td>{inline_markdown(str(row['label']))}</td>"
            f"<td>{inline_markdown(str(row['display']))}</td>"
            f"<td><span class=\"data-kind data-kind-{row['property']}\">{inline_markdown(str(row['property']))}</span></td>"
            "</tr>"
            for row in rows
        )
    else:
        table_header = "<th>项目</th><th>数值</th><th>性质</th>"
        table_rows = "".join(
            "<tr>"
            f"<td>{inline_markdown(str(row['label']))}</td>"
            f"<td>{inline_markdown(str(row['display']))}</td>"
            f"<td><span class=\"data-kind data-kind-{row['property']}\">{inline_markdown(str(row['property']))}</span></td>"
            "</tr>"
            for row in rows
        )
    figure = (
        f'<figure class="chart-figure echart-figure" data-purpose="{purpose}" data-chart-type="{resolved_type}">'
        f'<figcaption><strong>{inline_markdown(title)}</strong></figcaption>'
        f'<div class="visual-meta">{meta}</div>'
        f'<div id="{chart_id}" class="echart-canvas" role="img" aria-label="{html.escape(title, quote=True)}"></div>'
        '<details class="chart-data"><summary>查看图表数据</summary>'
        f'<div class="table-wrap"><table><thead><tr>{table_header}</tr></thead>'
        f'<tbody>{table_rows}</tbody></table></div></details>'
        f'<p class="chart-source">来源：{inline_markdown(source)}</p>'
        '</figure>'
    )
    return figure, {
        "id": chart_id,
        "option": option,
        "unit": unit_meta,
        "purpose": purpose,
        "resolved_type": resolved_type,
    }


def render_visual(lines: Sequence[str]) -> str:
    """Render qualitative structures and compact snapshots with HTML and CSS."""

    settings: Dict[str, str] = {}
    rows: List[List[str]] = []
    for raw_line in lines:
        line = raw_line.strip()
        if not line:
            continue
        key_match = re.match(r"^(title|type|source)\s*:\s*(.+)$", line, re.IGNORECASE)
        if key_match:
            settings[key_match.group(1).lower()] = key_match.group(2).strip()
            continue
        item_match = re.match(r"^item\s*:\s*(.+)$", line, re.IGNORECASE)
        if not item_match:
            raise ReportError(
                "结构图数据行必须以 item: 开头；不要写表头、字段名或不带 item: 的数据行："
                f"{line}"
            )
        cells = [cell.strip() for cell in item_match.group(1).split("|")]
        if len(cells) < 2 or len(cells) > 5 or any(not cell for cell in cells):
            raise ReportError(f"结构图数据格式不正确：{line}")
        rows.append(cells)

    title = settings.get("title", "")
    visual_type = settings.get("type", "").lower()
    source = settings.get("source", "")
    if not title:
        raise ReportError("结构图缺少 title。")
    allowed_types = ("chain", "timeline", "matrix", "comparison", "snapshot")
    if visual_type not in allowed_types:
        raise ReportError(
            "结构图 type 只支持 chain、timeline、matrix、comparison 或 snapshot。"
        )
    if visual_type == "snapshot":
        if len(rows) < 2 or len(rows) > 5:
            raise ReportError("行业速览必须包含 2—5 个有实质内容的项目。")
    elif len(rows) < 2 or len(rows) > 8:
        raise ReportError("结构图必须包含 2—8 个有实质内容的节点。")
    if not source or not CITATION_RE.search(source):
        raise ReportError("结构图必须通过 source: [n] 标明来源。")

    if visual_type == "snapshot":
        source_citations = set(CITATION_RE.findall(source))
        item_citations: set[str] = set()
        for cells in rows:
            if len(cells) != 3:
                raise ReportError(
                    "行业速览每项必须写成“简短名称 | 数值或状态 | 业务含义及引用”。"
                )
            if any(re.fullmatch(r"\s*[<{].+[>}]\s*", cell) for cell in cells):
                raise ReportError("行业速览不能保留模板占位内容。")
            citations = set(CITATION_RE.findall(" | ".join(cells)))
            if not citations:
                raise ReportError("行业速览中的每一项都必须直接给出引用。")
            item_citations.update(citations)
        if not item_citations.issubset(source_citations):
            raise ReportError("行业速览的 source 必须覆盖每一项使用的引用。")

    cards: List[str] = []
    for row_index, cells in enumerate(rows, 1):
        if visual_type == "snapshot":
            cards.append(
                '<div class="visual-card snapshot-card">'
                f'<span class="snapshot-label">{inline_markdown(cells[0])}</span>'
                f'<strong class="snapshot-value">{inline_markdown(cells[1])}</strong>'
                f'<p>{inline_markdown(cells[2])}</p>'
                "</div>"
            )
        else:
            heading = inline_markdown(cells[0])
            details = "".join(f"<p>{inline_markdown(cell)}</p>" for cell in cells[1:])
            badge = f'<span class="visual-index">{row_index:02d}</span>'
            cards.append(
                f'<div class="visual-card">{badge}<strong>{heading}</strong>{details}</div>'
            )
    layout = {
        "timeline": "horizontal" if len(rows) <= 4 else "vertical",
        "chain": "linear" if len(rows) <= 4 else "wrapped",
        "comparison": "compact" if len(rows) <= 4 else "dense",
        "matrix": "quad" if len(rows) == 4 else "flex",
        "snapshot": {
            2: "pair",
            3: "trio",
            4: "quad",
            5: "split",
        }[len(rows)],
    }[visual_type]
    return (
        f'<figure class="structure-figure visual-{visual_type}" data-layout="{layout}">'
        f'<figcaption><strong>{inline_markdown(title)}</strong></figcaption>'
        f'<div class="visual-grid">{"".join(cards)}</div>'
        f'<p class="chart-source">来源：{inline_markdown(source)}</p>'
        '</figure>'
    )


def heading_map(lines: Sequence[str], reference_heading_index: int) -> Dict[int, str]:
    """Assign stable, presentation-only anchors to report headings."""

    result: Dict[int, str] = {}
    section = 0
    subsection = 0
    for index, line in enumerate(lines):
        match = re.match(r"^(#{1,6})\s+(.+)$", line)
        if not match:
            continue
        level = len(match.group(1))
        if index == reference_heading_index:
            result[index] = "references"
        elif level == 2:
            section += 1
            subsection = 0
            result[index] = f"section-{section}"
        elif level == 3:
            subsection += 1
            result[index] = f"section-{section}-{subsection}"
    return result


def render_toc(lines: Sequence[str], anchors: Dict[int, str]) -> str:
    entries: List[str] = []
    for index, line in enumerate(lines):
        match = re.match(r"^(#{2,3})\s+(.+)$", line)
        if not match or index not in anchors:
            continue
        level = len(match.group(1))
        title = match.group(2).strip()
        class_name = "toc-section" if level == 2 else "toc-subsection"
        entries.append(
            f'<a class="{class_name}" href="#{anchors[index]}">{inline_markdown(title)}</a>'
        )
    return "\n".join(entries)


def render_markdown(
    lines: Sequence[str], reference_heading_index: int, anchors: Dict[int, str]
) -> Tuple[str, List[Dict[str, object]]]:
    output: List[str] = []
    chart_specs: List[Dict[str, object]] = []
    paragraph: List[str] = []
    index = 0
    in_code = False
    code_language = ""
    code_lines: List[str] = []
    list_type = ""
    list_class = ""
    current_section = ""
    first_paragraph = True
    has_section_heading = False
    title_suppressed = False

    def flush_paragraph() -> None:
        nonlocal first_paragraph
        if paragraph:
            class_name = (
                ' class="report-intro"'
                if first_paragraph and not has_section_heading
                else ""
            )
            output.append(f"<p{class_name}>{inline_markdown(' '.join(paragraph))}</p>")
            paragraph.clear()
            first_paragraph = False

    def close_list() -> None:
        nonlocal list_type, list_class
        if list_type:
            output.append(f"</{list_type}>")
            list_type = ""
            list_class = ""

    while index < len(lines):
        line = lines[index]
        stripped = line.strip()

        if in_code:
            if stripped.startswith("```"):
                if code_language.lower() == "chart":
                    figure, spec = render_chart(code_lines, len(chart_specs) + 1)
                    output.append(figure)
                    chart_specs.append(spec)
                elif code_language.lower() == "visual":
                    output.append(render_visual(code_lines))
                elif looks_like_visual_dsl(code_lines):
                    raise ReportError(
                        "疑似图表或结构图的数据块缺少 chart/visual 围栏标签，不能作为原始代码交付。"
                    )
                else:
                    language_class = f' class="language-{html.escape(code_language, quote=True)}"' if code_language else ""
                    output.append(
                        f"<pre><code{language_class}>{html.escape(chr(10).join(code_lines), quote=False)}</code></pre>"
                    )
                in_code = False
                code_language = ""
                code_lines.clear()
            else:
                code_lines.append(line)
            index += 1
            continue

        if stripped.startswith("```"):
            flush_paragraph()
            close_list()
            in_code = True
            code_language = stripped[3:].strip()
            index += 1
            continue

        if not stripped:
            flush_paragraph()
            if list_class == "key-findings":
                next_index = index + 1
                while next_index < len(lines) and not lines[next_index].strip():
                    next_index += 1
                if next_index < len(lines) and re.match(
                    r"^\s*\d+[.)]\s+(.+)$", lines[next_index]
                ):
                    index += 1
                    continue
            close_list()
            index += 1
            continue

        if (
            index + 1 < len(lines)
            and "|" in line
            and TABLE_DIVIDER_RE.match(lines[index + 1])
        ):
            flush_paragraph()
            close_list()
            table_rows: List[str] = []
            row_index = index + 2
            while row_index < len(lines) and "|" in lines[row_index] and lines[row_index].strip():
                table_rows.append(lines[row_index])
                row_index += 1
            prominent = any(keyword in current_section for keyword in ("数据", "规模", "指标", "比较", "对比"))
            output.append(render_table(line, table_rows, prominent=prominent))
            index = row_index
            continue

        heading = re.match(r"^(#{1,6})\s+(.+)$", line)
        if heading:
            flush_paragraph()
            close_list()
            level = len(heading.group(1))
            title = heading.group(2).strip()
            if level == 1 and not title_suppressed:
                title_suppressed = True
                index += 1
                continue
            if level == 2:
                current_section = re.sub(r"[*_`]", "", title)
                has_section_heading = True
            anchor = anchors.get(index, "")
            anchor_attribute = f' id="{anchor}"' if anchor else ""
            if index == reference_heading_index:
                output.append(
                    f'<h{level} id="references" class="references-title">{inline_markdown(title)}</h{level}>'
                )
            else:
                class_name = ' class="section-title"' if level == 2 else ""
                output.append(
                    f"<h{level}{anchor_attribute}{class_name}>{inline_markdown(title)}</h{level}>"
                )
            index += 1
            continue

        reference = REFERENCE_RE.match(line) if index > reference_heading_index else None
        if reference:
            flush_paragraph()
            close_list()
            number = int(reference.group(1))
            title = html.escape(reference.group(2).strip(), quote=False)
            url = html.escape(reference.group(3).strip(), quote=True)
            details = html.escape((reference.group(4) or "").strip(), quote=False)
            suffix = f" — {details}" if details else ""
            output.append(
                f'<p class="reference" id="ref-{number}"><span>{number}.</span> '
                f'<a href="{url}">{title}</a>{suffix} <a class="back" href="#references">↩</a></p>'
            )
            index += 1
            continue

        unordered = re.match(r"^\s*[-*+]\s+(.+)$", line)
        ordered = re.match(r"^\s*\d+[.)]\s+(.+)$", line)
        if unordered or ordered:
            flush_paragraph()
            target_type = "ul" if unordered else "ol"
            target_class = (
                "key-findings"
                if ordered and any(keyword in current_section for keyword in ("核心结论", "执行摘要"))
                else ""
            )
            if list_type != target_type or list_class != target_class:
                close_list()
                class_attribute = f' class="{target_class}"' if target_class else ""
                output.append(f"<{target_type}{class_attribute}>")
                list_type = target_type
                list_class = target_class
            content = (unordered or ordered).group(1)
            output.append(f"<li>{inline_markdown(content)}</li>")
            index += 1
            continue

        if stripped.startswith(">"):
            flush_paragraph()
            close_list()
            output.append(f"<blockquote>{inline_markdown(stripped.lstrip('>').strip())}</blockquote>")
            index += 1
            continue

        if re.match(r"^\s*(?:-{3,}|\*{3,}|_{3,})\s*$", line):
            flush_paragraph()
            close_list()
            output.append("<hr>")
            index += 1
            continue

        close_list()
        paragraph.append(stripped)
        index += 1

    if in_code:
        raise ReportError("代码块没有结束标记。")
    flush_paragraph()
    close_list()
    return "\n".join(output), chart_specs


def load_css() -> str:
    css_path = Path(__file__).resolve().parent.parent / "assets" / "report-template" / "report.css"
    try:
        return css_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ReportError(f"无法读取报告样式：{exc}") from exc


def load_echarts() -> str:
    script_path = Path(__file__).resolve().parent.parent / "assets" / "report-template" / "echarts.min.js"
    try:
        script = script_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ReportError(f"无法读取图表组件：{exc}") from exc
    return re.sub(r"</script", r"<\\/script", script, flags=re.IGNORECASE)


def chart_bootstrap(chart_specs: Sequence[Dict[str, object]]) -> str:
    if not chart_specs:
        return ""
    payload = json.dumps(chart_specs, ensure_ascii=False, separators=(",", ":"))
    payload = payload.replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")
    return (
        "<script>\n"
        "const chartSpecs=" + payload + ";\n"
        "const charts=[];\n"
        "chartSpecs.forEach(spec=>{\n"
        "  const el=document.getElementById(spec.id); if(!el) return;\n"
        "  if(spec.option?.tooltip?.valueFormatter==='__UNIT__'){spec.option.tooltip.valueFormatter=(value)=>`${value} ${spec.unit}`;}\n"
        "  const chart=echarts.init(el,null,{renderer:'canvas'}); chart.setOption(spec.option); charts.push(chart);\n"
        "});\n"
        "let resizeTimer; window.addEventListener('resize',()=>{clearTimeout(resizeTimer);resizeTimer=setTimeout(()=>charts.forEach(chart=>chart.resize()),120);});\n"
        "</script>\n"
    )


def report_title(lines: Sequence[str], override: Optional[str]) -> str:
    if override and override.strip():
        return override.strip()
    for line in lines:
        match = re.match(r"^#\s+(.+)$", line)
        if match:
            return re.sub(r"[*_`]", "", match.group(1)).strip()
    return "行业研究报告"


def build_html(markdown: str, title_override: Optional[str] = None) -> str:
    lines, reference_heading_index, _ = validate_report(markdown)
    title = report_title(lines, title_override)
    anchors = heading_map(lines, reference_heading_index)
    toc = render_toc(lines, anchors)
    body, chart_specs = render_markdown(lines, reference_heading_index, anchors)
    css = load_css()
    chart_runtime = ""
    if chart_specs:
        chart_runtime = f"<script>\n{load_echarts()}\n</script>\n{chart_bootstrap(chart_specs)}"
    return (
        "<!-- Generated by Trae Work -->\n"
        "<!doctype html>\n"
        '<html lang="zh-CN">\n<head>\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        f"<title>{html.escape(title, quote=False)}</title>\n"
        f"<style>\n{css}\n</style>\n</head>\n<body>\n"
        '<header class="report-hero">\n'
        '<div class="hero-inner">\n'
        '<p class="hero-kicker">INDUSTRY RESEARCH · 行业研究</p>\n'
        f'<h1>{html.escape(title, quote=False)}</h1>\n'
        '<div class="hero-rule"><span></span><span></span><span></span></div>\n'
        '</div>\n</header>\n'
        '<div class="report-layout">\n'
        '<aside class="report-toc"><p>报告目录</p><nav>\n'
        f'{toc}\n</nav></aside>\n'
        f'<main class="report"><article>\n{body}\n</article>'
        '<footer class="report-footer">公开资料研究 · 关键事实来源见参考资料</footer>'
        '</main>\n</div>\n'
        f'{chart_runtime}'
        "</body>\n</html>\n"
    )


def publish(input_path: Path, output_path: Path, title: Optional[str] = None) -> None:
    try:
        markdown = input_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ReportError(f"无法读取报告：{exc}") from exc
    result = build_html(markdown, title)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    temporary_name = ""
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=str(output_path.parent),
            prefix=f".{output_path.name}.",
            suffix=".tmp",
            delete=False,
        ) as temporary:
            temporary.write(result)
            temporary_name = temporary.name
        os.replace(temporary_name, output_path)
    finally:
        if temporary_name and os.path.exists(temporary_name):
            os.unlink(temporary_name)


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="检查报告引用并生成可离线阅读的 HTML。")
    parser.add_argument("--input", required=True, type=Path, help="report.md 路径")
    destination = parser.add_mutually_exclusive_group(required=True)
    destination.add_argument("--output", type=Path, help="report.html 路径")
    destination.add_argument("--check-only", action="store_true", help="只检查，不生成 HTML")
    parser.add_argument("--title", help="可选的 HTML 页面标题")
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)
    try:
        if args.check_only:
            try:
                markdown = args.input.read_text(encoding="utf-8")
            except OSError as exc:
                raise ReportError(f"无法读取报告：{exc}") from exc
            build_html(markdown, args.title)
        else:
            publish(args.input, args.output, args.title)
    except ReportError as exc:
        if args.check_only:
            print(f"检查失败：{exc}", file=sys.stderr)
        else:
            print(f"HTML 未生成：生成前校验未通过：{exc}", file=sys.stderr)
        return 1
    if args.check_only:
        print(f"检查通过：{args.input}")
    else:
        print(f"已生成：{args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
