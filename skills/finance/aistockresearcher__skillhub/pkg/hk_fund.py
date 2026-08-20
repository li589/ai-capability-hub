#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""港股基金/ETF 分析模块（v6.0 新增，零依赖纯标准库）

数据源说明（2026-07 实测）:
- 东财香港公募基金接口全部不可用:
  · fundmobapi FundMNewApi/FundMNHisNetList / FundMNFInfo → ErrCode 61136 "网络繁忙"（大陆基金同样报错，路由级失效）
  · fundmobapi FundMApi/FundNetDiagram.ashx → ErrCode 63116
  · fund.eastmoney.com/pingzhongdata/96xxxx.js → 404 页面
  fetch_hk_fund_nav 仍按候选端点依次探测（限流保护: 间隔≥1.5s、退避1/2/4s、Chrome120 UA），
  全部失败时优雅返回 {"error": ...}，绝不 traceback。
- 港股 ETF（5位代码，如 02800 盈富基金）走腾讯 r_hk K线（接口正常），
  用 K 线收盘价代替净值序列计算全套风险指标。
"""
from __future__ import annotations
import sys, json, math, re, time
from pathlib import Path
from typing import Optional

SKILL_DIR = Path(__file__).resolve().parents[1]

# 包内导入兼容: 既支持 `from pkg.hk_fund import ...`，也支持 sys.path 直挂 pkg/ 后 `import hk_fund`
try:
    from . import fund_analyzer as _fa
except ImportError:
    sys.path.insert(0, str(SKILL_DIR / "pkg"))
    import fund_analyzer as _fa

# 东财限流激进: UA 用 Chrome 120，请求间隔≥1.5s，指数退避重试(最多3次, 1/2/4s)
_UA_CHROME120 = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                 "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
_MIN_INTERVAL = 1.5
_last_req_ts = [0.0]


def _throttle():
    """全局限流: 保证相邻请求间隔 ≥ _MIN_INTERVAL 秒"""
    wait = _MIN_INTERVAL - (time.time() - _last_req_ts[0])
    if wait > 0:
        time.sleep(wait)
    _last_req_ts[0] = time.time()


def _http_get(url: str, referer: str = "https://fund.eastmoney.com/",
              timeout: int = 10, max_retry: int = 3) -> Optional[str]:
    """带限流+指数退避的 HTTP GET（东财接口专用），失败返回 None"""
    import urllib.request
    headers = {"User-Agent": _UA_CHROME120, "Referer": referer}
    for attempt in range(max_retry):
        _throttle()
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return resp.read().decode("utf-8-sig", errors="ignore")
        except Exception:
            if attempt < max_retry - 1:
                time.sleep(2 ** attempt)  # 退避 1s/2s
    return None


# ─────────────────────────────────────────────────────
# 香港公募基金净值（东财候选端点探测，2026-07 实测全部失效，保留探测逻辑以便日后恢复）
# ─────────────────────────────────────────────────────
def _parse_mobapi_his_net(raw: str, code: str) -> list[dict]:
    """解析 FundMNewApi/FundMNHisNetList 响应 → [{date, nav}]（字段名按东财移动端惯例尽力解析）"""
    try:
        data = json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return []
    if not data.get("Success") and data.get("ErrCode") not in (0, None):
        return []
    items = data.get("Datas") or []
    out = []
    for it in items:
        if not isinstance(it, dict):
            continue
        date_v = it.get("FSRQ") or it.get("NAVDATE") or it.get("date") or ""
        nav_v = it.get("DWJZ") or it.get("NAV") or it.get("nav")
        nav_f = _fa.safe_float(nav_v)
        if date_v and nav_f > 0:
            out.append({"date": str(date_v)[:10], "nav": nav_f})
    out.sort(key=lambda x: x["date"])
    return out


def _parse_pingzhong_hk(raw: str, code: str) -> tuple[str, list[dict]]:
    """解析 pingzhongdata/96xxxx.js（若港基也开通该接口）→ (name, [{date, nav}])"""
    name_m = re.search(r'var fS_name = "([^"]*)"', raw)
    nav_m = re.search(r'var Data_netWorthTrend = (\[.*?\]);', raw, re.S)
    if not nav_m:
        return "", []
    try:
        trend = json.loads(nav_m.group(1))
    except (json.JSONDecodeError, TypeError):
        return "", []
    from datetime import datetime
    hist = [{"date": datetime.fromtimestamp(p["x"] / 1000).strftime("%Y-%m-%d"),
             "nav": _fa.safe_float(p.get("y"))}
            for p in trend if p.get("x") and _fa.safe_float(p.get("y")) > 0]
    return (name_m.group(1) if name_m else ""), hist


def fetch_hk_fund_nav(code: str) -> dict:
    """获取香港公募基金历史净值（6位代码，如 968061）

    依次探测东财候选端点（限流: 间隔≥1.5s、退避重试、Chrome120 UA）。
    成功返回 {code, name, history: [{date, nav}], source}
    全部失败返回 {"error": ...}（2026-07 实测所有候选端点均不可用）
    """
    code = str(code).strip()
    if not (code.isdigit() and len(code) == 6):
        return {"error": f"香港公募基金代码应为6位数字(如968061)，收到: {code}"}

    candidates = [
        ("FundMNHisNetList",
         f"https://fundmobapi.eastmoney.com/FundMNewApi/FundMNHisNetList?FCODE={code}&pageIndex=1&pageSize=300",
         "mobapi"),
        ("pingzhongdata",
         f"https://fund.eastmoney.com/pingzhongdata/{code}.js",
         "pingzhong"),
    ]
    errors = []
    for name, url, kind in candidates:
        raw = _http_get(url)
        if not raw:
            errors.append(f"{name}: 无响应")
            continue
        if kind == "mobapi":
            hist = _parse_mobapi_his_net(raw, code)
            fund_name = ""
        else:
            # 404 反爬页面不含净值数据，解析会自然失败
            fund_name, hist = _parse_pingzhong_hk(raw, code)
        if hist:
            return {"code": code, "name": fund_name, "history": hist, "source": name}
        errors.append(f"{name}: 无有效净值数据")

    return {"error": (f"香港公募基金({code})净值获取失败: " + "; ".join(errors) +
                      "。可改用港股ETF路径 analyze_hk_etf(5位代码)")}


# ─────────────────────────────────────────────────────
# 港股 ETF 行情（腾讯 r_hk 接口，实测正常）
# ─────────────────────────────────────────────────────
# 常见港股 ETF 跟踪标的说明（不在表内的给出通用说明）
HK_ETF_TRACKING = {
    "02800": "盈富基金 — 跟踪恒生指数",
    "02828": "恒生中国企业ETF — 跟踪恒生中国企业指数(H股指数)",
    "03033": "南方恒生科技ETF — 跟踪恒生科技指数",
    "03032": "恒生科技ETF — 跟踪恒生科技指数",
    "03188": "华夏沪深300ETF — 跟踪沪深300指数",
    "02823": "安硕A50中国ETF — 跟踪富时中国A50指数",
    "03167": "工银南方国债ETF — 跟踪中债国债指数",
    "03081": "沛富基金 — 跟踪Markit iBoxx亚洲债券指数",
}


def _norm_hk5(code) -> str:
    """归一化为5位港股代码（'2800'/'02800'/'hk:02800' → '02800'）"""
    c = str(code).strip().lower()
    if c.startswith("hk:"):
        c = c[3:]
    c = re.sub(r"\D", "", c)
    return c.zfill(5)


def fetch_hk_kline(code, days: int = 300) -> list[dict]:
    """港股日K线（腾讯 ifzq.gtimg.cn）→ [{date, close}]，失败返回 []
    注意: K线接口港股前缀为 hk（如 hk02800）；r_hk 前缀仅行情接口(qt.gtimg.cn)可用，
    用于K线会返回 param error（2026-07 实测）。
    """
    import urllib.request
    code5 = _norm_hk5(code)
    for tc in (f"hk{code5}", f"r_hk{code5}"):
        url = f"https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param={tc},day,,,{days},qfq"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0",
                                                       "Referer": "https://gu.qq.com/"})
            with urllib.request.urlopen(req, timeout=8) as r:
                raw = r.read().decode("utf-8", errors="replace")
            raw = raw[raw.index("=") + 1:] if "=" in raw else raw
            data = json.loads(raw)
            sd = data.get("data", {}).get(tc, {})
            for k in ("qfqday", "day"):
                if k in sd:
                    return [{"date": i[0], "close": float(i[2])}
                            for i in sd[k][-days:] if len(i) >= 3 and float(i[2]) > 0]
        except Exception:
            continue
    return []


def fetch_hk_quote(code) -> dict:
    """港股实时行情（腾讯 qt.gtimg.cn）→ {name, price, chg_pct}，失败返回 {}"""
    import urllib.request
    tc = f"r_hk{_norm_hk5(code)}"
    try:
        req = urllib.request.Request(f"https://qt.gtimg.cn/q={tc}",
                                     headers={"User-Agent": "Mozilla/5.0",
                                              "Referer": "https://gu.qq.com/"})
        with urllib.request.urlopen(req, timeout=8) as r:
            raw = r.read().decode("gbk", errors="replace")
        f = raw.split('"')[1].split("~")
        if len(f) < 38:
            return {}
        return {"name": f[1], "price": _fa.safe_float(f[3]),
                "chg_pct": _fa.safe_float(f[32]), "currency": "HKD"}
    except Exception:
        return {}


# ─────────────────────────────────────────────────────
# 指标计算与评分（复用 fund_analyzer 的纯计算函数）
# ─────────────────────────────────────────────────────
def _metrics_from_prices(prices: list[float]) -> dict:
    """由净值/收盘价序列计算全套风险指标（年化收益/波动/夏普/Sortino/最大回撤/Calmar）"""
    rets = [(prices[i] / prices[i - 1] - 1)
            for i in range(1, len(prices)) if prices[i - 1] > 0]
    if len(rets) < 10:
        return {}
    n = len(rets)
    mean_ret = sum(rets) / n
    var = sum((r - mean_ret) ** 2 for r in rets) / n
    ann_ret = (1 + mean_ret) ** 252 - 1 if mean_ret > -1 else -1.0
    ann_vol = math.sqrt(var * 252)
    sharpe = (ann_ret - 0.03) / ann_vol if ann_vol > 0 else 0.0
    sortino = _fa._calc_sortino_ratio(rets)
    max_dd = _fa._calc_max_drawdown(prices)
    calmar = _fa._calc_calmar_ratio(rets, prices)
    return {
        "data_points": n,
        "annual_return_pct": round(ann_ret * 100, 2),
        "annual_vol_pct": round(ann_vol * 100, 1),
        "sharpe_ratio": round(sharpe, 2),
        "sortino_ratio": round(sortino, 3),
        "max_drawdown_pct": round(max_dd * 100, 2),
        "calmar_ratio": round(calmar, 3),
    }


def _score_from_metrics(m: dict, recent20_pct: float, details: list) -> tuple[int, str]:
    """四维评分(0-100): 近期表现30% + 夏普25% + 最大回撤25% + Sortino20%（子分口径与 score_fund_v3 一致）"""
    # 近期表现（近20交易日涨跌幅）
    if recent20_pct > 10:   perf_score = 90
    elif recent20_pct > 5:  perf_score = 75
    elif recent20_pct > 0:  perf_score = 60
    elif recent20_pct > -5: perf_score = 40
    else:                   perf_score = 20
    details.append(f"近期表现 {perf_score}分(权重30%) 近20日{recent20_pct:+.2f}%")

    sr = m["sharpe_ratio"]
    if sr > 1:      sharpe_score = 90
    elif sr > 0.3:  sharpe_score = 65
    elif sr > 0:    sharpe_score = 45
    else:           sharpe_score = 20
    details.append(f"夏普比率 {sharpe_score}分(权重25%) sharpe={sr:.2f}")

    dd = m["max_drawdown_pct"] / 100
    if dd < 0.10:   dd_score = 90
    elif dd < 0.20: dd_score = 75
    elif dd < 0.35: dd_score = 55
    elif dd < 0.50: dd_score = 35
    else:           dd_score = 15
    if m["calmar_ratio"] > 1:   dd_score = min(100, dd_score + 15)
    elif m["calmar_ratio"] > 0.5: dd_score = min(100, dd_score + 8)
    details.append(f"回撤控制 {dd_score}分(权重25%) 最大回撤={m['max_drawdown_pct']:.1f}% Calmar={m['calmar_ratio']:.2f}")

    so = m["sortino_ratio"]
    if so > 2:      sortino_score = 90
    elif so > 1:    sortino_score = 75
    elif so > 0.5:  sortino_score = 60
    elif so > 0:    sortino_score = 45
    else:           sortino_score = 20
    details.append(f"Sortino {sortino_score}分(权重20%) sortino={so:.2f}")

    total = round(perf_score * 0.30 + sharpe_score * 0.25
                  + dd_score * 0.25 + sortino_score * 0.20)
    total = max(0, min(100, total))
    grade = "A" if total > 75 else "B" if total > 55 else "C" if total > 40 else "D"
    return total, grade


def _build_score_result(code: str, name: str, prices: list[float],
                        dates: list[str], market: str, extra: Optional[dict] = None) -> dict:
    """由价格序列生成与 score_fund 系列同结构的评分结果"""
    m = _metrics_from_prices(prices)
    if not m:
        return {"code": code, "name": name, "market": market,
                "error": f"有效数据不足({len(prices)}点)，无法评分"}
    recent20_pct = (prices[-1] / prices[-21] - 1) * 100 if len(prices) >= 21 and prices[-21] > 0 else 0.0
    details: list = []
    score, grade = _score_from_metrics(m, recent20_pct, details)
    out = {
        "code": code,
        "name": name,
        "market": market,
        "score": score,
        "grade": grade,
        "details": details,
        "metrics": m,
        "period": f"{dates[0]} ~ {dates[-1]}" if dates else "",
    }
    if extra:
        out.update(extra)
    return out


# ─────────────────────────────────────────────────────
# 对外接口
# ─────────────────────────────────────────────────────
def analyze_hk_fund(code: str) -> dict:
    """分析香港公募基金（6位96开头代码，如 968061）

    复用 fund_analyzer 的风险指标计算，输出与 score_fund 系列同结构的评分结果。
    数据源不可用时优雅返回 {"error": ...}
    """
    nav = fetch_hk_fund_nav(code)
    if "error" in nav:
        return {"code": str(code), "market": "hk_fund", "error": nav["error"]}
    hist = nav["history"]
    prices = [h["nav"] for h in hist]
    dates = [h["date"] for h in hist]
    return _build_score_result(str(code), nav.get("name", ""), prices, dates,
                               market="hk_fund", extra={"source": nav.get("source", "")})


def analyze_hk_etf(code, days: int = 300) -> dict:
    """分析港股上市 ETF/基金（5位港股代码，如 02800 盈富基金）

    降级方案: 用腾讯港股 K 线收盘价代替净值序列，计算全套风险指标。
    """
    code5 = _norm_hk5(code)
    kline = fetch_hk_kline(code5, days=days)
    if len(kline) < 20:
        return {"code": code5, "market": "hk_etf",
                "error": f"港股ETF({code5})K线数据不足({len(kline)}条)，无法分析"}
    quote = fetch_hk_quote(code5)
    name = quote.get("name", "")
    tracking = HK_ETF_TRACKING.get(code5, "港股上市ETF/基金（跟踪标的未收录，请查阅基金公告）")
    prices = [k["close"] for k in kline]
    dates = [k["date"] for k in kline]
    result = _build_score_result(code5, name, prices, dates, market="hk_etf",
                                 extra={"tracking": tracking,
                                        "note": "以二级市场收盘价代替净值计算，含折溢价因素"})
    if quote:
        result["quote"] = quote
    return result


def score_hk_fund(code) -> dict:
    """港股基金统一入口
    - 5位数字(如 02800)     → 港股ETF路径 analyze_hk_etf
    - 6位96开头(如 968061)  → 香港公募基金路径 analyze_hk_fund
    - 其他                  → 返回错误说明
    """
    c = re.sub(r"\D", "", str(code).strip().lower().removeprefix("hk:"))
    if len(c) == 5:
        return analyze_hk_etf(c)
    if len(c) == 6 and c.startswith("96"):
        return analyze_hk_fund(c)
    return {"error": (f"无法识别的港股基金代码: {code}。"
                      "支持: 5位港股ETF代码(如02800) 或 6位96开头香港公募基金代码(如968061)")}


def get_hk_nav_series(code) -> tuple[list[float], list[str], str]:
    """供 fund_analyzer.predict_fund_short_term 复用: 取港股基金价格序列
    返回 (prices, dates, name)；失败时 prices 为 []
    """
    c = re.sub(r"\D", "", str(code).strip())
    if len(c) == 5:
        kline = fetch_hk_kline(c, days=300)
        return ([k["close"] for k in kline], [k["date"] for k in kline],
                fetch_hk_quote(c).get("name", ""))
    nav = fetch_hk_fund_nav(c)
    if "error" in nav:
        return [], [], ""
    return ([h["nav"] for h in nav["history"]],
            [h["date"] for h in nav["history"]], nav.get("name", ""))
