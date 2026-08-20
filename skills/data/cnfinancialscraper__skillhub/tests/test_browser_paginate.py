# -*- coding: utf-8 -*-
"""browser_scraper.py 增强方法 + web_parser.PageOperator 扩展测试。

注意：实际浏览器操作需要 playwright + chromium，本文件测试纯函数（无 IO）。
完整 E2E 测试请在 playwright 环境运行。
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.dont_write_bytecode = True

import unittest
from scripts.browser_scraper import _strip_dynamic_markers, _guess_image_ext


class TestStripDynamic(unittest.TestCase):
    def test_strips_scripts(self):
        html = "<div>x<script>alert(1)</script></div>"
        out = _strip_dynamic_markers(html)
        self.assertNotIn("alert", out)

    def test_strips_timestamp_10_13(self):
        html = "<p>Published at 1700000000</p>"
        out = _strip_dynamic_markers(html)
        self.assertNotIn("1700000000", out)
        self.assertIn("TS", out)

    def test_strips_iso_datetime(self):
        html = "<p>2026-07-29T10:00:00</p>"
        out = _strip_dynamic_markers(html)
        self.assertNotIn("2026-07-29T10:00:00", out)

    def test_keeps_normal_content(self):
        html = "<p>Static content 123</p>"
        out = _strip_dynamic_markers(html)
        self.assertIn("Static content", out)


class TestGuessImageExt(unittest.TestCase):
    def test_jpg(self):
        self.assertEqual(_guess_image_ext("https://x.com/a.jpg"), ".jpg")

    def test_jpeg(self):
        self.assertEqual(_guess_image_ext("https://x.com/a.jpeg"), ".jpg")

    def test_png(self):
        self.assertEqual(_guess_image_ext("https://x.com/path/b.png"), ".png")

    def test_webp(self):
        self.assertEqual(_guess_image_ext("https://x.com/x.webp?v=1"), ".webp")

    def test_default(self):
        self.assertEqual(_guess_image_ext("https://x.com/noext"), ".jpg")


class TestBrowserMethodsExist(unittest.TestCase):
    """检查所有新方法都已挂载到 BrowserScraper 类。"""

    def test_all_methods_mounted(self):
        from scripts.browser_scraper import BrowserScraper
        for name in ("paginate", "extract_links", "follow_links",
                     "download_images", "capture_canvas", "fetch_full_article"):
            with self.subTest(method=name):
                self.assertTrue(hasattr(BrowserScraper, name),
                                f"BrowserScraper.{name} 未挂载")


class TestPageOperatorMethodsExist(unittest.TestCase):
    """检查 PageOperator 已扩展三个方法。"""

    def test_all_methods_exist(self):
        from scripts.web_parser import PageOperator
        for name in ("paginate", "extract_all_links", "follow_links"):
            with self.subTest(method=name):
                self.assertTrue(hasattr(PageOperator, name),
                                f"PageOperator.{name} 未实现")


if __name__ == "__main__":
    unittest.main()