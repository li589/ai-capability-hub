"""scripts.main 结果展示与版本回归测试（v2.5.0）

覆盖：
- _display_v2_results 遇到分析器错误桩（details={"error": ...}）不再 KeyError 崩溃
- 版本号单一来源：main/cmd_version/report 与 core.version 一致
"""

import io
import sys
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import scripts.main as main_mod
from core.result import AnalysisResult
from core.version import __version__


class _FakeDM:
    def save_analysis(self, results):
        return "fake-chat-id"


class _FakeCM:
    def extract_events_from_messages(self, messages, chat_id):
        return []


class TestDisplayV2Robustness(unittest.TestCase):
    """_display_v2_results 对错误桩的容错（v2.5.0 bugfix）"""

    def test_mbti_error_stub_no_crash(self):
        """MBTI 分析器失败（error 桩）时不应 KeyError 崩溃"""
        results = {
            "mbti": AnalysisResult(
                analyzer_name="mbti", score=0.0, confidence=0.0,
                details={"error": "boom"}, metadata={"status": "failed"},
            ),
            "sentiment": AnalysisResult(
                analyzer_name="sentiment", score=60.0, confidence=60.0,
                details={"positive": 60.0, "negative": 20.0, "neutral": 20.0,
                         "trend": "stable", "timeline": [], "irony_count": 0,
                         "emotional_words": {"positive": [], "negative": []}},
            ),
        }
        buf = io.StringIO()
        with redirect_stdout(buf):
            main_mod._display_v2_results(
                results, messages=[], cm=_FakeCM(), raw_messages=[],
                dm=_FakeDM(), config={},
            )
        out = buf.getvalue()
        self.assertIn("分析失败", out)
        self.assertIn("boom", out)

    def test_normal_results_display(self):
        """正常 MBTI 结果仍完整展示"""
        results = {
            "mbti": AnalysisResult(
                analyzer_name="mbti", score=70.0, confidence=78.5,
                details={"type": "ENFP", "name": "竞选者", "dim_description": "外向|直觉|情感|感知",
                         "stability": 0.82},
            ),
        }
        buf = io.StringIO()
        with redirect_stdout(buf):
            main_mod._display_v2_results(
                results, messages=[], cm=_FakeCM(), raw_messages=[],
                dm=_FakeDM(), config={},
            )
        out = buf.getvalue()
        self.assertIn("ENFP", out)
        self.assertIn("竞选者", out)
        self.assertNotIn("分析失败", out)

    def test_predict_v2_error_stub_scenario(self):
        """predict-v2 中 scenario 分析器失败时场景回退 social"""
        results = {
            "scenario": AnalysisResult(
                analyzer_name="scenario", score=0.0, confidence=0.0,
                details={"error": "boom"}, metadata={"status": "failed"},
            ),
        }
        scenario = results["scenario"].details.get("primary", "social")
        self.assertEqual(scenario, "social")


class TestVersionSingleSource(unittest.TestCase):
    """版本号单一来源（v2.5.0）"""

    def test_main_version_matches_core(self):
        self.assertEqual(main_mod.__version__, __version__)

    def test_config_version_matches_core(self):
        import json
        config_path = Path(__file__).resolve().parent.parent.parent / "config.json"
        config = json.loads(config_path.read_text(encoding="utf-8"))
        self.assertEqual(config["version"], __version__)

    def test_cmd_version_output(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            main_mod.cmd_version(mock.MagicMock())
        self.assertIn(f"v{__version__}", buf.getvalue())


if __name__ == "__main__":
    unittest.main()
