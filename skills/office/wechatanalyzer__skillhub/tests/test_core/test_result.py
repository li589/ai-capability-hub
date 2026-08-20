"""core.result 单元测试"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from core.result import AnalysisResult, PredictionResult, Prediction


class TestAnalysisResult(unittest.TestCase):
    """AnalysisResult 测试"""

    def test_create_basic(self):
        result = AnalysisResult(
            analyzer_name="mbti",
            score=85.0,
            confidence=78.5,
            details={"type": "ENFP"},
        )
        self.assertEqual(result.analyzer_name, "mbti")
        self.assertEqual(result.score, 85.0)
        self.assertEqual(result.confidence, 78.5)
        self.assertEqual(result.details["type"], "ENFP")

    def test_default_metadata(self):
        result = AnalysisResult(analyzer_name="x")
        self.assertEqual(result.metadata, {})

    def test_to_dict_from_dict(self):
        original = AnalysisResult(
            analyzer_name="sentiment",
            score=65.0,
            confidence=90.0,
            details={"positive": 65.0, "negative": 35.0},
            metadata={"analyzer": "SentimentAnalyzer"},
        )
        d = original.to_dict()
        restored = AnalysisResult.from_dict(d)
        self.assertEqual(restored.analyzer_name, "sentiment")
        self.assertEqual(restored.score, 65.0)
        self.assertEqual(restored.confidence, 90.0)
        self.assertEqual(restored.details["positive"], 65.0)
        self.assertEqual(restored.metadata["analyzer"], "SentimentAnalyzer")


class TestPrediction(unittest.TestCase):
    """Prediction 测试"""

    def test_create(self):
        pred = Prediction(
            text="我知道了",
            confidence=0.75,
            strategy="rule",
            rationale="基于 MBTI 模板",
        )
        self.assertEqual(pred.text, "我知道了")
        self.assertEqual(pred.confidence, 0.75)
        self.assertEqual(pred.strategy, "rule")
        self.assertIn("MBTI", pred.rationale)

    def test_to_dict(self):
        pred = Prediction(text="x", confidence=0.5, strategy="default")
        d = pred.to_dict()
        self.assertEqual(d["text"], "x")
        self.assertEqual(d["confidence"], 0.5)


class TestPredictionResult(unittest.TestCase):
    """PredictionResult 测试"""

    def test_create(self):
        top = Prediction(text="好的", confidence=0.8, strategy="rule")
        alt = [Prediction(text="嗯嗯", confidence=0.5), Prediction(text="收到", confidence=0.4)]
        result = PredictionResult(
            top_prediction=top,
            alternatives=alt,
            scenario="work",
        )
        self.assertEqual(result.top_prediction.text, "好的")
        self.assertEqual(len(result.alternatives), 2)
        self.assertEqual(result.scenario, "work")

    def test_to_dict(self):
        top = Prediction(text="好的", confidence=0.8)
        result = PredictionResult(top_prediction=top, alternatives=[])
        d = result.to_dict()
        self.assertEqual(d["top_prediction"]["text"], "好的")
        self.assertEqual(d["alternatives"], [])

    def test_from_legacy(self):
        legacy = {
            "next_message": "我先确认一下",
            "alternatives": ["好的", "收到"],
            "based_on": "mbti_sentiment",
            "scenario": "work",
        }
        result = PredictionResult.from_legacy(legacy)
        self.assertEqual(result.top_prediction.text, "我先确认一下")
        self.assertEqual(len(result.alternatives), 2)
        self.assertEqual(result.top_prediction.strategy, "rule")
        self.assertIn("mbti_sentiment", result.top_prediction.rationale)


if __name__ == "__main__":
    unittest.main()
