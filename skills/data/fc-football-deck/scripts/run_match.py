"""FC 国家队卡组对位推演 · 一键脚本

输入：engine + home + away
输出：渲染好的 HTML 文件路径

自动串联：pick_engine → lineup(home) → lineup(away) → match → nation_stats → 组装 JSON → validate → render

用法：
  python3 run_match.py --home 葡萄牙 --away 法国
  python3 run_match.py --engine mobile --home 阿根廷 --away 巴西 --output /tmp/match.html
  python3 run_match.py --engine fco --home 葡萄牙 --away 法国 --story "..." --conclusion "..."
"""
import argparse
import json
import subprocess
import sys
import os
import tempfile
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
ROOT = SCRIPTS.parent
QUERY = SCRIPTS / "query.py"
VALIDATE = SCRIPTS / "validate_input_spid.py"
RENDER = SCRIPTS / "render_html.py"
DATA = ROOT / "data"

PYTHON = sys.executable or "python3"

# 确保 Windows 下子进程也用 UTF-8
_SUBPROC_ENV = os.environ.copy()
_SUBPROC_ENV.setdefault("PYTHONIOENCODING", "utf-8")
if sys.platform == "win32":
    _SUBPROC_ENV.setdefault("PYTHONUTF8", "1")


def _run(script, args, stdin_data=None):
    """运行子脚本，返回 JSON 输出。Windows 下用 bytes 模式避免编码问题。"""
    cmd = [PYTHON, str(script)] + args
    stdin_bytes = stdin_data.encode("utf-8") if isinstance(stdin_data, str) else None
    r = subprocess.run(cmd, capture_output=True, input=stdin_bytes, env=_SUBPROC_ENV)
    if r.returncode != 0:
        print(f"[run_match] ERROR running {script.name}: {r.stderr.decode('utf-8', errors='replace')}", file=sys.stderr)
        sys.exit(1)
    stdout = r.stdout.decode("utf-8", errors="replace")
    try:
        return json.loads(stdout)
    except json.JSONDecodeError:
        print(f"[run_match] ERROR parsing output from {script.name}: {stdout[:500]}", file=sys.stderr)
        sys.exit(1)


def _run_render(input_data):
    """运行 render_html.py，传入 JSON via stdin，返回输出文件路径。"""
    cmd = [PYTHON, str(RENDER)]
    stdin_bytes = json.dumps(input_data, ensure_ascii=False).encode("utf-8")
    r = subprocess.run(cmd, capture_output=True, input=stdin_bytes, env=_SUBPROC_ENV)
    if r.returncode != 0:
        print(f"[run_match] RENDER ERROR: {r.stderr.decode('utf-8', errors='replace')}", file=sys.stderr)
        sys.exit(1)
    # render_html.py 输出文件路径
    return r.stdout.decode("utf-8", errors="replace").strip()


def _run_validate(input_data, tmp_path=None):
    """运行 validate_input_spid.py 校验 spid，失败则退出。"""
    if tmp_path is None:
        tmp_path = os.path.join(tempfile.gettempdir(), "_match_input_auto.json")
    p = Path(tmp_path)
    p.write_text(json.dumps(input_data, ensure_ascii=False), encoding="utf-8")
    cmd = [PYTHON, str(VALIDATE), str(p)]
    r = subprocess.run(cmd, capture_output=True, env=_SUBPROC_ENV)
    stdout = r.stdout.decode("utf-8", errors="replace")
    stderr = r.stderr.decode("utf-8", errors="replace")
    if r.returncode != 0:
        print(f"[run_match] SPID VALIDATION FAILED:\n{stdout}\n{stderr}", file=sys.stderr)
        sys.exit(1)
    print(f"[run_match] {stdout.strip()}", file=sys.stderr)


def _default_formation(nation):
    """从 national_formations.json 取该国默认阵型。"""
    try:
        formations = json.loads((DATA / "national_formations.json").read_text(encoding="utf-8"))
        return formations.get("nations", {}).get(nation, {}).get("default", "4-3-3")
    except Exception:
        return "4-3-3"


def main():
    parser = argparse.ArgumentParser(description="FC 国家队卡组对位推演一键脚本")
    parser.add_argument("--home", required=True, help="主队名（如 葡萄牙）")
    parser.add_argument("--away", required=True, help="客队名（如 法国）")
    parser.add_argument("--engine", choices=["fco", "mobile"], default=None,
                        help="引擎（不传则随机）")
    parser.add_argument("--output", default=None, help="输出 HTML 路径")
    # 可选的高级字段（AI 或用户传入）
    parser.add_argument("--conclusion", default="", help="综合结论文字")
    parser.add_argument("--story", default="", help="剧情卡 HTML 内容")
    parser.add_argument("--score-hint", default="", help="主比分（如 '2 : 1'）")
    parser.add_argument("--score-alts", nargs="*", default=[], help="其他可能比分（如 2:0 1:1），1-2 个即可")
    parser.add_argument("--overall", default="", help="综合倾向（如 '葡萄牙略优'）")
    parser.add_argument("--real-tendency", default="", help="现实倾向")
    parser.add_argument("--hook-line", default="", help="顶部一句话钩子（有画面感的看点金句）")
    parser.add_argument("--core-points", nargs="*", default=[], help="核心判断列表")
    parser.add_argument("--follow-ups", nargs="*", default=[], help="追问列表")
    parser.add_argument("--market", default=None,
                        help="赛前公开预测信号三档强度值(主胜,平,客胜)，如 '1.13,5.86,13.50'(值越小越被看好)。"
                             "作为现实因子核心透传给 query match；仅后端用、前端不外显。")
    args = parser.parse_args()

    # ---- Step 1: 锁定引擎 ----
    if args.engine:
        engine = args.engine
    else:
        pick = _run(QUERY, ["pick_engine"])
        engine = pick["engine"]
    engine_name = {"fco": "FC Online", "mobile": "FC 足球世界"}[engine]
    print(f"[run_match] 引擎: {engine} ({engine_name})", file=sys.stderr)

    # ---- Step 2: 查询数据 ----
    home_lineup = _run(QUERY, ["lineup", "--engine", engine, "--nation", args.home])
    away_lineup = _run(QUERY, ["lineup", "--engine", engine, "--nation", args.away])
    match_args = ["match", "--engine", engine, "--home", args.home, "--away", args.away]
    if args.market:
        match_args += ["--market", args.market]
    match_data = _run(QUERY, match_args)
    home_stats = _run(QUERY, ["nation_stats", "--engine", engine, "--nation", args.home])
    away_stats = _run(QUERY, ["nation_stats", "--engine", engine, "--nation", args.away])

    # 检查 lineup 是否成功
    if not home_lineup.get("ok"):
        print(f"[run_match] ERROR: 主队 {args.home} 查询失败: {home_lineup.get('error')}", file=sys.stderr)
        sys.exit(1)
    if not away_lineup.get("ok"):
        print(f"[run_match] ERROR: 客队 {args.away} 查询失败: {away_lineup.get('error')}", file=sys.stderr)
        sys.exit(1)

    home_formation = home_lineup.get("formation") or _default_formation(args.home)
    away_formation = away_lineup.get("formation") or _default_formation(args.away)

    # ---- Step 3: 组装渲染 JSON ----
    fallback = match_data.get("fallback_required", False)
    away_is_fallback = away_stats.get("fallback_required", False) or fallback

    # 倾向文字
    overall_text = args.overall or match_data.get("overall_tendency") or ""
    # 比分：优先用户手传；否则采用 query.py match 的确定性 suggested_score（同数据同结果，可复现）
    sugg = match_data.get("suggested_score") or {}
    score_hint = args.score_hint or sugg.get("main", "")
    score_alts = args.score_alts or sugg.get("alts", [])
    real_tendency = args.real_tendency

    # 构造球员列表（lineup 已含 spid/name/ovr/role/has_card_image）
    home_players = home_lineup.get("players", [])
    away_players = away_lineup.get("players", [])

    # 关键球员 → 焦点对决（取双方 OVR 最高的各一人）
    home_top = home_players[0] if home_players else None
    away_top = away_players[0] if away_players else None

    # 焦点对决骨架：带 spid+ovr（渲染器据此挂双方球星卡图）。
    # ⚠️ title / tilt_text 这里只生成"待梗化"占位，正式产出必须由 AI 按 references/duel_flavor.md
    #    改写成「闪电侠大战钢铁侠」式的直接梗化文案（不要"像XX一样"明喻）。
    _lore = {}
    try:
        _lore = json.loads((DATA / "player_lore.json").read_text(encoding="utf-8"))
    except Exception:
        _lore = {}

    def _lore_title(name):
        if name in _lore and not name.startswith("_"):
            return _lore[name].get("title", "")
        alias = _lore.get("_aliases", {}).get(name)
        if alias:
            return _lore.get(alias, {}).get("title", "")
        return ""

    key_matchups = []
    if home_top and away_top:
        hn, an = home_top.get("name", ""), away_top.get("name", "")
        key_matchups.append({
            "title": f"{hn} vs {an}",
            "home_side": {"name": hn, "spid": home_top.get("spid"), "ovr": home_top.get("ovr"),
                          "tag": _lore_title(hn)},
            "away_side": {"name": an, "spid": away_top.get("spid"), "ovr": away_top.get("ovr"),
                          "tag": _lore_title(an)},
            "tilt_text": f"[待梗化] {hn}(OVR {home_top.get('ovr')}) 对位 {an}(OVR {away_top.get('ovr')})，"
                         f"按 duel_flavor.md 直接写成名场面对决（如闪电侠大战钢铁侠），别用'像XX一样'明喻。"
        })

    # 关键连线
    key_links = []
    if len(home_players) >= 3:
        mid = home_players[len(home_players) // 2]
        key_links.append({
            "team": "home", "team_name": args.home,
            "chain": f"{mid.get('name', '')} → {home_top.get('name', '')}",
            "desc": f"中场组织到前锋终结的核心链路"
        })
    if len(away_players) >= 3:
        mid = away_players[len(away_players) // 2]
        key_links.append({
            "team": "away", "team_name": args.away,
            "chain": f"{mid.get('name', '')} → {away_top.get('name', '')}",
            "desc": f"中场组织到前锋终结的核心链路"
        })

    # 玩法建议
    playstyle = [
        {"team": args.home, "tip": f"推荐阵型 {home_formation}，围绕 {home_top.get('name', '核心球员')} 组织进攻" if home_top else f"推荐阵型 {home_formation}"},
        {"team": args.away, "tip": f"推荐阵型 {away_formation}，围绕 {away_top.get('name', '核心球员')} 组织进攻" if away_top else f"推荐阵型 {away_formation}"},
    ]

    # 核心判断
    core_points = args.core_points
    if not core_points and match_data.get("fc_tendency"):
        gt = match_data.get("group_tendency", {})
        core_points = [
            f"FC 数据倾向：{match_data['fc_tendency']}",
            f"前场对比：{gt.get('前场', '—')}",
            f"中场对比：{gt.get('中场', '—')}",
        ]

    # 追问
    follow_ups = args.follow_ups
    if not follow_ups:
        follow_ups = [
            f"详细分析 {home_top.get('name', args.home + '核心')} 的能力",
            f"围绕 {home_top.get('name', '')} 配一套 {args.home} 国家队套",
            f"{args.away} 反击打法怎么复刻？",
        ]

    season_tag = "世界之巅赛季" if engine == "mobile" else "PTG 赛季"

    # 🔥 噱头：从双方阵容 OVR 自动算「攻/中/防」战力对比骨架（渲染器据此画对比条）
    # 归一到 0~99 直观刻度（端游 OVR ~125、手游 ~145，用相对比例转成易读分数）
    def _line_avg(players, roles):
        vals = [p.get("ovr", 0) for p in players
                if any(r in (p.get("role") or "").upper() for r in roles) and isinstance(p.get("ovr"), (int, float))]
        return round(sum(vals) / len(vals), 1) if vals else 0

    def _to_score(ovr):
        if not ovr:
            return 0
        base = 145 if engine == "mobile" else 125
        return max(60, min(99, round(60 + (ovr - base + 8) * 2.4)))

    power_compare = []
    if home_players and away_players and not away_is_fallback:
        att_roles = ("ST", "CF", "LW", "RW", "LM", "RM")
        mid_roles = ("CM", "CDM", "CAM", "DM", "AM")
        def_roles = ("CB", "LB", "RB", "LWB", "RWB", "GK")
        for lbl, roles in [("进攻", att_roles), ("中场", mid_roles), ("防守", def_roles)]:
            hv = _to_score(_line_avg(home_players, roles))
            av = _to_score(_line_avg(away_players, roles))
            if hv and av:
                power_compare.append({"label": lbl, "home": hv, "away": av})

    input_json = {
        "engine": engine,
        "title": f"{args.home}国家队套 vs {args.away}国家队套",
        "subtitle": f"{engine_name} · {season_tag}卡组对位推演",
        "hook_line": args.hook_line or real_tendency or "",
        "power_compare": power_compare,
        "summary": {
            "real_tendency": real_tendency,
            "overall": overall_text,
            "score_hint": score_hint,
            "score_alts": score_alts,
        },
        "core_points": core_points,
        "home": {
            "name": args.home,
            "formation": home_formation,
            "players": home_players,
        },
        "away": {
            "name": args.away,
            "formation": away_formation,
            "is_fallback": away_is_fallback,
            "players": away_players,
        },
        "key_matchups": key_matchups,
        "key_links": key_links,
        "conclusion": args.conclusion,
        "story": args.story,
        "playstyle": playstyle,
        "follow_ups": follow_ups,
        "match_meta": {
            "round_label": "FC 国家队套对位",
            "squad_tier": season_tag + "强化档位",
            "deck_note": "满化学度国家队套",
            "focus_text": f"卡组对位 · {args.home} vs {args.away}",
        },
        "output_path": args.output or os.path.join(tempfile.gettempdir(), f"fco_{args.home}_{args.away}.html"),
    }

    # ---- Step 4: 校验 spid ----
    _run_validate(input_json)

    # ---- Step 5: 渲染 HTML ----
    html_path = _run_render(input_json)
    print(html_path)
    return html_path


if __name__ == "__main__":
    main()
