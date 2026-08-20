# -*- coding: utf-8 -*-
"""v5.0.0 模块D：舆情分类器增强测试（否定词/相对时间/严重度统一/模糊去重）"""

import pytest

from scripts.sentiment_crawler import (
    SentimentClassifier, SentimentCrawler, SentimentArticle,
    _norm_time, _norm_relative_time,
    _SEEN_INDEX, _TITLE_INDEX,
)
from scripts.sentiment_keywords import SEVERITY_LEVELS, SEVERITY_LEVELS_POSITIVE


# ============================================================
# 1. 否定词处理
# ============================================================

def test_negation_flips_negative():
    """「否认业绩下滑」不应判负面"""
    c = SentimentClassifier()
    sentiment, score, _, severity = c.classify("公司否认业绩下滑传闻")
    assert sentiment != "negative"


def test_negation_keeps_positive_after_negation():
    """「否认业绩增长」应判中性（被否定）"""
    c = SentimentClassifier()
    sentiment, _, _, _ = c.classify("公司否认业绩增长")
    assert sentiment == "neutral"


def test_no_negation_still_detects_negative():
    c = SentimentClassifier()
    assert c.classify("公司业绩下滑严重")[0] == "negative"


def test_negation_in_content_not_title():
    """否定词在正文而非标题时同样生效"""
    c = SentimentClassifier()
    sentiment, _, _, _ = c.classify("公司回应", "市场传言公司业绩下滑，但公司否认该说法")
    assert sentiment != "negative"


# ============================================================
# 2. 相对时间解析
# ============================================================

def test_relative_hours_ago():
    from datetime import datetime, timedelta
    out = _norm_time("3小时前")
    expect = (datetime.now() - timedelta(hours=3)).strftime("%Y-%m-%d %H:%M:%S")
    assert out == expect


def test_relative_yesterday():
    from datetime import datetime, timedelta
    out = _norm_relative_time("昨天")
    expect = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S")
    assert out == expect


def test_relative_day_before():
    from datetime import datetime, timedelta
    out = _norm_time("前天")
    expect = (datetime.now() - timedelta(days=2)).strftime("%Y-%m-%d %H:%M:%S")
    assert out == expect


def test_relative_minutes():
    from datetime import datetime, timedelta
    out = _norm_time("30分钟前")
    expect = (datetime.now() - timedelta(minutes=30)).strftime("%Y-%m-%d %H:%M:%S")
    assert out == expect


def test_absolute_time_unchanged():
    """绝对时间不受相对时间正则影响"""
    assert _norm_time("2026-07-27") == "2026-07-27 00:00:00"
    assert _norm_time("2026-07-27 09:42") == "2026-07-27 09:42:00"


def test_relative_not_matched_for_plain_text():
    assert _norm_relative_time("没有任何相对时间") == ""


# ============================================================
# 3. 严重度阈值统一
# ============================================================

def test_severity_tables_defined():
    assert len(SEVERITY_LEVELS) >= 4
    assert len(SEVERITY_LEVELS_POSITIVE) >= 4


def test_severity_uses_unified_tables():
    """_severity 应从表取档，与 sentiment_keywords 一致"""
    c = SentimentClassifier()
    # 负面 10 分 → 查 SEVERITY_LEVELS：(4,9)低度 / (9,18)中度
    assert c._severity(10.0, "negative") == "中度舆情"
    # 负面 5 分 → 低度关注
    assert c._severity(5.0, "negative") == "低度关注"
    # 正面 20 分 → SEVERITY_LEVELS_POSITIVE 中度利好
    assert c._severity(20.0, "positive") == "中度利好"
    # 正面 40 分 → 重大利好
    assert c._severity(40.0, "positive") == "重大利好"
    # 中性恒为中性
    assert c._severity(99.0, "neutral") == "中性"


def test_severity_consistency_with_table():
    """从表推导与函数一致（防止再出现两套阈值）"""
    c = SentimentClassifier()
    for lo, hi, label in SEVERITY_LEVELS:
        assert c._severity((lo + hi) / 2.0, "negative") == label
    for lo, hi, label in SEVERITY_LEVELS_POSITIVE:
        assert c._severity((lo + hi) / 2.0, "positive") == label


# ============================================================
# 4. 模糊去重
# ============================================================

def _make_article(title, target="贵州茅台", url="https://x.com/a"):
    return SentimentArticle(title=title, target_name=target, url=url, publish_time="2026-08-01")


def test_fuzzy_dedup_detects_similar(monkeypatch):
    _TITLE_INDEX.clear()
    _SEEN_INDEX.clear()
    crawler = SentimentCrawler()
    # 先加入一条
    assert crawler._is_dup(_make_article("贵州茅台发布2026年半年度报告")) is False
    # 相似标题（加标点/日期差异）→ 模糊命中
    similar = _make_article("贵州茅台发布2026年半年度报告！", url="https://x.com/b")
    assert crawler._is_dup(similar) is True
    assert similar.dedup_ratio > 0.85


def test_fuzzy_dedup_allows_distinct_titles(monkeypatch):
    _TITLE_INDEX.clear()
    _SEEN_INDEX.clear()
    crawler = SentimentCrawler()
    assert crawler._is_dup(_make_article("茅台分红方案")) is False
    assert crawler._is_dup(_make_article("宁德时代业绩增长")) is False  # 不同 target 不误判


def test_fuzzy_dedup_per_target():
    """模糊索引按 target 隔离"""
    _TITLE_INDEX.clear()
    crawler = SentimentCrawler()
    crawler._is_dup(_make_article("利好新闻", target="公司A", url="https://x/1"))
    # 同标题不同 target → 不算重复
    assert crawler._is_dup(_make_article("利好新闻", target="公司B", url="https://x/2")) is False


def test_placeholder_not_deduped(monkeypatch):
    _SEEN_INDEX.clear()
    _TITLE_INDEX.clear()
    crawler = SentimentCrawler()
    p = SentimentArticle(title="[未能直接抓取] 某公司", target_name="某公司", url="https://x")
    assert crawler._is_dup(p) is False


# ============================================================
# 5. dedup_ratio 字段序列化
# ============================================================

def test_article_has_dedup_ratio_field():
    a = SentimentArticle(title="x", target_name="y")
    assert a.dedup_ratio == 0.0
    a.dedup_ratio = 0.9
    d = a.to_dict()
    assert d["dedup_ratio"] == 0.9
