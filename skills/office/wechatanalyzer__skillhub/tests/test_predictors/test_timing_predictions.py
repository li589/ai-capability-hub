"""时间感知对话预测测试（v2.3.0）"""

import sys
import unittest
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from core.message import Message
from core.predictor_base import PredictionContext
from predictors.ensemble import EnsemblePredictor
from predictors.rule_predictor import RulePredictor


def _msg(sender: str, content: str, minutes_ago: int = 0) -> Message:
    return Message(
        sender=sender,
        content=content,
        timestamp=datetime.now() - timedelta(minutes=minutes_ago),
    )


class TestRuleTimingPredictions(unittest.TestCase):
    def setUp(self):
        self.predictor = RulePredictor()

    def test_stale_context_returns_reconnect_candidates(self):
        ctx = PredictionContext(
            messages=[_msg("other", "上次聊到一半", minutes_ago=24 * 60 * 3)],
            scenario="social",
        )
        result = self.predictor.predict(ctx)
        self.assertEqual(result.context["timing"]["urgency"], "stale")
        all_texts = [result.top_prediction.text] + [a.text for a in result.alternatives]
        has_reconnect = any(
            kw in text for text in all_texts for kw in ("好久", "最近", "刚看到")
        )
        self.assertTrue(has_reconnect, f"stale 场景未生成找回联系候选: {all_texts}")

    def test_immediate_context_returns_short_reply(self):
        ctx = PredictionContext(
            messages=[_msg("other", "在吗？", minutes_ago=1)],
            scenario="social",
        )
        result = self.predictor.predict(ctx)
        self.assertEqual(result.context["timing"]["urgency"], "immediate")
        self.assertEqual(result.metadata["timing"]["urgency"], "immediate")
        self.assertIn("在的，你说", result.metadata["time_based_candidates"])


class TestEnsembleTiming(unittest.TestCase):
    def test_timing_propagated_to_context(self):
        ensemble = EnsemblePredictor()
        ensemble.add_predictor(RulePredictor())
        ctx = PredictionContext(
            messages=[_msg("other", "你好", minutes_ago=24 * 60 * 2)],
            scenario="social",
        )
        result = ensemble.predict(ctx)
        self.assertEqual(result.context["timing"]["urgency"], "stale")
        self.assertIn("timing", result.metadata["context_features"])


if __name__ == "__main__":
    unittest.main()
