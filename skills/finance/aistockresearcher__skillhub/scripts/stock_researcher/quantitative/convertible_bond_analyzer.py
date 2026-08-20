# -*- coding: utf-8 -*-
"""可转债量化分析（convertible_bond_analyzer.py，v8.0 新增）

核心指标：
  - 转股价值 = (100/转股价) × 正股价
  - 转股溢价率 = (转债价/转股价值 − 1) × 100%（越低越接近股性）
  - 纯债价值 = 折现票息 + 面值（用同期限国债收益率 + 信用利差折现）
  - 双低指数 = 转债价 + 转股溢价率（越小越低估，双低策略）
  - 股性/债性判断：溢价率低→股性强
  - 强赎触发价 = 130% × 转股价（常见条款）

用法：
    from stock_researcher.quantitative.convertible_bond_analyzer import ConvertibleBondAnalyzer
    r = ConvertibleBondAnalyzer().analyze(cb_price=120.0, conversion_price=12.5,
                                          stock_price=15.0, maturity_years=5.0)
"""

from typing import Dict, List, Optional


class ConvertibleBondAnalyzer:
    """可转债量化分析（纯标准库）。"""

    def analyze(self, cb_price: float, conversion_price: float,
                stock_price: float, maturity_years: float,
                avg_coupon: float = 0.005, discount_rate: float = 0.02,
                face: float = 100.0, forced_call_ratio: float = 1.30) -> Dict:
        """可转债综合分析。

        Args:
            cb_price: 转债当前价
            conversion_price: 转股价
            stock_price: 正股价
            maturity_years: 剩余期限（年）
            avg_coupon: 平均票面利率（年）
            discount_rate: 纯债折现率（近似同期限国债+信用利差）
            forced_call_ratio: 强赎触发比例（默认 130%）

        Returns:
            指标 dict + 双低评分。
        """
        conv_value = face / conversion_price * stock_price if conversion_price > 0 else 0.0
        conv_premium = (cb_price / conv_value - 1) * 100.0 if conv_value > 0 else 0.0
        # 纯债价值：折现票息 + 面值（半年付息近似）
        from stock_researcher.quantitative.bond_analyzer import bond_price
        pure_bond_val = bond_price(avg_coupon, discount_rate, maturity_years, face, freq=2)
        ytm_cb = None
        try:
            from stock_researcher.quantitative.bond_analyzer import ytm_from_price
            ytm_cb = ytm_from_price(cb_price, avg_coupon, maturity_years, face, freq=2)
        except Exception:
            pass
        dual_low = cb_price + conv_premium
        equity_content = conv_value / cb_price if cb_price > 0 else 0.0
        forced_call_price = forced_call_ratio * conversion_price

        # 双低评分：双低指数越小越低估（0-100 反向映射）
        dual_low_score = max(0.0, min(100.0, 100.0 - dual_low))
        if conv_premium < 10:
            character = "偏股型"      # 溢价率低 → 跟随正股
        elif conv_premium > 60:
            character = "偏债型"      # 溢价率高 → 债性保护
        else:
            character = "平衡型"
        signals = []
        if conv_premium < 0:
            signals.append("负溢价（转股套利机会）")
        elif conv_premium < 10:
            signals.append("低溢价，股性强")
        if stock_price >= forced_call_price:
            signals.append("正股价接近/超过强赎触发价，注意强赎风险")
        if pure_bond_val > 0 and cb_price < pure_bond_val:
            signals.append("转债价低于纯债价值，债底保护强")

        return {
            "cb_price": round(cb_price, 4),
            "conversion_value": round(conv_value, 4),
            "conversion_premium_pct": round(conv_premium, 4),
            "pure_bond_value": round(pure_bond_val, 4),
            "ytm_if_held": round(ytm_cb, 6) if ytm_cb is not None else None,
            "dual_low_index": round(dual_low, 4),
            "equity_content": round(equity_content, 4),
            "forced_call_price": round(forced_call_price, 4),
            "character": character,
            "dual_low_score": round(dual_low_score, 2),
            "signals": signals,
            "data_quality": "derived",
        }

    def quick_convertible_score(self, code: str) -> Dict:
        """一键可转债评分（数据获取失败返回 data_quality=unavailable）。"""
        try:
            from stock_researcher.data.akshare_provider import ak_convertible_quote
            q = ak_convertible_quote(code)
            if not q or q.get("conversion_price") is None or q.get("stock_price") is None:
                return {"error": "可转债行情不可用（akshare 未装或接口失败）",
                        "code": code, "data_quality": "unavailable"}
            return self.analyze(
                cb_price=q.get("cb_price", 100.0),
                conversion_price=q["conversion_price"],
                stock_price=q["stock_price"],
                maturity_years=q.get("maturity_years", 5.0),
            )
        except Exception as e:
            return {"error": str(e), "code": code, "data_quality": "unavailable"}


if __name__ == "__main__":
    import json
    r = ConvertibleBondAnalyzer().analyze(
        cb_price=120.0, conversion_price=12.5, stock_price=15.0, maturity_years=5.0)
    print(json.dumps(r, ensure_ascii=False, indent=2))
