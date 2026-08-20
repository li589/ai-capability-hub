"""把 FC 国家队卡组对位推演渲染成自包含 HTML（图片用 base64 内嵌）。

⚠️ 性质与合规口径：本工具是 FC 爱好者基于游戏内公开数据自行开发的第三方作品，
   非 FC / 腾讯 / EA / FIFA 任何一方的官方产品，也未获其授权。产出的所有内容均为
   游戏内国家队卡组的纸面数据演绎，不构成对任何现实赛事结果的预测；不与现实赛程、赛果、官方版权产生关联。

核心能力：
- 顶部对阵元信息卡（FC 内对阵编排 / 卡组档位 / 阵容标签）
- 阵型图 SVG（4-3-3 / 4-2-3-1 / 3-5-2 等 6 种），球员卡面挂位置
- 球员弹窗：六维雷达图、特性中文标签、详细分位置能力表、球员信息面板原图
- 焦点对决（海报式单卡）+ 焦点组合（双方各 1 条核心链路）
- 卡组演绎剧情（游戏内模拟对战风格的剧情卡）
"""
import base64
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FORMATIONS_PATH = ROOT / "data/national_formations.json"
LORE_PATH = ROOT / "data/player_lore.json"

# ---- 双引擎资源路径 ----
# 端游 FC Online（PTG）
FCO_CARDS_DIR = ROOT / "assets/cards"
FCO_PANELS_DIR = ROOT / "assets/panels"
FCO_DB_PATH = ROOT / "data/player_ptg_cache.json"
FCO_STATS_PATH = ROOT / "data/player_ptg_stats.json"
# 手游 FC 足球世界
MOBILE_CARDS_DIR = ROOT / "assets/mobile_cards"
MOBILE_DB_PATH = ROOT / "data/mobile_player_cache.json"

# 引擎元信息（影响页眉徽章、品牌条、CTA 文案）
ENGINE_INFO = {
    "fco": {
        "name": "FC Online", "label": "端游", "badge": "PTG",
        "source_line": "数据取自 FC Online · PTG 赛季游戏内公开卡组",
        "endorse": "全球海量球员数据 · 国家队卡组全档位覆盖 · 八强强化总评 · 六维 + 12 项分位置能力 + 持有/金特性",
        "cta_url": "https://fco.qq.com/main.shtml",
        "cta_cloud": "https://start.qq.com/game/special-all/index.html?ADTAG=web-fco-guanwang#/fco",
    },
    "mobile": {
        "name": "FC 足球世界", "label": "手游", "badge": "TWG",
        "source_line": "数据取自 FC 足球世界 · 世界之巅赛季游戏内公开球员库",
        "endorse": "全球海量球员数据 · 国家队全覆盖 · 世界之巅强化总评 · 六维能力 + 特性",
        "cta_url": "https://fcmobile.qq.com/",
        "cta_cloud": "",
    },
}


def _load(p):
    try:
        return json.loads(Path(p).read_text(encoding="utf-8"))
    except Exception:
        return {}


# ---- 当前激活引擎（默认端游，可由输入 JSON 的 engine 字段切换）----
ENGINE = "fco"
CARDS_DIR = FCO_CARDS_DIR
PANELS_DIR = FCO_PANELS_DIR
_DB = _load(FCO_DB_PATH)
_STATS = _load(FCO_STATS_PATH)
_FORMATIONS = _load(FORMATIONS_PATH)
_LORE = _load(LORE_PATH)


def _lore_for(name):
    """按球员中文名（可能带前缀如 'J. 贝林厄姆'）查梗库；先精确、再别名、再规范化子串。"""
    if not name or not _LORE:
        return None
    if name in _LORE and not name.startswith("_"):
        return _LORE[name]
    aliases = _LORE.get("_aliases", {})
    if name in aliases:
        return _LORE.get(aliases[name])
    # 规范化：去前缀字母点、空格、间隔号后做姓氏子串匹配
    import re as _re
    def norm(s):
        s = _re.sub(r'^[A-Za-z]\.\s*', '', s or '')
        return s.replace('·', '').replace('.', '').replace(' ', '')
    nn = norm(name)
    for k in _LORE:
        if k.startswith("_"):
            continue
        kk = norm(k)
        if kk and (kk == nn or (len(kk) >= 2 and (kk in nn or nn in kk))):
            return _LORE[k]
    for alias, key in aliases.items():
        if norm(alias) == nn:
            return _LORE.get(key)
    return None


def _lore_map_for_players(players):
    """给一组球员（含 name/name_cn）生成 {显示名: lore} 映射，供 JS 画像/剧情用。"""
    out = {}
    for p in players or []:
        nm = p.get("name") or p.get("name_cn")
        lo = _lore_for(nm)
        if lo:
            out[nm] = {k: v for k, v in lo.items() if not k.startswith("_")}
    return out


def _mobile_rec_to_stats(rec):
    """把手游 cache 一条记录转成渲染器统一的 stats 结构。
    cache 已含中文 six(0~99) / position_stats(扁平中文 0~99) / trait(空格串) / wfa / skill_moves。
    渲染 JS 要求：six_dims={名:值}、position_stats={位置名:{项:值}}、traits=[{name,type}]。"""
    six = {k: v for k, v in (rec.get("six") or {}).items() if v is not None}
    if not six:
        return None
    pos_flat = {k: v for k, v in (rec.get("position_stats") or {}).items() if v is not None}
    position_stats = {}
    if pos_flat:
        # 用主位置名做分组键，符合 JS 的嵌套结构
        pos_label = rec.get("position") or "主位置"
        position_stats = {f"{pos_label} 详细能力": pos_flat}
    traits = [{"name": t, "type": "持有特性"}
              for t in (rec.get("trait") or "").split() if t]
    return {
        "six_dims": six,
        "position_stats": position_stats,
        "traits": traits,
        "weak_foot": rec.get("wfa"),
        "skill_moves": rec.get("skill_moves"),
    }


def set_engine(engine):
    """切换激活引擎，重配 DB / 卡图目录 / 详细能力数据。"""
    global ENGINE, CARDS_DIR, PANELS_DIR, _DB, _STATS
    if engine == "mobile":
        ENGINE = "mobile"
        CARDS_DIR = MOBILE_CARDS_DIR
        PANELS_DIR = None  # 手游无信息面板图
        _DB = _load(MOBILE_DB_PATH)
        # 手游 STATS 从 cache 现场构建（六维/分位置/特性都来自 xlsx）
        _STATS = {pid: s for pid, rec in _DB.items()
                  if (s := _mobile_rec_to_stats(rec))}
    else:
        ENGINE = "fco"
        CARDS_DIR = FCO_CARDS_DIR
        PANELS_DIR = FCO_PANELS_DIR
        _DB = _load(FCO_DB_PATH)
        _STATS = _load(FCO_STATS_PATH)
    reset_img_registry()

# 内部字段名单（不渲染到用户可见层 - 详见 references/safety_policy.md 第 8 节）
_INTERNAL_KEYS = {"_synthesized", "_note", "_data_source", "fallback_required",
                  "stats_recorded", "data_source", "_internal", "_six_from"}

def _filter_internal_stats(stats_dict):
    """递归过滤 STATS_DB 中的所有内部字段，避免泄漏到 HTML"""
    if isinstance(stats_dict, dict):
        return {k: _filter_internal_stats(v) for k, v in stats_dict.items()
                if not (isinstance(k, str) and (k.startswith("_") or k in _INTERNAL_KEYS))}
    if isinstance(stats_dict, list):
        return [_filter_internal_stats(v) for v in stats_dict]
    return stats_dict

# 内置通用阵型坐标兜底（当 national_formations.json 缺 _formations 时用，绝不让阵容消失）
# x: 0~100 左右；y: 0(后场)~100(前场)，渲染时会翻转让 GK 在底
_FALLBACK_FORMATIONS = {
    "4-3-3": [
        {"role": "GK", "x": 50, "y": 5}, {"role": "LB", "x": 18, "y": 28}, {"role": "CB", "x": 38, "y": 22},
        {"role": "CB", "x": 62, "y": 22}, {"role": "RB", "x": 82, "y": 28}, {"role": "CM", "x": 30, "y": 52},
        {"role": "CM", "x": 50, "y": 48}, {"role": "CM", "x": 70, "y": 52}, {"role": "LW", "x": 20, "y": 80},
        {"role": "ST", "x": 50, "y": 85}, {"role": "RW", "x": 80, "y": 80},
    ],
    "4-2-3-1": [
        {"role": "GK", "x": 50, "y": 5}, {"role": "LB", "x": 18, "y": 28}, {"role": "CB", "x": 38, "y": 22},
        {"role": "CB", "x": 62, "y": 22}, {"role": "RB", "x": 82, "y": 28}, {"role": "CDM", "x": 38, "y": 45},
        {"role": "CDM", "x": 62, "y": 45}, {"role": "LM", "x": 20, "y": 70}, {"role": "CAM", "x": 50, "y": 68},
        {"role": "RM", "x": 80, "y": 70}, {"role": "ST", "x": 50, "y": 88},
    ],
    "4-4-2": [
        {"role": "GK", "x": 50, "y": 5}, {"role": "LB", "x": 18, "y": 28}, {"role": "CB", "x": 38, "y": 22},
        {"role": "CB", "x": 62, "y": 22}, {"role": "RB", "x": 82, "y": 28}, {"role": "LM", "x": 18, "y": 55},
        {"role": "CM", "x": 40, "y": 52}, {"role": "CM", "x": 60, "y": 52}, {"role": "RM", "x": 82, "y": 55},
        {"role": "ST", "x": 38, "y": 85}, {"role": "ST", "x": 62, "y": 85},
    ],
    "3-5-2": [
        {"role": "GK", "x": 50, "y": 5}, {"role": "CB", "x": 30, "y": 22}, {"role": "CB", "x": 50, "y": 20},
        {"role": "CB", "x": 70, "y": 22}, {"role": "LM", "x": 12, "y": 52}, {"role": "CM", "x": 35, "y": 50},
        {"role": "CM", "x": 50, "y": 48}, {"role": "CM", "x": 65, "y": 50}, {"role": "RM", "x": 88, "y": 52},
        {"role": "ST", "x": 40, "y": 85}, {"role": "ST", "x": 60, "y": 85},
    ],
    "5-4-1": [
        {"role": "GK", "x": 50, "y": 5}, {"role": "LWB", "x": 12, "y": 32}, {"role": "CB", "x": 32, "y": 22},
        {"role": "CB", "x": 50, "y": 20}, {"role": "CB", "x": 68, "y": 22}, {"role": "RWB", "x": 88, "y": 32},
        {"role": "LM", "x": 22, "y": 58}, {"role": "CM", "x": 42, "y": 55}, {"role": "CM", "x": 58, "y": 55},
        {"role": "RM", "x": 78, "y": 58}, {"role": "ST", "x": 50, "y": 85},
    ],
}

# 图片注册表：每张图只 base64 一次，缓存到 _IMG_REGISTRY 避免重复编码
_IMG_REGISTRY = {"cards": {}, "panels": {}}


# 图片压缩：缩放到展示尺寸 + WebP，显著减小 base64 体积（卡图原图 ~60KB PNG → ~6KB WebP）
try:
    from PIL import Image
    _PIL_OK = True
except Exception:
    _PIL_OK = False

# 卡面展示宽度（阵型小卡几十px、弹窗大图~260px；统一 260px 已足够清晰，再小会糊）
_CARD_MAX_W = 260
_PANEL_MAX_W = 520


def _resolve_img(path):
    """图片查找：优先同名 .webp（打包压缩版），回退 .png。path 传入 .png 路径。"""
    if path.exists():
        return path
    webp = path.with_suffix(".webp")
    if webp.exists():
        return webp
    return None


def _compress_b64(path, max_w):
    """缩放 + WebP 压缩，返回 dataURI；失败回退原图 base64。"""
    path = _resolve_img(path)
    if path is None:
        return None
    if not _PIL_OK:
        mime = "image/webp" if path.suffix == ".webp" else "image/png"
        return f"data:{mime};base64," + base64.b64encode(path.read_bytes()).decode()
    try:
        import io
        im = Image.open(path)
        if im.mode not in ("RGB", "RGBA"):
            im = im.convert("RGBA")
        if im.width > max_w:
            r = max_w / im.width
            im = im.resize((max_w, round(im.height * r)), Image.LANCZOS)
        buf = io.BytesIO()
        im.save(buf, format="WEBP", quality=80, method=4)
        return "data:image/webp;base64," + base64.b64encode(buf.getvalue()).decode()
    except Exception:
        return "data:image/png;base64," + base64.b64encode(path.read_bytes()).decode()


def card_b64(spid):
    """返回球员卡的压缩 base64 dataURI；外部球员或无图返回 None。"""
    spid = str(spid)
    if spid.startswith("ext_"):
        return None
    if spid not in _IMG_REGISTRY["cards"]:
        b64 = _compress_b64(CARDS_DIR / f"{spid}.png", _CARD_MAX_W)
        if b64 is None:
            return None
        _IMG_REGISTRY["cards"][spid] = b64
    return _IMG_REGISTRY["cards"].get(spid)


def panel_b64(spid):
    spid = str(spid)
    if spid.startswith("ext_") or PANELS_DIR is None:
        return None  # 手游无信息面板图
    if spid not in _IMG_REGISTRY["panels"]:
        b64 = _compress_b64(PANELS_DIR / f"{spid}.png", _PANEL_MAX_W)
        if b64 is None:
            return None
        _IMG_REGISTRY["panels"][spid] = b64
    return _IMG_REGISTRY["panels"].get(spid)


def reset_img_registry():
    """每次渲染开始前清空（避免多次 render 累积）"""
    _IMG_REGISTRY["cards"].clear()
    _IMG_REGISTRY["panels"].clear()


def enrich_player(p):
    rec = _DB.get(str(p.get("spid"))) or {}
    for k_db, k_p in [("salary", "salary"), ("nationality", "nationality"),
                      ("name_cn", "name"), ("ovr", "ovr")]:
        if not p.get(k_p) and rec.get(k_db):
            p[k_p] = rec[k_db]
    return p


CSS = """
:root {
  --bg: #0e1116;
  --panel: #161b22;
  --panel-2: #1c2128;
  --line: #30363d;
  --text: #e6edf3;
  --muted: #8b949e;
  --accent: #f0b429;
  --accent-2: #58a6ff;
  --red: #f85149;
  --green: #3fb950;
  --purple: #8957e5;
  --gold: #d4af37;
}
* { box-sizing: border-box; }
body { margin: 0; background: var(--bg); color: var(--text);
  font-family: -apple-system, "PingFang SC", "Microsoft YaHei", sans-serif; line-height: 1.6; }
.container { max-width: 980px; margin: 0 auto; padding: 32px 24px 80px; }
.brand-strip {
  display: inline-flex; align-items: center; gap: 8px;
  background: linear-gradient(90deg, rgba(137,87,229,.18), rgba(240,180,41,.18));
  border: 1px solid var(--line); border-radius: 20px;
  padding: 4px 12px; font-size: 11px; color: var(--accent); margin-bottom: 12px;
}
.brand-strip .bs-badge {
  background: var(--purple); color: #fff; padding: 1px 6px;
  border-radius: 4px; font-weight: 700; font-size: 10px;
}
.title { font-size: 28px; font-weight: 700; margin: 0 0 6px;
  background: linear-gradient(135deg, var(--accent) 0%, var(--accent-2) 100%);
  -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
.subtitle { color: var(--muted); font-size: 14px; margin-bottom: 24px; }

/* 比赛元信息 + 倒计时 */
.match-meta {
  background: linear-gradient(135deg, rgba(137,87,229,.10) 0%, rgba(15,23,42,.85) 50%, rgba(240,180,41,.08) 100%);
  border: 1px solid var(--line); border-left: 3px solid var(--gold);
  border-radius: 12px; padding: 18px 22px; margin: 0 0 18px;
}
.match-meta .mm-row { display: flex; flex-wrap: wrap; gap: 18px 26px; align-items: center; margin-bottom: 14px; }
.match-meta .mm-icon { margin-right: 6px; }
.match-meta .mm-time, .match-meta .mm-venue { font-size: 14px; color: var(--text); display: flex; align-items: center; gap: 4px; }
.match-meta .mm-date { font-weight: 600; color: var(--gold); }
.match-meta .mm-clock { font-weight: 700; color: #fff; font-size: 16px; margin-left: 4px; }
.match-meta .mm-tz { color: var(--muted); font-size: 12px; margin-left: 4px; }
.match-meta .mm-tags { display: flex; gap: 8px; flex-wrap: wrap; }
.match-meta .mm-group { background: rgba(88,166,255,.15); color: var(--accent-2);
  padding: 3px 10px; border-radius: 12px; font-size: 12px; font-weight: 600; }
.match-meta .mm-focus { background: rgba(240,180,41,.16); color: var(--accent);
  padding: 3px 10px; border-radius: 12px; font-size: 12px; font-weight: 600; }
.mm-countdown { display: flex; gap: 8px; align-items: center;
  padding-top: 12px; border-top: 1px dashed var(--line); flex-wrap: wrap; }
.mm-cd-label { color: var(--muted); font-size: 13px; margin-right: 6px; }
.mm-cd-num {
  background: var(--panel-2); border: 1px solid var(--line); border-radius: 8px;
  padding: 6px 12px; min-width: 56px; text-align: center;
  display: inline-flex; align-items: baseline; gap: 3px;
}
.mm-cd-num span:not(.mm-cd-unit) { font-size: 18px; font-weight: 700; color: var(--gold);
  font-variant-numeric: tabular-nums; }
.mm-cd-unit { font-size: 11px; color: var(--muted); }
.mm-countdown.kicked-off .mm-cd-num span:not(.mm-cd-unit) { color: var(--green); }
.mm-countdown.kicked-off .mm-cd-label::before { content: "🔴 "; }

/* 🔥 噱头模块：一句话钩子 + 比分记分牌 + 战力对比条 */
.hook-box { margin-bottom: 16px; }
.hook-line {
  font-size: 19px; font-weight: 700; color: var(--text); text-align: center;
  line-height: 1.5; padding: 4px 8px 14px; letter-spacing: .5px;
}
.scoreboard {
  position: relative; margin-bottom: 16px; overflow: hidden;
  border-radius: 22px; padding: 26px 24px 20px;
  background:
    radial-gradient(ellipse 90% 60% at 50% 0%, rgba(120,200,150,0.22) 0%, rgba(10,40,25,0) 62%),
    repeating-linear-gradient(180deg, #0c2417 0px, #0c2417 40px, #0e2a1b 40px, #0e2a1b 80px),
    #0a1f14;
  border: 1px solid rgba(255,255,255,0.14);
  box-shadow: inset 0 1px 0 rgba(255,255,255,0.1);
}
.sb-arena {
  display: grid; grid-template-columns: 1fr auto 1fr; align-items: center; gap: 8px;
}
.sb-side { text-align: center; }
.sb-crest {
  width: 60px; height: 60px; margin: 0 auto 10px; border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  font-size: 24px; font-weight: 800; color: #fff;
  border: 2px solid rgba(255,255,255,0.25);
  box-shadow: 0 6px 18px rgba(0,0,0,0.35);
}
.sb-crest-home { background: linear-gradient(135deg, #7a1020, #c0182e); }
.sb-crest-away { background: linear-gradient(135deg, #0b3d2e, #14633f); }
.sb-team { font-size: 16px; font-weight: 700; color: #fff; }
.sb-mid { text-align: center; }
.sb-score {
  font-size: 50px; font-weight: 900; color: #fff; white-space: nowrap; line-height: 1;
  font-variant-numeric: tabular-nums; letter-spacing: 1px;
  text-shadow: 0 0 30px rgba(244,211,94,.35);
}
.sb-colon { color: var(--accent); margin: 0 6px; }
.sb-tag {
  text-align: center; font-size: 11px; color: rgba(255,255,255,0.45);
  margin-top: 14px; letter-spacing: 1.5px;
}
.sb-alts {
  display: flex; flex-wrap: wrap; align-items: center; justify-content: center;
  gap: 8px; margin-top: 18px; padding-top: 16px;
  border-top: 1px dashed rgba(255,255,255,0.16);
}
.sb-alts-lbl { font-size: 11px; color: rgba(255,255,255,0.5); letter-spacing: 1px; }
.sb-alt-chip {
  font-size: 14px; font-weight: 800; color: var(--accent);
  font-variant-numeric: tabular-nums; padding: 4px 13px;
  background: rgba(244,211,94,.12); border: 1px solid rgba(244,211,94,.32);
  border-radius: 9px;
}
.power-compare {
  background: var(--panel); border: 1px solid var(--line); border-radius: 14px;
  padding: 16px 20px 18px; margin-bottom: 14px;
}
.pc-head { display: flex; justify-content: space-between; align-items: center;
  font-size: 13px; font-weight: 700; color: var(--text); margin-bottom: 14px; }
.pc-head-mid { color: var(--muted); font-size: 11px; font-weight: 400; letter-spacing: 2px; }
.pc-row { display: flex; align-items: center; gap: 10px; margin-bottom: 10px; }
.pc-row:last-child { margin-bottom: 0; }
.pc-val { font-size: 14px; font-weight: 700; color: var(--text); width: 34px;
  font-variant-numeric: tabular-nums; flex: none; }
.pc-val-l { text-align: right; }
.pc-val-r { text-align: left; }
.pc-track { flex: 1; display: flex; align-items: center; height: 24px; position: relative;
  border-radius: 6px; overflow: hidden; background: #0c0f14; }
.pc-bar { height: 100%; }
.pc-bar-l { background: var(--accent-2); opacity: .35; }
.pc-bar-r { background: var(--accent); opacity: .35; }
.pc-bar.ps-strong { opacity: .95; }
.pc-bar.ps-weak { opacity: .3; }
.pc-label { position: absolute; left: 50%; top: 50%; transform: translate(-50%,-50%);
  font-size: 11.5px; font-weight: 700; color: #fff; letter-spacing: 1px;
  text-shadow: 0 1px 3px rgba(0,0,0,.8); pointer-events: none; }

.summary { background: linear-gradient(180deg, var(--panel-2) 0%, var(--panel) 100%);
  border: 1px solid var(--line); border-radius: 14px; padding: 22px 24px; margin-bottom: 14px; }
.summary-row { display: flex; gap: 24px; margin-bottom: 14px; flex-wrap: wrap; }
.summary-row > div { flex: 1; min-width: 200px; }
.label { color: var(--muted); font-size: 12px; margin-bottom: 4px; }
.value { font-size: 17px; font-weight: 600; }
.value.highlight { color: var(--accent); }

.data-badge {
  background: var(--panel); border: 1px solid var(--line); border-left: 3px solid var(--accent-2);
  border-radius: 8px; padding: 12px 16px; font-size: 12.5px; color: var(--muted);
  margin-bottom: 28px; line-height: 1.65;
}
.data-badge strong { color: var(--text); }

.section-title { font-size: 18px; font-weight: 700; margin: 32px 0 14px;
  padding-left: 10px; border-left: 3px solid var(--accent); }

.points { background: var(--panel); border: 1px solid var(--line);
  border-radius: 10px; padding: 14px 22px; margin-bottom: 8px; }
.points ol { margin: 0; padding-left: 20px; }
.points li { margin: 6px 0; }

/* 阵型图 */
.formation-wrap {
  background: var(--panel); border: 1px solid var(--line); border-radius: 14px;
  padding: 18px 18px 6px; margin-bottom: 18px;
}
.formation-head { display: flex; justify-content: space-between; align-items: center;
  margin-bottom: 8px; flex-wrap: wrap; gap: 8px; }
.formation-head .ftitle { font-weight: 700; font-size: 15px; color: var(--text); }
.formation-head .ftag { background: var(--panel-2); color: var(--accent);
  padding: 3px 10px; border-radius: 12px; font-size: 12px; }
.formation-head .ftag.chem { color: var(--green); border: 1px solid rgba(63,185,80,.3); }
.pitch {
  position: relative; width: 100%; aspect-ratio: 7 / 9;
  background: linear-gradient(180deg, #0d3b1f 0%, #0a2e16 100%);
  border-radius: 12px; overflow: hidden;
  background-image:
    repeating-linear-gradient(0deg, rgba(255,255,255,.04), rgba(255,255,255,.04) 1px, transparent 1px, transparent 28px);
}
.pitch::before, .pitch::after {
  content: ""; position: absolute; left: 50%; transform: translateX(-50%);
  width: 35%; aspect-ratio: 5/2; border: 1.5px solid rgba(255,255,255,.18);
}
.pitch::before { top: 0; border-top: none; border-radius: 0 0 8px 8px; }
.pitch::after { bottom: 0; border-bottom: none; border-radius: 8px 8px 0 0; }
.pitch-mid {
  position: absolute; left: 0; right: 0; top: 50%; height: 1.5px;
  background: rgba(255,255,255,.18);
}
.pitch-mid-circle {
  position: absolute; left: 50%; top: 50%; transform: translate(-50%,-50%);
  width: 22%; aspect-ratio: 1; border-radius: 50%;
  border: 1.5px solid rgba(255,255,255,.18);
}
.formation-slot {
  position: absolute; transform: translate(-50%, -50%);
  display: flex; flex-direction: column; align-items: center;
  cursor: pointer;
}
.formation-slot.empty { cursor: default; }
.formation-slot img {
  width: 58px; height: auto; border-radius: 6px;
  box-shadow: 0 2px 8px rgba(0,0,0,.5);
  transition: transform .15s;
}
.formation-slot:hover img { transform: scale(1.1); }
.formation-slot .sname {
  font-size: 11px; background: rgba(0,0,0,.75); padding: 1px 6px;
  border-radius: 8px; margin-top: 3px; white-space: nowrap; max-width: 90px;
  overflow: hidden; text-overflow: ellipsis;
}
.formation-slot .srole {
  font-size: 10px; color: var(--accent); margin-bottom: 2px;
  background: rgba(0,0,0,.65); padding: 1px 5px; border-radius: 6px;
}
.formation-slot.empty .sslot-placeholder {
  width: 48px; height: 60px; border-radius: 8px;
  border: 1.5px dashed rgba(244,211,94,0.45);
  background:
    radial-gradient(ellipse 80% 55% at 50% 35%, rgba(244,211,94,0.10) 0%, rgba(15,23,42,0) 70%),
    linear-gradient(165deg, #1b2740 0%, #0e1626 100%);
  display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 3px;
}
.formation-slot.empty .ph-glove { font-size: 18px; line-height: 1; opacity: .8; }
.formation-slot.empty .ph-tip {
  font-size: 9px; color: rgba(244,211,94,0.8); font-weight: 600; text-align: center;
  line-height: 1.2; padding: 0 2px;
}
.formation-slot.empty .sname.ph-name {
  background: rgba(0,0,0,.55); color: rgba(255,255,255,.6);
}

/* 球员卡网格 */
.player-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: 16px; margin-bottom: 8px; }
.player-card { background: var(--panel); border: 1px solid var(--line);
  border-radius: 12px; padding: 12px; text-align: center;
  transition: transform .15s, border-color .15s; }
.player-card:hover { transform: translateY(-3px); border-color: var(--accent); }
.player-card img { width: 100%; max-width: 160px; height: auto;
  border-radius: 8px; display: block; margin: 0 auto 8px; }
.player-card.clickable { cursor: pointer; }
.player-card.clickable::after {
  content: "🔍 点击查看详情"; display: block; color: var(--accent-2);
  font-size: 11px; margin-top: 6px; opacity: 0.7;
}
.player-card.clickable:hover::after { opacity: 1; }
.player-card .pname { font-weight: 600; font-size: 14px; margin-bottom: 2px; }
.player-card .povr { color: var(--accent); font-size: 13px; font-weight: 600; }
.player-card .povr.ext { color: var(--gold); }
.player-card .prole { color: var(--muted); font-size: 12px; margin-top: 4px; }
.player-card.external { border-color: rgba(212,175,55,.35); background: linear-gradient(180deg, rgba(212,175,55,.04), var(--panel)); }
.player-card.external:hover { border-color: var(--gold); }
.ext-card-face {
  width: 100%; max-width: 160px; height: 200px;
  background: linear-gradient(160deg, #2a2317 0%, #1c1810 50%, #2a2317 100%);
  border: 1px solid rgba(212,175,55,.4);
  border-radius: 10px; padding: 14px 10px;
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  position: relative; overflow: hidden;
  margin: 0 auto 10px;
}
.ext-card-face::before {
  content: ""; position: absolute; inset: 0;
  background: radial-gradient(ellipse at top, rgba(212,175,55,.18) 0%, transparent 60%);
  pointer-events: none;
}
.ext-ovr-big { font-size: 38px; font-weight: 800; color: var(--gold); line-height: 1; margin-bottom: 4px; text-shadow: 0 0 20px rgba(212,175,55,.4); }
.ext-pos { font-size: 10px; color: var(--muted); letter-spacing: 2px; margin-bottom: 14px; }
.ext-name-big { font-size: 14px; font-weight: 700; color: #fff; text-align: center; margin-bottom: 6px; }
.ext-note { font-size: 10px; color: rgba(212,175,55,.75); text-align: center; line-height: 1.4; padding: 0 4px; }
.formation-slot.external .sname { color: var(--gold); }
.ext-slot-token {
  width: 50px; height: 50px; border-radius: 50%;
  background: radial-gradient(circle, #3a2f15 0%, #1a1408 100%);
  border: 2px solid var(--gold);
  display: flex; align-items: center; justify-content: center;
  box-shadow: 0 0 12px rgba(212,175,55,.4);
  margin: 0 auto;
}
.ext-slot-ovr { font-size: 18px; font-weight: 800; color: var(--gold); text-shadow: 0 0 8px rgba(212,175,55,.6); }

.fallback-card { background: var(--panel); border: 1px solid var(--line);
  border-left: 3px solid var(--purple); border-radius: 10px; padding: 18px 22px; }
.fallback-card .frow { display: flex; gap: 12px; margin: 6px 0; }
.fallback-card .fkey { color: var(--muted); min-width: 80px; font-size: 13px; }
.fallback-card .fval { font-size: 14px; }

.tip-box { background: var(--panel); border: 1px solid var(--line);
  border-radius: 10px; padding: 14px 18px; margin-bottom: 10px; }
.tip-box strong { color: var(--accent-2); }

.fu-tip { font-size: 12px; color: var(--muted); margin: 8px 0 2px; }
.followups { display: flex; flex-wrap: wrap; gap: 10px; margin-top: 12px; }
.followup { background: var(--panel-2); border: 1px solid var(--line);
  color: var(--text); padding: 9px 14px; border-radius: 18px; font-size: 13px;
  cursor: pointer; transition: border-color .15s, background .15s, transform .1s;
  display: inline-flex; align-items: center; gap: 8px; user-select: none; }
.followup:hover { border-color: var(--accent); background: rgba(240,180,41,0.08); }
.followup:active { transform: scale(.97); }
.followup .fu-copy { font-size: 11px; color: var(--accent); opacity: .65; white-space: nowrap; }
.followup.copied { border-color: var(--accent); background: rgba(240,180,41,0.14); }
.followup.copied .fu-copy { opacity: 1; }
/* 复制成功 toast */
#fuToast { position: fixed; left: 50%; bottom: 38px; transform: translateX(-50%) translateY(20px);
  background: linear-gradient(135deg, #1c2128, #161b22); border: 1px solid var(--accent);
  color: var(--text); padding: 12px 20px; border-radius: 12px; font-size: 14px; font-weight: 600;
  box-shadow: 0 8px 30px rgba(0,0,0,.5); z-index: 9999; opacity: 0; pointer-events: none;
  transition: opacity .25s, transform .25s; max-width: 86vw; text-align: center; line-height: 1.5; }
#fuToast.show { opacity: 1; transform: translateX(-50%) translateY(0); }
#fuToast .ft-strong { color: var(--accent); }

.disclaimer { margin-top: 32px; padding: 12px 16px; background: var(--panel);
  border-radius: 8px; color: var(--muted); font-size: 12px; line-height: 1.5; }

.brand-footer {
  margin-top: 24px; padding: 28px 24px;
  background:
    radial-gradient(circle at 20% 0%, rgba(240,180,41,.18) 0%, transparent 50%),
    radial-gradient(circle at 80% 100%, rgba(88,166,255,.12) 0%, transparent 50%),
    linear-gradient(135deg, #1c2128 0%, #161b22 100%);
  border: 1px solid var(--line); border-radius: 16px;
  text-align: center;
  position: relative; overflow: hidden;
}
.brand-footer::before {
  content: ""; position: absolute; inset: 0;
  background-image: repeating-linear-gradient(45deg,
    transparent 0, transparent 40px,
    rgba(240,180,41,.02) 40px, rgba(240,180,41,.02) 41px);
  pointer-events: none;
}
.brand-slogan {
  font-size: 26px; font-weight: 800; letter-spacing: 4px;
  background: linear-gradient(135deg, #f0b429 0%, #ffd668 50%, #f0b429 100%);
  -webkit-background-clip: text; -webkit-text-fill-color: transparent;
  margin: 4px 0 6px; line-height: 1.3;
  text-shadow: 0 0 30px rgba(240,180,41,.3);
  position: relative;
}
.brand-tagline {
  color: var(--muted); font-size: 12px; letter-spacing: 2px;
  margin-bottom: 22px; position: relative;
}
.brand-tagline::before, .brand-tagline::after {
  content: "—"; margin: 0 10px; color: rgba(240,180,41,.5);
}
.brand-soft {
  color: var(--text); font-size: 13.5px; line-height: 1.8;
  max-width: 560px; margin: 8px auto 16px; position: relative;
  opacity: .92;
}
.brand-soft strong { color: var(--accent); }
.cta-row {
  display: flex; gap: 14px; justify-content: center; flex-wrap: wrap;
  position: relative;
}
.cta-btn {
  display: inline-flex; align-items: center; gap: 10px;
  padding: 12px 24px; border-radius: 10px;
  font-size: 14px; font-weight: 600;
  text-decoration: none; cursor: pointer;
  transition: transform .15s, box-shadow .15s, filter .15s;
  border: none;
}
.cta-btn:hover { transform: translateY(-2px); }
.cta-btn .cta-icon { font-size: 18px; }
.cta-btn .cta-sub {
  display: block; font-size: 11px; font-weight: 400;
  opacity: 0.85; margin-top: 2px;
}
.cta-btn.cta-primary {
  background: linear-gradient(135deg, #f0b429 0%, #d4a01a 100%);
  color: #18191c;
  box-shadow: 0 4px 20px rgba(240,180,41,.35);
}
.cta-btn.cta-primary:hover { box-shadow: 0 6px 28px rgba(240,180,41,.5); filter: brightness(1.05); }
.cta-btn.cta-secondary {
  background: linear-gradient(135deg, #58a6ff 0%, #3b82f6 100%);
  color: #fff;
  box-shadow: 0 4px 20px rgba(88,166,255,.3);
}
.cta-btn.cta-secondary:hover { box-shadow: 0 6px 28px rgba(88,166,255,.45); filter: brightness(1.05); }
.cta-btn.cta-secondary::after {
  content: "⚡"; margin-left: 4px; color: #fff;
}
.cta-bottom {
  margin-top: 20px; padding-top: 16px;
  border-top: 1px solid rgba(255,255,255,.06);
  color: var(--muted); font-size: 11.5px; letter-spacing: 1px;
  position: relative;
}

.conclusion { background: linear-gradient(135deg, rgba(240,180,41,.08), rgba(88,166,255,.06));
  border: 1px solid var(--line); border-radius: 10px; padding: 16px 20px; font-size: 14px; }

/* 剧情卡 - 电影感比赛画面预演 */
.story-card {
  background:
    linear-gradient(135deg, rgba(248,81,73,.10) 0%, rgba(15,23,42,.85) 35%, rgba(0,65,112,.18) 100%),
    radial-gradient(ellipse at 30% 20%, rgba(240,180,41,.08), transparent 60%);
  border: 1px solid rgba(240,180,41,.25);
  border-left: 3px solid var(--gold);
  border-radius: 10px;
  padding: 22px 26px;
  font-size: 14.5px;
  line-height: 1.85;
  color: var(--text);
  position: relative;
  overflow: hidden;
  font-family: -apple-system, "PingFang SC", "Microsoft YaHei", "Songti SC", sans-serif;
}
.story-card::before {
  content: "";
  position: absolute; top: 0; left: 0; right: 0; height: 100%;
  background: repeating-linear-gradient(0deg, transparent, transparent 2px, rgba(255,255,255,.012) 2px, rgba(255,255,255,.012) 3px);
  pointer-events: none;
}
.story-card p { margin: 0 0 12px; position: relative; }
.story-card p:last-child { margin-bottom: 0; }
.story-card strong { color: var(--gold); font-weight: 600; }
.story-card em { color: var(--accent-2); font-style: normal; }

/* 焦点对决 - 海报式单卡（一场只一个最关键对决） */
.spotlight-duel {
  background:
    linear-gradient(135deg, rgba(248,81,73,.18) 0%, rgba(15,23,42,.88) 50%, rgba(88,166,255,.18) 100%),
    radial-gradient(ellipse at center, rgba(240,180,41,.10), transparent 60%);
  border: 1px solid rgba(240,180,41,.35);
  border-radius: 14px;
  padding: 28px 28px 24px;
  position: relative;
  overflow: hidden;
}
.spotlight-duel::before {
  content: "";
  position: absolute; inset: 0;
  background: repeating-linear-gradient(45deg, transparent 0 12px, rgba(255,255,255,.015) 12px 13px);
  pointer-events: none;
}
.spotlight-duel .sd-tag {
  display: inline-block; font-size: 11px; letter-spacing: 3px; color: var(--gold);
  font-weight: 600; margin-bottom: 8px;
}
.spotlight-duel .sd-title {
  font-size: 18px; font-weight: 700; color: #fff; margin-bottom: 22px; line-height: 1.5;
}
.spotlight-duel .sd-arena {
  display: grid; grid-template-columns: 1fr auto 1fr;
  gap: 22px; align-items: center; margin-bottom: 18px;
}
.spotlight-duel .sd-side {
  display: flex; flex-direction: column; gap: 6px; align-items: center;
}
.spotlight-duel .sd-side.right { text-align: center; align-items: center; }
/* 焦点对决卡面可点击：hover 微浮 + 金边，提示"点这能看详情" */
.spotlight-duel .sd-side.sd-clickable { cursor: pointer; border-radius: 12px;
  padding: 6px 6px 4px; margin: -6px -6px -4px; transition: background .16s, transform .16s; }
.spotlight-duel .sd-side.sd-clickable:hover { background: rgba(244,211,94,0.07); transform: translateY(-2px); }
.spotlight-duel .sd-side.sd-clickable:hover .sd-card { filter: drop-shadow(0 6px 18px rgba(240,180,41,.35)); }
.spotlight-duel .sd-tap-hint { font-size: 11px; font-weight: 600; color: var(--accent);
  opacity: .7; margin-top: 2px; letter-spacing: .5px; }
.spotlight-duel .sd-card {
  width: 96px; height: auto; border-radius: 8px; display: block;
  filter: drop-shadow(0 4px 14px rgba(0,0,0,.45));
}
.spotlight-duel .sd-card-ph {
  width: 96px; height: 116px; border-radius: 10px; overflow: hidden;
  display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 6px;
  background:
    radial-gradient(ellipse 80% 55% at 50% 30%, rgba(244,211,94,0.14) 0%, rgba(15,23,42,0) 65%),
    repeating-linear-gradient(135deg, rgba(255,255,255,0.03) 0px, rgba(255,255,255,0.03) 7px, rgba(255,255,255,0) 7px, rgba(255,255,255,0) 14px),
    linear-gradient(165deg, #1b2740 0%, #0e1626 100%);
  border: 1px dashed rgba(244,211,94,0.4);
  box-shadow: inset 0 1px 0 rgba(255,255,255,0.06);
}
.spotlight-duel .sd-ph-shield { position: relative; display: flex; align-items: center; justify-content: center; }
.spotlight-duel .sd-ph-char {
  position: absolute; font-size: 26px; font-weight: 900; color: rgba(255,255,255,0.92);
  text-shadow: 0 1px 6px rgba(0,0,0,0.6); line-height: 1;
}
.spotlight-duel .sd-ph-tip {
  font-size: 11px; font-weight: 600; color: rgba(244,211,94,0.75); letter-spacing: 1px;
}
.spotlight-duel .sd-stat-soft { color: rgba(255,255,255,0.6); font-weight: 600; font-size: 12px; }
.spotlight-duel .sd-name { font-size: 19px; font-weight: 800; color: #fff; line-height: 1.2; text-align: center; }
.spotlight-duel + .spotlight-duel { margin-top: 14px; }
/* 阵容 Tab 切换：两队阵容图分页放，省纵向空间 */
.squad-tabs { display: flex; gap: 10px; margin-bottom: 14px; }
.squad-tab {
  flex: 1; display: flex; flex-direction: column; align-items: center; gap: 2px;
  padding: 10px 8px; border-radius: 10px; cursor: pointer;
  background: rgba(255,255,255,.04); border: 1px solid rgba(255,255,255,.10);
  color: var(--muted); font-size: 15px; font-weight: 700; transition: all .15s;
}
.squad-tab .st-sub { font-size: 11px; font-weight: 400; color: var(--muted); }
.squad-tab.active {
  background: linear-gradient(135deg, rgba(240,180,41,.18), rgba(240,180,41,.06));
  border-color: rgba(240,180,41,.5); color: #fff;
}
.squad-tab.active .st-sub { color: var(--gold); }
.squad-formation-label { font-size: 13px; color: var(--muted); margin-bottom: 10px; text-align: center; }
.squad-chips { display: flex; flex-wrap: wrap; gap: 8px; margin: 12px 0; }
.squad-chip {
  background: rgba(255,255,255,.05); border: 1px solid rgba(255,255,255,.10);
  border-radius: 8px; padding: 6px 10px; font-size: 13px; color: var(--text);
}
.squad-chip i { color: var(--gold); font-style: normal; font-weight: 600; margin-left: 6px; }
.squad-text-note { font-size: 13px; color: var(--muted); line-height: 1.7; }
.spotlight-duel .sd-meta { font-size: 12px; color: var(--muted); }
.spotlight-duel .sd-stat {
  font-size: 13px; color: var(--gold); font-weight: 600; margin-top: 4px;
}
.spotlight-duel .sd-badges {
  display: flex; flex-wrap: wrap; gap: 5px; justify-content: center; margin-top: 6px;
}
.spotlight-duel .sd-ovr-chip {
  font-size: 11px; font-weight: 700; color: #1a1206; background: var(--gold);
  border-radius: 5px; padding: 2px 7px; letter-spacing: .3px;
}
.spotlight-duel .sd-badge {
  font-size: 11px; font-weight: 600; color: var(--gold);
  border: 1px solid rgba(240,180,41,.45); border-radius: 5px; padding: 2px 7px;
  background: rgba(240,180,41,.08);
}
.spotlight-duel .sd-vs {
  font-size: 28px; font-weight: 800; color: var(--gold);
  text-shadow: 0 0 24px rgba(240,180,41,.4);
}
.spotlight-duel .sd-xfactor {
  text-align: center; font-size: 12.5px; font-weight: 700; color: var(--accent);
  margin: 2px 0 14px; letter-spacing: .5px;
}
.spotlight-duel .sd-verdict {
  font-size: 13px; color: var(--text); line-height: 1.7;
  padding-top: 16px; border-top: 1px dashed rgba(240,180,41,.3);
}
.spotlight-duel .sd-verdict strong { color: var(--gold); }

/* 焦点组合 - 双方一行一条核心链路 */
.spotlight-links { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; }
@media (max-width: 720px) { .spotlight-links { grid-template-columns: 1fr; } }
.spotlight-link {
  background: var(--panel); border: 1px solid var(--line); border-radius: 12px;
  padding: 16px 18px; position: relative;
}
.spotlight-link.home { border-top: 3px solid var(--red); }
.spotlight-link.away { border-top: 3px solid var(--accent-2); }
.spotlight-link .sl-team {
  font-size: 12px; font-weight: 700; letter-spacing: 1px; margin-bottom: 8px;
}
.spotlight-link.home .sl-team { color: #ff6b75; }
.spotlight-link.away .sl-team { color: #4ba3df; }
.spotlight-link .sl-chain {
  font-size: 15px; font-weight: 700; color: #fff; margin-bottom: 6px; line-height: 1.5;
}
.spotlight-link .sl-desc { color: var(--muted); font-size: 12.5px; line-height: 1.65; }

/* 弹窗 */
.modal-backdrop { position: fixed; inset: 0; background: rgba(0,0,0,0.82);
  display: none; align-items: center; justify-content: center;
  z-index: 999; padding: 24px; overflow-y: auto; }
.modal-backdrop.active { display: flex; }
.modal-box { background: var(--panel); border: 1px solid var(--line);
  border-radius: 14px; max-width: 1150px; width: 100%; max-height: 92vh;
  overflow-y: auto; padding: 28px 32px; position: relative;
  animation: modal-pop .18s ease; }
@keyframes modal-pop { from { transform: scale(.95); opacity: 0; } to { transform: scale(1); opacity: 1; } }
.modal-close { position: absolute; top: 16px; right: 18px;
  width: 32px; height: 32px; border-radius: 50%;
  background: var(--panel-2); border: 1px solid var(--line); color: var(--text);
  font-size: 18px; cursor: pointer; display: flex; align-items: center; justify-content: center; }
.modal-close:hover { background: var(--red); border-color: var(--red); }
.modal-header { display: flex; gap: 24px; margin-bottom: 22px;
  padding-bottom: 18px; border-bottom: 1px solid var(--line); flex-wrap: wrap; }
.modal-header img.mcard { width: 140px; height: auto; border-radius: 8px; }
.modal-header .meta h3 { margin: 0 0 8px; font-size: 24px; color: var(--accent); }
.modal-header .meta-row { color: var(--muted); font-size: 13px; margin: 4px 0; }
.modal-header .meta-row strong { color: var(--text); margin-right: 6px; }
.modal-section-title { font-size: 14px; color: var(--accent-2); margin: 20px 0 10px;
  padding-left: 8px; border-left: 2px solid var(--accent-2); font-weight: 600; }

/* 六维雷达图 */
.radar-wrap {
  display: flex; gap: 24px; align-items: center; flex-wrap: wrap;
  background: var(--panel-2); border: 1px solid var(--line); border-radius: 10px;
  padding: 18px;
}
.radar-svg { flex: 0 0 280px; }
.radar-legend {
  flex: 1; min-width: 200px;
  display: grid; grid-template-columns: repeat(2, 1fr); gap: 8px;
}
.radar-legend-item {
  display: flex; justify-content: space-between; align-items: center;
  background: var(--panel); border: 1px solid var(--line); border-radius: 6px;
  padding: 6px 12px;
}
.radar-legend-item .rl-name { color: var(--muted); font-size: 12.5px; }
.radar-legend-item .rl-val { color: var(--accent); font-weight: 700; font-size: 14px; }
.radar-legend-item.top { border-left: 2px solid var(--accent); }

.traits { display: flex; flex-wrap: wrap; gap: 8px; }
.trait-chip {
  padding: 4px 12px; border-radius: 14px; font-size: 12.5px;
  background: var(--panel-2); border: 1px solid var(--line);
}
.trait-chip.gold { background: linear-gradient(135deg, rgba(212,175,55,.15), rgba(240,180,41,.18));
  border-color: var(--gold); color: var(--gold); }
.trait-chip.hold { color: var(--text); }
.pos-stats {
  display: grid; grid-template-columns: repeat(auto-fill, minmax(140px, 1fr)); gap: 8px;
}
.pos-stat-item {
  background: var(--panel-2); border: 1px solid var(--line); border-radius: 6px;
  padding: 6px 10px; font-size: 12px; display: flex; justify-content: space-between;
}
.pos-stat-item .psn { color: var(--muted); }
.pos-stat-item .psv { color: var(--accent); font-weight: 600; }
.modal-panel-img { width: 100%; border-radius: 8px; display: block; margin-top: 10px; }
.no-stats-hint {
  background: rgba(137,87,229,.1); border: 1px solid var(--line); border-left: 3px solid var(--purple);
  border-radius: 6px; padding: 10px 14px; color: var(--muted); font-size: 12px; margin-bottom: 12px;
}
.player-summary {
  display: flex; gap: 12px; align-items: flex-start;
  background: linear-gradient(135deg, rgba(240,180,41,.08), rgba(88,166,255,.08));
  border: 1px solid var(--line); border-left: 3px solid var(--accent);
  border-radius: 10px; padding: 14px 18px; margin-top: 4px; margin-bottom: 6px;
}
.player-summary .summary-icon { font-size: 18px; flex-shrink: 0; }
.player-summary .summary-text { font-size: 13.5px; line-height: 1.7; color: var(--text); }
.trait-explain {
  background: var(--panel-2); border: 1px solid var(--line);
  border-radius: 6px; padding: 10px 14px; margin-top: 6px;
  font-size: 12px; color: var(--muted); line-height: 1.6;
}
.trait-explain strong { color: var(--gold); }

/* ========== 移动端响应式 ========== */
@media (max-width: 720px) {
  .container { padding: 16px 12px 60px; }
  .title { font-size: 22px; line-height: 1.3; }
  .subtitle { font-size: 13px; }
  .section-title { font-size: 15px; margin: 24px 0 10px; }

  .summary-row { flex-direction: column; gap: 12px; }
  .summary-row > div { min-width: 100%; }
  .value { font-size: 15px; }

  .match-meta { padding: 14px 16px; }
  .match-meta .mm-row { gap: 12px 16px; }
  .match-meta .mm-time, .match-meta .mm-venue { font-size: 13px; }
  .match-meta .mm-clock { font-size: 15px; }
  .mm-cd-num { padding: 5px 9px; min-width: 48px; }
  .mm-cd-num span:not(.mm-cd-unit) { font-size: 16px; }

  .spotlight-duel { padding: 20px 18px 18px; }
  .spotlight-duel .sd-name { font-size: 17px; }
  .spotlight-duel .sd-vs { font-size: 22px; }
  .spotlight-duel .sd-arena { gap: 14px; }

  .player-grid { grid-template-columns: repeat(auto-fit, minmax(112px, 1fr)); gap: 8px; }
  .player-card { padding: 8px; }
  .player-card img, .player-card .ext-card-face { max-width: 100%; }

  .formation-wrap { padding: 12px; }
  .pitch { aspect-ratio: 7/9; }
  .formation-slot img { width: 36px; }
  .ext-slot-token { width: 36px; height: 36px; }
  .ext-slot-ovr { font-size: 14px; }
  .formation-slot .sname { font-size: 10px; }

  .modal-box { padding: 18px 14px; max-width: 100%; max-height: 92vh; overflow-y: auto; }
  .modal-header { flex-direction: column; gap: 12px; align-items: center; text-align: center; }
  .modal-header img.mcard { width: 110px; }
  .modal-header .meta h3 { font-size: 20px; }

  .story-card { padding: 18px 16px; font-size: 13.5px; line-height: 1.75; }
}
"""


# ---------- 阵型 SVG / 球员卡渲染 ----------

def render_formation(team_name, formation_name, players, nation_chem=True):
    """渲染阵型图（球员卡挂位置）。
    players: enrich 过的球员 list（带 spid/name/ovr/role）
    role 字段如果匹配 formation 中某个 role，就挂上去；用 OVR 排序兜底。
    """
    f_def = _FORMATIONS.get("_formations", {}).get(formation_name)
    if not f_def:
        # 兜底：预设缺失也绝不只显示一行字——用内置通用阵型坐标画出来
        f_def = _FALLBACK_FORMATIONS.get(formation_name) or _FALLBACK_FORMATIONS["4-3-3"]

    # 过滤掉空占位标记球员（spid=None / empty=True，如无门将卡时的 GK 空槽）——
    # 这些不进分配池，对应槽位（多为 GK）自然留空，渲染成空占位，绝不被外野球员顶替。
    players = [p for p in players if p.get("spid") and not p.get("empty")]
    # 按 OVR 排，role 优先匹配
    players_sorted = sorted(players, key=lambda x: x.get("ovr") or 0, reverse=True)
    used_spids = set()
    slot_assignments = []  # 每个 slot 分配的 player（可能为 None）

    # 🧤 门将识别：role=GK 优先；role 缺失时用知名门将名字兜底，防"门将被吞"
    _GK_NAMES = (
        "迪奥戈·科斯塔", "迪奥戈科斯塔", "科斯塔", "唐纳鲁马", "迈尼昂", "库尔图瓦",
        "诺伊尔", "特尔施特根", "埃德森", "阿利松", "奥纳纳", "拉亚", "皮克福德",
        "桑切斯", "卢宁", "拉莫斯达尔", "迈尼昂", "梅尼昂", "门多", "拉法埃尔",
        "马丁内斯", "乌加特",  # 注意：这些可能与外野同名，仅在 role 缺失时作弱兜底
    )
    # 强兜底白名单（几乎只可能是门将的名字，安全）
    _GK_STRONG = ("迪奥戈·科斯塔", "科斯塔", "唐纳鲁马", "库尔图瓦", "诺伊尔",
                  "特尔施特根", "埃德森", "阿利松", "奥纳纳", "皮克福德")

    def _is_gk(p):
        if (p.get("role") or "").upper() == "GK":
            return True
        # role 缺失时才用名字强兜底（避免误判外野同名球员）
        if not (p.get("role") or "").strip():
            nm = p.get("name", "")
            return any(k in nm for k in _GK_STRONG)
        return False

    # 🧤 GK 槽位优先独占处理：先把真正的门将锁进 GK 槽，绝不让外野球员兜底进门将位
    gk_slot_idx = [i for i, s in enumerate(f_def) if s["role"] == "GK"]
    gk_player = next((p for p in players_sorted if _is_gk(p)), None)
    # 一队通常只有 1 个 GK 槽；若有门将就先占住
    pre_assigned = {}
    if gk_slot_idx and gk_player:
        pre_assigned[gk_slot_idx[0]] = gk_player
        used_spids.add(gk_player["spid"])

    # 精准匹配 role（GK 槽已预占则跳过；其余槽位 GK 球员不参与，避免门将被排到外野）
    for i, slot in enumerate(f_def):
        if i in pre_assigned:
            slot_assignments.append(pre_assigned[i]); continue
        sr = slot["role"]
        assigned = None
        for p in players_sorted:
            if p["spid"] in used_spids:
                continue
            if sr != "GK" and _is_gk(p):
                continue  # 门将不去填非 GK 槽位
            pr = (p.get("role") or "").upper()
            if sr == "GK":
                if _is_gk(p):
                    assigned = p; used_spids.add(p["spid"]); break
                continue  # GK 槽只认门将，绝不子串误匹配
            if sr in pr or pr == sr:
                assigned = p; used_spids.add(p["spid"]); break
        slot_assignments.append(assigned)

    # 兜底：剩下的 slot 用 OVR 高的剩余球员填。
    # 🧤 GK 槽位即使没匹配到门将也绝不用外野球员兜底（宁可空着画占位，也不让前锋站门里）。
    for i, slot in enumerate(f_def):
        if slot_assignments[i] is None and slot["role"] != "GK":
            for p in players_sorted:
                if p["spid"] not in used_spids and not _is_gk(p):
                    slot_assignments[i] = p; used_spids.add(p["spid"]); break
    # 极端兜底：仍有非 GK 空槽且只剩门将（11 人里多门将等异常），才允许门将兜底外野
    for i, slot in enumerate(f_def):
        if slot_assignments[i] is None and slot["role"] != "GK":
            for p in players_sorted:
                if p["spid"] not in used_spids:
                    slot_assignments[i] = p; used_spids.add(p["spid"]); break

    slots_html = []
    for slot, p in zip(f_def, slot_assignments):
        # 球场坐标系：x 直接用，y 取反（让 GK 在底，前锋在顶）
        # 压缩到 [8, 92] 防止贴边裁掉
        raw_y = 100 - slot["y"]
        y = 8 + raw_y * 0.84
        x = slot["x"]
        if p is None:
            # 空槽位（主要是该队在本引擎下无门将卡时的 GK 槽）：画体面占位，不留丑灰框
            is_gk_slot = slot["role"] == "GK"
            ph_inner = (
                '<div class="ph-glove">🧤</div><div class="ph-tip">暂无门将卡</div>'
                if is_gk_slot else ''
            )
            name_line = '<div class="sname ph-name">待补强</div>' if is_gk_slot else ''
            slots_html.append(f'''<div class="formation-slot empty" style="left:{x}%;top:{y}%;">
                <div class="srole">{slot["role"]}</div>
                <div class="sslot-placeholder">{ph_inner}</div>
                {name_line}
            </div>''')
            continue
        img = card_b64(p["spid"])
        panel = panel_b64(p["spid"])
        is_external = str(p.get("spid","")).startswith("ext_") or img is None
        data_attrs = (
            f'data-spid="{p["spid"]}" data-name="{p["name"]}" data-ovr="{p["ovr"]}" '
            f'data-role="{p.get("role", slot["role"])}" '
            f'data-salary="{p.get("salary", "")}" data-nation="{p.get("nationality", "")}" '
            f'data-note="{p.get("note","")}" '
            f'data-card="{img or ""}" data-panel="{panel or ""}"'
        )
        if img:
            img_html = f'<img src="{img}" alt="{p["name"]}">'
        else:
            # 外部球员：金色 OVR 圆形徽章作为阵型槽位的视觉 token
            img_html = (
                f'<div class="ext-slot-token">'
                f'<div class="ext-slot-ovr">{p.get("ovr","-")}</div>'
                f'</div>'
            )
        ext_cls = " external" if is_external else ""
        slots_html.append(f'''<div class="formation-slot{ext_cls}" style="left:{x}%;top:{y}%;" {data_attrs} onclick="showPlayer(this)">
            <div class="srole">{slot["role"]}</div>
            {img_html}
            <div class="sname">{p["name"]}</div>
        </div>''')

    return f'''<div class="formation-wrap">
        <div class="formation-head">
            <div class="ftitle">{team_name} · 阵型 {formation_name}</div>
            <div><span class="ftag">点击球员看详情</span></div>
        </div>
        <div class="pitch">
            <div class="pitch-mid"></div>
            <div class="pitch-mid-circle"></div>
            {"".join(slots_html)}
        </div>
    </div>'''


def render_player_cards(players):
    if not players:
        return "<p style='color:var(--muted);font-size:13px;'>—</p>"
    # 跳过空占位标记球员（无门将卡时的 GK 空槽等），不画卡也不崩
    players = [p for p in players if p.get("spid") and not p.get("empty")]
    if not players:
        return "<p style='color:var(--muted);font-size:13px;'>—</p>"
    cards = []
    for raw in players:
        p = enrich_player(dict(raw))
        img = card_b64(p["spid"]); panel = panel_b64(p["spid"])
        is_external = str(p.get("spid","")).startswith("ext_") or img is None
        if img:
            img_html = f'<img src="{img}" alt="{p["name"]}">'
        else:
            # 无卡图球员：金色渐变占位卡（保底，不显示空/错位卡面），用当前引擎口径
            note = p.get("note", ENGINE_INFO[ENGINE]["name"] + " 现役球员")
            img_html = (
                f'<div class="ext-card-face">'
                f'<div class="ext-ovr-big">{p.get("ovr","-")}</div>'
                f'<div class="ext-pos">{p.get("role","")}</div>'
                f'<div class="ext-name-big">{p["name"]}</div>'
                f'<div class="ext-note">{note}</div>'
                f'</div>'
            )
        role = f'<div class="prole">{p["role"]}</div>' if p.get("role") else ""
        clickable_cls = " clickable" if panel else ""
        ovr_class = "povr ext" if is_external else "povr"
        data_attrs = (
            f'data-spid="{p["spid"]}" data-name="{p["name"]}" data-ovr="{p["ovr"]}" '
            f'data-role="{p.get("role", "")}" '
            f'data-salary="{p.get("salary", "")}" data-nation="{p.get("nationality", "")}" '
            f'data-note="{p.get("note","")}" '
            f'data-card="{img or ""}" data-panel="{panel or ""}"'
        )
        cards.append(f'''<div class="player-card{clickable_cls}{" external" if is_external else ""}" {data_attrs} onclick="showPlayer(this)">
            {img_html}<div class="pname">{p["name"]}</div>
            <div class="{ovr_class}">OVR {p["ovr"]}</div>{role}
        </div>''')
    return f'<div class="player-grid">{"".join(cards)}</div>'


def render_fallback(info):
    rows = []
    for key, label in [("fifa_rank", "世界排名"), ("world_rank", "世界排名"),
                       ("coach", "主教练"), ("style", "战术风格"),
                       ("key_players_text", "关键球员"), ("core", "核心球员"),
                       ("note", "看点"), ("absent", "缺阵")]:
        if info.get(key):
            v = f'第 {info[key]} 位' if key == "fifa_rank" else info[key]
            rows.append(f'<div class="frow"><div class="fkey">{label}</div><div class="fval">{v}</div></div>')
    return f'<div class="fallback-card">{"".join(rows)}</div>'


# ---------- 主渲染 ----------

def render(d):
    # 引擎切换（默认端游；input 传 engine=mobile 则全程用手游数据/卡图/文案）
    eng = d.get("engine", "fco")
    if eng not in ENGINE_INFO:
        eng = "fco"
    set_engine(eng)
    EI = ENGINE_INFO[eng]

    # 汇总本场所有出场球员，建梗库映射（含焦点对决双方），供 JS 画像/剧情用
    _all_players = []
    for side in ("home", "away"):
        _all_players += (d.get(side) or {}).get("players", []) or []
    for mm in d.get("key_matchups") or []:
        for k in ("home", "away"):
            if mm.get(k):
                _all_players.append({"name": mm[k]})
    _lore_db = _lore_map_for_players(_all_players)

    summary = d.get("summary", {})
    # 比分只在顶部记分牌呈现一次（见下方噱头模块），此处摘要栏不再重复展示比分，避免重复。
    rt_html = f'<div><div class="label">阵容看点</div><div class="value">{summary.get("real_tendency")}</div></div>' if summary.get("real_tendency") else ""
    summary_html = f'''
    <div class="summary">
      <div class="summary-row">
        {rt_html}
        <div><div class="label">卡组对位推演</div><div class="value highlight">{summary.get("overall","—")}</div></div>
      </div>
    </div>
    '''

    # 🔥 噱头模块：顶部「战力对比条 + 比分记分牌」——一眼看懂谁强、强在哪、可能几比几
    hook_html = ""
    home_name_h = d.get("home", {}).get("name", "主队")
    away_name_h = d.get("away", {}).get("name", "客队")
    one_liner = d.get("hook_line") or summary.get("real_tendency", "")
    pc = d.get("power_compare")  # [{"label":"进攻","home":92,"away":85}, ...]
    bars_html = ""
    if pc:
        rows = []
        for row in pc:
            lbl = row.get("label", "")
            hv = float(row.get("home", 0) or 0)
            av = float(row.get("away", 0) or 0)
            tot = (hv + av) or 1
            hp = round(hv / tot * 100)
            ap = 100 - hp
            h_strong = "ps-strong" if hv >= av else "ps-weak"
            a_strong = "ps-strong" if av > hv else "ps-weak"
            rows.append(f'''
            <div class="pc-row">
              <span class="pc-val pc-val-l">{int(hv) if hv==int(hv) else hv}</span>
              <div class="pc-track">
                <div class="pc-bar pc-bar-l {h_strong}" style="width:{hp}%;"></div>
                <div class="pc-bar pc-bar-r {a_strong}" style="width:{ap}%;"></div>
                <span class="pc-label">{lbl}</span>
              </div>
              <span class="pc-val pc-val-r">{int(av) if av==int(av) else av}</span>
            </div>''')
        bars_html = "".join(rows)

    score_big = summary.get("score_hint", "")
    # 备选比分：可来自 summary.score_alts(数组) 或 score_hint 内含「/」分隔的多个比分
    score_alts = summary.get("score_alts") or []
    if not score_alts and score_big and "/" in score_big:
        parts = [s.strip() for s in score_big.split("/") if s.strip()]
        if len(parts) > 1:
            score_big, score_alts = parts[0], parts[1:]
    if pc or one_liner or score_big:
        oneliner_html = f'<div class="hook-line">「{one_liner}」</div>' if one_liner else ""
        scoreboard_html = ""
        if score_big:
            # 比分大字：把 "3 : 0" 拆成 主 : 客，中间冒号金色
            sc = score_big.replace("：", ":")
            if ":" in sc:
                hsc, asc = [x.strip() for x in sc.split(":", 1)]
                score_inner = f'{hsc}<span class="sb-colon">:</span>{asc}'
            else:
                score_inner = score_big
            alts_html = ""
            if score_alts:
                chips = "".join(f'<span class="sb-alt-chip">{a}</span>' for a in score_alts)
                alts_html = f'<div class="sb-alts"><span class="sb-alts-lbl">其他可能</span>{chips}</div>'
            home_crest = home_name_h[0] if home_name_h else "主"
            away_crest = away_name_h[0] if away_name_h else "客"
            scoreboard_html = f'''
            <div class="scoreboard">
              <div class="sb-arena">
                <div class="sb-side">
                  <div class="sb-crest sb-crest-home">{home_crest}</div>
                  <div class="sb-team">{home_name_h}</div>
                </div>
                <div class="sb-mid">
                  <div class="sb-score">{score_inner}</div>
                </div>
                <div class="sb-side">
                  <div class="sb-crest sb-crest-away">{away_crest}</div>
                  <div class="sb-team">{away_name_h}</div>
                </div>
              </div>
              {alts_html}
              <div class="sb-tag">卡组对决可能打出的比分</div>
            </div>'''
        bars_block = f'''
            <div class="power-compare">
              <div class="pc-head"><span>{home_name_h}</span><span class="pc-head-mid">战力对比</span><span>{away_name_h}</span></div>
              {bars_html}
            </div>''' if bars_html else ""
        hook_html = f'''
        <div class="hook-box">
          {oneliner_html}
          {scoreboard_html}
          {bars_block}
        </div>'''

    # FC 内对阵元信息（不绑定现实赛程，仅展示游戏内卡组档位/阵容标签）
    match_meta_html = ""
    mm = d.get("match_meta")
    if mm:
        round_label = mm.get("round_label", "")  # 例: "FC 国家队套对位 · 第 1 轮"
        squad_tier = mm.get("squad_tier", "")    # 例: "PTG 八强强化档位"
        deck_note = mm.get("deck_note", "")      # 例: "双方均为满化学度国家队套"
        focus_text = mm.get("focus_text", "")    # 例: "卡组顶配对位 · 梅西+劳塔罗 vs 阿尔及利亚"
        round_html = f'<span class="mm-group">{round_label}</span>' if round_label else ""
        focus_html = f'<span class="mm-focus">⭐ {focus_text}</span>' if focus_text else ""
        tier_html = (
            f'<div class="mm-time"><span class="mm-icon">🎮</span><span class="mm-clock">{squad_tier}</span></div>'
            if squad_tier else ""
        )
        deck_html = (
            f'<div class="mm-venue"><span class="mm-icon">🃏</span><span>{deck_note}</span></div>'
            if deck_note else ""
        )
        match_meta_html = f'''
        <div class="match-meta">
          <div class="mm-row mm-info">
            {tier_html}
            {deck_html}
            <div class="mm-tags">{round_html}{focus_html}</div>
          </div>
        </div>
        '''

    data_badge_html = f'''
    <div class="data-badge">
      📊 <strong>数据来源：{EI["source_line"]}</strong>｜{EI["endorse"]}。基于 {EI["name"]} 游戏内卡组数据进行国家队对位推演。
    </div>
    '''

    points_html = ""
    if d.get("core_points"):
        items = "".join(f"<li>{p}</li>" for p in d["core_points"])
        points_html = f'<div class="section-title">核心判断</div><div class="points"><ol>{items}</ol></div>'

    # ---- 阵容区：分 Tab 切换 + 凑不齐 11 人则改文字（不强画阵容图）----
    # 规则：球星卡能凑满 11 人才出阵容图；不足 11 人（约旦/库拉索等）只用文字描述，不显示残缺阵型图。
    home = d["home"]
    away = d["away"]

    def _build_squad_panel(team, panel_id, active):
        """返回 (tab按钮html, tab面板html, 是否有阵容图)。"""
        name = team["name"]
        players = team.get("players", []) or []
        # enrich 真实球员（跳过空占位标记，如无门将卡的 GK 空槽，避免 enrich 报错）
        enriched = [enrich_player(dict(p)) if (p.get("spid") and not p.get("empty")) else dict(p)
                    for p in players]
        # 真正能上图的=有真实卡图的球员
        playable = [p for p in enriched
                    if p.get("spid") and not p.get("empty")
                    and not str(p.get("spid", "")).startswith("ext_")
                    and card_b64(p.get("spid")) is not None]
        # 空占位槽（主要是无门将卡的 GK 空槽）也算"已就位"——这类槽渲染时画体面占位卡，
        # 不该因为它没真实卡就把整套阵型降级成文字（瑞士/日本等无门将卡的队仍应出阵型图）。
        empty_ph = [p for p in enriched if p.get("empty")]
        has_pitch = (not team.get("is_fallback")) and (len(playable) + len(empty_ph)) >= 11
        act = " active" if active else ""
        show = "" if active else ' style="display:none;"'
        if has_pitch:
            fname = team.get("formation") or _FORMATIONS.get("nations", {}).get(name, {}).get("default", "4-3-3")
            pitch = render_formation(name, fname, enriched, nation_chem=True)
            body = f'<div class="squad-formation-label">{name} · {fname} 国家队套首发</div>{pitch}'
            btn_sub = fname
        else:
            # 凑不齐 11 人 → 文字描述（关键球员列表 + 兜底信息条），不画残缺阵型
            info = team.get("info", {}) or {}
            txt_players = [p for p in enriched if p.get("name")]
            txt_players.sort(key=lambda x: x.get("ovr") or 0, reverse=True)
            chips = "".join(
                f'<span class="squad-chip">{p.get("name")}<i>{p.get("ovr","")}</i></span>'
                for p in txt_players[:8])
            note = (f'<div class="squad-text-note">{name} 这套国家队卡里，挑出最能打的几张核心球星卡，'
                    f'看看里子有多硬。</div>')
            fb = render_fallback(info) if info else ""
            body = f'{note}<div class="squad-chips">{chips}</div>{fb}'
            btn_sub = "核心球星"
        btn = (f'<button class="squad-tab{act}" data-squad="{panel_id}" onclick="showSquad(\'{panel_id}\')">'
               f'{name}<span class="st-sub">{btn_sub}</span></button>')
        panel = f'<div class="squad-panel" id="squad-{panel_id}"{show}>{body}</div>'
        return btn, panel, has_pitch

    h_btn, h_panel, _ = _build_squad_panel(home, "home", True)
    a_btn, a_panel, _ = _build_squad_panel(away, "away", False)
    squad_tabs_html = (
        '<div class="section-title">📋 双方阵容（点击切换）</div>'
        f'<div class="squad-tabs">{h_btn}{a_btn}</div>'
        f'<div class="squad-panels">{h_panel}{a_panel}</div>'
    )
    # 占位变量（下方模板仍引用），阵容已并入 squad_tabs_html
    home_html = ""
    away_html = ""
    home_grid_html = ""

    variables_html = ""
    if d.get("key_variables"):
        items = "".join(f"<li>{v}</li>" for v in d["key_variables"])
        variables_html = f'<div class="section-title">关键变量</div><div class="points"><ol>{items}</ol></div>'

    # 焦点对决 - 海报式单卡（支持多组，每组带双方球星卡图 + 梗式看点）
    matchups_html = ""
    if d.get("key_matchups"):
        def _duel_side(side, right=False):
            nm = side.get("name") or side.get("player") or ""
            spid = side.get("spid")
            img = card_b64(spid) if spid else None
            lo = _lore_for(nm)
            tag = side.get("tag") or (lo.get("title") if lo else "")
            ovr = side.get("ovr")
            cls = "sd-side right" if right else "sd-side"
            # 可点击出详情：有 spid 即复用全局 showPlayer + STATS_DB（不另存球员数据，
            # 仅多挂几个 data 属性字符串；六维/特性全走 spid 查 STATS_DB，零重复）
            click_attrs = ""
            side_cls = cls
            if spid and not str(spid).startswith("ext_"):
                rec = _DB.get(str(spid)) or {}
                _ovr = ovr if (ovr not in (None, "", "—")) else rec.get("ovr", "")
                _panel = panel_b64(spid)
                click_attrs = (
                    f' data-spid="{spid}" data-name="{nm}" data-ovr="{_ovr}" '
                    f'data-role="{side.get("role") or rec.get("position","") or ""}" '
                    f'data-salary="{rec.get("salary","")}" data-nation="{rec.get("nationality","")}" '
                    f'data-note="" '
                    f'data-card="{img or ""}" data-panel="{_panel or ""}" '
                    f'onclick="showPlayer(this)"'
                )
                side_cls = cls + " sd-clickable"
            cls = side_cls
            if img:
                img_html = f'<img class="sd-card" src="{img}" alt="">'
            else:
                # 无卡面：做成有设计感的"剪影盾牌"占位，而不是空灰框
                crest_char = (nm[0] if nm else "?")
                img_html = (
                    '<div class="sd-card sd-card-ph">'
                    '<div class="sd-ph-shield">'
                    '<svg viewBox="0 0 56 64" width="62" height="70" fill="none" '
                    'stroke="rgba(244,211,94,0.5)" stroke-width="2">'
                    '<path d="M28 3l22 7v18c0 14-9 24-22 28C15 52 6 42 6 28V10z"/>'
                    '</svg>'
                    f'<div class="sd-ph-char">{crest_char}</div>'
                    '</div>'
                    '<div class="sd-ph-tip">整体作战</div>'
                    '</div>'
                )
            meta = f'<div class="sd-meta">{tag}</div>' if tag else ""
            # 招牌数据徽章（格斗游戏选人感）：badges=["速度 141","射门 136"]；无则回退 OVR
            badges = side.get("badges") or []
            is_blank_ovr = (ovr is None or ovr == "" or ovr == "—")
            if badges:
                chips = "".join(f'<span class="sd-badge">{b}</span>' for b in badges[:3])
                ovr_line = "" if is_blank_ovr else f'<span class="sd-ovr-chip">OVR {ovr}</span>'
                stat_html = f'<div class="sd-badges">{ovr_line}{chips}</div>'
            elif not is_blank_ovr:
                stat_html = f'<div class="sd-stat">OVR {ovr}</div>'
            elif not img:
                # 兜底侧没有 OVR：给一句中性强项描述，不露"—"
                stat_html = '<div class="sd-stat sd-stat-soft">整体防守 · 身体对抗</div>'
            else:
                stat_html = ""
            hint = '<div class="sd-tap-hint">点击查看球员详情 ›</div>' if click_attrs else ""
            return f'<div class="{cls}"{click_attrs}>{img_html}<div class="sd-name">{nm}</div>{meta}{stat_html}{hint}</div>'

        cards = []
        for m in d["key_matchups"][:3]:  # 最多 3 组焦点
            home_s = m.get("home_side") or {{"name": m.get("home", ""), "spid": m.get("home_spid"), "ovr": m.get("home_ovr"), "tag": m.get("home_tag")}}
            away_s = m.get("away_side") or {{"name": m.get("away", ""), "spid": m.get("away_spid"), "ovr": m.get("away_ovr"), "tag": m.get("away_tag")}}
            verdict = m.get("tilt_text") or m.get("verdict") or ""
            xf = m.get("x_factor", "")
            xf_html = f'<div class="sd-xfactor">🔑 {xf}</div>' if xf else ""
            cards.append(f'''<div class="spotlight-duel">
          <div class="sd-tag">焦点对决 · 话题1V1</div>
          <div class="sd-title">{m.get("title","")}</div>
          <div class="sd-arena">
            {_duel_side(home_s, False)}
            <div class="sd-vs">VS</div>
            {_duel_side(away_s, True)}
          </div>
          {xf_html}
          <div class="sd-verdict">{verdict}</div>
        </div>''')
        matchups_html = f'<div class="section-title">⚔️ 焦点对决</div>{"".join(cards)}'

    # 焦点组合 - 双方各取一条最核心战术链路
    links_html = ""
    if d.get("key_links"):
        home_link = next((l for l in d["key_links"] if l.get("team") in ("home","主队")), None)
        away_link = next((l for l in d["key_links"] if l.get("team") in ("away","客队")), None)
        cards = []
        if home_link:
            cards.append(f'''<div class="spotlight-link home">
              <div class="sl-team">{home_link.get("team_name","主队")}</div>
              <div class="sl-chain">{home_link.get("chain","")}</div>
              <div class="sl-desc">{home_link.get("desc","")}</div>
            </div>''')
        if away_link:
            cards.append(f'''<div class="spotlight-link away">
              <div class="sl-team">{away_link.get("team_name","客队")}</div>
              <div class="sl-chain">{away_link.get("chain","")}</div>
              <div class="sl-desc">{away_link.get("desc","")}</div>
            </div>''')
        if cards:
            links_html = f'<div class="section-title">🎯 焦点组合 · 双方核心链路</div><div class="spotlight-links">{"".join(cards)}</div>'

    conclusion_html = ""
    if d.get("conclusion"):
        conclusion_html = f'<div class="section-title">推演结论</div><div class="conclusion">{d["conclusion"]}</div>'
    if d.get("story"):
        conclusion_html += f'<div class="section-title">🎬 {EI["name"]} 卡组演绎剧情</div><div class="story-card">{d["story"]}</div>'

    playstyle_html = ""
    if d.get("playstyle"):
        tips = "".join(f'<div class="tip-box"><strong>{t["team"]}</strong>：{t["tip"]}</div>' for t in d["playstyle"])
        playstyle_html = f'<div class="section-title">{EI["name"]} 玩法建议</div>{tips}'

    followups_html = ""
    if d.get("follow_ups"):
        import html as _h
        chips = "".join(
            f'''<div class="followup" data-q="{_h.escape(str(f), quote=True)}" onclick="copyFollowup(this)">'''
            f'''<span class="fu-text">{f}</span><span class="fu-copy">⧉ 点击复制</span></div>'''
            for f in d["follow_ups"]
        )
        followups_html = (
            '<div class="section-title">你还可以继续问</div>'
            '<div class="fu-tip">💡 点任意一条即可复制，粘贴到龙虾对话框就能接着问</div>'
            f'<div class="followups">{chips}</div>'
        )

    # 软性收尾：不放下载按钮（三方口径味太重），改成「想自己上手就去搜 FC」
    # 两款游戏都可引导，不强制隔离——搜哪个都行
    cur_source = EI["source_line"]
    brand_footer = f'''<div class="brand-footer">
      <div class="brand-slogan">想自己上手摆一套？</div>
      <div class="brand-soft">本推演的球员能力、阵容数据来自 <strong>{cur_source}</strong>。
        想亲自试试这套对位的手感，直接去搜 <strong>「FC 足球世界」</strong>或<strong>「FC Online」</strong>就能开踢。</div>
      <div class="cta-bottom">数据全 · 真实 · 专业 · 世界之巅，即刻上场</div>
    </div>'''

    html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<title>{d["title"]}｜{EI["name"]} 数据推演</title>
<style>{CSS}</style>
</head>
<body>
<div class="container">
  <div class="brand-strip"><span class="bs-badge">{EI["badge"]}</span>{EI["name"]} · 国家队卡组对位推演</div>
  <div class="title">{d["title"]}</div>
  <div class="subtitle">{d.get("subtitle","")}</div>
  {match_meta_html}
  {hook_html}
  {summary_html}
  {data_badge_html}
  {points_html}
  {matchups_html}
  {squad_tabs_html}
  {links_html}
  {variables_html}
  {conclusion_html}
  {playstyle_html}
  {followups_html}
  {brand_footer}
  <div class="disclaimer"><strong>本作品由 FC 爱好者基于游戏内公开数据自行制作，非 {EI["name"]} 及其运营方的官方产品，亦未获官方授权。</strong>内容仅基于 {EI["name"]} 游戏内{"" if eng=="mobile" else " PTG 赛季"}国家队卡组数据进行虚拟对位推演，<strong>不构成对任何现实赛事结果的预测、不与现实赛程或赛果存在关联</strong>，仅供 {EI["name"]} 玩家了解卡组数据与游戏内国家队套搭配参考。所有结论以游戏内实际对战为准。</div>
</div>

<!-- 球员详情弹窗 -->
<div class="modal-backdrop" id="playerModal" onclick="closePlayer(event)">
  <div class="modal-box" onclick="event.stopPropagation()">
    <button class="modal-close" onclick="closePlayer()">×</button>
    <div class="modal-header">
      <img id="m-card" class="mcard" src="" alt="">
      <div class="meta">
        <h3 id="m-name"></h3>
        <div class="meta-row"><strong>总评</strong><span id="m-ovr"></span><span style="color:var(--muted);margin-left:8px;font-size:11px;">({"世界之巅赛季强化版本" if eng=="mobile" else "PTG 赛季 8 强强化版本"})</span></div>
        <div class="meta-row"><strong>位置/角色</strong><span id="m-role"></span></div>
        <div class="meta-row"><strong>国籍</strong><span id="m-nation"></span></div>
        <div class="meta-row"><strong>工资</strong><span id="m-salary"></span></div>
        <div id="m-body" class="meta-row" style="display:none;"><strong>身体数据</strong><span id="m-body-val"></span></div>
        <div id="m-feet" class="meta-row" style="display:none;"><strong>弱足 / 花式</strong><span id="m-feet-val"></span></div>
      </div>
    </div>

    <!-- 球员能力解读（人话版）：自动根据六维 + 特性生成画像，给不玩 FC 的人看 -->
    <div id="m-summary-box" class="player-summary" style="display:none;">
      <div class="summary-icon">💡</div>
      <div class="summary-text" id="m-summary-text"></div>
    </div>

    <div id="m-stats-section" style="display:none;">
      <div class="modal-section-title">六维基础能力</div>
      <div class="radar-wrap">
        <div class="radar-svg" id="m-radar"></div>
        <div class="radar-legend" id="m-radar-legend"></div>
      </div>

      <div class="modal-section-title">分位置详细能力</div>
      <div class="pos-stats" id="m-pos-stats"></div>

      <div class="modal-section-title">球员特性</div>
      <div class="traits" id="m-traits"></div>
    </div>

    <div id="m-panel-section">
      <div class="modal-section-title" id="m-panel-title">📊 {EI["name"]} 游戏内信息面板（原图）</div>
      <img id="m-panel" class="modal-panel-img" src="" alt="">
    </div>
  </div>
</div>

<!-- 复制成功提示 -->
<div id="fuToast"></div>

<script>
const STATS_DB = {json.dumps(_filter_internal_stats(_STATS), ensure_ascii=False)};
const LORE_DB = {json.dumps(_lore_db, ensure_ascii=False)};
const ENGINE_NAME = {json.dumps(EI["name"], ensure_ascii=False)};
const SEASON_NAME = {json.dumps("世界之巅赛季" if eng=="mobile" else "PTG 赛季", ensure_ascii=False)};

// 倒计时已移除 — 合规要求：不绑定现实赛程时间

// 特性中文解释（不玩 FC 的人也看得懂）
const TRAIT_EXPLAIN = {{
  "闪电突破": "慢速盘带后能瞬间提速向前拨球，过人犀利",
  "渗透者": "倾向停留越位线边缘，反越位跑位强",
  "偷猎者": "接传中和倒三角时触发短时加速，禁区抢点能力强",
  "灵巧致胜": "凌空射门动作多样，蝎子摆尾等花式终结",
  "精准输送": "过顶直塞球的弧线和落点更优",
  "空中堡垒": "提前占据空中球落点，争顶强势",
  "坚固壁垒": "预判封堵中距离射门",
  "破坏者": "范围更大的站立抢断",
  "捍卫者": "失球后短时间内回追加速",
  "斗士": "对抗能力强化",
  "坚持不懈": "大幅减少奔跑体力消耗",
  "传球大师": "直塞球落点和力度精准",
  "早期传中爱好者": "更早起脚传中，制造威胁",
  "长传爱好者": "更倾向使用长传发动进攻",
  "善于头球": "头球争顶和射门能力强",
  "善于搓射": "搓射弧线和精度更好",
  "善于远射": "中远距离射门威胁大",
  "善于花式过人": "花式动作更流畅、过人成功率高",
  "速度盘带手": "高速盘带保持球性",
  "技术盘带手": "近身技术细腻，小范围摆脱强",
  "钢铁身躯": "对抗稳定，不易被推开",
  "玻璃身躯": "对抗较弱，需保护",
  "激进型抢断爱好者": "积极上抢，断球意识强",
  "麻烦制造者": "比赛中容易吃牌，但也制造对方麻烦"
}};

// 六维雷达图：返回 SVG 字符串
function renderRadar(dims, maxVal=145) {{
  const labels = Object.keys(dims);
  const values = Object.values(dims);
  const n = labels.length;
  const size = 280, cx = size/2, cy = size/2 + 8, R = 100;

  // 多边形顶点
  function point(i, r) {{
    const angle = -Math.PI/2 + 2*Math.PI * i / n;
    return [cx + r * Math.cos(angle), cy + r * Math.sin(angle)];
  }}

  // 同心环（25/50/75/100%）
  let rings = '';
  [0.25, 0.5, 0.75, 1].forEach(t => {{
    const pts = Array.from({{length: n}}, (_, i) => point(i, R*t).join(',')).join(' ');
    rings += `<polygon points="${{pts}}" fill="none" stroke="rgba(139,148,158,0.18)" stroke-width="1"/>`;
  }});
  // 轴线
  let axes = '';
  for (let i = 0; i < n; i++) {{
    const [x, y] = point(i, R);
    axes += `<line x1="${{cx}}" y1="${{cy}}" x2="${{x}}" y2="${{y}}" stroke="rgba(139,148,158,0.18)" stroke-width="1"/>`;
  }}
  // 数据多边形
  const dataPts = values.map((v, i) => point(i, R * Math.min(1, v/maxVal)).join(',')).join(' ');
  const dataPoly = `<polygon points="${{dataPts}}" fill="rgba(240,180,41,0.28)" stroke="#f0b429" stroke-width="2"/>`;

  // 数据点
  let dots = '';
  values.forEach((v, i) => {{
    const [x, y] = point(i, R * Math.min(1, v/maxVal));
    dots += `<circle cx="${{x}}" cy="${{y}}" r="3.5" fill="#f0b429" stroke="#0e1116" stroke-width="1.5"/>`;
  }});

  // 标签
  let texts = '';
  labels.forEach((lab, i) => {{
    const [x, y] = point(i, R + 22);
    texts += `<text x="${{x}}" y="${{y}}" fill="#e6edf3" font-size="12" font-weight="600" text-anchor="middle" dominant-baseline="middle">${{lab}}</text>`;
    const [vx, vy] = point(i, R + 38);
    texts += `<text x="${{vx}}" y="${{vy}}" fill="#f0b429" font-size="11" font-weight="700" text-anchor="middle" dominant-baseline="middle">${{values[i]}}</text>`;
  }});

  return `<svg viewBox="0 0 ${{size}} ${{size+20}}" width="100%" height="auto" xmlns="http://www.w3.org/2000/svg">
    ${{rings}}${{axes}}${{dataPoly}}${{dots}}${{texts}}
  </svg>`;
}}

// 自动生成能力解读（球迷口吻版，褒义为主，让不玩 FC 的人也能秒懂）
function generateSummary(name, role, stats, ovr) {{
  // 维度的"球感"形容词库（每条都褒义/中性）
  const DIM_STYLE = {{
    "速度":  {{ adj: ["疾如闪电", "提速凶猛", "拉开瞬间就是一段"], scene: "拉开身位、打反击、冲身后" }},
    "射门":  {{ adj: ["射术精湛", "禁区一脚冷血", "终结嗅觉一流"], scene: "禁区抢点、关键一击" }},
    "传球":  {{ adj: ["视野开阔", "落点拿捏精准", "出球节奏极佳"], scene: "组织串联、撕破防线" }},
    "盘带":  {{ adj: ["球感细腻", "护球如灵蛇出洞", "近身摆脱出色"], scene: "肋部突破、连续过人" }},
    "防守":  {{ adj: ["防守稳健", "拦截硬朗", "上抢果断"], scene: "中场绞肉、后防铁闸" }},
    "强壮":  {{ adj: ["对抗稳如磐石", "身体素质过硬", "顶在前面就是支点"], scene: "身体对抗、做球支点" }}
  }};
  const dimNames = {{"速度":"速度","射门":"射门","传球":"传球","盘带":"盘带","防守":"防守","强壮":"对抗"}};

  // 段落 1：身份介绍（褒义包装）；阈值随引擎数值体系切换（端游120~131 / 手游138~150）
  function tierWord(o) {{
    if (ENGINE_NAME.indexOf('足球世界') >= 0) {{
      if (o >= 148) return "现象级巨星卡";
      if (o >= 145) return "顶级球星卡";
      if (o >= 143) return "一线球星卡";
      if (o >= 141) return "豪华主力卡";
      if (o >= 139) return "稳定主力卡";
      return "实战可用卡";
    }}
    if (o >= 134) return "现象级巨星卡";
    if (o >= 132) return "顶级球星卡";
    if (o >= 130) return "一线球星卡";
    if (o >= 128) return "豪华主力卡";
    if (o >= 125) return "稳定主力卡";
    return "实战可用卡";
  }}
  const roleStr = role && role !== '—' ? `（${{role}}）` : '';
  // 球星梗：命中梗库则用"称号 + 段子钩子"开场，让画像有灵魂（球迷段子风）
  const lore = (typeof LORE_DB !== 'undefined') ? LORE_DB[name] : null;
  let p1;
  if (lore) {{
    const ttl = lore.title ? `——人称<strong>${{lore.title}}</strong>` : '';
    p1 = `<strong>${{name}}${{roleStr}}</strong>${{ttl}}，在 ${{SEASON_NAME}}里是<strong>${{tierWord(ovr)}}</strong>（总评 ${{ovr}}）。${{lore.hook || ''}}`;
  }} else {{
    p1 = `<strong>${{name}}${{roleStr}}</strong> 是 ${{SEASON_NAME}}的<strong>${{tierWord(ovr)}}</strong>，综合总评 <strong>${{ovr}}</strong>，从纸面到实战都站在最前排。`;
  }}

  // 没结构化数据，给"风采型"通用画像就够（有梗也先把梗带上）
  if (!stats || !stats.six_dims) {{
    return p1 + " 下方是这张卡的游戏内完整面板，六维能力、各位置详细数值、特性图标一目了然。";
  }}

  // 段落 2：用最强两项 + 最弱一项编"画像句"
  const d = stats.six_dims;
  const entries = Object.entries(d).map(([k,v]) => ({{k, v, label: dimNames[k]||k, style: DIM_STYLE[k]}}));
  entries.sort((a,b) => b.v - a.v);
  const top = entries.slice(0,2);
  const bottom = entries[entries.length-1];

  // 用形容词包装强项
  function pick(arr) {{ return arr[Math.floor(Math.random()*arr.length)]; }}
  const top1Adj = pick(top[0].style.adj);
  const top2Adj = pick(top[1].style.adj);

  let p2 = `招牌能力是 <strong>${{top[0].label}} ${{top[0].v}}</strong>，${{top1Adj}}，${{top[0].style.scene}}都是看家本领；同时 <strong>${{top[1].label}} ${{top[1].v}}</strong> 也很能打，${{top2Adj}}，让他在 ${{top[1].style.scene}}场景下同样吃得开。`;

  // 段落 3：弱项用"特化"代替"短板"
  let p3 = '';
  if (bottom.k === '防守' && bottom.v < 90) {{
    p3 = `作为进攻型球员，防守端不需要他冲在最前线——这恰恰让他能心无旁骛地把火力全开在前场。`;
  }} else if (bottom.k === '强壮' && bottom.v < 100) {{
    p3 = `身体对抗不是他的取胜之道，但他用<strong>技术和节奏</strong>把这一项变成了"不需要"。`;
  }} else if (bottom.k === '速度' && bottom.v < 110) {{
    p3 = `他不靠速度吃饭，<strong>位置感和球商</strong>才是他的真正武器。`;
  }} else if (bottom.v >= 100) {{
    p3 = `各项能力之间没有明显短板，是一张<strong>全能型</strong>球员卡。`;
  }}

  // 段落 4：弱足 + 花式（褒义包装）
  let p4 = '';
  if (stats.weak_foot === 5 && stats.skill_moves === 5) {{
    p4 = `更让人放心的是 <strong>弱足 ⭐⭐⭐⭐⭐ + 花式 ⭐⭐⭐⭐⭐</strong> 双满级——左右脚都能开火，花式动作信手拈来，可以说是<strong>"想怎么踢就怎么踢"</strong>的顶级技术型。`;
  }} else if (stats.weak_foot >= 4 && stats.skill_moves >= 4) {{
    p4 = `弱足和花式技巧都在 4 星以上，技术比较全面，没有明显死角。`;
  }} else if (stats.skill_moves >= 5) {{
    p4 = `花式技巧拉满 5 星，过人动作非常丰富，<strong>观赏性</strong>拉满。`;
  }} else if (stats.weak_foot >= 5) {{
    p4 = `弱足 5 星意味着两只脚都能终结，对手不知道该往哪边封堵。`;
  }}

  // 段落 5：身高/体型（可选）
  let p5 = '';
  if (stats.body && stats.body.height_cm) {{
    const h = stats.body.height_cm;
    if (h >= 188) p5 = `${{h}}cm 的身高也是一笔财富——空中作战和定位球场景下，他就是球队的<strong>制空堡垒</strong>。`;
    else if (h <= 170) p5 = `${{h}}cm 的身高反而让他重心更低，<strong>变向和爆发</strong>更显灵巧。`;
  }}

  return p1 + " " + p2 + (p3 ? " " + p3 : "") + (p4 ? " " + p4 : "") + (p5 ? " " + p5 : "");
}}

// 追问 chip 点击：复制问题文本 → 弹提示，可粘贴到龙虾对话框继续问
let _fuToastTimer = null;
function _showFuToast(msg) {{
  const t = document.getElementById('fuToast');
  if (!t) return;
  t.innerHTML = msg;
  t.classList.add('show');
  if (_fuToastTimer) clearTimeout(_fuToastTimer);
  _fuToastTimer = setTimeout(function(){{ t.classList.remove('show'); }}, 2600);
}}
function copyFollowup(el) {{
  const q = el.getAttribute('data-q') || (el.querySelector('.fu-text') ? el.querySelector('.fu-text').textContent : '');
  function done() {{
    el.classList.add('copied');
    const c = el.querySelector('.fu-copy'); const old = c ? c.textContent : '';
    if (c) c.textContent = '✓ 已复制';
    setTimeout(function(){{ el.classList.remove('copied'); if (c) c.textContent = old; }}, 1800);
    _showFuToast('✅ 已复制：<span class="ft-strong">「' + q + '」</span><br>粘贴到龙虾对话框，就能接着问～');
  }}
  if (navigator.clipboard && navigator.clipboard.writeText) {{
    navigator.clipboard.writeText(q).then(done).catch(function(){{ _fallbackCopy(q, done); }});
  }} else {{
    _fallbackCopy(q, done);
  }}
}}
function _fallbackCopy(text, cb) {{
  try {{
    const ta = document.createElement('textarea');
    ta.value = text; ta.style.position = 'fixed'; ta.style.opacity = '0';
    document.body.appendChild(ta); ta.focus(); ta.select();
    document.execCommand('copy'); document.body.removeChild(ta);
    cb();
  }} catch (e) {{
    _showFuToast('请长按选中文本手动复制：<br><span class="ft-strong">「' + text + '」</span>');
  }}
}}
function showSquad(which) {{
  document.querySelectorAll('.squad-panel').forEach(function(p){{ p.style.display = 'none'; }});
  document.querySelectorAll('.squad-tab').forEach(function(b){{ b.classList.remove('active'); }});
  var panel = document.getElementById('squad-' + which);
  if (panel) panel.style.display = '';
  document.querySelectorAll('.squad-tab').forEach(function(b){{
    if (b.dataset.squad === which) b.classList.add('active');
  }});
}}

function showPlayer(el) {{
  const spid = el.dataset.spid;
  const ovr = parseInt(el.dataset.ovr) || 0;
  const isExternal = !el.dataset.card || spid.startsWith('ext_');
  const mCard = document.getElementById('m-card');
  const mPanel = document.getElementById('m-panel');
  const mPanelTitle = document.getElementById('m-panel-title');
  if (el.dataset.card) {{
    mCard.src = el.dataset.card; mCard.style.display = '';
  }} else {{
    mCard.style.display = 'none';
  }}
  if (el.dataset.panel) {{
    mPanel.src = el.dataset.panel;
    mPanel.style.display = ''; mPanelTitle.style.display = '';
  }} else {{
    mPanel.style.display = 'none'; mPanelTitle.style.display = 'none';
  }}
  document.getElementById('m-name').textContent = el.dataset.name;
  document.getElementById('m-ovr').textContent = el.dataset.ovr;
  document.getElementById('m-role').textContent = el.dataset.role || '—';
  document.getElementById('m-nation').textContent = el.dataset.nation || '—';
  document.getElementById('m-salary').textContent = el.dataset.salary || '—';

  const stats = STATS_DB[spid];
  const statsSection = document.getElementById('m-stats-section');
  const summaryBox = document.getElementById('m-summary-box');

  // 能力解读（始终展示，无 stats 也给通用画像）
  summaryBox.style.display = 'flex';
  if (isExternal && el.dataset.note) {{
    // 外部球员用 note + 角色描述
    document.getElementById('m-summary-text').innerHTML =
      `<strong>${{el.dataset.name}}</strong>（${{el.dataset.role||''}} · OVR ${{ovr}}）：${{el.dataset.note}}。${{ENGINE_NAME}} 现役数据展示。`;
  }} else {{
    document.getElementById('m-summary-text').innerHTML = generateSummary(
      el.dataset.name, el.dataset.role, stats, ovr
    );
  }}

  if (stats) {{
    statsSection.style.display = 'block';

    // 身体
    if (stats.body) {{
      document.getElementById('m-body').style.display = '';
      document.getElementById('m-body-val').textContent = `${{stats.body.height_cm}}cm / ${{stats.body.weight_kg}}kg / ${{stats.body.model||''}}`;
    }}
    if (stats.weak_foot || stats.skill_moves) {{
      document.getElementById('m-feet').style.display = '';
      document.getElementById('m-feet-val').innerHTML = `${{'⭐'.repeat(stats.weak_foot||0)}} / ${{'⭐'.repeat(stats.skill_moves||0)}}`;
    }}
    // 六维雷达图 + 图例
    const dims = stats.six_dims || {{}};
    document.getElementById('m-radar').innerHTML = renderRadar(dims);
    const legend = document.getElementById('m-radar-legend'); legend.innerHTML = '';
    const sortedDims = Object.entries(dims).sort((a,b) => b[1]-a[1]);
    sortedDims.forEach(([k, v], i) => {{
      const cls = i < 2 ? ' top' : '';
      legend.innerHTML += `<div class="radar-legend-item${{cls}}"><span class="rl-name">${{k}}</span><span class="rl-val">${{v}}</span></div>`;
    }});
    // 分位置
    const ps = document.getElementById('m-pos-stats'); ps.innerHTML = '';
    const pos = stats.position_stats || {{}};
    for (const [posName, statsObj] of Object.entries(pos)) {{
      for (const [k, v] of Object.entries(statsObj)) {{
        ps.innerHTML += `<div class="pos-stat-item"><span class="psn">${{k}}</span><span class="psv">${{v}}</span></div>`;
      }}
    }}
    // 特性 + 中文解释
    const tr = document.getElementById('m-traits'); tr.innerHTML = '';
    let traitExplains = [];
    (stats.traits || []).forEach(t => {{
      const cls = t.type === '金特性' ? 'gold' : 'hold';
      tr.innerHTML += `<div class="trait-chip ${{cls}}">${{t.name}}<span style="color:var(--muted);margin-left:4px;font-size:10px;">${{t.type}}</span></div>`;
      const explain = TRAIT_EXPLAIN[t.name];
      if (explain) traitExplains.push(`<strong>${{t.name}}</strong>：${{explain}}`);
    }});
    if (traitExplains.length) {{
      tr.insertAdjacentHTML('afterend', `<div class="trait-explain">${{traitExplains.join('<br>')}}</div>`);
    }}
  }} else {{
    statsSection.style.display = 'none';
    document.getElementById('m-body').style.display = 'none';
    document.getElementById('m-feet').style.display = 'none';
  }}

  document.getElementById('playerModal').classList.add('active');
  document.body.style.overflow = 'hidden';
}}
function closePlayer(e) {{
  if (e && e.target.id !== 'playerModal' && !e.target.classList.contains('modal-close')) return;
  document.getElementById('playerModal').classList.remove('active');
  document.body.style.overflow = '';
  document.querySelectorAll('.trait-explain').forEach(n => n.remove());
}}
document.addEventListener('keydown', e => {{
  if (e.key === 'Escape') closePlayer({{target: document.getElementById('playerModal')}});
}});
</script>
</body>
</html>'''
    return html


def _dedupe_images(html):
    """后处理瘦身：同一张 base64 图常被嵌多次（阵型 img src + data-card 属性 + 焦点卡）。
    去重抽成全局 JS 数组 __IMG，把 base64 串替换成占位符 §IMGn§，加载时安全回填：
    - <img src="§IMGn§"> → 遍历 img 设 src
    - data-card="§IMGn§" / data-panel 等属性 → 遍历带该属性的元素回填
    不使用 innerHTML 重解析，避免破坏事件绑定。"""
    import re
    pattern = re.compile(r'data:image/(?:webp|png|jpeg);base64,[A-Za-z0-9+/=]+')
    seen = {}
    order = []

    def repl(m):
        s = m.group(0)
        if s not in seen:
            seen[s] = len(order)
            order.append(s)
        return f'§IMG{seen[s]}§'
    replaced = pattern.sub(repl, html)
    if not order:
        return html
    arr = "[" + ",".join(json.dumps(s) for s in order) + "]"
    restore = """
<script>
(function(){
  var I=""" + arr + """;
  function real(v){ if(!v) return v; var m=/^§IMG(\\d+)§$/.exec(v); return m? I[+m[1]] : v; }
  // 1) 所有 <img src="§IMGn§">
  document.querySelectorAll('img').forEach(function(el){
    var s=el.getAttribute('src'); if(s && s.indexOf('§IMG')===0) el.setAttribute('src', real(s));
  });
  // 2) 所有带 data-card / data-panel 占位的元素
  ['data-card','data-panel'].forEach(function(attr){
    document.querySelectorAll('['+attr+']').forEach(function(el){
      var s=el.getAttribute(attr); if(s && s.indexOf('§IMG')===0) el.setAttribute(attr, real(s));
    });
  });
  // 3) 内联 style background-image: url(§IMGn§)
  document.querySelectorAll('[style*="§IMG"]').forEach(function(el){
    el.setAttribute('style', el.getAttribute('style').replace(/§IMG(\\d+)§/g,function(_,n){return I[+n];}));
  });
})();
</script>"""
    if "</body>" in replaced:
        replaced = replaced.replace("</body>", restore + "\n</body>", 1)
    else:
        replaced += restore
    return replaced


def main():
    data = json.load(sys.stdin)
    html = render(data)
    html = _dedupe_images(html)
    out = Path(data.get("output_path") or "/tmp/fco_match.html")
    out.write_text(html, encoding="utf-8")
    print(str(out))


if __name__ == "__main__":
    main()
