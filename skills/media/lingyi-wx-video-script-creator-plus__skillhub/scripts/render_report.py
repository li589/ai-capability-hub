#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""视频号爆款文案生成（进阶版）—— 输出后端 markdown

后端返回完整、可交付的 Markdown（`data.result.markdown`）。本脚本从输入 JSON
中定位该 markdown 字段并原样写出，与后端产物保持一致。

用法:
    python3 render_report.py --in <resp.json> --out <report.md>

退出码:
    0  成功
    22 输入文件读不到 / 写盘失败
    23 未在响应中找到 markdown 字段
"""

import argparse
import json
import sys
from pathlib import Path

E_OK = 0
E_IO = 22
E_NO_MARKDOWN = 23


def find_markdown(obj):
    """从后端标准响应 data.result.markdown 取报告正文。"""
    if not isinstance(obj, dict):
        return None
    data = obj.get("data")
    if not isinstance(data, dict):
        return None
    result = data.get("result")
    if not isinstance(result, dict):
        return None
    md = result.get("markdown")
    return md if isinstance(md, str) and md.strip() else None


def main():
    ap = argparse.ArgumentParser(description="直出后端 markdown（视频号脚本生成进阶版）")
    ap.add_argument("--in", dest="inp", required=True, help="输入接口响应 JSON 路径")
    ap.add_argument("--out", required=True, help="输出 MD 路径")
    args = ap.parse_args()

    inp = Path(args.inp)
    try:
        resp = json.loads(inp.read_text("utf-8"))
    except FileNotFoundError:
        print("[render_report] 输入文件不存在：%s" % inp, file=sys.stderr)
        sys.exit(E_IO)
    except (json.JSONDecodeError, OSError) as e:
        print("[render_report] 读取/解析失败：%s" % e, file=sys.stderr)
        sys.exit(E_IO)

    md = find_markdown(resp) if isinstance(resp, dict) else None
    if not md:
        print("[render_report] 未在响应中找到 markdown 字段（data.result.markdown）", file=sys.stderr)
        sys.exit(E_NO_MARKDOWN)

    try:
        out = Path(args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(md if md.endswith("\n") else md + "\n", "utf-8")
    except OSError as e:
        print("[render_report] 写盘失败：%s" % e, file=sys.stderr)
        sys.exit(E_IO)

    print("[render_report] 已写入（后端 markdown 直出）：%s" % out, file=sys.stderr)
    sys.exit(E_OK)


if __name__ == "__main__":
    main()
