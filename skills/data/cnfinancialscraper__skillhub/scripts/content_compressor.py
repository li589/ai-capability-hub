# -*- coding: utf-8 -*-
"""
内容分析压缩引擎 v4.0
从大量爬取内容/文件中提取关键信息，压缩为 2-3 页结构化摘要。

核心策略：
1. 财务指标优先提取（复用 document_analyzer）
2. 关键词密度排序（TF-IDF 启发式）
3. 首尾段落加权（倒金字塔结构）
4. 去重合并（语义相似度检测）
5. 结构化输出（Markdown 格式）

支持用户指定关注维度：财务 / 风险 / 行业 / 政策 / 全面
"""

import re
import json
import math
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Set
from datetime import datetime
from collections import Counter
from dataclasses import dataclass, field

# 复用现有模块
try:
    from document_analyzer import (
        classify_document, extract_metadata, extract_financial_indicators,
        extract_risk_factors, extract_glossary, extract_sections,
        FINANCIAL_INDICATOR_PATTERNS, DOC_CATEGORIES
    )
    HAS_ANALYZER = True
except ImportError:
    HAS_ANALYZER = False
    FINANCIAL_INDICATOR_PATTERNS = {}
    DOC_CATEGORIES = []

try:
    from enhanced_parser import MultiFormatParser
    HAS_ENHANCED_PARSER = True
except ImportError:
    HAS_ENHANCED_PARSER = False

SKILL_DATA_DIR = Path(__file__).parent.parent / "data"
SKILL_DATA_DIR.mkdir(parents=True, exist_ok=True)


# ==================== 中文停用词 ====================

STOP_WORDS = set([
    '的', '了', '在', '是', '我', '有', '和', '就', '不', '人', '都', '一',
    '一个', '上', '也', '很', '到', '说', '要', '去', '你', '会', '着',
    '没有', '看', '好', '自己', '这', '他', '她', '它', '们', '那', '些',
    '什么', '怎么', '如何', '为什么', '因为', '所以', '但是', '然而',
    '可以', '这个', '那个', '这些', '那些', '已经', '还是', '只是',
    '比较', '非常', '更加', '尤其', '其中', '其他', '以及', '或者',
    '根据', '按照', '通过', '经过', '为了', '对于', '关于', '由于',
    '目前', '现在', '正在', '将', '将把', '被', '让', '把', '向',
    '与', '从', '以', '对', '等', '及', '或', '但', '而', '且',
    '为', '其', '之', '所', '者', '于', '则', '也', '因',
    '年', '月', '日', '时', '分', '万', '亿', '元', '只', '个',
    '该', '此', '本', '各', '每', '另', '另', '第', '前', '后',
    '中', '内', '外', '间', '里', '后', '前', '左右', '上下',
])


# ==================== 金融关键词权重表 ====================

FINANCIAL_KEYWORDS = {
    # 财务指标类 (权重 10)
    "营业收入": 10, "净利润": 10, "总资产": 10, "净资产": 10, "每股收益": 10,
    "市盈率": 10, "市净率": 10, "净资产收益率": 10, "毛利率": 10, "净利率": 10,
    "资产负债率": 10, "现金流": 10, "同比增长": 10, "环比增长": 10,
    "归母净利润": 10, "扣非净利润": 10, "经营性现金流": 10,
    # 市场类 (权重 8)
    "股价": 8, "涨跌幅": 8, "成交量": 8, "成交额": 8, "换手率": 8,
    "市值": 8, "估值": 8, "分红": 8, "股息率": 8,
    # 评级推荐类 (权重 9)
    "买入": 9, "增持": 9, "目标价": 9, "评级": 9, "推荐": 9,
    "上调": 9, "下调": 9,
    # 风险类 (权重 7)
    "风险": 7, "诉讼": 7, "违规": 7, "处罚": 7, "退市": 7,
    "减值": 7, "亏损": 7, "债务违约": 7,
    # 行业政策类 (权重 6)
    "政策": 6, "监管": 6, "改革": 6, "利好": 6, "利空": 6,
    "行业前景": 6, "市场竞争": 6, "技术创新": 6,
    # 事件类 (权重 5)
    "收购": 5, "并购": 5, "重组": 5, "上市": 5, "融资": 5,
    "增发": 5, "回购": 5, "重大合同": 5, "战略合作": 5,
}

# 按维度分类的关键词
DIMENSION_KEYWORDS = {
    "财务": ["营业收入", "净利润", "总资产", "净资产", "每股收益", "市盈率", "市净率",
             "净资产收益率", "毛利率", "净利率", "资产负债率", "现金流", "同比增长",
             "归母净利润", "扣非净利润", "经营性现金流"],
    "风险": ["风险", "诉讼", "违规", "处罚", "退市", "减值", "亏损", "债务违约",
             "担保", "质押", "冻结", "警示", "问询", "调查"],
    "行业": ["行业", "市场", "竞争", "格局", "份额", "趋势", "前景", "产业链",
             "上下游", "供给", "需求", "产能", "景气"],
    "政策": ["政策", "监管", "法规", "改革", "合规", "牌照", "审批", "指导意见",
             "通知", "规定", "办法"],
    "事件": ["收购", "并购", "重组", "上市", "融资", "增发", "回购", "分红",
             "重大合同", "战略合作", "投资", "减持", "增持", "解禁"],
}


# ==================== 数据结构 ====================

@dataclass
class CompressConfig:
    """压缩配置"""
    focus: str = "全面"  # 财务 / 风险 / 行业 / 政策 / 事件 / 全面
    max_pages: int = 3  # 目标页数 (约 1000 字/页)
    max_chars: int = 3000  # 最大输出字符数
    include_tables: bool = True  # 是否包含表格
    include_charts_hint: bool = True  # 是否包含图表建议
    language: str = "zh"  # 输出语言


@dataclass
class CompressResult:
    """压缩结果"""
    title: str
    summary: str  # 一句话摘要
    key_points: List[str]  # 关键要点 (3-5 条)
    financial_highlights: Dict[str, Any]  # 财务亮点
    risk_summary: List[str]  # 风险摘要
    structured_report: str  # 结构化 Markdown 报告
    focus_dimensions: List[str]  # 实际覆盖的维度
    stats: Dict[str, Any]  # 统计信息
    source_info: Dict[str, Any]  # 来源信息


# ==================== 内容压缩引擎 ====================

class ContentCompressor:
    """内容分析压缩引擎。"""

    def __init__(self):
        self._parser = None
        if HAS_ENHANCED_PARSER:
            self._parser = MultiFormatParser()

    def compress(self, source: Any, config: Optional[CompressConfig] = None) -> CompressResult:
        """
        压缩内容为 2-3 页摘要。

        Args:
            source: 文本内容(str)、文件路径(str)、或解析结果(dict)
            config: 压缩配置

        返回: CompressResult
        """
        if config is None:
            config = CompressConfig()

        # 1. 标准化输入
        text_content, source_info = self._normalize_source(source)
        if not text_content:
            return CompressResult(
                title="内容为空", summary="", key_points=[],
                financial_highlights={}, risk_summary=[],
                structured_report="# 内容压缩失败\n\n原始内容为空，无法提取有效信息。",
                focus_dimensions=[], stats={}, source_info=source_info
            )

        # 2. 提取结构化信息
        metadata = self._extract_metadata(text_content, source_info)
        financial = self._extract_financial(text_content)
        risks = self._extract_risks(text_content)
        sections = self._extract_sections(text_content)
        keywords = self._extract_keywords(text_content, config.focus)

        # 3. 生成关键要点（按维度筛选）
        key_points = self._generate_key_points(
            text_content, metadata, financial, risks, keywords, config
        )

        # 4. 构建结构化报告
        structured_report = self._build_report(
            metadata, financial, risks, key_points, sections, config
        )

        # 5. 组装结果
        title = metadata.get("title") or source_info.get("name", "未命名内容")
        summary = self._generate_one_line_summary(text_content, metadata, financial)

        return CompressResult(
            title=title,
            summary=summary,
            key_points=key_points,
            financial_highlights=financial,
            risk_summary=risks[:5],
            structured_report=structured_report,
            focus_dimensions=self._get_active_dimensions(config.focus),
            stats={
                "source_chars": len(text_content),
                "output_chars": len(structured_report),
                "compression_ratio": f"{len(structured_report)/max(len(text_content),1)*100:.1f}%",
                "key_points_count": len(key_points),
                "financial_indicators_count": len(financial),
                "risk_factors_count": len(risks),
                "compressed_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            },
            source_info=source_info,
        )

    def compress_multiple(self, sources: List[Any],
                          config: Optional[CompressConfig] = None) -> CompressResult:
        """
        批量压缩多个来源的内容，合并为一个统一摘要。

        Args:
            sources: 多个来源（文本、文件路径、解析结果）
            config: 压缩配置

        返回: 合并后的 CompressResult
        """
        if config is None:
            config = CompressConfig()

        results = []
        for src in sources:
            try:
                r = self.compress(src, config)
                results.append(r)
            except Exception:
                continue

        if not results:
            return CompressResult(
                title="合并压缩失败", summary="", key_points=[],
                financial_highlights={}, risk_summary=[],
                structured_report="# 合并压缩失败\n\n所有来源均无法提取有效信息。",
                focus_dimensions=[], stats={}, source_info={}
            )

        # 合并
        all_points = []
        all_fin = {}
        all_risks = []
        for r in results:
            all_points.extend(r.key_points)
            all_fin.update(r.financial_highlights)
            all_risks.extend(r.risk_summary)

        # 去重关键要点
        unique_points = []
        seen = set()
        for p in all_points:
            norm = re.sub(r'\s+', '', p)[:30]
            if norm not in seen:
                seen.add(norm)
                unique_points.append(p)

        # 构建合并报告
        merged_meta = {"title": f"多源内容合并摘要 ({len(results)} 个来源)"}
        return CompressResult(
            title=merged_meta["title"],
            summary=f"合并了 {len(results)} 个来源的内容，提取 {len(unique_points)} 条关键要点。",
            key_points=unique_points[:8],
            financial_highlights=dict(list(all_fin.items())[:15]),
            risk_summary=list(dict.fromkeys(all_risks))[:8],
            structured_report=self._build_merged_report(results, config),
            focus_dimensions=self._get_active_dimensions(config.focus),
            stats={
                "source_count": len(results),
                "total_source_chars": sum(r.stats.get("source_chars", 0) for r in results),
                "key_points_count": len(unique_points),
                "compressed_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            },
            source_info={"sources": [r.source_info for r in results]},
        )

    def _normalize_source(self, source: Any) -> Tuple[str, Dict[str, Any]]:
        """标准化输入为纯文本。"""
        source_info = {}

        if isinstance(source, str) and len(source) < 500 and os.path.isfile(source):
            # 文件路径
            source_info = {"type": "file", "path": source, "name": Path(source).name}
            result = self._parse_file(source)
            text = result.get("text_content", "") or ""
            source_info.update({k: v for k, v in result.items()
                               if k not in ("text_content", "all_text", "slides")})
            return text, source_info

        elif isinstance(source, dict):
            # 解析结果
            source_info = {
                "type": source.get("file_type", "dict"),
                "name": source.get("file_path", source.get("title", "未命名")),
            }
            text = source.get("text_content", source.get("all_text", "")) or ""
            if not text:
                text = json.dumps(source, ensure_ascii=False)
            return text, source_info

        elif isinstance(source, str):
            # 纯文本
            source_info = {"type": "text", "name": "文本内容"}
            return source, source_info

        else:
            # 尝试转字符串
            source_info = {"type": "unknown", "name": str(type(source).__name__)}
            return str(source), source_info

    def _parse_file(self, file_path: str) -> Dict[str, Any]:
        """使用增强解析器解析文件。"""
        if self._parser:
            try:
                return self._parser.parse(file_path)
            except Exception:
                pass

        # fallback: 直接读文本
        result = {"file_type": Path(file_path).suffix, "file_path": file_path}
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                result["text_content"] = f.read()
        except (UnicodeDecodeError, Exception):
            try:
                with open(file_path, 'rb') as f:
                    raw = f.read()
                    # 尝试常见编码
                    for enc in ['gbk', 'gb2312', 'gb18030']:
                        try:
                            result["text_content"] = raw.decode(enc)
                            break
                        except UnicodeDecodeError:
                            continue
                    if "text_content" not in result:
                        result["text_content"] = raw.decode('utf-8', errors='ignore')
            except Exception:
                result["text_content"] = ""
        return result

    def _extract_metadata(self, text: str, source_info: Dict) -> Dict[str, str]:
        """提取内容元数据。"""
        if HAS_ANALYZER:
            meta = extract_metadata(text)
            if source_info.get("name"):
                meta.setdefault("title", source_info["name"])
            return meta

        # 简易提取
        meta = {"title": source_info.get("name", ""), "institution": "", "date": "", "stock_code": ""}
        lines = [l.strip() for l in text.split('\n') if l.strip()]
        if lines:
            meta["title"] = lines[0][:120]
        # 日期
        dm = re.search(r'(\d{4})[-/年](\d{1,2})[-/月](\d{1,2})', text[:2000])
        if dm:
            meta["date"] = f"{dm.group(1)}-{int(dm.group(2)):02d}-{int(dm.group(3)):02d}"
        # 股票代码
        cm = re.search(r'[\(（](\d{6})[\)）]', text[:500])
        if cm:
            meta["stock_code"] = cm.group(1)
        return meta

    def _extract_financial(self, text: str) -> Dict[str, Any]:
        """提取财务指标。"""
        if HAS_ANALYZER:
            return extract_financial_indicators(text)

        # 简易财务提取
        fin: Dict[str, Any] = {}
        for key, pat in FINANCIAL_INDICATOR_PATTERNS.items():
            m = re.search(pat, text)
            if m:
                try:
                    val = m.group(1).replace(",", "")
                    fin[key] = float(val) if '.' in val else int(val)
                except (ValueError, AttributeError):
                    fin[key] = m.group(1)
        return fin

    def _extract_risks(self, text: str) -> List[str]:
        """提取风险因素。"""
        if HAS_ANALYZER:
            return extract_risk_factors(text)

        risks = []
        risk_section = re.search(
            r'(?:风险因素|风险提示|风险分析|风险警示)(.{0,3000}?)(?=第[一二三四五六七八九十\d]+[章节]|\Z)',
            text, re.DOTALL
        )
        if risk_section:
            chunk = risk_section.group(0)
            for m in re.finditer(r'[•·●◆■\d+\.、．)]\s*([^\n•·●◆■]{10,200})', chunk):
                item = m.group(1).strip()
                if len(item) > 10 and item not in risks:
                    risks.append(item[:150])
        return risks[:15]

    def _extract_sections(self, text: str) -> List[Dict[str, Any]]:
        """提取章节结构。"""
        if HAS_ANALYZER:
            return extract_sections(text)

        sections = []
        for m in re.finditer(
            r'^[第]*[一二三四五六七八九十\d]+[章节篇、.]\s*([^\n]{3,80})$',
            text, re.MULTILINE
        ):
            sections.append({"title": m.group(0).strip(), "level": 1})
        return sections[:20]

    def _extract_keywords(self, text: str, focus: str) -> Dict[str, float]:
        """
        提取关键词及其重要性得分（TF-IDF 启发式）。
        """
        # 分词（简单字符级 n-gram）
        words = []
        for m in re.finditer(r'[\u4e00-\u9fff]{2,8}|[A-Za-z]{2,20}|[+-]?\d+[\.]?\d*%?', text):
            words.append(m.group())

        total = len(words) if words else 1

        # TF 计算
        word_counts = Counter(words)

        # 结合预定义金融关键词权重
        keywords: Dict[str, float] = {}
        active_dims = self._get_active_dimensions(focus)

        for word, count in word_counts.items():
            if word in STOP_WORDS or len(word) < 2:
                continue

            tf = count / total
            bonus = 0

            # 金融关键词加权
            if word in FINANCIAL_KEYWORDS:
                bonus = FINANCIAL_KEYWORDS[word] * 0.1

            # 维度匹配加权
            for dim in active_dims:
                if dim in DIMENSION_KEYWORDS and word in DIMENSION_KEYWORDS[dim]:
                    bonus += 0.5

            score = tf * (1 + bonus)
            if score > 0.001:
                keywords[word] = score

        # 排序取 Top 20
        return dict(sorted(keywords.items(), key=lambda x: -x[1])[:20])

    def _generate_key_points(self, text: str, metadata: Dict, financial: Dict,
                              risks: List, keywords: Dict, config: CompressConfig) -> List[str]:
        """生成关键要点列表。"""
        points = []

        # 1. 财务要点
        if financial:
            fin_items = list(financial.items())
            for key, val in fin_items[:5]:
                label = key.replace('_', ' ')
                points.append(f"📊 {label}: {val}")

        # 2. 关键词要点
        top_kw = list(keywords.keys())[:5]
        if top_kw:
            # 查找这些关键词所在的句子
            sentences = re.split(r'[。！；\n]', text)
            for kw in top_kw[:3]:
                for sent in sentences:
                    if kw in sent and len(sent) > 15:
                        sent_clean = sent.strip()[:120]
                        if sent_clean not in points and sent_clean not in ' '.join(points):
                            points.append(f"🔑 [{kw}] {sent_clean}")
                        break

        # 3. 风险要点
        if risks and config.focus in ("风险", "全面"):
            for risk in risks[:3]:
                if risk not in ' '.join(points):
                    points.append(f"⚠️ 风险提示: {risk[:100]}")

        # 4. 标题/元数据要点
        if metadata.get("title"):
            points.insert(0, f"📄 标题: {metadata['title']}")
        if metadata.get("date"):
            points.insert(1, f"📅 日期: {metadata['date']}")
        if metadata.get("institution"):
            points.insert(2, f"🏢 机构: {metadata['institution']}")

        # 确保至少 3 条
        if len(points) < 3:
            # 取文本首尾关键句
            sentences = [s.strip() for s in re.split(r'[。！；\n]', text) if len(s.strip()) > 20]
            for sent in sentences[:5]:
                if sent not in ' '.join(points):
                    points.append(f"💡 {sent[:120]}")
                if len(points) >= 5:
                    break

        return points[:8]

    def _generate_one_line_summary(self, text: str, metadata: Dict,
                                    financial: Dict) -> str:
        """生成一句话摘要。"""
        parts = []
        if metadata.get("title"):
            parts.append(metadata["title"])
        if metadata.get("institution"):
            parts.append(f"({metadata['institution']})")
        if metadata.get("date"):
            parts.append(f"[{metadata['date']}]")

        # 取第一段关键词句
        lines = [l.strip() for l in text.split('\n') if len(l.strip()) > 30]
        if lines:
            first_line = lines[0][:200]
            parts.append(f"— {first_line}")

        return ' '.join(parts)[:300]

    def _build_report(self, metadata: Dict, financial: Dict, risks: List,
                      key_points: List, sections: List,
                      config: CompressConfig) -> str:
        """构建结构化 Markdown 报告。"""
        lines = []

        # 标题
        title = metadata.get("title") or "内容压缩报告"
        lines.append(f"# {title}\n")

        # 元数据栏
        meta_parts = []
        if metadata.get("date"):
            meta_parts.append(f"📅 {metadata['date']}")
        if metadata.get("institution"):
            meta_parts.append(f"🏢 {metadata['institution']}")
        if metadata.get("stock_code"):
            meta_parts.append(f"📈 {metadata['stock_code']}")
        if meta_parts:
            lines.append(" | ".join(meta_parts))
            lines.append("")

        # 一句话摘要
        lines.append("## 📋 摘要\n")
        lines.append(f"> {self._generate_one_line_summary('', metadata, financial)}\n")

        # 关键要点
        if key_points:
            lines.append("## 🔑 关键要点\n")
            for i, point in enumerate(key_points, 1):
                lines.append(f"{i}. {point}")
            lines.append("")

        # 财务数据
        if financial and config.include_tables:
            lines.append("## 💰 核心财务数据\n")
            lines.append("| 指标 | 数值 |")
            lines.append("|------|------|")
            for key, val in list(financial.items())[:10]:
                label = key.replace('_', ' ').replace('  ', ' ')
                lines.append(f"| {label} | {val} |")
            lines.append("")

        # 风险提示
        if risks and config.focus in ("风险", "全面"):
            lines.append("## ⚠️ 风险因素\n")
            for i, risk in enumerate(risks[:5], 1):
                lines.append(f"{i}. {risk}")
            lines.append("")

        # 章节结构（如果有）
        if sections and len(sections) >= 3:
            lines.append("## 📑 内容结构\n")
            for sec in sections[:10]:
                indent = "  " * (sec.get("level", 1) - 1)
                lines.append(f"{indent}- {sec['title']}")
            lines.append("")

        # 页脚
        lines.append("---")
        lines.append(f"*压缩时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | "
                     f"关注维度: {config.focus}*")

        return '\n'.join(lines)

    def _build_merged_report(self, results: List[CompressResult],
                              config: CompressConfig) -> str:
        """构建多源合并报告。"""
        lines = [f"# 多源内容合并摘要 ({len(results)} 个来源)\n"]

        lines.append("## 📋 来源列表\n")
        for i, r in enumerate(results, 1):
            lines.append(f"{i}. [{r.source_info.get('type', '?')}] {r.title}")
        lines.append("")

        # 合并关键要点
        all_points = []
        seen = set()
        for r in results:
            for p in r.key_points:
                norm = re.sub(r'\s+', '', p)[:30]
                if norm not in seen:
                    seen.add(norm)
                    all_points.append(p)

        if all_points:
            lines.append("## 🔑 综合关键要点\n")
            for i, point in enumerate(all_points[:10], 1):
                lines.append(f"{i}. {point}")
            lines.append("")

        # 合并财务数据
        all_fin: Dict[str, Any] = {}
        for r in results:
            all_fin.update(r.financial_highlights)

        if all_fin:
            lines.append("## 💰 财务数据汇总\n")
            lines.append("| 指标 | 数值 |")
            lines.append("|------|------|")
            for key, val in list(all_fin.items())[:12]:
                label = key.replace('_', ' ').replace('  ', ' ')
                lines.append(f"| {label} | {val} |")
            lines.append("")

        lines.append("---")
        lines.append(f"*合并压缩时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")
        return '\n'.join(lines)

    def _get_active_dimensions(self, focus: str) -> List[str]:
        """获取活跃的分析维度。"""
        if focus == "全面":
            return list(DIMENSION_KEYWORDS.keys())
        elif focus in DIMENSION_KEYWORDS:
            return [focus]
        return ["全面"]

    def to_text(self, result: CompressResult) -> str:
        """将压缩结果转为纯文本。"""
        return result.structured_report

    def to_json(self, result: CompressResult) -> str:
        """将压缩结果序列化为 JSON。"""
        data = {
            "title": result.title,
            "summary": result.summary,
            "key_points": result.key_points,
            "financial_highlights": result.financial_highlights,
            "risk_summary": result.risk_summary,
            "focus_dimensions": result.focus_dimensions,
            "stats": result.stats,
            "source_info": result.source_info,
            "report": result.structured_report,
        }
        return json.dumps(data, ensure_ascii=False, indent=2)

    def save_report(self, result: CompressResult, output_path: str = "") -> str:
        """保存压缩报告到文件。"""
        if not output_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_title = re.sub(r'[^\w\u4e00-\u9fff]', '_', result.title)[:50]
            output_path = str(SKILL_DATA_DIR / "compressed" / f"{safe_title}_{timestamp}.md")

        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(result.structured_report)
        return output_path


# ==================== 便捷函数 ====================

_compressor = ContentCompressor()


def compress_content(source: Any, focus: str = "全面",
                     max_pages: int = 3) -> CompressResult:
    """
    一键压缩内容为 2-3 页摘要。

    Args:
        source: 文本、文件路径或解析结果
        focus: 关注维度 — 财务 / 风险 / 行业 / 政策 / 事件 / 全面
        max_pages: 目标页数

    返回: CompressResult
    """
    config = CompressConfig(focus=focus, max_pages=max_pages,
                            max_chars=max_pages * 1000)
    return _compressor.compress(source, config)


def compress_multiple(sources: List[Any], focus: str = "全面",
                      max_pages: int = 3) -> CompressResult:
    """批量压缩多个来源。"""
    config = CompressConfig(focus=focus, max_pages=max_pages,
                            max_chars=max_pages * 1000)
    return _compressor.compress_multiple(sources, config)


# ==================== CLI 入口 ====================

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("用法: python content_compressor.py <文件路径> [关注维度] [页数]")
        print("  关注维度: 财务 / 风险 / 行业 / 政策 / 事件 / 全面(默认)")
        print("  页数: 1-5 (默认3)")
        print()
        print("示例:")
        print("  python content_compressor.py report.pdf 财务 2")
        print("  python content_compressor.py \"这是一段长文本...\" 全面")
        sys.exit(1)

    source = sys.argv[1]
    focus = sys.argv[2] if len(sys.argv) > 2 else "全面"
    pages = int(sys.argv[3]) if len(sys.argv) > 3 else 3

    result = compress_content(source, focus=focus, max_pages=pages)

    print(result.structured_report)
    print(f"\n{'='*60}")
    print(f"📊 压缩统计: {json.dumps(result.stats, ensure_ascii=False)}")

    # 自动保存
    saved = _compressor.save_report(result)
    print(f"💾 已保存: {saved}")
