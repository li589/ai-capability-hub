# -*- coding: utf-8 -*-
"""v5.0.0 模块F：运行优化测试（协作式超时 / 并发锁）"""

import time
from concurrent.futures import ThreadPoolExecutor

import pytest

from scripts.sentiment_crawler import (
    SentimentCrawler, SentimentArticle, _SEEN_INDEX, _TITLE_INDEX, _SEEN_LOCK,
)


@pytest.fixture(autouse=True)
def _clean_globals():
    _SEEN_INDEX.clear()
    _TITLE_INDEX.clear()
    yield
    _SEEN_INDEX.clear()
    _TITLE_INDEX.clear()


# ============================================================
# 1. 协作式超时
# ============================================================

def test_run_with_timeout_normal():
    c = SentimentCrawler()
    assert c._run_with_timeout(lambda: 42, timeout=5) == 42


def test_run_with_timeout_timeout_returns_none():
    """超时后立即返回 None（不阻塞外层）"""
    c = SentimentCrawler()
    start = time.time()
    out = c._run_with_timeout(lambda: time.sleep(5) or "x", timeout=0.2, name="慢源")
    elapsed = time.time() - start
    assert out is None
    assert elapsed < 3.0, f"超时后阻塞 {elapsed:.1f}s（应 <3s）"


def test_run_with_timeout_marks_cancelled():
    """超时后源名进入 _cancelled_sources"""
    c = SentimentCrawler()
    c._run_with_timeout(lambda: time.sleep(5) or "x", timeout=0.2, name="被取消源")
    assert "被取消源" in c._cancelled_sources


def test_run_with_timeout_zero_timeout():
    """timeout<=0 直接同步执行"""
    c = SentimentCrawler()
    assert c._run_with_timeout(lambda: 7, timeout=0) == 7


def test_run_with_timeout_exception():
    c = SentimentCrawler()
    def _boom():
        raise ValueError("x")
    assert c._run_with_timeout(_boom, timeout=5) is None


# ============================================================
# 2. 并发 _is_dup 线程安全
# ============================================================

def test_concurrent_is_dup_no_loss():
    """8 线程并发插入不同标题（长且互不相同）→ 全部保留，无竞态丢失"""
    import hashlib
    c = SentimentCrawler()
    titles = [f"并发测试文章{hashlib.md5(str(i).encode()).hexdigest()}" for i in range(40)]
    urls = [f"https://x.com/{i}" for i in range(40)]

    def _add(i):
        a = SentimentArticle(title=titles[i], target_name="并发目标",
                             url=urls[i], publish_time="2026-08-01")
        return c._is_dup(a)  # 首次应 False（新增）

    with ThreadPoolExecutor(max_workers=8) as ex:
        results = list(ex.map(_add, range(40)))

    assert all(r is False for r in results), "并发新增不应被误判重复"
    with _SEEN_LOCK:
        assert len(_SEEN_INDEX) == 40, f"索引大小 {len(_SEEN_INDEX)} ≠ 40（丢失）"


def test_concurrent_is_dup_same_title_detected():
    """并发下相同标题只保留一条"""
    c = SentimentCrawler()
    first = c._is_dup(SentimentArticle(title="同标题", target_name="T", url="https://x/1"))
    assert first is False
    # 并发重复检查
    def _check(_):
        return c._is_dup(SentimentArticle(title="同标题！", target_name="T", url="https://x/2"))
    with ThreadPoolExecutor(max_workers=8) as ex:
        results = list(ex.map(_check, range(16)))
    assert all(r is True for r in results), "模糊重复应全部命中"


def test_concurrent_placeholder_seen():
    """并发占位去重：8 个不同组合首见 False，重复 True，不抛异常"""
    c = SentimentCrawler()
    combos = [(f"目标{i}", f"源{i}") for i in range(8)]

    def _check(i):
        t, s = combos[i]
        return c._placeholder_seen(t, s)

    with ThreadPoolExecutor(max_workers=8) as ex:
        results = list(ex.map(_check, range(8)))
    assert not any(results), "每个 (target,source) 首次应 False"
    # 再次全部应 True
    again = [c._placeholder_seen(t, s) for t, s in combos]
    assert all(again)


# ============================================================
# 3. 精度校验
# ============================================================

def test_timeout_elapsed_precision():
    """超时耗时应在 timeout 附近（不过早不过晚太多）"""
    c = SentimentCrawler()
    start = time.time()
    c._run_with_timeout(lambda: time.sleep(5), timeout=0.3)
    elapsed = time.time() - start
    assert 0.25 <= elapsed < 2.0, f"耗时 {elapsed:.2f}s 异常"


def test_fetch_failure_logging_structure():
    """B5: 失败日志含 URL 和阶段（吞错可诊断）"""
    c = SentimentCrawler()
    # 不真正请求，仅验证 _log_fetch_failure 不抛异常
    c._log_fetch_failure("https://example.com/x", "http", ValueError("测试"))
