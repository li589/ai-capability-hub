#!/usr/bin/env python3
"""Finalize one assembled industry report in a single deterministic command."""

from __future__ import annotations

import argparse
from pathlib import Path
import re
import sys

from apply_editorial import EditorialError, merge_editorial
from extract_context import build_report_context
from normalize_references import NormalizeError, normalize
from publish import ReportError, publish


HTML_DECLARATION = "<!doctype html>"
TITLE_RE = re.compile(r"^#\s+(.+?)\s*$", re.MULTILINE)
INVALID_FILENAME_RE = re.compile(r'[\\/:*?"<>|\x00-\x1f]')
GENERIC_REPORT_TITLES = {"报告", "研究报告", "行业研究报告"}
MAX_ARTIFACT_STEM_LENGTH = 80


def artifact_stem(markdown: str) -> str:
    """Derive a portable, user-meaningful artifact name from the report title."""

    match = TITLE_RE.search(markdown)
    if not match:
        raise ReportError("正式报告缺少一级标题，无法生成有意义的产物文件名。")
    title = re.sub(r"\s+", " ", match.group(1)).strip()
    if title in GENERIC_REPORT_TITLES:
        raise ReportError("报告标题必须包含用户研究主题，不能只写“行业研究报告”。")
    title = INVALID_FILENAME_RE.sub("-", title)
    title = re.sub(r"\s*-\s*", "-", title)
    title = re.sub(r"-{2,}", "-", title).strip(" .-_")
    title = title[:MAX_ARTIFACT_STEM_LENGTH].rstrip(" .-_")
    if not title:
        raise ReportError("报告标题不能生成有效的产物文件名。")
    return title


def write_review(
    path: Path,
    status: str,
    detail: str,
    html_ready: bool,
    context_ready: bool,
    markdown_name: str = "",
    html_name: str = "",
) -> None:
    path.write_text(
        "# 核查结果\n\n"
        f"## 结论\n{status}\n\n"
        f"## 核查摘要\n{detail}\n\n"
        "## 业务摘要\n"
        + (
            "报告已完成整理，主要判断、专题正文和引用已进入正式报告。"
            if html_ready
            else "当前报告未能形成可交付的 HTML，已确认内容仍保留在专题稿中。"
        )
        + "\n\n"
        f"## HTML 交付\n{'已生成并验证' if html_ready else '未生成'}\n\n"
        "## 交付文件\n"
        + (
            f"Markdown：{markdown_name}\nHTML：{html_name}"
            if markdown_name and html_name
            else "尚未生成可交付文件名。"
        )
        + "\n\n"
        f"## 摘要上下文\n{'已生成' if context_ready else '未生成'}\n",
        encoding="utf-8",
    )


def finalize(work_dir: Path) -> str:
    draft_path = work_dir / "draft.md"
    editorial_path = work_dir / "editorial.md"
    delivery_path = work_dir / "delivery-context.md"
    review_path = work_dir / "review.md"
    report_path: Path | None = None
    html_path: Path | None = None

    status = "PASS"
    detail = "专题正文、引用、图表和 HTML 已完成一次确定性检查。"
    html_ready = False
    context_ready = False

    try:
        draft = draft_path.read_text(encoding="utf-8")
        candidate = draft
        if editorial_path.is_file() and editorial_path.stat().st_size:
            try:
                candidate = merge_editorial(
                    draft, editorial_path.read_text(encoding="utf-8")
                )
            except (OSError, EditorialError) as exc:
                status = "PASS_WITH_LIMITS"
                detail = f"局部编辑未能安全合并，已保留确定性组装稿：{exc}"
        else:
            status = "PASS_WITH_LIMITS"
            detail = "未取得局部编辑内容，已保留确定性组装稿。"

        normalized, _ = normalize(candidate)
        stem = artifact_stem(normalized)
        report_path = work_dir / f"{stem}.md"
        html_path = work_dir / f"{stem}.html"
        report_path.write_text(normalized, encoding="utf-8")
        publish(report_path, html_path)
        html_text = html_path.read_text(encoding="utf-8")
        if not html_text.strip() or HTML_DECLARATION not in html_text.lower():
            raise ReportError("HTML 文件为空或缺少文档声明。")
        html_ready = True

        delivery = build_report_context(
            work_dir,
            "delivery",
            source_path=report_path,
            html_path=html_path,
        )
        delivery_path.write_text(delivery.rstrip() + "\n", encoding="utf-8")
        context_ready = bool(delivery.strip())
        if not context_ready:
            raise ReportError("最终交付上下文为空。")
    except (OSError, UnicodeError, ValueError, NormalizeError, ReportError) as exc:
        status = "BLOCKED"
        detail = str(exc)
        write_review(
            review_path,
            status,
            detail,
            html_ready=html_ready,
            context_ready=context_ready,
            markdown_name=report_path.name if report_path else "",
            html_name=html_path.name if html_path else "",
        )
        raise

    write_review(
        review_path,
        status,
        detail,
        html_ready=html_ready,
        context_ready=context_ready,
        markdown_name=report_path.name if report_path else "",
        html_name=html_path.name if html_path else "",
    )
    return status


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--work-dir", required=True, type=Path)
    args = parser.parse_args()
    try:
        status = finalize(args.work_dir)
    except (OSError, UnicodeError, ValueError, NormalizeError, ReportError) as exc:
        print(f"最终报告生成失败：{exc}", file=sys.stderr)
        return 1
    print("最终报告已生成。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
