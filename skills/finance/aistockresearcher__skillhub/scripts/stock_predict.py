#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
零依赖全球股票涨跌预测引擎 v7.4
纯 Python 标准库实现，无需 pip install。
数据源: 腾讯财经免费接口（国内直连,无需API Key）
支持: A股(600519) / 港股(hk:00700) / 美股(us:AAPL)
      全球市场 v6.1: 指数(idx:N225/idx:SPX) / 商品期货(gold:comex/crude:wti)
      / 海外个股(jp:7203 等，走东方财富数据源，覆盖有限时友好降级)
"""

import json, math, random, statistics, sys, time, urllib.request, urllib.error

HTTP_TIMEOUT = 8  # 网络请求超时秒数

# ═══════════════ 市场识别 ═══════════════

# v6.1: 全球市场前缀（走东方财富数据源，stock_researcher.data.global_market）
GLOBAL_PREFIXES = ("jp:", "kr:", "uk:", "de:", "fr:", "au:", "in:", "tw:",
                   "ca:", "gold:", "silver:", "crude:", "fut:", "idx:")

# 币种符号表（v6.1 扩充）
CCY_SYMBOLS = {"CNY": "¥", "HKD": "HK$", "USD": "$", "JPY": "JP¥",
               "GBP": "£", "EUR": "€", "INR": "₹", "KRW": "₩",
               "TWD": "NT$", "AUD": "A$", "CAD": "C$"}


def _detect(code):
    """自动识别市场 → (prefix, normalized_code, market)
    注：市场分类的权威实现见 stock_researcher.data.market_classifier.MarketClassifier
    """
    c = str(code).strip()
    low = c.lower()
    # 全球市场显式前缀
    for p in GLOBAL_PREFIXES:
        if low.startswith(p):
            return "em", c, p[:-1]
    # hk:/us:/cn: 显式前缀
    if low.startswith("hk:"):
        return "r_hk", c[3:].zfill(5), "hk"
    if low.startswith("us:"):
        return "t_us", c[3:].upper(), "us"
    if low.startswith("cn:"):
        c2 = c[3:].zfill(6)
        return ("sh" if c2[0] in "5689" else "sz"), c2, "cn"
    # .HK / .US / .NYSE / .NASDAQ 后缀
    upper = c.upper()
    if upper.endswith(".HK"):
        return "r_hk", c[:-3].zfill(5), "hk"
    if upper.endswith(".US"):
        return "t_us", c[:-3].upper(), "us"
    if upper.endswith(".NYSE"):
        return "t_us", c[:-5].upper(), "us"
    if upper.endswith(".NASDAQ"):
        return "t_us", c[:-7].upper(), "us"
    # 纯字母 → 美股
    if upper == c and not c.isdigit() and 1 <= len(c) <= 5:
        return "t_us", upper, "us"
    # 4-5位纯数字 → 港股
    if c.isdigit() and len(c) <= 5:
        return "r_hk", c.zfill(5), "hk"
    # 默认 A 股
    c2 = c.zfill(6)
    return ("sh" if c2[0] in "689" else "sz"), c2, "cn"


def fval(v):
    try: return float(v)
    except (ValueError, TypeError): return 0.0


def _clamp(v, lo, hi):
    return lo if v < lo else hi if v > hi else v


# ═══════════════ 数据获取（多市场） ═══════════════

def _global_module():
    """延迟导入全球市场数据模块（v6.1），导入失败返回 None 友好降级"""
    try:
        import os
        d = os.path.dirname(os.path.abspath(__file__))
        if d not in sys.path:
            sys.path.insert(0, d)
        from stock_researcher.data import global_market
        return global_market
    except Exception:
        return None


def _exponential_backoff(attempt, base=0.5, max_delay=4.0):
    """指数退避：attempt 1→0.5s, 2→1s, 3→2s, 4→4s。

    v7.7 新增：用于网络请求重试。
    """
    return min(max_delay, base * (2 ** (attempt - 1)))


def fetch_quote(code, silent=False, max_retries=3):
    """实时行情 - 腾讯财经 qt.gtimg.cn（A股/港股/美股）+ 东方财富（全球市场）

    v7.7：增加指数退避重试（默认 3 次），提高网络抖动场景的鲁棒性。
    """
    prefix, norm, market = _detect(code)
    # v6.1: 全球市场委托东方财富数据源
    if prefix == "em":
        gm = _global_module()
        if gm is None:
            return {"error": "全球市场模块不可用（stock_researcher.data.global_market 导入失败）"}
        return gm.fetch_global_quote(norm)
    tc = f"{prefix}{norm}"
    if not silent:
        print(f"  ⏳ 获取 {code} 行情...", end="", flush=True, file=sys.stderr)
    last_err = None
    for attempt in range(1, max_retries + 1):
        try:
            req = urllib.request.Request(f"https://qt.gtimg.cn/q={tc}",
                headers={"User-Agent":"Mozilla/5.0","Referer":"https://gu.qq.com/"})
            with urllib.request.urlopen(req, timeout=HTTP_TIMEOUT) as r:
                raw = r.read().decode("gbk", errors="replace")
            if not silent:
                print(" ✔", file=sys.stderr)
            for line in raw.strip().split("\n"):
                if '"' not in line: continue
                f = line.split('"')[1].split("~")
                if len(f) < 38: continue
                # 通用字段（三市场共用）
                result = {
                    "name": f[1], "code": norm, "market": market,
                    "price": fval(f[3]), "prev_close": fval(f[4]),
                    "open": fval(f[5]), "vol": fval(f[6]),
                    "high": fval(f[33]), "low": fval(f[34]),
                    "amount": fval(f[38]), "change": fval(f[31]),
                    "chg_pct": fval(f[32]),
                }
                # 市场特定字段
                if market == "cn":
                    result["pe"] = fval(f[39])
                    result["turnover"] = fval(f[38])
                    result["currency"] = "CNY"
                elif market == "hk":
                    result["pe"] = fval(f[47]) if len(f) > 47 else 0
                    result["turnover"] = fval(f[39]) if len(f) > 39 else 0
                    result["currency"] = "HKD"
                else:
                    result["pe"] = fval(f[39]) if len(f) > 39 else 0
                    result["turnover"] = fval(f[38]) if len(f) > 38 else 0
                    result["currency"] = "USD"
                return result
            last_err = "返回数据为空"
        except urllib.error.URLError as e:
            last_err = e.reason
        except (OSError, Exception) as e:
            last_err = str(e)[:60]
        if attempt < max_retries:
            wait = _exponential_backoff(attempt)
            if not silent:
                print(f" (重试 {attempt+1}/{max_retries}，等 {wait}s)", end="", flush=True, file=sys.stderr)
            time.sleep(wait)
    if not silent:
        print(" ⚠", file=sys.stderr)
    proxy_hint = "请检查网络连接，关闭代理" if "proxy" in str(last_err).lower() or "tunnel" in str(last_err).lower() else "请检查网络连接"
    return {"error": f"网络请求失败（已重试 {max_retries} 次）: {last_err}", "hint": proxy_hint}



def fetch_kline(code, days=120, silent=False):
    """历史K线（前复权）- 腾讯财经（多市场）+ 东方财富（全球市场）"""
    prefix, norm, market = _detect(code)
    # v6.1: 全球市场委托东方财富数据源
    if prefix == "em":
        gm = _global_module()
        if gm is None:
            return []
        return gm.fetch_global_kline(norm, days)
    if market == "cn":
        tc = f"{prefix}{norm}"
    else:
        kp = {"hk": "hk", "us": "us"}.get(market, prefix)
        tc = f"{kp}{norm}"
    if not silent:
        print(f"  \u23f3 获取 {code} K线...", end="", flush=True, file=sys.stderr)
    try:
        url = f"https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param={tc},day,,,{days},qfq"
        req = urllib.request.Request(url, headers={"User-Agent":"Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=HTTP_TIMEOUT) as r:
            raw = r.read().decode("utf-8", errors="replace")
        if not silent:
            print(" \u2714", file=sys.stderr)
        raw = raw[raw.index("=")+1:] if "=" in raw else raw
        data = json.loads(raw)
        sd = data.get("data", {}).get(tc, {})
        for k in ("qfqday", "day"):
            if k in sd:
                return [{"date": i[0], "open": float(i[1]), "close": float(i[2]),
                    "high": float(i[3]), "low": float(i[4]), "vol": float(i[5])}
                    for i in sd[k][-days:] if len(i) >= 6]
    except (urllib.error.URLError, json.JSONDecodeError, KeyError, Exception) as e:
        if not silent:
            print(f" \u26a0 K线获取失败 ({type(e).__name__})", file=sys.stderr)
        return []


# ═══════════════ 技术指标（纯数学，零依赖） ═══════════════

def calc_rsi(closes, period=14):
    if len(closes) < period+1: return 50.0
    g = l = 0.0
    for i in range(len(closes)-period, len(closes)):
        d = closes[i] - closes[i-1]
        if d > 0: g += d
        else: l += abs(d)
    if l == 0: return 50.0 if g == 0 else 100.0
    return 100 - 100/(1 + g/l)


def calc_macd(closes, fast=12, slow=26, sig=9):
    if len(closes) < slow+sig: return {"dif": 0, "dea": 0, "hist": 0}
    def ema(d, p):
        r = [sum(d[:p])/p]; m = 2/(p+1)
        for i in range(p, len(d)): r.append(d[i]*m + r[-1]*(1-m))
        return r
    ef = ema(closes, fast); es = ema(closes, slow)
    n = min(len(ef), len(es))
    dif = [ef[-n+i] - es[-n+i] for i in range(n)]
    dea = ema(dif, sig)
    return {"dif": round(dif[-1], 4), "dea": round(dea[-1], 4),
        "hist": round((dif[-1]-dea[-1])*2, 4)}


def calc_boll(closes, period=20):
    if len(closes) < period: return {"up": 0, "mid": 0, "lo": 0, "w": 0, "pos": 50}
    r = closes[-period:]; mid = sum(r)/period
    std = math.sqrt(sum((x-mid)**2 for x in r)/period)
    up = mid + 2*std; lo = mid - 2*std; w = (up-lo)/mid*100 if mid != 0 else 0
    pos = (closes[-1]-lo)/(up-lo)*100 if up != lo else 50
    return {"up": round(up, 2), "mid": round(mid, 2), "lo": round(lo, 2),
        "w": round(w, 2), "pos": round(pos, 1)}


def calc_kdj(highs, lows, closes, period=9):
    if len(closes) < period: return {"k": 50, "d": 50, "j": 50}
    k = d = 50.0
    for i in range(len(closes)):
        s = max(0, i-period+1)
        hh = max(highs[s:i+1]); ll = min(lows[s:i+1])
        rsv = (closes[i]-ll)/(hh-ll)*100 if hh != ll else 50
        k = 2/3*k + 1/3*rsv; d = 2/3*d + 1/3*k
    j = 3*k - 2*d
    return {"k": round(k, 1), "d": round(d, 1), "j": round(j, 1)}


def calc_wr(highs, lows, closes, period=14):
    """威廉指标 WR: -100~0, <-80超卖, >-20超买"""
    n = min(len(highs), len(lows), len(closes))
    if n < period: return -50.0
    hh = max(highs[-period:]); ll = min(lows[-period:])
    if hh == ll: return -50.0
    return round((hh - closes[-1]) / (hh - ll) * -100, 2)


def calc_cci(highs, lows, closes, period=20):
    """商品通道指数 CCI: >+100超买, <-100超卖"""
    n = min(len(highs), len(lows), len(closes))
    if n < period: return 0.0
    tp = [(highs[i]+lows[i]+closes[i])/3 for i in range(n)]
    tp_slice = tp[-period:]; tp_avg = sum(tp_slice)/len(tp_slice)
    md = sum(abs(t-tp_avg) for t in tp_slice)/len(tp_slice)
    if md == 0: return 0.0
    return round((tp[-1]-tp_avg)/(0.015*md), 2)


def calc_mfi(highs, lows, closes, volumes, period=14):
    """资金流量指标 MFI: 0-100, >80超买, <20超卖"""
    n = min(len(highs), len(lows), len(closes), len(volumes))
    if n < period+1: return 50.0
    tp = [(highs[i]+lows[i]+closes[i])/3 for i in range(n)]
    pos_flow = neg_flow = 0.0
    for i in range(n-period, n):
        mf = tp[i] * volumes[i]
        if i > 0 and tp[i] > tp[i-1]: pos_flow += mf
        else: neg_flow += mf
    if neg_flow == 0: return 100.0
    return round(100 - 100/(1 + pos_flow/neg_flow), 1)


def calc_atr(highs, lows, closes, period=14):
    """真实波幅 ATR"""
    n = min(len(highs), len(lows), len(closes))
    if n < period+1: return 0.0
    tr = []
    for i in range(1, n):
        tr.append(max(highs[i]-lows[i], abs(highs[i]-closes[i-1]), abs(lows[i]-closes[i-1])))
    if not tr: return 0.0
    atr = sum(tr[:period])/period
    for i in range(period, len(tr)):
        atr = (atr*(period-1) + tr[i])/period
    return round(atr, 4)


def calc_adx(highs, lows, closes, period=14):
    """平均趋向指数 ADX: >25强趋势, <20震荡"""
    n = min(len(highs), len(lows), len(closes))
    if n < period*2: return {"adx": 0, "pdi": 0, "ndi": 0}
    tr_list, plus_dm, minus_dm = [], [], []
    for i in range(1, n):
        tr_list.append(max(highs[i]-lows[i], abs(highs[i]-closes[i-1]), abs(lows[i]-closes[i-1])))
        up = highs[i] - highs[i-1]; down = lows[i-1] - lows[i]
        plus_dm.append(up if up > down and up > 0 else 0)
        minus_dm.append(down if down > up and down > 0 else 0)
    # Wilder's smoothing
    atr_val = sum(tr_list[:period])
    pdi_sum = sum(plus_dm[:period]); ndi_sum = sum(minus_dm[:period])
    adx_vals = []
    for i in range(period, len(tr_list)):
        atr_val = atr_val - atr_val/period + tr_list[i]
        pdi_sum = pdi_sum - pdi_sum/period + plus_dm[i]
        ndi_sum = ndi_sum - ndi_sum/period + minus_dm[i]
        pdi = (pdi_sum/atr_val*100) if atr_val > 0 else 0
        ndi = (ndi_sum/atr_val*100) if atr_val > 0 else 0
        dx = abs(pdi-ndi)/(pdi+ndi)*100 if (pdi+ndi) > 0 else 0
        adx_vals.append(dx)
    if adx_vals:
        adx = sum(adx_vals[:period])/period if len(adx_vals) >= period else sum(adx_vals)/len(adx_vals)
        for i in range(period, len(adx_vals)):
            adx = (adx*(period-1) + adx_vals[i])/period
        return {"adx": round(adx, 1), "pdi": round(pdi_sum/period/atr_val*100 if atr_val > 0 else 0, 1),
                "ndi": round(ndi_sum/period/atr_val*100 if atr_val > 0 else 0, 1)}
    return {"adx": 0, "pdi": 0, "ndi": 0}


def calc_obv(closes, volumes):
    """能量潮 OBV — 只返回终值，O(1) 额外内存

    修复 BUG-002：原版用 `min(len(closes), len(volumes))` 但后续
    `closes[i] > closes[i-1]` 与 `volumes[i]` 用同一个 i，
    当 closes 比 volumes 长时 volumes[i] 会 IndexError。
    """
    n = min(len(closes), len(volumes))
    if n < 2:
        return 0.0
    obv = 0.0
    for i in range(1, n):
        # 修复 BUG-002：双侧长度保护（防御性编程）
        if i >= len(closes) or i >= len(volumes):
            break
        if closes[i] > closes[i-1]:
            obv += volumes[i]
        elif closes[i] < closes[i-1]:
            obv -= volumes[i]
    return obv


# ═══════════════ 蒙特卡洛模拟 ═══════════════

def monte_carlo(closes, price, sims=1000, seed=None):
    """蒙特卡洛模拟（GBM）。

    修复 BUG-003：原版用 `random.Random(seed)` 但 seed=None 时
    所有调用方共享同一序列，导致不同股票/不同日期的蒙特卡洛结果
    相关 → 降低模拟准确性。现改为：(1) seed=None 时用 price +
    len(closes) 派生确定性种子；(2) seed 显式传入时仍可复现。
    """
    if len(closes) < 10:
        return {"5d": {"avg":0,"up":0.5,"p50":price},"10d": {"avg":0,"up":0.5,"p50":price}}
    # 修复 BUG-003：基于输入数据派生确定性种子，避免共享全局状态
    if seed is None:
        seed = int((price * 1000 + len(closes)) % (2 ** 31 - 1))
    rng = random.Random(seed)
    rets = [closes[i]/closes[i-1]-1 for i in range(1, len(closes))]
    mu = statistics.mean(rets)
    sg = statistics.stdev(rets) if len(rets) > 1 else 0.02
    result = {}
    for days in (5, 10):
        fs = [0.0] * sims
        gauss = rng.gauss
        for i in range(sims):
            p = price
            for _ in range(days):
                p *= 1.0 + gauss(mu, sg)
            fs[i] = p if p > 0.01 else 0.01
        fs.sort(); n = sims//2
        result[f"{days}d"] = {
            "avg": round((statistics.mean(fs)-price)/price*100, 2),
            "up": round(sum(1 for x in fs if x > price)/sims, 2),
            "p50": round(fs[n], 2),
            "lo": round(fs[sims//10], 2), "hi": round(fs[sims*9//10], 2),
        }
    return result


# ═══════════════ 综合评分引擎（六维 v6.0） ═══════════════

def score(q, t, mc, closes, market="cn"):
    """七维评分 v7.0: 趋势22 + 动量18 + 量价12 + 波动8 + 概率18 + 环境12 + 黄金10 = 满分100"""
    # 趋势 (0-22) — MA排列 + ADX趋势强度
    tr = 11.0
    if not any(math.isnan(t[k]) for k in ("ma5","ma10","ma20")):
        if t["ma5"] > t["ma10"] > t["ma20"]: tr = 20
        elif t["ma5"] > t["ma10"]: tr = 16
        elif t["ma10"] > t["ma20"]: tr = 12
        else: tr = 6 if t["ma5"] < t["ma10"] < t["ma20"] else 9
        tr += sum(1.0 for m in ("ma5","ma10","ma20") if q["price"] > t[m] and not math.isnan(t[m]))
    adx_val = t.get("adx", {}).get("adx", 0) if isinstance(t.get("adx"), dict) else 0
    if adx_val > 25: tr += 2
    tr = _clamp(tr, 0, 22)
    # 动量 (0-18) — RSI+MACD+KDJ+WR+CCI
    mo = 9.0; rsi = t.get("rsi", 50)
    if rsi > 70: mo -= 3
    elif rsi > 60: mo += 3
    elif rsi < 30: mo -= 4
    elif rsi < 40: mo -= 2
    else: mo += 2
    mo += 3 if t.get("macd", {}).get("hist", 0) > 0 else -3
    kdj_j = t.get("kdj", {}).get("j", 50)
    if kdj_j > 85: mo -= 2
    elif kdj_j < 15: mo += 3
    wr = t.get("wr", -50)
    if wr < -80: mo += 3
    elif wr > -20: mo -= 2
    cci = t.get("cci", 0)
    if cci > 100: mo -= 2
    elif cci < -100: mo += 2
    mo = _clamp(mo, 0, 18)
    # 量价 (0-12) — 量比+MFI
    vp = 6.0; vr = t.get("vol_ratio", 1)
    if 1.2 <= vr <= 2.5: vp += 3
    elif vr > 2.5: vp += 1
    elif vr < 0.6: vp -= 3
    c = q["chg_pct"]
    if 1 <= c <= 5: vp += 2
    elif c > 5: vp += 1
    elif -5 <= c <= -1: vp -= 2
    elif c < -5: vp -= 3
    mfi = t.get("mfi", 50)
    if mfi < 20: vp += 2
    elif mfi > 80: vp -= 2
    vp = _clamp(vp, 0, 12)
    # 波动 (0-8) — 布林带位置+ATR风险
    vol_score = 4.0
    bp = t.get("boll", {}).get("pos", 50)
    if 30 <= bp <= 70: vol_score += 2
    elif bp < 15: vol_score -= 2
    elif bp > 85: vol_score -= 2
    atr_pct = t.get("atr_pct", 0)
    if atr_pct > 5: vol_score -= 2
    vol_score = _clamp(vol_score, 0, 8)
    # 概率 (0-18) — 蒙特卡洛模拟
    pr = 9.0
    if "5d" in mc: pr += (mc["5d"]["up"] - 0.5) * 22
    if "10d" in mc: pr += (mc["10d"]["up"] - 0.5) * 14
    pr = _clamp(pr, 0, 18)
    # 环境 (0-12) — v7.0 动态化：全球风险偏好 + 市场特征
    env = 6.0
    # 动态获取全球风险偏好
    try:
        global_risk = _get_cached_risk_appetite()
        if global_risk and global_risk.get("source_status") != "error":
            risk_score = global_risk["score"]
            if risk_score > 30: env += 4
            elif risk_score > 10: env += 2
            elif risk_score < -30: env -= 4
            elif risk_score < -10: env -= 2
    except Exception:
        pass
    # 市场特定调节
    if market == "hk": env += 1
    elif market in ("gold", "silver"): env += 2  # 商品通常受益于不确定性
    env = _clamp(env, 0, 12)
    # 黄金因子 (0-10) — v7.0 新增：仅对 gold 市场生效
    gf = 0
    if market == "gold":
        try:
            gold_factors = _get_cached_gold_factors()
            if gold_factors:
                gold_score = gold_factors["score"]
                # 将 -100~+100 映射到 0~10
                gf = _clamp((gold_score + 100) / 20, 0, 10)
        except Exception:
            gf = 5  # 默认中性

    total = tr + mo + vp + vol_score + pr + env + gf
    ma_stat = "多头排列" if (t.get("ma5",0) > t.get("ma10",0) > t.get("ma20",0)) else \
              ("空头排列" if (t.get("ma5",0) < t.get("ma10",0) < t.get("ma20",0)) else "震荡整理")
    return {"total": round(total, 1), "trend": round(tr, 1), "momentum": round(mo, 1),
        "vol": round(vp, 1), "volatility": round(vol_score, 1), "prob": round(pr, 1),
        "env": round(env, 1), "gold_factor": round(gf, 1), "ma": ma_stat}


# ── v7.0 缓存：全球风险偏好和黄金因子（避免重复请求）──
# 修复 BUG-001：原模块级单例缓存无锁，多线程/多实例会共享状态 + 竞态条件
_risk_cache = {"ts": 0, "data": None}
_gold_cache = {"ts": 0, "data": None}
_cache_lock = __import__("threading").Lock()


def _safe_cache_get(cache_dict, ttl_seconds=300):
    """线程安全的缓存读取：原子检查 + 返回。"""
    now = time.time()
    with _cache_lock:
        if (now - cache_dict["ts"] < ttl_seconds
                and cache_dict["data"] is not None):
            return cache_dict["data"]
    return None


def _safe_cache_set(cache_dict, data):
    """线程安全的缓存写入。"""
    with _cache_lock:
        cache_dict["data"] = data
        cache_dict["ts"] = time.time()


def _get_cached_risk_appetite():
    """缓存5分钟的全球风险偏好（线程安全）。"""
    cached = _safe_cache_get(_risk_cache, ttl_seconds=300)
    if cached is not None:
        return cached
    try:
        gm = _global_module()
        if gm and hasattr(gm, 'get_global_risk_appetite'):
            data = gm.get_global_risk_appetite()
            _safe_cache_set(_risk_cache, data)
            return data
    except Exception:
        pass
    return _risk_cache.get("data")  # 兜底返回过期值


def _get_cached_gold_factors():
    """缓存5分钟的黄金因子分析（线程安全）。"""
    cached = _safe_cache_get(_gold_cache, ttl_seconds=300)
    if cached is not None:
        return cached
    try:
        gm = _global_module()
        if gm and hasattr(gm, 'analyze_gold_factors'):
            data = gm.analyze_gold_factors()
            _safe_cache_set(_gold_cache, data)
            return data
    except Exception:
        pass
    return _gold_cache.get("data")  # 兜底返回过期值


# ═══════════════ 信号生成 ═══════════════

def signal(s):
    """根据综合分生成信号 + 置信度。

    修复 BUG-005：原版阈值 25→35 区间内置信度公式 `(t-25)*0.005`
    和 `(t-35)*0.01` 系数差 1 倍，导致跨越 35 边界时置信度跳跃。
    改为统一系数 0.008 (每分 0.8% 置信度)，平滑过渡。
    """
    t = s["total"]
    if t >= 70: sig, cf = "\U0001f4c8 强烈看涨", 0.8 + (t-70)*0.006
    elif t >= 60: sig, cf = "\U0001f4c8 看涨", 0.65 + (t-60)*0.015
    elif t >= 45: sig, cf = "\U0001f4ca 震荡偏强", 0.5 + (t-45)*0.008  # 修复 BUG-005
    elif t >= 35: sig, cf = "\U0001f4ca 震荡", 0.4 + (t-35)*0.008   # 修复 BUG-005
    elif t >= 25: sig, cf = "\U0001f4ca 震荡偏弱", 0.32 + (t-25)*0.008  # 修复 BUG-005
    elif t >= 15: sig, cf = "\U0001f4c9 看跌", 0.24 + (t-15)*0.008
    else: sig, cf = "\U0001f4c9 强烈看跌", max(0.10, 0.24 - (15-t)*0.008)
    return sig, round(min(cf, 0.95), 2)


# ═══════════════ 核心预测函数 ═══════════════

def predict(code, silent=False, quick_mode=False):
    """全球股票涨跌预测（A股/港股/美股/全球市场指数与期货）"""
    prefix, norm, market = _detect(code)

    q = fetch_quote(code, silent=silent)
    if not q: return {"error": f"无法获取{code}行情，请检查代码或网络", "hint": "关闭代理后重试，或确认代码格式正确"}
    # v6.1: 全球市场模块返回的明确错误（如不支持的个股市场）
    if "error" in q:
        err = dict(q)
        err["code"] = code
        return err
    # v6.1: 全球模块返回精确市场标签（如 idx:N225 → jp）
    if prefix == "em" and q.get("market"):
        market = q["market"]

    kl = fetch_kline(code, silent=silent)
    if kl:
        cl = [k["close"] for k in kl]
        hi = [k["high"] for k in kl]
        lo = [k["low"] for k in kl]
    else:
        p = q["price"]
        cl = [p] * 30
        hi = [p] * 30
        lo = [p] * 30
    vl = [k["vol"] for k in kl] if kl else [0]*30

    # 均线 - 只算终值, O(1)额外内存
    def _sma(d, p):
        n = len(d)
        if n < p:
            return sum(d)/n if n > 0 else float("nan")
        return sum(d[-p:]) / p

    m5 = _sma(cl, 5)
    m10 = _sma(cl, 10)
    m20 = _sma(cl, 20)
    m60 = _sma(cl, 60)
    vr = vl[-1]/(sum(vl[-6:-1])/5) if len(vl) >= 6 and sum(vl[-6:-1]) > 0 else 1.0

    # v6.0: 计算全部指标（含新增 6 个）
    t = {
        "ma5": round(m5, 2), "ma10": round(m10, 2),
        "ma20": round(m20, 2), "ma60": round(m60, 2),
        "rsi": round(calc_rsi(cl), 1),
        "macd": calc_macd(cl),
        "boll": calc_boll(cl),
        "kdj": calc_kdj(hi, lo, cl),
        "vol_ratio": round(vr, 2),
        # v6.0 新增指标
        "wr": calc_wr(hi, lo, cl),
        "cci": calc_cci(hi, lo, cl),
        "mfi": calc_mfi(hi, lo, cl, vl),
        "atr": round(calc_atr(hi, lo, cl), 4),
        "atr_pct": round(calc_atr(hi, lo, cl) / q["price"] * 100, 2) if q["price"] > 0 else 0,
        "adx": calc_adx(hi, lo, cl),
        "obv": round(calc_obv(cl, vl), 0),
    }

    mc = monte_carlo(cl, q["price"], seed=f"{norm}-{kl[-1]['date'] if kl else 'nodata'}")
    sc = score(q, t, mc, cl, market=market)
    sig, cf = signal(sc)

    currency = q.get("currency", "CNY")
    symbol = CCY_SYMBOLS.get(currency, "¥")

    sum_text = (f"{q['name']}({norm}) [{market.upper()}] 评分{sc['total']}/100 "
        f"信号:{sig}({cf:.0%}) 现价{symbol}{q['price']:.2f} "
        f"今日{q['chg_pct']:+.2f}% 均线:{sc['ma']} RSI:{t['rsi']:.0f}")

    return {
        "code": norm, "name": q["name"], "market": market,
        "price": {k: q.get(k, 0) for k in ("price","chg_pct","open","high","low","vol","amount","pe","turnover")},
        "currency": currency,
        "technical": t, "monte_carlo": mc, "score": sc,
        "signal": sig, "confidence": cf, "summary": sum_text,
    }


# ═══════════════ 格式化输出 ═══════════════

def pp(r):
    if "error" in r: print(f"\n  ❌ {r['error']}"); return
    p = r["price"]; t = r["technical"]; mc = r["monte_carlo"]; s = r["score"]
    market_label = {"cn": "A股", "hk": "港股", "us": "美股",
                    "jp": "日股", "kr": "韩股", "uk": "英股", "de": "德股",
                    "fr": "法股", "au": "澳股", "in": "印度股", "tw": "台股",
                    "ca": "加股", "gold": "黄金", "silver": "白银",
                    "crude": "原油", "fut": "期货", "idx": "指数",
                    }.get(r.get("market", "cn"), "")
    ccy = CCY_SYMBOLS.get(r.get("currency", "CNY"), "¥")

    print(f"\n{'='*60}")
    print(f"  \U0001f4c8 {r['name']}({r['code']}) [{market_label}] 涨跌预测 v7.4")
    print(f"{'='*60}")
    print(f"  现价:{ccy}{p['price']:.2f}  涨跌:{p['chg_pct']:+.2f}%  PE:{p.get('pe',0):.1f}  换手:{p.get('turnover',0):.1f}%")
    print(f"  今开:{ccy}{p['open']:.2f}  最高:{ccy}{p['high']:.2f}  最低:{ccy}{p['low']:.2f}")

    print(f"\n  ── 技术指标 ──")
    print(f"  MA5:{t['ma5']} MA10:{t['ma10']} MA20:{t['ma20']} MA60:{t['ma60']}")
    print(f"  RSI:{t['rsi']} MACD:DIF={t['macd']['dif']} DEA={t['macd']['dea']} HIST={t['macd']['hist']}")
    print(f"  KDJ:K={t['kdj']['k']} D={t['kdj']['d']} J={t['kdj']['j']}  量比:{t['vol_ratio']}")
    print(f"  布林: 上{t['boll']['up']} 中{t['boll']['mid']} 下{t['boll']['lo']} 位置:{t['boll']['pos']}%")
    # v6.0 新增指标
    adx_d = t.get("adx", {})
    print(f"  \U0001f7e2 ADX:{adx_d.get('adx',0)} PDI:{adx_d.get('pdi',0)} NDI:{adx_d.get('ndi',0)}  WR:{t.get('wr',0)} CCI:{t.get('cci',0)}")
    print(f"  MFI:{t.get('mfi',0)} ATR%:{t.get('atr_pct',0)}% OBV:{t.get('obv',0)}")

    print(f"\n  ── 蒙特卡洛概率预测 ──")
    h1, h2, h3, h4, h5 = "周期", "平均涨跌", "上涨概率", "中位数价", "置信区间"
    print(f"  {h1:<6} {h2:>10} {h3:>10} {h4:>10} {h5:>16}")
    for pd in ("5d", "10d"):
        m = mc[pd]; ci = f"{ccy}{m['lo']}~{ccy}{m['hi']}"
        print(f"  {pd:<6} {m['avg']:>+9.2f}% {m['up']:>9.0%}  {ccy}{m['p50']:>9.2f}  {ci:>16}")

    print(f"\n  ── 综合评分 v7.4 ──")
    print(f"  总分:{s['total']:.1f}/100  趋势:{s['trend']:.1f}  动量:{s['momentum']:.1f}  量价:{s['vol']:.1f}")
    print(f"  波动:{s.get('volatility',0):.1f}  概率:{s.get('prob',0):.1f}  环境:{s.get('env',0):.1f}  黄金:{s.get('gold_factor',0):.1f}  均线:{s['ma']}")

    print(f"\n  {'-'*50}")
    print(f"  \U0001f3af 信号:{r['signal']} (置信度:{r['confidence']:.0%})")
    print(f"  {r['summary']}")
    print(f"{'='*60}")


# ═══════════════ CLI ═══════════════

def _print_usage():
    """精简帮助信息"""
    print("\u80a1\u7968\u6da8\u8dcc\u9884\u6d4b\u5f15\u64ce v7.4 \u2014 \u652f\u6301 A\u80a1/\u6e2f\u80a1/\u7f8e\u80a1/\u5168\u7403\u6307\u6570\u4e0e\u5546\u54c1\u671f\u8d27")
    print()
    print("\u7528\u6cd5: python stock_predict.py <\u4ee3\u7801> [\u9009\u9879]")
    print()
    print("\u4ee3\u7801\u683c\u5f0f:")
    print("  A\u80a1:     600519 cn:600519")
    print("  \u6e2f\u80a1:     hk:00700 00700.HK")
    print("  \u7f8e\u80a1:     us:AAPL AAPL.US")
    print("  \u5168\u7403\u6307\u6570: idx:N225 idx:SPX idx:FTSE idx:DAX \u7b49")
    print("  \u5546\u54c1\u671f\u8d27: gold:comex silver:comex crude:wti")
    print("  \u6279\u91cf:     600519,hk:00700,us:AAPL")
    print()
    print("\u9009\u9879:")
    print("  --json     JSON \u683c\u5f0f\u8f93\u51fa\uff08\u4f9b\u7a0b\u5e8f\u8c03\u7528\uff09")
    print("  --simple   \u7b80\u6d01\u5355\u884c\u8f93\u51fa")
    print("  --test     \u79bb\u7ebf\u81ea\u68c0\uff1a\u6a21\u5757\u5bfc\u5165+\u4ee3\u7801\u89e3\u6790\uff0c\u4e0d\u8bbf\u95ee\u7f51\u7edc")
    print("  --quick    \u5feb\u901f\u6a21\u5f0f\uff1a\u4ec5\u884c\u60c5+\u6280\u672f\u6307\u6807\uff0c\u8df3\u8fc7\u8499\u7279\u5361\u6d1b")
    print("  --sector-ranking [cn/hk/us]   板块RPS相对强度排名 (v9.0)")
    print("  --index-regime [code]         指数市场体制分类 (v9.0)")
    print("  --scenario [name]             宏观情景概率加权 (v9.0)")
    print("  --topdown [cn/hk/us]          自上而下市场全景 (v9.0)")
    print()
    print("\u793a\u4f8b:")
    print("  python stock_predict.py 600519")
    print("  python stock_predict.py hk:00700 --json")
    print("  python stock_predict.py us:AAPL --simple")
    print("  python stock_predict.py --test")


def _arg_value(flag: str, default: str) -> str:
    """取 flag 后的参数值（argv 简易解析）。"""
    try:
        i = sys.argv.index(flag)
        if i + 1 < len(sys.argv) and not sys.argv[i + 1].startswith("--"):
            return sys.argv[i + 1]
    except ValueError:
        pass
    return default


def _run_v90_command() -> bool:
    """v9.0 新命令：--sector-ranking / --index-regime / --scenario / --topdown。

    处理成功返回 True（main 提前返回）；未命中返回 False。
    """
    try:
        if "--sector-ranking" in sys.argv:
            market = _arg_value("--sector-ranking", "cn")
            from stock_researcher.sector_analysis.relative_strength import rps_ranking
            results = rps_ranking(market=market)
            from stock_researcher.sector_analysis.relative_strength import SectorRelativeStrength
            print(SectorRelativeStrength.format_ranking(results, market=market))
            return True
        if "--index-regime" in sys.argv:
            code = _arg_value("--index-regime", "sh000001")
            from stock_researcher.index_analysis.market_regime import MarketRegimeClassifier
            print(MarketRegimeClassifier.format(MarketRegimeClassifier().classify(code)))
            return True
        if "--scenario" in sys.argv:
            name = _arg_value("--scenario", "")
            from stock_researcher.quantitative.scenario_engine import MacroScenarioEngine
            eng = MacroScenarioEngine()
            if name and name not in eng.list_scenarios():
                print(f"未知情景 {name}，可选: {', '.join(eng.list_scenarios())}")
                return True
            probs = {name: 1.0} if name else None
            print(MacroScenarioEngine.format(eng.analyze(0.08, 0.20, probs)))
            return True
        if "--topdown" in sys.argv:
            market = _arg_value("--topdown", "cn")
            from stock_researcher.analysis.top_down import TopDownReport
            print(TopDownReport.format(TopDownReport().build(market=market)))
            return True
    except Exception as e:
        print(f"❌ v9.0 命令执行失败: {e}")
        return True
    return False


def main():
    # --test: 离线自检（不访问网络）
    if "--test" in sys.argv:
        print("\U0001f50d \u79bb\u7ebf\u81ea\u68c0 stock_predict.py v7.4\n")
        issues = []
        # 模块导入
        import importlib
        d = __import__("os").path.dirname(__import__("os").path.abspath(__file__))
        for m in ["stock_researcher.data.market_classifier", "stock_researcher.data.global_market"]:
            try:
                if d not in sys.path: sys.path.insert(0, d)
                importlib.import_module(m)
                print(f"  \u2714 {m}")
            except Exception as e:
                print(f"  \u2716 {m}: {e}")
                issues.append(f"\u6a21\u5757\u5bfc\u5165\u5931\u8d25: {m}")
        # 市场检测测试
        test_codes = [
            ("600519","cn"),("hk:00700","hk"),("us:AAPL","us"),
            ("idx:N225","idx"),("gold:comex","gold"),("crude:wti","crude"),
            ("00700.HK","hk"),("AAPL.US","us"),
        ]
        print()
        for tc, exp in test_codes:
            try:
                _, _, mkt = _detect(tc)
                ok = mkt == exp or (exp == "idx" and mkt in ("idx","jp")) or (exp in ("gold","crude") and mkt == exp)
                status = "\u2714" if ok else "\u26a0"
                print(f"  {status} {tc:20s} \u2192 {mkt:6s} (\u9884\u671f {exp})")
                if not ok: issues.append(f"\u5e02\u573a\u68c0\u6d4b: {tc} \u8fd4\u56de {mkt}, \u9884\u671f {exp}")
            except Exception as e:
                print(f"  \u2716 {tc:20s} \u2192 \u5f02\u5e38: {e}")
                issues.append(f"\u5e02\u573a\u68c0\u6d4b: {tc} \u5f02\u5e38: {e}")
        print(f"\n{'='*40}")
        if issues:
            print(f"  \u274c \u53d1\u73b0 {len(issues)} \u4e2a\u95ee\u9898:")
            for i in issues: print(f"    - {i}")
        else:
            print("  \u2705 \u81ea\u68c0\u901a\u8fc7\uff01\u6240\u6709\u6a21\u5757\u6b63\u5e38\uff0c\u4ee3\u7801\u89e3\u6790\u6b63\u786e\u3002")
            print("  \u4e0b\u4e00\u6b65: python stock_predict.py 600519 --simple")
        sys.exit(0 if not issues else 1)

    # v9.0 新命令：板块排名 / 指数体制 / 宏观情景 / 自上而下全景
    if _run_v90_command():
        return

    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help", "help"):
        _print_usage()
        sys.exit(0)

    quick_mode = "--quick" in sys.argv
    codes = [c.strip() for c in sys.argv[1].split(",") if c.strip() and not c.strip().startswith("--")]
    if not codes:
        _print_usage()
        sys.exit(1)

    jf = "--json" in sys.argv; sf = "--simple" in sys.argv
    # 批量模式下预缓存环境数据，避免重复网络请求
    if len(codes) > 1 and not quick_mode:
        _get_cached_risk_appetite()
        _get_cached_gold_factors()

    for code in codes:
        r = predict(code, silent=jf, quick_mode=quick_mode)
        if jf:
            print(json.dumps(r, ensure_ascii=False, indent=2))
        elif sf:
            if "error" in r:
                print(f"\u274c {r.get('code',code)}: {r['error']}")
                if r.get("hint"): print(f"   \U0001f4a1 {r['hint']}")
            else:
                m = r["monte_carlo"]["5d"] if "5d" in r.get("monte_carlo",{}) else {"up": 0.5}
                market_tag = r.get("market", "").upper()
                ccy = CCY_SYMBOLS.get(r.get("currency","CNY"),"\u00a5")
                print(f"[{market_tag}] {r['name']}({r['code']}) {ccy}{r['price']['price']:.2f} "
                      f"{r['signal']}({r['confidence']:.0%}) | 5\u65e5\u6da8{m['up']:.0%} | "
                      f"\u8bc4\u5206{r['score']['total']:.0f}/100")
        else:
            pp(r)



if __name__ == "__main__":
    main()
