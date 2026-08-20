# -*- coding: utf-8 -*-
"""
全网舆情爬虫 — 对话入口助手 v4.3
==================================
让用户通过自然语言触发舆情爬取 / 导出 / 定时任务，无需记忆命令。

触发示例：
  "帮我爬一下贵州茅台最近7天的舆情"
  "工银瑞信最近3天的负面新闻"
  "看下华夏基金今天的正面新闻并导出 Excel"
  "每天早上9点爬取银行板块舆情"
  "增加自定义目标：恒生电子"
"""

from __future__ import annotations

import hashlib
import json
import re
import time
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime

_import_error = None
try:
    from .sentiment_crawler import (
        crawl_sentiment, SentimentCrawler,
        list_sentiment_targets, list_sentiment_sources,
        add_custom_sentiment_target, SentimentSourceLoader,
        SentimentTargetLoader,
    )
    from .sentiment_exporter import to_dialog
    from .sentiment_keywords import POSITIVE_KEYWORDS, NEGATIVE_KEYWORDS
except (ImportError, ValueError):
    try:
        from sentiment_crawler import (
            crawl_sentiment, SentimentCrawler,
            list_sentiment_targets, list_sentiment_sources,
            add_custom_sentiment_target, SentimentSourceLoader,
            SentimentTargetLoader,
        )
        from sentiment_exporter import to_dialog
        from sentiment_keywords import POSITIVE_KEYWORDS, NEGATIVE_KEYWORDS
    except ImportError as e:
        _import_error = str(e)
        crawl_sentiment = SentimentCrawler = None
        list_sentiment_targets = list_sentiment_sources = None
        SentimentTargetLoader = None
        add_custom_sentiment_target = None
        to_dialog = None
        POSITIVE_KEYWORDS = set()
        NEGATIVE_KEYWORDS = set()


# ================================================================
# 0. v4.5 爬取前确认 — 指纹/缓存/格式化
# ================================================================

CONFIRM_FILE = Path(__file__).parent.parent / "data" / "sentiment_confirmations.json"


def _compute_fingerprint(targets: List[str], source_categories: List[str],
                         days: int) -> str:
    """计算 (targets, categories, days) 的指纹。"""
    key = json.dumps({
        "targets": sorted(targets or []),
        "cats": sorted(source_categories or []),
        "days": days,
    }, ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(key.encode("utf-8")).hexdigest()[:16]


def _is_confirmed_recently(fingerprint: str, ttl_hours: int = 24) -> bool:
    """检查该指纹在 ttl_hours 小时内是否已被确认过。"""
    data = _load_confirmations()
    entry = data.get(fingerprint)
    if not entry:
        return False
    ts = entry.get("confirmed_at", 0)
    return (time.time() - ts) < ttl_hours * 3600


def _mark_confirmed(fingerprint: str) -> None:
    """记录一次确认。"""
    data = _load_confirmations()
    data[fingerprint] = {
        "confirmed_at": time.time(),
        "snapshot_id": "",
    }
    try:
        CONFIRM_FILE.parent.mkdir(parents=True, exist_ok=True)
        CONFIRM_FILE.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    except Exception:
        pass  # 容错


def _load_confirmations() -> Dict[str, Any]:
    if not CONFIRM_FILE.exists():
        return {}
    try:
        return json.loads(CONFIRM_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _format_plan_reply(plan: Dict[str, Any]) -> str:
    """把 plan 渲染成可读中文。"""
    lines = ["🗂️ 爬取计划（预览，未执行）", ""]
    targets = plan.get("targets", [])
    if targets:
        lines.append("📌 目标机构")
        for t in targets[:10]:
            lines.append(f"  · {t.get('name', '')} [{t.get('category', '')}]")
        if len(targets) > 10:
            lines.append(f"  · ... 共 {len(targets)} 个")
        lines.append("")
    sources = plan.get("sources", [])
    if sources:
        lines.append(f"📰 媒体源（{len(sources)} 家）")
        # 按类别分组
        types: Dict[str, int] = {}
        for s in sources:
            t = s.get("type", "other") or "other"
            types[t] = types.get(t, 0) + 1
        for t, n in sorted(types.items()):
            lines.append(f"  · {t}: {n}")
        lines.append("")
    lines.append(f"⏱️  时间窗口：最近 {plan.get('days', 7)} 天")
    lines.append(f"📊 预计文章：~{plan.get('estimated_articles', '?')} 条")
    lines.append(f"⏳ 预计耗时：~{plan.get('estimated_seconds', '?')} 秒")
    lines.append("")
    lines.append("[确认] 回复 go / y / 开始 / 确认 / 是")
    lines.append("[修改] 例：把窗口改成 3 天 / 只看负面 / 加上东方财富")
    return "\n".join(lines)


# ================================================================
# 1. 简易 NLU — 关键词 + 正则 + 行业黑话
# ================================================================

class SentimentChatParser:
    """对话式 NLU — 解析用户自然语言到 API 参数"""

    def parse(self, text: str) -> Dict[str, Any]:
        """返回字典 {intent, params}"""
        text = (text or "").strip()
        intent = self._detect_intent(text)
        params: Dict[str, Any] = {}
        if intent in ("crawl", "crawl_export"):
            params = self._parse_crawl(text, with_export=(intent == "crawl_export"))
        elif intent == "schedule":
            params = self._parse_schedule(text)
        elif intent == "add_target":
            params = self._parse_add_target(text)
        elif intent == "list":
            params = self._parse_list(text)
        elif intent == "help":
            params = {}
        else:
            intent = "help"
        return {"intent": intent, "params": params, "raw": text}

    # ---------- Intent 识别 ----------

    def _detect_intent(self, text: str) -> str:
        t = text.lower()
        # 添加自定义目标
        if re.search(r"(新增|添加|加入|新建).{0,8}(目标|机构|公司|基金)", t) or \
           re.search(r"add.{0,6}target", t):
            return "add_target"
        # 列表/查 (在定时前优先 — 「有哪些目标」等等)
        if re.search(r"(哪些媒体|有什么媒体|有哪些媒体|哪些源|媒体源|目标库|金融机构列表|有哪些目标|有哪些机构|支持的.{0,4}机构)", t):
            return "list"
        # 定时
        if re.search(r"(每天|每周|每月|定时|每隔|每小时|每.{1,3}分钟|设置.{0,4}任务)", t) or \
           re.search(r"schedule|cron", t):
            return "schedule"
        # 是否包含导出/生成文件类词 → crawl_export
        has_export = bool(re.search(
            r"(导出|生成|做|导出到).*?(word|excel|docx|xlsx|csv|报告|表格|文件)", t))
        # 爬/舆情/资讯 — 拓宽到 0-12 字符
        if re.search(r"(爬|获取|看看|查|搜索|搜索一下|导出|生成|整理).{0,12}(舆情|新闻|资讯|舆论|消息|报道)", t):
            return "crawl_export" if has_export else "crawl"
        if re.search(r"(正能量|正面|利多|利好|利空|负面|舆情|批评)", t) and \
           re.search(r"(信息|新闻|报道)", t):
            return "crawl_export" if has_export else "crawl"
        # 直接出现舆情/新闻 + 动作词也视为爬取
        if re.search(r"舆情|新闻|资讯|报道", t) and re.search(r"爬|获取|看|查|分析|查证", t):
            return "crawl_export" if has_export else "crawl"
        # 「看看/查查 + 实体 + 时间/政策」也是爬取
        if re.search(r"(帮我)?(看看|看下|爬一下|爬|搜索)(.{2,30})", t) and re.search(r"过去|最近|今天|板块|新闻|政策|公告|舆情|媒体", t):
            return "crawl_export" if has_export else "crawl"
        # 新增: "XXX的舆情/新闻/评价" 直接触发
        if re.search(r"(.{2,20})的(舆情|新闻|资讯|消息|风评|口碑|评价|报道)", t):
            return "crawl_export" if has_export else "crawl"
        return "help"

    # ---------- 参数抽取 ----------

    def _parse_crawl(self, text: str, with_export: bool = False) -> Dict[str, Any]:
        params: Dict[str, Any] = {}

        # 时间窗
        m = re.search(r"(最近|近|过去)?(\d+)\s*天", text)
        params["days"] = int(m.group(2)) if m else 7
        mh = re.search(r"(\d+)\s*小时", text)
        if mh:
            params["days"] = max(1, int(int(mh.group(1)) // 24 + (1 if int(mh.group(1)) % 24 else 0)))

        # v4.6: 月份识别 — "7月" → 覆盖整个7月
        mm = re.search(r"(?:(\d{4})\s*年\s*)?(\d{1,2})\s*月(?:份)?(?:\s*数据)?", text)
        if mm:
            month = int(mm.group(2)) if mm.group(2) else None
            year = int(mm.group(1)) if mm.group(1) else None
            if month and 1 <= month <= 12:
                now = datetime.now()
                if year is None:
                    year = now.year if month <= now.month else now.year - 1
                target_start = datetime(year, month, 1)
                if month == 12:
                    target_end = datetime(year + 1, 1, 1)
                else:
                    target_end = datetime(year, month + 1, 1)
                # 该月到现在的天数
                if target_end > now:
                    target_end = now
                days_to_cover = (target_end - target_start).days + 1
                # 如果用户指定了"7月"而现在是7月30日, 覆盖整个7月=30天
                params["days"] = max(days_to_cover, 1)
                params["date_hint"] = f"{year}年{month}月"
        params["max_articles"] = 60

        # 情感筛选
        if re.search(r"(负面|舆情|利空|批评|投诉|违规|风险)", text):
            params["negative_only"] = True
        elif re.search(r"(正面|利好|好消息|正能量)", text):
            params["positive_only"] = True
        else:
            params["positive_only"] = False
            params["negative_only"] = False

        # 目标：从目标库里模糊匹配
        params["targets"] = self._extract_targets(text)

        # 媒体类别
        params["source_categories"] = self._extract_source_categories(text)

        # 导出格式
        params["export"] = "dialog"
        if with_export:
            if re.search(r"word", text, re.I):
                params["export"] = "word"
            elif re.search(r"excel|xlsx|表格", text, re.I):
                params["export"] = "excel"
            elif re.search(r"csv", text, re.I):
                params["export"] = "csv"
            elif re.search(r"json", text, re.I):
                params["export"] = "json"
            elif re.search(r"(全部|所有格式|多格式)", text):
                params["export"] = "all"
            else:
                params["export"] = "all"

        return params

    def _parse_schedule(self, text: str) -> Dict[str, Any]:
        params: Dict[str, Any] = {}
        # 频率
        if re.search(r"每小时", text) or re.search(r"每小时一次", text):
            params["frequency"] = "hourly"
        elif re.search(r"每(?:天|日)", text) or re.search(r"早上.{0,4}(9|十)", text):
            params["frequency"] = "daily"
        elif re.search(r"每周", text):
            params["frequency"] = "weekly"
        elif re.search(r"每月", text):
            params["frequency"] = "monthly"
        elif (m := re.search(r"每\s*(\d+)\s*分钟", text)):
            interval = int(m.group(1))
            params["frequency"] = {5: "every_5_minutes", 10: "every_10_minutes",
                                    30: "every_30_minutes", 1: "every_minute"}.get(interval, "every_30_minutes")
        elif (m := re.search(r"每\s*(\d+)\s*小时", text)):
            interval = int(m.group(1))
            params["frequency"] = {6: "every_6_hours", 12: "every_12_hours"}.get(interval, "hourly")
        else:
            params["frequency"] = "daily"

        # 完整爬取参数（先去除频率/动作修饰词）
        scrubbed = re.sub(r"(每天|每周|每月|每小时|每\d+小时|每\d+分钟|定时|自动|设置.{0,4}任务|爬取|爬|搜索|拉一下)", " ", text)
        crawl_params = self._parse_crawl(scrubbed)
        params.update({k: crawl_params[k] for k in
                       ("targets", "days", "negative_only", "positive_only", "source_categories") if k in crawl_params})
        params["action"] = "crawl_sentiment_export"
        params["export_format"] = crawl_params.get("export", "all")

        return params

    def _parse_add_target(self, text: str) -> Dict[str, Any]:
        # 先看显式「目标 工银瑞信」或「目标：工银瑞信」或「目标=工银瑞信」
        m = re.search(r"(?:新增|添加|加入|新建)(?:自定义)?(?:目标|机构|公司|基金)?\s*[::：=]?\s*([^，。、\s,]+?)(?:\s|$)", text)
        name = (m.group(1).strip() if m else "")
        # 如果 (默认 fallback 取错)，从剩余 token 过滤
        if not name or name in {"自定义", "目标", "机构", "公司", "基金"}:
            # 取所有名词短语中的第一个
            for tok in re.split(r"[，。、\s,]", text):
                tok = tok.strip()
                if tok and tok not in {"帮我", "新增", "添加", "加入", "新建", "自定义", "目标", "机构", "公司", "基金"}:
                    name = tok
                    break

        category = "listed_company"  # 默认
        if re.search(r"基金", text):
            category = "fund_company"
        elif re.search(r"券商|证券", text):
            category = "securities"
        elif re.search(r"银行", text):
            category = "commercial_bank"
        elif re.search(r"保险", text):
            category = "insurance"
        elif re.search(r"信托", text):
            category = "trust_company"
        elif re.search(r"私募", text):
            category = "private_fund"

        return {"category": category, "name": name}

    def _parse_list(self, text: str) -> Dict[str, Any]:
        if re.search(r"(目标|机构|公司)", text):
            return {"what": "targets"}
        return {"what": "sources"}

    # ---------- 抽取目标 / 媒体类别 ----------

    def _extract_targets(self, text: str) -> List[str]:
        """从文本抽取目标名 — 严格边界 + 后缀词 + 多实体切分。"""
        if SentimentTargetLoader is None:
            return []
        loader = SentimentTargetLoader()
        all_items = loader.all_targets()

        matched: List[str] = []

        # 预清洗
        text_clean = re.sub(r"[，,。.！!？?\"\"''《》（）()\[\]【】]", " ", text)

        # 1) 优先精确匹配注册表里的实体名 (按长度倒序)
        for _cat, _label, name in sorted(all_items, key=lambda x: -len(x[2] or "")):
            if not name:
                continue
            if re.search(re.escape(name), text_clean):
                if name not in matched:
                    matched.append(name)
        if matched:
            return matched[:8]

        # 2) 多实体切分：先按「、」「和」「与」「，」「,」切
        multi = re.split(r"[、，,]|\s+(?:和|与|及、?以及)\s+", text_clean)
        # 然后对每个 token 再剥离前/后 修饰
        prefixes = ("帮我", "请帮我", "看看", "看下", "查看", "了解",
                     "爬", "爬一下", "获取", "搜索", "查", "查一下", "查查", "分析",
                     "一下", "一下子")
        suffixes = ("最近", "今天", "过去", "以下", "舆情", "新闻", "资讯", "报道",
                     "消息", "信息", "舆论", "公告", "金融政策", "政策",
                     "正面", "负面", "板块", "项", "板块的", "行业",
                     "时间", "最新", "的", "这", "那", "爬取一下", "一下")
        stop_words = {"信息", "新闻", "舆情", "资讯", "报道", "舆论", "负面", "正面",
                       "消息", "政策", "板块", "金融政策", "项", "今天", "昨天", "过去",
                       "最近", "所有", "全部"}

        for tok in multi:
            tok = tok.strip()
            if not tok:
                continue
            # 反复剥离前缀后缀
            changed = True
            while changed:
                changed = False
                for pref in prefixes:
                    if tok.startswith(pref):
                        tok = tok[len(pref):].strip()
                        changed = True
                for suf in suffixes:
                    # suffix 是「字符+任意数字+字符」的形式，匹配「最近7天」「最近几天」等
                    if re.match(r"^" + re.escape(suf) + r"(?:\d+(?:天|小时|分钟|周|月))?$", tok):
                        tok = ""
                        break
                    if tok.endswith(suf):
                        tok = tok[: -len(suf)].strip()
                        changed = True
            tok = tok.strip("的块板块项业，。.,;:；：")
            if not tok or len(tok) < 2 or len(tok) > 20:
                continue
            if tok in stop_words:
                continue
            if tok in POSITIVE_KEYWORDS or tok in NEGATIVE_KEYWORDS:
                continue
            if re.fullmatch(r"[的了是个在有要就也我你他她它们]+", tok):
                continue
            if tok not in matched:
                matched.append(tok)
            if len(matched) >= 8:
                break

        # 最终裁剪：把 "X最近Y天" "X过去Y天" "X今天" 合并 → 只保留 X
        cleaned: List[str] = []
        for tok in matched:
            m = re.match(r"^(.*?)(最近|过去|近|今|近|这两天)(?:\s*\d+)?\s*(天|小时|分钟|周|月|分钟|个)?(\s*日)?\s*$", tok)
            if m and m.group(1):
                tok = m.group(1).strip()
            # 截掉尾部的时间/单字后缀
            tok = re.sub(r"(最近|过去|今天|明天|昨天|前年|去年|近期|这个|那个|哪|几)\s*$", "", tok).strip()
            if not tok or len(tok) < 2:
                continue
            if tok not in cleaned:
                cleaned.append(tok)
        return cleaned[:5]


    def _extract_source_categories(self, text: str) -> List[str]:
        cats: List[str] = []
        rules = {
            "authoritative": r"(权威|财经媒体|财联社|华尔街见闻|第一财经|财新)",
            "financial_vertical": r"(财经垂直|财联社|华尔街|第一财经|财新|垂直)",
            "self_media": r"(自媒|微博|微信|今日头条|百家号|雪球|股吧|抖音|自媒体)",
            "international": r"(国际|境外|路透|Bloomberg|彭博|WSJ|FT|尼康|Nikkei)",
        }
        for cat, pat in rules.items():
            if re.search(pat, text):
                cats.append(cat)
        # 全媒体
        if not cats and re.search(r"(全网|所有|全部媒体|所有媒体)", text):
            cats = ["authoritative", "financial_vertical", "self_media", "international"]
        # 默认 - 财经类
        if not cats:
            cats = ["authoritative", "financial_vertical"]
        return cats


# ================================================================
# 2. 顶层对话入口
# ================================================================

def chat_handle(text: str) -> Dict[str, Any]:
    """统一对话处理。返回 {intent, params, reply, snapshot_or_files}"""
    if crawl_sentiment is None:
        return {
            "intent": "help",
            "reply": (
                "⚠️ sentiment_crawler 模块未能加载。\n"
                "解决方案：\n"
                "  1. 运行 python setup_env.py 安装依赖\n"
                "  2. 或手动安装: pip install -r requirements.txt\n"
                "  3. 确认当前目录包含 scripts/ 文件夹"
            ),
            "params": {},
            "output": None,
        }
    parser = SentimentChatParser()
    parsed = parser.parse(text)
    intent = parsed["intent"]
    params = parsed["params"]

    if intent == "help":
        return {
            "intent": "help",
            "params": {},
            "reply": show_help(),
            "output": None,
        }

    if intent == "list":
        what = params.get("what", "sources")
        if what == "targets":
            data = list_sentiment_targets() or []
            return {
                "intent": "list_targets",
                "params": params,
                "reply": _format_targets_reply(data),
                "output": data,
            }
        else:
            data = list_sentiment_sources() or []
            return {
                "intent": "list_sources",
                "params": params,
                "reply": _format_sources_reply(data),
                "output": data,
            }

    if intent == "add_target":
        if not params.get("name"):
            return {"intent": "add_target", "params": params,
                    "reply": "⚠️ 未识别到目标名称，请尝试：新增目标 工银瑞信", "output": None}
        result = add_custom_sentiment_target(params["category"], params["name"])
        ok = "✅" if result.get("ok") else "⚠️"
        return {"intent": "add_target", "params": params, "reply":
                f"{ok} 新增 {params['category']} - {params['name']}\n{json.dumps(result, ensure_ascii=False)}",
                "output": result}

    if intent in ("crawl", "crawl_export"):
        try:
            # v4.5 进度反馈：打印当前状态
            targets = params.get("targets") or []
            scats = params.get("source_categories") or []

            # v4.5: 爬取前确认流程
            user_text = (params.get("raw_text") or "").strip().lower()
            is_confirm_reply = user_text in (
                "go", "y", "yes", "ok", "确认", "开始", "继续", "crawl",
                "是", "好的", "跑", "执行", "yep", "yeah", "确认爬取",
            )
            fingerprint = _compute_fingerprint(targets, scats,
                                              params.get("days", 7))
            skip_confirm = (
                is_confirm_reply
                or params.get("skip_confirm", False)
                or _is_confirmed_recently(fingerprint, ttl_hours=24)
            )

            if not skip_confirm:
                # 第一次：仅返回计划
                snapshot = crawl_sentiment(
                    targets=targets,
                    source_categories=scats,
                    days=params.get("days", 7),
                    positive_only=params.get("positive_only", False),
                    negative_only=params.get("negative_only", False),
                    max_articles=params.get("max_articles", 60),
                    confirmed=False,
                )
                if snapshot and snapshot.plan:
                    reply = _format_plan_reply(snapshot.plan)
                    return {
                        "intent": intent,
                        "params": params,
                        "reply": reply,
                        "output": snapshot,
                        "awaiting_confirmation": True,
                    }
                # plan 失败 → fallback 真爬（容错，落到下面分支）

            # 已确认 → 真爬
            if targets:
                print(f"\n⏳ 正在爬取 {', '.join(targets[:3])}{' 等' if len(targets)>3 else ''} 的舆情，媒体源: {', '.join(scats)}...")
            snapshot = crawl_sentiment(
                targets=targets,
                source_categories=scats,
                days=params.get("days", 7),
                positive_only=params.get("positive_only", False),
                negative_only=params.get("negative_only", False),
                max_articles=params.get("max_articles", 60),
                confirmed=True,
                run_backtest=params.get("run_backtest", False),
            )
            # 记录确认（24h 缓存）
            if snapshot and snapshot.articles:
                _mark_confirmed(fingerprint)
            if snapshot and snapshot.articles:
                print(f"  ✔ 获取 {len(snapshot.articles)} 条记录")
        except Exception as e:
            return {"intent": intent, "params": params,
                    "reply": f"❌ 爬取过程出错: {type(e).__name__}: {e}",
                    "output": None}
        if not snapshot or not snapshot.articles:
            extra = ""
            if snapshot is not None and snapshot.stats.get("timed_out"):
                extra = f"（本次因超时提前返回，耗时 {snapshot.stats.get('elapsed_seconds', 0):.1f}s）"
            return {"intent": intent, "params": params,
                    "reply": f"📭 未获取到结果。建议：放宽时间窗、添加媒体源、或重试。{extra}",
                    "output": None}

        # 输出
        if intent == "crawl":
            reply = to_dialog(snapshot)
            return {"intent": "crawl", "params": params, "reply": reply, "output": snapshot}
        # crawl_export
        try:
            from sentiment_exporter import export as export_sentiment
            outputs = export_sentiment(snapshot, fmt=params.get("export", "all"))
        except Exception as e:
            outputs = {"dialog": to_dialog(snapshot)}
            # 导出失败不影响对话仍然展示
        reply_lines = [f"✅ 已导出 {len(outputs)} 个产物", ""]
        for k, v in outputs.items():
            if k == "dialog":
                continue
            reply_lines.append(f"  📦 [{k.upper()}] {v}")
        if "dialog" in outputs:
            reply_lines.append("\n--- 对话预览 ---\n" + outputs["dialog"][:2000])
        return {"intent": "crawl_export", "params": params, "reply": "\n".join(reply_lines), "output": outputs}

    if intent == "schedule":
        try:
            from crawl_scheduler import get_scheduler
            scheduler = get_scheduler()
            from crawl_scheduler import TaskAction
            crawl_p = params.copy()
            task = scheduler.create_task(
                name=f"舆情[{','.join(crawl_p.get('targets') or []) or '默认'}]-{datetime.now().strftime('%H%M%S')}",
                frequency=crawl_p.get("frequency", "daily"),
                action=TaskAction(crawl_p.get("action", "crawl_sentiment_export")),
                sentiment_targets=crawl_p.get("targets") or [],
                sentiment_source_categories=crawl_p.get("source_categories") or [],
                sentiment_days=crawl_p.get("days", 7),
                sentiment_positive_only=crawl_p.get("positive_only", False),
                sentiment_negative_only=crawl_p.get("negative_only", False),
                sentiment_export_format=crawl_p.get("export_format", "all"),
            )
            if not scheduler.is_running():
                scheduler.start()
            return {"intent": "schedule", "params": crawl_p,
                    "reply": (
                        f"✅ 定时任务已创建\n"
                        f"   ID: {task.task_id}\n"
                        f"   频率: {task.frequency.value}\n"
                        f"   下次执行: {task.next_run_at}\n"
                        f"   💡 使用 list_scheduled_tasks 可随时查看"
                    ),
                    "output": task}
        except Exception as e:
            return {"intent": "schedule", "params": params,
                    "reply": f"❌ 创建定时任务失败: {e}", "output": None}

    return {"intent": intent, "params": params, "reply": show_help(), "output": None}


def _format_targets_reply(data: List[Dict[str, Any]]) -> str:
    lines = ["🎯 全网舆情目标库", ""]
    for it in data:
        lines.append(f"  · {it.get('category','')} — {it.get('label','')} ({it.get('count',0)} 个)")
    lines.append("\n💡 直接对我说：'爬XXX的舆情' 即可触发。")
    return "\n".join(lines)


def _format_sources_reply(data: List[Dict[str, Any]]) -> str:
    by_cat: Dict[str, List[str]] = {}
    for item in data:
        by_cat.setdefault(item.get("category", "未知"), []).append(item.get("name", ""))
    lines = ["📰 全网舆情媒体源", ""]
    for cat, names in by_cat.items():
        lines.append(f"  [{cat}]")
        for n in names:
            lines.append(f"    · {n}")
    return "\n".join(lines)


# ================================================================
# 3. 帮助 / 使用教程
# ================================================================

def show_help() -> str:
    return SENTIMENT_HELP


SENTIMENT_HELP = """\
🆕 cn-financial-scraper 全网舆情爬虫 v4.3 — 使用指南
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
我能做：根据您的对话，全网爬取基金公司、上市公司、证券公司、银行、保险、信托等机构的
正面新闻与舆情，并把结果以对话/Word/Excel/CSV/JSON 反馈给您，也可以设置定时任务。

🗞️ 爬取哪些机构的什么信息？
  · 目标类型 (11 大类)：
    fund_company / listed_company / securities
    / commercial_bank / insurance / trust_company / private_fund
    / foreign_institution / futures / wealth_management / leasing_consumer_finance
  · 信息类型：标题 / 内容简介 / 发布平台 / 发布时间 / 页面连接  — 已自动结构化
  · 情感分类：positive 正面 / negative 舆情 / neutral 中性
  · 严重等级：低度关注 / 中度舆情 / 高危舆情（负面）/ 低度利好 / 中度利好 / 重大利好（正面）

📰 爬哪些媒体？
  · authoritative        — 财经媒体（财联社/华尔街见闻/第一财经/财新/21世纪/经济观察报/36氪/集思录）
  · financial_vertical   — 财经垂直（财联社/华尔街见闻/一财/财新/21世纪/经济观察报/36氪/集思录）
  · self_media           — 自媒体（微信公众号/微博/今日头条/雪球/东财股吧/知乎/B站财经）
  · international        — 国际媒体（路透/Bloomberg/FT/WSJ/日经中文/港媒）

▶️ 对话示例 — 直接复制即可
  · 爬一下贵州茅台最近7天的舆情
  · 工银瑞信最近3天的负面新闻，并导出 Excel
  · 看下华夏基金今天的正面新闻并生成 Word
  · 每天早上9点爬取银行板块舆情
  · 哪些媒体可用？哪些目标？
  · 新增自定义目标 工银瑞信
  · 爬取所有媒体的 贵州茅台 过去24小时舆情，导出 Word/Excel

🔧 完整 API / MCP 工具
  · crawl_global_sentiment( 单/多机构, days, 媒体类别, fmt )
  · export_sentiment_report( snapshot_id, fmt )
  · list_sentiment_targets / list_sentiment_sources
  · add_sentiment_target( category, name, aliases )
  · schedule_crawl_task( frequency, sentiment_targets=..., action=crawl_sentiment_export )

📂 产物落盘
  · 快照      : data/sentiment_snapshots/<snapshot_id>.json
  · Word/Excel: data/sentiment_exports/<snapshot_id>.{docx,xlsx}
  · 索引      : data/sentiment_snapshots/index.json
  · 自定义目标: data/sentiment_custom_targets.json

⚠️ 注意事项
  · 浏览器自动化 v4.2 已作为兜底，反爬严格时自动启用
  · 去重：URL + 标题双维指纹，跨调用生效
  · 调度：基于 schedule 库，关闭进程后失效；重启后可从 data/scheduled_tasks.json 自动恢复
  · 结果可与 v4.0 内容压缩 / v4.1 海外翻译 / v4.2 浏览器自动化 协同使用

💡 提示
  · 我会在您的对话中直接调用工具，并把结果用 Markdown / 文件路径直接呈现
  · 关键词「帮助」、「help」、「怎么用」会再次展示这份指南
"""


# ================================================================
# 4. CLI 调试
# ================================================================

def _cli():
    import argparse
    parser = argparse.ArgumentParser(description="对话入口 CLI")
    parser.add_argument("text", nargs="+", help="用户原话")
    parser.add_argument("--raw", action="store_true", help="仅显示解析结果")
    args = parser.parse_args()
    text = " ".join(args.text)
    parser_obj = SentimentChatParser()
    parsed = parser_obj.parse(text)
    if args.raw:
        print(json.dumps(parsed, ensure_ascii=False, indent=2))
        return
    result = chat_handle(text)
    print(result["reply"])
    if result.get("output") and not isinstance(result["output"], (str, int)):
        print("\n--- 摘要 ---")
        if hasattr(result["output"], "to_dict"):
            out = result["output"]
            print(f"snapshot_id={out.snapshot_id}, total={len(out.articles)}, pos={out.positive_count()}, neg={out.negative_count()}")


if __name__ == "__main__":
    _cli()
