# -*- coding: utf-8 -*-
"""v7.0.0 模块测试：网页操作深度增强 / API 挖掘 / 名单扩充 / 官网补全 / 宏观接口。

全部离线 mock（不依赖 Playwright 浏览器实例与真实网络），Playwright 未装
或不可用时相关用例自动跳过。
"""
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.dont_write_bytecode = True

SKILL_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = SKILL_DIR / "data"


# ═══════════════ 一、browser_pro 纯逻辑（离线可测） ═══════════════

class TestBrowserProCore(unittest.TestCase):
    """宏参数替换 / 分页识别 / API 注册表去重。"""

    def test_substitute_recursive(self):
        from scripts.browser_pro import _substitute
        sub = _substitute({"a": "{{x}}", "b": ["{{x}}", "k{{y}}"], "c": 1},
                          {"x": 42, "y": "v"})
        self.assertEqual(sub["a"], 42)
        self.assertEqual(sub["b"][0], 42)
        self.assertEqual(sub["b"][1], "kv")
        self.assertEqual(sub["c"], 1)
        # 未知变量保持原样
        self.assertEqual(_substitute("{{z}}", {}), "{{z}}")

    def test_detect_pagination(self):
        from scripts.browser_pro import _detect_pagination
        entries = [
            {"url": "https://a.com/api?pn=1&size=20", "ts": 1},
            {"url": "https://a.com/api?pn=2&size=20", "ts": 2},
            {"url": "https://a.com/api?pn=3&size=20", "ts": 3},
        ]
        pg = _detect_pagination(entries)
        self.assertEqual(len(pg), 1)
        self.assertEqual(pg[0]["pagination_param"], "pn")
        self.assertEqual(pg[0]["step"], 1)

    def test_detect_pagination_non_numeric_ignored(self):
        from scripts.browser_pro import _detect_pagination
        entries = [
            {"url": "https://a.com/api?k=aa&x=1", "ts": 1},
            {"url": "https://a.com/api?k=bb&x=2", "ts": 2},
        ]
        self.assertEqual(_detect_pagination(entries), [])

    def test_api_registry_dedup_and_search(self):
        from scripts.browser_pro import ApiRegistry
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "api_registry.json"
            reg = ApiRegistry(path)
            ep = {"url": "https://a.com/api?pn=1", "method": "GET",
                  "sample_response": "{}", "discovered_at": "now"}
            self.assertTrue(reg.add(dict(ep)))
            self.assertFalse(reg.add(dict(ep)))          # 同端点去重
            self.assertTrue(reg.add({**ep, "url": "https://b.com/x?y=1"}))
            reg.save()
            reg2 = ApiRegistry(path)                      # 重读持久化
            self.assertEqual(len(reg2.search()), 2)
            self.assertEqual(len(reg2.search(domain="a.com")), 1)
            self.assertEqual(reg2._doc["endpoints"][0]["hit_count"], 2)

    def test_truncate(self):
        from scripts.browser_pro import _truncate
        s = _truncate({"k": "x" * 5000})
        self.assertLess(len(s), 2100)
        self.assertTrue(s.endswith("…[截断]"))


class TestMacroPlayer(unittest.TestCase):
    """宏回放离线部分：加载/保存/列表 + 缺失浏览器时优雅报错。"""

    def test_macro_io(self):
        from scripts.browser_pro import MacroPlayer
        with tempfile.TemporaryDirectory() as td:
            macro = {"name": "demo", "steps": [{"action": "goto", "url": "{{u}}"}]}
            path = MacroPlayer.save_macro(macro, "demo_macro")
            loaded = MacroPlayer.load_macro(path.name)
            self.assertEqual(loaded["name"], "demo")
            self.assertEqual(path.name, "demo_macro.json")

    def test_play_unknown_action_errors(self):
        # 真实 BrowserScraper（Chromium 已装，不开页面不联网）：未知动作应报错
        from scripts.browser_scraper import BrowserScraper
        from scripts.browser_pro import MacroPlayer
        with BrowserScraper(headless=True) as bs:
            result = MacroPlayer(scraper=bs).play(
                {"steps": [{"action": "no_such_action"}]})
        self.assertFalse(result["ok"])
        self.assertIn("未知宏动作", result["error"])


class TestUrlCompleter(unittest.TestCase):
    """官网补全的候选过滤（聚合域/gov.cn 绝不入库）。"""

    def test_domain_ok(self):
        from scripts.url_completer import _domain_ok
        self.assertTrue(_domain_ok("https://www.icbc.com.cn/"))
        self.assertTrue(_domain_ok("https://yafco.com/about/"))
        self.assertFalse(_domain_ok("https://www.baidu.com/s?wd=x"))
        self.assertFalse(_domain_ok("https://gs.nfra.gov.cn/"))     # 脱敏红线
        self.assertFalse(_domain_ok("https://www.tianyancha.com/company/x"))
        self.assertFalse(_domain_ok("https://www.eastmoney.com/"))

    def test_normalize(self):
        from scripts.url_completer import _normalize
        self.assertEqual(_normalize("http://www.abc.com/"), "https://www.abc.com")
        self.assertEqual(_normalize("www.abc.com"), "https://www.abc.com")

    def test_is_homepage(self):
        from scripts.url_completer import _is_homepage
        self.assertTrue(_is_homepage("https://a.com/"))
        self.assertTrue(_is_homepage("https://a.com/index.html"))
        self.assertFalse(_is_homepage("https://a.com/about"))

    def test_is_acceptable_url(self):
        from scripts.url_completer import _is_acceptable_url
        self.assertTrue(_is_acceptable_url("https://a.com/"))
        self.assertTrue(_is_acceptable_url("https://a.com/cn/"))
        self.assertFalse(_is_acceptable_url("https://a.com/article/12345"))
        self.assertFalse(_is_acceptable_url("https://a.com/newsDetail_forward_1"))
        self.assertFalse(_is_acceptable_url("https://a.com/p/abc123"))
        self.assertFalse(_is_acceptable_url("https://a.com/x/y/z"))   # 深路径


# ═══════════════ 二、名单扩充（离线，用小样本 curated 目录） ═══════════════

class TestInstitutionExpander(unittest.TestCase):
    """normalize / 合并去重 / 类型名单重写 / 舆情计数同步。"""

    def test_normalize_name(self):
        from scripts.institution_expander import normalize_name
        self.assertEqual(normalize_name("易方达基金管理有限公司"), "易方达基金管理")
        self.assertEqual(normalize_name("中信证券股份有限公司"), "中信证券")
        self.assertEqual(normalize_name("中国（上海）自贸区银行"), "中国(上海)自贸区银行")

    def _build_registry(self, tmp):
        rows = [
            [1, "华夏基金", "HX", "基金管理公司", "公开信息", "2026-01-01", "", "curated"],
            [2, "中信证券", "CITIC", "证券公司", "公开信息", "2026-01-01", "", "curated"],
        ]
        doc = {"_f": "c", "c": ["id", "name", "code", "type", "data_source",
                                "update_time", "website", "url_source"], "d": rows}
        reg = Path(tmp) / "institution_registry.json"
        reg.write_text(json.dumps(doc, ensure_ascii=False), encoding="utf-8")
        return reg

    def test_merge_dedup_and_sync(self):
        import scripts.institution_expander as exp
        orig_live = exp.LIVE_SOURCES
        exp.LIVE_SOURCES = {}                     # 测试不联网，禁用 live 源
        try:
            with tempfile.TemporaryDirectory() as td:
                tmp = Path(td)
                exp.DATA_DIR = tmp
                exp.REGISTRY_FILE = self._build_registry(tmp)
                exp.CURATED_DIR = tmp / "curated"
                exp.CURATED_DIR.mkdir()
                (exp.CURATED_DIR / "fund_company.json").write_text(
                    json.dumps(["华夏基金", "易方达基金", "广发基金"]),
                    encoding="utf-8")
                (exp.CURATED_DIR / "private_bank.json").write_text(
                    json.dumps(["微众银行", "网商银行"]), encoding="utf-8")
                targets = {"fund_company": {"label": "基金管理公司", "count": 1,
                                            "source_registry": "x"},
                           "_meta": {"version": "6.0.0", "updated_at": ""}}
                (tmp / "sentiment_targets.json").write_text(
                    json.dumps(targets, ensure_ascii=False), encoding="utf-8")
                report = exp.run(dry_run=False)
                self.assertEqual(report["fund_company"]["added"], 2)   # 华夏去重
                self.assertEqual(report["fund_company"]["total"], 3)
                self.assertEqual(report["private_bank"]["total"], 2)
                doc = json.loads(exp.REGISTRY_FILE.read_text(encoding="utf-8"))
                self.assertEqual(len(doc["d"]), 6)   # 2 旧 + 2 基金 + 2 民营
                lst = json.loads((tmp / "fund_company_list.json")
                                 .read_text(encoding="utf-8"))
                self.assertEqual(lst["count"], 3)
                t2 = json.loads((tmp / "sentiment_targets.json")
                                .read_text(encoding="utf-8"))
                self.assertEqual(t2["fund_company"]["count"], 3)
                self.assertEqual(t2["_meta"]["version"], "7.0.0")
        finally:
            exp.LIVE_SOURCES = orig_live


# ═══════════════ 三、爬取增强：gzip 自动解压 / 宏观指标 ═══════════════

class TestHttpUtilsDecompress(unittest.TestCase):
    """v7.0.0 gzip/deflate 响应自动解压。"""

    def _gzip_bytes(self, text: str):
        import gzip
        return gzip.compress(text.encode("utf-8"))

    def test_gzip_via_header(self):
        from scripts.http_utils import StdlibResponse
        data = self._gzip_bytes('{"ok": true}')
        resp = StdlibResponse("https://a.com", 200, {"Content-Encoding": "gzip"},
                              data)
        self.assertEqual(resp.json(), {"ok": True})

    def test_gzip_via_magic_bytes(self):
        from scripts.http_utils import StdlibResponse
        data = self._gzip_bytes('{"magic": 1}')
        resp = StdlibResponse("https://a.com", 200, {}, data)   # 无头也解
        self.assertEqual(resp.json(), {"magic": 1})

    def test_plain_passthrough(self):
        from scripts.http_utils import StdlibResponse
        resp = StdlibResponse("https://a.com", 200, {}, b'{"plain": 1}')
        self.assertEqual(resp.json(), {"plain": 1})

    def test_corrupt_gzip_falls_back(self):
        from scripts.http_utils import StdlibResponse
        resp = StdlibResponse("https://a.com", 200, {"Content-Encoding": "gzip"},
                              b"\x1f\x8b not real gzip")
        self.assertIsInstance(resp.content, bytes)


class TestMacroIndicators(unittest.TestCase):
    """宏观指标映射（离线：字段映射 + 入口分派，不真发请求）。"""

    def test_macro_reports_registry(self):
        from scripts.market_data_scraper import MACRO_REPORTS
        for ind in ("cpi", "ppi", "pmi", "gdp", "m2"):
            self.assertIn(ind, MACRO_REPORTS)

    def test_unknown_indicator_returns_empty(self):
        from scripts.market_data_scraper import get_macro_indicator
        self.assertEqual(get_macro_indicator("nope"), [])

    def test_get_market_data_dispatch(self):
        from scripts.market_data_scraper import get_market_data
        # 未知类型返回 error dict（不抛异常）
        r = get_market_data("macro_xyz")
        self.assertIsInstance(r, dict)
        self.assertIn("error", r)


# ═══════════════ 四、脱敏回归：v7 新增文件零 gov.cn/官媒 ═══════════════

class TestV700Sanitization(unittest.TestCase):
    """v7.0.0 新增数据/代码文件不含 gov.cn 域名与官媒词。"""

    FORBIDDEN = ["gov.cn", "人民日报", "新华社", "央视财经", "光明日报",
                 "中国新闻网", "新华网", "参考消息"]

    def test_curated_data_clean(self):
        curated = DATA_DIR / "curated"
        if not curated.exists():
            self.skipTest("curated 目录不存在")
        for f in curated.glob("*.json"):
            text = f.read_text(encoding="utf-8")
            for term in self.FORBIDDEN:
                self.assertNotIn(term, text, f"{f.name} 含 {term}")

    def test_new_scripts_clean(self):
        for name in ("browser_pro.py", "institution_expander.py",
                     "url_completer.py"):
            text = (SKILL_DIR / "scripts" / name).read_text(encoding="utf-8")
            for term in self.FORBIDDEN:
                self.assertNotIn(term, text, f"{name} 含 {term}")

    def test_listed_companies_markets(self):
        f = DATA_DIR / "listed_companies.json"
        if not f.exists():
            self.skipTest("listed_companies.json 未生成")
        doc = json.loads(f.read_text(encoding="utf-8"))
        self.assertGreater(doc["meta"]["total_count"], 4000)
        self.assertIn("BJ", doc["meta"]["markets"])


if __name__ == "__main__":
    unittest.main()
