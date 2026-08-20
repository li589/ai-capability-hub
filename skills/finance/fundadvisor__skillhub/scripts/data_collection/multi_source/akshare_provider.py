#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""akshare 数据源 (v6.0 新增)

扩展 akshare 用法，替换 macro_analyzer 假数据 + 提供净值/持仓/指数。
akshare 为可选依赖：未安装时本源 unavailable，不阻断其他源。

覆盖能力：macro / fund_nav / fund_holdings / index / fund_ratings(间接)
"""
from __future__ import annotations

import sys
import math
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

_SCRIPTS = Path(__file__).resolve().parents[2]
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from .base import DataSource, SourceResponse  # noqa: E402

# akshare 可选
try:
    import akshare as ak
    HAS_AKSHARE = True
except Exception:
    HAS_AKSHARE = False


def _safe_float(v, default=None):
    try:
        if v in (None, "", "-", "N/A", "null"):
            return default
        f = float(v)
        return f if math.isfinite(f) else default
    except (TypeError, ValueError):
        return default


class AkshareProvider(DataSource):
    """akshare 数据源"""

    name = "akshare"
    capabilities = ["macro", "fund_nav", "fund_holdings", "index", "fund_ratings"]

    def __init__(self):
        if not HAS_AKSHARE:
            self._available = False
        else:
            self._available = True

    # ─── 宏观数据（真实，替换 macro_analyzer 假数据）─────────
    def fetch_macro(self) -> SourceResponse:
        if not self._available:
            return SourceResponse.fail(self.name, "akshare 未安装: pip install akshare")
        indicators = {}
        errors = []
        # GDP（列：国内生产总值-同比增长）
        try:
            df = ak.macro_china_gdp()
            if df is not None and len(df) > 0:
                v = _safe_float(df.iloc[0].get("国内生产总值-同比增长"))
                if v is not None:
                    indicators["gdp_yoy"] = v
        except Exception as e:
            errors.append(f"gdp:{e}")
        # CPI（列：全国-同比增长）
        try:
            df = ak.macro_china_cpi()
            if df is not None and len(df) > 0:
                v = _safe_float(df.iloc[0].get("全国-同比增长"))
                if v is not None:
                    indicators["cpi_yoy"] = v
        except Exception as e:
            errors.append(f"cpi:{e}")
        # PPI（列：当月同比增长）
        try:
            df = ak.macro_china_ppi()
            if df is not None and len(df) > 0:
                v = _safe_float(df.iloc[0].get("当月同比增长"))
                if v is not None:
                    indicators["ppi_yoy"] = v
        except Exception as e:
            errors.append(f"ppi:{e}")
        # PMI（列：制造业-指数）
        try:
            df = ak.macro_china_pmi()
            if df is not None and len(df) > 0:
                v = _safe_float(df.iloc[0].get("制造业-指数"))
                if v is not None:
                    indicators["pmi"] = v
        except Exception as e:
            errors.append(f"pmi:{e}")
        # 货币供应（列：货币和准货币(M2)-同比增长 / 货币(M1)-同比增长）
        try:
            df = ak.macro_china_money_supply()
            if df is not None and len(df) > 0:
                row = df.iloc[0]
                v2 = _safe_float(row.get("货币和准货币(M2)-同比增长"))
                v1 = _safe_float(row.get("货币(M1)-同比增长"))
                if v2 is not None:
                    indicators["m2_yoy"] = v2
                if v1 is not None:
                    indicators["m1_yoy"] = v1
        except Exception as e:
            errors.append(f"m2:{e}")
        # LPR（列：LPR1Y / LPR5Y，首行可能 NaN，取最近非 NaN 行）
        try:
            df = ak.macro_china_lpr()
            if df is not None and len(df) > 0:
                for col, key in [("LPR1Y", "lpr_1y"), ("LPR5Y", "lpr_5y")]:
                    if col in df.columns:
                        # 从末尾找首个非 NaN
                        non_nan = df[col].dropna()
                        if len(non_nan) > 0:
                            indicators[key] = _safe_float(non_nan.iloc[-1])
        except Exception as e:
            errors.append(f"lpr:{e}")
        # 社融
        try:
            df = ak.macro_china_shrzgm()
            if df is not None and len(df) > 0:
                latest = df.iloc[0].to_dict()
                for k, v in latest.items():
                    if "社融" in str(k) or "增量" in str(k):
                        indicators["social_financing"] = _safe_float(v)
                        break
        except Exception as e:
            errors.append(f"shrzgm:{e}")

        if not indicators:
            return SourceResponse.fail(self.name, "所有宏观指标获取失败: " + "; ".join(errors[:3]))
        indicators["_errors"] = errors[:3]
        indicators["_fetched_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return SourceResponse.ok(self.name, indicators)

    # ─── 基金净值 ─────────────────────────────────────────
    def fetch_fund_nav(self, code: str) -> SourceResponse:
        if not self._available:
            return SourceResponse.fail(self.name, "akshare 未安装")
        try:
            # 单位净值走势（最近若干日）
            df = ak.fund_open_fund_info_em(symbol=code, indicator="单位净值走势")
            if df is None or len(df) == 0:
                return SourceResponse.fail(self.name, f"{code} 无净值数据")
            latest = df.iloc[-1].to_dict()
            # 列名可能是 净值日期/单位净值/日增长率
            nav = None
            nav_date = None
            change = None
            for k, v in latest.items():
                if "净值" in str(k) and "日期" not in str(k) and nav is None:
                    nav = _safe_float(v)
                elif "日期" in str(k):
                    nav_date = str(v)[:10]
                elif "增长" in str(k) or "涨跌" in str(k):
                    change = _safe_float(v)
            if nav is None:
                return SourceResponse.fail(self.name, f"{code} 净值解析失败")
            return SourceResponse.ok(self.name, {
                "nav": nav, "nav_date": nav_date, "change_pct": change,
                "history_count": len(df),
            })
        except Exception as e:
            return SourceResponse.fail(self.name, f"{code} 净值获取失败: {e}")

    # ─── 基金持仓（行业配置）──────────────────────────────
    def fetch_fund_holdings(self, code: str) -> SourceResponse:
        if not self._available:
            return SourceResponse.fail(self.name, "akshare 未安装")
        try:
            df = ak.fund_portfolio_industry_allocation_em(symbol=code)
            if df is None or len(df) == 0:
                return SourceResponse.fail(self.name, f"{code} 无行业配置数据")
            holdings = []
            for _, row in df.head(20).iterrows():
                d = row.to_dict()
                holdings.append({
                    "period": str(d.get("年度", d.get("季度", "")))[:10],
                    "industry": d.get("行业类别", ""),
                    "ratio": _safe_float(d.get("占净值比例", d.get("比例"))),
                })
            return SourceResponse.ok(self.name, holdings)
        except Exception as e:
            return SourceResponse.fail(self.name, f"{code} 持仓获取失败: {e}")

    # ─── 指数历史 ─────────────────────────────────────────
    def fetch_index(self, index_code: str) -> SourceResponse:
        if not self._available:
            return SourceResponse.fail(self.name, "akshare 未安装")
        try:
            end = datetime.now().strftime("%Y%m%d")
            start = (datetime.now() - timedelta(days=365)).strftime("%Y%m%d")
            df = ak.index_zh_a_hist(symbol=index_code, period="daily",
                                     start_date=start, end_date=end)
            if df is None or len(df) == 0:
                return SourceResponse.fail(self.name, f"{index_code} 无指数数据")
            latest = df.iloc[-1].to_dict()
            closes = [_safe_float(x) for x in df["收盘"].tolist()] if "收盘" in df.columns else []
            return SourceResponse.ok(self.name, {
                "latest_close": _safe_float(latest.get("收盘")),
                "latest_date": str(latest.get("日期", ""))[:10],
                "history_count": len(df),
                "closes": closes[-60:] if closes else [],
            })
        except Exception as e:
            return SourceResponse.fail(self.name, f"{index_code} 指数获取失败: {e}")

    # ─── 基金评级（akshare 间接：东财评级+雪球）──────────
    def fetch_fund_ratings(self, code: str) -> SourceResponse:
        if not self._available:
            return SourceResponse.fail(self.name, "akshare 未安装")
        # 1. 优先: fund_rating_all 聚合星级（上海证券/招商证券/济安金信/晨星）
        try:
            df = ak.fund_rating_all()
            if df is not None and len(df) > 0:
                # 列名含基金代码
                code_col = None
                for c in df.columns:
                    if "代码" in str(c) or "code" in str(c).lower():
                        code_col = c
                        break
                if code_col:
                    row = df[df[code_col].astype(str).str.contains(code, na=False)]
                    if len(row) > 0:
                        d = row.iloc[0].to_dict()
                        stars = []
                        for k, v in d.items():
                            if "星" in str(k) or "评级" in str(k):
                                sv = _safe_float(v)
                                if sv and 0 < sv <= 5:
                                    stars.append(sv)
                        if stars:
                            return SourceResponse.ok(self.name, {
                                "source_detail": "东财聚合(上海证券/招商/济安/晨星)",
                                "star": round(sum(stars) / len(stars), 2),
                                "stars_detail": stars,
                            })
        except Exception:
            pass
        # 2. 回退: 雪球基金分析
        try:
            df = ak.fund_individual_analysis_xq(symbol=code)
            if df is None or len(df) == 0:
                return SourceResponse.fail(self.name, f"{code} 无评级数据")
            latest = df.iloc[-1].to_dict()
            return SourceResponse.ok(self.name, {
                "source_detail": "雪球",
                "sharpe": _safe_float(latest.get("夏普比率")),
                "max_drawdown": _safe_float(latest.get("最大回撤")),
                "annual_volatility": _safe_float(latest.get("年化波动率")),
                "period": str(latest.get("周期", latest.get("时间", "")))[:20],
            })
        except Exception as e:
            return SourceResponse.fail(self.name, f"{code} 评级获取失败: {e}")


def main():
    print("=== akshare 数据源测试 ===")
    p = AkshareProvider()
    if not HAS_AKSHARE:
        print("akshare 未安装，跳过（优雅降级）")
        return
    print("\n--- 宏观数据 ---")
    r = p.fetch_macro()
    print(f"available={r.available}, source={r.source}")
    if r.available:
        for k, v in r.data.items():
            if not k.startswith("_"):
                print(f"  {k}: {v}")
    print("\n--- 基金净值 110022 ---")
    r = p.fetch_fund_nav("110022")
    print(f"available={r.available}, data={r.data if r.available else r.error}")


if __name__ == "__main__":
    main()
