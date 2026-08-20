"""predictors.ensemble 单元测试"""

import sys
import unittest
from pathlib import Path
from typing import List

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from core.message import Message
from core.predictor_base import PredictorBase, PredictionContext
from core.result import PredictionResult, Prediction
from predictors.ensemble import EnsemblePredictor


class MockPredictor(PredictorBase):
    """用于测试的 Mock 预测器"""
    def __init__(self, name="mock", predictions=None, available=True, weight=1.0):
        super().__init__()
        self.name = name
        self._predictions = predictions or []
        self._available = available
        self.weight = weight

    def is_available(self) -> bool:
        return self._available

    def predict(self, context: PredictionContext) -> PredictionResult:
        if not self._predictions:
            return PredictionResult(
                top_prediction=Prediction(text="默认", confidence=0.3, strategy=self.name),
            )
        top = self._predictions[0]
        alts = [Prediction(text=p["text"], confidence=p.get("confidence", 0.5),
                          strategy=p.get("strategy", self.name))
                for p in self._predictions[1:]]
        return PredictionResult(
            top_prediction=Prediction(text=top["text"], confidence=top.get("confidence", 0.7),
                                     strategy=top.get("strategy", self.name)),
            alternatives=alts,
            scenario=context.scenario,
        )


class TestEnsemblePredictor(unittest.TestCase):
    """EnsemblePredictor 测试"""

    def setUp(self):
        self.ensemble = EnsemblePredictor()

    def test_add_predictor(self):
        p = MockPredictor(name="p1")
        self.ensemble.add_predictor(p)
        self.assertIn("p1", self.ensemble.list_predictors())

    def test_remove_predictor(self):
        p = MockPredictor(name="p1")
        self.ensemble.add_predictor(p)
        self.ensemble.remove_predictor("p1")
        self.assertNotIn("p1", self.ensemble.list_predictors())

    def test_add_invalid_type(self):
        with self.assertRaises(TypeError):
            self.ensemble.add_predictor("not a predictor")

    def test_is_available_with_no_predictors(self):
        self.assertFalse(self.ensemble.is_available())

    def test_is_available_with_one_available(self):
        self.ensemble.add_predictor(MockPredictor(name="p1", available=True))
        self.assertTrue(self.ensemble.is_available())

    def test_predict_basic(self):
        self.ensemble.add_predictor(MockPredictor(
            name="p1",
            predictions=[{"text": "预测1", "confidence": 0.8}],
        ))
        ctx = PredictionContext(messages=[], scenario="social")
        result = self.ensemble.predict(ctx)
        self.assertIsNotNone(result.top_prediction)

    def test_predict_merges_same_text(self):
        """相同文本应被合并"""
        self.ensemble.add_predictor(MockPredictor(
            name="p1",
            predictions=[{"text": "好的", "confidence": 0.7, "strategy": "rule"}],
        ))
        self.ensemble.add_predictor(MockPredictor(
            name="p2",
            predictions=[{"text": "好的", "confidence": 0.6, "strategy": "rag"}],
        ))
        ctx = PredictionContext(messages=[], scenario="social")
        result = self.ensemble.predict(ctx)
        # 合并后 top 应该是 "好的"，且 strategy 包含两种
        self.assertEqual(result.top_prediction.text, "好的")
        self.assertIn("rule", result.top_prediction.strategy)
        self.assertIn("rag", result.top_prediction.strategy)

    def test_predict_with_unavailable_predictor(self):
        """不可用的预测器被跳过"""
        self.ensemble.add_predictor(MockPredictor(name="p1", available=False))
        self.ensemble.add_predictor(MockPredictor(
            name="p2", available=True,
            predictions=[{"text": "test", "confidence": 0.5}],
        ))
        ctx = PredictionContext(messages=[], scenario="social")
        result = self.ensemble.predict(ctx)
        self.assertEqual(result.top_prediction.text, "test")

    def test_no_predictors_fallback(self):
        ctx = PredictionContext(messages=[], scenario="social")
        result = self.ensemble.predict(ctx)
        # 应该有 fallback
        self.assertIsNotNone(result.top_prediction)
        self.assertIn("fallback", result.top_prediction.strategy)

    def test_update_accuracy(self):
        self.ensemble.add_predictor(MockPredictor(name="p1"))
        self.ensemble.update_accuracy("p1", 0.9)
        # 应不影响 list
        self.assertIn("p1", self.ensemble.list_predictors())


if __name__ == "__main__":
    unittest.main()
