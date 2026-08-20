#!/usr/bin/env python3
"""
prefill_month.py — 按历史规律预排某月的财经事件

当 WSCN API 无数据（如未来2个月外）时，基于各指标的月度发布规律
生成预排事件列表。

用法:
    python prefill_month.py --month 2026-08
    python prefill_month.py --month 2026-08 --output events.json
    python prefill_month.py --month 2026-08 --format table
"""
import argparse
import json
import sys
from datetime import datetime, timedelta, date
import calendar as cal_module


# 各指标的月度发布规律
# 格式: (title, country, day_rule, time_str, importance, calendar_type, category, description)
# day_rule:
#   int → 每月该日
#   "first_friday" → 每月第一个周五
#   "last_day" → 每月最后一天
#   "mid" → 月中(15日前后)
#   "flexible" → 大致时间区间
RECURRENCE_RULES = [
    # ===== 中国宏观数据 =====
    ("官方制造业PMI", "中国", "last_day", "09:00", 3, "FD", "macro", "国家统计局制造业PMI，50为荣枯线"),
    ("官方非制造业PMI", "中国", "last_day", "09:00", 2, "FD", "macro", "非制造业商务活动指数"),
    ("官方综合PMI", "中国", "last_day", "09:00", 2, "FD", "macro", "综合PMI产出指数"),
    ("财新制造业PMI", "中国", "next_day_1", "09:45", 2, "FD", "macro", "财新中国制造业PMI（次月1日）"),
    ("CPI / PPI", "中国", 9, "09:30", 3, "FD", "macro", "居民消费价格指数 + 工业生产者出厂价格指数"),
    ("进出口数据", "中国", 10, "10:00", 2, "FD", "macro", "海关总署美元计价进出口同比"),
    ("社融 / M2", "中国", "flexible_10_15", "—", 3, "FD", "macro", "社会融资规模增量 + M2同比"),
    ("MLF操作", "中国", 15, "09:20", 3, "FD", "monetary", "央行中期借贷便利操作，关注利率变动"),
    ("工业增加值/固投/社零", "中国", 15, "10:00", 2, "FD", "macro", "月度经济活动数据（季度月含GDP）"),
    ("LPR报价", "中国", 20, "09:15", 3, "FD", "monetary", "1年期/5年期贷款市场报价利率"),
    ("外汇储备", "中国", 7, "—", 1, "FD", "macro", "央行外汇储备规模"),

    # ===== 美国宏观数据 =====
    ("非农就业报告", "美国", "first_friday", "20:30", 4, "FD", "macro", "BLS非农就业人数+失业率+薪资"),
    ("失业率", "美国", "first_friday", "20:30", 3, "FD", "macro", "与非农同步发布"),
    ("CPI", "美国", "mid_12", "20:30", 4, "FD", "macro", "含核心CPI，美联储通胀核心指标"),
    ("PPI", "美国", "mid_13", "20:30", 2, "FD", "macro", "生产者价格指数，CPI先行指标"),
    ("零售销售", "美国", "mid_15", "20:30", 2, "FD", "macro", "占GDP约70%的消费支出观测"),
    ("PCE物价指数", "美国", "last_friday", "20:30", 4, "FD", "macro", "美联储最青睐的通胀指标"),
    ("初请失业金", "美国", "every_thursday", "20:30", 1, "FD", "macro", "每周四发布"),
    ("ISM制造业PMI", "美国", "first_monday", "22:00", 3, "FD", "macro", "供应管理协会制造业PMI"),
    ("ISM非制造业PMI", "美国", "first_wednesday", "22:00", 2, "FD", "macro", "供应管理协会非制造业PMI"),

    # ===== 央行政策 =====
    ("FOMC利率决议", "美国", "fomc", "02:00", 4, "FD", "monetary", "美联储议息会议（每年8次，需查具体日程）"),
    ("FOMC会议纪要", "美国", "fomc_minutes", "02:00", 2, "FD", "monetary", "会议后3周发布"),
    ("ECB利率决议", "欧元区", "ecb", "20:45", 3, "FD", "monetary", "欧央行每6周一次"),
    ("BOJ利率决议", "日本", "boj", "—", 3, "FD", "monetary", "日本央行每年8次"),

    # ===== 重要会议 =====
    ("OPEC+会议", "全球", "opec", "—", 3, "FE", "meeting", "OPEC+部长级会议（影响油价）"),
    ("Jackson Hole全球央行年会", "美国", "jackson_hole", "—", 3, "FE", "meeting", "每年8月下旬，美联储主席讲话"),
]


def get_first_friday(year, month):
    """每月第一个周五"""
    d = date(year, month, 1)
    while d.weekday() != 4:  # 4=Friday
        d += timedelta(days=1)
    return d.day


def get_last_friday(year, month):
    """每月最后一个周五"""
    last_day = cal_module.monthrange(year, month)[1]
    d = date(year, month, last_day)
    while d.weekday() != 4:
        d -= timedelta(days=1)
    return d.day


def get_first_monday(year, month):
    d = date(year, month, 1)
    while d.weekday() != 0:
        d += timedelta(days=1)
    return d.day


def get_first_wednesday(year, month):
    d = date(year, month, 1)
    while d.weekday() != 2:
        d += timedelta(days=1)
    return d.day


def get_last_day(year, month):
    return cal_module.monthrange(year, month)[1]


def resolve_day(day_rule, year, month):
    """把发布规律解析成具体日期"""
    if isinstance(day_rule, int):
        return day_rule
    if day_rule == "first_friday":
        return get_first_friday(year, month)
    if day_rule == "last_friday":
        return get_last_friday(year, month)
    if day_rule == "first_monday":
        return get_first_monday(year, month)
    if day_rule == "first_wednesday":
        return get_first_wednesday(year, month)
    if day_rule == "last_day":
        return get_last_day(year, month)
    if day_rule == "next_day_1":
        # 次月1日，返回 None 表示跳过本月
        return None
    if day_rule == "flexible_10_15":
        return 12  # 取中间值
    if day_rule == "mid_12":
        return 12
    if day_rule == "mid_13":
        return 13
    if day_rule == "mid_15":
        return 15
    if day_rule == "every_thursday":
        return "thursdays"  # 特殊处理
    # 需要查具体日程的（fomc/ecb/boj/opec/jackson_hole）返回 None，单独处理
    return None


def get_special_events(year, month):
    """获取需要查具体日程的特殊事件（FOMC/ECB/Jackson Hole等）"""
    special = []
    # Jackson Hole: 每年8月下旬（通常是8月22-24日左右）
    if month == 8:
        special.append({
            "title": "Jackson Hole 全球央行年会",
            "country": "美国",
            "day": 22,
            "time": "22:00",
            "importance": 3,
            "calendar_type": "FE",
            "category": "meeting",
            "description": "全球央行年会，美联储主席通常发表重要讲话，影响市场对后续政策路径预期",
            "source": "预排（按历史规律）",
        })
    return special


def prefill_month(year, month):
    """生成某月的预排事件"""
    events = []
    event_id = 1

    for title, country, day_rule, time_str, importance, ctype, category, desc in RECURRENCE_RULES:
        if day_rule == "every_thursday":
            # 每周四的事件（如初请失业金）
            for d in range(1, get_last_day(year, month) + 1):
                dt = date(year, month, d)
                if dt.weekday() == 3:  # Thursday
                    events.append({
                        "id": event_id,
                        "title": title,
                        "country": country,
                        "day": d,
                        "time": time_str,
                        "importance": importance,
                        "calendar_type": ctype,
                        "category": category,
                        "description": desc,
                        "source": "预排（按历史规律）",
                        "prev": "",
                        "exp": "",
                        "actual": "",
                    })
                    event_id += 1
            continue

        day = resolve_day(day_rule, year, month)
        if day is None:
            continue

        events.append({
            "id": event_id,
            "title": title,
            "country": country,
            "day": day,
            "time": time_str,
            "importance": importance,
            "calendar_type": ctype,
            "category": category,
            "description": desc,
            "source": "预排（按历史规律）",
            "prev": "",
            "exp": "",
            "actual": "",
        })
        event_id += 1

    # 添加特殊事件
    events.extend(get_special_events(year, month))

    # 按日期+时间排序
    def sort_key(e):
        time_sort = e["time"] if e["time"] != "—" else "99:99"
        return (e["day"], time_sort)

    events.sort(key=sort_key)
    return events


def format_event(ev, year, month):
    """格式化输出"""
    stars = "★" * ev.get("importance", 0)
    type_label = "数据" if ev.get("calendar_type") == "FD" else "事件"
    return (
        f"{year}-{month:02d}-{ev['day']:02d} {ev['time']} | {ev['country']} | {stars} | "
        f"{type_label} | {ev['title']} | {ev.get('description', '')} [预排]"
    )


def main():
    parser = argparse.ArgumentParser(description="按历史规律预排财经事件")
    parser.add_argument("--month", required=True, help="预排月份 YYYY-MM")
    parser.add_argument("--format", choices=["table", "json"], default="table")
    parser.add_argument("--output", help="输出到文件")
    args = parser.parse_args()

    year, month = map(int, args.month.split("-"))
    events = prefill_month(year, month)

    print(f"=== {year}年{month}月 预排事件（共{len(events)}条）===\n", file=sys.stderr)
    print(f"⚠️ 预排数据基于历史规律，实际发布日期可能因节假日调整，请以官方公告为准\n", file=sys.stderr)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(events, f, ensure_ascii=False, indent=2)
        print(f"已保存到 {args.output}", file=sys.stderr)
    elif args.format == "json":
        print(json.dumps(events, ensure_ascii=False, indent=2))
    else:
        for ev in events:
            print(format_event(ev, year, month))


if __name__ == "__main__":
    main()
