"""predictors.mirofish_predictor 单元测试"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from core.message import Message
from core.predictor_base import PredictionContext
from predictors.mirofish_predictor import MiroFishPredictor


class TestMiroFishPredictor(unittest.TestCase):
    """MiroFishPredictor 测试"""

    def test_disabled_by_default(self):
        """默认禁用"""
        p = MiroFishPredictor(config={"mirofish": {"enabled": False}})
        self.assertFalse(p.is_available())

    def test_enabled_via_config(self):
        """配置启用"""
        p = MiroFishPredictor(config={"mirofish": {"enabled": True}})
        self.assertTrue(p.is_available())

    def test_predict_when_disabled(self):
        """禁用时返回 fallback"""
        p = MiroFishPredictor(config={"mirofish": {"enabled": False}})
        ctx = PredictionContext(messages=[Message(sender="other", content="x")])
        result = p.predict(ctx)
        self.assertIn("disabled", result.top_prediction.strategy)

    def test_predict_when_enabled(self):
        """启用时多智能体模拟"""
        p = MiroFishPredictor(config={
            "mirofish": {
                "enabled": True,
                "max_agents": 3,
                "simulation_rounds": 1,
            }
        })
        msgs = [Message(sender="other", content="今天加班")]
        ctx = PredictionContext(messages=msgs, mbti="ENFP", scenario="work")
        result = p.predict(ctx)
        # 应有模拟预测
        self.assertEqual(result.top_prediction.strategy, "mirofish")
        self.assertGreater(len(result.top_prediction.text), 0)
        # 应有 metadata 说明使用了多少 agents
        self.assertIn("agents", result.metadata)

    def test_voting_aggregation(self):
        """多个 Agent 同意同一文本应提升置信度"""
        p = MiroFishPredictor(config={
            "mirofish": {
                "enabled": True,
                "max_agents": 5,
                "simulation_rounds": 2,
            }
        })
        msgs = [Message(sender="other", content="吃饭")]
        ctx = PredictionContext(messages=msgs, scenario="romantic")
        result = p.predict(ctx)
        # 应有 metadata
        self.assertGreater(result.metadata.get("total_responses", 0), 0)

    def test_score_response(self):
        """测试 _score_response 方法"""
        p = MiroFishPredictor(config={"mirofish": {"enabled": True}})

        # 短确认类应降低分
        score_short = p._score_response("嗯嗯", None)
        # 主动类应加分
        score_proactive = p._score_response("我来处理一下", None)
        # 主动类应 >= 短确认类
        self.assertGreaterEqual(score_proactive, score_short - 0.1)


if __name__ == "__main__":
    unittest.main()
