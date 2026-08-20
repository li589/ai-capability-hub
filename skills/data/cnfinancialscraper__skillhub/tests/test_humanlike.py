# -*- coding: utf-8 -*-
"""测试 browser_scraper.py 新增的类人操作方法（纯函数部分，不依赖 Playwright）。"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
sys.dont_write_bytecode = True

from browser_scraper import BrowserScraper


class TestHumanlikeMethodsExist(unittest.TestCase):
    """验证类人操作方法已挂载到 BrowserScraper 类。"""

    @classmethod
    def setUpClass(cls):
        cls.methods = [m for m in dir(BrowserScraper) if not m.startswith("__")]

    def test_human_mouse_move_exists(self):
        self.assertIn("_human_mouse_move", self.methods)

    def test_human_type_exists(self):
        self.assertIn("_human_type", self.methods)

    def test_human_dwell_exists(self):
        self.assertIn("_human_dwell", self.methods)

    def test_random_scroll_exists(self):
        self.assertIn("_random_scroll", self.methods)

    def test_random_viewport_exists(self):
        self.assertIn("_random_viewport", self.methods)

    def test_humanlike_fetch_exists(self):
        self.assertIn("humanlike_fetch", self.methods)

    def test_legacy_methods_still_present(self):
        """确保重构后原有方法仍然存在。"""
        legacy = ["fetch", "extract_text", "screenshot", "paginate",
                   "extract_links", "follow_links", "download_images",
                   "capture_canvas", "fetch_full_article", "smart_fetch"]
        for m in legacy:
            self.assertIn(m, self.methods, f"Missing legacy method: {m}")


class TestHumanlikeDesign(unittest.TestCase):
    """测试类人操作设计的合理性（参数验证等）。"""

    def test_humanlike_fetch_accepts_all_params(self):
        """验证 humanlike_fetch 接受预期参数。"""
        import inspect
        sig = inspect.signature(BrowserScraper.humanlike_fetch)
        params = list(sig.parameters.keys())
        self.assertIn("url", params)
        self.assertIn("scroll", params)
        self.assertIn("dwell", params)
        self.assertIn("random_viewport", params)

    def test_no_new_dependencies(self):
        """验证类人操作不引入新依赖（全部基于标准库 + Playwright）。"""
        import browser_scraper as bs_mod
        # 检查没有新的外部 import
        source = Path(bs_mod.__file__).read_text(encoding="utf-8")
        # 确认不使用 AI/ML 库
        self.assertNotIn("import torch", source)
        self.assertNotIn("import tensorflow", source)
        self.assertNotIn("import opencv", source)
        self.assertNotIn("import cv2", source)
        self.assertNotIn("from PIL", source)
        self.assertNotIn("import selenium", source)


class TestBackwardCompatibility(unittest.TestCase):
    """确保增强后向后兼容。"""

    def test_original_fetch_still_works(self):
        """原始 fetch 方法签名不变。"""
        import inspect
        sig = inspect.signature(BrowserScraper.fetch)
        params = list(sig.parameters.keys())
        self.assertIn("url", params)
        # 仍支持 wait_until, wait_selector, scroll, dismiss_cookies
        self.assertIn("wait_until", params)
        self.assertIn("scroll", params)
        self.assertIn("dismiss_cookies", params)

    def test_extract_text_unchanged(self):
        """extract_text 方法签名不变。"""
        import inspect
        sig = inspect.signature(BrowserScraper.extract_text)
        params = list(sig.parameters.keys())
        self.assertIn("url", params)
        self.assertIn("selector", params)


if __name__ == "__main__":
    unittest.main()
