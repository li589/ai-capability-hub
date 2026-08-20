# -*- coding: utf-8 -*-
"""v6.0.0 模块测试：脱敏回归 / 解析智能 / 浏览器新行为 / HTML·PDF 导出 / zip 增强。

全部离线 mock，无网络请求。
"""
import sys
import json
import shutil
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.dont_write_bytecode = True

import unittest

SKILL_DIR = Path(__file__).resolve().parent.parent

# 官方媒体 / 政府实体（脱敏后应全项目零命中）
FORBIDDEN_TERMS = [
    "gov.cn", "人民日报", "新华社", "央视财经", "参考消息", "光明日报",
    "新华网财经", "中国新闻网财经",
]
GOV_ENTITY_TERMS = ["国家金融监督管理总局", "中国人民银行", "中国证券监督管理委员会"]


class TestSanitization(unittest.TestCase):
    """脱敏回归：代码与数据文件零残留。"""

    def _scan(self, patterns, files):
        hits = []
        for p in files:
            try:
                text = p.read_text(encoding="utf-8", errors="replace")
            except Exception:
                continue
            for pat in patterns:
                if pat in text:
                    hits.append((p.name, pat))
        return hits

    def test_no_forbidden_terms_in_py(self):
        py_files = [p for p in (SKILL_DIR / "scripts").rglob("*.py")]
        hits = self._scan(FORBIDDEN_TERMS, py_files)
        self.assertEqual([], hits, f"scripts/ 存在禁止词: {hits}")

    def test_no_forbidden_terms_in_json(self):
        json_files = list((SKILL_DIR / "data").glob("*.json"))
        hits = self._scan(FORBIDDEN_TERMS, json_files)
        self.assertEqual([], hits, f"data/ 存在禁止词: {hits}")

    def test_no_gov_entity_in_registry(self):
        reg = json.loads((SKILL_DIR / "data" / "institution_registry.json")
                         .read_text(encoding="utf-8"))
        src = json.dumps(reg, ensure_ascii=False)
        for term in GOV_ENTITY_TERMS:
            self.assertNotIn(term, src, f"机构注册表含 {term}")

    def test_sources_no_official_media(self):
        ss = json.loads((SKILL_DIR / "data" / "sentiment_sources.json")
                        .read_text(encoding="utf-8"))
        names = {s.get("name", "") for cat in ss
                 if isinstance(ss[cat], list)
                 for s in ss[cat] if isinstance(s, dict)}
        forbidden = {"人民日报", "新华社", "央视财经", "经济日报", "参考消息",
                     "新华网财经", "中国新闻网财经", "光明日报经济", "中国财经报",
                     "中国证券报", "上海证券报", "证券时报", "证券日报", "金融时报"}
        self.assertEqual(set(), names & forbidden,
                         f"媒体源仍含官媒: {names & forbidden}")

    def test_targets_no_government(self):
        tg = json.loads((SKILL_DIR / "data" / "sentiment_targets.json")
                        .read_text(encoding="utf-8"))
        self.assertNotIn("local_government", tg, "目标库仍含 local_government")

    def test_regulatory_scraper_no_gov(self):
        src = (SKILL_DIR / "scripts" / "regulatory_scraper.py").read_text(encoding="utf-8")
        self.assertNotIn("gov.cn", src)
        self.assertNotIn("cbirc.gov.cn", src)
        self.assertNotIn("nfra.gov.cn", src)

    def test_meta_version_is_700(self):
        ss = json.loads((SKILL_DIR / "data" / "sentiment_sources.json")
                        .read_text(encoding="utf-8"))
        self.assertEqual("7.0.0", ss["_meta"]["version"])
        tg = json.loads((SKILL_DIR / "data" / "sentiment_targets.json")
                        .read_text(encoding="utf-8"))
        self.assertEqual("7.0.0", tg["_meta"]["version"])

    def test_skill_version_is_700(self):
        skill = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
        # v7.2.0 起版本断言由 test_meta_sync / test_v720 接管，此处跟随最新版本
        self.assertIn("version: 7.2.0", skill)


class TestParsingSmart(unittest.TestCase):
    """解析智能：正文抽取 / JSON-LD 文章类型。"""

    def test_extract_main_content(self):
        from scripts.web_parser import extract_main_content
        html = (
            "<html><head><title>测试标题</title></head><body>"
            "<nav>导航菜单</nav>"
            "<article><p>这是正文第一段，包含足够长度的金融分析内容，用于测试正文抽取算法，"
            "涵盖了市场走势、公司基本面与行业竞争格局等多个维度。"
            "<a href='http://x'>链接</a></p>"
            "<p>这是正文第二段，继续讨论投资策略与风险管理建议。</p></article>"
            "<footer>版权信息</footer></body></html>"
        )
        r = extract_main_content(html)
        self.assertIn("这是正文第一段", r["content"])
        self.assertIn("投资策略", r["content"])
        self.assertEqual("测试标题", r["title"])
        self.assertGreater(r["text_len"], 60)

    def test_extract_article_from_jsonld(self):
        from scripts.web_parser import extract_product_from_jsonld
        ld = [{
            "@type": "NewsArticle",
            "headline": "某公司发布半年报",
            "datePublished": "2026-08-01T10:00:00+08:00",
            "author": {"name": "分析师甲"},
            "image": {"url": "https://img.example.com/a.png"},
            "articleBody": "正文内容……",
        }]
        r = extract_product_from_jsonld(ld)
        self.assertEqual("某公司发布半年报", r.get("article_title"))
        self.assertEqual("分析师甲", r.get("article_author"))
        self.assertEqual("2026-08-01T10:00:00", r.get("article_date"))

    def test_selector_cache_confidence_decay(self):
        """连续失败 ≥3 次的缓存选择器应被淘汰。"""
        from scripts.web_parser import AdaptiveSelectorMatcher

        class FakePage:
            """按选择器名返回结果：good 命中，其他为空。"""

            def __init__(self, good_sel):
                self.good_sel = good_sel

            def css_first(self, sel):
                if sel == self.good_sel:
                    return object()
                return None

        class AllFailPage:
            def css_first(self, sel):
                return None

        # 场景 1：bad 选择器持续失败 → 计数累积，flush 时淘汰
        m = AdaptiveSelectorMatcher("decaytest.example",
                                    {"title": ["bad1", "bad2", "good"]})
        fail_page = AllFailPage()
        for _ in range(3):
            m.css_first(fail_page, "title")
        self.assertEqual(3, m._failures["title"].get("bad1", 0))
        self.assertEqual(3, m._failures["title"].get("bad2", 0))

        cache_file = SKILL_DIR / "data" / "selector_cache" / "decaytest_example.json"
        if cache_file.exists():
            cache_file.unlink()
        try:
            # 无任何成功 → 不写缓存（避免缓存污染）
            m.flush()
            self.assertFalse(cache_file.exists(),
                             "全部失败时不应写入缓存")

            # 场景 2：good 成功 + bad 已失败 ≥3 → flush 仅保留 good
            m2 = AdaptiveSelectorMatcher("decaytest.example",
                                         {"title": ["bad1", "bad2", "good"]})
            ok_page = FakePage(good_sel="good")
            for _ in range(3):
                m2.css_first(ok_page, "title")
                m2.css_first(fail_page, "title")  # 坏选择器继续失败
            self.assertEqual("good", m2._successful["title"])
            m2.flush()
            self.assertTrue(cache_file.exists())
            data = json.loads(cache_file.read_text(encoding="utf-8"))
            sels = data.get("selectors", {}).get("title", [])
            self.assertNotIn("bad1", sels)
            self.assertNotIn("bad2", sels)
            self.assertIn("good", sels)
        finally:
            if cache_file.exists():
                cache_file.unlink()


class TestBrowserV600(unittest.TestCase):
    """浏览器 v6.0.0 新行为（离线断言，无需 Playwright）。"""

    def test_scroll_modes_defined(self):
        from scripts.browser_scraper import BrowserScraper, PLAYWRIGHT_AVAILABLE
        self.assertTrue(hasattr(BrowserScraper, "SCROLL_MODES"))
        self.assertEqual(
            {"fast_browse", "slow_read", "segmented", "rewind"},
            set(BrowserScraper.SCROLL_MODES))

    def test_captcha_signs_defined(self):
        from scripts.browser_scraper import BrowserScraper
        signs = BrowserScraper.CAPTCHA_TEXT_SIGNS
        self.assertIn("人机验证", signs)
        self.assertIn("captcha", signs)

    def test_humanlike_fetch_new_params(self):
        import inspect
        from scripts.browser_scraper import BrowserScraper
        sig = inspect.signature(BrowserScraper.humanlike_fetch)
        for p in ["think_time", "hover", "tab_switch", "captcha_handoff", "include_iframes"]:
            self.assertIn(p, sig.parameters, f"humanlike_fetch 缺参数 {p}")

    def test_fetch_new_params(self):
        import inspect
        from scripts.browser_scraper import BrowserScraper
        sig = inspect.signature(BrowserScraper.fetch)
        for p in ["captcha_handoff", "include_iframes"]:
            self.assertIn(p, sig.parameters, f"fetch 缺参数 {p}")

    def test_detect_captcha_with_mock_page(self):
        """验证码检测应截图并返回命中特征（mock page，真实尺寸截图）。"""
        from scripts.browser_scraper import BrowserScraper
        bs = BrowserScraper.__new__(BrowserScraper)

        class FakePage:
            def text_content(self, sel):
                return "请输入验证码完成安全验证，请稍后再试"

            def screenshot(self, path):
                Path(path).parent.mkdir(parents=True, exist_ok=True)
                # 真实截图 ≥100B（v7.0.0 起空截图会被清理，模拟真实尺寸）
                Path(path).write_bytes(b"f" * 150)

        shot_dir = SKILL_DIR / "data" / "screenshots"
        try:
            cap = bs._detect_captcha(FakePage(), url="https://www.example.com/x")
            self.assertIsNotNone(cap)
            self.assertIn(cap["captcha"], BrowserScraper.CAPTCHA_TEXT_SIGNS)
            self.assertTrue(cap["screenshot"])
            self.assertGreater(Path(cap["screenshot"]).stat().st_size, 100)
        finally:
            shutil.rmtree(shot_dir, ignore_errors=True)   # 不留测试产物

    def test_storage_state_paths(self):
        from scripts.browser_scraper import BROWSER_STATE_FILE
        self.assertTrue(str(BROWSER_STATE_FILE).endswith("state.json"))
        self.assertIn("browser_state", str(BROWSER_STATE_FILE))


class TestHtmlExporter(unittest.TestCase):
    """HtmlExporter：网页版报告渲染与落盘。"""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _sample_data(self):
        class Broker:
            rating = "买入"
            title = "深度研究报告"
            publish_date = "2026-08-01"
            broker_name = "某券商"
            analyst = "分析师甲"
            target_price = 12.5
            url = "https://www.example.com/research"

        class Announcement:
            title = "2026年半年度报告"
            publish_date = "2026-08-10"
            announcement_type = "定期报告"
            url = "https://www.example.com/ann"

        return {
            "summary": {"stock_name": "示例股份", "periodic_count": 2,
                        "broker_count": 1, "announcement_count": 1,
                        "has_buy_rating": True},
            "periodic_reports": [],
            "broker_reports": [Broker()],
            "announcements": [Announcement()],
        }

    def test_render_html_contains_sections(self):
        from scripts.report_exporter import HtmlExporter
        html = HtmlExporter().render_html(self._sample_data(), "600000")
        self.assertIn("示例股份", html)
        self.assertIn("报告概览", html)
        self.assertIn("券商研报", html)
        self.assertIn("评级分布", html)
        self.assertIn("某券商", html)
        self.assertIn("https://www.example.com/ann", html)
        self.assertIn("<style>", html)

    def test_export_writes_file(self):
        from scripts.report_exporter import HtmlExporter
        out = str(Path(self.tmp) / "test_report.html")
        path = HtmlExporter().export_comprehensive_report(self._sample_data(), "600000", out)
        self.assertTrue(Path(path).exists())
        self.assertIn("<!DOCTYPE html>", Path(path).read_text(encoding="utf-8"))


class TestPdfExporterFallback(unittest.TestCase):
    """PDFExporter：无 Playwright 时 fallback 返回 HTML 路径（不崩溃）。"""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_fallback_returns_html_path(self):
        from scripts.report_exporter import PDFExporter
        ex = PDFExporter()
        out = str(Path(self.tmp) / "r.pdf")
        data = {
            "summary": {"stock_name": "测试"},
            "periodic_reports": [], "broker_reports": [], "announcements": [],
        }
        result = ex.export_comprehensive_report(data, "T0001", out)
        # 环境无 Playwright 时返回 HTML；有 Playwright 但渲染失败也返回 HTML
        self.assertTrue(result.endswith(".html") or result.endswith(".pdf"))
        if result.endswith(".html"):
            self.assertTrue(Path(result).exists())


class TestCrawlPackagerV600(unittest.TestCase):
    """zip v6.0.0：进度回调 / 增量去重 / metadata hashes。"""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_progress_callback(self):
        from scripts.crawl_packager import CrawlPackager
        items = [{"name": "A", "content": "内容A", "category": "银行"},
                 {"name": "B", "content": "内容B", "category": "基金"}]
        calls = []
        packager = CrawlPackager(output_dir=self.tmp)
        path = packager.package(
            items, zip_name="prog_test",
            progress_callback=lambda d, t, n: calls.append((d, t, n)))
        self.assertTrue(Path(path).exists())
        self.assertEqual(2, len(calls))
        self.assertEqual((2, 2), (calls[-1][0], calls[-1][1]))

    def test_metadata_has_hashes(self):
        from scripts.crawl_packager import CrawlPackager
        items = [{"name": "A", "content": "唯一内容XYZ", "category": "银行"}]
        packager = CrawlPackager(output_dir=self.tmp)
        path = packager.package(items, zip_name="hash_test")
        import zipfile
        with zipfile.ZipFile(path) as zf:
            meta = json.loads(zf.read("metadata.json").decode("utf-8"))
        self.assertIn("item_hashes", meta)
        self.assertEqual(1, len(meta["item_hashes"]))
        self.assertIn("hash", meta["item_hashes"][0])
        self.assertEqual(32, len(meta["item_hashes"][0]["hash"]))

    def test_incremental_skips_duplicates(self):
        from scripts.crawl_packager import CrawlPackager
        items = [{"name": "A", "content": "相同内容", "category": "银行"},
                 {"name": "B", "content": "相同内容", "category": "基金"},
                 {"name": "C", "content": "新内容", "category": "基金"}]
        packager = CrawlPackager(output_dir=self.tmp)
        first = packager.package(items[:2], zip_name="inc_first")
        # 增量：C 是新内容，A/B 应被跳过
        path, skipped = packager.package_incremental(
            items, previous_zip=first, zip_name="inc_second")
        self.assertEqual(2, skipped)
        self.assertTrue(Path(path).exists())
        import zipfile
        with zipfile.ZipFile(path) as zf:
            names = zf.namelist()
        self.assertTrue(any("新内容" in "" and "C" in n for n in names)
                        or any("C" in n for n in names))

    def test_failed_items_written(self):
        """package_batch_crawl 失败项应写入包内 failed.json（mock 爬取器）。"""
        from scripts.crawl_packager import CrawlPackager
        import sys

        class FakeCrawler:
            def crawl_by_names(self, inst_list):
                return [{"name": "好机构", "content": "正常内容", "success": True},
                        {"name": "坏机构", "content": "", "success": False}]

        sys.modules["batch_institution_crawler"] = type(
            "M", (), {"BatchInstitutionCrawler": lambda *a, **k: FakeCrawler()})()
        try:
            packager = CrawlPackager(output_dir=self.tmp)
            path = packager.package_batch_crawl(names="好机构,坏机构", zip_name="fail_test")
        finally:
            sys.modules.pop("batch_institution_crawler", None)
        self.assertTrue(Path(path).exists())
        import zipfile
        with zipfile.ZipFile(path) as zf:
            names = zf.namelist()
        self.assertTrue(any("failed" in n for n in names),
                        f"包内应含失败清单, 实际: {names}")


if __name__ == "__main__":
    unittest.main()
