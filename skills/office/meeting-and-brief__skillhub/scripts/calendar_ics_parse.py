#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
shared/wecom_ics_parse.py · ICS 导出文件解析（v1.1.1 备选路线）

为什么有这个文件：
  企微 OA `get_by_calendar` 接口只能拉【应用 API 创建的日历】，
  普通用户在 APP 里手动建的日历 API 拉不到。
  这条文件提供"导出 ics → 解析"的备选路线——零网络依赖、零凭据，
  用户在企微 APP 里手动导出日历为 .ics 后丢给 plugin。

输出结构与 wecom_calendar.fetch_schedules() 一致：
    [{date, time, title, attendees, location, body, verb, source: "ics"}]

调用：
    from wecom_ics_parse import parse_ics
    items = parse_ics(
        ics_path="/path/to/calendar.ics",
        start="2025-11-01", end="2025-11-30",
        client_keywords=["客户"],
    )
"""
from __future__ import annotations
import datetime as dt
import re
from pathlib import Path
from typing import Optional


VERBS = ["汇报", "沟通", "讨论", "评审", "研讨", "走访", "参观", "梳理", "答疑",
         "汇总", "修订", "发送", "审议", "确认", "对接", "培训", "辅导"]


def _guess_verb(title: str) -> str:
    for v in VERBS:
        if v in title:
            return v
    return "参加"


def _unescape_ics(s: str) -> str:
    """解 ICS 转义：\\n → newline, \\, → ',', \\; → ';'。"""
    return (s.replace("\\n", "\n").replace("\\N", "\n")
              .replace("\\,", ",").replace("\\;", ";")
              .replace("\\\\", "\\"))


def _parse_ics_dt(value: str) -> Optional[dt.datetime]:
    """解析 ICS 的 DTSTART/DTEND 值。支持：
       - 20251118T140000Z（UTC）
       - 20251118T140000（floating local）
       - 20251118（whole-day）
    """
    if not value:
        return None
    # Strip TZID prefix like "TZID=Asia/Shanghai:20251118T140000"
    if ":" in value:
        value = value.rsplit(":", 1)[-1]
    value = value.strip()

    try:
        if value.endswith("Z"):
            # UTC
            return dt.datetime.strptime(value, "%Y%m%dT%H%M%SZ").replace(tzinfo=dt.timezone.utc).astimezone()
        if "T" in value:
            return dt.datetime.strptime(value, "%Y%m%dT%H%M%S")
        # date-only
        return dt.datetime.strptime(value, "%Y%m%d")
    except ValueError:
        return None


def _unfold_lines(text: str) -> list:
    """ICS 行折叠（RFC 5545 §3.1）：以空格/制表符开头的行是上一行的续行。"""
    out = []
    for line in text.splitlines():
        if line.startswith(" ") or line.startswith("\t"):
            if out:
                out[-1] += line[1:]
        else:
            out.append(line)
    return out


def _parse_events(text: str) -> list:
    """切出所有 VEVENT 块，每个块解析为字段字典。"""
    lines = _unfold_lines(text)
    events = []
    cur = None
    for line in lines:
        ls = line.strip()
        if ls == "BEGIN:VEVENT":
            cur = {"attendees": []}
        elif ls == "END:VEVENT":
            if cur is not None:
                events.append(cur)
            cur = None
        elif cur is not None and ":" in ls:
            key_full, _, val = ls.partition(":")
            key = key_full.split(";")[0].upper()    # 去掉参数（如 TZID）
            params = key_full
            val = _unescape_ics(val)

            if key == "SUMMARY":
                cur["summary"] = val
            elif key == "DESCRIPTION":
                cur["description"] = val
            elif key == "LOCATION":
                cur["location"] = val
            elif key == "DTSTART":
                cur["dtstart"] = _parse_ics_dt(params + ":" + val)
            elif key == "DTEND":
                cur["dtend"] = _parse_ics_dt(params + ":" + val)
            elif key == "ATTENDEE":
                # 形如 ATTENDEE;CN=张三:mailto:zhangsan@example.com
                cn_match = re.search(r"CN=([^;:]+)", params)
                name = cn_match.group(1) if cn_match else val.replace("mailto:", "")
                cur["attendees"].append(name)
            elif key == "STATUS":
                cur["status"] = val   # CONFIRMED / CANCELLED / TENTATIVE
            elif key == "UID":
                cur["uid"] = val
            elif key == "ORGANIZER":
                cn_match = re.search(r"CN=([^;:]+)", params)
                cur["organizer"] = cn_match.group(1) if cn_match else val.replace("mailto:", "")
    return events


def _in_window(d: dt.datetime, start: str, end: str) -> bool:
    s_y, s_m, s_d = (int(x) for x in start.split("-"))
    e_y, e_m, e_d = (int(x) for x in end.split("-"))
    s_dt = dt.datetime(s_y, s_m, s_d, 0, 0, 0)
    e_dt = dt.datetime(e_y, e_m, e_d, 23, 59, 59)
    # 处理 tz-aware vs naive
    if d.tzinfo is not None:
        d = d.replace(tzinfo=None)
    return s_dt <= d <= e_dt


def _match_keywords(event: dict, keywords: list) -> bool:
    if not keywords:
        return True
    keys = [k.lower() for k in keywords]
    haystack = " ".join([
        event.get("summary", "") or "",
        event.get("description", "") or "",
        event.get("location", "") or "",
        " ".join(event.get("attendees", []) or []),
    ]).lower()
    return any(k in haystack for k in keys)


# ============ 主入口 ============

def parse_ics(
    ics_path: str,
    start: str,
    end: str,
    client_keywords: Optional[list] = None,
) -> list:
    """解析 ICS 文件 → 时间窗 + 关键字过滤 → 结构化日程条目。"""
    text = Path(ics_path).read_text(encoding="utf-8", errors="replace")
    events = _parse_events(text)

    items = []
    for ev in events:
        if (ev.get("status") or "").upper() == "CANCELLED":
            continue
        dtstart = ev.get("dtstart")
        if not dtstart or not _in_window(dtstart, start, end):
            continue
        if not _match_keywords(ev, client_keywords or []):
            continue

        dtend = ev.get("dtend")
        title = ev.get("summary") or "(无标题)"
        items.append({
            "date": dtstart.strftime("%Y-%m-%d"),
            "time": (dtstart.strftime("%H:%M") + "-" + dtend.strftime("%H:%M")) if dtend else dtstart.strftime("%H:%M"),
            "title": title,
            "attendees": ev.get("attendees") or [],
            "location": ev.get("location") or "",
            "body": ev.get("description") or "",
            "verb": _guess_verb(title),
            "source": "ics",
        })
    items.sort(key=lambda x: (x["date"], x["time"]))
    return items


def to_brief_log_line(item: dict) -> str:
    if not item.get("date"):
        return ""
    y, m, d = item["date"].split("-")
    title = item['title']
    # 避免重复：title 已含动词时不再加 verb 前缀
    if any(title.startswith(v) for v in VERBS) or title.startswith("参加"):
        return f"{int(m)}月{int(d)}日，{title}；"
    return f"{int(m)}月{int(d)}日，{item['verb']}{title}；"


# ============ CLI ============

if __name__ == "__main__":
    import sys, argparse, json
    p = argparse.ArgumentParser(description="ICS 文件日程解析")
    p.add_argument("--ics", required=True, help="ICS 文件路径")
    p.add_argument("--start", required=True, help="YYYY-MM-DD")
    p.add_argument("--end", required=True, help="YYYY-MM-DD")
    p.add_argument("--client", action="append", default=[], help="客户关键字，可重复")
    p.add_argument("--format", choices=["json", "brief-log"], default="json")
    args = p.parse_args()

    items = parse_ics(args.ics, args.start, args.end, client_keywords=args.client)

    if args.format == "json":
        print(json.dumps(items, ensure_ascii=False, indent=2, default=str))
    else:
        for it in items:
            print(to_brief_log_line(it))
    print(f"\n共 {len(items)} 条日程匹配", file=sys.stderr)
