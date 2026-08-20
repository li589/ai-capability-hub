# -*- coding: utf-8 -*-
"""
dataSupplement V7.1 · 领域模块 · 研报层
=======================================

功能概览:
  - stock_reports: 个股研报列表
  - industry_reports: 行业研报列表
  - consensus_eps: 机构一致预期 EPS
  - semantic_search: 自然语言语义搜索

数据源:
  个股/行业研报: 东财 reportapi.eastmoney.com
  一致预期: 同花顺 basic.10jqka.com.cn
  语义搜索: iwencai openapi (需 API Key)

零外部依赖 — 仅使用 Python 标准库 + 项目内部模块。
"""

from __future__ import annotations

import json
import os
import sys
from typing import Optional

# 设置模块搜索路径
_SKILL_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _SKILL_ROOT not in sys.path:
    sys.path.insert(0, _SKILL_ROOT)

from core.client import http_get, http_post
from core.throttle import throttled_get
from core.ticker import normalize

__all__ = [
    "stock_reports",
    "industry_reports",
    "consensus_eps",
    "semantic_search",
]

# ---------------------------------------------------------------------------
# 内部工具
# ---------------------------------------------------------------------------


def _safe_float(val) -> Optional[float]:
    """安全浮点数转换。"""
    if val is None or val == "" or val == "-":
        return None
    try:
        return float(str(val).replace(",", "").replace("%", "").strip())
    except (ValueError, TypeError):
        return None


# ---------------------------------------------------------------------------
# 常量
# ---------------------------------------------------------------------------

_REPORT_API = "https://reportapi.eastmoney.com/report/list"
_REPORT_JGDY_API = "https://reportapi.eastmoney.com/report/jgdy/list"

_THS_CONSENSUS_API = "https://basic.10jqka.com.cn/basicapi/gdyj/yjbb/web"
_THS_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Referer": "http://basic.10jqka.com.cn/",
    "Accept": "application/json, text/plain, */*",
}

_IWENCAI_API = "https://www.iwencai.com/customized/chart/get-robot-data"
_IWENCAI_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Referer": "https://www.iwencai.com/",
    "Content-Type": "application/json",
    "Accept": "application/json",
}


# ===========================================================================
# 公开 API
# ===========================================================================


def stock_reports(code: str, count: int = 20) -> list[dict]:
    """个股研报列表

    获取券商/机构对指定股票发布的研究报告，包含评级、目标价、
    分析师等信息，用于了解机构观点和预期变化。

    Source: 东财 reportapi.eastmoney.com

    Args:
        code: 股票代码（6位数字），如 "600519"
        count: 获取条数，默认 20，最大 100

    Returns:
        研报列表，每项包含:
        - title: 研报标题
        - institution: 研究机构名称
        - analyst: 分析师姓名（多人以逗号分隔）
        - rating: 投资评级（如 "买入"、"增持"、"推荐"）
        - target_price: 目标价（元），可能为 None
        - date: 发布日期（YYYY-MM-DD）
        - url: 研报原文链接
        - summary: 核心观点摘要
        - prev_rating: 前次评级（如有变化）
        - eps_current: 当年预测 EPS
        - eps_next: 明年预测 EPS

    示例:
        >>> stock_reports("600519", count=5)
        [{title: "贵州茅台深度报告:...", institution: "中信证券", rating: "买入", ...}]
    """
    normalized = normalize(code)
    count = min(count, 100)

    params = {
        "industryCode": "*",
        "pageNo": "1",
        "pageSize": str(count),
        "code": normalized,
        "qType": "0",
        "beginTime": "",
        "endTime": "",
    }

    resp = throttled_get(_REPORT_API, params=params)
    if not resp or not resp.ok:
        return []

    try:
        data = resp.json()
    except (ValueError, AttributeError):
        return []

    items = data.get("data", [])
    if not isinstance(items, list):
        return []

    results = []
    for item in items:
        # 分析师列表
        researchers = item.get("researcher", [])
        analyst_str = ""
        if isinstance(researchers, list):
            analyst_str = ", ".join(researchers)
        elif isinstance(researchers, str):
            analyst_str = researchers

        # 预测 EPS
        predict_this = item.get("predictThisYearEps")
        predict_next = item.get("predictNextYearEps")

        # 构建研报URL
        info_code = item.get("infoCode", "")
        report_url = ""
        if info_code:
            report_url = f"https://data.eastmoney.com/report/zw_stock.jshtml?infocode={info_code}"

        results.append({
            "title": item.get("title", ""),
            "institution": item.get("orgSName", item.get("orgName", "")),
            "analyst": analyst_str,
            "rating": item.get("emRatingName", item.get("sRatingName", "")),
            "target_price": _safe_float(item.get("bpiTarget")),
            "date": item.get("publishDate", "")[:10],
            "url": report_url,
            "summary": item.get("abstract", item.get("content", ""))[:500],
            "prev_rating": item.get("lastEmRatingName", ""),
            "eps_current": _safe_float(predict_this),
            "eps_next": _safe_float(predict_next),
        })

    return results


def industry_reports(industry: str = None, count: int = 20) -> list[dict]:
    """行业研报列表

    获取行业研究报告列表，可按行业筛选或获取全部最新行业研报。
    便于了解各行业景气度变化和机构观点。

    Source: 东财 reportapi.eastmoney.com

    Args:
        industry: 行业名称，如 "电子"、"医药生物"、"计算机"。
                  None 表示获取全行业最新研报。
        count: 获取条数，默认 20，最大 100

    Returns:
        行业研报列表，每项包含:
        - title: 研报标题
        - institution: 研究机构名称
        - analyst: 分析师姓名
        - industry_name: 行业名称
        - rating: 行业评级（如 "看好"、"中性"）
        - date: 发布日期（YYYY-MM-DD）
        - url: 研报原文链接
        - summary: 核心观点摘要

    示例:
        >>> industry_reports("人工智能", count=5)
        [{title: "AI行业深度:...", institution: "国盛证券", industry_name: "计算机", ...}]
        >>> industry_reports(count=10)  # 全行业最新
    """
    count = min(count, 100)

    # 东财 reportapi 的行业研报(qType=1)要求带时间窗口参数，否则返回空。
    # 取近一年区间；industryName 过滤在服务端已不生效，改为客户端侧过滤。
    from datetime import date, timedelta
    _today = date.today()
    params = {
        "industryCode": "*",
        "pageNo": "1",
        "pageSize": str(count if not industry else min(count * 5, 100)),
        "qType": "1",  # 1=行业研报
        "beginTime": (_today - timedelta(days=365)).strftime("%Y-%m-%d"),
        "endTime": _today.strftime("%Y-%m-%d"),
    }

    resp = throttled_get(_REPORT_API, params=params)
    if not resp or not resp.ok:
        return []

    try:
        data = resp.json()
    except (ValueError, AttributeError):
        return []

    items = data.get("data", [])
    if not isinstance(items, list):
        return []

    results = []
    for item in items:
        # 分析师列表
        researchers = item.get("researcher", [])
        analyst_str = ""
        if isinstance(researchers, list):
            analyst_str = ", ".join(researchers)
        elif isinstance(researchers, str):
            analyst_str = researchers

        # 构建URL
        info_code = item.get("infoCode", "")
        report_url = ""
        if info_code:
            report_url = f"https://data.eastmoney.com/report/zw_industry.jshtml?infocode={info_code}"

        results.append({
            "title": item.get("title", ""),
            "institution": item.get("orgSName", item.get("orgName", "")),
            "analyst": analyst_str,
            "industry_name": item.get("industryName", item.get("plateCode", "")),
            "rating": item.get("emRatingName", item.get("sRatingName", "")),
            "date": item.get("publishDate", "")[:10],
            "url": report_url,
            "summary": item.get("abstract", item.get("content", ""))[:500],
        })

    # 客户端侧行业过滤（服务端 industryName 过滤已失效）
    if industry:
        kw = industry.strip()
        filtered = [
            r for r in results
            if kw in (r.get("industry_name") or "") or kw in (r.get("title") or "")
        ]
        # 命中则返回过滤结果，未命中则回退全行业列表（避免空返回）
        results = filtered if filtered else results

    return results[:count]


def consensus_eps(code: str) -> dict:
    """机构一致预期 EPS

    获取机构对指定股票的盈利一致预期数据，包括 EPS 均值、
    极值、覆盖机构数量以及目标价预期等。

    Source: 同花顺 basic.10jqka.com.cn

    Args:
        code: 股票代码（6位数字），如 "600519"

    Returns:
        一致预期数据字典:
        - year: 预测年度
        - eps_mean: 一致预期 EPS 均值
        - eps_max: EPS 最高预测值
        - eps_min: EPS 最低预测值
        - institution_count: 覆盖机构数量
        - pe_forecast: 预测 PE 估值
        - target_price_avg: 平均目标价
        - target_price_high: 最高目标价
        - target_price_low: 最低目标价
        - rating: 综合投资评级
        - net_profit_mean: 一致预期归母净利润(亿元)
        - revenue_mean: 一致预期营收(亿元)

    示例:
        >>> consensus_eps("600519")
        {year: "2025", eps_mean: 68.5, institution_count: 32, rating: "买入", ...}
    """
    normalized = normalize(code)

    # ─── 主源: 同花顺一致预期 ───
    result = _consensus_ths(normalized)
    if result:
        return result

    # ─── Fallback: 东财研报汇总 ───
    return _consensus_eastmoney(normalized)


def _consensus_ths(code: str) -> dict:
    """同花顺一致预期接口。"""
    url = f"{_THS_CONSENSUS_API}/{code}"

    resp = throttled_get(url, headers=_THS_HEADERS)
    if not resp or not resp.ok:
        return {}

    try:
        data = resp.json()
    except (ValueError, AttributeError):
        return {}

    result = data.get("data", data)
    if not isinstance(result, dict):
        return {}

    # 解析预期数据结构
    forecasts = result.get("forecast", result.get("data", {}))
    if not isinstance(forecasts, dict):
        forecasts = {}

    eps_list = forecasts.get("eps", [])
    np_list = forecasts.get("np", forecasts.get("netProfit", []))
    revenue_list = forecasts.get("income", forecasts.get("revenue", []))
    pe_list = forecasts.get("pe", [])

    # 获取年份信息
    years = forecasts.get("year", forecasts.get("years", []))
    current_year = ""
    if isinstance(years, list) and years:
        current_year = str(years[0])
    elif isinstance(result.get("year"), str):
        current_year = result["year"]

    # 获取机构数目
    org_count = result.get("analyst_count", result.get("orgNum"))
    if org_count is None:
        org_count = forecasts.get("orgNum", forecasts.get("num"))

    parsed = {
        "year": current_year,
        "eps_mean": _safe_float(eps_list[0]) if len(eps_list) > 0 else None,
        "eps_max": _safe_float(result.get("eps_max") or (eps_list[1] if len(eps_list) > 1 else None)),
        "eps_min": _safe_float(result.get("eps_min") or (eps_list[2] if len(eps_list) > 2 else None)),
        "institution_count": org_count,
        "pe_forecast": _safe_float(pe_list[0]) if isinstance(pe_list, list) and pe_list else _safe_float(result.get("pe")),
        "target_price_avg": _safe_float(result.get("target_price_avg") or result.get("avgPrice")),
        "target_price_high": _safe_float(result.get("target_price_high") or result.get("maxPrice")),
        "target_price_low": _safe_float(result.get("target_price_low") or result.get("minPrice")),
        "rating": result.get("rating", result.get("composite_rating", "")),
        "net_profit_mean": _safe_float(np_list[0]) if isinstance(np_list, list) and np_list else None,
        "revenue_mean": _safe_float(revenue_list[0]) if isinstance(revenue_list, list) and revenue_list else None,
    }

    # 关键字段全为空 → 视为无效，让 caller 触发 fallback
    if parsed.get("eps_mean") is None and parsed.get("net_profit_mean") is None and not parsed.get("rating"):
        return {}

    return parsed


def _consensus_eastmoney(code: str) -> dict:
    """东财研报一致预期（Fallback）— 从研报接口聚合。"""
    params = {
        "industryCode": "*",
        "pageNo": "1",
        "pageSize": "50",
        "code": code,
        "qType": "0",
        "beginTime": "",
        "endTime": "",
    }

    resp = throttled_get(_REPORT_API, params=params)
    if not resp or not resp.ok:
        return {}

    try:
        data = resp.json()
    except (ValueError, AttributeError):
        return {}

    items = data.get("data", [])
    if not isinstance(items, list) or not items:
        return {}

    # 从研报中提取 EPS 预测
    eps_values = []
    target_prices = []
    ratings = []

    for item in items:
        eps = _safe_float(item.get("predictThisYearEps"))
        if eps is not None:
            eps_values.append(eps)

        tp = _safe_float(item.get("bpiTarget"))
        if tp is not None:
            target_prices.append(tp)

        rating = item.get("emRatingName", "")
        if rating:
            ratings.append(rating)

    # 汇总计算
    eps_mean = round(sum(eps_values) / len(eps_values), 4) if eps_values else None
    eps_max = max(eps_values) if eps_values else None
    eps_min = min(eps_values) if eps_values else None
    tp_avg = round(sum(target_prices) / len(target_prices), 2) if target_prices else None
    tp_high = max(target_prices) if target_prices else None
    tp_low = min(target_prices) if target_prices else None

    # 评级取众数
    consensus_rating = ""
    if ratings:
        from collections import Counter
        rating_counts = Counter(ratings)
        consensus_rating = rating_counts.most_common(1)[0][0]

    from datetime import date as _date
    current_year = str(_date.today().year)

    return {
        "year": current_year,
        "eps_mean": eps_mean,
        "eps_max": eps_max,
        "eps_min": eps_min,
        "institution_count": len(eps_values),
        "pe_forecast": None,
        "target_price_avg": tp_avg,
        "target_price_high": tp_high,
        "target_price_low": tp_low,
        "rating": consensus_rating,
        "net_profit_mean": None,
        "revenue_mean": None,
    }


def semantic_search(
    query: str,
    channel: str = "stock",
    size: int = 10,
) -> list[dict]:
    """自然语言语义搜索（需 API Key）

    通过 iwencai (同花顺智能问答) 接口执行自然语言查询，
    支持复杂条件组合，如"市盈率小于20且营收增长超过30%的股票"。

    Source: iwencai.com openapi

    注意: 该接口需要有效的 iwencai token。如未配置，
    将尝试通过 Web 页面接口进行无鉴权查询（功能受限）。

    Args:
        query: 自然语言查询语句，如:
            - "近5日涨幅超过20%的股票"
            - "市盈率低于15且ROE大于20%的银行股"
            - "北向资金连续5日净买入的股票"
            - "今日涨停的人工智能概念股"
        channel: 查询频道，可选:
            - "stock": 股票（默认）
            - "fund": 基金
            - "bond": 债券
            - "index": 指数
        size: 返回条数，默认 10，最大 100

    Returns:
        查询结果列表，每项包含:
        - code: 证券代码
        - name: 证券名称
        - market: 所属市场
        - 其他字段: 根据查询内容动态返回（如涨跌幅、市盈率、营收等）

    示例:
        >>> semantic_search("今日涨停的芯片概念股")
        [{code: "300661", name: "圣邦股份", market: "sz", 涨跌幅: 10.0, ...}]
        >>> semantic_search("ROE连续3年大于20%的消费股", size=20)
    """
    size = min(size, 100)

    # 频道映射
    _CHANNEL_MAP = {
        "stock": "stock",
        "fund": "fund",
        "bond": "bond",
        "index": "index",
        "a股": "stock",
        "基金": "fund",
        "债券": "bond",
        "指数": "index",
    }
    resolved_channel = _CHANNEL_MAP.get(channel.lower(), "stock")

    # 尝试通过 iwencai Web 接口查询
    return _iwencai_web_search(query, resolved_channel, size)


def _iwencai_web_search(query: str, channel: str, size: int) -> list[dict]:
    """通过 iwencai Web 接口进行语义搜索。"""
    url = _IWENCAI_API

    payload = {
        "question": query,
        "perpage": size,
        "page": 1,
        "secondary_intent": channel,
        "log_info": json.dumps({"input_type": "typewrite"}),
        "source": "Ths_iwencai_498",
        "version": "2.0",
        "query_area": "",
        "block_list": "",
        "add_info": json.dumps({"urp": {"scene": 1, "company": 1, "business": 1}}),
    }

    resp = http_post(url, json_data=payload, headers=_IWENCAI_HEADERS)
    if not resp or not resp.ok:
        return []

    try:
        data = resp.json()
    except (ValueError, AttributeError):
        return []

    # 解析 iwencai 复杂返回结构
    answer = data.get("data", {})
    if not isinstance(answer, dict):
        return []

    # 尝试多种结构路径
    components = answer.get("answer", [])
    if isinstance(components, list) and components:
        first_answer = components[0] if components else {}
        if isinstance(first_answer, dict):
            txt = first_answer.get("txt", [])
            if isinstance(txt, list) and txt:
                content = txt[0] if txt else {}
                if isinstance(content, dict):
                    # 表格数据结构
                    result_data = content.get("content", {})
                    if isinstance(result_data, dict):
                        components = result_data.get("components", [])
                        if isinstance(components, list) and components:
                            table_data = components[0].get("data", {})
                            if isinstance(table_data, dict):
                                datas = table_data.get("datas", [])
                                if isinstance(datas, list):
                                    return _parse_iwencai_table(datas)

    # 尝试直接的 data.answer 结构
    result_list = answer.get("result", [])
    if isinstance(result_list, list) and result_list:
        return _parse_iwencai_results(result_list)

    return []


def _parse_iwencai_table(datas: list) -> list[dict]:
    """解析 iwencai 表格数据结构。"""
    results = []
    for row in datas:
        if not isinstance(row, dict):
            continue

        # 提取基本字段
        record = {}
        for key, value in row.items():
            # 转换常见字段名
            clean_key = key.strip()
            if "代码" in clean_key or "code" in clean_key.lower():
                record["code"] = str(value)
            elif "简称" in clean_key or "名称" in clean_key or "name" in clean_key.lower():
                record["name"] = str(value)
            elif "市场" in clean_key or "market" in clean_key.lower():
                record["market"] = str(value)
            else:
                # 保留其他动态字段
                record[clean_key] = value

        if record.get("code") or record.get("name"):
            results.append(record)

    return results


def _parse_iwencai_results(result_list: list) -> list[dict]:
    """解析 iwencai 直接结果列表。"""
    results = []
    for item in result_list:
        if not isinstance(item, dict):
            continue
        record = {
            "code": item.get("code", item.get("stock_code", "")),
            "name": item.get("name", item.get("stock_name", "")),
            "market": item.get("market", ""),
        }
        # 保留其他字段
        for key, value in item.items():
            if key not in ("code", "name", "market", "stock_code", "stock_name"):
                record[key] = value
        results.append(record)

    return results
