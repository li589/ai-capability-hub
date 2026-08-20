"""scripts.v2_report_generator smoke test（v2.1.0）"""

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from scripts.v2_report_generator import V2ReportGenerator, generate_v2_summary


def _fake_results():
    """构造一份模拟分析结果（AnalysisResult.to_dict() 结构）"""
    return {
        "mbti": {
            "analyzer_name": "mbti", "score": 75.0, "confidence": 80.0,
            "details": {"type": "ENFP", "name": "竞选者",
                        "dim_description": "E: 外向 | N: 直觉",
                        "stability": 0.3},
            "metadata": {},
        },
        "bigfive": {
            "analyzer_name": "bigfive", "score": 55.0, "confidence": 60.0,
            "details": {
                "radar_data": [
                    {"label": "开放性", "value": 65.0},
                    {"label": "尽责性", "value": 50.0},
                    {"label": "外向性", "value": 70.0},
                    {"label": "宜人性", "value": 45.0},
                    {"label": "神经质", "value": 40.0},
                ],
            },
            "metadata": {},
        },
        "sentiment": {
            "analyzer_name": "sentiment", "score": 60.0, "confidence": 85.0,
            "details": {"positive": 55.0, "negative": 20.0, "neutral": 25.0,
                        "trend": "up",
                        "emotional_words": {"positive": ["开心", "谢谢"],
                                            "negative": ["难过"]},
                        "irony_count": 0},
            "metadata": {},
        },
        "risk": {
            "analyzer_name": "risk", "score": 0.0, "confidence": 80.0,
            "details": {"risks": {}, "overall_level": "low", "risk_score": 0.0},
            "metadata": {},
        },
        "scenario": {
            "analyzer_name": "scenario", "score": 3.0, "confidence": 65.0,
            "details": {"primary": "social",
                        "sorted": [{"scenario": "social", "weight": 3},
                                   {"scenario": "work", "weight": 1}]},
            "metadata": {},
        },
        "pattern": {
            "analyzer_name": "pattern", "score": 120.0, "confidence": 80.0,
            "details": {
                "initiation": {"self": 2, "other": 3,
                               "self_pct": 40.0, "other_pct": 60.0},
                "reply_speed": {"avg_seconds": 120.0, "count": 5,
                                "fast_replies": 3, "slow_replies": 1},
                "duration_days": 7,
            },
            "metadata": {},
        },
    }


class TestV2ReportGenerator(unittest.TestCase):
    """HTML 报告生成 smoke test"""

    def test_generate_creates_file_with_key_markers(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            out = str(Path(tmpdir) / "report.html")
            generator = V2ReportGenerator(config={})
            path = generator.generate(results=_fake_results(),
                                      meta={"total_messages": 42},
                                      output_path=out)
            self.assertTrue(Path(path).exists())
            content = Path(path).read_text(encoding="utf-8")

        # 关键标记：自包含（无外部资源）、中文界面、各分析区块、SVG 图表
        self.assertIn("<!DOCTYPE html>", content)
        self.assertIn("微信聊天分析报告", content)
        self.assertIn("ENFP", content)               # MBTI 卡片
        self.assertIn("大五人格", content)
        self.assertIn("<svg", content)               # 雷达图/环形图
        self.assertIn("情感分析", content)
        self.assertIn("对话模式", content)
        self.assertIn("风险预警", content)
        self.assertIn("对话场景", content)
        self.assertIn("一句话总结", content)
        self.assertIn("生成时间", content)
        # 完全自包含：禁止任何外部资源引用
        self.assertNotIn("http://", content.replace("http://localhost", ""))
        self.assertNotIn("https://", content)
        self.assertNotIn("cdn", content.lower())
        self.assertNotIn("<script src", content.lower())
        self.assertNotIn("link rel", content.lower())

    def test_generate_default_output_path(self):
        """不传 output_path 时生成到 data/reports/"""
        generator = V2ReportGenerator(config={})
        path = generator.generate(results=_fake_results())
        try:
            self.assertTrue(Path(path).exists())
            self.assertIn("reports", path)
        finally:
            Path(path).unlink(missing_ok=True)

    def test_empty_results_no_crash(self):
        """空结果也应生成合法 HTML"""
        with tempfile.TemporaryDirectory() as tmpdir:
            out = str(Path(tmpdir) / "empty.html")
            generator = V2ReportGenerator(config={})
            path = generator.generate(results={}, output_path=out)
            content = Path(path).read_text(encoding="utf-8")
        self.assertIn("<!DOCTYPE html>", content)


class TestGenerateV2Summary(unittest.TestCase):
    """一句话总结测试"""

    def test_summary_positive_low_risk(self):
        summary = generate_v2_summary(_fake_results())
        self.assertIn("积极", summary)
        self.assertIn("未发现风险信号", summary)
        # ENFP → 偏外向感性
        self.assertIn("偏外向", summary)

    def test_summary_high_risk(self):
        results = _fake_results()
        results["risk"]["details"]["overall_level"] = "high"
        summary = generate_v2_summary(results)
        self.assertIn("高风险", summary)

    def test_summary_empty(self):
        summary = generate_v2_summary({})
        self.assertIsInstance(summary, str)
        self.assertTrue(len(summary) > 0)


if __name__ == "__main__":
    unittest.main()
