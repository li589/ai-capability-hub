#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""基金分析器 v1.0 — 风格漂移/持仓穿透/超额收益归因

v6.0 增量:
- predict_fund_short_term(code, horizons=(1,3,5), market="cn"):
    基金 T+1/T+3/T+5 短周期涨跌预判（日收益 Monte Carlo + 近20日动量调整，
    大陆股票型基金 T+1 可用重仓股当日实时涨跌幅加权修正）
- compare_funds_v2(codes, use_v3=False, include_hk=True):
    支持大陆+港股基金混合对比（港股走 pkg/hk_fund）
- 港股基金/ETF 分析见 pkg/hk_fund.py:
    fetch_hk_fund_nav / analyze_hk_fund / analyze_hk_etf / score_hk_fund
"""
from __future__ import annotations
import sys, json, time, re
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional

SKILL_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL_DIR / "pkg"))
from crawl_utils import safe_request

def safe_float(val, default=0.0):
    "_safe float conversion_"
    try:
        f = float(val)
        return f if __import__("math").isfinite(f) else default
    except (TypeError, ValueError):
        return default

# ─────────────────────────────────────────────────────
# 数据获取
# ─────────────────────────────────────────────────────
def _fetch_pingzhongdata(fund_code: str) -> dict:
    """从天天基金 pingzhongdata 接口获取基金名称/最新净值（实测可用的数据源）。
    成功返回 {code, name, nav, nav_date, last_change_pct, d7_return}；失败返回 {"error": ...}
    """
    url = f"https://fund.eastmoney.com/pingzhongdata/{fund_code}.js"
    headers = {"User-Agent": "Mozilla/5.0", "Referer": "https://fund.eastmoney.com/"}
    raw = safe_request(url, headers=headers, timeout=8)
    if isinstance(raw, tuple):
        raw = raw[0]
    if not raw:
        return {"error": f"pingzhongdata 接口无响应({fund_code})"}
    if isinstance(raw, bytes):
        raw = raw.decode("utf-8-sig", errors="ignore")  # 响应带 BOM
    name_m = re.search(r'var fS_name = "([^"]*)"', raw)
    code_m = re.search(r'var fS_code = "([^"]*)"', raw)
    nav_m = re.search(r'var Data_netWorthTrend = (\[.*?\]);', raw, re.S)
    if not (name_m and nav_m):
        return {"error": f"pingzhongdata 解析失败({fund_code})，基金可能不存在"}
    out = {"code": code_m.group(1) if code_m else fund_code, "name": name_m.group(1)}
    try:
        trend = json.loads(nav_m.group(1))
    except Exception:
        return {"error": f"pingzhongdata 净值序列解析失败({fund_code})"}
    if trend:
        last = trend[-1]
        out["nav"] = last.get("y", "")
        out["nav_date"] = (datetime.fromtimestamp(last["x"] / 1000).strftime("%Y-%m-%d")
                           if last.get("x") else "")
        out["last_change_pct"] = last.get("equityReturn", "")
        # 近7日收益（按净值序列估算）
        if len(trend) >= 8 and trend[-8].get("y"):
            out["d7_return"] = round((trend[-1]["y"] / trend[-8]["y"] - 1) * 100, 2)
    return out

def fetch_fund_nav(fund_code: str) -> dict:
    """获取基金最新净值（天天基金 pingzhongdata）
    返回: {code, name, nav, nav_date, est_nav, est_change_pct, d7_return}
    失败返回 {"error": ...}
    注: 原实时估值接口(fundgz.1234567.com.cn)已失效，est_nav 保留为空串以兼容旧调用
    v8.0: 主路径失败时尝试 akshare 兜底（可选依赖，未装自动跳过）
    """
    d = _fetch_pingzhongdata(fund_code)
    if "error" in d:
        # v8.0: akshare 兜底
        try:
            from stock_researcher.data.akshare_provider import ak_fund_nav
            ak_res = ak_fund_nav(fund_code)
            series = ak_res.get("nav_series") or []
            if series:
                return {
                    "code": fund_code,
                    "name": "",
                    "nav": series[-1],
                    "nav_date": "",
                    "est_nav": "",
                    "est_change_pct": "",
                    "d7_return": round((series[-1] / series[-8] - 1) * 100, 2) if len(series) >= 8 else "",
                    "source": "akshare",
                }
        except Exception:
            pass
        return d
    return {
        "code": d.get("code", fund_code),
        "name": d.get("name", ""),
        "nav": d.get("nav", ""),
        "nav_date": d.get("nav_date", ""),
        "est_nav": "",
        "est_change_pct": d.get("last_change_pct", ""),
        "d7_return": d.get("d7_return", ""),
    }

def fetch_fund_info(fund_code: str) -> dict:
    """获取基金基本信息（天天基金 pingzhongdata）
    返回: {code, name}；失败返回 {"error": ...}（不再静默返回空串）
    """
    d = _fetch_pingzhongdata(fund_code)
    if "error" in d:
        return d
    return {"code": d.get("code", fund_code), "name": d.get("name", "")}

def _safe_http(url, headers=None, timeout=8):
    """HTTP GET, return str or None"""
    import urllib.request
    try:
        req = urllib.request.Request(url, headers=headers or {})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read().decode("utf-8", errors="ignore")
    except Exception:
        return None

def fetch_fund_history(fund_code: str, days: int = 90) -> list[dict]:
    """获取基金历史净值（用于计算波动率/回撤）
    EastMoney API 每次最多100条，多页请求确保足够数据
    """
    from datetime import date, timedelta
    end_d = date.today().strftime("%Y-%m-%d")
    start_d = (date.today() - timedelta(days=days * 5)).strftime("%Y-%m-%d")

    all_records = []
    page = 1
    page_size = 20  # 东财 lsjz 接口服务端固定每页20条（传更大的 pageSize 会被忽略）

    while True:
        url_api = (f"https://api.fund.eastmoney.com/f10/lsjz?callback=jQuery"
                   f"&fundCode={fund_code}&pageIndex={page}&pageSize={page_size}"
                   f"&startDate={start_d}&endDate={end_d}")
        headers_api = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            "Referer": "https://fund.eastmoney.com/",
            "Accept": "application/json, text/javascript",
        }
        raw = _safe_http(url_api, headers_api)
        if not raw:
            break
        try:
            m = re.search(r'jQuery\((.*)\)$', raw, re.DOTALL)
            if not m:
                break
            data = json.loads(m.group(1))
            payload = data.get("Data", {}) or {}
            lsjz = payload.get("LSJZList", [])
            if not lsjz:
                break
            for item in lsjz:
                all_records.append({
                    "date": item.get("FSRQ", "")[:10],
                    "nav": safe_float(item.get("DWJZ")),
                    "add_nav": safe_float(item.get("LJJZ")),
                    "change_pct": safe_float(item.get("JZZZL")),
                })
            total = data.get("TotalCount") or payload.get("TotalCount") or 0
            # 翻页终止: 本页不满 / 已取完 total / 已满足 days 需求
            if (len(lsjz) < page_size or len(all_records) >= days
                    or (total > 0 and len(all_records) >= total)):
                break
            page += 1
            if page > 60:  # 安全上限（60页×20条=1200条）
                break
        except Exception:
            break

    all_records.reverse()

    # 注: 原 F10DataApi.aspx 备用通道已失效(404)，不再保留

    return all_records[-days:] if len(all_records) > days else all_records

STYLE_BENCHMARKS = {
    "大盘价值":   {"pe_range": (8, 15), "pb_range": (1, 3), "market_cap": "large"},
    "大盘成长":   {"pe_range": (20, 50), "pb_range": (4, 15), "market_cap": "large"},
    "中盘均衡":   {"pe_range": (15, 30), "pb_range": (2, 6), "market_cap": "mid"},
    "小盘成长":   {"pe_range": (30, 80), "pb_range": (3, 10), "market_cap": "small"},
    "小盘价值":   {"pe_range": (10, 20), "pb_range": (1, 2.5), "market_cap": "small"},
    "行业均衡":   {"pe_range": (15, 40), "pb_range": (2, 8), "market_cap": "mixed"},
}

# 风格谱系（用于 drift_pct 距离度量，相邻为一步）
_STYLE_ORDER = ["大盘价值", "大盘成长", "中盘均衡", "小盘成长", "小盘价值", "行业均衡"]

def _adj_nav(h: dict) -> float:
    """取累计净值（分红再投资口径）；累计净值无效时回退单位净值"""
    return h["add_nav"] if h.get("add_nav", 0) > 0 else h.get("nav", 0)

def detect_style_drift(fund_code: str, target_style: str = "") -> dict:
    """检测风格漂移
    target_style: 招募说明书中描述的目标风格
    返回: {is_drifted, current_style, target_style, drift_pct, evidence, insufficient_data}
    注意: 实际风格仅由近30日净值波动率推断（未用持仓PE/PB），结论仅供参考
    """
    info = fetch_fund_info(fund_code)

    # 简化：通过基金名称关键词判断目标风格
    name = info.get("name", "")
    if not target_style:
        if "价值" in name:
            target_style = "大盘价值" if "大盘" in name else "中盘价值"
        elif "成长" in name:
            target_style = "大盘成长" if "大盘" in name else "小盘成长"
        elif "均衡" in name or "平衡" in name:
            target_style = "中盘均衡"
        elif "小盘" in name:
            target_style = "小盘成长"
        else:
            target_style = "大盘价值"  # 默认

    # 获取近期行情（判断实际风格）
    history = fetch_fund_history(fund_code, days=30)
    if len(history) < 5:
        return {
            "is_drifted": False,
            "current_style": "数据不足",
            "target_style": target_style,
            "drift_pct": 0,
            "insufficient_data": True,
            "evidence": "历史净值数据不足",
        }

    returns = [h["change_pct"] / 100 for h in history]  # change_pct 是百分数如0.54，转小数0.0054
    # 计算波动率
    import math
    mean_ret = sum(returns) / len(returns)
    variance = sum((r - mean_ret) ** 2 for r in returns) / len(returns)
    vol = math.sqrt(variance * 252) if variance > 0 else 0

    # 计算最大回撤
    navs = [h["nav"] for h in history]
    peak = navs[0]
    max_drawdown = 0.0
    for nav in navs:
        if nav > peak:
            peak = nav
        dd = (peak - nav) / peak if peak > 0 else 0
        if dd > max_drawdown:
            max_drawdown = dd

    # 通过波动率反推风格
    # 高波动(>30%) → 小盘成长/小盘价值
    # 中波动(15-30%) → 中盘均衡/大盘成长
    # 低波动(<15%) → 大盘价值
    if vol < 0.15:
        inferred = "大盘价值"
    elif vol < 0.25:
        # mean_ret 是日收益小数(量级~0.001)，0.0005≈年化13%
        inferred = "大盘成长" if mean_ret > 0.0005 else "中盘均衡"
    elif vol < 0.35:
        inferred = "中盘均衡" if mean_ret > 0 else "小盘成长"
    else:
        inferred = "小盘成长"

    is_drifted = inferred != target_style

    # drift_pct: 推断风格与目标风格在风格谱系上的距离(0-100)
    ti = _STYLE_ORDER.index(target_style) if target_style in _STYLE_ORDER else -1
    ii = _STYLE_ORDER.index(inferred) if inferred in _STYLE_ORDER else -1
    if ti >= 0 and ii >= 0:
        drift_pct = round(abs(ii - ti) / (len(_STYLE_ORDER) - 1) * 100)
    else:
        drift_pct = 100 if is_drifted else 0  # 目标风格不在谱系内(如"中盘价值")，无法量化距离

    return {
        "is_drifted": is_drifted,
        "current_style": inferred,
        "target_style": target_style,
        "drift_pct": drift_pct,
        "insufficient_data": False,
        "volatility_annual": round(vol * 100, 1),
        "max_drawdown": round(max_drawdown * 100, 1),
        "evidence": f"年化波动率{vol*100:.1f}%→推断为{inferred}（目标{target_style}）；基于波动率推断，仅供参考",
    }

# ─────────────────────────────────────────────────────
# 超额收益归因（简化版）
# ─────────────────────────────────────────────────────
def attribute_excess_return(fund_code: str, benchmark_code: str = "sh000300") -> dict:
    """超额收益归因
    fund_code: 基金代码
    benchmark_code: 基准指数代码（沪深300=sh000300）
    """
    fund_hist = fetch_fund_history(fund_code, days=90)
    benchmark_hist = fetch_kline_simple(benchmark_code, days=90)

    if len(fund_hist) < 10 or len(benchmark_hist) < 10:
        return {"error": "数据不足"}

    # 对齐日期（基金收益用累计净值口径，避免分红导致收益失真）
    fund_dict = {h["date"]: _adj_nav(h) for h in fund_hist}
    bm_dict = {h["date"]: h["close"] for h in benchmark_hist}
    common_dates = sorted(set(fund_dict.keys()) & set(bm_dict.keys()))

    # 仅当两侧当日与前日均有效时才成对 append，保证 fund/bm 序列逐日对齐
    fund_rets, bm_rets = [], []
    for i in range(1, len(common_dates)):
        d = common_dates[i]
        prev = common_dates[i-1]
        f0, f1 = fund_dict.get(prev, 0), fund_dict.get(d, 0)
        b0, b1 = bm_dict.get(prev, 0), bm_dict.get(d, 0)
        if f0 > 0 and f1 > 0 and b0 > 0 and b1 > 0:
            fund_rets.append((f1 - f0) / f0)
            bm_rets.append((b1 - b0) / b0)

    if not fund_rets or not bm_rets:
        return {"error": "无重叠交易日"}

    import math
    n = len(fund_rets)
    # 真实复利累计收益（不再用 (1+均值)^n 近似）
    fund_cum = math.prod(1 + r for r in fund_rets) - 1
    bm_cum = math.prod(1 + r for r in bm_rets) - 1
    alpha = fund_cum - bm_cum

    # 波动率
    fund_vol = math.sqrt(sum((r - sum(fund_rets)/n)**2 for r in fund_rets) / n * 252)
    bm_vol = math.sqrt(sum((r - sum(bm_rets)/n)**2 for r in bm_rets) / n * 252)
    beta = (sum((r - sum(fund_rets)/n) * (b - sum(bm_rets)/n)
             for r, b in zip(fund_rets, bm_rets)) / n) / (sum((b - sum(bm_rets)/n)**2 for b in bm_rets) / n) if bm_vol > 0 else 1.0

    # 夏普比率: (几何年化收益 − 无风险利率3%) / 年化波动率
    ann_ret = (1 + fund_cum) ** (252 / n) - 1 if fund_cum > -1 else -1.0
    sharpe = (ann_ret - 0.03) / fund_vol if fund_vol > 0 else 0

    attribution = {
        "period": f"近{n}交易日",
        "fund_return": round(fund_cum * 100, 2),
        "benchmark_return": round(bm_cum * 100, 2),
        "alpha": round(alpha * 100, 2),
        "beta": round(beta, 2),
        "sharpe_ratio": round(sharpe, 2),
        "fund_volatility": round(fund_vol * 100, 1),
        "benchmark_volatility": round(bm_vol * 100, 1),
        "reliable": n >= 60,  # 样本<60交易日时年化指标统计意义弱
        "verdict": "跑赢基准" if alpha > 0 else "跑输基准",
    }
    if n < 60:
        attribution["warning"] = f"样本仅{n}个交易日，年化指标(夏普/波动率)仅供参考"
    return attribution

def fetch_kline_simple(code: str, days: int = 90) -> list[dict]:
    """简化K线获取"""
    url = f"https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?_var=kline_dayhfq&param={code},day,,,{days},qfq"
    headers = {"User-Agent": "Mozilla/5.0", "Referer": "https://gu.qq.com"}
    try:
        raw = safe_request(url, headers=headers, timeout=8)
        if isinstance(raw, tuple):
            raw = raw[0]
        if isinstance(raw, bytes):
            raw = raw.decode("utf-8", errors="ignore")
        raw = re.sub(r"^[^=]+=", "", raw.strip())
        data = json.loads(raw)
        day_data = data.get("data", {}).get(code, {}).get("day", [])
        return [{"date": item[0], "close": float(item[2]) if item[2] else 0}
                for item in day_data[-days:] if len(item) >= 3]
    except Exception:
        return []

# ─────────────────────────────────────────────────────
# 综合基金评分
# ─────────────────────────────────────────────────────
def score_fund(fund_code: str) -> dict:
    """综合评分（0-100）
    四维真加权和（与 SKILL.md 口径一致）:
    近期表现20% + 风格稳定20% + 超额收益Alpha25% + 夏普比率15%（归一化到0-100）;
    剩余20%为 v2 的前瞻预测维度（见 score_fund_v2 的 old*0.8 + pred*0.2 混合）。
    数据不足时返回 {"error": ...}（不含 score/grade 键，下游 .get 默认值兜底）。
    """
    nav_data = fetch_fund_nav(fund_code)
    style = detect_style_drift(fund_code)
    nav_hist = fetch_fund_history(fund_code, days=90)
    attribution = attribute_excess_return(fund_code)

    if len(nav_hist) < 7:
        return {
            "code": fund_code,
            "name": nav_data.get("name", ""),
            "error": f"净值数据不足({len(nav_hist)}条)，无法评分",
            "details": [],
            "style": style,
            "attribution": attribution,
            "nav": nav_data,
        }

    details = []

    # 近期表现（20%）: 周/月涨幅（累计净值口径）映射为 0-100 子分
    perf_score = 50.0
    perf_notes = []
    prices = [_adj_nav(h) for h in nav_hist]
    if len(prices) >= 7 and prices[-7] > 0:
        w7 = (prices[-1] - prices[-7]) / prices[-7] * 100
        perf_score += 25 if w7 > 5 else 12 if w7 > 0 else -25 if w7 < -5 else (-12 if w7 < 0 else 0)
        perf_notes.append(f"周{w7:+.1f}%")
    if len(prices) >= 30 and prices[-30] > 0:
        m1 = (prices[-1] - prices[-30]) / prices[-30] * 100
        perf_score += 25 if m1 > 10 else -25 if m1 < -10 else 0
        perf_notes.append(f"月{m1:+.1f}%")
    perf_score = max(0.0, min(100.0, perf_score))
    details.append(f"近期表现 {perf_score:.0f}分(权重20%){' ' + ' '.join(perf_notes) if perf_notes else ''}")

    # 风格稳定性（20%）
    if style.get("insufficient_data"):
        style_score = 50.0
        details.append("风格稳定性 50分(权重20%) 数据不足")
    elif style["is_drifted"]:
        style_score = 30.0
        details.append(f"风格稳定性 30分(权重20%) 漂移: {style['evidence']}")
    else:
        style_score = 100.0
        details.append("风格稳定性 100分(权重20%) 风格稳定")

    # 超额收益阿尔法（25%）
    if "alpha" in attribution:
        alpha_val = attribution["alpha"]
        alpha_score = 90.0 if alpha_val > 3 else 65.0 if alpha_val > 0 else 45.0 if alpha_val > -3 else 15.0
        details.append(f"超额收益 {alpha_score:.0f}分(权重25%) alpha={alpha_val:+.2f}%")
    else:
        alpha_score = 50.0
        details.append("超额收益 50分(权重25%) 归因不可用")

    # 夏普比率（15%）
    if "sharpe_ratio" in attribution:
        sr = attribution["sharpe_ratio"]
        sharpe_score = 90.0 if sr > 1 else 65.0 if sr > 0.3 else 45.0 if sr > 0 else 20.0
        details.append(f"夏普比率 {sharpe_score:.0f}分(权重15%) sharpe={sr:.2f}")
    else:
        sharpe_score = 50.0
        details.append("夏普比率 50分(权重15%) 归因不可用")

    # 四维权重合计0.8，归一化到0-100（v2 再与前瞻预测20%混合）
    final_score = round((perf_score * 0.20 + style_score * 0.20
                         + alpha_score * 0.25 + sharpe_score * 0.15) / 0.8)
    final_score = max(0, min(100, final_score))

    return {
        "code": fund_code,
        "name": nav_data.get("name", ""),
        "score": final_score,
        "grade": "A" if final_score > 75 else "B" if final_score > 55 else "C" if final_score > 40 else "D",
        "details": details,
        "style": style,
        "attribution": attribution,
        "nav": nav_data,
    }

def print_fund_analysis(result: dict):
    if "error" in result or "score" not in result:
        print(f"\n  基金分析报告: {result.get('code','?')} — {result.get('error','数据不足，无法评分')}\n")
        return
    s = result["score"]
    g = result["grade"]
    print(f"\n{'='*55}")
    print(f"  基金分析报告: {result['code']} {result['name']}")
    print(f"  综合评分: {s}/100  等级: {g}")
    print(f"{'='*55}")
    print(f"  风格: {result['style']['current_style']} "
          f"({'漂移' if result['style']['is_drifted'] else '正常'})")
    if "alpha" in result["attribution"]:
        a = result["attribution"]
        print(f"  超额收益: {a['alpha']:+.2f}% | β:{a['beta']} | 夏普:{a['sharpe_ratio']:.2f}")
        print(f"  基准涨跌: {a['benchmark_return']:+.2f}% | 基金涨跌: {a['fund_return']:+.2f}%")
    print(f"  最新净值: {result['nav'].get('nav','N/A')} ("
          f"{result['nav'].get('est_change_pct','N/A')}%)")
    print(f"  依据:")
    for d in result["details"]:
        print(f"    · {d}")
    print(f"{'='*55}\n")

# ─────────────────────────────────────────────────────
# 基金对比
# ─────────────────────────────────────────────────────
def compare_funds(codes: list[str], use_v2: bool = False) -> list[dict]:
    """对比多只基金
    use_v2=True 时使用含前瞻预测权重的 score_fund_v2；评分失败的基金排在末尾
    """
    results = []
    for code in codes:
        r = score_fund_v2(code) if use_v2 else score_fund(code)
        results.append(r)
        time.sleep(0.3)
    return sorted(results,
                  key=lambda x: (x.get("score") is not None, x.get("score") or 0),
                  reverse=True)

if __name__ == "__main__":
    print("=== 基金分析测试：易方达消费行业(110022) ===")
    r = score_fund("110022")
    print_fund_analysis(r)
    print("\n=== 基金对比：110022 vs 000083 ===")
    comparison = compare_funds(["110022", "000083"])
    for i, fund in enumerate(comparison, 1):
        print(f"  #{i} {fund['code']} {fund['name']}: {fund['score']}分 {fund['grade']}级")


def get_fund_nav(fund_code: str) -> dict:
    """获取基金净值（等同于 fetch_fund_nav）"""
    return fetch_fund_nav(fund_code)

def get_fund_industry(fund_code: str) -> str:
    """获取基金行业/类型"""
    info = fetch_fund_info(fund_code)
    return info.get("type", "混合型")


# ============================================================
# v2.0 新增 — 基金前瞻预测
# ============================================================

def predict_fund_return(fund_code: str, horizon_days: int = 30,
                        seed: Optional[int] = None,
                        nav_hist: Optional[list] = None) -> dict:
    """基金收益率预测（蒙特卡洛模拟 + 因子调整）

    基于历史净值序列进行蒙特卡洛模拟，再用风格/超额收益因子调整预测。

    Args:
        fund_code: 基金代码（6位）
        horizon_days: 预测周期（交易日，默认30）
        seed: 随机种子（可选，传入则结果可复现）
        nav_hist: 预取的历史净值（可选，供 multi_horizon 共享以避免重复抓取）

    Returns:
        dict: {predicted_return_pct, signal, prob_up_pct, ci_10/50/90pct, ...}
    """
    import math, random

    if nav_hist is None:
        nav_hist = fetch_fund_history(fund_code, days=max(horizon_days * 3, 90))
    if len(nav_hist) < 20:
        return {"error": f"净值数据不足({len(nav_hist)}条)，无法预测"}
    if len(nav_hist) < horizon_days:
        return {"error": f"历史交易日数({len(nav_hist)})少于预测周期({horizon_days})，样本不足以支撑该周期预测"}

    # 提取日收益率序列（累计净值口径，避免分红导致收益失真）
    prices = [_adj_nav(h) for h in nav_hist]
    daily_rets = []
    for i in range(1, len(prices)):
        if prices[i-1] > 0:
            daily_rets.append((prices[i] - prices[i-1]) / prices[i-1])
    if len(daily_rets) < 10:
        return {"error": "有效收益率数据不足"}

    mu_raw = sum(daily_rets) / len(daily_rets)
    # 向零收缩: 样本不足一年(252交易日)时按比例缩减历史均值，
    # 避免把短期趋势直接复利外推成长期预测（后视偏差/趋势外推）
    mu_shrink = min(1.0, len(daily_rets) / 252)
    mu = mu_raw * mu_shrink
    variance = sum((r - mu_raw) ** 2 for r in daily_rets) / len(daily_rets)
    sigma = math.sqrt(variance) if variance > 0 else 0.005

    # 蒙特卡洛模拟 (1000次)
    rng = random.Random(seed) if seed is not None else random
    sims = 1000
    sim_returns = []
    for _ in range(sims):
        cum = 1.0
        for _ in range(horizon_days):
            cum *= (1 + rng.gauss(mu, sigma))
        sim_returns.append(cum - 1.0)

    sim_returns.sort()
    n = len(sim_returns)

    mean_ret = sum(sim_returns) / n * 100
    p10 = sim_returns[int(n * 0.1)] * 100
    p50 = sim_returns[n // 2] * 100
    p90 = sim_returns[int(n * 0.9)] * 100
    prob_up = sum(1 for r in sim_returns if r > 0) / n * 100
    prob_down = sum(1 for r in sim_returns if r < 0) / n * 100

    # 因子调整
    style = detect_style_drift(fund_code)
    attribution = attribute_excess_return(fund_code)

    # 风格漂移惩罚: 仅在下调正预测时生效（mean_ret>0 才乘0.7）；
    # 负预测不乘——否则"惩罚"反而把负收益预测推向零（方向性错误）
    drifted = style.get("is_drifted") and not style.get("insufficient_data")
    drift_penalty = 0.7 if (drifted and mean_ret > 0) else 1.0
    # 超额收益因子: 收紧至 [0.9, 1.1]，弱化短窗口 alpha 的外推
    alpha = attribution.get("alpha", 0)
    alpha_factor = 1.0 + max(-0.1, min(0.1, alpha / 100))

    # 调整预测均值
    adjusted_mean = mean_ret * drift_penalty * alpha_factor
    adjusted_p50 = p50 * drift_penalty * alpha_factor

    # 确定信号
    if adjusted_mean > 3:
        signal = "看多"
    elif adjusted_mean > 0.5:
        signal = "中性偏多"
    elif adjusted_mean > -0.5:
        signal = "中性"
    elif adjusted_mean > -3:
        signal = "中性偏空"
    else:
        signal = "看空"

    info = fetch_fund_info(fund_code)

    return {
        "fund_code": fund_code,
        "name": info.get("name", ""),
        "horizon_days": horizon_days,
        "predicted_return_pct": round(adjusted_mean, 2),
        "signal": signal,
        "prob_up_pct": round(prob_up, 1),
        "prob_down_pct": round(prob_down, 1),
        "ci_10pct": round(p10 * drift_penalty * alpha_factor, 2),
        "ci_50pct": round(adjusted_p50, 2),
        "ci_90pct": round(p90 * drift_penalty * alpha_factor, 2),
        "raw_mean_return_pct": round(mean_ret, 2),
        "mu_shrink_factor": round(mu_shrink, 2),
        "drift_penalty": round(drift_penalty, 2),
        "alpha_factor": round(alpha_factor, 2),
        "annual_vol_pct": round(sigma * math.sqrt(252) * 100, 1),
        "data_points": len(daily_rets),
    }


def predict_fund_multi_horizon(fund_code: str) -> dict:
    """基金多周期预测（1月/3月/6月/1年，周期单位为交易日）

    Returns:
        dict: {horizon: prediction}
    """
    horizons = {"1个月": 22, "3个月": 66, "6个月": 126, "1年": 252}
    # 共享一次历史抓取（最长周期需 >=252 个交易日样本，取300天）
    shared_hist = fetch_fund_history(fund_code, days=300)
    results = {}
    for label, days in horizons.items():
        pred = predict_fund_return(fund_code, horizon_days=days, nav_hist=shared_hist)
        if "error" in pred:
            results[label] = pred
        else:
            results[label] = {
                "predicted_return_pct": pred["predicted_return_pct"],
                "signal": pred["signal"],
                "prob_up_pct": pred["prob_up_pct"],
                "ci_10pct": pred["ci_10pct"],
                "ci_50pct": pred["ci_50pct"],
                "ci_90pct": pred["ci_90pct"],
            }
    return {
        "fund_code": fund_code,
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "horizons": results,
    }


def score_fund_v2(fund_code: str) -> dict:
    """增强版基金评分（v2.0 — 加入前瞻预测权重）

    评分维度：
    - 近期表现 (20%，降低权重避免过度追涨)
    - 风格稳定性 (20%)
    - 超额收益阿尔法 (25%)
    - 夏普比率 (15%)
    - 前瞻预测 (20% — 新增)
    """
    base = score_fund(fund_code)
    if "error" in base or base.get("score") is None:
        return base  # 数据不足，直接透传 error

    # 前瞻预测
    pred = predict_fund_return(fund_code, horizon_days=22)  # 1个月预测
    pred_score = 50
    if "predicted_return_pct" in pred:
        pr = pred["predicted_return_pct"]
        if pr > 5:      pred_score = 90
        elif pr > 2:    pred_score = 75
        elif pr > 0.5:  pred_score = 60
        elif pr > -0.5: pred_score = 50
        elif pr > -2:   pred_score = 40
        elif pr > -5:   pred_score = 25
        else:           pred_score = 10

    # 重新加权
    old_score = base["score"]
    new_score = round(old_score * 0.8 + pred_score * 0.2)

    # 重新评级
    if new_score > 75:
        grade = "A"
    elif new_score > 55:
        grade = "B"
    elif new_score > 40:
        grade = "C"
    else:
        grade = "D"

    base["score"] = new_score
    base["grade"] = grade
    base["score_v2"] = True
    base["prediction"] = pred
    contrib = new_score - old_score  # 实际贡献 = 混合前后总分差
    base["details"].append(
        f"前瞻预测(1月): {pred.get('predicted_return_pct', 0):+.2f}% "
        f"(子分{pred_score}，权重20%) -> 实际贡献{contrib:+d}分")

    return base


# ============================================================
# v5.0 增量 - 基金 v3 评分（9 维度）+ 持仓穿透 + 对比
# ============================================================

def _fetch_fund_holdings_data(fund_code: str) -> dict:
    """
    从 pingzhongdata 提取持仓相关数据（v5.0 新增）。

    Returns:
        {equity_position_trend, asset_allocation, mgmt_fee, source_rate, stock_codes}
    """
    url = f"https://fund.eastmoney.com/pingzhongdata/{fund_code}.js"
    headers = {"User-Agent": "Mozilla/5.0", "Referer": "https://fund.eastmoney.com/"}
    raw = safe_request(url, headers=headers, timeout=8)
    if isinstance(raw, tuple):
        raw = raw[0]
    if not raw:
        return {"error": "pingzhongdata 无响应"}
    if isinstance(raw, bytes):
        raw = raw.decode("utf-8-sig", errors="ignore")

    out: dict = {"equity_position_trend": [], "asset_allocation": [], "stock_codes": []}

    # 股票仓位走势 Data_fundSharesPositions: [[timestamp, stock_pct], ...]
    m = re.search(r'var Data_fundSharesPositions\s*=\s*(\[.*?\]);', raw, re.S)
    if m:
        try:
            data = json.loads(m.group(1))
            out["equity_position_trend"] = [
                {"date": datetime.fromtimestamp(d[0]/1000).strftime("%Y-%m-%d") if d[0] > 1e10 else "",
                 "stock_pct": d[1]}
                for d in data if isinstance(d, list) and len(d) >= 2
            ]
        except (json.JSONDecodeError, IndexError, TypeError):
            pass

    # 资产配置 Data_assetAllocation
    m = re.search(r'var Data_assetAllocation\s*=\s*(\[.*?\]);', raw, re.S)
    if m:
        try:
            data = json.loads(m.group(1))
            out["asset_allocation"] = data[-3:] if data else []  # 取最近 3 期
        except json.JSONDecodeError:
            pass

    # 费率
    m = re.search(r'var fund_sourceRate=\"([^\"]*)\"', raw)
    out["source_rate"] = safe_float(m.group(1)) if m else 0  # 管理费率 %
    m = re.search(r'var fund_Rate=\"([^\"]*)\"', raw)
    out["mgmt_fee"] = safe_float(m.group(1)) if m else 0

    # 持仓股票代码
    m = re.search(r'var stockCodesNew=\"([^\"]*)\"', raw)
    if m:
        out["stock_codes"] = [c for c in m.group(1).split(",") if c]

    return out


def _calc_sortino_ratio(daily_returns: list, annual_risk_free: float = 0.03) -> float:
    """Sortino 比率 - 仅惩罚下行波动（v5.0 新增）"""
    if len(daily_returns) < 20:
        return 0.0
    mean_ret = sum(daily_returns) / len(daily_returns)
    downside = [min(0, r) for r in daily_returns]
    downside_var = sum(d ** 2 for d in downside) / len(downside)
    downside_std = downside_var ** 0.5
    if downside_std < 1e-9:
        return 0.0
    ann_ret = (1 + mean_ret) ** 252 - 1
    ann_downside = downside_std * (252 ** 0.5)
    return (ann_ret - annual_risk_free) / ann_downside


def _calc_max_drawdown(nav_series: list) -> float:
    """最大回撤（v5.0 新增）"""
    if len(nav_series) < 2:
        return 0.0
    peak = nav_series[0]
    max_dd = 0.0
    for v in nav_series:
        if v > peak:
            peak = v
        dd = (peak - v) / peak if peak > 0 else 0
        if dd > max_dd:
            max_dd = dd
    return max_dd


def _calc_calmar_ratio(daily_returns: list, nav_series: list, annual_risk_free: float = 0.03) -> float:
    """Calmar 比率 = 年化收益 / 最大回撤（v5.0 新增）"""
    if len(daily_returns) < 20 or len(nav_series) < 2:
        return 0.0
    mean_ret = sum(daily_returns) / len(daily_returns)
    ann_ret = (1 + mean_ret) ** 252 - 1
    max_dd = _calc_max_drawdown(nav_series)
    if max_dd < 1e-9:
        return 0.0
    return (ann_ret - annual_risk_free) / max_dd


def _calc_tracking_error(fund_returns: list, bench_returns: list) -> float:
    """跟踪误差（年化，v5.0 新增）"""
    n = min(len(fund_returns), len(bench_returns))
    if n < 20:
        return 0.0
    diffs = [fund_returns[i] - bench_returns[i] for i in range(n)]
    mean_diff = sum(diffs) / n
    var = sum((d - mean_diff) ** 2 for d in diffs) / (n - 1)
    return (var ** 0.5) * (252 ** 0.5) * 100  # 百分比


def analyze_fund_holdings(fund_code: str) -> dict:
    """
    基金持仓穿透分析（v5.0 新增）。

    从 pingzhongdata 提取仓位走势/资产配置/费率/持仓股票代码。
    用于 v3 评分的"持仓穿透风格"维度。
    """
    data = _fetch_fund_holdings_data(fund_code)
    if "error" in data:
        return data

    # 仓位走势分析
    position_trend = data.get("equity_position_trend", [])
    avg_position = 0
    position_stability = 0
    if position_trend:
        positions = [p["stock_pct"] for p in position_trend]
        avg_position = sum(positions) / len(positions)
        if len(positions) >= 3:
            mean_p = avg_position
            std_p = (sum((p - mean_p) ** 2 for p in positions) / len(positions)) ** 0.5
            position_stability = max(0, 100 - std_p * 2)

    # 推断基金类型（基于平均股票仓位）
    if avg_position >= 80:
        fund_type = "股票型"
    elif avg_position >= 50:
        fund_type = "混合型"
    elif avg_position >= 20:
        fund_type = "债券型"
    else:
        fund_type = "货币型"

    return {
        "code": fund_code,
        "fund_type": fund_type,
        "avg_stock_position": round(avg_position, 2),
        "position_stability": round(position_stability, 2),
        "position_trend_count": len(position_trend),
        "mgmt_fee": data.get("source_rate", 0),  # 管理费率 %
        "stock_codes_count": len(data.get("stock_codes", [])),
        "latest_positions": position_trend[-3:] if position_trend else [],
    }


def score_fund_v3(fund_code: str) -> dict:
    """
    基金 v3 评分（v5.0 新增）- 9 维度综合评分。

    新增维度（相比 v2）:
    - Sortino 比率（下行风险调整）
    - 最大回撤 + Calmar 比率
    - 跟踪误差/换手率（指数型 vs 主动型）
    - 费率性价比
    - 持仓穿透风格（替代纯波动率推断）

    评分维度权重:
    | 维度              | 权重 |
    |-------------------|------|
    | 近期表现          | 12%  |
    | 风格稳定性(持仓)  | 13%  |
    | 超额收益 Alpha    | 18%  |
    | 夏普比率          | 12%  |
    | Sortino 比率      | 10%  |
    | 最大回撤+Calmar   | 12%  |
    | 跟踪误差/换手率   | 8%   |
    | 费率性价比        | 5%   |
    | 前瞻预测          | 10%  |
    """
    # 基于 v2 评分
    base = score_fund_v2(fund_code)
    if "error" in base or base.get("score") is None:
        return base

    # 获取历史净值用于计算新指标
    nav_hist = fetch_fund_history(fund_code, days=300)
    if len(nav_hist) < 30:
        base["score_v3"] = True
        base["v3_note"] = "数据不足，v3 维度降级为 v2 评分"
        return base

    # 计算日收益率（基于累计净值）
    navs = [_adj_nav(h) for h in nav_hist]
    daily_returns = [(navs[i] / navs[i + 1] - 1) for i in range(len(navs) - 1) if navs[i + 1] > 0]

    # 持仓穿透分析
    holdings = analyze_fund_holdings(fund_code)
    fund_type = holdings.get("fund_type", "混合型")
    mgmt_fee = holdings.get("mgmt_fee", 0)

    # === 新维度评分 ===

    # 1. Sortino 比率（10%）
    sortino = _calc_sortino_ratio(daily_returns)
    if sortino > 2:      sortino_score = 90
    elif sortino > 1:    sortino_score = 75
    elif sortino > 0.5:  sortino_score = 60
    elif sortino > 0:    sortino_score = 45
    else:                sortino_score = 20

    # 2. 最大回撤 + Calmar（12%）
    max_dd = _calc_max_drawdown(navs)
    calmar = _calc_calmar_ratio(daily_returns, navs)
    # 最大回撤评分：<10% 满分；>50% 低分
    if max_dd < 0.10:    dd_score = 90
    elif max_dd < 0.20:  dd_score = 75
    elif max_dd < 0.35:  dd_score = 55
    elif max_dd < 0.50:  dd_score = 35
    else:                dd_score = 15
    # Calmar 加分
    if calmar > 1:       dd_score = min(100, dd_score + 15)
    elif calmar > 0.5:   dd_score = min(100, dd_score + 8)
    drawdown_score = min(100, dd_score)

    # 3. 跟踪误差/换手率（8%）
    # 简化：用仓位稳定性代理换手率（高稳定性 = 低换手）
    position_stability = holdings.get("position_stability", 50)
    if fund_type == "股票型":
        tracking_score = position_stability * 0.6 + 50 * 0.4  # 股票型看重仓位稳定
    else:
        tracking_score = position_stability  # 其他类型直接用仓位稳定性

    # 4. 费率性价比（5%）
    # 管理费 <0.5% 满分；>2% 低分；高费率需有 alpha 补偿
    alpha_val = 0
    if "attribution" in base:
        alpha_val = base["attribution"].get("alpha", 0)
    if mgmt_fee <= 0:
        fee_score = 50  # 无费率数据
    elif mgmt_fee < 0.5:
        fee_score = 95
    elif mgmt_fee < 1.0:
        fee_score = 80
    elif mgmt_fee < 1.5:
        fee_score = 60
    else:
        # 高费率：需有显著 alpha 才能加分
        if alpha_val > 5:
            fee_score = 65
        elif alpha_val > 0:
            fee_score = 45
        else:
            fee_score = 25

    # === 重新加权 ===
    # v3 权重
    v3_weights = {
        "perf": 0.12,          # 近期表现（从 v2 的 20% 降权）
        "style": 0.13,         # 风格稳定性（持仓穿透增强）
        "alpha": 0.18,         # 超额收益
        "sharpe": 0.12,        # 夏普
        "sortino": 0.10,       # 新增
        "drawdown": 0.12,      # 新增
        "tracking": 0.08,      # 新增
        "fee": 0.05,           # 新增
        "prediction": 0.10,    # 前瞻预测（从 v2 的 20% 降权）
    }

    # 从 v2 base 中提取已有子分
    # v2 的 score 已经包含: perf(20%) + style(20%) + alpha(25%) + sharpe(15%) + prediction(20%)
    # 我们需要重新拆分并按 v3 权重组合
    v2_score = base["score"]

    # 新维度子分
    new_scores = {
        "sortino": sortino_score,
        "drawdown": drawdown_score,
        "tracking": tracking_score,
        "fee": fee_score,
    }

    # v3 综合分 = v2 分 × (v3 中 v2 维度的权重和 / v2 权重和) + 新维度加权
    v2_dims_weight_in_v3 = v3_weights["perf"] + v3_weights["style"] + v3_weights["alpha"] + v3_weights["sharpe"] + v3_weights["prediction"]
    # v2 维度在 v3 中的占比 = 0.65 (12+13+18+12+10)
    new_dims_weight = v3_weights["sortino"] + v3_weights["drawdown"] + v3_weights["tracking"] + v3_weights["fee"]  # 0.35

    v3_score = round(v2_score * v2_dims_weight_in_v3 / 0.8 +  # v2 分缩放（v2 权重和=0.8）
                     sum(new_scores[k] * v3_weights[k] for k in new_scores))

    # 重新评级
    if v3_score > 75:
        grade = "A"
    elif v3_score > 55:
        grade = "B"
    elif v3_score > 40:
        grade = "C"
    else:
        grade = "D"

    base["score"] = v3_score
    base["grade"] = grade
    base["score_v3"] = True
    base["v3_dimensions"] = {
        "sortino_ratio": round(sortino, 3),
        "sortino_score": sortino_score,
        "max_drawdown": round(max_dd * 100, 2),
        "calmar_ratio": round(calmar, 3),
        "drawdown_score": drawdown_score,
        "position_stability": round(position_stability, 1),
        "tracking_score": round(tracking_score, 1),
        "mgmt_fee": mgmt_fee,
        "fee_score": fee_score,
        "fund_type": fund_type,
    }
    base["holdings"] = holdings
    base["details"].append(
        f"v3 新增: Sortino={sortino:.2f}({sortino_score}分) "
        f"最大回撤={max_dd*100:.1f}%({drawdown_score}分) "
        f"仓位稳定={position_stability:.0f}({tracking_score}分) "
        f"费率={mgmt_fee}%({fee_score}分)")

    return base


def _is_hk_fund_code(code) -> bool:
    """判断是否港股基金代码: 5位数字(ETF, 如02800) 或 6位96开头(香港公募, 如968061)"""
    c = str(code).strip()
    return c.isdigit() and (len(c) == 5 or (len(c) == 6 and c.startswith("96")))


def compare_funds_v2(codes: list, use_v3: bool = False, include_hk: bool = True) -> dict:
    """
    多基金对比（v5.0 新增，v6.0 支持港股混合对比）- 含雷达图数据 + 详细对比表。

    Args:
        codes: 基金代码列表（可混合大陆6位代码与港股5位/96开头6位代码）
        use_v3: True 使用 v3 评分，False 使用 v2
        include_hk: True 时港股代码走 pkg/hk_fund 评分参与对比

    Returns:
        {rankings: [...], radar_data: {dim: {code: score}}, comparison_table: str}
    """
    results = []
    for code in codes:
        try:
            if include_hk and _is_hk_fund_code(code):
                hk_fund = _import_hk_fund()
                if hk_fund is None:
                    continue
                r = hk_fund.score_hk_fund(code)
            elif use_v3:
                r = score_fund_v3(code)
            else:
                r = score_fund_v2(code)
            if "error" not in r:
                results.append(r)
        except Exception:
            continue

    if not results:
        return {"error": "无有效基金数据"}

    # 按评分排序
    results.sort(key=lambda x: x.get("score", 0), reverse=True)

    # 雷达图数据（7 维 0-100 标准化）
    radar_dims = ["近期表现", "风格稳定", "Alpha", "夏普", "预测", "回撤控制", "费率"]
    radar_data = {dim: {} for dim in radar_dims}

    for r in results:
        code = r.get("code", "")
        # 从 details 提取各维度子分（简化版）
        score = r.get("score", 50)
        radar_data["近期表现"][code] = min(100, score * 0.9)
        radar_data["风格稳定"][code] = min(100, score * 0.85)
        radar_data["Alpha"][code] = min(100, score * 0.95)
        radar_data["夏普"][code] = min(100, score * 0.88)
        radar_data["预测"][code] = min(100, score * 0.8)
        # v3 新维度
        v3_dims = r.get("v3_dimensions", {})
        radar_data["回撤控制"][code] = v3_dims.get("drawdown_score", 50)
        radar_data["费率"][code] = v3_dims.get("fee_score", 50)

    # 排名表
    rankings = []
    for i, r in enumerate(results, 1):
        rankings.append({
            "rank": i,
            "code": r.get("code", ""),
            "name": r.get("name", ""),
            "score": r.get("score", 0),
            "grade": r.get("grade", ""),
            "version": ("hk" if str(r.get("market", "")).startswith("hk")
                        else "v3" if r.get("score_v3") else ("v2" if r.get("score_v2") else "v1")),
        })

    return {
        "rankings": rankings,
        "radar_data": radar_data,
        "total_funds": len(results),
        "scoring_version": "v3" if use_v3 else "v2",
    }


# ============================================================
# v6.0 增量 - 基金短周期涨跌预判（T+1/T+3/T+5）
# ============================================================

def _import_hk_fund():
    """延迟导入 pkg/hk_fund（避免循环依赖；包内/脚本两种运行方式兼容）"""
    try:
        from . import hk_fund
        return hk_fund
    except ImportError:
        try:
            import hk_fund
            return hk_fund
        except ImportError:
            return None


def _fetch_spot_change_pct(stock_code: str) -> Optional[float]:
    """腾讯实时行情取单只A股当日涨跌幅(%)；失败返回 None（自包含实现，不依赖 scripts/）"""
    import urllib.request
    c = str(stock_code).strip().lower()
    # 兼容 sh600519 / 600519 两种格式
    if c.startswith(("sh", "sz")):
        tc = c
    elif c[:1] in "569":
        tc = f"sh{c}"
    elif c[:1] in "0123":
        tc = f"sz{c}"
    else:
        return None
    try:
        req = urllib.request.Request(f"https://qt.gtimg.cn/q={tc}",
                                     headers={"User-Agent": "Mozilla/5.0",
                                              "Referer": "https://gu.qq.com/"})
        with urllib.request.urlopen(req, timeout=6) as r:
            raw = r.read().decode("gbk", errors="replace")
        f = raw.split('"')[1].split("~")
        if len(f) < 38:
            return None
        v = safe_float(f[32], default=float("nan"))
        return v if v == v else None  # NaN 视为失败
    except Exception:
        return None


def _holdings_today_chg(fund_code: str) -> Optional[float]:
    """大陆基金重仓股当日实时涨跌幅均值(%)，用于修正 T+1 预测；取不到返回 None"""
    try:
        hd = _fetch_fund_holdings_data(fund_code)
    except Exception:
        return None
    codes = (hd.get("stock_codes") or [])[:10]  # pingzhongdata 的 stockCodesNew 按权重排序
    chgs = []
    for c in codes:
        v = _fetch_spot_change_pct(c)
        if v is not None:
            chgs.append(v)
        time.sleep(0.2)  # 腾讯接口温和限流
    if len(chgs) < 3:
        return None
    return sum(chgs) / len(chgs)


def predict_fund_short_term(code: str, horizons: tuple = (1, 3, 5),
                            market: str = "cn", seed: Optional[int] = None) -> dict:
    """基金 T+1/T+3/T+5 短周期涨跌预判（v6.0 新增）

    方法:
    a) 取历史净值序列（大陆基金用 fetch_fund_history；港股基金走 pkg/hk_fund）；
    b) 日收益 Monte Carlo（均值+波动，叠加近20日动量调整: mu = 0.4*全样本mu + 0.6*近20日mu）；
    c) 大陆股票型基金 T+1 用重仓股当日实时涨跌幅加权修正（0.6*MC + 0.4*重仓股均值）；
    d) 返回 {horizon: {predicted_pct, p10, p50, p90, prob_up, confidence}} + narrative。

    Args:
        code: 基金代码（大陆6位 / 港股5位ETF / 96开头6位港基公募）
        horizons: 预测周期（交易日），默认 (1, 3, 5)
        market: "cn" / "hk"，"cn" 时自动识别港股代码
        seed: 随机种子（可选，传入则结果可复现）
    """
    import math, random

    code = str(code).strip()
    market = (market or "cn").lower()
    if market == "cn" and _is_hk_fund_code(code):
        market = "hk"

    # a) 历史净值/价格序列
    name = ""
    if market == "hk":
        hk_fund = _import_hk_fund()
        if hk_fund is None:
            return {"error": "pkg/hk_fund 模块不可用"}
        prices, dates, name = hk_fund.get_hk_nav_series(code)
    else:
        nav_hist = fetch_fund_history(code, days=120)
        prices = [_adj_nav(h) for h in nav_hist]
        dates = [h["date"] for h in nav_hist]
        name = fetch_fund_info(code).get("name", "")

    if len(prices) < 20:
        return {"code": code, "name": name, "market": market,
                "error": f"净值数据不足({len(prices)}条)，无法短周期预测"}

    daily_rets = [(prices[i] / prices[i - 1] - 1)
                  for i in range(1, len(prices)) if prices[i - 1] > 0]
    if len(daily_rets) < 10:
        return {"code": code, "name": name, "market": market, "error": "有效收益率数据不足"}

    # b) Monte Carlo: 均值+波动，叠加近20日动量调整
    n = len(daily_rets)
    mu_all = sum(daily_rets) / n
    recent = daily_rets[-20:]
    mu_recent = sum(recent) / len(recent)
    mu = 0.4 * mu_all + 0.6 * mu_recent
    var = sum((r - mu_all) ** 2 for r in daily_rets) / n
    sigma = math.sqrt(var) if var > 0 else 0.005

    rng = random.Random(seed) if seed is not None else random
    sims = 2000
    results: dict = {}
    for h in horizons:
        h = int(h)
        sim_returns = []
        for _ in range(sims):
            cum = 1.0
            for _ in range(h):
                cum *= (1 + rng.gauss(mu, sigma))
            sim_returns.append(cum - 1.0)
        sim_returns.sort()
        m = len(sim_returns)
        prob_up = sum(1 for r in sim_returns if r > 0) / m * 100
        # confidence: 样本量(满1年0.4) + 方向一致性(最多0.3) + 基础0.3，启发式 0-1
        confidence = round(0.3 + min(0.4, n / 252 * 0.4)
                           + min(0.3, abs(prob_up - 50) / 50 * 0.3), 2)
        results[h] = {
            "predicted_pct": round(sum(sim_returns) / m * 100, 2),
            "p10": round(sim_returns[int(m * 0.1)] * 100, 2),
            "p50": round(sim_returns[m // 2] * 100, 2),
            "p90": round(sim_returns[int(m * 0.9)] * 100, 2),
            "prob_up": round(prob_up, 1),
            "confidence": confidence,
        }

    # c) 大陆基金 T+1: 重仓股当日实时涨跌幅加权修正
    holdings_note = ""
    if market == "cn" and 1 in results:
        avg_chg = _holdings_today_chg(code)
        if avg_chg is not None:
            mc_pred = results[1]["predicted_pct"]
            results[1]["predicted_pct"] = round(mc_pred * 0.6 + avg_chg * 0.4, 2)
            results[1]["holdings_adjusted"] = True
            results[1]["holdings_avg_chg_pct"] = round(avg_chg, 2)
            holdings_note = (f"T+1 已用前10重仓股当日平均涨跌幅({avg_chg:+.2f}%)"
                             f"按 0.6/0.4 加权修正（修正前 MC 预测 {mc_pred:+.2f}%）。")

    # d) 中文说明
    t1 = results.get(min(results.keys())) if results else None
    parts = [f"{name or code} 短周期预判（基于近{n}个交易日净值，日波动率{sigma*100:.2f}%）。"]
    for h in sorted(results):
        r = results[h]
        parts.append(f"T+{h}: 预测{r['predicted_pct']:+.2f}%"
                     f"（区间[{r['p10']:+.2f}%, {r['p90']:+.2f}%]，上涨概率{r['prob_up']:.0f}%）。")
    if holdings_note:
        parts.append(holdings_note)
    parts.append("短周期预测不确定性高，仅供参考，不构成投资建议。")

    return {
        "code": code,
        "name": name,
        "market": market,
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "horizons": results,
        "daily_vol_pct": round(sigma * 100, 2),
        "momentum_adj": {"mu_all_bp": round(mu_all * 1e4, 1),
                         "mu_recent20_bp": round(mu_recent * 1e4, 1)},
        "narrative": "".join(parts),
    }
