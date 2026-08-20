#!/usr/bin/env python3
"""
fetch_wscn.py — 华尔街见闻财经日历 API 调用脚本

调用 https://api-one-wscn.awtmt.com/apiv1/finance/macrodatas
返回结构化的财经事件列表。

用法:
    python fetch_wscn.py --month 2026-07
    python fetch_wscn.py --start 2026-07-01 --end 2026-07-31
    python fetch_wscn.py --date 2026-07-09
    python fetch_wscn.py --month 2026-07 --output events.json
    python fetch_wscn.py --month 2026-07 --format table
"""
import argparse
import calendar
import json
import sys
import urllib.request
import urllib.error
from datetime import datetime, timezone, timedelta

API_URL = "https://api-one-wscn.awtmt.com/apiv1/finance/macrodatas"

# 北京时间时区
CST = timezone(timedelta(hours=8))


def date_to_unix_range(date_str):
    """把 YYYY-MM-DD 转成当天的 UTC unix 时间戳区间 [start, end]"""
    dt = datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    start = int(dt.timestamp())
    end = start + 86400 - 1
    return start, end


def month_to_unix_range(month_str):
    """把 YYYY-MM 转成当月的 unix 时间戳区间"""
    year, month = map(int, month_str.split("-"))
    # 用 UTC 时间
    start_dt = datetime(year, month, 1, tzinfo=timezone.utc)
    if month == 12:
        end_dt = datetime(year + 1, 1, 1, tzinfo=timezone.utc)
    else:
        end_dt = datetime(year, month + 1, 1, tzinfo=timezone.utc)
    return int(start_dt.timestamp()), int(end_dt.timestamp()) - 1


def fetch_events(start_ts, end_ts):
    """调用 WSCN API 获取事件"""
    url = f"{API_URL}?start={start_ts}&end={end_ts}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        if data.get("code") != 20000:
            print(f"API 返回错误: {data}", file=sys.stderr)
            return []
        return data.get("data", {}).get("items", [])
    except urllib.error.URLError as e:
        print(f"网络错误: {e}", file=sys.stderr)
        return []
    except json.JSONDecodeError as e:
        print(f"JSON 解析错误: {e}", file=sys.stderr)
        return []


def format_event(ev):
    """格式化单个事件为可读字符串"""
    dt = datetime.fromtimestamp(ev["public_date"], tz=CST)
    stars = "★" * (ev.get("importance") or 0)
    country = ev.get("country", "")
    title = ev.get("title", "")
    prev = ev.get("previous", "") or "--"
    forecast = ev.get("forecast", "") or "--"
    actual = ev.get("actual", "") or "--"
    unit = ev.get("unit", "") or ""
    ctype = ev.get("calendar_type", "")
    type_label = "数据" if ctype == "FD" else "事件"
    return (
        f"{dt.strftime('%Y-%m-%d %H:%M')} | {country} | {stars} | {type_label} | "
        f"{title} | 前:{prev} 预:{forecast} 实:{actual} {unit}"
    )


def filter_events(events, args):
    """根据参数过滤事件"""
    result = events
    if args.importance:
        imp_map = {"high": [3, 4], "mid": [2], "low": [1]}
        levels = imp_map.get(args.importance, [1, 2, 3, 4])
        result = [e for e in result if (e.get("importance") or 0) in levels]
    if args.country:
        result = [e for e in result if args.country.lower() in (e.get("country", "")).lower() or args.country.lower() in (e.get("country_id", "")).lower()]
    if args.category:
        cat_map = {"macro": "FD", "monetary": "FD", "event": "FE"}
        # WSCN 的 FD/FE 分类较粗，这里只做粗过滤
        target = cat_map.get(args.category)
        if target:
            result = [e for e in result if e.get("calendar_type") == target]
    if args.keyword:
        kw = args.keyword.lower()
        result = [e for e in result if kw in e.get("title", "").lower()]
    return result


def main():
    parser = argparse.ArgumentParser(description="华尔街见闻财经日历 API 调用")
    parser.add_argument("--date", help="单日查询 YYYY-MM-DD")
    parser.add_argument("--month", help="单月查询 YYYY-MM")
    parser.add_argument("--start", help="区间开始 YYYY-MM-DD")
    parser.add_argument("--end", help="区间结束 YYYY-MM-DD")
    parser.add_argument("--importance", choices=["high", "mid", "low"], help="按重要性过滤")
    parser.add_argument("--country", help="按国家过滤（如 中国/美国/US/CN）")
    parser.add_argument("--category", choices=["macro", "monetary", "event"], help="按类别过滤")
    parser.add_argument("--keyword", help="按关键词过滤（如 非农/CPI/FOMC）")
    parser.add_argument("--format", choices=["table", "json"], default="table", help="输出格式")
    parser.add_argument("--output", help="输出到文件（JSON 格式）")
    args = parser.parse_args()

    # 确定时间范围
    if args.date:
        start_ts, end_ts = date_to_unix_range(args.date)
    elif args.month:
        start_ts, end_ts = month_to_unix_range(args.month)
    elif args.start and args.end:
        start_ts, _ = date_to_unix_range(args.start)
        _, end_ts = date_to_unix_range(args.end)
    else:
        # 默认查今天
        today = datetime.now(tz=CST).strftime("%Y-%m-%d")
        start_ts, end_ts = date_to_unix_range(today)
        print(f"未指定日期，默认查询今天 {today}", file=sys.stderr)

    # 拉取
    events = fetch_events(start_ts, end_ts)
    if not events:
        print("未获取到事件数据（可能是 API 无数据或网络问题）", file=sys.stderr)
        print("提示：WSCN API 通常只覆盖未来 1-2 个月，更远的日期请用 prefill_month.py 预排", file=sys.stderr)
        return

    # 过滤
    events = filter_events(events, args)
    events.sort(key=lambda e: e.get("public_date", 0))

    # 输出
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(events, f, ensure_ascii=False, indent=2)
        print(f"已保存 {len(events)} 条事件到 {args.output}", file=sys.stderr)
    elif args.format == "json":
        print(json.dumps(events, ensure_ascii=False, indent=2))
    else:
        print(f"共 {len(events)} 条事件\n")
        for ev in events:
            print(format_event(ev))


if __name__ == "__main__":
    main()
