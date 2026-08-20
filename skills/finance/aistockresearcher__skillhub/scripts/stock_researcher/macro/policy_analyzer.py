#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""政策解读模块 (v6.1 新增)

从东方财富财经新闻接口抓取最近政策相关新闻，按 POLICY_KEYWORDS 分类表
逐条匹配政策事件，输出结构化的政策影响分析：
  - 政策分类（货币政策/财政政策/资本市场政策/行业政策/海外政策）
  - 影响方向（利多/利空/双向）
  - 受影响板块与受影响市场
  - 重要度(1-5)与一句话中文解读
  - policy_score: 综合政策面对指定市场的净影响分 (-100~+100)

本模块不含 LLM；format_for_llm() 输出 markdown 结构化清单，
方便 Agent 宿主在此基础上做深度解读。

数据来源（全部免费、国内直连）：
  - 东财国内要闻: np-listapi.eastmoney.com column=350
  - 东财搜索:     search-api-web.eastmoney.com (JSONP 包裹，需剥离)

注意：东财限流激进，所有请求节流 >=1.5s、失败退避重试、绝不抛出 traceback。
"""
from __future__ import annotations

import json
import re
import time
import urllib.request
import urllib.error
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from urllib.parse import quote

# ── 请求基础设施（节流 + 退避重试，自包含不依赖 pkg）──────────
_UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
       "AppleWebKit/537.36 (KHTML, like Gecko) "
       "Chrome/120.0.0.0 Safari/537.36")
_MIN_INTERVAL = 1.6   # 东财限流激进：请求间隔 >=1.5s
_last_req = 0.0


def _throttle():
    """请求节流：保证距上次请求至少 _MIN_INTERVAL 秒"""
    global _last_req
    wait = _MIN_INTERVAL - (time.time() - _last_req)
    if wait > 0:
        time.sleep(wait)
    _last_req = time.time()


def _http_get(url: str, timeout: int = 10, retries: int = 3) -> Optional[bytes]:
    """带退避重试的 HTTP GET，全部失败返回 None（绝不抛异常）"""
    for attempt in range(retries):
        try:
            _throttle()
            req = urllib.request.Request(url, headers={
                "User-Agent": _UA,
                "Referer": "https://www.eastmoney.com/",
                "Accept": "*/*",
            })
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return resp.read()
        except Exception:
            if attempt < retries - 1:
                time.sleep(2.0 * (attempt + 1))   # 退避 2s/4s
    return None


def _strip_jsonp(text: str) -> Optional[dict]:
    """剥离 JSONP 包裹（如 jQuery({...})），返回 dict 或 None"""
    if not text:
        return None
    t = text.lstrip("﻿ \r\n")
    # 去掉 callback(...) 包裹
    m = re.search(r"^[A-Za-z_$][\w$]*\s*\((.*)\)\s*;?\s*$", t, re.S)
    if m:
        t = m.group(1)
    try:
        return json.loads(t)
    except (json.JSONDecodeError, ValueError):
        return None


# ── 政策事件分类表 ──────────────────────────────────────────
# 每条：category 分类、keywords 关键词、direction 影响方向(利多/利空/双向)、
#       sectors 受影响板块、markets 受影响市场(cn/hk/us/global)、importance 基础重要度
POLICY_KEYWORDS: List[Dict] = [
    # ── 货币政策 ──
    {
        "category": "货币政策-宽松",
        "keywords": ["降准", "降息", "LPR下调", "LPR 下调", "MLF", "中期借贷便利",
                     "逆回购放量", "宽松", "量化宽松", "QE", "扩表", "流动性投放",
                     "再贷款", "麻辣粉"],
        "direction": "利多",
        "sectors": ["银行", "非银金融", "房地产", "有色金属"],
        "markets": ["cn", "hk"],
        "importance": 4,
    },
    {
        "category": "货币政策-收紧",
        "keywords": ["加息", "缩表", "QT", "量化紧缩", "回笼流动性", "收紧"],
        "direction": "利空",
        "sectors": ["房地产", "新能源", "计算机", "电子"],
        "markets": ["cn", "hk", "us", "global"],
        "importance": 4,
    },
    # ── 财政政策 ──
    {
        "category": "财政政策-积极",
        "keywords": ["专项债", "特别国债", "减税降费", "减税", "财政刺激",
                     "基建投资", "以旧换新", "消费补贴", "化债"],
        "direction": "利多",
        "sectors": ["机械设备", "化工", "汽车", "食品饮料", "有色金属"],
        "markets": ["cn"],
        "importance": 4,
    },
    {
        "category": "财政政策-紧缩",
        "keywords": ["加税", "财政整顿", "削减赤字", "财政悬崖"],
        "direction": "利空",
        "sectors": ["机械设备", "化工"],
        "markets": ["cn", "global"],
        "importance": 3,
    },
    # ── 资本市场政策 ──
    {
        "category": "资本市场-交易制度",
        "keywords": ["注册制", "IPO", "退市", "减持新规", "印花税", "分红",
                     "回购增持", "中长期资金", "险资入市", "养老金入市",
                     "并购重组", "市值管理", "交易经手费"],
        "direction": "双向",
        "sectors": ["非银金融", "银行"],
        "markets": ["cn"],
        "importance": 3,
    },
    {
        "category": "资本市场-资金利好",
        "keywords": ["印花税下调", "降低印花税", "鼓励分红", "国家队", "汇金增持",
                     "平准基金", "险资", "社保入市", "放宽外资"],
        "direction": "利多",
        "sectors": ["非银金融", "银行", "食品饮料"],
        "markets": ["cn", "hk"],
        "importance": 4,
    },
    {
        "category": "资本市场-监管收紧",
        "keywords": ["IPO提速", "IPO加速", "规范减持", "严查", "处罚", "立案调查",
                     "监管风暴"],
        "direction": "利空",
        "sectors": ["非银金融"],
        "markets": ["cn"],
        "importance": 3,
    },
    # ── 行业政策 ──
    {
        "category": "行业政策-新能源",
        "keywords": ["新能源", "光伏", "风电", "储能", "锂电池", "充电桩",
                     "新能源车", "碳中和", "双碳"],
        "direction": "双向",
        "sectors": ["新能源", "汽车", "有色金属"],
        "markets": ["cn"],
        "importance": 3,
    },
    {
        "category": "行业政策-地产",
        "keywords": ["房地产", "地产", "房贷", "限购", "公积金", "保交楼",
                     "白名单", "城中村", "保障房", "首付比例"],
        "direction": "双向",
        "sectors": ["房地产", "银行", "机械设备"],
        "markets": ["cn", "hk"],
        "importance": 4,
    },
    {
        "category": "行业政策-半导体",
        "keywords": ["半导体", "芯片", "集成电路", "国产替代", "大基金",
                     "光刻", "先进制程", "EDA"],
        "direction": "双向",
        "sectors": ["电子", "计算机", "通信"],
        "markets": ["cn", "hk", "us"],
        "importance": 3,
    },
    {
        "category": "行业政策-医药",
        "keywords": ["医药", "集采", "医保谈判", "创新药", "医疗器械",
                     "生物医药", "CXO"],
        "direction": "双向",
        "sectors": ["医药生物"],
        "markets": ["cn", "hk"],
        "importance": 3,
    },
    {
        "category": "行业政策-金融",
        "keywords": ["银行", "券商", "保险", "金融监管", "资本充足率",
                     "存款利率", "息差"],
        "direction": "双向",
        "sectors": ["银行", "非银金融"],
        "markets": ["cn", "hk"],
        "importance": 3,
    },
    {
        "category": "行业政策-消费",
        "keywords": ["消费", "消费券", "提振消费", "内需", "零售", "免税",
                     "白酒", "生育补贴"],
        "direction": "双向",
        "sectors": ["食品饮料", "汽车", "传媒"],
        "markets": ["cn"],
        "importance": 3,
    },
    # ── 海外政策 ──
    {
        "category": "海外政策-美联储鸽派",
        "keywords": ["美联储降息", "鸽派", "FOMC降息", "放缓缩表", "鲍威尔鸽"],
        "direction": "利多",
        "sectors": ["有色金属", "电子", "计算机", "新能源"],
        "markets": ["us", "global", "hk"],
        "importance": 4,
    },
    {
        "category": "海外政策-美联储鹰派",
        "keywords": ["美联储加息", "鹰派", "FOMC加息", "维持高利率", "缩表加速",
                     "鲍威尔鹰"],
        "direction": "利空",
        "sectors": ["电子", "计算机", "新能源"],
        "markets": ["us", "global", "hk"],
        "importance": 4,
    },
    {
        "category": "海外政策-宏观数据",
        "keywords": ["非农", "CPI", "PPI", "通胀数据", "就业数据", "失业率",
                     "GDP"],
        "direction": "双向",
        "sectors": [],
        "markets": ["us", "global"],
        "importance": 3,
    },
    {
        "category": "海外政策-关税制裁",
        "keywords": ["关税", "制裁", "出口管制", "实体清单", "贸易战",
                     "反制", "加征"],
        "direction": "利空",
        "sectors": ["电子", "计算机", "通信", "新能源"],
        "markets": ["global", "cn", "us"],
        "importance": 4,
    },
    {
        "category": "海外政策-地缘政治",
        "keywords": ["冲突", "战争", "地缘", "停火", "谈判", "中东局势",
                     "红海", "霍尔木兹"],
        "direction": "双向",
        "sectors": ["军工", "有色金属"],
        "markets": ["global"],
        "importance": 3,
    },
]

# 方向 → 符号
_DIRECTION_SIGN = {"利多": 1, "利空": -1, "双向": 0}

# ── 一句话解读模板 ─────────────────────────────────────────
_INTERPRET_TEMPLATES = {
    "利多": "{category}释放积极信号，{sector_text}板块有望受益，关注政策落地节奏。",
    "利空": "{category}偏紧，{sector_text}板块短期承压，注意规避风险敞口。",
    "双向": "{category}出现新变化，影响双向分化，{sector_text}板块需结合细则判断。",
}

# ── 模块级缓存（避免重复抓取触发限流）──────────────────────
_CACHE = {"ts": 0.0, "news": None, "analysis": None}
_CACHE_TTL = 300   # 5 分钟内复用结果


def _fetch_domestic_news(page_size: int = 30) -> List[Dict]:
    """东财国内要闻 column=350（已实测可用，返回纯 JSON）"""
    url = ("https://np-listapi.eastmoney.com/comm/web/getNewsByColumns?"
           "client=web&biz=web_news_col&column=350&order=1&needInteractData=0"
           f"&page_index=1&page_size={page_size}&req_trace=1")
    raw = _http_get(url)
    news = []
    if not raw:
        return news
    try:
        data = json.loads(raw.decode("utf-8-sig", errors="replace"))
    except (json.JSONDecodeError, ValueError):
        return news
    items = (data.get("data") or {}).get("list") or []
    for item in items:
        title = item.get("title", "") or ""
        if not title:
            continue
        news.append({
            "title": title,
            "date": (item.get("showtime", "") or "")[:10],
            "url": item.get("url", "") or "",
            "source": "东财-国内要闻",
        })
    return news


def _fetch_search_news(keyword: str, page_size: int = 20) -> List[Dict]:
    """东财搜索接口（JSONP 包裹需剥离）。已实测可用。"""
    param = {
        "uid": "", "keyword": keyword, "type": ["cmsArticleWebOld"],
        "client": "web", "clientType": "web", "clientVersion": "curr",
        "param": {"cmsArticleWebOld": {"searchScope": "default", "sort": "time",
                                       "pageIndex": 1, "pageSize": page_size}},
    }
    url = ("https://search-api-web.eastmoney.com/search/jsonp?cb=jQuery&param="
           + quote(json.dumps(param, ensure_ascii=False)))
    raw = _http_get(url)
    news = []
    if not raw:
        return news
    data = _strip_jsonp(raw.decode("utf-8-sig", errors="replace"))
    if not data:
        return news
    items = ((data.get("result") or {}).get("cmsArticleWebOld")) or []
    for item in items:
        title = re.sub(r"<[^>]+>", "", item.get("title", "") or "")  # 搜索标题可能带高亮标签
        if not title:
            continue
        news.append({
            "title": title,
            "date": (item.get("date", "") or "")[:10],
            "url": item.get("url", "") or "",
            "source": f"东财-搜索[{keyword}]",
        })
    return news


def fetch_policy_news(days: int = 7, use_cache: bool = True) -> List[Dict]:
    """抓取最近 days 天的政策相关新闻（多源合并去重）。

    数据源：东财国内要闻(column 350) + 东财搜索("央行"/"美联储")。
    任一源失败不影响其他源；全部失败返回空列表。

    Args:
        days: 回溯天数
        use_cache: 是否使用 5 分钟模块级缓存

    Returns:
        [{title, date, url, source}, ...] 按日期倒序
    """
    if use_cache and _CACHE["news"] is not None and \
            time.time() - _CACHE["ts"] < _CACHE_TTL:
        return _CACHE["news"]

    cutoff = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    all_news: List[Dict] = []
    all_news.extend(_fetch_domestic_news(page_size=30))
    for kw in ("央行", "美联储"):
        all_news.extend(_fetch_search_news(kw, page_size=20))

    # 过滤日期 + 按标题去重
    seen = set()
    news = []
    for item in all_news:
        date = item.get("date") or ""
        if date and date < cutoff:
            continue
        key = re.sub(r"\s+", "", item["title"])
        if key in seen:
            continue
        seen.add(key)
        news.append(item)
    news.sort(key=lambda x: x.get("date", ""), reverse=True)

    _CACHE["ts"] = time.time()
    _CACHE["news"] = news
    return news


def _match_policy(title: str) -> List[Dict]:
    """匹配标题命中的政策分类条目"""
    matched = []
    for entry in POLICY_KEYWORDS:
        if any(kw in title for kw in entry["keywords"]):
            matched.append(entry)
    return matched


def analyze_policy_impact(news_items: List[Dict], use_cache: bool = True) -> List[Dict]:
    """逐条分析新闻的政策影响。

    Args:
        news_items: fetch_policy_news 的返回
        use_cache: 是否使用 5 分钟模块级缓存（同一批新闻）

    Returns:
        [{title, date, source, url, category, direction, affected_sectors,
          affected_markets, importance(1-5), interpretation}, ...]
        只保留命中政策关键词的新闻；未命中的丢弃。
    """
    if use_cache and _CACHE["analysis"] is not None and \
            _CACHE["news"] is news_items and \
            time.time() - _CACHE["ts"] < _CACHE_TTL:
        return _CACHE["analysis"]

    results = []
    for item in news_items:
        title = item.get("title", "")
        matched = _match_policy(title)
        if not matched:
            continue

        # 合并命中条目：分类拼接、方向取多数、板块/市场并集
        categories = [m["category"] for m in matched]
        directions = [m["direction"] for m in matched]
        pos = directions.count("利多")
        neg = directions.count("利空")
        if pos > neg:
            direction = "利多"
        elif neg > pos:
            direction = "利空"
        else:
            direction = "双向"

        sectors: List[str] = []
        markets: List[str] = []
        for m in matched:
            for s in m["sectors"]:
                if s not in sectors:
                    sectors.append(s)
            for mk in m["markets"]:
                if mk not in markets:
                    markets.append(mk)

        # 重要度：基础重要度最大值 + 多分类命中加成，封顶 5
        importance = max(m["importance"] for m in matched)
        if len(matched) >= 2:
            importance += 1
        importance = max(1, min(5, importance))

        sector_text = "、".join(sectors[:3]) if sectors else "相关"
        interpretation = _INTERPRET_TEMPLATES[direction].format(
            category=categories[0], sector_text=sector_text)

        results.append({
            "title": title,
            "date": item.get("date", ""),
            "source": item.get("source", ""),
            "url": item.get("url", ""),
            "category": "、".join(dict.fromkeys(categories)),
            "direction": direction,
            "affected_sectors": sectors,
            "affected_markets": markets,
            "importance": importance,
            "interpretation": interpretation,
        })

    _CACHE["analysis"] = results
    return results


def policy_score(market: str = "cn", days: int = 7) -> Dict:
    """综合最近政策面对指定市场的净影响分 (-100 ~ +100)。

    计分规则：Σ(方向符号 × 重要度)，只统计覆盖该市场(或 global)的事件，
    双向事件计 0 分但计入事件数；总分按 Σ符号×重要度 × 10 缩放并封顶 ±100。

    Returns:
        {score, label, event_count, pos_count, neg_count, market, days, top_events}
    """
    news = fetch_policy_news(days=days)
    analysis = analyze_policy_impact(news)

    total = 0.0
    pos_count = neg_count = 0
    used = []
    for ev in analysis:
        markets = ev.get("affected_markets", [])
        if market not in markets and "global" not in markets:
            continue
        sign = _DIRECTION_SIGN.get(ev["direction"], 0)
        total += sign * ev["importance"]
        if sign > 0:
            pos_count += 1
        elif sign < 0:
            neg_count += 1
        used.append(ev)

    score = max(-100.0, min(100.0, total * 10))
    if score >= 40:
        label = "政策面明显偏多"
    elif score >= 15:
        label = "政策面温和偏多"
    elif score > -15:
        label = "政策面中性"
    elif score > -40:
        label = "政策面温和偏空"
    else:
        label = "政策面明显偏空"

    return {
        "score": round(score, 1),
        "label": label,
        "event_count": len(used),
        "pos_count": pos_count,
        "neg_count": neg_count,
        "market": market,
        "days": days,
        "top_events": sorted(used, key=lambda x: x["importance"], reverse=True)[:5],
    }


def format_for_llm(news_items: List[Dict]) -> str:
    """输出结构化政策事件清单（markdown），方便 Agent 宿主做深度解读。

    本 skill 不含 LLM；此格式可直接粘贴给大模型作为分析上下文。
    """
    analysis = analyze_policy_impact(news_items)
    lines = ["# 政策事件清单（结构化，供深度解读）", ""]
    if not analysis:
        lines.append("近期未捕获到命中政策关键词的新闻（可能为网络原因）。")
        return "\n".join(lines)

    # 按分类分组
    groups: Dict[str, List[Dict]] = {}
    for ev in analysis:
        key = ev["category"].split("-")[0]
        groups.setdefault(key, []).append(ev)

    for group, events in groups.items():
        lines.append(f"## {group}")
        for ev in events:
            lines.append(
                f"- **[{ev['direction']}|重要度{ev['importance']}/5]** "
                f"{ev['title']}（{ev.get('date', '')}）")
            lines.append(f"  - 分类: {ev['category']}")
            if ev["affected_sectors"]:
                lines.append(f"  - 受影响板块: {'、'.join(ev['affected_sectors'])}")
            lines.append(f"  - 受影响市场: {', '.join(ev['affected_markets'])}")
            lines.append(f"  - 初步解读: {ev['interpretation']}")
        lines.append("")
    return "\n".join(lines)


def format_policy_report(market: str = "cn", days: int = 7) -> str:
    """生成政策解读文本报告（中文表格风格）"""
    news = fetch_policy_news(days=days)
    analysis = analyze_policy_impact(news)
    score = policy_score(market=market, days=days)

    lines = []
    hr = "=" * 70
    lines.append(hr)
    lines.append(f"  📜 政策解读报告  |  最近{days}天  |  "
                 f"{datetime.now().strftime('%Y-%m-%d %H:%M')}")
    lines.append(hr)
    lines.append(f"  政策面净影响({market.upper()}): {score['score']:+.1f}  "
                 f"[{score['label']}]  事件{score['event_count']}件 "
                 f"(利多{score['pos_count']}/利空{score['neg_count']})")
    lines.append("-" * 70)
    if not analysis:
        lines.append("  近期未捕获到政策相关新闻（数据源不可用或限流，稍后重试）。")
    for ev in analysis[:15]:
        icon = "🟢" if ev["direction"] == "利多" else \
               ("🔴" if ev["direction"] == "利空" else "🟡")
        lines.append(f"  {icon} [{ev['category']}|重要度{ev['importance']}] "
                     f"{ev['title'][:38]}")
        lines.append(f"     {ev['interpretation']}")
        if ev["affected_sectors"]:
            lines.append(f"     板块: {'、'.join(ev['affected_sectors'][:4])}  "
                         f"市场: {', '.join(ev['affected_markets'])}")
    lines.append(hr)
    return "\n".join(lines)


def main():
    print(format_policy_report())


if __name__ == "__main__":
    main()
