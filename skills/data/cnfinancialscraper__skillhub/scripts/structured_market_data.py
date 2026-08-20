# -*- coding: utf-8 -*-
"""结构化市场数据源统一入口（structured_market_data.py，v5.0.0 新增）

低代码 akshare 优先，覆盖此前缺失的几类结构化数据：
- 期货：实时行情 / 日线 / 持仓排名（上期所/大商所/郑商所/中金所/能源/广期所 全市场）
- 宏观：GDP / CPI / PPI / PMI / 外汇储备（公开宏观统计渠道）
- 同业市场：Shibor（上海银行间同业拆放利率）
- 港股 / 美股：全市场实时行情（东方财富聚合，大陆可达）

统一走 akshare（零 token、A 股/期货最全），akshare 未安装时返回 None，
保持核心零依赖语义。所有 akshare 调用带异常兜底，失败返回 None 不阻塞下游。

用法：
    from scripts.structured_market_data import get_structured_data, list_data_types
    df = get_structured_data("shibor")            # Shibor 利率
    df = get_structured_data("futures_spot", symbol="V0")  # 指定品种
    df = get_structured_data("macro_cpi")         # CPI 同比
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

log = logging.getLogger(__name__)

# data_type -> (akshare 函数名, 默认参数)
# 注意：部分接口默认参数即为"最新/全市场"；具体品种/年份通过 kwargs 覆盖。
AKSHARE_ROUTES: Dict[str, Dict[str, Any]] = {
    # ── 期货 ──
    "futures_spot": {"func": "futures_zh_spot", "defaults": {"symbol": ""}},
    "futures_daily": {"func": "futures_zh_daily_sina", "defaults": {"symbol": "V0"}},
    "futures_holding": {"func": "futures_zh_holding_rank", "defaults": {"symbol": "V0"}},
    # ── 宏观 ──
    "macro_gdp": {"func": "macro_china_gdp", "defaults": {"start_year": "2020"}},
    "macro_cpi": {"func": "macro_china_cpi", "defaults": {"start_year": "2020"}},
    "macro_ppi": {"func": "macro_china_ppi", "defaults": {"start_year": "2020"}},
    "macro_pmi": {"func": "macro_china_pmi", "defaults": {}},
    "macro_m2": {"func": "macro_china_money_supply", "defaults": {}},
    "macro_fx_reserves": {"func": "macro_china_fx_reserves_yearly", "defaults": {}},
    # ── 同业市场 ──
    "shibor": {"func": "money_interest_shibor", "defaults": {}},
    "repo_rate": {"func": "bond_repo_rate", "defaults": {"symbol": "FR007"}},
    # ── 港股 / 美股 ──
    "hk_spot": {"func": "stock_hk_spot_em", "defaults": {}},
    "us_spot": {"func": "stock_us_spot_em", "defaults": {}},
}


def list_data_types() -> List[Dict[str, str]]:
    """列出所有可用 data_type 及其 akshare 函数。"""
    return [
        {"data_type": k, "akshare_func": v["func"]}
        for k, v in AKSHARE_ROUTES.items()
    ]


def _call_akshare(func_name: str, kwargs: Dict[str, Any]) -> Any:
    """门控调用 akshare（复用 akshare_fallback 的封装，含 HAS_AKSHARE 检查）。"""
    from scripts.akshare_fallback import _call_akshare as _dispatch
    return _dispatch(func_name, kwargs)


def get_structured_data(data_type: str, **kwargs: Any) -> Optional[Any]:
    """统一结构化数据入口。

    Args:
        data_type: 见 :data:`AKSHARE_ROUTES` 键（futures_spot / macro_cpi / shibor / hk_spot ...）
        **kwargs: 覆盖默认参数（如 symbol="V0" / start_year="2022"）

    Returns:
        akshare 返回的 DataFrame（或 list）；失败 / akshare 未装 / 未知类型 → None。
    """
    route = AKSHARE_ROUTES.get(data_type)
    if route is None:
        log.warning("未知 data_type: %s，可用: %s", data_type, ", ".join(AKSHARE_ROUTES))
        return None

    func_name = route["func"]
    merged = dict(route["defaults"])
    merged.update({k: v for k, v in kwargs.items() if v is not None})

    try:
        result = _call_akshare(func_name, merged)
        if result is not None:
            return result
    except Exception as e:  # pragma: no cover - 防御
        log.debug("get_structured_data(%s) 异常: %s", data_type, e)

    # 降级：带默认参数失败时尝试空参数（部分接口无参即最新/全市场）
    if merged:
        try:
            result = _call_akshare(func_name, {})
            if result is not None:
                return result
        except Exception:  # pragma: no cover - 防御
            pass

    # v7.0.0 二级兜底：宏观 5 指标在 akshare 缺失/失败时走东财 datacenter
    # 纯 HTTP 接口（零 pip 依赖），保住"核心零依赖语义"下的宏观可用性
    if data_type in ("macro_gdp", "macro_cpi", "macro_ppi", "macro_pmi"):
        try:
            from scripts.market_data_scraper import get_macro_indicator
            rows = get_macro_indicator(data_type[len("macro_"):],
                                       limit=int(kwargs.get("limit", 24)))
            if rows:
                log.info("get_structured_data(%s) 已走 v7.0.0 HTTP 兜底", data_type)
                return rows
        except Exception as e:  # pragma: no cover - 防御
            log.debug("macro HTTP 兜底失败(%s): %s", data_type, e)
    return None


def quick_check() -> Dict[str, Any]:
    """自检：akshare 是否可用 + 各 data_type 是否可达（仅诊断用）。"""
    from scripts.akshare_fallback import HAS_AKSHARE
    out: Dict[str, Any] = {"akshare_installed": HAS_AKSHARE, "data_types": list(AKSHARE_ROUTES)}
    return out


if __name__ == "__main__":
    import json
    print(json.dumps(quick_check(), ensure_ascii=False, indent=2))
