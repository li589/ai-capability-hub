# -*- coding: utf-8 -*-
"""
dataSupplement V7.1 · 领域模块 · 舆情互动
==========================================

功能概览:
  - hot_list: 人气热榜（排名/人气值/概念标签/变化）
  - stock_popularity: 个股人气排名+概念热度
  - investor_qa: 互动易问答（投资者提问+公司回复）

数据源:
  - 人气榜: 同花顺 dq.10jqka (扶摇人气榜)
  - 个股热度: 东财 emappdata (人气排名+概念热度)
  - 互动易: 巨潮 irm.cninfo (投资者问答平台)
"""

from __future__ import annotations

import sys
import os
import json
from typing import Optional

# 路径设置: 确保 core/ 和 providers/ 可导入
_SKILL_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _SKILL_ROOT not in sys.path:
    sys.path.insert(0, _SKILL_ROOT)

from core.client import http_get, http_post
from core.cache import cache_get, cache_set, make_key, TTL_QUOTE, TTL_NEWS
from core.throttle import throttled_get
from core.ticker import normalize

# ---------------------------------------------------------------------------
# 内部工具
# ---------------------------------------------------------------------------

_THS_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Referer": "http://www.10jqka.com.cn/",
    "Accept": "application/json, text/plain, */*",
}

_EM_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Referer": "https://guba.eastmoney.com/",
    "Accept": "application/json, text/plain, */*",
}


def _safe_float(val) -> Optional[float]:
    """安全转换为浮点数。"""
    if val is None or val == "" or val == "—" or val == "-":
        return None
    try:
        return float(str(val).replace(",", "").replace("%", ""))
    except (ValueError, TypeError):
        return None


def _safe_int(val) -> Optional[int]:
    """安全转换为整数。"""
    if val is None or val == "" or val == "—":
        return None
    try:
        return int(float(str(val).replace(",", "")))
    except (ValueError, TypeError):
        return None


# ---------------------------------------------------------------------------
# 公开 API
# ---------------------------------------------------------------------------

# 同花顺人气榜 URL
_HOT_LIST_API = "https://dq.10jqka.com.cn/fuyao/hot_list_data/out/hot_list"


def hot_list(period: str = "hour") -> list[dict]:
    """人气热榜（排名/人气值/概念标签/变化）

    获取同花顺扶摇人气排行榜，展示市场关注度最高的股票。

    Source: 同花顺 dq.10jqka
    备用: 东财人气排名

    Args:
        period: 时间维度，可选:
            - "hour": 小时榜（实时关注度）
            - "day": 日榜（当日累计关注）
            - "3day": 3日榜
            - "week": 周榜

    Returns:
        人气排行列表:
        [{code, name, rank, hot_value, change_pct, 
          rank_change, tag, concept, ...}]
    """
    ck = make_key("hot_list", period)
    cached = cache_get(ck)
    if cached is not None:
        return cached

    result = []

    # 主源: 同花顺人气榜
    period_map = {"hour": "hour", "day": "day", "3day": "3day", "week": "week"}
    p = period_map.get(period, "hour")

    try:
        from providers.tonghuashun import hot_list as ths_hot_list
        ths_data = ths_hot_list(p)
        if ths_data:
            result = ths_data
    except Exception:
        pass

    # 直接请求作为备用
    if not result:
        try:
            params = {"period": p, "type": "stock"}
            url = f"{_HOT_LIST_API}?period={p}&type=stock"
            resp = throttled_get(url, headers=_THS_HEADERS)
            if resp and resp.ok:
                data = resp.json()
                result_data = data.get("data", {})
                stock_list = result_data.get("stock_list", [])
                if not stock_list and isinstance(result_data, list):
                    stock_list = result_data

                for item in stock_list:
                    result.append({
                        "code": item.get("code", ""),
                        "name": item.get("name", ""),
                        "rank": _safe_int(item.get("rank", item.get("order"))),
                        "hot_value": _safe_float(item.get("hot_value", item.get("score"))),
                        "change_pct": _safe_float(item.get("change_pct", item.get("rise"))),
                        "rank_change": _safe_int(item.get("rank_change", item.get("change", 0))),
                        "tag": item.get("tag", ""),
                        "concept": item.get("concept", item.get("plate", "")),
                    })
        except Exception:
            pass

    # 备源: 东财人气排名
    if not result:
        try:
            from providers.eastmoney import popularity_rank
            em_data = popularity_rank(top=50)
            for idx, item in enumerate(em_data, 1):
                result.append({
                    "code": item.get("sc", item.get("code", "")),
                    "name": item.get("sn", item.get("name", "")),
                    "rank": idx,
                    "hot_value": _safe_float(item.get("ps", item.get("popularity"))),
                    "change_pct": None,
                    "rank_change": _safe_int(item.get("rc", item.get("rankChange"))),
                    "tag": "",
                    "concept": "",
                })
        except Exception:
            pass

    if result:
        cache_set(ck, result, ttl=TTL_QUOTE)
    return result


# 东财人气/概念热度接口
_POPULARITY_API = "https://emappdata.eastmoney.com/stockrank/getAllCurrentList"
_CONCEPT_HITS_API = "https://emappdata.eastmoney.com/stockrank/getHotStockRank"


def stock_popularity(code: str) -> dict:
    """个股人气排名+概念热度

    获取单只股票在全市场的人气排名，以及该股关联概念板块的热度。

    Source: 东财 emappdata
    备用: 同花顺人气榜搜索

    Args:
        code: 股票代码，如 '600519'

    Returns:
        人气详情字典:
        {code, name, rank, rank_change, popularity_score,
         concepts: [{concept, heat, rank}], ...}
    """
    normalized = normalize(code)

    ck = make_key("stock_popularity", normalized)
    cached = cache_get(ck)
    if cached is not None:
        return cached

    result = {
        "code": normalized,
        "name": "",
        "rank": None,
        "rank_change": None,
        "popularity_score": None,
        "concepts": [],
    }

    # 东财人气排名
    try:
        payload = {
            "appId": "appId01",
            "globalId": "786e4c21-70dc-435a-93bb-38",
            "srcSecurityCode": f"0.{normalized}" if normalized[0] in "0123" else f"1.{normalized}",
        }
        resp = http_post(
            _POPULARITY_API,
            json_data=payload,
            headers=_EM_HEADERS,
        )
        if resp and resp.ok:
            data = resp.json()
            items = data.get("data", [])
            if items and isinstance(items, list):
                item = items[0] if items else {}
                result["name"] = item.get("sn", item.get("name", ""))
                result["rank"] = _safe_int(item.get("rk", item.get("rank")))
                result["rank_change"] = _safe_int(item.get("rc", item.get("rankChange")))
                result["popularity_score"] = _safe_float(item.get("ps", item.get("score")))
    except Exception:
        pass

    # 东财概念热度
    try:
        payload2 = {
            "appId": "appId01",
            "globalId": "786e4c21-70dc-435a-93bb-38",
            "srcSecurityCode": f"0.{normalized}" if normalized[0] in "0123" else f"1.{normalized}",
        }
        resp2 = http_post(
            _CONCEPT_HITS_API,
            json_data=payload2,
            headers=_EM_HEADERS,
        )
        if resp2 and resp2.ok:
            data2 = resp2.json()
            concept_list = data2.get("data", [])
            if isinstance(concept_list, list):
                concepts = []
                for c in concept_list:
                    concepts.append({
                        "concept": c.get("conceptName", c.get("plateName", "")),
                        "heat": _safe_float(c.get("hotValue", c.get("score"))),
                        "rank": _safe_int(c.get("rank")),
                    })
                result["concepts"] = concepts
    except Exception:
        pass

    if result.get("rank") is not None:
        cache_set(ck, result, ttl=TTL_QUOTE)
    return result


# 巨潮互动易接口
_INVESTOR_QA_URL = "https://irm.cninfo.com.cn/ssgs/questionListByPage"


def investor_qa(code: str, page: int = 1) -> list[dict]:
    """互动易问答（投资者提问+公司回复）

    从巨潮互动易平台获取投资者与上市公司的问答记录。

    Source: 巨潮 irm.cninfo
    备用: cninfo provider

    Args:
        code: 股票代码，如 '600519'
        page: 页码，从1开始，每页20条

    Returns:
        问答列表:
        [{question, answer, question_date, answer_date, questioner, ...}]
    """
    normalized = normalize(code)

    ck = make_key("investor_qa", normalized, page)
    cached = cache_get(ck)
    if cached is not None:
        return cached

    result = []

    # 主源: cninfo provider
    try:
        from providers.cninfo import investor_qa as cninfo_qa
        result = cninfo_qa(normalized, page=page)
    except Exception:
        pass

    # 直接请求作为备用
    if not result:
        try:
            params = {
                "stockCode": normalized,
                "pageNo": str(page),
                "pageSize": "20",
            }
            query_str = "&".join(f"{k}={v}" for k, v in params.items())
            url = f"{_INVESTOR_QA_URL}?{query_str}"

            resp = throttled_get(url, headers={
                "User-Agent": _THS_HEADERS["User-Agent"],
                "Referer": "https://irm.cninfo.com.cn/",
                "Accept": "application/json",
            })
            if resp and resp.ok:
                data = resp.json()
                records = data.get("records", data.get("data", []))
                if not isinstance(records, list):
                    records = []

                for item in records:
                    result.append({
                        "question": item.get("question", item.get("mainContent", "")),
                        "answer": item.get("answer", item.get("attachedContent", "")),
                        "question_date": item.get("questionDate", item.get("mainDate", "")),
                        "answer_date": item.get("answerDate", item.get("attachedDate", "")),
                        "questioner": item.get("questioner", item.get("nickname", "")),
                    })
        except Exception:
            pass

    if result:
        cache_set(ck, result, ttl=TTL_NEWS)
    return result
