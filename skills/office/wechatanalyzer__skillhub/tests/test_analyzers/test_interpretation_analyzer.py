"""analyzers.interpretation_analyzer 单元测试（v2.2.0 新增，v2.3.0 补全）

覆盖 4 大解读能力：
- 意图识别（询问/表白/感谢/请求/拒绝…）
- 实体识别 NER Lite（金额/百分比/手机/邮箱/URL…）
- 主题抽取（工作/美食/财务…）
- 立场识别（positive/negative/neutral）
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from core.message import Message
from analyzers.interpretation_analyzer import InterpretationAnalyzer


class TestInterpretationAnalyzer(unittest.TestCase):
    """InterpretationAnalyzer 测试"""

    def setUp(self):
        self.analyzer = InterpretationAnalyzer()

    def _msgs(self, contents, sender="A"):
        return [Message(sender=sender, content=c) for c in contents]

    # ----------------------------------------------------------------
    # 意图识别
    # ----------------------------------------------------------------
    def test_intent_question(self):
        r = self.analyzer._recognize_intents(self._msgs(["你在吗？", "什么时候出发？"]))
        self.assertGreater(r["intent_counts"]["询问"], 0)
        self.assertTrue(r["available"])

    def test_intent_confession(self):
        r = self.analyzer._recognize_intents(self._msgs(["我喜欢你很久了"]))
        self.assertGreater(r["intent_counts"]["表白"], 0)

    def test_intent_thanks(self):
        r = self.analyzer._recognize_intents(self._msgs(["谢谢你帮我"]))
        self.assertGreater(r["intent_counts"]["感谢"], 0)

    def test_intent_request(self):
        r = self.analyzer._recognize_intents(self._msgs(["麻烦你帮我订个餐厅"]))
        self.assertGreater(r["intent_counts"]["请求"], 0)

    def test_intent_rejection(self):
        r = self.analyzer._recognize_intents(self._msgs(["我不去，下次吧"]))
        self.assertGreater(r["intent_counts"]["拒绝"], 0)

    def test_intent_by_sender(self):
        r = self.analyzer._recognize_intents(self._msgs(["谢谢你"] * 3, sender="B"))
        self.assertIn("B", r["by_sender"])
        self.assertGreater(r["by_sender"]["B"].get("感谢", 0), 0)

    def test_intent_distribution_sums_to_1(self):
        r = self.analyzer._recognize_intents(self._msgs(["在吗？", "谢谢你", "一起吃饭吧"]))
        total = sum(r["distribution"].values())
        # 分布各项按 3 位取整，1/3 取整后累加可能略小于 1，容忍 2 位精度
        self.assertAlmostEqual(total, 1.0, places=2)

    def test_intent_empty(self):
        r = self.analyzer._recognize_intents(self._msgs([""]))
        self.assertFalse(r["available"])
        self.assertEqual(r["dominant_intent"], "unknown")

    # ----------------------------------------------------------------
    # 实体识别（NER Lite）
    # ----------------------------------------------------------------
    def test_ner_amount(self):
        r = self.analyzer._extract_entities(self._msgs(["这次费用¥500万"]))
        types = [t for t, _ in r["by_type"]]
        self.assertIn("金额", types)

    def test_ner_percent_phone_email_url(self):
        r = self.analyzer._extract_entities(
            self._msgs(["涨了50%，电话13800138000，邮箱a@b.com，链接https://x.com/abc"])
        )
        types = [t for t, _ in r["by_type"]]
        for expect in ["百分比", "手机", "邮箱", "URL"]:
            self.assertIn(expect, types)

    def test_ner_dedupe_same_value(self):
        r = self.analyzer._extract_entities(self._msgs(["50%……也是50%"]))
        counts = dict(r["by_type"])
        self.assertEqual(counts.get("百分比", 0), 1, "同类型同值应去重")

    def test_ner_cap_per_type(self):
        # 每种类型最多保留 20 个，避免数据爆炸
        long_content = " ".join(f"价格¥{i}万" for i in range(30))
        r = self.analyzer._extract_entities(self._msgs([long_content]))
        self.assertLessEqual(len(r["entities"]["金额"]), 20)

    def test_ner_none(self):
        r = self.analyzer._extract_entities(self._msgs(["随便聊聊"]))
        self.assertFalse(r["available"])
        self.assertEqual(r["total_count"], 0)

    # ----------------------------------------------------------------
    # 主题抽取
    # ----------------------------------------------------------------
    def test_topic_work(self):
        r = self.analyzer._extract_topics(self._msgs(["项目会议几点开始", "客户要方案"]))
        names = [t["name"] for t in r["topics"]]
        self.assertIn("工作", names)

    def test_topic_food(self):
        r = self.analyzer._extract_topics(self._msgs(["去吃火锅吧", "这家烧烤不错"]))
        names = [t["name"] for t in r["topics"]]
        self.assertIn("美食", names)

    def test_topic_finance(self):
        r = self.analyzer._extract_topics(self._msgs(["什么时候还你钱", "工资到账了"]))
        names = [t["name"] for t in r["topics"]]
        self.assertIn("财务", names)

    def test_topic_weight_once_per_msg(self):
        # 一条消息命中多个关键词只算 1 次
        r = self.analyzer._extract_topics(self._msgs(["吃火锅喝奶茶"]))
        weights = {t["name"]: t["weight"] for t in r["topics"]}
        self.assertEqual(weights.get("美食", 0), 1)

    def test_topic_top5_limit(self):
        contents = ["项目", "开会", "吃火锅", "还钱", "考试", "加班", "喜欢"] * 2
        r = self.analyzer._extract_topics(self._msgs(contents))
        self.assertLessEqual(len(r["topics"]), 5)

    def test_topic_none(self):
        r = self.analyzer._extract_topics(self._msgs(["哈哈哈哈", "嗯嗯"]))
        self.assertFalse(r["available"])

    # ----------------------------------------------------------------
    # 立场识别
    # ----------------------------------------------------------------
    def _topic_arg(self):
        return {"available": True, "topics": [{"name": "工作", "weight": 3}]}

    def test_stance_positive(self):
        r = self.analyzer._detect_stances(
            self._msgs(["我同意你的方案", "没问题", "好的"]), self._topic_arg()
        )
        self.assertTrue(r["available"])
        for _sender, info in r["by_sender"].items():
            self.assertEqual(info["dominant"], "positive")

    def test_stance_negative(self):
        r = self.analyzer._detect_stances(
            self._msgs(["我不同意", "不行", "反对"]), self._topic_arg()
        )
        self.assertTrue(r["available"])
        for _sender, info in r["by_sender"].items():
            self.assertEqual(info["dominant"], "negative")

    def test_stance_no_topic(self):
        r = self.analyzer._detect_stances(
            self._msgs(["我同意"]), {"available": False, "topics": []}
        )
        self.assertFalse(r["available"])

    def test_classify_stance(self):
        self.assertEqual(self.analyzer._classify_stance("我同意", []), "positive")
        self.assertEqual(self.analyzer._classify_stance("我反对", []), "negative")
        self.assertEqual(self.analyzer._classify_stance("我考虑看看", []), "neutral")

    # ----------------------------------------------------------------
    # validate / analyze 整体
    # ----------------------------------------------------------------
    def test_validate_threshold(self):
        self.assertFalse(self.analyzer.validate(self._msgs(["a", "b"])))
        self.assertTrue(self.analyzer.validate(self._msgs(["a", "b", "c"])))

    def test_analyze_full_details(self):
        msgs = self._msgs(["帮我订餐厅，今晚吃火锅", "好的，¥500够吗？", "谢谢你！"])
        r = self.analyzer.analyze(msgs)
        for key in ("intents", "entities", "topics", "stances", "summary"):
            self.assertIn(key, r.details)
        self.assertGreaterEqual(r.confidence, 0)

    def test_analyze_empty_no_crash(self):
        r = self.analyzer.analyze(self._msgs(["", ""]))
        self.assertIn("summary", r.details)
        self.assertEqual(r.details["intents"]["dominant_intent"], "unknown")

    def test_analyze_metadata(self):
        r = self.analyzer.analyze(self._msgs(["你好", "谢谢", "好的"]))
        self.assertEqual(r.metadata["analyzer"], "InterpretationAnalyzer")
        self.assertIn("has_jieba", r.metadata)
        self.assertEqual(r.metadata["sample_size"], 3)


if __name__ == "__main__":
    unittest.main()
