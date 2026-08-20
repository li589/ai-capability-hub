# -*- coding: utf-8 -*-
"""
crawl_backtester.py v1.0 — 4 维数据回测工具（零依赖）
====================================================
对爬到的文章做 4 维校验，保证真实可靠且最新：

1. 新鲜度 (Freshness)        — 发布时间是否在阈值内
2. 交叉源 (Cross-source)     — 同一事件是否在其它源也被收录
3. 历史快照 (Snapshot diff)  — 与历史快照对比，是否新增/修改
4. 数字一致性 (Numeric)      — 文章内数字自洽（如年份、百分比、金额）

用法:
    from crawl_backtester import CrawlBacktester
    bt = CrawlBacktester()
    result = bt.backtest({
        "title": "...", "url": "...", "published_at": "2026-07-29",
        "content": "...", "source": "财联社"
    })
    print(bt.explain(result))

返回值 (BacktestResult):
    - passed: bool                    是否通过（score >= 0.6）
    - overall_score: float            0-1 综合分
    - freshness: dict                 {age_days, level, score}
    - cross_source: dict              {matched_sources, consensus_score}
    - snapshot_compare: dict          {appeared_in_n_snapshots, newly_emerged}
    - numeric: dict                   {extracted, inconsistencies}
    - issues: List[str]               问题列表
"""
from __future__ import annotations

import difflib
import hashlib
import json
import re
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple


SKILL_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = SKILL_DIR / "data"
SNAPSHOT_INDEX = DATA_DIR / "sentiment_snapshots" / "index.json"
RULES_FILE = DATA_DIR / "validation_rules.json"
CONFLICTS_DIR = DATA_DIR / "backtest_conflicts"

CONFLICTS_DIR.mkdir(parents=True, exist_ok=True)


# ============== 数据模型 ==============

@dataclass
class BacktestResult:
    article_id: str
    freshness: Dict[str, Any] = field(default_factory=dict)
    cross_source: Dict[str, Any] = field(default_factory=dict)
    snapshot_compare: Dict[str, Any] = field(default_factory=dict)
    numeric: Dict[str, Any] = field(default_factory=dict)
    overall_score: float = 0.0
    passed: bool = False
    issues: List[str] = field(default_factory=list)
    recommendation: str = ""   # v4.5: "可信任" / "需人工核实" / "建议丢弃"
    source_credibility: float = 0.0  # v4.5: 0-1 源可信度
    content_hash: str = ""     # v4.5: 内容 MD5 哈希

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# ============== 主类 ==============

class CrawlBacktester:
    """4 维数据回测器。"""

    def __init__(self, max_age_days: int = 7,
                 similarity_threshold: float = 0.7,
                 snapshot_index_path: Optional[str] = None,
                 rules_path: Optional[str] = None):
        """
        Args:
            max_age_days: 新鲜度阈值（默认 7 天）
            similarity_threshold: 标题相似度阈值（默认 0.7）
            snapshot_index_path: 快照索引路径（可选，覆盖默认）
            rules_path: 验证规则路径（可选，覆盖默认）
        """
        self.max_age_days = max_age_days
        self.similarity_threshold = similarity_threshold
        self.snapshot_index_path = Path(snapshot_index_path) if snapshot_index_path else SNAPSHOT_INDEX
        self.rules_path = Path(rules_path) if rules_path else RULES_FILE
        self._snapshot_index: List[Dict] = self._load_snapshot_index()

    # --- 主入口 ---

    def backtest(self, article: Dict[str, Any], *,
                 weights: Optional[Dict[str, float]] = None) -> BacktestResult:
        """对单篇文章做 4 维回测。

        Args:
            article: 文章字典
            weights: 自定义权重 {"freshness": 0.35, "cross_source": 0.30,
                     "snapshot": 0.15, "numeric": 0.20}
        """
        aid = article.get("id") or article.get("url") or article.get("title", "")[:30]

        freshness = self.check_freshness(article, max_age_days=self.max_age_days)
        cross = self.cross_source_validate(article)
        snap = self.compare_with_snapshot(article)
        numeric = self.numeric_consistency(article)
        # v4.5: 新增
        src_cred = self.source_credibility_score(article)
        content_hash = self.content_hash_compare(article)

        w = weights or {"freshness": 0.35, "cross_source": 0.30,
                        "snapshot": 0.15, "numeric": 0.20}
        score, issues = self._aggregate(freshness, cross, snap, numeric, src_cred, w)
        recommendation = self._make_recommendation(score, issues, src_cred)
        passed = score >= 0.6 and not self._has_critical_issue(issues)

        return BacktestResult(
            article_id=aid,
            freshness=freshness,
            cross_source=cross,
            snapshot_compare=snap,
            numeric=numeric,
            overall_score=score,
            passed=passed,
            issues=issues,
            recommendation=recommendation,
            source_credibility=src_cred,
            content_hash=content_hash,
        )

    def backtest_batch(self, articles: List[Dict[str, Any]]) -> List[BacktestResult]:
        """批量回测。"""
        return [self.backtest(a) for a in articles]

    def explain(self, result: BacktestResult) -> str:
        """生成中文可读解释。"""
        lines = [f"📊 回测报告 — {result.article_id[:40]}",
                 f"   综合分: {result.overall_score:.2f} | "
                 f"{'✅ 通过' if result.passed else '❌ 未通过'}",
                 ""]

        # 新鲜度
        f = result.freshness
        age = f.get("age_days")
        level = f.get("level", "unknown")
        score = f.get("score", 0)
        lines.append(f"🕐 新鲜度: age={age}d level={level} score={score:.2f}")

        # 交叉源
        c = result.cross_source
        ms = c.get("matched_sources", [])
        lines.append(f"🔗 交叉源: 命中 {len(ms)} 个源, consensus={c.get('consensus_score', 0):.2f}")

        # 快照
        s = result.snapshot_compare
        lines.append(f"📚 历史快照: 出现 {s.get('appeared_in_n_snapshots', 0)} 次, "
                     f"newly_emerged={s.get('newly_emerged', True)}")

        # 数字一致性
        n = result.numeric
        inc = n.get("inconsistencies", [])
        lines.append(f"🔢 数字一致性: 抽取 {len(n.get('extracted', {}))} 项, "
                     f"{len(inc)} 处不一致")

        # 问题
        if result.issues:
            lines.append("")
            lines.append("⚠️ 问题:")
            for i in result.issues:
                lines.append(f"   - {i}")
        return "\n".join(lines)

    # --- 维度 1: 新鲜度 ---

    def check_freshness(self, article: Dict[str, Any],
                        max_age_days: Optional[int] = None) -> Dict[str, Any]:
        """解析发布时间，计算 age_days 与 level。

        返回: {"age_days": int|None, "level": fresh|stale|expired|unknown, "score": 0-1}
        """
        if max_age_days is None:
            max_age_days = self.max_age_days
        pub = article.get("published_at") or article.get("publish_time") or article.get("date")
        if not pub:
            return {"age_days": None, "level": "unknown", "score": 0.5}

        dt = _parse_datetime(str(pub))
        if dt is None:
            return {"age_days": None, "level": "unknown", "score": 0.5}

        now = datetime.now()
        age = (now - dt).days
        if age < 0:
            # 未来时间（异常）
            return {"age_days": age, "level": "expired", "score": 0.0,
                    "reason": "published_at is in the future"}

        if age <= max_age_days:
            level = "fresh"
            score = max(0.0, 1.0 - age / max_age_days * 0.5)
        elif age <= max_age_days * 2:
            level = "stale"
            score = 0.5
        else:
            level = "expired"
            score = max(0.0, 0.2 - (age - max_age_days * 2) / 100)

        return {"age_days": age, "level": level, "score": round(score, 3)}

    # --- 维度 2: 交叉源 ---

    def cross_source_validate(self, article: Dict[str, Any]) -> Dict[str, Any]:
        """用快照索引里同标题的文章作为其它源，看有多少匹配。

        返回: {"matched_sources": [...], "consensus_score": 0-1, "title_similarity": float}
        """
        title = (article.get("title") or "").strip()
        source = article.get("source", "")
        if not title:
            return {"matched_sources": [], "consensus_score": 0.0, "title_similarity": 0.0}

        matched_sources: List[Dict[str, Any]] = []
        best_sim = 0.0
        for snap in self._snapshot_index:
            items = snap.get("articles") or snap.get("items") or []
            for it in items:
                t = (it.get("title") or "").strip()
                if not t:
                    continue
                sim = difflib.SequenceMatcher(None, title, t).ratio()
                if sim >= self.similarity_threshold:
                    matched_sources.append({
                        "source": it.get("source", "unknown"),
                        "snapshot_id": snap.get("id", ""),
                        "title_similarity": round(sim, 3),
                    })
                    best_sim = max(best_sim, sim)

        # 去重 source
        unique_sources = list({m["source"] for m in matched_sources if m["source"] != source})
        consensus = min(1.0, len(unique_sources) * 0.3 + best_sim * 0.4)

        return {
            "matched_sources": matched_sources[:10],  # 限制返回
            "consensus_score": round(consensus, 3),
            "unique_other_sources": len(unique_sources),
            "title_similarity": round(best_sim, 3),
        }

    # --- 维度 3: 历史快照 ---

    def compare_with_snapshot(self, article: Dict[str, Any],
                              lookback: int = 5) -> Dict[str, Any]:
        """在最近 N 个快照中找同 title/url。

        返回: {"appeared_in_n_snapshots": int, "newly_emerged": bool}
        """
        title = (article.get("title") or "").strip()
        url = (article.get("url") or "").strip()
        if not title and not url:
            return {"appeared_in_n_snapshots": 0, "newly_emerged": True}

        # 最近 N 个快照
        recent = self._snapshot_index[-lookback:] if self._snapshot_index else []
        appeared = 0
        appeared_snapshots: List[str] = []
        for snap in recent:
            items = snap.get("articles") or snap.get("items") or []
            for it in items:
                t = (it.get("title") or "").strip()
                u = (it.get("url") or "").strip()
                if (title and t and difflib.SequenceMatcher(None, title, t).ratio() >= self.similarity_threshold) \
                        or (url and u and url == u):
                    appeared += 1
                    appeared_snapshots.append(snap.get("id", ""))
                    break

        return {
            "appeared_in_n_snapshots": appeared,
            "appeared_snapshot_ids": appeared_snapshots[:5],
            "newly_emerged": appeared == 0,
            "lookback": lookback,
        }

    # --- 维度 4: 数字一致性 ---

    def numeric_consistency(self, article: Dict[str, Any]) -> Dict[str, Any]:
        """提取文章内的数字（金额/百分比/年份），检查自洽性。

        检查项:
        - 金额单位一致性（亿/万 混用？）
        - 百分比相加是否合理（如增长率 15% + 25% 不应为 100%）
        - 年份是否在合理范围
        - 同字段不同地方数字是否一致（如"营收 1500亿"与"营收 15000000万"应一致）

        返回: {"extracted": {...}, "inconsistencies": [{field, expected, got, delta}]}
        """
        content = article.get("content", "") or article.get("text", "")
        title = article.get("title", "")
        text = f"{title} {content}"

        extracted = _extract_numbers(text)
        inconsistencies: List[Dict[str, Any]] = []

        # 1. 检查年份
        years = extracted.get("years", [])
        current_year = datetime.now().year
        for y in years:
            if y > current_year + 1 or y < 1990:
                inconsistencies.append({
                    "field": "year", "value": y,
                    "reason": f"年份 {y} 超出合理范围"
                })

        # 2. 检查同含义不同数字（如"营收 1500亿"和"营收 15000000万"）
        # 简化：把所有数字按 value 排序找近似
        amounts = extracted.get("amounts", [])
        if len(amounts) >= 2:
            # 按数量级分组，看是否有跨越 ≥10x 的近似值
            for i in range(len(amounts)):
                for j in range(i + 1, len(amounts)):
                    a, b = amounts[i], amounts[j]
                    if a == 0 or b == 0:
                        continue
                    ratio = max(a, b) / min(a, b)
                    if 9 < ratio < 11:  # 数量级差 10 倍，可能单位不一致
                        inconsistencies.append({
                            "field": "amount", "values": [a, b], "ratio": round(ratio, 2),
                            "reason": f"两个数字 {a} 和 {b} 数量级差 10 倍，可能单位不一致"
                        })

        return {
            "extracted": {
                "amounts": extracted.get("amounts", []),
                "percentages": extracted.get("percentages", []),
                "years": extracted.get("years", []),
            },
            "inconsistencies": inconsistencies[:5],  # 限制返回
            "inconsistency_count": len(inconsistencies),
        }

    # --- 内部 ---

    def _aggregate(self, freshness: Dict, cross: Dict,
                   snap: Dict, numeric: Dict,
                   src_cred: float = 0.0,
                   weights: Optional[Dict[str, float]] = None) -> tuple:
        """聚合 4 维分数 + 生成问题列表（v4.5: 支持自定义权重）。"""
        issues: List[str] = []

        f_score = freshness.get("score", 0.5)
        c_score = cross.get("consensus_score", 0)
        s_score = 1.0 if snap.get("newly_emerged") else 0.7
        n_score = 1.0 - 0.2 * min(3, numeric.get("inconsistency_count", 0))

        w = weights or {"freshness": 0.35, "cross_source": 0.30,
                        "snapshot": 0.15, "numeric": 0.20}
        overall = (w.get("freshness", 0.35) * f_score +
                   w.get("cross_source", 0.30) * c_score +
                   w.get("snapshot", 0.15) * s_score +
                   w.get("numeric", 0.20) * n_score)
        # 源可信度影响 +-5%
        if src_cred > 0:
            overall = overall * (1 + 0.05 * (src_cred - 0.5))
        overall = max(0.0, min(1.0, overall))

        if freshness.get("level") == "expired":
            issues.append(f"文章已过期 ({freshness.get('age_days')} 天)")
        elif freshness.get("level") == "stale":
            issues.append(f"文章新鲜度低 ({freshness.get('age_days')} 天)")

        if cross.get("matched_sources") == [] and cross.get("title_similarity", 0) < 0.3:
            issues.append("未找到其它源交叉验证（孤源）")

        if numeric.get("inconsistency_count", 0) > 0:
            issues.append(f"数字不一致 {numeric.get('inconsistency_count')} 处")

        return round(overall, 3), issues

    def _has_critical_issue(self, issues: List[str]) -> bool:
        """严重问题：孤源 + 数字不一致 + 过期。"""
        critical = ("孤源", "不一致", "过期")
        return sum(1 for i in issues if any(c in i for c in critical)) >= 2

    # --- v4.5 新增方法 ---

    def content_hash_compare(self, article: Dict[str, Any]) -> str:
        """计算文章内容的 MD5 哈希，用于快速检测内容是否真正更新。

        返回: MD5 hex 字符串（可与历史快照哈希比对）
        """
        content = article.get("content", "") or article.get("text", "")
        title = article.get("title", "")
        text = f"{title}\n{content}"
        return hashlib.md5(text.encode("utf-8", errors="replace")).hexdigest()

    def source_credibility_score(self, article: Dict[str, Any]) -> float:
        """基于历史快照中的命中率评估来源可信度。

        返回: 0.0-1.0（越高越可信）
        """
        source = article.get("source", "")
        url = article.get("url", "")
        if not source:
            return 0.5  # 未知来源：中性

        # 统计该来源在历史快照中出现的次数
        total_appearances = 0
        confirmed_appearances = 0
        for snap in self._snapshot_index:
            items = snap.get("articles") or snap.get("items") or []
            for it in items:
                if it.get("source", "") == source:
                    total_appearances += 1
                    # 有 URL 视为可核实
                    if it.get("url"):
                        confirmed_appearances += 1

        if total_appearances == 0:
            # 来源第一次出现 → 中等可信度（需更多数据）
            return 0.5

        # 基础分：历史出现次数越多越可信（最大 0.8）
        base_score = min(0.8, 0.3 + total_appearances * 0.05)
        # URL 核实加分
        if confirmed_appearances > 0:
            base_score += 0.1 * (confirmed_appearances / total_appearances)

        # 已知高可信源加分
        HIGH_CRED_SOURCES = {
            "财联社", "第一财经", "21世纪经济报道", "经济观察报", "每日经济新闻",
            "华尔街见闻", "财新网", "Reuters", "Bloomberg", "WSJ", "FT",
        }
        if source in HIGH_CRED_SOURCES:
            base_score = min(1.0, base_score + 0.15)

        return round(min(1.0, max(0.0, base_score)), 3)

    def _make_recommendation(self, score: float, issues: List[str],
                             src_cred: float) -> str:
        """根据综合分数、问题和源可信度生成推荐。"""
        critical_count = sum(1 for i in issues
                            if any(c in i for c in ("过期", "孤源", "不一致")))

        if score >= 0.75 and critical_count == 0:
            return "可信任"
        elif score >= 0.5 and critical_count <= 1 and src_cred >= 0.4:
            return "需人工核实"
        elif score < 0.3 or critical_count >= 2:
            return "建议丢弃"
        else:
            return "需人工核实"

    def _load_snapshot_index(self) -> List[Dict]:
        if not self.snapshot_index_path.exists():
            return []
        try:
            data = json.loads(self.snapshot_index_path.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                return data.get("snapshots") or data.get("items") or []
            if isinstance(data, list):
                return data
            return []
        except Exception:
            return []


# ============== 工具函数 ==============

def _parse_datetime(s: str) -> Optional[datetime]:
    """解析多种日期格式。"""
    s = s.strip()
    if not s:
        return None
    # 尝试常见格式
    formats = [
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M:%S.%f",
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%Y-%m-%d",
        "%Y/%m/%d",
        "%Y年%m月%d日",
        "%m月%d日",
    ]
    for fmt in formats:
        try:
            dt = datetime.strptime(s, fmt)
            return dt
        except ValueError:
            continue
    # 相对时间（如 "3天前"）
    m = re.match(r"(\d+)\s*(秒|分|小时|天|日|周|个月|月|年)前", s)
    if m:
        n = int(m.group(1))
        unit = m.group(2)
        delta_map = {
            "秒": timedelta(seconds=n), "分": timedelta(minutes=n),
            "小时": timedelta(hours=n), "天": timedelta(days=n),
            "日": timedelta(days=n), "周": timedelta(weeks=n),
            "个月": timedelta(days=30 * n), "月": timedelta(days=30 * n),
            "年": timedelta(days=365 * n),
        }
        return datetime.now() - delta_map.get(unit, timedelta(0))
    return None


_NUM_PATTERNS = {
    "amounts": re.compile(r"(\d+(?:\.\d+)?)\s*(亿|万|千|百|元|块|美金|美元)?"),
    "percentages": re.compile(r"(\d+(?:\.\d+)?)\s*%"),
    "years": re.compile(r"(?:^|[^\d])(19\d\d|20\d\d)(?:[^\d]|$)"),
}


def _extract_numbers(text: str) -> Dict[str, List]:
    """从文本中抽取金额/百分比/年份。"""
    out: Dict[str, List] = {"amounts": [], "percentages": [], "years": []}

    # 金额（仅保留有单位的或大数字）
    for m in _NUM_PATTERNS["amounts"].finditer(text):
        try:
            v = float(m.group(1))
            unit = m.group(2) or ""
            if unit in ("亿",):
                v *= 1e8
            elif unit in ("万",):
                v *= 1e4
            elif unit in ("千",):
                v *= 1e3
            elif unit in ("百",):
                v *= 100
            if v >= 1000:  # 忽略小数
                out["amounts"].append(int(v))
        except ValueError:
            pass

    for m in _NUM_PATTERNS["percentages"].finditer(text):
        try:
            out["percentages"].append(float(m.group(1)))
        except ValueError:
            pass

    for m in _NUM_PATTERNS["years"].finditer(text):
        try:
            out["years"].append(int(m.group(1)))
        except ValueError:
            pass

    return out


# ============== 便捷函数 ==============

def quick_backtest(article: Dict[str, Any]) -> BacktestResult:
    """便捷函数：用默认配置回测单条。"""
    return CrawlBacktester().backtest(article)


def explain_text(article: Dict[str, Any]) -> str:
    """便捷函数：直接返回 explain 文本。"""
    return CrawlBacktester().explain(quick_backtest(article))


# ============== v4.5.1 批量汇总与过滤 ==============

def batch_summary(results: List[BacktestResult]) -> Dict[str, Any]:
    """对一批回测结果做汇总统计。

    返回:
        {
          "total": N, "passed": N_pass, "failed": N_fail,
          "pass_rate": 0-1, "avg_score": float,
          "by_recommendation": {"可信任": N, "需人工核实": N, "建议丢弃": N},
          "by_issue_type": {"孤源": N, "数字不一致": N, "过期": N, "新鲜度低": N},
          "avg_source_credibility": float,
        }
    """
    if not results:
        return {"total": 0, "passed": 0, "failed": 0, "pass_rate": 0.0,
                "avg_score": 0.0, "by_recommendation": {}, "by_issue_type": {},
                "avg_source_credibility": 0.0}

    total = len(results)
    passed = sum(1 for r in results if r.passed)
    avg_score = sum(r.overall_score for r in results) / total
    avg_cred = sum(r.source_credibility for r in results) / total

    by_rec: Dict[str, int] = {}
    by_issue: Dict[str, int] = {}
    for r in results:
        by_rec[r.recommendation or "未知"] = by_rec.get(r.recommendation or "未知", 0) + 1
        for issue in r.issues:
            # 提取问题类型（前缀）
            t = issue.split("（")[0].split(" ")[0]
            if any(k in issue for k in ("孤源",)):
                t = "孤源"
            elif any(k in issue for k in ("数字不一致", "不一致")):
                t = "数字不一致"
            elif "过期" in issue:
                t = "过期"
            elif "新鲜度" in issue:
                t = "新鲜度低"
            by_issue[t] = by_issue.get(t, 0) + 1

    return {
        "total": total,
        "passed": passed,
        "failed": total - passed,
        "pass_rate": round(passed / total, 3),
        "avg_score": round(avg_score, 3),
        "by_recommendation": by_rec,
        "by_issue_type": by_issue,
        "avg_source_credibility": round(avg_cred, 3),
    }


def filter_by_recommendation(results: List[BacktestResult],
                             articles: List[Any],
                             drop_levels: Tuple[str, ...] = ("建议丢弃",)
                             ) -> Tuple[List[Any], List[BacktestResult]]:
    """按推荐等级过滤掉低质量文章。

    Args:
        results: BacktestResult 列表
        articles: 对应的原始文章列表（与 results 同序）
        drop_levels: 需要丢弃的推荐等级元组，默认仅丢弃"建议丢弃"

    Returns:
        (kept_articles, kept_results) 保留的文章与回测结果
    """
    drop_set = set(drop_levels)
    kept_a, kept_r = [], []
    for art, r in zip(articles, results):
        if (r.recommendation or "") in drop_set:
            continue
        kept_a.append(art)
        kept_r.append(r)
    return kept_a, kept_r