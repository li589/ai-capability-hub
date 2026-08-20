"""FC 国家队卡组对位推演 Skill 的核心查询脚本（双引擎）。

⚠️ 双引擎隔离（最重要）：
  - --engine fco    端游 FC Online（PTG 赛季，OVR 120~131 体系）
  - --engine mobile 手游 FC 足球世界（世界之巅赛季，OVR 138~150 + 六维 600~1050 体系）
  两套数值体系完全不同，绝不能在一次呈现里混用。
  每次推演由上层 Skill **临场随机**选一个 engine，不设固定默认。
  本脚本若不传 --engine，会自己随机选一个并在输出里回报 `engine` 字段。

用法：
  query.py squad --engine mobile --nation 葡萄牙 --top 11
  query.py player --engine fco --name C·罗纳尔多
  query.py match --engine mobile --home 葡萄牙 --away 法国
  query.py nation_stats --engine fco --nation 约旦
  query.py pick_engine          # 仅返回本次随机选中的引擎

输出统一为 JSON（stdout），便于上层 Skill 解析后组装回复。
"""
import argparse
import json
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"

# 端游 FC Online（PTG）
FCO_DB_PATH = DATA / "player_ptg_cache.json"
FCO_NATION_INDEX_PATH = DATA / "nation_index.json"
# 端游详细能力库（六维 / 分位置 / 特性，球员单点查询时合并进输出）
FCO_STATS_PATH = DATA / "player_ptg_stats.json"
# 手游 FC 足球世界
MOBILE_DB_PATH = DATA / "mobile_player_cache.json"
MOBILE_NATION_INDEX_PATH = DATA / "mobile_nation_index.json"
MOBILE_TEAM_OVR_PATH = DATA / "mobile_team_ovr.json"

ALIAS_PATH = DATA / "player_alias_map.json"
GROUPS_PATH = DATA / "national_teams_2026_groups.json"

ENGINE_META = {
    "fco": {"name": "FC Online", "label": "端游", "ovr_band": (120, 131)},
    "mobile": {"name": "FC 足球世界", "label": "手游", "ovr_band": (138, 150)},
}


def pick_engine(explicit=None):
    """显式优先；否则临场随机。"""
    if explicit in ("fco", "mobile"):
        return explicit
    return random.choice(["fco", "mobile"])


def engine_paths(engine):
    if engine == "mobile":
        return MOBILE_DB_PATH, MOBILE_NATION_INDEX_PATH
    return FCO_DB_PATH, FCO_NATION_INDEX_PATH


def _has_card_image(p):
    return bool(p.get("card_image"))


def dedup_starters(spids, db, n):
    """按球员名去重取前 n 张。
    手游同一球员有多张卡：**优先选有卡图的那张**（高强化 72 卡常常无图，会渲染成空白/错位），
    其次才比 OVR。这样邓弗里斯/范戴克/久保都能拿到带图的基础卡。
    能力数据已由 build 阶段从基础卡回填，无图高卡的六维并不会丢。"""
    # 先按球员名分组
    groups = {}
    order = []
    for s in spids:
        p = db.get(str(s))
        if not p:
            continue
        key = p.get("name_cn") or p.get("name_en") or str(s)
        if key not in groups:
            groups[key] = []
            order.append(key)
        groups[key].append(s)
    # 每名球员选代表卡：有图优先，其次 OVR 高
    res = []
    for key in order:
        cands = groups[key]
        cands.sort(key=lambda s: (_has_card_image(db[str(s)]), db[str(s)].get("ovr") or 0),
                   reverse=True)
        res.append(cands[0])
        if len(res) >= n:
            break
    return res


# 槽位 → 严格位置族（第一轮，本位/最贴近的位置）
_POS_STRICT = {
    "GK": {"GK"},
    "RB": {"RB", "RWB"}, "LB": {"LB", "LWB"},
    "RWB": {"RWB", "RB"}, "LWB": {"LWB", "LB"},
    "CB": {"CB", "RCB", "LCB"},
    "CDM": {"CDM"}, "CM": {"CM", "CAM", "CDM"},
    "CAM": {"CAM", "CM"},
    "RM": {"RM", "RW"}, "LM": {"LM", "LW"},
    "RW": {"RW", "RM"}, "LW": {"LW", "LM"},
    "CF": {"CF"}, "ST": {"ST", "CF"},
}
# 槽位 → 宽松位置族（第二轮，相邻位置可兼任，但不让前锋去踢后卫这种离谱）
_POS_LOOSE = {
    "GK": {"GK"},
    "RB": {"RB", "RWB", "RM", "CB"}, "LB": {"LB", "LWB", "LM", "CB"},
    "RWB": {"RWB", "RB", "RM"}, "LWB": {"LWB", "LB", "LM"},
    "CB": {"CB", "RCB", "LCB", "CDM"},
    "CDM": {"CDM", "CM"}, "CM": {"CM", "CDM", "CAM"},
    "CAM": {"CAM", "CM", "RW", "LW", "CF"},
    "RM": {"RM", "RW", "RWB", "CAM"}, "LM": {"LM", "LW", "LWB", "CAM"},
    "RW": {"RW", "RM", "CAM", "ST"}, "LW": {"LW", "LM", "CAM", "ST"},
    "CF": {"CF", "ST", "CAM"}, "ST": {"ST", "CF", "RW", "LW", "CAM"},
}


def pick_by_formation(spids, db, formation_slots):
    """三轮位置匹配填阵型 + OVR 兜底（久保 RM 不会被塞去后腰/边后卫）：
    第一轮严格本位，第二轮严格本位 + secondary_positions，第三轮宽松相邻兼任，最后剩余 OVR 兜底。
    返回 [(role, spid), ...]。"""
    cand = dedup_starters(spids, db, len(spids))
    used = set()
    filled = [None] * len(formation_slots)

    def _can_fill(rec, fam, use_secondary=False):
        pos = (rec.get("position") or "").upper()
        if pos in fam:
            return True
        if use_secondary:
            for sec in (rec.get("secondary_positions") or []):
                if str(sec).upper() in fam:
                    return True
        return False

    def try_fill(fam_map, use_secondary=False):
        for i, role in enumerate(formation_slots):
            if filled[i] is not None:
                continue
            fam = fam_map.get(role, {role})
            pool = [s for s in cand if s not in used and _can_fill(db[str(s)], fam, use_secondary)]
            pool.sort(key=lambda s: (_has_card_image(db[str(s)]), db[str(s)].get("ovr") or 0),
                      reverse=True)
            if pool:
                filled[i] = pool[0]
                used.add(pool[0])

    try_fill(_POS_STRICT, use_secondary=False)   # 第一轮：严格本位
    try_fill(_POS_STRICT, use_secondary=True)    # 第二轮：严格本位 + 副位置
    try_fill(_POS_LOOSE)                          # 第三轮：宽松相邻兼任
    # 第四轮：剩余球员"按位置相容度"兜底（不再无脑顺序塞，避免后卫被塞到边锋）
    # 🧤 GK 槽绝不用外野球员兜底：没有真门将卡时宁可留空（渲染层画空占位）。
    # 用线路距离（守线/中线/锋线）做相容打分：同线优先，越级（如 LB→RW）排最后，
    #   保证扎卡(LB) 不会被塞进 RW 这种跨线离谱位置。
    _LINE = {  # 每个位置归到一条线 + 左右倾向（用于兜底相容打分）
        "GK": ("gk", 0), "RB": ("def", 1), "RWB": ("def", 1), "LB": ("def", -1),
        "LWB": ("def", -1), "CB": ("def", 0), "RCB": ("def", 0), "LCB": ("def", 0),
        "CDM": ("mid", 0), "CM": ("mid", 0), "CAM": ("mid", 0), "DM": ("mid", 0), "AM": ("mid", 0),
        "RM": ("mid", 1), "LM": ("mid", -1),
        "RW": ("att", 1), "LW": ("att", -1), "ST": ("att", 0), "CF": ("att", 0),
    }
    _LINE_ORDER = {"gk": 0, "def": 1, "mid": 2, "att": 3}

    def _compat_cost(player_pos, slot_role):
        """球员真实位置填入某槽位的"别扭程度"，越小越合适。"""
        pl = _LINE.get((player_pos or "").upper(), ("mid", 0))
        sl = _LINE.get(slot_role, ("mid", 0))
        line_gap = abs(_LINE_ORDER[pl[0]] - _LINE_ORDER[sl[0]])  # 跨线惩罚（守↔锋=2，很重）
        side_gap = abs(pl[1] - sl[1])                            # 左右倾向不符的轻惩罚
        return line_gap * 10 + side_gap

    empty_idx = [i for i in range(len(filled))
                 if filled[i] is None and formation_slots[i] != "GK"]
    # 🧤 兜底池排除门将：GK 球员绝不被塞进外野槽（与"外野不填GK槽"对称）。
    #    否则替补门将(如巴西埃德森)会被硬塞进 LB 等外野位。门将只进 GK 槽。
    leftover = [s for s in cand if s not in used
                and (db[str(s)].get("position") or "").upper() != "GK"]
    # 贪心：每次给"最缺人的槽"挑"最相容且 OVR 高"的球员
    while empty_idx and leftover:
        best = None  # (cost, -ovr, slot_i, spid)
        for i in empty_idx:
            role = formation_slots[i]
            for s in leftover:
                cost = _compat_cost(db[str(s)].get("position"), role)
                ovr = db[str(s)].get("ovr") or 0
                key = (cost, -ovr)
                if best is None or key < best[0]:
                    best = (key, i, s)
        _, slot_i, spid = best
        filled[slot_i] = spid
        used.add(spid)
        empty_idx.remove(slot_i)
        leftover.remove(spid)
    # 返回时保留 GK 空槽信息：用 (role, None) 占位，让上层知道该位无真门将
    return [(formation_slots[i], filled[i]) for i in range(len(filled))]


def load_json(p):
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)


def out(obj):
    print(json.dumps(obj, ensure_ascii=False, indent=2))


# ---------- 实体解析 ----------

def resolve_player(name=None, alias=None, db=None, alias_map=None):
    """归一化球员输入 → 返回 player record 或 None。"""
    if alias:
        alias = alias.strip().lower()
        norm = alias_map.get("alias_to_name", {}).get(alias)
        if norm:
            name = norm
        else:
            # alias 没命中，尝试当作名字模糊匹配
            name = alias
    if not name:
        return None
    name = name.strip()
    # 精确
    for spid, p in db.items():
        if p["name_cn"] == name:
            return p
    # 包含匹配（处理"罗德里戈" vs "罗德里戈·戈伊斯"）
    matches = [p for p in db.values() if name in p["name_cn"] or p["name_cn"] in name]
    if len(matches) == 1:
        return matches[0]
    if len(matches) > 1:
        # 取 OVR 最高
        matches.sort(key=lambda x: x.get("ovr") or 0, reverse=True)
        return matches[0]
    return None


# ---------- 命令实现 ----------

def cmd_squad(args, db, nation_index, engine):
    nation = args.nation
    spids = nation_index.get(nation, [])
    if not spids:
        out({"ok": False, "engine": engine, "error": f"未找到国家队：{nation}",
             "available_nations": sorted(nation_index.keys())})
        return
    top = args.top or 11
    starters = dedup_starters(spids, db, top)
    players = [db[str(s)] for s in starters]
    out({
        "ok": True,
        "engine": engine,
        "engine_name": ENGINE_META[engine]["name"],
        "nation": nation,
        "card_count": len(spids),
        "returned": len(players),
        "players": players,
    })


def cmd_player(args, db, alias_map, engine):
    p = resolve_player(name=args.name, alias=args.alias, db=db, alias_map=alias_map)
    if not p:
        out({"ok": False, "engine": engine, "error": "球员未找到", "input": args.name or args.alias})
        return
    # 合并详细能力（六维 / 分位置 / 特性 / 主次位置），让单点查询能给出数据依据。
    # 端游：cache 只有基础字段，详细能力在 player_ptg_stats.json；手游：cache 本身已含 six/position_stats。
    p = dict(p)
    if engine == "fco":
        stats = load_json(FCO_STATS_PATH)
        s = stats.get(str(p.get("spid")))
        if isinstance(s, dict):
            for k in ("six_dims", "position_stats", "traits", "primary_position",
                      "secondary_positions", "weak_foot", "skill_moves", "body"):
                if s.get(k) is not None and p.get(k) is None:
                    p[k] = s[k]
    has_detail = bool(p.get("six_dims") or p.get("six"))
    out({"ok": True, "engine": engine, "engine_name": ENGINE_META[engine]["name"],
         "has_detail_stats": has_detail, "player": p})


# 常见阵型槽位预设（按 role 顺序）
_FORMATION_SLOTS = {
    "4-3-3": ["GK", "RB", "CB", "CB", "LB", "CDM", "CM", "CM", "RW", "ST", "LW"],
    "4-2-3-1": ["GK", "RB", "CB", "CB", "LB", "CDM", "CDM", "RM", "CAM", "LM", "ST"],
    "4-4-2": ["GK", "RB", "CB", "CB", "LB", "RM", "CM", "CM", "LM", "ST", "ST"],
    "3-5-2": ["GK", "CB", "CB", "CB", "RM", "CM", "CM", "CM", "LM", "ST", "ST"],
    "4-3-2-1": ["GK", "RB", "CB", "CB", "LB", "CDM", "CM", "CM", "CAM", "CAM", "ST"],
    "5-4-1": ["GK", "RWB", "CB", "CB", "CB", "LWB", "RM", "CM", "CM", "LM", "ST"],
}


def _best_formation(spids, db):
    """根据该队可用卡的位置分布，挑一个"错位最少"的阵型。
    用 pick_by_formation 实跑每个候选阵型，统计跨线错位 + 空槽，取代价最小者。
    保证如瑞士(无 RW、左倾)这类队不会被硬塞进需要纯右边锋的 4-3-3。"""
    _LINE = {
        "GK": "gk", "RB": "def", "RWB": "def", "LB": "def", "LWB": "def",
        "CB": "def", "RCB": "def", "LCB": "def",
        "CDM": "mid", "CM": "mid", "CAM": "mid", "DM": "mid", "AM": "mid", "RM": "mid", "LM": "mid",
        "RW": "att", "LW": "att", "ST": "att", "CF": "att",
    }
    _ORDER = {"gk": 0, "def": 1, "mid": 2, "att": 3}
    best_f, best_cost = "4-3-3", 1e9
    # 候选顺序：常见优先，同代价时偏向靠前的
    for f in ("4-3-3", "4-2-3-1", "4-4-2", "3-5-2", "4-3-2-1", "5-4-1"):
        slots = _FORMATION_SLOTS[f]
        pairs = pick_by_formation(spids, db, slots)
        cost = 0
        for role, s in pairs:
            if s is None:
                if role != "GK":      # GK 缺位不惩罚（无门将卡是普遍情况，不影响选阵型）
                    cost += 6
                continue
            pos = (db[str(s)].get("position") or "").upper()
            gap = abs(_ORDER.get(_LINE.get(pos, "mid"), 2) - _ORDER.get(_LINE.get(role, "mid"), 2))
            cost += gap * gap        # 跨线越远惩罚越重（守↔锋=9）
        if cost < best_cost:
            best_cost, best_f = cost, f
    return best_f


def cmd_lineup(args, db, nation_index, engine):
    """返回按阵型位置匹配好的首发 11 人（role + 球员 + 是否有卡图），直接喂给渲染器。"""
    nation = args.nation
    spids = nation_index.get(nation, [])
    if not spids:
        out({"ok": False, "engine": engine, "error": f"未找到国家队：{nation}",
             "available_nations": sorted(nation_index.keys())})
        return
    # 阵型：用户显式指定就用指定的；否则自动挑"位置最契合"的阵型（避免硬套 4-3-3
    # 导致右边锋这种缺位被乱填，如瑞士无 RW 时不该选需要 RW 的阵型）。
    if args.formation:
        formation = args.formation
    else:
        formation = _best_formation(spids, db)
    slots = _FORMATION_SLOTS.get(formation, _FORMATION_SLOTS["4-3-3"])
    pairs = pick_by_formation(spids, db, slots)
    players = []
    empty_slots = []  # 没匹配到真实球员的槽位（主要是无门将卡时的 GK 槽）
    for role, s in pairs:
        if s is None:
            # 槽位空缺（如该队无门将卡）：不塞外野球员，标记给渲染层画占位
            empty_slots.append(role)
            players.append({
                "spid": None, "name": None, "ovr": None,
                "role": role, "position": None,
                "has_card_image": False, "empty": True,
            })
            continue
        p = db[str(s)]
        players.append({
            "spid": s,
            "name": p.get("name_cn"),
            "ovr": p.get("ovr"),
            "role": role,
            "position": p.get("position"),
            "has_card_image": bool(p.get("card_image")),
        })
    out({
        "ok": True,
        "engine": engine,
        "engine_name": ENGINE_META[engine]["name"],
        "nation": nation,
        "formation": formation,
        "players": players,
        "empty_slots": empty_slots,
        "_note": ("有空缺槽位（如 GK）：该队在本引擎下无对应位置的真实卡，"
                  "渲染时画空占位，绝不用外野球员顶替。") if empty_slots else "",
    })


def cmd_nation_stats(args, db, nation_index, groups, engine):
    nation = args.nation
    spids = nation_index.get(nation, [])
    # 手游覆盖很全，几乎不触发兜底；端游沿用 no_or_low_ptg 名单
    no_low = groups.get("no_or_low_ptg", {}) if engine == "fco" else {}
    is_low = nation in no_low or len(spids) < 11
    out({
        "ok": True,
        "engine": engine,
        "engine_name": ENGINE_META[engine]["name"],
        "nation": nation,
        "card_count": len(spids),
        "is_low_coverage": is_low,
        "fallback_required": is_low,
        "fallback_hint": "卡组深度不足，建议走通用话术：『FC 近千场后台模拟比赛预估，分析可能是……』+ 公开数据支撑" if is_low else None,
        "ovr_distribution": _ovr_dist(spids, db),
    })


def _ovr_dist(spids, db):
    if not spids:
        return {}
    ovrs = [db[str(s)].get("ovr") or 0 for s in spids]
    return {
        "max": max(ovrs),
        "min": min(ovrs),
        "avg": round(sum(ovrs) / len(ovrs), 1),
        "ge_125": sum(1 for o in ovrs if o >= 125),
        "ge_130": sum(1 for o in ovrs if o >= 130),
    }


def _avg_top_n_ovr(spids, db, n):
    if not spids:
        return 0
    ovrs = sorted([db[str(s)].get("ovr") or 0 for s in spids], reverse=True)[:n]
    return round(sum(ovrs) / max(len(ovrs), 1), 2)


def parse_market_signal(signal_arg):
    """把「赛前公开预测信号」三档强度值解析成归一化的现实倾向概率(home_win/draw/away_win)。
    入参为三个公开预测强度值(主胜/平/客胜)，值越小代表该结果越被看好，例如 '1.13,5.86,13.50'。
    转换：强度倒数 = 1/值 → 三项归一(去除冗余度)得到现实倾向概率分布。
    解析失败返回 None(链路回退纯卡组，不报错)。这是现实因子的底层信号，仅后端融合、前端不外显。"""
    if not signal_arg:
        return None
    import re as _re
    nums = _re.findall(r"\d+\.?\d*", str(signal_arg))
    nums = [float(x) for x in nums if float(x) > 1.0]
    if len(nums) < 3:
        return None
    home_v, draw_v, away_v = nums[0], nums[1], nums[2]
    raw = {"home_win": 1.0 / home_v, "draw": 1.0 / draw_v, "away_win": 1.0 / away_v}
    s = sum(raw.values()) or 1
    return {k: round(v / s, 3) for k, v in raw.items()}


def label_from_probs(probs, home, away):
    """由三方概率反推倾向标签(5档)，用于融合现实信号后重判'谁占优'。"""
    hw, dw, aw = probs["home_win"], probs["draw"], probs["away_win"]
    strong, weak = (hw, aw) if hw >= aw else (aw, hw)
    side = home if hw >= aw else away
    gap = strong - weak
    if abs(hw - aw) < 0.06:
        return "势均力敌"
    if gap < 0.15:
        return f"{side}略优"
    if gap < 0.30:
        return f"{side}小优"
    if gap < 0.50:
        return f"{side}明显占优"
    return f"{side}碾压优势"


def cmd_match(args, db, nation_index, groups, engine):
    home, away = args.home, args.away
    home_spids = nation_index.get(home, [])
    away_spids = nation_index.get(away, [])

    # 手游覆盖很全，几乎不触发兜底；端游沿用 no_or_low_ptg 名单
    no_low = groups.get("no_or_low_ptg", {}) if engine == "fco" else {}
    home_low = home in no_low or len(home_spids) < 11
    away_low = away in no_low or len(away_spids) < 11

    # 去重取首发（手游同一球员多张卡，只留最高 OVR 那张），评分与关键球员都基于首发
    home_spids = dedup_starters(home_spids, db, 11)
    away_spids = dedup_starters(away_spids, db, 11)

    # 轻量评分模型（P0 简化版）：用 top11 平均 OVR 作为 FC 分组能力因子
    home_fc = _avg_top_n_ovr(home_spids, db, 11)
    away_fc = _avg_top_n_ovr(away_spids, db, 11)

    # 分组对比：取前场=top3、中场=4-7、后防=8-10、门将=top1 GK 假设按 OVR 排序粗略代理
    def group_score(spids, ranges):
        return {
            grp: _avg_top_n_ovr(spids[start:end], db, end - start)
            for grp, (start, end) in ranges.items()
        }
    ranges = {"前场": (0, 3), "中场": (3, 7), "后防": (7, 10), "门将": (10, 11)}
    home_groups = group_score(home_spids, ranges)
    away_groups = group_score(away_spids, ranges)

    # 倾向语言化 v2：5 档 + 三方概率（主胜/平/客胜）。阈值随引擎数值体系缩放（手游 OVR 跨度更大）
    scale = 2.2 if engine == "mobile" else 1.0

    def tendency_v2(a, b, label_a, label_b):
        """v2：返回 (倾向文字, 三方概率dict)。差值越小平局概率越高（参考五大联赛平局率~25%）。"""
        diff = a - b
        abs_diff = abs(diff)
        if abs_diff < 0.3 * scale:
            draw_prob = 0.32
            stronger_prob = 0.34 + abs_diff / (0.3 * scale) * 0.05
            weaker_prob = 1.0 - draw_prob - stronger_prob
            label = "势均力敌"
        elif abs_diff < 0.8 * scale:
            draw_prob = max(0.25, 0.30 - (abs_diff - 0.3 * scale) / (0.5 * scale) * 0.05)
            stronger_prob = 0.38 + (abs_diff - 0.3 * scale) / (0.5 * scale) * 0.07
            weaker_prob = 1.0 - draw_prob - stronger_prob
            label = f"{label_a if diff > 0 else label_b}略优"
        elif abs_diff < 1.5 * scale:
            draw_prob = max(0.18, 0.25 - (abs_diff - 0.8 * scale) / (0.7 * scale) * 0.07)
            stronger_prob = 0.45 + (abs_diff - 0.8 * scale) / (0.7 * scale) * 0.10
            weaker_prob = 1.0 - draw_prob - stronger_prob
            label = f"{label_a if diff > 0 else label_b}小优"
        elif abs_diff < 3.0 * scale:
            draw_prob = max(0.10, 0.18 - (abs_diff - 1.5 * scale) / (1.5 * scale) * 0.08)
            stronger_prob = 0.55 + (abs_diff - 1.5 * scale) / (1.5 * scale) * 0.15
            weaker_prob = 1.0 - draw_prob - stronger_prob
            label = f"{label_a if diff > 0 else label_b}明显占优"
        else:
            draw_prob = max(0.05, 0.10 - (abs_diff - 3.0 * scale) * 0.01)
            stronger_prob = min(0.85, 0.70 + (abs_diff - 3.0 * scale) * 0.02)
            weaker_prob = max(0.05, 1.0 - draw_prob - stronger_prob)
            label = f"{label_a if diff > 0 else label_b}碾压优势"
        stronger_prob = max(0, stronger_prob); weaker_prob = max(0, weaker_prob); draw_prob = max(0, draw_prob)
        total = stronger_prob + draw_prob + weaker_prob
        probs = {
            "home_win": round((stronger_prob if diff > 0 else weaker_prob) / total, 3),
            "draw": round(draw_prob / total, 3),
            "away_win": round((weaker_prob if diff > 0 else stronger_prob) / total, 3),
        }
        return label, probs

    def defense_adjusted_probs(base_probs, hg, ag, scale):
        """双方后防+门将均强且接近 → 平局概率上浮（防守稳固进球少更易平）。"""
        home_def = (hg.get("后防", 0) + hg.get("门将", 0)) / 2
        away_def = (ag.get("后防", 0) + ag.get("门将", 0)) / 2
        def_diff = abs(home_def - away_def)
        if home_def > 126 * scale and away_def > 126 * scale and def_diff < 1.0 * scale:
            adj = 0.04
        elif home_def > 125 * scale and away_def > 125 * scale and def_diff < 1.5 * scale:
            adj = 0.02
        else:
            adj = 0.0
        if adj > 0:
            probs = dict(base_probs)
            probs["draw"] = min(0.40, probs["draw"] + adj)
            if probs["home_win"] >= probs["away_win"]:
                probs["home_win"] = max(0.05, probs["home_win"] - adj)
            else:
                probs["away_win"] = max(0.05, probs["away_win"] - adj)
            total = probs["home_win"] + probs["draw"] + probs["away_win"]
            return {k: round(v / total, 3) for k, v in probs.items()}
        return base_probs

    # 兜底场景：任一队 PTG 卡 < 11，FC 数据维度不可比（样本不对等），倾向字段置空
    if home_low or away_low:
        fc_tendency = None
        group_tendency = None
        overall = None
        draw_probability = None
        three_way_probs = None
    else:
        fc_tendency, fc_probs = tendency_v2(home_fc, away_fc, home, away)
        fc_probs = defense_adjusted_probs(fc_probs, home_groups, away_groups, scale)
        group_tendency = {g: tendency_v2(home_groups[g], away_groups[g], home, away)[0]
                          for g in ranges.keys()}
        overall = fc_tendency
        # ---- 现实因子：赛前公开预测信号融合（底层逻辑，前端绝不外显）----
        # 赛前公开预测信号是经大数据综合定型的现实预判，信息质量最高 → 作为「现实比赛因子」核心。
        # 把三档强度值 → 归一化现实倾向概率，与 FC 卡组概率按权重融合。
        # 权重对齐 scoring_model.md：现实因子(以公开预测为核心)45% + FC 卡组30% → 融合时现实占 0.6、卡组占 0.4。
        market_prob = parse_market_signal(getattr(args, "market", None))
        if market_prob:
            W_REAL = 0.6   # 现实(公开预测)主导
            blended = {
                "home_win": fc_probs["home_win"] * (1 - W_REAL) + market_prob["home_win"] * W_REAL,
                "draw":     fc_probs["draw"]     * (1 - W_REAL) + market_prob["draw"]     * W_REAL,
                "away_win": fc_probs["away_win"] * (1 - W_REAL) + market_prob["away_win"] * W_REAL,
            }
            tot = sum(blended.values()) or 1
            fc_probs = {k: round(v / tot, 3) for k, v in blended.items()}
            # 倾向标签随融合后概率重判（让"谁占优"也反映现实信号）
            overall = label_from_probs(fc_probs, home, away)
        draw_probability = fc_probs["draw"]
        three_way_probs = fc_probs

    # 平局概率 >=25% 或"势均力敌"时，标记需要 WebSearch 补现实信号（后端三合一融合，前端不外显）
    real_world_search_required = (
        (draw_probability is not None and draw_probability >= 0.25)
        or (fc_tendency == "势均力敌")
    )

    # ---- 比分推算（确定性 · v1.4.4）----
    # 由"实力差 + 三方概率"直接映射出推荐主比分 + 1-2 备选，纯函数：同数据 → 同比分，
    # 杜绝手填随意性（曾出现同对阵两次手填 3:0 / 2:0 不一致）。
    # 注意：这是「卡组对决可能打出的比分」，不是现实赛果预测；real_world_search_required=true 时，
    # 上层仍需 WebSearch 现实信号后，可在 suggested 基础上微调。
    suggested_score = None
    if three_way_probs is not None:
        diff = round(home_fc - away_fc, 2)
        ad = abs(diff)
        hw, dw = three_way_probs["home_win"], three_way_probs["draw"]
        aw = three_way_probs["away_win"]
        # 比分档位由两路信号取强者决定：
        #  ① 卡组实力差 gap（FC 数据维度）
        #  ② 三方概率的"胜方压制度" prob_gap（融合现实信号后会显著放大）
        # 这样现实信号接入后，强弱悬殊的场（如主胜率 65%+）能正确拉高净胜球档，而不被卡组低估锁死。
        gap = ad / scale

        def margin_from_gap(g):
            if g < 0.3:
                return 0
            if g < 0.8:
                return 1
            if g < 1.5:
                return 1
            if g < 3.0:
                return 2
            return 3
        # 胜方概率优势 → 档位（与五大联赛常见净胜球分布对齐）
        prob_dom = max(hw, aw) - min(hw, aw)   # 主客胜率差，越大越一边倒
        if max(hw, aw) < 0.40 or prob_dom < 0.10:
            margin_prob = 0
        elif prob_dom < 0.25:
            margin_prob = 1
        elif prob_dom < 0.45:
            margin_prob = 2
        else:
            margin_prob = 3
        main_margin = max(margin_from_gap(gap), margin_prob)
        ALT = {0: [1], 1: [0, 2], 2: [1, 3], 3: [2, 4]}
        alt_margins = ALT.get(main_margin, [1])
        # 强队基础进球数：差距越大、对方防线越弱进越多；平局概率高则压低
        strong_goals = {0: 1, 1: 2, 2: 2, 3: 3}.get(main_margin, 2)
        if dw >= 0.25 and main_margin >= 2:
            strong_goals = max(2, strong_goals - 1)  # 焦灼(平局率高)时净胜球同档但少进一个
        weak_goals = max(0, strong_goals - main_margin)
        # 胜方：现实信号/概率融合后由 home_win vs away_win 决定（比纯卡组实力差更可信）
        home_strong = hw >= aw if (abs(hw - aw) > 0.02) else (diff >= 0)

        def fmt(sg, wg):
            return f"{sg} : {wg}" if home_strong else f"{wg} : {sg}"
        if main_margin == 0:
            # 势均力敌：主比分给平局，备选给双方各小胜一球
            main_score = "1 : 1"
            alts = ["2 : 1", "1 : 0"] if home_strong else ["1 : 2", "0 : 1"]
        else:
            main_score = fmt(strong_goals, weak_goals)
            alts = []
            for m in alt_margins:
                sg2 = {0: 1, 1: 2, 2: 2, 3: 3}.get(m, strong_goals)
                wg2 = max(0, sg2 - m)
                s = "1 : 1" if m == 0 else fmt(sg2, wg2)
                if s != main_score and s not in alts:
                    alts.append(s)
        suggested_score = {
            "main": main_score,
            "alts": alts[:2],
            "margin": main_margin,
            "basis": f"实力差 {diff}（归一 {round(gap,2)}）· 主胜率 {hw} · 平局率 {dw} · {overall}",
            "_note": "卡组对决可能打出的比分，非现实赛果预测；real_world_search_required=true 时可结合现实信号微调。",
        }

    # 关键球员（前 5）
    def key_players(spids, n=5):
        return [{
            "name": db[str(s)]["name_cn"],
            "ovr": db[str(s)]["ovr"],
            "card_image": db[str(s)]["card_image"],
        } for s in spids[:n]]

    out({
        "ok": True,
        "engine": engine,
        "engine_name": ENGINE_META[engine]["name"],
        "engine_label": ENGINE_META[engine]["label"],
        "match": f"{home} vs {away}",
        "fallback_required": home_low or away_low,
        "fallback_teams": [t for t, low in [(home, home_low), (away, away_low)] if low],
        "coverage": {home: len(home_spids), away: len(away_spids)},
        "fc_data_score": {home: home_fc, away: away_fc},
        "fc_tendency": fc_tendency,
        "draw_probability": draw_probability,
        "three_way_probs": three_way_probs,
        "suggested_score": suggested_score,
        "real_signal_blended": bool(parse_market_signal(getattr(args, "market", None))),
        "real_world_search_required": real_world_search_required,
        "group_score_home": home_groups,
        "group_score_away": away_groups,
        "group_tendency": group_tendency,
        "key_players": {home: key_players(home_spids), away: key_players(away_spids)},
        "overall_tendency": overall,
        "_note": ("引擎=" + ENGINE_META[engine]["name"] +
                  "。v2 评分含三方概率(three_way_probs:主胜/平/客胜)+平局档。"
                  "real_world_search_required=true 时，上层 Skill 必须 WebSearch 双方近期正式比赛结果/状态/伤停"
                  "（后端三合一：FC卡组 + 现实信号 + 公开倾向 融合得比分；**前端只外显『卡组对决比分结果』口径，不外显具体外部来源**）。"
                  "0-100 分位与 OVR 仅内部参考，绝不把分数当比分。两套引擎数值体系不同，绝不混用。"),
    })


# ---------- main ----------

def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd", required=True)

    # 仅返回本次随机选中的引擎（上层 Skill 先调它锁定引擎，后续查询都带上同一个 engine）
    sub.add_parser("pick_engine")

    def add_engine(p):
        p.add_argument("--engine", choices=["fco", "mobile"], default=None,
                       help="不传则临场随机；上层 Skill 应先 pick_engine 再固定传同一个")

    p_squad = sub.add_parser("squad")
    p_squad.add_argument("--nation", required=True)
    p_squad.add_argument("--top", type=int, default=11)
    add_engine(p_squad)

    p_player = sub.add_parser("player")
    p_player.add_argument("--name")
    p_player.add_argument("--alias")
    add_engine(p_player)

    p_match = sub.add_parser("match")
    p_match.add_argument("--home", required=True)
    p_match.add_argument("--away", required=True)
    p_match.add_argument("--market", default=None,
                         help="赛前公开预测信号三档强度值(主胜,平,客胜)，如 '1.13,5.86,13.50'(值越小越被看好)。"
                              "作为现实因子核心融入概率/比分；仅后端用、前端不外显。可省略(回退纯卡组)。")
    add_engine(p_match)

    p_ns = sub.add_parser("nation_stats")
    p_ns.add_argument("--nation", required=True)
    add_engine(p_ns)

    p_lu = sub.add_parser("lineup")
    p_lu.add_argument("--nation", required=True)
    p_lu.add_argument("--formation", default="4-3-3")
    add_engine(p_lu)

    args = parser.parse_args()

    if args.cmd == "pick_engine":
        e = pick_engine()
        out({"ok": True, "engine": e, "engine_name": ENGINE_META[e]["name"],
             "engine_label": ENGINE_META[e]["label"],
             "_note": "本次推演锁定该引擎，后续所有 query 都用 --engine " + e + "，不要中途换引擎。"})
        return

    engine = pick_engine(getattr(args, "engine", None))
    db_path, idx_path = engine_paths(engine)
    db = load_json(db_path)
    nation_index = load_json(idx_path)
    alias_map = load_json(ALIAS_PATH)
    groups = load_json(GROUPS_PATH)

    if args.cmd == "squad":
        cmd_squad(args, db, nation_index, engine)
    elif args.cmd == "player":
        cmd_player(args, db, alias_map, engine)
    elif args.cmd == "match":
        cmd_match(args, db, nation_index, groups, engine)
    elif args.cmd == "nation_stats":
        cmd_nation_stats(args, db, nation_index, groups, engine)
    elif args.cmd == "lineup":
        cmd_lineup(args, db, nation_index, engine)


if __name__ == "__main__":
    main()
