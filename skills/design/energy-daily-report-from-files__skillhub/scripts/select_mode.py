#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Deterministically suggest the skill execution mode from a short user description."""
from __future__ import annotations

import argparse
import json
import re


def _has(text: str, patterns: list[str]) -> bool:
    return any(re.search(p, text, flags=re.IGNORECASE) for p in patterns)


def select_mode(description: str, *, has_files: bool = False, has_existing_system: bool = False) -> dict:
    text = " ".join((description or "").strip().split())

    analysis_only = _has(text, [r"只分析", r"先分析.*不要.*生成", r"先不要生成", r"不要生成系统", r"只看看文件", r"只看.*字段"])
    existing = has_existing_system or _has(text, [r"旧系统", r"已有系统", r"现有系统", r"系统\s*zip", r"在.*系统.*基础.*改", r"增量修改"])
    desktop = _has(text, [r"独立桌面", r"单文件.*桌面", r"不要\s*web", r"不启.*web", r"桌面版"])
    prototype = _has(text, [r"原型", r"样机", r"demo", r"暂时没有.*文件", r"还没有.*数据", r"没有真实.*文件", r"先看.*界面"])
    full = _has(text, [r"完整.*系统", r"本地部署", r"局域网", r"完整包", r"源码\s*zip", r"生成.*系统", r"做成.*系统", r"exe", r"一键启动"])

    if analysis_only:
        mode = "analysis_only"
        reason = "用户明确要求只分析或先不要生成系统。"
        next_prompt = "只分析这些文件，输出字段、口径、冲突、待确认项和数据质量问题。"
    elif existing:
        mode = "adapt_existing_system"
        reason = "检测到已有/旧系统增量修改意图。"
        next_prompt = "以我上传的旧系统 ZIP 为基础，按新资料增量修改并重新交付完整 ZIP。"
    elif desktop:
        mode = "desktop_optional"
        reason = "用户明确要求独立桌面版或不使用 Web。"
        next_prompt = "我明确只要独立桌面版，请保留完整桌面 Python 源码和 EXE 构建源码。"
    elif prototype and not has_files:
        mode = "prototype_from_description"
        reason = "用户暂时没有真实业务文件，但需要结构/界面评审原型。"
        next_prompt = "先按业务描述生成可评审原型，未确认内容标记 demo/待确认，不要虚构真实历史数据。"
    elif full or has_files:
        mode = "full_lan_build"
        reason = "存在真实文件或明确的完整本地系统交付意图。"
        next_prompt = "根据我上传的文件生成完整能源日报本地部署 ZIP，保留完整源码、成对启停、备份恢复和 EXE 构建源码。"
    else:
        mode = "guidance_only"
        reason = "当前描述不足以安全判断是否应生成完整系统。"
        next_prompt = "帮我判断应该用完整系统、旧系统修改、只分析还是原型模式，不要先生成。"

    return {
        "mode": mode,
        "reason": reason,
        "has_files": bool(has_files),
        "has_existing_system": bool(has_existing_system),
        "next_prompt": next_prompt,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="判断能源日报技能应使用哪种执行模式")
    parser.add_argument("description", nargs="?", default="")
    parser.add_argument("--has-files", action="store_true")
    parser.add_argument("--has-existing-system", action="store_true")
    args = parser.parse_args()
    print(json.dumps(select_mode(args.description, has_files=args.has_files, has_existing_system=args.has_existing_system), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
