# -*- coding: utf-8 -*-
"""v4.7 浏览器类人爬取加固测试（不启动真实浏览器）。

验证:
    - STEALTH_JS 升级覆盖 12+ 指纹
    - humanlike_fetch 新增参数与 finally 关闭
    - fetch/extract_text 等资源泄漏修复（静态检查）
"""
import inspect
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))


class TestStealthJsContent(unittest.TestCase):
    """STEALTH_JS 应覆盖主要反检测指纹。"""

    @classmethod
    def setUpClass(cls):
        import browser_scraper
        cls.js = browser_scraper.STEALTH_JS

    def test_webdriver_hidden(self):
        self.assertIn("navigator", self.js)
        self.assertIn("webdriver", self.js)

    def test_plugins_spoof(self):
        self.assertIn("PluginArray", self.js)
        self.assertIn("namedItem", self.js)

    def test_languages_platform(self):
        self.assertIn("languages", self.js)
        self.assertIn("platform", self.js)

    def test_hardware_fingerprints(self):
        self.assertIn("hardwareConcurrency", self.js)
        self.assertIn("deviceMemory", self.js)

    def test_permissions_api(self):
        self.assertIn("permissions.query", self.js)

    def test_chrome_runtime(self):
        self.assertIn("chrome.runtime", self.js)

    def test_webgl_spoof(self):
        self.assertIn("37445", self.js)  # UNMASKED_VENDOR_WEBGL
        self.assertIn("37446", self.js)  # UNMASKED_RENDERER_WEBGL

    def test_window_outer(self):
        self.assertIn("outerWidth", self.js)
        self.assertIn("outerHeight", self.js)

    def test_phantom_cleanup(self):
        self.assertIn("callPhantom", self.js)

    def test_min_fingerprint_count(self):
        """覆盖至少 10 个指纹项。"""
        markers = ["webdriver", "PluginArray", "languages", "platform",
                   "hardwareConcurrency", "deviceMemory", "permissions.query",
                   "chrome.runtime", "37445", "outerWidth", "connection.rtt",
                   "callPhantom"]
        hits = sum(1 for m in markers if m in self.js)
        self.assertGreaterEqual(hits, 10, f"STEALTH_JS 指纹覆盖不足: {hits}/12")


class TestHumanlikeFetchSignature(unittest.TestCase):
    """humanlike_fetch 应支持新参数。"""

    def test_new_params(self):
        import browser_scraper
        sig = inspect.signature(browser_scraper.BrowserScraper.humanlike_fetch)
        for param in ("mouse_simulation", "input_selector", "input_text"):
            self.assertIn(param, sig.parameters, f"缺少参数 {param}")
        self.assertEqual(sig.parameters["mouse_simulation"].default, True)

    def test_body_uses_mouse_and_type(self):
        """humanlike_fetch 方法体应调用 _human_mouse_move 与 _human_type。"""
        import browser_scraper
        src = inspect.getsource(browser_scraper.BrowserScraper.humanlike_fetch)
        self.assertIn("_human_mouse_move", src)
        self.assertIn("_human_type", src)

    def test_finally_closes_page(self):
        import browser_scraper
        src = inspect.getsource(browser_scraper.BrowserScraper.humanlike_fetch)
        self.assertIn("finally", src)
        self.assertIn("page.close", src)


class TestResourceLeakFixes(unittest.TestCase):
    """fetch/extract_text 等应使用 try/finally 关闭 page。"""

    def _src_of(self, func_name):
        import browser_scraper
        cls = browser_scraper.BrowserScraper
        return inspect.getsource(getattr(cls, func_name))

    def test_fetch_has_finally(self):
        src = self._src_of("fetch")
        self.assertIn("finally", src)
        self.assertIn("page.close", src)

    def test_extract_text_has_finally(self):
        src = self._src_of("extract_text")
        self.assertIn("finally", src)
        self.assertIn("page.close", src)

    def test_extract_multiple_has_finally(self):
        src = self._src_of("extract_multiple")
        self.assertIn("finally", src)

    def test_extract_table_has_finally(self):
        src = self._src_of("extract_table")
        self.assertIn("finally", src)


class TestFetchRetry(unittest.TestCase):
    """fetch 应支持 retries 参数。"""

    def test_retries_param(self):
        import browser_scraper
        sig = inspect.signature(browser_scraper.BrowserScraper.fetch)
        self.assertIn("retries", sig.parameters)
        self.assertEqual(sig.parameters["retries"].default, 2)


if __name__ == "__main__":
    unittest.main()
