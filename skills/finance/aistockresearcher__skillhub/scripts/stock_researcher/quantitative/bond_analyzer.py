# -*- coding: utf-8 -*-
"""债券量化分析（bond_analyzer.py，v8.0 新增）

纯标准库实现债券定价与利率风险度量：
- 债券定价：bond_price（半年付息默认）
- 久期：bond_duration（Macaulay 久期，年化）
- 凸性：bond_convexity（价格对收益率的二阶敏感度）
- 到期收益率：ytm_from_price（二分法求 YTM）
- 信用利差：credit_spread（债 YTM − 国债 YTM，bp）
- 收益率曲线：yield_curve_metrics（level/slope/curvature）

用法：
    from stock_researcher.quantitative.bond_analyzer import analyze_bond, bond_price
    r = analyze_bond(code="128046", coupon_rate=0.01, ytm=None,
                     maturity_years=6, price=110.0)
"""

import math
from typing import Dict, List, Optional


def bond_price(coupon_rate: float, ytm: float, maturity_years: float,
               face: float = 100.0, freq: int = 2) -> float:
    """债券定价（默认半年付息）。"""
    c = coupon_rate * face / freq
    n = int(maturity_years * freq)
    r = ytm / freq
    pv_coupons = sum(c / (1 + r) ** t for t in range(1, n + 1))
    pv_face = face / (1 + r) ** n
    return pv_coupons + pv_face


def bond_duration(coupon_rate: float, ytm: float, maturity_years: float,
                  face: float = 100.0, freq: int = 2) -> float:
    """Macaulay 久期（年）。"""
    c = coupon_rate * face / freq
    n = int(maturity_years * freq)
    r = ytm / freq
    num = sum(t * c / (1 + r) ** t for t in range(1, n + 1)) + n * face / (1 + r) ** n
    p = bond_price(coupon_rate, ytm, maturity_years, face, freq)
    return (num / p) / freq if p > 0 else 0.0


def bond_convexity(coupon_rate: float, ytm: float, maturity_years: float,
                   face: float = 100.0, freq: int = 2) -> float:
    """凸性（年化）。"""
    c = coupon_rate * face / freq
    n = int(maturity_years * freq)
    r = ytm / freq
    num = sum(t * (t + 1) * c / (1 + r) ** (t + 2) for t in range(1, n + 1))
    num += n * (n + 1) * face / (1 + r) ** (n + 2)
    p = bond_price(coupon_rate, ytm, maturity_years, face, freq)
    return (num / p) / (freq ** 2) if p > 0 else 0.0


def ytm_from_price(price: float, coupon_rate: float, maturity_years: float,
                   face: float = 100.0, freq: int = 2,
                   lo: float = -0.5, hi: float = 0.5, tol: float = 1e-8) -> float:
    """由价格反解到期收益率（二分法；债券价格对 YTM 单调递减）。"""
    if price <= 0:
        return 0.0
    for _ in range(200):
        mid = (lo + hi) / 2.0
        p = bond_price(coupon_rate, mid, maturity_years, face, freq)
        if p > price:
            lo = mid  # 价格偏高 → 收益率偏低
        else:
            hi = mid
        if hi - lo < tol:
            break
    return (lo + hi) / 2.0


def credit_spread(bond_ytm: float, treasury_ytm: float) -> float:
    """信用利差（bp）。"""
    return (bond_ytm - treasury_ytm) * 10000.0


def yield_curve_metrics(maturities: List[float], yields: List[float]) -> Dict[str, float]:
    """收益率曲线形态指标：level（长端）、slope（10Y−2Y）、curvature（2·5Y−2Y−10Y）。"""
    if not maturities or len(maturities) != len(yields):
        return {}
    ymap = dict(zip(maturities, yields))

    def _y(y):
        # 找最近到期年限的收益率
        if y in ymap:
            return ymap[y]
        near = min(ymap.keys(), key=lambda k: abs(k - y))
        return ymap[near]

    ten = _y(10.0)
    two = _y(2.0)
    five = _y(5.0)
    return {
        "level": round(ten, 4),          # 长端收益率
        "slope": round(ten - two, 4),    # 期限利差（陡峭度）
        "curvature": round(2 * five - two - ten, 4),  # 曲率
    }


def _ytm_sensitivity(coupon_rate: float, ytm: float, maturity_years: float,
                     face: float = 100.0, freq: int = 2) -> Dict[str, float]:
    """YTM ±1% 的价格变动幅度（久期/凸性验证）。"""
    p0 = bond_price(coupon_rate, ytm, maturity_years, face, freq)
    p_up = bond_price(coupon_rate, ytm + 0.01, maturity_years, face, freq)
    p_down = bond_price(coupon_rate, ytm - 0.01, maturity_years, face, freq)
    return {
        "price": round(p0, 4),
        "price_if_ytm_minus1pct": round(p_down, 4),
        "price_if_ytm_plus1pct": round(p_up, 4),
        "change_minus1pct_pct": round((p_down / p0 - 1) * 100, 4),
        "change_plus1pct_pct": round((p_up / p0 - 1) * 100, 4),
    }


def analyze_bond(code: str = "", coupon_rate: Optional[float] = None,
                 ytm: Optional[float] = None, maturity_years: Optional[float] = None,
                 price: Optional[float] = None, treasury_ytm: float = 0.0,
                 face: float = 100.0, freq: int = 2) -> Dict:
    """债券综合分析：定价 / 久期 / 凸性 / YTM / 信用利差 / YTM 敏感性。

    Args:
        code: 债券代码（用于标识；不联网）
        coupon_rate: 票面利率（年）
        ytm: 到期收益率；None 且有 price 时反解
        maturity_years: 剩余期限（年）
        price: 当前价格（用于反解 YTM / 敏感性）
        treasury_ytm: 同期限国债收益率（计算信用利差）

    Returns:
        分析结果 dict（含 data_quality 标记）。
    """
    if coupon_rate is None or maturity_years is None:
        return {"error": "需要 coupon_rate 和 maturity_years", "code": code}
    if ytm is None:
        if price is None:
            return {"error": "需要 ytm 或 price（反解）", "code": code}
        ytm = ytm_from_price(price, coupon_rate, maturity_years, face, freq)

    p = bond_price(coupon_rate, ytm, maturity_years, face, freq)
    dur = bond_duration(coupon_rate, ytm, maturity_years, face, freq)
    conv = bond_convexity(coupon_rate, ytm, maturity_years, face, freq)
    result = {
        "code": code,
        "coupon_rate": coupon_rate,
        "ytm": round(ytm, 6),
        "maturity_years": maturity_years,
        "price": round(p, 4),
        "duration": round(dur, 4),
        "convexity": round(conv, 4),
        "modified_duration": round(dur / (1 + ytm / freq), 4),
        "credit_spread_bp": round(credit_spread(ytm, treasury_ytm), 2) if treasury_ytm else None,
        "sensitivity": _ytm_sensitivity(coupon_rate, ytm, maturity_years, face, freq),
        "data_quality": "derived",  # 基于输入参数计算（非抓取）
    }
    return result


if __name__ == "__main__":
    import json
    r = analyze_bond(code="示例", coupon_rate=0.03, ytm=0.04, maturity_years=10)
    print(json.dumps(r, ensure_ascii=False, indent=2))
