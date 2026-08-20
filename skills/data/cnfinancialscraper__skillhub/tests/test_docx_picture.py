# -*- coding: utf-8 -*-
"""report_exporter.py 新增 export_with_images / MarkdownExporter 测试。"""
import sys
import shutil
import tempfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.dont_write_bytecode = True

import unittest
from scripts.report_exporter import WordExporter, MarkdownExporter


class TestWordExporterWithImages(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        # 准备测试图片（1x1 PNG）
        import struct
        png_data = (
            b"\x89PNG\r\n\x1a\n"
            b"\x00\x00\x00\rIHDR"
            b"\x00\x00\x00\x01\x00\x00\x00\x01"
            b"\x08\x06\x00\x00\x00\x1f\x15\xc4\x89"
            b"\x00\x00\x00\rIDATx\x9cc\xf8\xff\xff?\x00\x05\xfe\x02\xfe\xa3\x8b\x80\x00\x00\x00"
            b"\x00IEND\xaeB`\x82"
        )
        self.img_path = Path(self.tmp) / "test.png"
        self.img_path.write_bytes(png_data)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_export_with_images_md_fallback(self):
        # 即使没装 python-docx，fallback 也能写 MD
        we = WordExporter()
        data = {
            "title": "测试报告",
            "metadata": {"source": "财联社", "date": "2026-07-29"},
            "sections": [
                {"heading": "一、引言", "level": 1,
                 "paragraphs": ["这是引言段落"],
                 "images": [{"path": str(self.img_path), "caption": "测试图"}]},
                {"heading": "二、结论", "level": 1,
                 "paragraphs": ["这是结论段落"],
                 "images": []},
            ]
        }
        out = we.export_with_images(data, output_path=str(Path(self.tmp) / "out.docx"))
        self.assertTrue(Path(out).exists())

    def test_markdown_exporter_basic(self):
        me = MarkdownExporter(output_dir=self.tmp)
        data = {"title": "测试", "source": "财联社",
                "content": "<h2>子标题</h2><p>正文</p>"}
        out = me.export(data)
        self.assertTrue(Path(out).exists())
        text = Path(out).read_text(encoding="utf-8")
        self.assertIn("测试", text)
        self.assertIn("财联社", text)


if __name__ == "__main__":
    unittest.main()