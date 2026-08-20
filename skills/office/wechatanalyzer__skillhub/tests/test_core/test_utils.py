"""core.utils 编码自动检测 单元测试（v2.1.0）"""

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from core.utils import decode_bytes_auto, read_text_auto


class TestDecodeBytesAuto(unittest.TestCase):
    """decode_bytes_auto 测试"""

    def test_utf8(self):
        # 无 BOM 的 UTF-8 用 utf-8-sig 也能正确解码（两者结果一致），
        # 按优先级报 utf-8-sig 属正常
        text, enc = decode_bytes_auto("你好，世界".encode("utf-8"))
        self.assertEqual(text, "你好，世界")
        self.assertIn(enc, ("utf-8", "utf-8-sig"))

    def test_utf8_sig(self):
        text, enc = decode_bytes_auto("你好".encode("utf-8-sig"))
        self.assertEqual(text, "你好")
        self.assertEqual(enc, "utf-8-sig")

    def test_gb18030(self):
        text, enc = decode_bytes_auto("小王: 你好啊".encode("gb18030"))
        self.assertEqual(text, "小王: 你好啊")
        self.assertEqual(enc, "gb18030")

    def test_fallback_order(self):
        """utf-8 失败时应回退到 gb18030"""
        data = "微信聊天记录".encode("gbk")
        text, enc = decode_bytes_auto(data)
        self.assertEqual(text, "微信聊天记录")
        self.assertEqual(enc, "gb18030")


class TestReadTextAuto(unittest.TestCase):
    """read_text_auto 测试"""

    def _write(self, data: bytes) -> str:
        fd, path = tempfile.mkstemp(suffix=".txt")
        import os
        with os.fdopen(fd, "wb") as f:
            f.write(data)
        return path

    def test_read_gbk_file(self):
        path = self._write("张三: 周末聚餐".encode("gb18030"))
        try:
            text, enc = read_text_auto(path)
            self.assertEqual(text, "张三: 周末聚餐")
            self.assertEqual(enc, "gb18030")
        finally:
            Path(path).unlink()

    def test_read_utf8_bom_file(self):
        path = self._write("self: 你好".encode("utf-8-sig"))
        try:
            text, enc = read_text_auto(path)
            self.assertEqual(text, "self: 你好")
            self.assertEqual(enc, "utf-8-sig")
        finally:
            Path(path).unlink()

    def test_missing_file_friendly_error(self):
        with self.assertRaises(FileNotFoundError) as ctx:
            read_text_auto("不存在的文件_xyz.txt")
        self.assertIn("文件不存在", str(ctx.exception))

    def test_empty_file(self):
        path = self._write(b"")
        try:
            text, _enc = read_text_auto(path)
            self.assertEqual(text, "")
        finally:
            Path(path).unlink()


if __name__ == "__main__":
    unittest.main()
