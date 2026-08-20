# -*- coding: utf-8 -*-
"""crawl_packager.py + markdown_exporter.py 中文文件名 ZIP 测试。"""
import sys
import zipfile
import shutil
import tempfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.dont_write_bytecode = True

import unittest
from scripts.crawl_packager import _write_zip_utf8, set_zip_encoding, package_with_images


class TestWriteZipUtf8(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_ascii_filename_no_extra(self):
        # 纯 ASCII 不应附加 extra 字段
        f = Path(self.tmp) / "ascii.txt"
        f.write_text("hello", encoding="utf-8")
        zip_path = Path(self.tmp) / "out.zip"
        with zipfile.ZipFile(str(zip_path), "w", zipfile.ZIP_DEFLATED) as zf:
            _write_zip_utf8(zf, str(f), "ascii.txt")
        # 验证能正常读取
        with zipfile.ZipFile(zip_path) as zf:
            self.assertIn("ascii.txt", zf.namelist())

    def test_chinese_filename_preserved(self):
        f = Path(self.tmp) / "源.txt"
        f.write_text("数据", encoding="utf-8")
        zip_path = Path(self.tmp) / "out.zip"
        with zipfile.ZipFile(str(zip_path), "w", zipfile.ZIP_DEFLATED) as zf:
            _write_zip_utf8(zf, str(f), "源文件.txt")
        with zipfile.ZipFile(zip_path) as zf:
            names = zf.namelist()
            # 中文文件名应保留
            self.assertTrue(any("源文件" in n for n in names), f"中文丢失: {names}")


class TestPackageWithImages(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_basic(self):
        # 模拟有图片的内容
        img_dir = Path(self.tmp) / "imgs"
        img_dir.mkdir()
        img = img_dir / "测试.png"
        img.write_bytes(b"\x89PNG fake image data")

        items = [
            {"name": "新闻1", "content": "正文1", "image_map": {"https://x/a.png": str(img)}},
            {"name": "新闻2", "content": "正文2", "image_map": {}},
        ]
        zip_path = package_with_images(items, zip_name="中文测试",
                                       output_dir=self.tmp)
        self.assertTrue(Path(zip_path).exists())
        # 验证包含中文图片名
        with zipfile.ZipFile(zip_path) as zf:
            names = zf.namelist()
            self.assertTrue(any("测试" in n for n in names))


class TestSetZipEncoding(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_fix_zip(self):
        # 创建一个中文 ZIP
        f = Path(self.tmp) / "原.txt"
        f.write_text("内容", encoding="utf-8")
        zip_path = Path(self.tmp) / "src.zip"
        with zipfile.ZipFile(str(zip_path), "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("原文件.txt", "数据")
        # 修复
        fixed = set_zip_encoding(str(zip_path))
        self.assertTrue(Path(fixed).exists())
        with zipfile.ZipFile(fixed) as zf:
            names = zf.namelist()
            self.assertEqual(len(names), len(set(names)),
                             f"修复后的 ZIP 不应包含重复条目: {names}")
            self.assertEqual(names.count("原文件.txt"), 1)


if __name__ == "__main__":
    unittest.main()
