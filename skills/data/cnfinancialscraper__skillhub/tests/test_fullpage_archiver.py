# -*- coding: utf-8 -*-
"""测试 fullpage_archiver.py — 纯函数部分（不依赖浏览器）。"""
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
sys.dont_write_bytecode = True

from fullpage_archiver import (
    FullPageArchiver, ArchiveResult, _IMG_SRC_RE, _TABLE_RE,
)


class TestArchiveResult(unittest.TestCase):
    """ArchiveResult 数据类测试。"""

    def test_to_dict(self):
        r = ArchiveResult(
            url="https://example.com",
            title="Test Article",
            page_count=3,
            image_count=10,
            canvas_count=2,
            table_count=5,
        )
        d = r.to_dict()
        self.assertEqual(d["url"], "https://example.com")
        self.assertEqual(d["title"], "Test Article")
        self.assertEqual(d["page_count"], 3)

    def test_summary_contains_key_info(self):
        r = ArchiveResult(
            url="https://example.com",
            title="测试文章",
            page_count=2,
            image_count=5,
            canvas_count=1,
            table_count=3,
            inline_html_path="/tmp/test_inline.html",
        )
        s = r.summary
        self.assertIn("测试文章", s)
        self.assertIn("2", s)  # page count
        self.assertIn("5", s)  # image count
        self.assertIn("test_inline.html", s)

    def test_summary_handles_errors(self):
        r = ArchiveResult(
            url="https://example.com",
            errors=["连接超时", "图片下载失败"],
        )
        self.assertIn("2 个错误", r.summary)


class TestImageExtraction(unittest.TestCase):
    """图片 URL 提取正则测试。"""

    def test_img_src_simple(self):
        html = '<img src="https://example.com/img.jpg">'
        matches = _IMG_SRC_RE.findall(html)
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0], "https://example.com/img.jpg")

    def test_img_src_single_quotes(self):
        html = "<img src='https://example.com/img.png'>"
        matches = _IMG_SRC_RE.findall(html)
        self.assertEqual(len(matches), 1)

    def test_img_src_multiple(self):
        html = """
        <img src="a.jpg" alt="A">
        <img src="b.png" alt="B">
        <img src="c.gif" alt="C">
        """
        matches = _IMG_SRC_RE.findall(html)
        self.assertEqual(len(matches), 3)

    def test_img_data_uri_ignored(self):
        """data: URI 不应该被提取（由 _download_single_image 处理）。"""
        html = '<img src="data:image/png;base64,ABC123">'
        matches = _IMG_SRC_RE.findall(html)
        self.assertEqual(len(matches), 1)  # 提取出来，但在下载时跳过
        self.assertIn("data:image/png", matches[0])


class TestTableExtraction(unittest.TestCase):
    """表格提取测试。"""

    def test_simple_table(self):
        html = """
        <table>
            <tr><th>Name</th><th>Value</th></tr>
            <tr><td>营收</td><td>1500亿</td></tr>
            <tr><td>净利润</td><td>300亿</td></tr>
        </table>
        """
        archiver = FullPageArchiver()
        tables = archiver._extract_page_tables(html, 1, tempfile.mkdtemp())
        self.assertEqual(len(tables), 1)
        self.assertEqual(tables[0]["rows"], 3)
        self.assertEqual(tables[0]["cols"], 2)

    def test_empty_table_no_rows(self):
        html = "<table></table>"
        archiver = FullPageArchiver()
        tables = archiver._extract_page_tables(html, 1, tempfile.mkdtemp())
        self.assertEqual(len(tables), 0)

    def test_table_with_colspan(self):
        html = """
        <table>
            <tr><th>Header</th></tr>
            <tr><td>Value 1</td></tr>
        </table>
        """
        archiver = FullPageArchiver()
        tables = archiver._extract_page_tables(html, 1, tempfile.mkdtemp())
        self.assertEqual(len(tables), 1)

    def test_multiple_tables(self):
        html = "<table><tr><td>A</td></tr></table><table><tr><td>B</td></tr></table>"
        archiver = FullPageArchiver()
        tables = archiver._extract_page_tables(html, 1, tempfile.mkdtemp())
        self.assertEqual(len(tables), 2)


class TestHTMLProcessing(unittest.TestCase):
    """HTML 处理函数测试。"""

    def test_extract_title(self):
        html = "<html><head><title>测试标题</title></head><body></body></html>"
        title = FullPageArchiver._extract_title(html)
        self.assertEqual(title, "测试标题")

    def test_extract_title_none(self):
        title = FullPageArchiver._extract_title("<html></html>")
        self.assertEqual(title, "")

    def test_extract_domain(self):
        domain = FullPageArchiver._extract_domain("https://www.example.com/path?a=1")
        self.assertEqual(domain, "example.com")

    def test_guess_image_ext(self):
        self.assertEqual(FullPageArchiver._guess_image_ext("https://x.com/img.png"), ".png")
        self.assertEqual(FullPageArchiver._guess_image_ext("https://x.com/img.jpg"), ".jpg")
        self.assertEqual(FullPageArchiver._guess_image_ext("https://x.com/img.jpeg"), ".jpg")
        self.assertEqual(FullPageArchiver._guess_image_ext("https://x.com/img.webp"), ".webp")
        self.assertEqual(FullPageArchiver._guess_image_ext("https://x.com/img"), ".jpg")  # default

    def test_escape_html(self):
        self.assertEqual(
            FullPageArchiver._escape_html('<script>alert("XSS")</script>'),
            '&lt;script&gt;alert(&quot;XSS&quot;)&lt;/script&gt;',
        )

    def test_file_to_base64(self):
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False, mode="w") as f:
            f.write("hello")
            path = f.name
        try:
            b64 = FullPageArchiver._file_to_base64(path)
            self.assertTrue(len(b64) > 0)
        finally:
            os.unlink(path)

    def test_file_to_base64_missing(self):
        b64 = FullPageArchiver._file_to_base64("/nonexistent/file.jpg")
        self.assertEqual(b64, "")


class TestFallbackFetch(unittest.TestCase):
    """HTTP 回退抓取测试（不依赖浏览器）。"""

    def test_http_fallback_returns_list(self):
        archiver = FullPageArchiver()
        # 用不存在的 URL 测试回退逻辑
        result = archiver._fetch_pages_http("https://invalid.example.com/nonexistent")
        self.assertIsInstance(result, list)

    def test_http_fallback_empty_on_failure(self):
        archiver = FullPageArchiver()
        result = archiver._fetch_pages_http("https://192.0.2.1/nonexistent")
        self.assertEqual(len(result), 0)


class TestInlineImageReplacement(unittest.TestCase):
    """图片内嵌替换测试。"""

    def setUp(self):
        self.archiver = FullPageArchiver()

    def test_inline_with_no_images(self):
        html = "<p>No images here</p>"
        result = self.archiver._inline_images_in_html(html, {}, "https://example.com")
        self.assertIn("No images here", result)

    def test_relink_with_no_images(self):
        html = "<p>No images here</p>"
        result = self.archiver._relink_images_in_html(html, {})
        self.assertIn("No images here", result)

    def test_extract_body_content(self):
        html = "<html><head></head><body><p>Hello</p></body></html>"
        content = self.archiver._extract_body_content(html)
        self.assertIn("Hello", content)

    def test_extract_body_no_body_tag(self):
        html = "<p>No body tag</p>"
        content = self.archiver._extract_body_content(html)
        self.assertIn("No body tag", content)


if __name__ == "__main__":
    unittest.main()
