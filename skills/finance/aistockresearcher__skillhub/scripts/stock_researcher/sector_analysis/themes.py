#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""概念/主题板块分析 (v9.0.0 新增)
==============================
现 v8.0 仅有申万一级行业（银行/电子/…）。但 A 股活跃资金常沿「主题概念」轮动
（AI算力、人形机器人、低空经济、固态电池…），这类板块跨越传统行业分类。

本模块提供主题概念板块的代表股映射，并复用 SectorAnalyzer/SectorRelativeStrength
等既有分析器，对主题板块做与行业板块一致的强度/宽度/离散度/资金分析。

用法:
    from stock_researcher.sector_analysis.themes import (
        THEME_SECTOR_MAP, list_themes, analyze_theme,
    )
    print(list_themes("cn"))
    r = analyze_theme("AI算力", market="cn")
"""

from __future__ import annotations

from typing import Dict, List, Optional

# ── A 股主题概念板块 → 代表股（跨行业，按市值/流动性/纯度精选） ──
# 说明：代表股为各主题内最具辨识度与流动性的标的，用于构造主题代理指数。
# 主题随市场演进会变化，后续可经 data/index_constituents 动态扩充。
THEME_SECTOR_MAP: Dict[str, Dict[str, List[str]]] = {
    "cn": {
        "AI算力": ["002230", "000977", "300033", "300474", "600839", "688041"],
        "人形机器人": ["300124", "002747", "688169", "002527", "300759", "300024"],
        "低空经济": ["002097", "688322", "300449", "002013", "600118", "300853"],
        "固态电池": ["300750", "300073", "002460", "600884", "300331", "688006"],
        "氢能": ["002249", "300471", "600875", "000723", "002648", "300435"],
        "创新药": ["603259", "300122", "300601", "688180", "300896", "300683"],
        "数据要素": ["300033", "002230", "300212", "603881", "300245", "688561"],
        "卫星互联网": ["002025", "600118", "688566", "300698", "300853", "002465"],
        "半导体设备": ["688012", "300604", "688200", "688036", "300236", "002371"],
        "跨境电商": ["300464", "300597", "601113", "300866", "001317", "300839"],
        "脑机接口": ["300780", "300624", "603696", "688223", "300024", "002223"],
        "稀土永磁": ["600111", "600392", "000795", "002600", "300127", "600259"],
        "光伏": ["601012", "300274", "002459", "688599", "002129", "601877"],
        "军工信息化": ["600760", "000768", "002414", "688566", "300034", "300526"],
        "券商": ["601318", "600030", "601688", "000166", "600837", "601066"],
    },
    "hk": {
        "AI与互联网": ["00700", "09988", "03690", "09888", "02015", "09618"],
        "新能源车": ["01211", "09866", "09863", "00175", "02015", "02238"],
        "创新医药": ["02269", "01801", "06185", "01177", "01093", "02162"],
        "半导体": ["01347", "02013", "09885", "01368", "02500", "02878"],
        "新消费": ["02020", "09633", "02331", "06862", "01876", "09999"],
    },
    "us": {
        "AI算力龙头": ["NVDA", "AMD", "AVGO", "MRVL", "ARM", "SMCI"],
        "云与互联网": ["MSFT", "GOOGL", "META", "AMZN", "NFLX", "CRM"],
        "电动车与自动驾驶": ["TSLA", "RIVN", "LCID", "F", "GM", "MBLY"],
        "生物科技": ["MRNA", "VRTX", "REGN", "GILD", "BNTX", "ILMN"],
        "半导体设备": ["ASML", "AMAT", "LRCX", "KLAC", "NXPI", "QCOM"],
        "网络安全": ["CRWD", "PANW", "ZS", "FTNT", "S", "OKTA"],
    },
}


def list_themes(market: str = "cn") -> List[str]:
    """列出指定市场的全部主题概念板块名。"""
    return list(THEME_SECTOR_MAP.get(market, {}).keys())


def get_theme_stocks(theme: str, market: str = "cn") -> List[str]:
    """取主题板块代表股。"""
    return list(THEME_SECTOR_MAP.get(market, {}).get(theme, []))


def analyze_theme(
    theme: str, market: str = "cn", depth: str = "full",
) -> Dict:
    """对主题板块做综合分析（复用既有分析器）。

    Args:
        theme: 主题名（见 list_themes）
        market: cn/hk/us
        depth: "full"=相对强度+宽度+离散度+资金；"quick"=仅强度+资金

    Returns:
        dict: {theme, market, stocks, strength, breadth?, dispersion?, money_flow?, realtime}
    """
    stocks = get_theme_stocks(theme, market)
    out: Dict = {
        "theme": theme, "market": market, "stocks": stocks,
        "data_mode": "proxy", "note": "",
    }
    if not stocks:
        out["note"] = "未知主题，请用 list_themes 查看"
        return out

    # 实时行情 + 资金（cn）
    try:
        from stock_researcher.data.market import MarketData
        rt = MarketData().fetch_realtime(stocks)
        if rt:
            chgs = [d.get("change_pct", 0) for d in rt.values() if d.get("price", 0) > 0]
            flows = [d.get("main_net_flow", 0) for d in rt.values()]
            out["realtime"] = {
                "avg_change_pct": round(sum(chgs) / len(chgs), 2) if chgs else 0,
                "total_net_flow": round(sum(flows), 2),
                "up": sum(1 for c in chgs if c > 0),
                "down": sum(1 for c in chgs if c < 0),
            }
    except Exception:
        pass

    # 相对强度
    try:
        from stock_researcher.sector_analysis.relative_strength import SectorRelativeStrength
        out["strength"] = SectorRelativeStrength().relative_strength(theme, market=market)
    except Exception as e:
        out["strength"] = None
        out["note"] = f"强度分析失败: {e}"

    if depth == "quick":
        return out

    # 宽度
    try:
        from stock_researcher.sector_analysis.breadth import SectorBreadth
        out["breadth"] = SectorBreadth().analyze(theme, market=market)
    except Exception:
        out["breadth"] = None

    # 离散度
    try:
        from stock_researcher.sector_analysis.dispersion import SectorDispersion
        out["dispersion"] = SectorDispersion().analyze(theme, market=market)
    except Exception:
        out["dispersion"] = None

    return out


def rank_themes(market: str = "cn", top_n: Optional[int] = None) -> List[Dict]:
    """主题板块按 RPS 排名。"""
    try:
        from stock_researcher.sector_analysis.relative_strength import SectorRelativeStrength
        srs = SectorRelativeStrength()

        # 临时把主题映射注入代表篮子（通过 provider）
        def _provider(sector, mkt):
            return THEME_SECTOR_MAP.get(mkt, {}).get(sector, [])

        srs._provider = _provider
        results = []
        for name in list_themes(market):
            try:
                r = srs.relative_strength(name, market=market)
                results.append(r)
            except Exception:
                continue
        results.sort(key=lambda x: x.rps_score, reverse=True)
        for i, r in enumerate(results, 1):
            r.rps_rank = i
        return results[:top_n] if top_n else results
    except Exception:
        return []
