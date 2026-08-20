"""core.analyzer_base 单元测试"""

import sys
import unittest
from pathlib import Path
from typing import List

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from core.analyzer_base import AnalyzerBase, AnalyzerRegistry
from core.message import Message
from core.result import AnalysisResult


class MockAnalyzer(AnalyzerBase):
    """用于测试的 Mock 分析器"""
    name = "mock"

    def __init__(self, config=None, should_pass=True, name=None):
        super().__init__(config)
        self.should_pass = should_pass
        self.call_count = 0
        if name is not None:
            self.name = name

    def validate(self, messages: List[Message]) -> bool:
        return self.should_pass

    def analyze(self, messages: List[Message], **kwargs) -> AnalysisResult:
        self.call_count += 1
        return AnalysisResult(
            analyzer_name=self.name,
            score=len(messages) * 1.0,
            confidence=80.0,
            details={"message_count": len(messages)},
        )


class TestAnalyzerBase(unittest.TestCase):
    """AnalyzerBase 测试"""

    def test_subclass(self):
        a = MockAnalyzer()
        self.assertEqual(a.name, "mock")
        self.assertEqual(a.version, "2.2.0")

    def test_get_confidence(self):
        a = MockAnalyzer()
        result = AnalysisResult(analyzer_name="x", confidence=75.0)
        self.assertEqual(a.get_confidence(result), 75.0)

    def test_get_summary(self):
        a = MockAnalyzer()
        result = AnalysisResult(analyzer_name="x", score=50.0, confidence=80.0)
        summary = a.get_summary(result)
        # 默认使用 self.name ("mock")
        self.assertIn("mock", summary)
        self.assertIn("50", summary)


class TestAnalyzerRegistry(unittest.TestCase):
    """AnalyzerRegistry 测试"""

    def test_register(self):
        registry = AnalyzerRegistry()
        a = MockAnalyzer()
        registry.register(a)
        self.assertEqual(registry.list(), ["mock"])

    def test_register_duplicate(self):
        registry = AnalyzerRegistry()
        a1 = MockAnalyzer()
        a2 = MockAnalyzer()
        registry.register(a1)
        with self.assertRaises(ValueError):
            registry.register(a2)

    def test_unregister(self):
        registry = AnalyzerRegistry()
        a = MockAnalyzer()
        registry.register(a)
        registry.unregister("mock")
        self.assertEqual(registry.list(), [])

    def test_get(self):
        registry = AnalyzerRegistry()
        a = MockAnalyzer()
        registry.register(a)
        self.assertIs(registry.get("mock"), a)
        self.assertIsNone(registry.get("nonexistent"))

    def test_register_invalid_type(self):
        registry = AnalyzerRegistry()
        with self.assertRaises(TypeError):
            registry.register("not an analyzer")

    def test_run_all(self):
        registry = AnalyzerRegistry()
        registry.register(MockAnalyzer(name="a1"))
        registry.register(MockAnalyzer(name="a2"))

        msgs = [Message(sender="other", content="x") for _ in range(5)]
        results = registry.run_all(msgs)

        self.assertEqual(len(results), 2)
        self.assertIn("a1", results)
        self.assertIn("a2", results)
        self.assertEqual(results["a1"].score, 5.0)

    def test_run_all_skip_invalid(self):
        registry = AnalyzerRegistry()
        registry.register(MockAnalyzer(name="passing", should_pass=True))
        registry.register(MockAnalyzer(name="failing", should_pass=False))

        msgs = [Message(sender="other", content="x")]
        results = registry.run_all(msgs, skip_invalid=True)

        self.assertIn("passing", results)
        self.assertNotIn("failing", results)

    def test_run_all_with_failure(self):
        class FailingAnalyzer(AnalyzerBase):
            name = "fail"
            def validate(self, messages): return True
            def analyze(self, messages, **kwargs):
                raise RuntimeError("test error")

        registry = AnalyzerRegistry()
        registry.register(MockAnalyzer(name="ok"))
        registry.register(FailingAnalyzer())

        msgs = [Message(sender="other", content="x")]
        results = registry.run_all(msgs)

        self.assertIn("ok", results)
        self.assertIn("fail", results)
        self.assertIn("error", results["fail"].details)

    def test_run_one(self):
        registry = AnalyzerRegistry()
        registry.register(MockAnalyzer(name="a"))
        msgs = [Message(sender="other", content="x")]

        result = registry.run_one("a", msgs)
        self.assertEqual(result.analyzer_name, "a")

    def test_run_one_not_found(self):
        registry = AnalyzerRegistry()
        with self.assertRaises(KeyError):
            registry.run_one("missing", [])


if __name__ == "__main__":
    unittest.main()
