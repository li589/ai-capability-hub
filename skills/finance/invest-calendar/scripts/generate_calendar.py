#!/usr/bin/env python3
"""
generate_calendar.py — 根据事件数据生成可交互 HTML 日历

复用 references/calendar_template.html 模板，把事件数据注入。

用法:
    python generate_calendar.py --month 2026-08 --output 8月日历.html
    python generate_calendar.py --start 2026-08-01 --end 2026-08-31 --output 8月日历.html
    python generate_calendar.py --events events.json --output 日历.html
"""
import argparse
import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent.resolve()
SKILL_DIR = SCRIPT_DIR.parent
TEMPLATE_PATH = SKILL_DIR / "references" / "calendar_template.html"


def fetch_events_via_query(args):
    """通过 query_events.py 获取事件"""
    cmd = [sys.executable, str(SCRIPT_DIR / "query_events.py"), "--format", "json"]
    if args.month:
        cmd += ["--month", args.month]
    elif args.start and args.end:
        cmd += ["--start", args.start, "--end", args.end]
    if args.importance:
        cmd += ["--importance", args.importance]

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    if result.returncode != 0:
        print(f"查询失败: {result.stderr}", file=sys.stderr)
        return []
    try:
        return json.loads(result.stdout) if result.stdout.strip() else []
    except json.JSONDecodeError:
        return []


def event_to_js_object(ev, idx):
    """把单个事件转成 JS 对象字符串"""
    # 映射 importance 数字到 high/mid/low
    imp = ev.get("importance", 1)
    if imp >= 3:
        imp_str = "high"
    elif imp == 2:
        imp_str = "mid"
    else:
        imp_str = "low"

    # 映射 country 到 region
    country = ev.get("country", "")
    region_map = {
        "中国": "cn", "美国": "us", "欧元区": "eu", "日本": "jp",
        "全球": "global", "英国": "global", "德国": "eu", "法国": "eu",
    }
    region = region_map.get(country, "global")

    # 映射 category
    cat = ev.get("category", "macro")
    if cat == "event":
        cat = "corporate"

    # flag
    flag_map = {"中国": "🇨🇳", "美国": "🇺🇸", "欧元区": "🇪🇺", "日本": "🇯🇵", "全球": "🌍", "英国": "🇬🇧", "德国": "🇩🇪", "法国": "🇫🇷"}
    flag = flag_map.get(country, "🌍")

    title = ev.get("title", "").replace('"', '\\"')
    desc = ev.get("description", "").replace('"', '\\"')
    source = ev.get("source", "").replace('"', '\\"')
    prev = (ev.get("prev") or "").replace('"', '\\"')
    exp = (ev.get("exp") or "").replace('"', '\\"')
    actual = (ev.get("actual") or "").replace('"', '\\"')

    day = ev.get("day", 1)
    time_str = ev.get("time", "—")

    assets_json = json.dumps(ev.get("assets", ["市场"]), ensure_ascii=False)

    return (
        f'  {{ id:{idx}, day:{day}, time:"{time_str}", title:"{title}", '
        f'flag:"{flag}", region:"{region}", cat:"{cat}", imp:"{imp_str}", '
        f'desc:"{desc}", source:"{source}", prev:"{prev}", exp:"{exp}", actual:"{actual}", '
        f'assets:{assets_json} }},'
    )


def generate_html(events, year, month, output_path):
    """把事件注入模板生成 HTML"""
    if not TEMPLATE_PATH.exists():
        print(f"模板文件不存在: {TEMPLATE_PATH}", file=sys.stderr)
        return False

    template = TEMPLATE_PATH.read_text(encoding="utf-8")

    # 生成事件 JS 数组
    events_js = "\n".join(event_to_js_object(ev, i + 1) for i, ev in enumerate(events))
    events_block = f"const EVENTS = [\n{events_js}\n];"

    # 替换模板中的 EVENTS 数组（用正则匹配从 const EVENTS = [ 到 ];）
    pattern = r"const EVENTS = \[[\s\S]*?\];"
    new_template = re.sub(pattern, events_block, template, count=1)

    if new_template == template:
        print("警告：未找到 EVENTS 数组，模板未修改", file=sys.stderr)
        return False

    # 替换月份注入逻辑：所有事件都属于当前月份
    # 把 forEach 注入改成按 month/year 字段（如果有），否则全部归当前月
    # 查找现有的 forEach 注入块（支持多行格式）
    inject_pattern = r"// [^\n]*月份/年份标记[^\n]*\nEVENTS\.forEach\([\s\S]*?\}\);"
    inject_replacement = f"EVENTS.forEach(e => {{ e.month = {month - 1}; e.year = {year}; }});"
    new_template = re.sub(inject_pattern, inject_replacement, new_template, count=1)

    # 把 currentDate 和 viewDate 设为今天（模板里已经是用 new Date()，保留）
    # 但要确保 viewDate 默认指向目标月份
    state_pattern = r"let viewDate = new Date\(today0\.getFullYear\(\), today0\.getMonth\(\), 1\);"
    state_replacement = f"let viewDate = new Date({year}, {month - 1}, 1);"
    new_template = re.sub(state_pattern, state_replacement, new_template, count=1)

    # 写入输出文件
    Path(output_path).write_text(new_template, encoding="utf-8")
    return True


def main():
    parser = argparse.ArgumentParser(description="生成 HTML 财经日历")
    parser.add_argument("--month", help="目标月份 YYYY-MM")
    parser.add_argument("--start", help="区间开始")
    parser.add_argument("--end", help="区间结束")
    parser.add_argument("--events", help="直接指定事件 JSON 文件")
    parser.add_argument("--importance", choices=["high", "mid", "low"])
    parser.add_argument("--output", required=True, help="输出 HTML 路径")
    args = parser.parse_args()

    # 确定年份月份
    if args.month:
        year, month = map(int, args.month.split("-"))
    elif args.start:
        dt = datetime.strptime(args.start, "%Y-%m-%d")
        year, month = dt.year, dt.month
    else:
        now = datetime.now()
        year, month = now.year, now.month

    # 获取事件
    if args.events:
        with open(args.events, "r", encoding="utf-8") as f:
            events = json.load(f)
        print(f"从文件加载 {len(events)} 条事件", file=sys.stderr)
    else:
        events = fetch_events_via_query(args)
        print(f"查询获取 {len(events)} 条事件", file=sys.stderr)

    if not events:
        print("无事件数据，无法生成日历", file=sys.stderr)
        sys.exit(1)

    # 生成 HTML
    if generate_html(events, year, month, args.output):
        print(f"✓ 日历已生成: {args.output}（{len(events)} 条事件）", file=sys.stderr)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
