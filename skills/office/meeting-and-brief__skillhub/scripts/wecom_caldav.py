#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
shared/wecom_caldav.py · 企业微信 CalDAV 日程拉取主脚本（v1.3.0）

通过标准 CalDAV 协议直连企微日历服务器 caldav.wecom.work，
读本地 ~/.consult/wecom-caldav.yaml 取 username/password，
按时段 + 客户关键字过滤后输出与 calendar_ics_parse.py 一致结构。

⚠ 安全：CalDAV 密码虽然不是 corpsecret 长期凭据（可在企微后台撤销），
   但仍是敏感字段——本机 ~/.consult/ 配置，绝不进 plugin/git，
   泄露后立即在企微 APP → 同步设置 → 关闭/重生成。

依赖：
    pip install caldav

调用：
    from wecom_caldav import fetch_schedules
    items = fetch_schedules(
        start="2025-11-01", end="2025-11-30",
        client_keywords=["客户", "甲方"],
    )
"""
from __future__ import annotations
import os
import datetime as dt
from pathlib import Path
from typing import Optional


CONFIG_PATH = Path.home() / ".consult" / "wecom-caldav.yaml"

CONFIG_HINT = """
请在 ~/.consult/wecom-caldav.yaml 写入：

username: "your-wecom-account"           # 企微 APP → 日历 → 同步到其他日历 → 账户
password: "your-caldav-password"          # 同上 → 密码（固定密码，不过期）
server: "https://caldav.wecom.work"      # 企微 CalDAV 服务器（固定）

# 可选：只拉特定日历名（精确匹配 summary）
calendar_filter: []
#  - "我的日程"
#  - "客户工作"

⚠ 该文件含敏感密码：
   1. .gitignore 必须包含 .consult/
   2. 文件权限 chmod 600
   3. 不发邮件 / 不微信 / 不复制粘贴
   4. 泄露后在企微 APP → 日历 → 同步设置 → 关闭或重新生成
"""

VERBS = ["汇报", "沟通", "讨论", "评审", "研讨", "走访", "参观", "梳理", "答疑",
         "汇总", "修订", "发送", "审议", "确认", "对接", "培训", "辅导"]


# ============ 配置 ============

def _load_config():
    cfg = {}
    # 环境变量优先
    for k in ("username", "password", "server"):
        envk = "CONSULT_CALDAV_" + k.upper()
        if os.environ.get(envk):
            cfg[k] = os.environ[envk]
    # 本地 yaml
    if CONFIG_PATH.exists():
        import yaml
        with open(CONFIG_PATH, encoding="utf-8") as f:
            file_cfg = yaml.safe_load(f) or {}
        for k, v in file_cfg.items():
            cfg.setdefault(k, v)

    missing = [k for k in ("username", "password") if not cfg.get(k)]
    if missing:
        raise RuntimeError(f"CalDAV 凭据缺失：{missing}\n{CONFIG_HINT}")
    cfg.setdefault("server", "https://caldav.wecom.work")
    cfg.setdefault("calendar_filter", [])
    return cfg


# ============ 工具方法 ============

def _guess_verb(title: str) -> str:
    for v in VERBS:
        if v in title:
            return v
    return "参加"


def _match_keywords(text_bundle: str, keywords: list) -> bool:
    if not keywords:
        return True
    keys = [k.lower() for k in keywords]
    haystack = text_bundle.lower()
    return any(k in haystack for k in keys)


def _to_local_dt(d) -> dt.datetime:
    """把 vobject/icalendar 的 datetime/date 统一转为 naive local datetime。"""
    if hasattr(d, 'astimezone'):
        # tz-aware → 本地时区
        try:
            d = d.astimezone()
        except Exception:
            pass
        return d.replace(tzinfo=None)
    if isinstance(d, dt.date) and not isinstance(d, dt.datetime):
        return dt.datetime(d.year, d.month, d.day, 0, 0, 0)
    return d


# ============ 主入口 ============

def fetch_schedules(
    start: str,
    end: str,
    client_keywords: Optional[list] = None,
) -> list:
    """CalDAV 拉时段日程，按关键字过滤。

    依赖：pip install caldav

    Args:
        start: "YYYY-MM-DD"，含
        end:   "YYYY-MM-DD"，含
        client_keywords: 客户匹配关键字列表

    Returns:
        list[dict]：date / time / title / attendees / location / body / verb / source="caldav" / calendar

    Raises:
        ImportError: 未装 caldav 库
        RuntimeError: 凭据缺失 / 连接失败 / 认证失败
    """
    try:
        import caldav
    except ImportError:
        raise ImportError(
            "未装 caldav 库。请运行：pip install caldav\n"
            "（或改用 calendar_ics_parse.py 离线方案）"
        )

    cfg = _load_config()

    # 连接
    try:
        client = caldav.DAVClient(
            url=cfg["server"],
            username=cfg["username"],
            password=cfg["password"],
        )
        principal = client.principal()
        calendars = principal.calendars()
    except Exception as e:
        raise RuntimeError(
            f"CalDAV 连接/认证失败：{e}\n"
            f"检查 username/password 是否正确；"
            f"密码可在企微 APP → 日历 → 同步到其他日历 重新生成"
        )

    # 过滤指定日历名
    name_filter = cfg.get("calendar_filter") or []
    if name_filter:
        calendars = [c for c in calendars if str(c.name) in name_filter]

    # 时间窗
    s_y, s_m, s_d = (int(x) for x in start.split("-"))
    e_y, e_m, e_d = (int(x) for x in end.split("-"))
    s_dt = dt.datetime(s_y, s_m, s_d, 0, 0, 0)
    e_dt = dt.datetime(e_y, e_m, e_d, 23, 59, 59)

    items = []
    for cal in calendars:
        try:
            events = cal.search(start=s_dt, end=e_dt, event=True, expand=True)
        except Exception:
            # 部分服务器不支持 expand（展开 RRULE 重复）→ 退化为不展开
            try:
                events = cal.date_search(start=s_dt, end=e_dt)
            except Exception:
                continue

        for ev in events:
            try:
                vobj = ev.icalendar_component
                summary = str(vobj.get("summary") or "")
                description = str(vobj.get("description") or "")
                location = str(vobj.get("location") or "")
                status = str(vobj.get("status") or "").upper()
                if status == "CANCELLED":
                    continue

                dtstart_raw = vobj.get("dtstart")
                if not dtstart_raw:
                    continue
                d_start = _to_local_dt(dtstart_raw.dt)

                dtend_raw = vobj.get("dtend")
                d_end = _to_local_dt(dtend_raw.dt) if dtend_raw else None

                # 客户端再过滤一次时段（CalDAV 服务端可能返回边界外事件）
                if not (s_dt <= d_start <= e_dt):
                    continue

                # 参与人
                attendee_names = []
                att_raw = vobj.get("attendee")
                if att_raw is not None:
                    att_list = att_raw if isinstance(att_raw, list) else [att_raw]
                    for a in att_list:
                        cn = a.params.get("CN") if hasattr(a, "params") else None
                        if cn:
                            attendee_names.append(str(cn))
                        else:
                            attendee_names.append(str(a).replace("mailto:", ""))

                # 关键字过滤
                bundle = summary + " " + description + " " + location + " " + " ".join(attendee_names)
                if not _match_keywords(bundle, client_keywords or []):
                    continue

                items.append({
                    "date": d_start.strftime("%Y-%m-%d"),
                    "time": (d_start.strftime("%H:%M") + "-" + d_end.strftime("%H:%M")) if d_end else d_start.strftime("%H:%M"),
                    "title": summary,
                    "attendees": attendee_names,
                    "location": location,
                    "body": description,
                    "verb": _guess_verb(summary),
                    "source": "caldav",
                    "calendar": str(cal.name) if hasattr(cal, "name") else "",
                })
            except Exception:
                continue   # 单事件解析失败不阻塞整批

    items.sort(key=lambda x: (x["date"], x["time"]))
    return items


def to_brief_log_line(item: dict) -> str:
    """转简报"{月}月{日}日，{动词}{对象}；"格式。"""
    if not item.get("date"):
        return ""
    y, m, d = item["date"].split("-")
    title = item['title']
    if any(title.startswith(v) for v in VERBS) or title.startswith("参加"):
        return f"{int(m)}月{int(d)}日，{title}；"
    return f"{int(m)}月{int(d)}日，{item['verb']}{title}；"


# ============ CLI ============

if __name__ == "__main__":
    import sys, argparse, json
    p = argparse.ArgumentParser(description="企微 CalDAV 日程拉取（v1.3.0）")
    p.add_argument("--start", required=True, help="YYYY-MM-DD")
    p.add_argument("--end", required=True, help="YYYY-MM-DD")
    p.add_argument("--client", action="append", default=[], help="客户关键字，可重复")
    p.add_argument("--format", choices=["json", "brief-log"], default="json")
    args = p.parse_args()

    try:
        items = fetch_schedules(args.start, args.end, client_keywords=args.client)
    except Exception as e:
        print(f"❌ {e}", file=sys.stderr)
        sys.exit(1)

    if args.format == "json":
        print(json.dumps(items, ensure_ascii=False, indent=2, default=str))
    else:
        for it in items:
            print(to_brief_log_line(it))
    print(f"\n共 {len(items)} 条日程匹配", file=sys.stderr)
