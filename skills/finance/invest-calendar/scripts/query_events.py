#!/usr/bin/env python3
"""
query_events.py — 统一事件查询入口

自动判断数据源：先试 WSCN API，无数据则走预排。

用法:
    python query_events.py --date 2026-08-07
    python query_events.py --month 2026-08
    python query_events.py --start 2026-08-01 --end 2026-08-31
    python query_events.py --keyword 非农
    python query_events.py --month 2026-08 --importance high
"""
import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent.resolve()


def run_fetch_wscn(args):
    """调用 fetch_wscn.py，返回事件列表"""
    cmd = [sys.executable, str(SCRIPT_DIR / "fetch_wscn.py"), "--format", "json"]
    if args.date:
        cmd += ["--date", args.date]
    elif args.month:
        cmd += ["--month", args.month]
    elif args.start and args.end:
        cmd += ["--start", args.start, "--end", args.end]
    if args.importance:
        cmd += ["--importance", args.importance]
    if args.country:
        cmd += ["--country", args.country]
    if args.keyword:
        cmd += ["--keyword", args.keyword]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        if result.returncode != 0:
            return []
        return json.loads(result.stdout) if result.stdout.strip() else []
    except (subprocess.TimeoutExpired, json.JSONDecodeError):
        return []


def run_prefill(month_str):
    """调用 prefill_month.py，返回预排事件列表"""
    cmd = [sys.executable, str(SCRIPT_DIR / "prefill_month.py"), "--month", month_str, "--format", "json"]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode != 0:
            return []
        return json.loads(result.stdout) if result.stdout.strip() else []
    except (subprocess.TimeoutExpired, json.JSONDecodeError):
        return []


def normalize_wscn_event(ev):
    """把 WSCN 事件归一化为统一格式"""
    from datetime import timezone, timedelta
    CST = timezone(timedelta(hours=8))
    dt = datetime.fromtimestamp(ev.get("public_date", 0), tz=CST)
    return {
        "id": ev.get("id"),
        "title": ev.get("title", ""),
        "country": ev.get("country", ""),
        "day": dt.day,
        "month": dt.month,
        "year": dt.year,
        "time": dt.strftime("%H:%M"),
        "importance": ev.get("importance", 0),
        "calendar_type": ev.get("calendar_type", ""),
        "category": "macro" if ev.get("calendar_type") == "FD" else "event",
        "description": "",
        "prev": ev.get("previous", "") or "",
        "exp": ev.get("forecast", "") or "",
        "actual": ev.get("actual", "") or "",
        "unit": ev.get("unit", "") or "",
        "source": "华尔街见闻 API",
    }


def normalize_prefill_event(ev, year, month):
    """把预排事件归一化"""
    return {
        "id": ev.get("id"),
        "title": ev.get("title", ""),
        "country": ev.get("country", ""),
        "day": ev.get("day"),
        "month": month,
        "year": year,
        "time": ev.get("time", "—"),
        "importance": ev.get("importance", 0),
        "calendar_type": ev.get("calendar_type", ""),
        "category": ev.get("category", ""),
        "description": ev.get("description", ""),
        "prev": "",
        "exp": "",
        "actual": "",
        "unit": "",
        "source": "预排（历史规律）",
    }


def filter_events(events, args):
    """统一过滤"""
    result = events
    if args.importance:
        imp_map = {"high": [3, 4], "mid": [2], "low": [1]}
        levels = imp_map.get(args.importance, [1, 2, 3, 4])
        result = [e for e in result if e.get("importance", 0) in levels]
    if args.country:
        kw = args.country.lower()
        result = [e for e in result if kw in e.get("country", "").lower()]
    if args.keyword:
        kw = args.keyword.lower()
        result = [e for e in result if kw in e.get("title", "").lower() or kw in e.get("description", "").lower()]
    return result


def main():
    parser = argparse.ArgumentParser(description="统一事件查询入口")
    parser.add_argument("--date", help="单日 YYYY-MM-DD")
    parser.add_argument("--month", help="单月 YYYY-MM")
    parser.add_argument("--start", help="区间开始")
    parser.add_argument("--end", help="区间结束")
    parser.add_argument("--importance", choices=["high", "mid", "low"])
    parser.add_argument("--country", help="国家过滤")
    parser.add_argument("--keyword", help="关键词")
    parser.add_argument("--format", choices=["table", "json"], default="table")
    parser.add_argument("--output", help="输出到文件")
    args = parser.parse_args()

    # 确定查询的月份
    if args.month:
        year, month = map(int, args.month.split("-"))
        month_str = args.month
    elif args.date:
        dt = datetime.strptime(args.date, "%Y-%m-%d")
        year, month = dt.year, dt.month
        month_str = args.date[:7]
    elif args.start:
        dt = datetime.strptime(args.start, "%Y-%m-%d")
        year, month = dt.year, dt.month
        month_str = args.start[:7]
    else:
        today = datetime.now()
        year, month = today.year, today.month
        month_str = today.strftime("%Y-%m")

    # 1. 先试 WSCN API
    print(f"查询 {month_str} 事件...", file=sys.stderr)
    wscn_events = run_fetch_wscn(args)
    if wscn_events:
        events = [normalize_wscn_event(e) for e in wscn_events]
        print(f"从 WSCN API 获取 {len(events)} 条事件", file=sys.stderr)
    else:
        # 2. 无数据则走预排
        print("WSCN API 无数据，改用历史规律预排...", file=sys.stderr)
        prefill_events = run_prefill(month_str)
        events = [normalize_prefill_event(e, year, month) for e in prefill_events]
        print(f"预排生成 {len(events)} 条事件", file=sys.stderr)

    # 过滤
    events = filter_events(events, args)
    events.sort(key=lambda e: (e.get("day", 0), e.get("time", "99")))

    # 输出
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(events, f, ensure_ascii=False, indent=2)
        print(f"已保存 {len(events)} 条事件到 {args.output}", file=sys.stderr)
    elif args.format == "json":
        print(json.dumps(events, ensure_ascii=False, indent=2))
    else:
        print(f"\n共 {len(events)} 条事件\n")
        for ev in events:
            stars = "★" * ev.get("importance", 0)
            type_label = "数据" if ev.get("calendar_type") == "FD" else "事件"
            vals = ""
            if ev.get("prev") or ev.get("exp") or ev.get("actual"):
                vals = f" | 前:{ev.get('prev','--')} 预:{ev.get('exp','--')} 实:{ev.get('actual','--')}"
            src = "📡" if ev.get("source", "").startswith("华尔街") else "🔮"
            print(
                f"{src} {ev['year']}-{ev['month']:02d}-{ev['day']:02d} {ev['time']} | "
                f"{ev['country']} | {stars} | {type_label} | {ev['title']}{vals}"
            )


if __name__ == "__main__":
    main()
