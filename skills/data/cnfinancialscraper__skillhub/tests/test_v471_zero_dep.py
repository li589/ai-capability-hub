#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""v4.7.1 零依赖回归测试

目标：确保未安装 BeautifulSoup 等第三方包时，核心包仍可导入，
自适应解析与全量机构爬虫提供 stdlib 降级路径。
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))


def test_adaptive_parser_stdlib_table_fallback(monkeypatch):
    from scripts.adaptive_parser_v2 import AdaptivePageParser, HAS_BS4
    original = HAS_BS4
    monkeypatch.setattr("scripts.adaptive_parser_v2.HAS_BS4", False)
    try:
        html = (
            "<table><tr><th>名称</th><th>代码</th></tr>"
            "<tr><td>测试基金</td><td>000001</td></tr></table>"
        )
        rows = AdaptivePageParser().parse_table(html)
        assert rows == [{"名称": "测试基金", "代码": "000001"}]
    finally:
        monkeypatch.setattr("scripts.adaptive_parser_v2.HAS_BS4", original)


def test_full_institution_crawler_stdlib_fallback(monkeypatch):
    from scripts.full_institution_crawler import FullInstitutionCrawler, HAS_BS4
    original = HAS_BS4
    monkeypatch.setattr("scripts.full_institution_crawler.HAS_BS4", False)
    try:
        html = (
            "<table><tr><th>name</th><th>code</th></tr>"
            "<tr><td>测试银行</td><td>ABC</td></tr></table>"
        )
        rows = FullInstitutionCrawler()._parse_html_table(html)
        assert rows == [["name", "code"], ["测试银行", "ABC"]]
    finally:
        monkeypatch.setattr("scripts.full_institution_crawler.HAS_BS4", original)


def test_scripts_package_does_not_require_bs4_import():
    """核心包入口不应在模块顶层强制 import bs4。"""
    init_src = (SCRIPTS / "__init__.py").read_text(encoding="utf-8")
    parser_src = (SCRIPTS / "adaptive_parser_v2.py").read_text(encoding="utf-8")
    crawler_src = (SCRIPTS / "full_institution_crawler.py").read_text(encoding="utf-8")
    assert "from bs4" not in init_src, "scripts/__init__.py 不应顶层强制导入 bs4"
    assert "HAS_BS4" in parser_src
    assert "HAS_BS4" in crawler_src


def test_runtests_uses_pytest_main():
    src = (ROOT / "runtests.py").read_text(encoding="utf-8")
    assert "os.execvp" not in src, "runtests.py 不应再用 os.execvp"
    assert "pytest.main" in src, "runtests.py 应改为同一进程内 pytest.main"


def test_pytest_ini_no_unknown_option():
    src = (ROOT / "pytest.ini").read_text(encoding="utf-8")
    assert "cache_dir" not in src, "pytest.ini 不应包含未知的 cache_dir 配置"


def test_package_uses_unique_temp_dir_and_cleans_up():
    import tempfile
    from pathlib import Path
    from scripts.crawl_packager import CrawlPackager, TEMP_DIR
    with tempfile.TemporaryDirectory() as out:
        packager = CrawlPackager(output_dir=out)
        p1 = packager.package([{"name": "A", "content": "x"}], zip_name="same_name")
        p2 = packager.package([{"name": "B", "content": "y"}], zip_name="same_name")
        assert Path(p1).exists()
        assert Path(p2).exists()
    leftovers = [p for p in TEMP_DIR.glob("same_name_*") if p.is_dir()]
    assert leftovers == [], f"临时目录应清理干净，残留: {leftovers}"
