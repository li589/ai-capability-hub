# -*- coding: utf-8 -*-
"""
爬虫性能优化模块测试
"""

import os
import sys
import time
import pytest
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))


# ============================================================
# DNS 缓存测试
# ============================================================

class TestDNSCache:
    """DNS 缓存测试"""

    def test_cache_resolve(self):
        """测试 DNS 缓存解析"""
        from crawl_performance import DNSCache

        cache = DNSCache(ttl=60)
        # 首次解析
        ip1 = cache.resolve("localhost")
        # 缓存命中
        ip2 = cache.resolve("localhost")

        assert ip1 is not None
        assert ip1 == ip2

    def test_cache_ttl(self):
        """测试缓存过期"""
        from crawl_performance import DNSCache

        cache = DNSCache(ttl=0)  # 立即过期
        ip1 = cache.resolve("localhost")
        ip2 = cache.resolve("localhost")

        # 即使 TTL=0，相同域名应该能解析
        assert ip1 is not None

    def test_cache_clear(self):
        """测试清除缓存"""
        from crawl_performance import DNSCache

        cache = DNSCache()
        cache.resolve("localhost")
        assert len(cache._cache) > 0

        cache.clear()
        assert len(cache._cache) == 0


# ============================================================
# CrawlResult 测试
# ============================================================

class TestCrawlResult:
    """CrawlResult 测试"""

    def test_success_result(self):
        """测试成功结果"""
        from crawl_performance import CrawlResult

        result = CrawlResult(
            url="https://example.com",
            success=True,
            status_code=200,
            text="Hello",
            elapsed=0.5,
        )

        assert result.success == True
        assert result.status_code == 200
        assert result.text == "Hello"
        assert result.from_cache == False

    def test_failure_result(self):
        """测试失败结果"""
        from crawl_performance import CrawlResult

        result = CrawlResult(
            url="https://example.com",
            success=False,
            error="Connection timeout",
        )

        assert result.success == False
        assert result.error == "Connection timeout"


# ============================================================
# PerformanceCrawler 测试
# ============================================================

class TestPerformanceCrawler:
    """PerformanceCrawler 测试"""

    def test_init(self):
        """测试初始化"""
        from crawl_performance import PerformanceCrawler

        crawler = PerformanceCrawler(max_workers=3, timeout=10)
        assert crawler.max_workers == 3
        assert crawler.timeout == 10

    def test_cache_mechanism(self):
        """测试缓存机制"""
        from crawl_performance import PerformanceCrawler, CrawlResult

        crawler = PerformanceCrawler()

        # 手动设置缓存
        result = CrawlResult(
            url="https://example.com",
            success=True,
            status_code=200,
            text="cached",
        )
        crawler._set_cache("https://example.com", result)

        # 从缓存获取
        cached = crawler._get_from_cache("https://example.com")
        assert cached is not None
        assert cached.text == "cached"

    def test_cache_miss(self):
        """测试缓存未命中"""
        from crawl_performance import PerformanceCrawler

        crawler = PerformanceCrawler()
        cached = crawler._get_from_cache("https://nonexistent.com")
        assert cached is None

    def test_stats(self):
        """测试统计信息"""
        from crawl_performance import PerformanceCrawler

        crawler = PerformanceCrawler()
        stats = crawler.get_stats()

        assert 'total_requests' in stats
        assert 'cache_hits' in stats
        assert 'errors' in stats
        assert 'cache_hit_rate' in stats
        assert 'avg_response_time' in stats

    def test_clear_cache(self):
        """测试清除缓存"""
        from crawl_performance import PerformanceCrawler, CrawlResult

        crawler = PerformanceCrawler()

        result = CrawlResult(url="https://example.com", success=True)
        crawler._set_cache("https://example.com", result)

        assert len(crawler._cache) > 0

        crawler.clear_cache()
        assert len(crawler._cache) == 0

    def test_rate_limit(self):
        """测试限流"""
        from crawl_performance import PerformanceCrawler

        crawler = PerformanceCrawler()

        # 首次请求不应等待
        start = time.time()
        crawler._rate_limit("https://example.com", delay=0.1)
        elapsed = time.time() - start

        # 应该很快完成
        assert elapsed < 0.5


# ============================================================
# 全局函数测试
# ============================================================

class TestGlobalFunctions:
    """全局函数测试"""

    def test_get_crawler(self):
        """测试获取全局爬虫"""
        from crawl_performance import get_crawler, PerformanceCrawler

        crawler = get_crawler(max_workers=2)
        assert isinstance(crawler, PerformanceCrawler)
        assert crawler.max_workers == 2

    def test_get_crawler_singleton(self):
        """测试单例模式"""
        from crawl_performance import get_crawler

        crawler1 = get_crawler()
        crawler2 = get_crawler()
        assert crawler1 is crawler2


# ============================================================
# 集成测试（可选，需要网络）
# ============================================================

@pytest.mark.skipif(
    os.environ.get("CI") == "true",
    reason="跳过网络测试"
)
class TestNetworkIntegration:
    """网络集成测试（可选）"""

    @pytest.mark.skip(reason="需要网络连接")
    def test_single_get(self):
        """测试单个请求"""
        from crawl_performance import PerformanceCrawler

        crawler = PerformanceCrawler()
        result = crawler.get("https://www.baidu.com", use_cache=False)

        assert result.success == True
        assert result.status_code == 200
        assert result.text is not None
        assert result.elapsed > 0

    @pytest.mark.skip(reason="需要网络连接")
    def test_batch_get(self):
        """测试批量请求"""
        from crawl_performance import PerformanceCrawler

        crawler = PerformanceCrawler(max_workers=3)
        urls = [
            "https://www.baidu.com",
            "https://www.qq.com",
            "https://www.sina.com",
        ]

        results = crawler.batch_get(urls, rate_limit=False)

        assert len(results) == 3
        assert all(r.success for r in results)

    @pytest.mark.skip(reason="需要网络连接")
    def test_cache_hit(self):
        """测试缓存命中"""
        from crawl_performance import PerformanceCrawler

        crawler = PerformanceCrawler()

        # 首次请求
        result1 = crawler.get("https://www.baidu.com", use_cache=True)
        assert result1.from_cache == False

        # 第二次请求（应该命中缓存）
        result2 = crawler.get("https://www.baidu.com", use_cache=True)
        assert result2.from_cache == True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
