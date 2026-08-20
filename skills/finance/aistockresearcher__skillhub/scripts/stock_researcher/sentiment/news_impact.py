#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
新闻利好/利空识别 (v6.1.0)
==========================
纯规则（不调 LLM）的新闻情绪分析：
  - 逐条判定 利好/利空/中性 + 强度(1-5) + 类型标签
  - 关键词命中 + 程度副词加权，中英文覆盖
  - 综合新闻情绪分（带时效衰减：24h 权重 1.0 / 72h 0.6 / 更早 0.3）

用法:
    from stock_researcher.sentiment.news_impact import (
        analyze_news_impact, summarize_good_news, summarize_bad_news, news_score,
    )
    items = [{"title": "公司前三季度净利润同比增长19%，超市场预期", "summary": "..."}]
    print(analyze_news_impact(items))
    print(news_score(items))
"""

import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from .sentiment_keywords import (
    CN_POSITIVE_KEYWORDS, CN_NEGATIVE_KEYWORDS,
    CN_STRONG_POSITIVE, CN_STRONG_NEGATIVE,
    EN_POSITIVE_KEYWORDS, EN_NEGATIVE_KEYWORDS,
    EN_STRONG_POSITIVE, EN_STRONG_NEGATIVE,
    HK_SPECIFIC_POSITIVE, HK_SPECIFIC_NEGATIVE,
)

# ═══════════════════════════════════════════════════════════════
# 新闻类型标签 → 识别关键词（命中即归类，按表内顺序优先）
# ═══════════════════════════════════════════════════════════════

NEWS_CATEGORIES = {
    "监管处罚": [
        "立案", "立案调查", "处罚", "罚款", "警示函", "监管函", "违规",
        "财务造假", "造假", "退市", "终止上市", "investigation", "probe",
        "sec investigation", "fine", "fraud", "class action", "delisting",
    ],
    "增减持": [
        "增持", "减持", "举牌", "清仓式减持", "大宗交易减持", "stake",
        "insider buying", "insider selling",
    ],
    "并购重组": [
        "并购", "重组", "收购", "借壳", "资产注入", "分拆", "要约",
        "merger", "acquisition", "takeover", "spin-off", "spinoff", "m&a",
    ],
    "评级调整": [
        "评级", "目标价", "上调评级", "下调评级", "upgrade", "downgrade",
        "price target", "initiated", "overweight", "underweight", "top pick",
    ],
    "分红回购": [
        "分红", "派息", "回购", "回购注销", "送转", "股息", "特别息",
        "buyback", "dividend", "repurchase", "share repurchase",
    ],
    "订单合同": [
        "中标", "订单", "合同", "签订", "签约", "框架协议", "定点",
        "批量交付", "订单饱满", "wins contract", "secures deal",
        "contract", "backlog",
    ],
    "业绩": [
        "业绩", "净利润", "净利", "营收", "利润", "亏损", "扭亏",
        "盈利", "年报", "季报", "中报", "业绩预告", "业绩快报",
        "超预期", "预亏", "预减", "盈喜", "盈警", "earnings", "profit",
        "revenue", "guidance", "eps",
    ],
    "政策": [
        "政策", "国务院", "央行", "发改委", "工信部", "财政部", "补贴",
        "规划", "降准", "降息", "试点", "批复", "获批", "policy",
        "stimulus", "fed ", "rate cut", "rate hike", "subsidy",
    ],
    "宏观": [
        "宏观", "经济", "gdp", "cpi", "pmi", "通胀", "关税", "利率",
        "汇率", "非农", "inflation", "tariff", "macro", "economy",
        "jobs report", "recession",
    ],
    "行业动态": [
        "行业", "产能", "涨价", "降价", "提价", "供需", "景气",
        "价格战", "扩产", "投产", "量产", "sector", "industry",
        "price war", "capacity", "demand",
    ],
}

# ═══════════════════════════════════════════════════════════════
# 程度副词（调整强度，不改变方向）
# ═══════════════════════════════════════════════════════════════

DEGREE_STRONG = [
    "大幅", "显著", "巨额", "重磅", "超级", "爆发", "翻倍", "翻番",
    "创历史新高", "创新高", "史上", "首次", "空前", "同比大增",
    "soar", "surge", "record", "massive", "sharp", "plunge",
    "tumble", "crash", "all-time", "blockbuster",
]

DEGREE_WEAK = [
    "小幅", "略有", "微幅", "轻微", "温和", "slightly", "modest",
    "marginal", "mild", "narrowly",
]

# 时间字段候选（不同数据源字段名不同）
_TIME_KEYS = ("time", "public_date", "date", "showTime", "showtime", "created_at")

_TIME_FORMATS = (
    "%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d",
    "%Y/%m/%d %H:%M:%S", "%Y/%m/%d %H:%M", "%Y/%m/%d",
    "%Y年%m月%d日 %H:%M", "%Y年%m月%d日",
)


def _parse_news_time(item: Dict) -> Optional[datetime]:
    """尽力解析新闻时间，解析失败返回 None"""
    raw = None
    for key in _TIME_KEYS:
        if item.get(key):
            raw = item[key]
            break
    if raw is None:
        return None

    # 时间戳（秒或毫秒）
    if isinstance(raw, (int, float)):
        try:
            ts = float(raw)
            if ts > 1e12:
                ts /= 1000.0
            return datetime.fromtimestamp(ts)
        except Exception:
            return None

    text = str(raw).strip()
    if text.isdigit():
        return _parse_news_time({"time": int(text)})

    text = text.replace("T", " ").split("+")[0].split("Z")[0].strip()
    for fmt in _TIME_FORMATS:
        try:
            return datetime.strptime(text, fmt)
        except Exception:
            continue
    # 截断后重试（容忍尾部多余字符）
    for fmt in _TIME_FORMATS:
        try:
            return datetime.strptime(text[:19], fmt)
        except Exception:
            continue
    return None


def _time_weight(item: Dict, now: Optional[datetime] = None) -> float:
    """时效衰减：24h 内 1.0，72h 内 0.6，更早 0.3；无法解析按 0.8 处理"""
    t = _parse_news_time(item)
    if t is None:
        return 0.8
    now = now or datetime.now()
    age = now - t
    if age < timedelta(hours=24):
        return 1.0
    if age < timedelta(hours=72):
        return 0.6
    return 0.3


def _detect_category(text_lower: str) -> str:
    """识别新闻类型标签"""
    for category, keywords in NEWS_CATEGORIES.items():
        for kw in keywords:
            if kw in text_lower:
                return category
    return "综合"


def _count_hits(text_lower: str, keywords: List[str]) -> int:
    return sum(1 for kw in keywords if kw in text_lower)


def _analyze_one(item: Dict) -> Dict:
    """逐条分析：利好/利空/中性 + 强度(1-5) + 类型标签"""
    title = str(item.get("title", "") or "")
    summary = str(item.get("summary", "") or item.get("content", "") or "")
    text = f"{title} {summary}"
    text_lower = text.lower()

    # 中英文关键词一起匹配（中文不区分大小写，lower 不影响）
    pos_hits = _count_hits(text_lower, [k.lower() for k in CN_POSITIVE_KEYWORDS + HK_SPECIFIC_POSITIVE + EN_POSITIVE_KEYWORDS])
    neg_hits = _count_hits(text_lower, [k.lower() for k in CN_NEGATIVE_KEYWORDS + HK_SPECIFIC_NEGATIVE + EN_NEGATIVE_KEYWORDS])
    strong_pos = _count_hits(text_lower, [k.lower() for k in CN_STRONG_POSITIVE + EN_STRONG_POSITIVE])
    strong_neg = _count_hits(text_lower, [k.lower() for k in CN_STRONG_NEGATIVE + EN_STRONG_NEGATIVE])

    net = pos_hits - neg_hits
    if net > 0:
        direction = "利好"
    elif net < 0:
        direction = "利空"
    else:
        direction = "中性"

    # 强度：基础 1 + 命中密度 + 强信号加成 + 程度副词调整
    hits = pos_hits + neg_hits
    strength = 1
    if hits > 0:
        strength = min(3, 1 + (hits - 1) // 2)
    if strong_pos or strong_neg:
        strength += 1
    if any(w in text_lower for w in DEGREE_STRONG):
        strength += 1
    if any(w in text_lower for w in DEGREE_WEAK):
        strength -= 1
    if direction == "中性":
        strength = 1
    strength = max(1, min(5, strength))

    # 提取命中的代表性关键词（最多5个）
    matched = []
    for kw in (CN_STRONG_POSITIVE + CN_STRONG_NEGATIVE + EN_STRONG_POSITIVE + EN_STRONG_NEGATIVE
               + CN_POSITIVE_KEYWORDS + CN_NEGATIVE_KEYWORDS):
        if kw in text_lower or kw.lower() in text_lower:
            if kw not in matched:
                matched.append(kw)
        if len(matched) >= 5:
            break

    return {
        "title": title,
        "summary": summary[:120],
        "time": next((item[k] for k in _TIME_KEYS if item.get(k)), ""),
        "direction": direction,     # 利好/利空/中性
        "strength": strength,       # 1-5
        "category": _detect_category(text_lower),
        "score": (strength if direction == "利好" else (-strength if direction == "利空" else 0)),
        "keywords": matched,
    }


def analyze_news_impact(news_items: List[Dict]) -> List[Dict]:
    """
    对新闻列表逐条判定利好/利空。

    Args:
        news_items: [{"title": str, "summary"/"content": str, "time"/"public_date": ...}, ...]

    Returns:
        List[Dict]: 每条含 direction/strength(1-5)/category/score/keywords
    """
    results = []
    for item in news_items or []:
        try:
            results.append(_analyze_one(item))
        except Exception:
            results.append({
                "title": str(item.get("title", "") or ""),
                "summary": "", "time": "",
                "direction": "中性", "strength": 1,
                "category": "综合", "score": 0, "keywords": [],
            })
    return results


def _importance(analyzed: Dict, now: Optional[datetime] = None) -> float:
    """重要性 = 强度 × 时效权重"""
    return analyzed.get("strength", 1) * _time_weight(analyzed, now)


def summarize_good_news(news_items: List[Dict], top_n: int = 5) -> List[Dict]:
    """提取最重要的利好新闻摘要（按 强度×时效 排序）"""
    analyzed = analyze_news_impact(news_items)
    now = datetime.now()
    good = [a for a in analyzed if a["direction"] == "利好"]
    good.sort(key=lambda a: _importance(a, now), reverse=True)
    return good[:top_n]


def summarize_bad_news(news_items: List[Dict], top_n: int = 5) -> List[Dict]:
    """提取最重要的利空新闻摘要（按 强度×时效 排序）"""
    analyzed = analyze_news_impact(news_items)
    now = datetime.now()
    bad = [a for a in analyzed if a["direction"] == "利空"]
    bad.sort(key=lambda a: _importance(a, now), reverse=True)
    return bad[:top_n]


def news_score(news_items: List[Dict]) -> float:
    """
    综合新闻情绪分，-100 ~ +100。

    单条贡献 = score(±强度) × 12 × 时效权重，求和后做软压缩
    （raw/(100+|raw|)×100），避免多条同向新闻直接顶满 ±100。
    """
    if not news_items:
        return 0.0
    now = datetime.now()
    total = 0.0
    try:
        for a in analyze_news_impact(news_items):
            total += a.get("score", 0) * 12.0 * _time_weight(a, now)
    except Exception:
        return 0.0
    score = total * 100.0 / (100.0 + abs(total))
    return round(max(-100.0, min(100.0, score)), 1)


def main():
    """简单自测"""
    items = [
        {"title": "贵州茅台前三季度净利润同比增长19%，超市场预期", "summary": "公司公告"},
        {"title": "某公司遭证监会立案调查，涉嫌财务造假", "summary": "监管动态"},
        {"title": "行业动态：白酒批价稳定", "summary": ""},
    ]
    for a in analyze_news_impact(items):
        print(a["direction"], a["strength"], a["category"], a["title"][:30])
    print("good:", [g["title"][:20] for g in summarize_good_news(items)])
    print("score:", news_score(items))


if __name__ == "__main__":
    main()
