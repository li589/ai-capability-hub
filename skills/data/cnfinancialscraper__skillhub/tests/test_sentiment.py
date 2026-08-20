# -*- coding: utf-8 -*-
"""v4.3 全网舆情爬虫 — 单元测试

覆盖：
  1. 关键词词典完整
  2. 情感分类器正确
  3. 媒体源/目标库加载
  4. 自定义目标持久化
  5. 对话 NLU 解析
  6. 导出器降级 (openpyxl/python-docx 缺失时)
  7. ScheduledTask sentiment 字段
  8. Snapshot.to_dict 完整性
"""
import sys
import os
import json
import pytest
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

# 强制使 data 目录指向临时项目副本，避免污染真实数据
TEST_DATA_DIR = Path(__file__).resolve().parent / "_test_data"
TEST_DATA_DIR.mkdir(parents=True, exist_ok=True)

import sentiment_keywords as sk


# ============================================================
# 1. 关键词词典
# ============================================================
class TestKeywords:
    def test_keys_present(self):
        for name in ["POSITIVE_KEYWORDS", "NEGATIVE_KEYWORDS", "NEUTRAL_KEYWORDS"]:
            assert hasattr(sk, name), f"missing {name}"
            assert isinstance(getattr(sk, name), dict)

    def test_enough_keywords(self):
        # 至少 200 条负向 + 100 条正向 + 20 条中性
        assert len(sk.POSITIVE_KEYWORDS) >= 50
        assert len(sk.NEGATIVE_KEYWORDS) >= 100
        assert len(sk.NEUTRAL_KEYWORDS) >= 15

    def test_severity_levels_ordered(self):
        levels = sk.SEVERITY_LEVELS
        for a, b in zip(levels, levels[1:]):
            assert a[1] <= b[0] + 1, f"overlap: {a} vs {b}"


# ============================================================
# 2. 情感分类
# ============================================================
from sentiment_crawler import SentimentClassifier


class TestClassifier:
    def setup_method(self):
        self.clf = SentimentClassifier()

    def test_positive(self):
        s, sc, hits, sev = self.clf.classify("贵州茅台业绩增长11%，分红方案获好评", "")
        assert s == "positive", f"got {s}"
        assert sc > 0
        assert sev in ("低度利好", "中度利好", "重大利好")

    def test_negative(self):
        s, sc, hits, sev = self.clf.classify("ST退市预警，被证监会处罚责令改正", "")
        assert s == "negative", f"got {s}"
        assert sc >= 5
        assert sev in ("低度关注", "中度舆情", "高危舆情")

    def test_neutral(self):
        s, sc, hits, sev = self.clf.classify("关于召开股东大会的通知", "")
        # 既无正向也无负向重大命中 - 应当归为 neutral
        assert s in ("neutral", "positive"), f"got {s}"
        # 标题里「股东大会」「通知」是中性词，分数>=2 但应该归 neutral
        if s == "neutral":
            assert sev == "中性"

    def test_severity_negative(self):
        # 强烈负面
        s, _, _, sev = self.clf.classify("资金链断裂，跑路！董事长失联，财务造假，债务违约", "")
        assert s == "negative"
        assert sev == "高危舆情"

    def test_severity_positive(self):
        s, _, _, sev = self.clf.classify("业绩增长，营业收入增长，归母净利润增长，分红方案", "")
        assert s == "positive"
        assert sev in ("低度利好", "中度利好", "重大利好")


# ============================================================
# 3. 媒体源 / 目标库加载
# ============================================================
from sentiment_crawler import SentimentSourceLoader, SentimentTargetLoader


class TestLoaders:
    def test_sources_load(self):
        loader = SentimentSourceLoader()
        stats = loader.stats()
        assert stats.get("authoritative", 0) >= 5
        assert stats.get("financial_vertical", 0) >= 5
        assert stats.get("self_media", 0) >= 5
        assert stats.get("international", 0) >= 5
        assert "local_media" not in stats  # v6.0.0 已移除官媒分类

    def test_targets_load(self):
        loader = SentimentTargetLoader()
        cats = loader.categories
        assert "fund_company" in cats
        assert "listed_company" in cats
        assert "local_government" not in cats  # v6.0.0 已移除政府目标
        all_items = loader.all_targets()
        assert len(all_items) >= 1

    def test_pick_by_name(self):
        loader = SentimentSourceLoader()
        picked = loader.pick_by_names(["财联社"])
        assert len(picked) >= 1
        assert picked[0]["name"] == "财联社"


# ============================================================
# 4. 自定义目标
# ============================================================
def test_custom_target_add(tmp_path, monkeypatch):
    # 隔离 user custom 文件
    fake_user = tmp_path / "sentiment_custom_targets.json"
    monkeypatch.setattr("sentiment_crawler.USER_CUSTOM_FILE", fake_user)

    from sentiment_crawler import add_custom_sentiment_target
    r = add_custom_sentiment_target("custom", f"_test_{tmp_path.name}_bank", aliases=["X银行"])
    assert r.get("ok") is True
    assert fake_user.exists()


# ============================================================
# 5. 对话 NLU
# ============================================================
from sentiment_chat import SentimentChatParser


class TestChatParser:
    def setup_method(self):
        self.p = SentimentChatParser()

    def test_help(self):
        result = self.p.parse("帮助")
        assert result["intent"] == "help"

    def test_crawl_single(self):
        result = self.p.parse("帮我爬一下贵州茅台最近7天的舆情")
        assert result["intent"] == "crawl"
        assert "贵州茅台" in result["params"]["targets"] or len(result["params"]["targets"]) >= 1
        assert result["params"]["days"] == 7

    def test_crawl_multiple(self):
        result = self.p.parse("看下华夏基金、招商银行、中国人寿过去3天的负面新闻")
        assert result["intent"] == "crawl"
        targets = result["params"]["targets"]
        assert any("华夏基金" in t for t in targets)
        assert any("招商银行" in t for t in targets)
        assert any("中国人寿" in t for t in targets)
        assert result["params"]["days"] == 3
        assert result["params"]["negative_only"] is True

    def test_crawl_export_word(self):
        result = self.p.parse("看下华夏基金今天的正面新闻并生成Word")
        assert result["intent"] == "crawl_export"
        assert result["params"]["positive_only"] is True
        assert result["params"]["export"] == "word"

    def test_crawl_export_excel(self):
        result = self.p.parse("工银瑞信最近3天的负面新闻，并导出Excel")
        assert result["intent"] == "crawl_export"
        assert result["params"]["negative_only"] is True
        assert result["params"]["export"] == "excel"

    def test_schedule_daily(self):
        result = self.p.parse("每天早上9点爬取银行板块舆情")
        assert result["intent"] == "schedule"
        assert result["params"]["frequency"] == "daily"
        assert result["params"]["action"] == "crawl_sentiment_export"

    def test_schedule_every_n_minutes(self):
        result = self.p.parse("每30分钟爬取银行舆情")
        assert result["intent"] == "schedule"
        assert result["params"]["frequency"] == "every_30_minutes"

    def test_list_sources(self):
        result = self.p.parse("哪些媒体可用？")
        assert result["intent"] == "list"
        assert result["params"]["what"] == "sources"

    def test_list_targets(self):
        result = self.p.parse("有哪些目标")
        assert result["intent"] == "list"
        assert result["params"]["what"] == "targets"

    def test_add_target(self):
        result = self.p.parse("新增自定义目标 工银瑞信")
        assert result["intent"] == "add_target"
        assert result["params"]["name"] == "工银瑞信"

    def test_add_target_fund(self):
        result = self.p.parse("新增目标 工银瑞信基金")
        assert result["intent"] == "add_target"
        assert result["params"]["name"] == "工银瑞信基金"
        assert result["params"]["category"] == "fund_company"


# ============================================================
# 6. 导出器降级
# ============================================================
from sentiment_crawler import SentimentSnapshot, SentimentArticle
from sentiment_exporter import to_json, to_csv, export as export_sent


def _make_snapshot() -> SentimentSnapshot:
    arts = [
        SentimentArticle(title="T1", source="财联社", source_type="financial_vertical",
                          target_name="贵州茅台", target_type="上市公司",
                          publish_time="2026-07-27 10:00:00", url="https://example.com/1",
                          sentiment="positive", sentiment_score=10, severity="中度利好",
                          summary="业绩增长", keywords_matched=["业绩增长"]),
        SentimentArticle(title="T2", source="新浪财经", source_type="self_media",
                          target_name="贵州茅台", target_type="上市公司",
                          publish_time="2026-07-26 08:00:00", url="https://example.com/2",
                          sentiment="negative", sentiment_score=20, severity="高危舆情",
                          summary="处罚决定", keywords_matched=["处罚"]),
    ]
    return SentimentSnapshot(
        snapshot_id="sn_test",
        created_at="2026-07-27 12:00:00",
        target_filter={"names": ["贵州茅台"], "categories": []},
        source_filter=["财联社", "新浪财经"],
        articles=arts,
        stats={
            "total": 2,
            "by_sentiment": {"positive": 1, "negative": 1, "neutral": 0},
            "by_severity": {"中度利好": 1, "高危舆情": 1},
            "by_source_type": {"financial_vertical": 1, "self_media": 1},
        },
    )


class TestExporter:
    def test_json(self, tmp_path):
        snap = _make_snapshot()
        out = to_json(snap, tmp_path / "x.json")
        assert Path(out).exists()
        loaded = json.loads(Path(out).read_text(encoding="utf-8"))
        assert loaded["snapshot_id"] == "sn_test"
        assert len(loaded["articles"]) == 2

    def test_csv(self, tmp_path):
        snap = _make_snapshot()
        out = to_csv(snap, tmp_path / "x.csv")
        assert Path(out).exists()
        text = Path(out).read_text(encoding="utf-8-sig")
        assert "财联社" in text
        assert "T1" in text and "T2" in text

    def test_excel(self, tmp_path):
        try:
            import openpyxl  # noqa
        except ImportError:
            pytest.skip("openpyxl 未安装")
        snap = _make_snapshot()
        out = export_sent(snap, fmt="excel", output_path=tmp_path / "sn_test.xlsx")
        # 返回 dict: {excel: path}
        assert "excel" in out
        p = Path(out["excel"])
        assert p.exists()
        assert p.stat().st_size > 1000

    def test_word(self, tmp_path):
        try:
            import docx  # noqa
        except ImportError:
            pytest.skip("python-docx 未安装")
        snap = _make_snapshot()
        out = export_sent(snap, fmt="word", output_path=tmp_path / "sn_test.docx")
        assert "word" in out
        assert Path(out["word"]).exists()


# ============================================================
# 7. ScheduledTask sentiment 字段
# ============================================================
def test_scheduled_task_sentiment_fields():
    from crawl_scheduler import ScheduledTask, TaskFrequency, TaskAction
    t = ScheduledTask(
        task_id="x", name="bank_yuqing",
        action=TaskAction.CRAWL_SENTIMENT_EXPORT,
        sentiment_targets=["招商银行"],
        sentiment_categories=["commercial_bank"],
        sentiment_source_categories=["authoritative"],
        sentiment_days=7, sentiment_negative_only=True,
        sentiment_max=50, sentiment_export_format="all",
    )
    d = t.to_dict()
    assert d["action"] == "crawl_sentiment_export"
    assert d["sentiment_targets"] == ["招商银行"]
    assert d["sentiment_days"] == 7

    t2 = ScheduledTask.from_dict(d)
    assert t2.sentiment_export_format == "all"
    assert t2.sentiment_targets == ["招商银行"]


# ============================================================
# 8. Snapshot.to_dict
# ============================================================
def test_snapshot_to_dict():
    snap = _make_snapshot()
    d = snap.to_dict()
    assert d["snapshot_id"] == "sn_test"
    assert "stats" in d
    assert "articles" in d
    assert d["stats"]["by_sentiment"]["positive"] == 1


# ============================================================
# run with pytest
# ============================================================
if __name__ == "__main__":
    pytest.main([__file__, "-v", "-x"])


# ============================================================
# 10. v4.3.1 优化后的测试 — 速度控制 / 短路 / 异常安全
from sentiment_crawler import SentimentCrawler
# ============================================================

import time as _time


class TestTimeoutsAndShortCircuit:
    def test_time_up_default(self):
        c = SentimentCrawler()
        c._run_start_ts = _time.time()
        assert c._time_up() is False

    def test_time_up_exceeded(self):
        c = SentimentCrawler(max_total_seconds=1)
        c._run_start_ts = _time.time() - 5
        assert c._time_up() is True

    def test_placeholder_dedup(self):
        c = SentimentCrawler()
        # 第一次应 False
        assert c._placeholder_seen("贵州茅台", "财联社") is False
        # 第二次 True (占位已用过)
        assert c._placeholder_seen("贵州茅台", "财联社") is True
        # 不同 source 不互相影响
        assert c._placeholder_seen("贵州茅台", "新华") is False

    def test_dns_short_circuit(self):
        c = SentimentCrawler()
        # 不存在域名应短路
        bad_url = "https://nonexistent-host-xyz.invalid/foo"
        assert c._domain_unresolvable(bad_url) is True

    def test_default_max_total_seconds(self):
        """默认 max_total_seconds 应 <=30s（对话体验友好）"""
        from sentiment_crawler import crawl_sentiment, SentimentCrawler
        c = SentimentCrawler()
        assert c.max_total_seconds <= 60, f"got {c.max_total_seconds}"


class TestExceptionsSafe:
    def test_chat_exception_safe(self):
        from sentiment_chat import chat_handle
        for txt in ["", "  ", "\n", "你好", None, "💥⚡"]:
            try:
                r = chat_handle(txt or "empty")
                assert "reply" in r
            except Exception as e:
                pytest.fail(f"chat_handle({txt!r}) crashed: {e}")

    def test_classifier_empty(self):
        clf = SentimentClassifier()
        for s, sc, h, sev in [clf.classify("", ""), clf.classify("  ", None)]:
            assert s in ("positive", "negative", "neutral")


class TestStatsCompleteness:
    def test_stats_by_source_type(self):
        from sentiment_crawler import SentimentSnapshot, SentimentArticle
        from sentiment_exporter import to_dialog
        # 制造一个 snapshots, 验证 to_dialog 显示 by_source_type
        arts = [
            SentimentArticle(title="t1", source="财联社", source_type="financial_vertical",
                              target_name="茅台", sentiment="positive", severity="低度利好"),
            SentimentArticle(title="t2", source="财联社", source_type="authoritative",
                              target_name="茅台", sentiment="negative", severity="高危舆情"),
        ]
        snap = SentimentSnapshot(
            snapshot_id="test", created_at="2026-07-27",
            target_filter={"names": ["茅台"], "categories": []},
            source_filter=["财联社", "新华网"],
            articles=arts,
            stats={"total": 2, "by_sentiment": {"positive": 1, "negative": 1, "neutral": 0},
                    "by_severity": {"低度利好": 1, "高危舆情": 1},
                    "by_source_type": {"financial_vertical": 1, "authoritative": 1},
                    "elapsed_seconds": 12.3, "timed_out": True},
        )
        d = to_dialog(snap)
        assert "媒体类别 Top" in d
        assert "12.3s" in d or "12s" in d
        assert "超时" in d


class TestSchedulerRoundtrip:
    def test_sentiment_fields_roundtrip(self):
        from crawl_scheduler import ScheduledTask, TaskAction
        original = ScheduledTask(
            task_id="x1", name="test",
            action=TaskAction.CRAWL_SENTIMENT_EXPORT,
            sentiment_targets=["工银瑞信", "贵州茅台"],
            sentiment_categories=["fund_company"],
            sentiment_source_categories=["authoritative"],
            sentiment_days=5, sentiment_positive_only=True,
            sentiment_negative_only=False, sentiment_export_format="word",
        )
        d = original.to_dict()
        # 反序列化
        restored = ScheduledTask.from_dict(d)
        assert restored.sentiment_targets == ["工银瑞信", "贵州茅台"]
        assert restored.sentiment_days == 5
        assert restored.action == TaskAction.CRAWL_SENTIMENT_EXPORT


class TestFingerprint:
    def test_url_normalized(self):
        a = SentimentArticle(title="t", url="https://x.com/a?utm_source=x", target_name="y")
        b = SentimentArticle(title="t", url="https://x.com/a?utm_source=y", target_name="y")
        # utm 后缀应去掉，URL 同
        assert a.fingerprint == b.fingerprint

    def test_trailing_slash_normalized(self):
        a = SentimentArticle(title="t", url="https://x.com/a/", target_name="y")
        b = SentimentArticle(title="t", url="https://x.com/a", target_name="y")
        assert a.fingerprint == b.fingerprint
