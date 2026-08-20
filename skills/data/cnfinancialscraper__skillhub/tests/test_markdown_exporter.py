# -*- coding: utf-8 -*-
"""markdown_exporter.py 单元测试 — 单文件/批量/ZIP/中文文件名。"""
import sys
import shutil
import zipfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.dont_write_bytecode = True

import unittest
import tempfile
from scripts.markdown_exporter import MarkdownExporter, export_to_markdown, batch_to_markdown, _safe_filename


class TestSafeFilename(unittest.TestCase):
    def test_chinese_kept(self):
        self.assertEqual(_safe_filename("贵州茅台"), "贵州茅台")

    def test_illegal_chars_replaced(self):
        self.assertEqual(_safe_filename('a/b\\c:d*e?f"g<h>i|j'), "a_b_c_d_e_f_g_h_i_j")

    def test_empty_safe(self):
        self.assertEqual(_safe_filename(""), "untitled")

    def test_whitespace_normalized(self):
        self.assertEqual(_safe_filename("a  b\tc"), "a_b_c")


class TestSingleExport(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.exp = MarkdownExporter(output_dir=self.tmp)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_html_content_converted(self):
        data = {
            "title": "测试标题",
            "source": "财联社",
            "url": "https://x.com",
            "published_at": "2026-07-29",
            "content": "<h2>子标题</h2><p>正文内容</p>",
        }
        path = self.exp.export(data)
        self.assertTrue(Path(path).exists())
        text = Path(path).read_text(encoding="utf-8")
        self.assertIn("# 测试标题", text)
        self.assertIn("## 子标题", text)
        self.assertIn("正文内容", text)
        self.assertIn("**来源**: 财联社", text)

    def test_md_content_kept(self):
        data = {
            "title": "MD 测试",
            "content": "# Already MD\n\n正文",
        }
        path = self.exp.export(data)
        text = Path(path).read_text(encoding="utf-8")
        # 原始 MD 不应被二次转换
        self.assertIn("# Already MD", text)


class TestBatchExport(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.exp = MarkdownExporter(output_dir=self.tmp)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_batch_creates_structure(self):
        items = [
            {"title": "新闻1", "source": "财联社", "content": "<p>c1</p>"},
            {"title": "新闻2", "source": "新华财经", "content": "<p>c2</p>"},
        ]
        res = self.exp.build_batch_export(items, batch_id="b1")
        self.assertEqual(res["count"], "2")
        self.assertTrue(Path(res["dir"]).exists())
        self.assertTrue(Path(res["index"]).exists())
        self.assertTrue(Path(res["metadata"]).exists())
        self.assertTrue(Path(res["zip"]).exists())

        # 索引文件应包含目录
        idx_text = Path(res["index"]).read_text(encoding="utf-8")
        self.assertIn("新闻1", idx_text)
        self.assertIn("财联社", idx_text)

    def test_chinese_filename_in_zip(self):
        items = [{"title": "中文测试", "source": "测试媒体", "content": "<p>x</p>"}]
        res = self.exp.build_batch_export(items, batch_id="中文批次")
        with zipfile.ZipFile(res["zip"]) as zf:
            names = zf.namelist()
            # 中文应保留
            self.assertTrue(any("测试媒体" in n for n in names), f"中文文件名丢失: {names}")


class TestMerge(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.exp = MarkdownExporter(output_dir=self.tmp)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_merge_with_toc(self):
        # 先创建 2 个 MD 文件
        f1 = self.exp.export({"title": "文章甲", "content": "<p>内容甲</p>"})
        f2 = self.exp.export({"title": "文章乙", "content": "<p>内容乙</p>"})
        merged = self.exp.merge_files([f1, f2], f"{self.tmp}/merged.md", toc=True)
        text = Path(merged).read_text(encoding="utf-8")
        self.assertIn("# 合并报告", text)
        self.assertIn("## 目录", text)
        self.assertIn("文章甲", text)
        self.assertIn("文章乙", text)


class TestZipEncoding(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_zip_round_trip_chinese(self):
        # 写入中文文件名的 MD
        md = Path(self.tmp) / "中文文档.md"
        md.write_text("# 测试", encoding="utf-8")
        # 创建 media 目录
        media = Path(self.tmp) / "media"
        media.mkdir()
        img = media / "图片.png"
        img.write_bytes(b"\x89PNG fake")

        zip_path = Path(self.tmp) / "out.zip"
        exp = MarkdownExporter(output_dir=self.tmp)
        exp.generate_zip(str(md), media_dir=str(media), zip_path=str(zip_path))

        # 重新打开 ZIP 验证
        with zipfile.ZipFile(zip_path) as zf:
            names = zf.namelist()
            # 中文文件名应保留（可能路径前缀不同）
            all_text = " ".join(names)
            self.assertIn("中文文档", all_text)
            self.assertIn("图片.png", all_text)


if __name__ == "__main__":
    unittest.main()