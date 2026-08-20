#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""赛程查询：默认以在线赛程源 worldcup26.ir 为准，拿不到再退回包内静态 JSON。
设计目标——彻底杜绝"把占位符(附加赛X)当真实对手"以及"凭印象编对阵"两类错误。

命令：
  schedule.py online                         # 拉在线源全量(标准化后)的 JSON，给上层 agent 用
  schedule.py team --name 葡萄牙              # 查某队全部对阵(优先在线源)
  schedule.py day  --date 2026-06-18         # 查北京时间某天的对阵(优先在线源)
  schedule.py opponent --name 葡萄牙 --next  # 查某队下一场未开赛对手

约定：
- 在线源 local_date 是赛事当地(美洲)时区。北京时间 = local_date + 1 天(凌晨/上午场)。
- 任何输出若仍含占位符(附加赛/胜者/TBD)，置 has_placeholder=true 并在 _warn 中提示必须 WebSearch 核实。
- 在线源拉取由上层 agent 用 WebFetch 完成后，把 JSON 文本通过 --online-json 传入；
  本脚本不直接发网络请求(运行环境无 requests 保障)，只做"标准化 + 优先级 + 占位符拦截"。
"""
import argparse, json, sys, re
from pathlib import Path
from datetime import datetime, timedelta

DATA = Path(__file__).resolve().parent.parent / "data"
STATIC = DATA / "national_teams_2026_schedule.json"
SCHEDULE_URL = "https://worldcup26.ir/get/games"

PLACEHOLDER_RE = re.compile(r"附加赛|胜者|待定|TBD|playoff|winner", re.I)

# 在线源英文队名 -> 中文(覆盖48强；缺失则原样保留并标记)
EN2CN = {
    "Portugal": "葡萄牙", "Democratic Republic of the Congo": "刚果（金）",
    "Congo DR": "刚果（金）", "DR Congo": "刚果（金）",
    "Uzbekistan": "乌兹别克斯坦", "Colombia": "哥伦比亚",
    "England": "英格兰", "Croatia": "克罗地亚", "Ghana": "加纳", "Panama": "巴拿马",
    "Mexico": "墨西哥", "South Korea": "韩国", "Korea Republic": "韩国",
    "South Africa": "南非", "Czech Republic": "捷克", "Czechia": "捷克",
    "Canada": "加拿大", "Qatar": "卡塔尔", "Switzerland": "瑞士",
    "Bosnia and Herzegovina": "波黑", "Bosnia": "波黑",
    "United States": "美国", "USA": "美国", "Australia": "澳大利亚",
    "Turkey": "土耳其", "Türkiye": "土耳其", "Paraguay": "巴拉圭",
    "Netherlands": "荷兰", "Japan": "日本", "Tunisia": "突尼斯", "Sweden": "瑞典",
    "France": "法国", "Senegal": "塞内加尔", "Norway": "挪威", "Iraq": "伊拉克",
    "Brazil": "巴西", "Morocco": "摩洛哥", "Haiti": "海地", "Scotland": "苏格兰",
    "Germany": "德国", "Curacao": "库拉索", "Curaçao": "库拉索",
    "Ivory Coast": "科特迪瓦", "Cote d'Ivoire": "科特迪瓦", "Ecuador": "厄瓜多尔",
    "Belgium": "比利时", "Egypt": "埃及", "Iran": "伊朗", "New Zealand": "新西兰",
    "Spain": "西班牙", "Cape Verde": "佛得角", "Cape Verde Islands": "佛得角",
    "Saudi Arabia": "沙特阿拉伯", "Uruguay": "乌拉圭",
    "Argentina": "阿根廷", "Algeria": "阿尔及利亚", "Austria": "奥地利", "Jordan": "约旦",
    "Italy": "意大利", "Denmark": "丹麦", "Wales": "威尔士",
}


def cn(name):
    return EN2CN.get(name, name)


def has_ph(*names):
    return any(PLACEHOLDER_RE.search(str(n) or "") for n in names)


def normalize_online(raw):
    """把 worldcup26.ir 的原始 games 列表标准化。raw 可为 list 或 {'games':[...]} 或整段。"""
    games = raw.get("games") if isinstance(raw, dict) else raw
    if not isinstance(games, list):
        # 尝试找第一个 list 值
        if isinstance(raw, dict):
            for v in raw.values():
                if isinstance(v, list):
                    games = v
                    break
    out = []
    for g in (games or []):
        home_en = g.get("home_team_name_en") or g.get("home_team_name") or g.get("home") or ""
        away_en = g.get("away_team_name_en") or g.get("away_team_name") or g.get("away") or ""
        ld = g.get("local_date") or g.get("date") or ""
        finished = str(g.get("finished", "")).upper() in ("TRUE", "1") or g.get("time_elapsed") == "finished"
        status = "finished" if finished else "notstarted"
        # 北京时间日期 = local_date + 1 天(凌晨/上午场约定)
        bj_date = ""
        m = re.search(r"(\d{2})/(\d{2})/(\d{4})", ld)
        if m:
            mm, dd, yy = m.group(1), m.group(2), m.group(3)
            try:
                d = datetime(int(yy), int(mm), int(dd)) + timedelta(days=1)
                bj_date = d.strftime("%Y-%m-%d")
            except ValueError:
                pass
        out.append({
            "home": cn(home_en), "away": cn(away_en),
            "home_en": home_en, "away_en": away_en,
            "group": g.get("group") or g.get("group_name") or "",
            "local_date": ld, "bj_date": bj_date, "status": status,
            "home_score": g.get("home_score"), "away_score": g.get("away_score"),
        })
    return out


def load_static():
    d = json.loads(STATIC.read_text(encoding="utf-8"))
    return d.get("group_stage", [])


def out(obj):
    print(json.dumps(obj, ensure_ascii=False, indent=2))


def get_games(args):
    """返回 (games, source)。优先在线源(由 --online-json 传入)，否则静态。"""
    if getattr(args, "online_json", None):
        try:
            raw = json.loads(Path(args.online_json).read_text(encoding="utf-8")) \
                if Path(args.online_json).exists() else json.loads(args.online_json)
            return normalize_online(raw), "online(worldcup26.ir)"
        except Exception as e:
            sys.stderr.write(f"[schedule] 在线源解析失败，退回静态: {e}\n")
    # 静态：把 group_stage 的 date(ISO 北京时间) 转成统一结构
    games = []
    for m in load_static():
        bj = ""
        mt = re.match(r"(\d{4}-\d{2}-\d{2})", m.get("date", ""))
        if mt:
            bj = mt.group(1)
        games.append({"home": m["home"], "away": m["away"], "group": m.get("group", ""),
                      "local_date": "", "bj_date": bj, "status": m.get("status", "notstarted"),
                      "iso": m.get("date", "")})
    return games, "static(包内JSON)"


def main():
    ap = argparse.ArgumentParser(description="赛程查询(在线源优先)")
    sub = ap.add_subparsers(dest="cmd", required=True)
    for c in ("online", "team", "day", "opponent"):
        p = sub.add_parser(c)
        p.add_argument("--online-json", help="WebFetch 拉到的在线源 JSON(文件路径或字符串)")
        if c == "team":
            p.add_argument("--name", required=True)
        if c == "day":
            p.add_argument("--date", required=True, help="北京时间 YYYY-MM-DD")
        if c == "opponent":
            p.add_argument("--name", required=True)
            p.add_argument("--next", action="store_true")
    args = ap.parse_args()

    games, source = get_games(args)
    warn = None
    if source.startswith("static"):
        warn = ("当前用的是包内静态赛程，可能滞后。强烈建议上层先用 WebFetch 拉 "
                f"{SCHEDULE_URL}，再用 --online-json 传入以在线源为准。")

    if args.cmd == "online":
        ph = [g for g in games if has_ph(g["home"], g["away"])]
        out({"ok": True, "source": source, "count": len(games), "games": games,
             "has_placeholder": bool(ph), "placeholder_games": ph,
             "_warn": warn or ("⚠️ 仍含占位符，必须 WebSearch 核实真实球队！" if ph else None),
             "schedule_url": SCHEDULE_URL})
        return

    if args.cmd in ("team", "opponent"):
        nm = args.name

        def hit(g, side):
            return nm in (g.get(side) or "") or nm in (g.get(side + "_en") or "")
        ms = [g for g in games if hit(g, "home") or hit(g, "away")]
        if args.cmd == "opponent":
            ns = [g for g in ms if g["status"] == "notstarted"]
            target = (ns[0] if ns else (ms[0] if ms else None))
            if not target:
                out({"ok": False, "source": source, "error": f"未找到 {nm} 的对阵", "_warn": warn})
                return
            opp = target["away"] if hit(target, "home") else target["home"]
            ph = has_ph(opp)
            out({"ok": True, "source": source, "team": nm, "opponent": opp,
                 "match": target, "has_placeholder": ph,
                 "_warn": ("🚨 对手是占位符，禁止直接使用，必须 WebSearch 核实真实晋级球队！"
                           if ph else warn)})
            return
        ph = any(has_ph(g["home"], g["away"]) for g in ms)
        out({"ok": True, "source": source, "team": nm, "count": len(ms), "matches": ms,
             "has_placeholder": ph, "_warn": (warn or ("🚨 含占位符，需 WebSearch 核实" if ph else None))})
        return

    if args.cmd == "day":
        ms = [g for g in games if g.get("bj_date") == args.date]
        ph = any(has_ph(g["home"], g["away"]) for g in ms)
        out({"ok": True, "source": source, "date_bj": args.date, "count": len(ms), "matches": ms,
             "has_placeholder": ph, "_warn": (warn or ("🚨 含占位符，需 WebSearch 核实" if ph else None))})
        return


if __name__ == "__main__":
    main()
