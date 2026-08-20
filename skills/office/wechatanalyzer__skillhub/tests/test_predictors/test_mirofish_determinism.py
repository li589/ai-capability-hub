"""MiroFish 预测器确定性回归测试（v2.5.0）

修复：_simulate_response 曾用全局 random.choice，每次运行结果不同
（测试/报告 flaky）。现改为独立 seeded 随机源：
- 相同配置（默认 seed=0）多次运行结果一致
- 不同 seed 可给出不同（但各自可复现）的结果
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from core.message import Message
from core.predictor_base import PredictionContext
from predictors.mirofish_predictor import MiroFishPredictor


def _run_predict(seed=None):
    cfg = {
        "mirofish": {
            "enabled": True,
            "max_agents": 8,
            "simulation_rounds": 2,
        }
    }
    if seed is not None:
        cfg["mirofish"]["seed"] = seed
    p = MiroFishPredictor(config=cfg)
    msgs = [Message(sender="other", content="今天加班到很晚")]
    ctx = PredictionContext(messages=msgs, mbti="ENFP", scenario="work")
    result = p.predict(ctx)
    texts = [result.top_prediction.text]
    texts += [a.text for a in result.alternatives]
    return texts, result.metadata


class TestMiroFishDeterminism(unittest.TestCase):
    """v2.5.0：seeded 随机源 → 结果可复现"""

    def test_default_seed_reproducible(self):
        """默认配置（seed=0）两次运行结果一致"""
        t1, _ = _run_predict()
        t2, _ = _run_predict()
        self.assertEqual(t1, t2, "默认种子下两次预测应一致")

    def test_explicit_seed_reproducible(self):
        """显式 seed 同样可复现"""
        t1, _ = _run_predict(seed=42)
        t2, _ = _run_predict(seed=42)
        self.assertEqual(t1, t2)

    def test_different_seeds_may_differ(self):
        """不同种子是不同随机序列（允许不同，但各自可复现）"""
        t1, _ = _run_predict(seed=1)
        t3, _ = _run_predict(seed=1)
        self.assertEqual(t1, t3)
        # 不同种子的两个确定性序列不应强制相等——这里只验证类型完整
        t2, _ = _run_predict(seed=2)
        self.assertTrue(all(isinstance(t, str) and t for t in t2))


if __name__ == "__main__":
    unittest.main()
