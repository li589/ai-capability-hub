#!/usr/bin/env python3
"""Assemble researched notes into one Markdown draft.

The script orders, copies and renumbers researched content and builds a conservative
overview fallback from existing conclusions. It does not search, add facts or decide
whether a claim is true.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
import re
import sys
from typing import Dict, List, Optional, Sequence, Tuple
from urllib.parse import urlparse


REFERENCE_HEADING_RE = re.compile(r"^##\s+(参考资料|References)\s*$", re.IGNORECASE)
REFERENCE_RE = re.compile(
    r"^\s*(\d+)\.\s+\[([^\]]+)\]\((https?://[^)\s]+)\)\s*[—-]\s*(.+?)\s*$"
)
CITATION_RE = re.compile(r"(?<!!)\[(\d+)\]")
INSUFFICIENT_RE = re.compile(r"\A\s*INSUFFICIENT\s*[：:]\s*(.+?)\s*(?:\n|\Z)", re.IGNORECASE)
BOUNDARY_LINE_RE = re.compile(r"^\s*>\s*资料边界\s*[：:]\s*(.+?)\s*$")
WEAK_MARKER_RE = re.compile(
    r"(?:未直接打开|间接引用|仅供参考|口径待确认|个人作者|个人账号|"
    r"普通账号|自媒体|论坛用户|股吧|无署名|来源不明|聚合转载|营销软文|\bUGC\b)",
    re.IGNORECASE,
)
GATEWAY_MARKER_RE = re.compile(
    r"(?:文件发布(?:页)?|政策列表|新闻索引|首页|栏目页)",
    re.IGNORECASE,
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
INTERNAL_RESEARCH_PROCESS_RE = re.compile(
    r"(?:规划候选|规划分配|本轮(?:已)?打开(?:的)?页面|"
    r"本轮(?:两次)?定向搜索|本次搜索(?:中)?|"
    r"本步骤(?:未|没有)取得|按规则舍弃|不纳入本稿)"
)
UNVERIFIED_DOCUMENT_HOSTS = (
    "docin.com",
    "doc88.com",
    "wenku.baidu.com",
    "book118.com",
)
MAX_NOTE_CHARACTERS = 40_000


class AssembleError(ValueError):
    """Raised when notes cannot be assembled without losing traceability."""


@dataclass(frozen=True)
class SectionSpec:
    key: str
    title: str
    aliases: Tuple[str, ...]
    keywords: Tuple[str, ...]


@dataclass
class Reference:
    number: int
    title: str
    url: str
    details: str


@dataclass
class Chapter:
    spec: SectionSpec
    path: Path
    body: str
    conclusion: str
    references: List[Reference]
    limited: bool = False


SECTION_SPECS = (
    SectionSpec(
        "market",
        "市场规模",
        ("market", "market-size", "市场", "市场规模", "市场规模与预测"),
        ("市场规模", "规模测算"),
    ),
    SectionSpec(
        "chain",
        "产业链与关键瓶颈",
        ("chain", "industry-chain", "产业链", "产业链结构"),
        ("产业链", "价值链", "供应链"),
    ),
    SectionSpec(
        "competition",
        "竞争格局",
        ("competition", "competitive-landscape", "竞争", "竞争格局"),
        ("竞争格局", "市场结构"),
    ),
    SectionSpec(
        "companies",
        "重点企业",
        ("companies", "company", "key-enterprises", "企业", "重点企业"),
        ("重点企业", "企业画像", "公司比较"),
    ),
    SectionSpec(
        "macro",
        "宏观与政策环境",
        ("macro", "macro-policy", "宏观", "宏观与政策环境", "宏观政策"),
        ("宏观", "政策", "监管"),
    ),
    SectionSpec(
        "trends",
        "趋势、机会与风险",
        ("trends", "trend", "trend-opportunity-risk", "趋势", "趋势机会风险", "趋势机会与风险"),
        ("趋势", "机会", "风险"),
    ),
)


def is_unverified_document_host(url: str) -> bool:
    parsed = urlparse(url)
    hostname = (parsed.hostname or "").lower()
    return any(
        hostname == host or hostname.endswith(f".{host}")
        for host in UNVERIFIED_DOCUMENT_HOSTS
    )


def has_platform_only_publisher(details: str) -> bool:
    """Reject a hosting-platform label when no content publisher is named."""

    without_date = DATE_SUFFIX_RE.sub("", details).strip()
    return bool(PLATFORM_ONLY_PUBLISHER_RE.fullmatch(without_date))


def locate_notes(work_dir: Path) -> List[Tuple[SectionSpec, Path]]:
    notes_dir = work_dir / "notes"
    if not notes_dir.is_dir():
        raise AssembleError(f"缺少专题目录：{notes_dir}")
    candidates = sorted(path for path in notes_dir.glob("*.md") if path.is_file())
    if not candidates:
        raise AssembleError("专题目录中没有 Markdown 稿件。")

    located: List[Tuple[SectionSpec, Path]] = []
    used: set[Path] = set()
    for spec in SECTION_SPECS:
        exact = [path for path in candidates if path.stem.lower() in {a.lower() for a in spec.aliases}]
        matches = exact or [
            path
            for path in candidates
            if any(keyword.lower() in path.stem.lower() for keyword in spec.keywords)
        ]
        matches = [path for path in matches if path not in used]
        if len(matches) > 1:
            names = "、".join(path.name for path in matches)
            raise AssembleError(f"{spec.title}存在多份候选稿：{names}")
        if matches:
            located.append((spec, matches[0]))
            used.add(matches[0])
    return located


def split_note(markdown: str, path: Path) -> Tuple[List[str], List[str]]:
    lines = markdown.splitlines()
    indexes = [index for index, line in enumerate(lines) if REFERENCE_HEADING_RE.match(line)]
    if len(indexes) != 1:
        raise AssembleError(f"{path.name} 必须且只能有一个“## 参考资料”章节。")
    index = indexes[0]
    return lines[:index], lines[index + 1 :]


def inspect_references(
    lines: Sequence[str], path: Path
) -> Tuple[List[Reference], List[str]]:
    references: List[Reference] = []
    prohibited_numbers: List[int] = []
    errors: List[str] = []
    for line in lines:
        if not line.strip():
            continue
        match = REFERENCE_RE.match(line)
        if not match:
            errors.append(f"参考资料不是带链接的标准格式：{line.strip()}")
            continue
        reference = Reference(
            number=int(match.group(1)),
            title=match.group(2).strip(),
            url=match.group(3).strip(),
            details=(match.group(4) or "").strip(),
        )
        label = f"{reference.title} {reference.details}"
        if (
            WEAK_MARKER_RE.search(label)
            or GATEWAY_MARKER_RE.search(label)
            or has_platform_only_publisher(reference.details)
            or is_unverified_document_host(reference.url)
        ):
            prohibited_numbers.append(reference.number)
        references.append(reference)

    if prohibited_numbers:
        labels = "、".join(f"[{number}]" for number in prohibited_numbers)
        errors.append(
            f"参考资料 {labels} 属于个人内容、来源身份不明、入口页或文档预览来源，不能进入最终报告。"
        )

    if not references:
        errors.append("没有有效参考资料。")
    expected = list(range(1, len(references) + 1))
    actual = [reference.number for reference in references]
    if references and actual != expected:
        errors.append(
            "参考资料编号必须从 1 连续排列；"
            f"当前编号为 {actual}。"
        )
    return references, errors


def parse_references(lines: Sequence[str], path: Path) -> List[Reference]:
    references, errors = inspect_references(lines, path)
    if errors:
        details = "\n".join(f"- {path.name}：{error}" for error in errors)
        raise AssembleError(details)
    return references


def remove_note_title(lines: Sequence[str]) -> List[str]:
    output = list(lines)
    while output and not output[0].strip():
        output.pop(0)
    if output and re.match(r"^#\s+", output[0]):
        output.pop(0)
    while output and not output[0].strip():
        output.pop(0)
    return output


def remove_internal_wrapper_headings(lines: Sequence[str]) -> List[str]:
    """Remove note-only headings while preserving every line of report content."""

    wrappers = {"核心结论", "核心判断", "结论摘要", "正文", "详细分析"}
    output: List[str] = []
    in_fence = False
    for line in lines:
        if line.strip().startswith("```"):
            in_fence = not in_fence
            output.append(line)
            continue
        match = None if in_fence else re.match(r"^#{2,5}\s+(.+?)\s*$", line)
        if match:
            heading = re.sub(r"[：:。.!！?？]$", "", match.group(1).strip())
            if heading in wrappers:
                continue
        output.append(line)
    return output


def demote_headings(lines: Sequence[str]) -> List[str]:
    output: List[str] = []
    in_fence = False
    for line in lines:
        if line.strip().startswith("```"):
            in_fence = not in_fence
            output.append(line)
            continue
        match = None if in_fence else re.match(r"^(#{2,5})(\s+.+)$", line)
        if match:
            output.append("#" + match.group(1) + match.group(2))
        else:
            output.append(line)
    return output


def normalize_boundary_text(value: str) -> str:
    """Normalize harmless punctuation so an INSUFFICIENT reason is not repeated."""

    return re.sub(r"[\s。；;，,！？!?]+$", "", value.strip())


def collect_note_errors(path: Path) -> List[str]:
    """Return every deterministic note error that can be found in one pass."""
    markdown = path.read_text(encoding="utf-8")
    errors: List[str] = []
    if len(markdown) > MAX_NOTE_CHARACTERS:
        errors.append("长度异常，疑似包含重复生成内容，不能进入最终报告。")

    insufficient = INSUFFICIENT_RE.match(markdown)
    content = markdown[insufficient.end() :] if insufficient else markdown
    lines = content.lstrip().splitlines()
    reference_indexes = [
        index for index, line in enumerate(lines) if REFERENCE_HEADING_RE.match(line)
    ]

    if insufficient:
        if len(reference_indexes) > 1:
            errors.append("最多只能有一个“## 参考资料”章节。")
        if reference_indexes:
            index = reference_indexes[0]
            body_lines = lines[:index]
            reference_lines = lines[index + 1 :]
        else:
            body_lines = lines
            reference_lines = []
    else:
        if len(reference_indexes) != 1:
            errors.append("必须且只能有一个“## 参考资料”章节。")
        if reference_indexes:
            index = reference_indexes[0]
            body_lines = lines[:index]
            reference_lines = lines[index + 1 :]
        else:
            body_lines = lines
            reference_lines = []

    references: List[Reference] = []
    if reference_lines:
        references, reference_errors = inspect_references(reference_lines, path)
        errors.extend(reference_errors)
    elif reference_indexes:
        errors.append("没有有效参考资料。")

    body_lines = remove_note_title(body_lines)
    body = "\n".join(body_lines).strip()
    if not insufficient and not body:
        errors.append("没有实质正文。")
    if INTERNAL_RESEARCH_PROCESS_RE.search(body):
        errors.append(
            "包含规划候选、检索轮次或内部取舍过程；"
            "请改写为用户可理解的业务资料边界。"
        )

    cited = {int(number) for number in CITATION_RE.findall(body)}
    available = {reference.number for reference in references}
    if not insufficient and not cited:
        errors.append("正文没有对应可点击参考资料的引用编号。")

    missing = sorted(cited - available)
    if missing:
        labels = "、".join(f"[{number}]" for number in missing)
        errors.append(f"正文引用没有对应参考资料：{labels}。")

    unused = sorted(available - cited)
    if unused:
        labels = "、".join(f"[{number}]" for number in unused)
        errors.append(f"参考资料未在正文使用：{labels}。")
    return errors


def remap_citations(text: str, mapping: Dict[int, int], path: Path) -> str:
    cited = {int(value) for value in CITATION_RE.findall(text)}
    missing = sorted(cited - set(mapping))
    if missing:
        labels = "、".join(f"[{number}]" for number in missing)
        raise AssembleError(f"{path.name} 的正文引用没有对应参考资料：{labels}")

    def replace(match: re.Match[str]) -> str:
        return f"[{mapping[int(match.group(1))]}]"

    return CITATION_RE.sub(replace, text)


def extract_conclusion(lines: Sequence[str]) -> str:
    candidates: List[str] = []
    in_core = False
    for raw in lines:
        line = raw.strip()
        if re.match(r"^#{2,5}\s+", line):
            heading = re.sub(r"^#{2,5}\s+", "", line)
            in_core = any(word in heading for word in ("核心结论", "核心判断", "结论摘要"))
            continue
        if not line or line.startswith("|") or line.startswith("```"):
            continue
        if in_core:
            candidates.append(re.sub(r"^(?:\d+[.)]|[-*])\s+", "", line))
    if not candidates:
        for raw in lines:
            line = raw.strip()
            if line and not line.startswith(("#", "|", "```")):
                candidates.append(re.sub(r"^(?:\d+[.)]|[-*])\s+", "", line))
                break
    if not candidates:
        return ""
    cited = next((value for value in candidates if CITATION_RE.search(value)), candidates[0])
    # Keep complete sentences instead of cutting a paragraph at an arbitrary
    # character boundary. The 320-character target is soft: the first complete
    # cited sentence is always preserved, even when it is longer.
    sentences = [
        value.strip()
        for value in re.findall(r".*?[。！？!?](?:\[\d+\])*|.+$", cited.strip())
        if value.strip()
    ]
    selected: List[str] = []
    for sentence in sentences:
        if selected and sum(len(value) for value in selected) + len(sentence) > 320:
            if CITATION_RE.search("".join(selected)):
                break
        selected.append(sentence)
        if sum(len(value) for value in selected) >= 320 and CITATION_RE.search(
            "".join(selected)
        ):
            break
    excerpt = "".join(selected).strip() if selected else cited.strip()
    if re.search(r"[。！？!?](?:\[\d+\])+$", excerpt):
        return excerpt
    trailing_citations = re.search(r"((?:\[\d+\])+)$", excerpt)
    if trailing_citations:
        prefix = excerpt[: trailing_citations.start()].rstrip("；;，,。")
        return prefix + "。" + trailing_citations.group(1)
    if not excerpt.endswith(("。", "！", "？", "!", "?")):
        excerpt = excerpt.rstrip("；;，,") + "。"
    return excerpt


def read_chapter(spec: SectionSpec, path: Path) -> Chapter:
    markdown = path.read_text(encoding="utf-8")
    if len(markdown) > MAX_NOTE_CHARACTERS:
        raise AssembleError(
            f"{path.name} 长度异常，疑似包含重复生成内容，不能进入最终报告。"
        )
    insufficient = INSUFFICIENT_RE.match(markdown)
    if insufficient:
        reason = normalize_boundary_text(insufficient.group(1))
        remainder = markdown[insufficient.end() :].lstrip()
        lines = remainder.splitlines()
        reference_indexes = [
            index for index, line in enumerate(lines) if REFERENCE_HEADING_RE.match(line)
        ]
        if len(reference_indexes) > 1:
            raise AssembleError(f"{path.name} 最多只能有一个“## 参考资料”章节。")
        if reference_indexes:
            index = reference_indexes[0]
            body_lines = lines[:index]
            references = parse_references(lines[index + 1 :], path)
        else:
            body_lines = lines
            references = []
        body_lines = remove_internal_wrapper_headings(remove_note_title(body_lines))
        boundary_line = f"> 资料边界：{reason}。"
        reason_key = normalize_boundary_text(reason)
        has_equivalent_boundary = any(
            match and normalize_boundary_text(match.group(1)) == reason_key
            for line in body_lines
            for match in [BOUNDARY_LINE_RE.match(line)]
        )
        if not has_equivalent_boundary:
            if body_lines and body_lines[-1].strip():
                body_lines.append("")
            body_lines.append(boundary_line)
        partial_body = "\n".join(demote_headings(body_lines)).strip()
        if CITATION_RE.search(partial_body) and not references:
            raise AssembleError(f"{path.name} 的局部结论有引用编号，但没有对应参考资料。")
        return Chapter(
            spec=spec,
            path=path,
            body=partial_body,
            conclusion=f"{spec.title}资料有限：{reason}。",
            references=references,
            limited=True,
        )
    body_lines, reference_lines = split_note(markdown, path)
    references = parse_references(reference_lines, path)
    body_lines = remove_internal_wrapper_headings(remove_note_title(body_lines))
    body = "\n".join(body_lines).strip()
    if not body:
        raise AssembleError(f"{path.name} 没有实质正文。")
    if not CITATION_RE.search(body):
        raise AssembleError(f"{path.name} 的正文没有对应可点击参考资料的引用编号。")
    return Chapter(
        spec=spec,
        path=path,
        body="\n".join(demote_headings(body_lines)).strip(),
        conclusion=extract_conclusion(body_lines),
        references=references,
    )


def field_from_files(work_dir: Path, label: str) -> str:
    pattern = re.compile(rf"^-\s*{re.escape(label)}[：:]\s*(.+)$", re.MULTILINE)
    for name in ("research-card.md", "plan.md"):
        path = work_dir / name
        if path.is_file():
            match = pattern.search(path.read_text(encoding="utf-8"))
            if match:
                return match.group(1).strip()
    return ""


def default_title(work_dir: Path) -> str:
    industry = field_from_files(work_dir, "行业定义")
    if industry:
        industry = re.split(r"[，；。]", industry, maxsplit=1)[0].strip()[:36]
        if industry.endswith("研究报告"):
            return industry
        if industry.endswith("行业"):
            return industry + "研究报告"
        return industry + "行业研究报告"
    return "行业研究报告"


def scope_intro(work_dir: Path) -> str:
    geography = field_from_files(work_dir, "地域").rstrip(" \t。；;，,！？!?")
    cutoff = field_from_files(work_dir, "资料截止日").rstrip(" \t。；;，,！？!?")
    parts = []
    if geography:
        parts.append(f"地域为{geography}")
    if cutoff:
        parts.append(f"资料截至{cutoff}")
    if not parts:
        return ""
    intro = "研究范围：" + "；".join(parts) + "。"
    return intro[:120]


def is_substantive_conclusion(conclusion: str) -> bool:
    """Return whether a conclusion is usable as standalone report prose."""

    visible = re.sub(r"\[\d+\]|[*_`#]", "", conclusion.strip())
    visible = re.sub(r"\s+", "", visible)
    return bool(visible) and (len(visible) >= 14 or "资料有限" in visible)


def substantive_conclusions(chapters: Sequence[Chapter]) -> List[str]:
    """Keep distinct, sentence-like conclusions for the draft fallback summary."""

    selected: List[str] = []
    seen: set[str] = set()
    for chapter in chapters:
        if chapter.limited:
            continue
        conclusion = chapter.conclusion.strip()
        if not is_substantive_conclusion(conclusion):
            continue
        visible = re.sub(r"\[\d+\]|[*_`#]", "", conclusion)
        visible = re.sub(r"\s+", "", visible)
        normalized = re.sub(r"[^\w\u4e00-\u9fff]", "", visible).lower()
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        selected.append(conclusion)
    return selected


def overview_entry(work_dir: Path) -> List[str]:
    """Create only the scope entry that the single editorial pass will expand."""

    industry = field_from_files(work_dir, "行业定义") or "本报告所研究行业"
    geography = field_from_files(work_dir, "地域")
    cutoff = field_from_files(work_dir, "资料截止日")
    boundary = f"本报告研究对象为{industry}"
    if geography:
        boundary += f"，地域范围为{geography}"
    if cutoff:
        boundary += f"，资料截至{cutoff}"
    boundary = boundary.rstrip("。") + "。"

    return [boundary]


def assemble(work_dir: Path, output: Path, title: Optional[str], require_full: bool) -> str:
    located = locate_notes(work_dir)
    if require_full and len(located) != len(SECTION_SPECS):
        found = {spec.key for spec, _ in located}
        missing = "、".join(spec.title for spec in SECTION_SPECS if spec.key not in found)
        raise AssembleError(f"完整研究缺少专题稿：{missing}")
    if not located:
        raise AssembleError("没有找到可组装的专题稿。")

    chapters: List[Chapter] = []
    chapter_errors: List[str] = []
    for spec, path in located:
        try:
            note_errors = collect_note_errors(path)
            if note_errors:
                chapter_errors.extend(
                    f"{path.name}：{error}" for error in note_errors
                )
                continue
            chapters.append(read_chapter(spec, path))
        except (AssembleError, OSError) as exc:
            chapter_errors.append(f"{path.name}：{exc}")
    if chapter_errors:
        details = "\n".join(f"- {error}" for error in chapter_errors)
        raise AssembleError(f"专题预检发现 {len(chapter_errors)} 项阻断问题：\n{details}")
    global_references: List[Reference] = []
    url_to_number: Dict[str, int] = {}
    for chapter in chapters:
        mapping: Dict[int, int] = {}
        for reference in chapter.references:
            if reference.url not in url_to_number:
                url_to_number[reference.url] = len(global_references) + 1
                global_references.append(reference)
            mapping[reference.number] = url_to_number[reference.url]
        chapter.body = remap_citations(chapter.body, mapping, chapter.path)
        chapter.conclusion = remap_citations(chapter.conclusion, mapping, chapter.path)

    conclusions = substantive_conclusions(chapters)
    lines = [f"# {title or default_title(work_dir)}", ""]
    intro = scope_intro(work_dir)
    if intro:
        lines.extend([intro, ""])
    lines.extend(["## 核心结论", ""])
    lines.extend(f"{index}. {conclusion}" for index, conclusion in enumerate(conclusions[:6], 1))

    if require_full:
        lines.extend(["", "## 行业概览", ""])
        lines.extend(overview_entry(work_dir))

    for chapter in chapters:
        lines.extend(["", f"## {chapter.spec.title}", ""])
        if chapter.body:
            lines.append(chapter.body)

    outlook = next(
        (
            chapter.conclusion
            for chapter in chapters
            if chapter.spec.key == "trends"
            and is_substantive_conclusion(chapter.conclusion)
        ),
        conclusions[-1] if conclusions else "",
    )
    lines.extend(["", "## 结论与展望", ""])
    if outlook:
        lines.append(outlook)
    lines.extend(["", "## 参考资料", ""])
    for number, reference in enumerate(global_references, 1):
        details = f" — {reference.details}" if reference.details else ""
        lines.append(f"{number}. [{reference.title}]({reference.url}){details}")

    markdown = "\n".join(lines).rstrip() + "\n"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(markdown, encoding="utf-8")
    return markdown


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--work-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--title")
    parser.add_argument("--require-full", action="store_true")
    args = parser.parse_args(argv)
    try:
        assemble(args.work_dir, args.output, args.title, args.require_full)
    except (AssembleError, OSError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(f"OK: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
