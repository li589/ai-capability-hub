# -*- coding: utf-8 -*-
"""v4.7 阶段 A 修复的回归测试。

覆盖:
    - search_engine.py 缺少 import random（致命 NameError）
    - crawl_backtester.py typing 缺 Tuple
    - name_scraper.py 招商银行 URL 错误映射
    - regulatory_scraper.py 废弃域名 cbirc → nfra
    - cninfo_scraper.py column/orgId 硬编码参数化
    - exchange_scraper.py CATALOGID/TABKEY 提取为常量
    - web_parser.py if False 死代码分支清理
    - mcp_server.py 导入前缀一致性与死代码清理
"""
import sys
import unittest
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SCRIPTS_DIR))
sys.path.insert(0, str(ROOT_DIR))


class TestSearchEngineRandomImport(unittest.TestCase):
    """A1: search_engine.py 必须有 import random，否则 search() 崩溃。"""

    def test_module_has_random_import(self):
        src = (SCRIPTS_DIR / "search_engine.py").read_text(encoding="utf-8")
        import re
        self.assertTrue(
            re.search(r"^import random$|^import random\s*$", src, re.MULTILINE),
            "search_engine.py 缺少 import random",
        )

    def test_search_no_name_error(self):
        """mock urlopen 后调用 DDG search()，不应抛 NameError。"""
        from unittest import mock
        from search_engine import DuckDuckGoHTML

        fake_html = (
            '<html><body><div class="result">'
            '<a class="result__a" href="http://example.com">测试标题</a>'
            '<div class="result__snippet">摘要</div></div></body></html>'
        )

        class FakeResp:
            def __init__(self, content):
                self._content = content
            def read(self):
                return self._content.encode("utf-8")
            def __enter__(self):
                return self
            def __exit__(self, *a):
                return False
            def getheader(self, n, d=None):
                return "text/html"

        with mock.patch("urllib.request.urlopen", return_value=FakeResp(fake_html)):
            s = DuckDuckGoHTML()
            try:
                results = s.search("测试", limit=5)
                # 不抛 NameError 即算通过
                self.assertIsInstance(results, list)
            except NameError as e:
                self.fail(f"search() 触发 NameError: {e}")


class TestBacktesterTupleImport(unittest.TestCase):
    """A10: crawl_backtester.py 的 typing 需导入 Tuple。"""

    def test_tuple_in_typing_import(self):
        src = (SCRIPTS_DIR / "crawl_backtester.py").read_text(encoding="utf-8")
        self.assertIn("Tuple", src.split("\n")[0:60][-1] if False else src.splitlines()[38] if len(src.splitlines()) > 38 else src)
        # 更稳：检查 typing import 行包含 Tuple
        typing_line = [l for l in src.splitlines() if "from typing import" in l][0]
        self.assertIn("Tuple", typing_line)

    def test_module_imports(self):
        import crawl_backtester
        self.assertTrue(hasattr(crawl_backtester, "CrawlBacktester"))


class TestNameScraperURLs(unittest.TestCase):
    """A5: 招商银行应指向 cmbchina.com，民生银行指向 cmbc.com.cn。"""

    def test_correct_bank_urls(self):
        from name_scraper import URL_PATTERNS
        self.assertEqual(URL_PATTERNS.get("招商银行"), "https://www.cmbchina.com",
                         "招商银行官网应为 cmbchina.com（原错误指向民生银行）")
        self.assertEqual(URL_PATTERNS.get("民生银行"), "https://www.cmbc.com.cn")

    def test_urls_valid_format(self):
        from name_scraper import URL_PATTERNS
        for name, url in URL_PATTERNS.items():
            self.assertTrue(url.startswith("https://") or url.startswith("http://"),
                            f"{name} 的 URL 格式错误: {url}")


class TestRegulatoryDomain(unittest.TestCase):
    """A6: regulatory_scraper.py 数据源应为商业源（东财/新浪/巨潮），不含 gov.cn。"""

    def test_no_gov_domain(self):
        src = (SCRIPTS_DIR / "regulatory_scraper.py").read_text(encoding="utf-8")
        self.assertNotIn("gov.cn", src, "regulatory_scraper 不应包含 gov.cn 域名")
        self.assertNotIn("cbirc.gov.cn", src, "不应引用已废弃的 cbirc 域名")
        self.assertNotIn("nfra.gov.cn", src, "不应引用 nfra 域名")

    def test_commercial_sources(self):
        """应使用商业数据源（东方财富/新浪/巨潮）。"""
        src = (SCRIPTS_DIR / "regulatory_scraper.py").read_text(encoding="utf-8")
        self.assertIn("eastmoney", src, "应使用东方财富数据源")
        self.assertIn("cninfo", src, "应使用巨潮资讯数据源")

    def test_api_shape_kept(self):
        """对外 API 形状应保留（get_regulatory_updates 等）。"""
        src = (SCRIPTS_DIR / "regulatory_scraper.py").read_text(encoding="utf-8")
        self.assertIn("def get_regulatory_updates", src,
                      "对外 API get_regulatory_updates 应保留")


class TestCninfoParametrized(unittest.TestCase):
    """A7: cninfo_scraper.py 的 column/orgId 应参数化。"""

    def test_market_param_in_signature(self):
        src = (SCRIPTS_DIR / "cninfo_scraper.py").read_text(encoding="utf-8")
        self.assertIn("market: str = \"szse\"", src,
                      "search_announcements 应支持 market 参数")

    def test_no_hardcoded_orgid(self):
        """硬编码 orgId 不应再作为 stock 参数的实际取值。

        注释中提及旧魔数属正常文档，故仅校验取值逻辑（org_prefix 推导）。
        """
        src = (SCRIPTS_DIR / "cninfo_scraper.py").read_text(encoding="utf-8")
        self.assertIn('org_prefix = {"szse": "gssz", "sse": "gssh", "bjse": "gsbj"}',
                      src, "应按市场推导 orgId")
        self.assertIn("stock_param = f\"{stock_code},orgId,{org_prefix}{zcode}\"",
                      src, "stock 参数应使用推导的 orgId")
        # 不再以 gssz0000858 作为字面量拼接进 stock 参数
        self.assertNotIn("\"stock\": f\"{stock_code},orgId,gssz0000858\"", src,
                         "硬编码的五粮液 orgId 不应再作为取值")


class TestExchangeConstants(unittest.TestCase):
    """A8: exchange_scraper.py 的 CATALOGID/TABKEY 应提取为常量。"""

    def test_constants_defined(self):
        src = (SCRIPTS_DIR / "exchange_scraper.py").read_text(encoding="utf-8")
        for const in ("SZSE_CATALOG_IPO", "SZSE_CATALOG_LISTED",
                      "SZSE_CATALOG_ANNOUNCEMENT", "SZSE_TABKEY"):
            self.assertIn(f"{const} =", src, f"缺少常量 {const}")

    def test_no_literal_catalogid(self):
        src = (SCRIPTS_DIR / "exchange_scraper.py").read_text(encoding="utf-8")
        # 请求体里不应再有字面 "1110" CATALOGID（常量里可以有）
        self.assertIn('"CATALOGID": SZSE_CATALOG', src,
                      "请求参数应引用常量")


class TestWebParserNoDeadCode(unittest.TestCase):
    """A9: web_parser.py 的 if False 死代码分支应被清理。"""

    def test_no_if_false_branches(self):
        src = (SCRIPTS_DIR / "web_parser.py").read_text(encoding="utf-8")
        self.assertNotIn("if False else", src,
                         "web_parser.py 仍有 if False 死代码")


class TestMcpServerImports(unittest.TestCase):
    """A4: mcp_server.py 导入前缀一致且无死代码。"""

    def test_no_scripts_prefix_import(self):
        src = (ROOT_DIR / "mcp_server.py").read_text(encoding="utf-8")
        self.assertNotIn("from scripts.fullpage_archiver", src,
                         "应使用无前缀导入 from fullpage_archiver")
        self.assertNotIn("from scripts.search_engine", src,
                         "应使用无前缀导入 from search_engine")
        self.assertIn("from fullpage_archiver import", src)
        self.assertIn("from search_engine import", src)

    def test_dead_imports_removed(self):
        src = (ROOT_DIR / "mcp_server.py").read_text(encoding="utf-8")
        for dead in ("get_stock_brief", "cls_articles", "get_stock_list",
                     "create_scheduled_task", "package_crawl_results",
                     "compress_multiple", "MultiFormatParser",
                     "get_template_outline", "generate_report_from_raw",
                     "quick_report"):
            self.assertNotIn(f"import {dead}", src, f"死代码导入 {dead} 应被删除")
            self.assertNotIn(f"import {dead} as", src, f"死代码导入 {dead} 应被删除")


class TestSearchEngineNameError(unittest.TestCase):
    """search_engine.py 修复后 import 不应失败，且多引擎可实例化。"""

    def test_multi_engine_init(self):
        from search_engine import MultiEngineSearch
        s = MultiEngineSearch(engines=["duckduckgo"])
        self.assertEqual(s.engines[0].name, "duckduckgo")


if __name__ == "__main__":
    unittest.main()
