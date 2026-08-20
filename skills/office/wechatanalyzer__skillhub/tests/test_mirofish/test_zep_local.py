"""mirofish.core.zep_local.ZepLocalGraph 单元测试（v2.1.0）"""

import sys
import tempfile
import unittest
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from core.message import Message
from mirofish.core.zep_local import ZepLocalGraph


def _make_messages():
    return [
        Message(sender="小王", content="周末我们一起聚餐吧",
                timestamp=datetime(2024, 1, 1, 12, 0, 0)),
        Message(sender="self", content="好的，周末有空",
                timestamp=datetime(2024, 1, 1, 12, 1, 0)),
        Message(sender="小王", content="投资理财的事情你考虑下",
                timestamp=datetime(2024, 1, 1, 12, 2, 0)),
    ]


class TestZepLocalGraph(unittest.TestCase):
    """ZepLocalGraph 建库 / 统计 / 幂等测试"""

    def setUp(self):
        fd, self.db_path = tempfile.mkstemp(suffix=".db")
        import os
        os.close(fd)
        Path(self.db_path).unlink()  # 让 ZepLocalGraph 自己创建
        self.graph = ZepLocalGraph(db_path=self.db_path)

    def tearDown(self):
        if Path(self.db_path).exists():
            Path(self.db_path).unlink()

    def test_build_and_stats(self):
        """建库后统计应大于 0"""
        added = self.graph.build_from_messages(_make_messages())
        self.assertEqual(added, 3)
        stats = self.graph.get_stats()
        self.assertGreaterEqual(stats["entities"], 2)  # 至少两个发送者
        self.assertGreater(stats["relations"], 0)
        self.assertEqual(stats["memories"], 3)

    def test_build_idempotent(self):
        """重复 build 幂等：第二次不新增任何记忆/实体/关系"""
        self.graph.build_from_messages(_make_messages())
        stats1 = self.graph.get_stats()
        added2 = self.graph.build_from_messages(_make_messages())
        stats2 = self.graph.get_stats()
        self.assertEqual(added2, 0)
        self.assertEqual(stats1, stats2)

    def test_build_incremental(self):
        """增量 build：新增消息只追加新记忆"""
        msgs = _make_messages()
        self.graph.build_from_messages(msgs[:2])
        added = self.graph.build_from_messages(msgs)
        self.assertEqual(added, 1)
        self.assertEqual(self.graph.get_stats()["memories"], 3)

    def test_get_graph_format(self):
        """get_graph 输出兼容 main.py graph-stats 展示代码"""
        self.graph.build_from_messages(_make_messages())
        data = self.graph.get_graph()
        self.assertIn("entities", data)
        self.assertIn("relations", data)
        for e in data["entities"]:
            self.assertIn("name", e)
            self.assertIn("type", e)
        for r in data["relations"]:
            self.assertIn("type", r)
        # 发送者应作为 person 实体存在
        names = {e["name"] for e in data["entities"] if e["type"] == "person"}
        self.assertIn("小王", names)

    def test_empty_messages(self):
        """空输入不报错"""
        added = self.graph.build_from_messages([])
        self.assertEqual(added, 0)
        self.assertEqual(self.graph.get_stats(),
                         {"entities": 0, "relations": 0, "memories": 0})

    def test_dict_messages_compatible(self):
        """兼容 dict 形式消息输入"""
        added = self.graph.build_from_messages([
            {"sender": "小王", "content": "你好啊朋友", "timestamp": None}
        ])
        self.assertEqual(added, 1)
        self.assertEqual(self.graph.get_stats()["memories"], 1)


if __name__ == "__main__":
    unittest.main()
