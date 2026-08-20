#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
统一舆情关键词库 (v6.0.0)
==========================
合并了 sentiment_forum_crawler.py、news.py、agents/sentiment.py 三处重复定义。
支持中英文多市场。
"""

# ═══════════════════════════════════════════════════════════════
# 中文关键词（A股 + 港股通用）
# ═══════════════════════════════════════════════════════════════

CN_POSITIVE_KEYWORDS = [
    "涨停", "大涨", "暴涨", "净流入", "业绩预增", "政策利好",
    "回购", "增持", "上调评级", "突破", "创新高", "国产替代",
    "中标", "订单", "合作", "扩张", "超预期", "大幅增长",
    "行业龙头", "技术突破", "产能扩张", "低估", "价值投资",
    "抄底", "加仓", "看好", "必涨", "牛", "赚", "盈利",
    "研发投入", "市场份额提升", "毛利率改善", "现金流改善",
    "派息", "分红增加", "回购注销",
    # v6.1.0 增量：新闻利好高频词
    "签订", "签约", "获批", "获批上市", "中标金额", "涨价", "提价",
    "订单饱满", "扩产", "满产", "放量", "扭亏", "扭亏为盈", "创新高",
    "净利增长", "利润增长", "营收增长", "同比大增", "环比改善",
    "批量交付", "量产", "投产", "点火", "并表", "资产注入",
    "引入战投", "战略投资", "借壳上市", "分拆上市", "股权激励",
    "高送转", "特别分红", "提价函", "供不应求", "景气度提升",
    "开门红", "预喜", "盈喜", "双增长", "恢复增长",
    "增长", "好转", "回暖", "向好",
]

CN_NEGATIVE_KEYWORDS = [
    "跌停", "大跌", "暴跌", "净流出", "业绩下滑", "被调查",
    "被处罚", "减持", "下调评级", "产能过剩", "黑天鹅",
    "诉讼", "亏损", "债务危机", "商誉减值", "大幅减少",
    "业绩变脸", "库存积压", "竞争加剧", "政策利空",
    "雷", "崩盘", "割肉", "清仓", "跑", "亏", "死", "凉",
    "退市风险", "ST", "带帽", "质押爆仓", "资金链断裂",
    "流动性紧张", "信用评级下调", "大股东占款",
    # v6.1.0 增量：新闻利空高频词
    "立案", "立案调查", "处罚", "罚款", "警示函", "问询函",
    "退市", "终止上市", "暂停上市", "质押", "爆仓", "强平",
    "下调", "暴雷", "爆雷", "商誉减值", "资产减值", "计提",
    "业绩预亏", "首亏", "续亏", "预减", "盈警", "盈利警告",
    "债务违约", "逾期", "冻结", "查封", "仲裁",
    "监管函", "违规", "造假", "财务造假", "虚增", "掏空",
    "解禁", "抛压", "大宗交易减持", "清仓式减持", "降价", "价格战",
    "库存高企", "毛利率下滑", "现金流恶化",
]

CN_STRONG_POSITIVE = [
    "涨停", "大涨", "业绩预增", "回购", "增持", "突破",
    "中标", "政策利好", "超预期",
]

CN_STRONG_NEGATIVE = [
    "跌停", "大跌", "被调查", "被处罚", "债务危机",
    "ST", "退市风险", "崩盘",
]

# ═══════════════════════════════════════════════════════════════
# 英文关键词（美股 + 国际通用）
# ═══════════════════════════════════════════════════════════════

EN_POSITIVE_KEYWORDS = [
    "beat", "raise", "upgrade", "buyback", "acquisition",
    "partnership", "fda approval", "launch", "record",
    "surge", "outperform", "growth", "expansion",
    "dividend increase", "guidance raised", "strong demand",
    "profit", "gain", "bullish", "rally", "breakout",
    "positive", "momentum", "upward", "accelerating",
    # v6.1.0 增量：常见英文利好词
    "beats", "exceeds", "topped", "upgraded", "raises guidance",
    "boosts", "soars", "jumps", "climbs", "rebounds", "recovers",
    "all-time high", "52-week high", "new high", "upside",
    "strong earnings", "revenue growth", "margin expansion",
    "share repurchase", "stock buyback", "special dividend",
    "dividend hike", "raises dividend", "wins contract",
    "secures deal", "strategic partnership", "joint venture",
    "approval granted", "clears fda", "breakthrough", "launches",
    "expands capacity", "ramp up", "backlog", "robust demand",
    "overweight", "top pick", "outlook raised",
]

EN_NEGATIVE_KEYWORDS = [
    "miss", "downgrade", "layoff", "lawsuit", "investigation",
    "recall", "decline", "warning", "cut", "weak",
    "delay", "debt", "bankruptcy", "guidance lowered",
    "sell-off", "crash", "underperform", "loss",
    "bearish", "plunge", "negative", "downturn",
    "restructuring", "impairment",
    # v6.1.0 增量：常见英文利空词
    "misses", "falls short", "downgraded", "lowers guidance",
    "cuts guidance", "slashes", "tumbles", "plunges", "slides",
    "sinks", "drops", "selloff", "sell off", "pullback",
    "52-week low", "new low", "downside", "weak demand",
    "earnings miss", "revenue miss", "margin pressure",
    "margin compression", "profit warning", "losses widen",
    "dividend cut", "suspends dividend", "layoffs", "job cuts",
    "sec investigation", "probe", "fraud", "accounting scandal",
    "class action", "settlement", "recalls", "bankruptcy filing",
    "chapter 11", "default", "downgrade to sell", "underweight",
    "price target cut", "capex cut", "inventory glut",
]

EN_STRONG_POSITIVE = [
    "beat", "raise guidance", "buyback", "fda approval",
    "record", "breakout", "surge",
]

EN_STRONG_NEGATIVE = [
    "bankruptcy", "investigation", "lawsuit", "crash",
    "guidance lowered", "layoff",
]

# ═══════════════════════════════════════════════════════════════
# 港股专用关键词（补充）
# ═══════════════════════════════════════════════════════════════

HK_SPECIFIC_POSITIVE = [
    "染蓝", "港股通纳入", "北水流入", "南向资金增持",
    "回购", "特别息", "分拆上市", "引入战投",
    "盈利预喜", "盈喜", "重估", "估值修复",
]

HK_SPECIFIC_NEGATIVE = [
    "剔出港股通", "北水流出", "配股", "供股",
    "合股", "盈利警告", "盈警", "停牌",
    "沽空报告", "做空", "大股东减持",
]

# ═══════════════════════════════════════════════════════════════
# 工具函数
# ═══════════════════════════════════════════════════════════════

def calc_text_sentiment(text: str, market: str = "cn") -> float:
    """
    计算文本的情感分数。

    Args:
        text: 待分析的文本
        market: 市场 (cn/hk/us)，决定使用哪套关键词

    Returns:
        float: -3 到 +3 的情感分数
    """
    text_lower = text.lower()

    if market == "us":
        pos_kw, neg_kw = EN_POSITIVE_KEYWORDS, EN_NEGATIVE_KEYWORDS
        strong_pos, strong_neg = EN_STRONG_POSITIVE, EN_STRONG_NEGATIVE
    elif market == "hk":
        pos_kw = CN_POSITIVE_KEYWORDS + HK_SPECIFIC_POSITIVE
        neg_kw = CN_NEGATIVE_KEYWORDS + HK_SPECIFIC_NEGATIVE
        strong_pos = CN_STRONG_POSITIVE
        strong_neg = CN_STRONG_NEGATIVE
    else:
        pos_kw = CN_POSITIVE_KEYWORDS
        neg_kw = CN_NEGATIVE_KEYWORDS
        strong_pos = CN_STRONG_POSITIVE
        strong_neg = CN_STRONG_NEGATIVE

    score = 0.0

    for kw in strong_pos:
        if kw in text_lower:
            score += 1.0
    for kw in pos_kw:
        if kw in text_lower:
            score += 0.5
    for kw in strong_neg:
        if kw in text_lower:
            score -= 1.0
    for kw in neg_kw:
        if kw in text_lower:
            score -= 0.5

    return max(-3.0, min(3.0, score))


def classify_sentiment(score: float) -> str:
    """
    将情感分数分类。

    Args:
        score: -3 到 +3 的情感分数

    Returns:
        "positive" | "neutral" | "negative"
    """
    if score > 0.5:
        return "positive"
    elif score < -0.5:
        return "negative"
    return "neutral"
