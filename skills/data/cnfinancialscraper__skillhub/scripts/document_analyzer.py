# -*- coding: utf-8 -*-
"""
金融文档分析整理模块
在 document_parser 基础上构建结构化分析层：
- 单文档深度分析（分类/元数据/章节/财务指标/风险因素/术语表）
- 批量整理目录（扫描+逐份分析+分类聚合+索引+汇总）
- 多文档并排对比（同维度提取+差异高亮）
零新外部依赖（复用 PyPDF2/python-docx/openpyxl，正则+启发式分类）。
"""

import re
import json
import os as _os
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime

try:
    from document_parser import parse_document, extract_financial_numbers
except ImportError:
    def parse_document(file_path, **kw):
        return {"error": "document_parser not available"}
    def extract_financial_numbers(text):
        return {}

SKILL_DATA_DIR = Path(__file__).parent.parent / "data"
DOC_INDEX_DIR = SKILL_DATA_DIR / "document_index"


# ==================== 文档分类 ====================

DOC_CATEGORIES = [
    ("券商研报", ["研究报告", "评级推荐", "目标价", "分析师", "投资建议", "证券研究报告"], 10),
    ("公告", ["公告编号", "证券代码", "临时公告", "重大事项"], 9),
    ("年报", ["年度报告", "annual report", "年报摘要"], 8),
    ("半年报", ["半年度报告", "半年报", "中期报告"], 7),
    ("季报", ["季度报告", "一季报", "三季报"], 6),
    ("基金合同", ["基金合同", "基金托管协议", "基金管理人"], 5),
    ("招募说明书", ["招募说明书", "招募更新"], 4),
    ("财务报告", ["财务报告", "财务报表", "审计报告", "合并报表"], 3),
    ("通用金融文档", [], 0),
]

SECTION_PATTERNS = {
    "h1": re.compile(r'第[一二三四五六七八九十百零\d]+[章节篇部]\s*[^\n]{0,80}'),
    "h2": re.compile(r'^[一二三四五六七八九十]+\s*[、.．]\s*[^\n]{0,80}', re.MULTILINE),
    "h3": re.compile(r'^\d+[\.．]\s*(?!\d)[^\n]{0,80}', re.MULTILINE),
    "h4": re.compile(r'^[（\(]\d+[）\)]\s*[^\n]{0,80}', re.MULTILINE),
}

FINANCIAL_INDICATOR_PATTERNS = {
    "营业收入": r'营业(?:总)?收入[（(]?万元?[）)]?\s*[:：]?\s*([+-]?\d[\d,.]*)\s*(?:万?元?|亿?)',
    "净利润": r'(?:归属.*)?净利润[（(]?万元?[）)]?\s*[:：]?\s*([+-]?\d[\d,.]*)\s*(?:万?元?|亿?)',
    "总资产": r'总资产[（(]?万元?[）)]?\s*[:：]?\s*([+-]?\d[\d,.]*)\s*(?:万?元?|亿?)',
    "净资产": r'(?:归属.*)?净资产[（(]?万元?[）)]?\s*[:：]?\s*([+-]?\d[\d,.]*)\s*(?:万?元?|亿?)',
    "每股收益_EPS": r'(?:基本)?每股收益[（(]?EPS[）)]?\s*[:：]?\s*([+-]?\d+[\.]?\d*)',
    "市盈率_PE": r'市盈率[（(]?P[Ee][）)]?\s*[:：]?\s*([+-]?\d+[\.]?\d*)',
    "市净率_PB": r'市净率[（(]?P[Bb][）)]?\s*[:：]?\s*([+-]?\d+[\.]?\d*)',
    "净资产收益率_ROE": r'净资产收益率[（(]?ROE[）)]?\s*[:：]?\s*([+-]?\d+[\.]?\d*)\s*%?',
    "毛利率": r'毛利率\s*[:：]?\s*([+-]?\d+[\.]?\d*)\s*%',
    "资产负债率": r'资产负债率\s*[:：]?\s*([+-]?\d+[\.]?\d*)\s*%',
    "同比增速": r'(?:营业[总收]入.*)?同比[增减增速]*[:：]?\s*([+-]?\d+[\.]?\d*)\s*%',
}


# ==================== 辅助函数 ====================

def classify_document(text: str, file_path: str = "") -> Tuple[str, int]:
    """启发式文档分类。返回 (类别, 置信度 0-100)。"""
    text_head = (text or "")[:3000].lower()
    file_lower = Path(file_path).name.lower() if file_path else ""

    best_category = "通用金融文档"
    best_score = 0
    max_possible = 60

    for cat_name, keywords, priority in DOC_CATEGORIES:
        score = 0
        for kw in keywords:
            kw_lower = kw.lower()
            if re.search(kw_lower, text_head):
                score += 15
            if file_lower and re.search(kw_lower, file_lower):
                score += 20
        if score > best_score:
            best_score = score
            best_category = cat_name

    confidence = min(100, int(best_score / max_possible * 100)) if max_possible > 0 else 10
    return best_category, max(confidence, 10)


def extract_metadata(text: str, file_path: str = "") -> Dict[str, str]:
    """从文本提取元数据：标题、机构、日期、股票代码。"""
    meta = {"title": "", "institution": "", "date": "", "stock_code": ""}
    text_head = (text or "")[:2000]

    lines = [l.strip() for l in text_head.split("\n") if l.strip()]
    if lines:
        meta["title"] = lines[0][:120]
    title_match = re.search(r'(?:标题|题目|报告名称)[：:]\s*(.+?)(?:\n|$)', text_head)
    if title_match:
        meta["title"] = title_match.group(1).strip()[:120]

    inst_patterns = [
        r'([\u4e00-\u9fff]{2,8}(?:证券|基金|期货|信托|银行|保险|资产管理|资本|投资|研究))(?:(?:股份)?有限(?:公司|责任公司))?',
        r'([\u4e00-\u9fff]{2,12}(?:股份)?有限(?:公司|责任公司))',
        r'(?:发布机构|研究机构|出处|来源|作者单位)[：:]\s*([^\n]{2,40})',
    ]
    for pat in inst_patterns:
        m = re.search(pat, text_head)
        if m:
            inst = m.group(1).strip()
            if len(inst) >= 4:
                meta["institution"] = inst
                break

    date_patterns = [
        r'(\d{4})\s*[年\-\/.]\s*(\d{1,2})\s*[月\-\/.]\s*(\d{1,2})\s*日?',
        r'(\d{4})-(\d{2})-(\d{2})',
        r'(?:报告日期|发布日期|公告日期|日期)[：:]\s*(\d{4}[\-\/.]\d{1,2}[\-\/.]\d{1,2})',
    ]
    for pat in date_patterns:
        m = re.search(pat, text_head)
        if m:
            if len(m.groups()) >= 3:
                y, mo, d = m.group(1), m.group(2), m.group(3)
                try:
                    meta["date"] = f"{int(y)}-{int(mo):02d}-{int(d):02d}"
                except ValueError:
                    pass
            elif len(m.groups()) == 1:
                meta["date"] = m.group(1)
            break

    code_match = re.search(r'(?:股票代码|证券代码|标的代码|code)[：:]\s*(\d{6})', text_head)
    if code_match:
        meta["stock_code"] = code_match.group(1)
    else:
        code_match2 = re.search(r'[\(（](\d{6})[\._\s]?(?:SH|SZ|sh|sz|上证|深证)?[\)）]', text_head)
        if code_match2:
            meta["stock_code"] = code_match2.group(1)

    return meta


def extract_sections(text: str) -> List[Dict[str, Any]]:
    """提取文档章节结构。"""
    sections = []
    seen_titles = set()
    lines = text.split("\n")

    for line_no, line in enumerate(lines):
        line = line.strip()
        if not line or len(line) < 3:
            continue
        if len(line) > 150:
            continue

        level = None
        title = None

        for lvl_name, pattern in SECTION_PATTERNS.items():
            m = pattern.match(line)
            if m:
                title = m.group(0).strip()
                if title.replace(" ", "").replace(".", "").replace("．", "").isdigit():
                    continue
                level = int(lvl_name[1])
                break

        if title and level:
            norm = re.sub(r'\s+', '', title)
            if norm in seen_titles:
                continue
            seen_titles.add(norm)

            preview_start = line_no + 1
            preview_parts = []
            for l in lines[preview_start:preview_start + 5]:
                if l.strip():
                    preview_parts.append(l.strip())
            preview = " ".join(preview_parts)[:150]

            sections.append({
                "title": title,
                "level": level,
                "preview": preview,
                "line": line_no + 1,
            })

    return sections[:60]


def extract_risk_factors(text: str) -> List[str]:
    """提取风险因素/风险提示章节条目。"""
    risks = []
    risk_patterns = [
        r'(?:风险因素|风险提示|风险分析|风险管理|风险警示)(?:.{0,500}?)',
    ]
    for pat in risk_patterns:
        for m in re.finditer(pat, text):
            start = m.start()
            chunk = text[start:start + 3000]

            bullet_patterns = [
                r'[•·●◆■]\s*([^\n•·●◆■]{5,200})',
                r'(?:^|\n)\s*\d+[\.、．)]\s*([^\n]{5,200})',
                r'(?:^|\n)\s*[（\(]\d+[）\)]\s*([^\n]{5,200})',
            ]
            for bpat in bullet_patterns:
                for bm in re.finditer(bpat, chunk):
                    item = bm.group(1).strip()
                    if len(item) > 10 and item not in risks:
                        risks.append(item[:200])
                if risks:
                    break
            if risks:
                break
        if risks:
            break

    return risks[:20]


def extract_glossary(text: str) -> Dict[str, str]:
    """提取术语定义：匹配 "XX 指/系/是指/谓/意为" 模式。"""
    glossary = {}
    pattern = re.compile(
        r'([\u4e00-\u9fffA-Za-z]{2,15})\s*(?:指|系|是指|谓|意为|即|又称)\s*(.{5,120}?)(?:[。；;]|$|\n)'
    )
    for m in re.finditer(pattern, text[:5000]):
        term = m.group(1).strip()
        definition = m.group(2).strip()
        if term and definition and term not in glossary:
            glossary[term] = definition[:120]

    return dict(list(glossary.items())[:30])


def extract_financial_indicators(text: str) -> Dict[str, Any]:
    """扩展的财务指标提取（比 extract_financial_numbers 更全面）。"""
    indicators = {}
    for key, pattern in FINANCIAL_INDICATOR_PATTERNS.items():
        m = re.search(pattern, text)
        if m:
            try:
                val = m.group(1).replace(",", "")
                indicators[key] = float(val) if '.' in val else int(val)
            except (ValueError, AttributeError):
                pass
    return indicators


# ==================== DocumentAnalyzer 类 ====================

class DocumentAnalyzer:
    """金融文档分析整理器。"""

    def __init__(self):
        self._cache = {}

    def analyze(self, file_path: str) -> Dict[str, Any]:
        """
        单文档深度分析。
        返回：{file_path, file_type, doc_category, category_confidence,
               metadata, summary, sections, financial_indicators,
               risk_factors, glossary, stats}
        """
        cache_key = _os.path.abspath(file_path)
        if cache_key in self._cache:
            return self._cache[cache_key]

        result = {
            "file_path": file_path,
            "file_type": Path(file_path).suffix.lower().lstrip("."),
            "doc_category": "通用金融文档",
            "category_confidence": 0,
            "metadata": {},
            "summary": "",
            "sections": [],
            "financial_indicators": {},
            "risk_factors": [],
            "glossary": {},
            "stats": {},
        }

        parsed = parse_document(file_path)
        if parsed.get("error"):
            result["error"] = parsed["error"]
            return result

        text_content = parsed.get("text_content", "") or ""
        if not text_content.strip():
            result["error"] = "文档内容为空或无法提取文本"
            return result

        category, confidence = classify_document(text_content, file_path)
        result["doc_category"] = category
        result["category_confidence"] = confidence
        result["metadata"] = extract_metadata(text_content, file_path)
        result["sections"] = extract_sections(text_content)
        result["financial_indicators"] = extract_financial_indicators(text_content)
        # 合并 document_parser 的简单数字提取
        simple_nums = extract_financial_numbers(text_content)
        for k, v in simple_nums.items():
            if k not in result["financial_indicators"] and k not in ("amounts_yi", "total_yi", "percentages"):
                result["financial_indicators"][k] = v
        result["risk_factors"] = extract_risk_factors(text_content)
        result["glossary"] = extract_glossary(text_content)
        result["summary"] = text_content[:600].replace("\n", " ").strip()
        result["stats"] = {
            "char_count": len(text_content),
            "section_count": len(result["sections"]),
            "indicator_count": len(result["financial_indicators"]),
            "risk_count": len(result["risk_factors"]),
            "analyzed_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }

        self._cache[cache_key] = result
        return result

    def organize_directory(self, dir_path: str, recursive: bool = True) -> Dict[str, Any]:
        """
        批量整理文档目录。
        返回：{total, categories, index_file, summary_file}
        """
        dir_p = Path(dir_path)
        if not dir_p.is_dir():
            return {"error": f"目录不存在: {dir_path}"}

        supported_ext = {".pdf", ".docx", ".doc", ".xlsx", ".xls", ".txt", ".md", ".csv"}
        files = []
        if recursive:
            for f in dir_p.rglob("*"):
                if f.is_file() and f.suffix.lower() in supported_ext:
                    files.append(f)
        else:
            for f in dir_p.iterdir():
                if f.is_file() and f.suffix.lower() in supported_ext:
                    files.append(f)

        if not files:
            return {"error": "目录中没有支持的文档文件", "total": 0, "categories": {}}

        categories: Dict[str, List[Dict]] = {}
        for fp in files:
            try:
                analysis = self.analyze(str(fp))
                cat = analysis.get("doc_category", "通用金融文档")
                if cat not in categories:
                    categories[cat] = []
                categories[cat].append({
                    "file": fp.name,
                    "path": str(fp),
                    "type": analysis.get("file_type", ""),
                    "metadata": analysis.get("metadata", {}),
                    "confidence": analysis.get("category_confidence", 0),
                    "indicator_count": len(analysis.get("financial_indicators", {})),
                })
            except Exception as e:
                if "处理错误" not in categories:
                    categories["处理错误"] = []
                categories["处理错误"].append({"file": fp.name, "error": str(e)})

        total = sum(len(v) for v in categories.values())

        DOC_INDEX_DIR.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        index_file = DOC_INDEX_DIR / f"index_{timestamp}.json"
        summary_file = DOC_INDEX_DIR / f"summary_{timestamp}.md"

        index_data = {
            "source_dir": str(dir_p),
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "total_documents": total,
            "category_count": len(categories),
            "categories": {},
        }
        for cat, items in categories.items():
            index_data["categories"][cat] = {"count": len(items), "files": items}
        with open(index_file, "w", encoding="utf-8") as f:
            json.dump(index_data, f, ensure_ascii=False, indent=2)

        md_lines = [
            "# 文档目录整理报告\n",
            f"- 来源目录: {dir_p}",
            f"- 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"- 文档总数: {total}",
            f"- 类别数: {len(categories)}\n",
        ]
        for cat, items in sorted(categories.items(), key=lambda x: -len(x[1])):
            md_lines.append(f"## {cat} ({len(items)}份)")
            for item in items[:50]:
                meta = item.get("metadata", {})
                title = meta.get("title", item["file"])[:80]
                date_str = meta.get("date", "")
                inst = meta.get("institution", "")
                code = meta.get("stock_code", "")
                extras = " / ".join(filter(None, [date_str, inst, code]))
                line = f"- **{title}** ({item['type']})"
                if extras:
                    line += f" — {extras}"
                md_lines.append(line)
            md_lines.append("")
        with open(summary_file, "w", encoding="utf-8") as f:
            f.write("\n".join(md_lines))

        return {
            "total": total,
            "categories": {cat: len(items) for cat, items in categories.items()},
            "index_file": str(index_file),
            "summary_file": str(summary_file),
        }

    def compare(self, file_paths: List[str]) -> Dict[str, Any]:
        """多文档并排对比。"""
        results = []
        for fp in file_paths:
            r = self.analyze(fp)
            results.append(r)

        if not results:
            return {"compared": 0, "files": [], "dimensions": {}, "differences": []}

        dimensions = {
            "文档类型": [], "文件类型": [], "日期": [], "机构": [],
            "股票代码": [], "文档规模（字符数）": [], "章节数": [],
            "财务指标数": [], "风险因素数": [], "关键指标": [],
        }

        for r in results:
            dimensions["文档类型"].append(r.get("doc_category", ""))
            dimensions["文件类型"].append(r.get("file_type", ""))
            dimensions["日期"].append(r.get("metadata", {}).get("date", ""))
            dimensions["机构"].append(r.get("metadata", {}).get("institution", ""))
            dimensions["股票代码"].append(r.get("metadata", {}).get("stock_code", ""))
            dimensions["文档规模（字符数）"].append(r.get("stats", {}).get("char_count", 0))
            dimensions["章节数"].append(r.get("stats", {}).get("section_count", 0))
            dimensions["财务指标数"].append(r.get("stats", {}).get("indicator_count", 0))
            dimensions["风险因素数"].append(r.get("stats", {}).get("risk_count", 0))
            dimensions["关键指标"].append(r.get("financial_indicators", {}))

        differences = []
        for dim, values in dimensions.items():
            if dim == "关键指标":
                continue
            unique_vals = set(str(v) for v in values)
            if len(unique_vals) > 1:
                file_names = [Path(fp).name for fp in file_paths]
                labeled = [f"{file_names[i]}: {values[i]}" for i in range(len(values))]
                differences.append(f"[{dim}] {', '.join(labeled)}")

        return {
            "compared": len(results),
            "files": [
                {"name": Path(fp).name, "path": fp,
                 "category": r.get("doc_category", ""),
                 "summary": r.get("summary", "")[:200]}
                for fp, r in zip(file_paths, results)
            ],
            "dimensions": dimensions,
            "differences": differences,
        }

    def to_markdown(self, analysis: Dict[str, Any]) -> str:
        """将 analyze() 结果转换为结构化 Markdown 报告。"""
        if analysis.get("error"):
            return f"## 文档分析失败\n\n错误: {analysis['error']}"

        lines = [
            "# 文档分析报告\n",
            f"- **文件**: {Path(analysis['file_path']).name}",
            f"- **格式**: {analysis.get('file_type', '').upper()}",
            f"- **分类**: {analysis.get('doc_category', '未知')} (置信度: {analysis.get('category_confidence', 0)}%)",
            f"- **分析时间**: {analysis.get('stats', {}).get('analyzed_at', '')}\n",
        ]

        meta = analysis.get("metadata", {})
        if any(meta.values()):
            lines.append("## 元数据\n")
            if meta.get("title"):
                lines.append(f"- **标题**: {meta['title']}")
            if meta.get("institution"):
                lines.append(f"- **机构**: {meta['institution']}")
            if meta.get("date"):
                lines.append(f"- **日期**: {meta['date']}")
            if meta.get("stock_code"):
                lines.append(f"- **股票代码**: {meta['stock_code']}")
            lines.append("")

        lines.append("## 内容摘要\n")
        lines.append(f"> {analysis.get('summary', '无法提取摘要')[:500]}\n")

        sections = analysis.get("sections", [])
        if sections:
            lines.append(f"## 章节结构 ({len(sections)} 个章节)\n")
            for sec in sections[:30]:
                indent = "  " * (sec.get("level", 1) - 1)
                preview = sec.get('preview', '')
                lines.append(f"{indent}- **{sec['title']}**  _{preview[:80].replace(chr(10), ' ')}_\n")
            lines.append("")

        indicators = analysis.get("financial_indicators", {})
        if indicators:
            lines.append(f"## 财务指标 ({len(indicators)} 项)\n")
            for key, value in indicators.items():
                if key not in ("amounts_yi", "total_yi", "percentages"):
                    lines.append(f"- **{key}**: {value}")
            lines.append("")

        risks = analysis.get("risk_factors", [])
        if risks:
            lines.append(f"## 风险因素 ({len(risks)} 条)\n")
            for i, risk in enumerate(risks, 1):
                lines.append(f"{i}. {risk}")
            lines.append("")

        glossary = analysis.get("glossary", {})
        if glossary:
            lines.append(f"## 关键术语 ({len(glossary)} 条)\n")
            for term, defn in list(glossary.items())[:15]:
                lines.append(f"- **{term}**: {defn}")

        stats = analysis.get("stats", {})
        lines.append(f"\n---\n*文档字符数: {stats.get('char_count', 0):,}  |  "
                     f"章节: {stats.get('section_count', 0)}  |  "
                     f"指标: {stats.get('indicator_count', 0)}  |  "
                     f"风险: {stats.get('risk_count', 0)}*")

        return "\n".join(lines)


# ==================== CLI 入口 ====================

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 3:
        print("用法: python document_analyzer.py <命令> <参数>")
        print("  analyze <文件路径>       -- 深度分析单份文档")
        print("  organize <目录路径>      -- 批量整理文档目录")
        print("  compare <文件1,文件2,...> -- 对比多份文档")
        print("  markdown <文件路径>      -- 深度分析并以 Markdown 输出")
        sys.exit(1)

    cmd = sys.argv[1]
    target = sys.argv[2]
    analyzer = DocumentAnalyzer()

    if cmd == "analyze":
        result = analyzer.analyze(target)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    elif cmd == "organize":
        result = analyzer.organize_directory(target)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    elif cmd == "compare":
        paths = [p.strip() for p in target.split(",") if p.strip()]
        result = analyzer.compare(paths)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    elif cmd == "markdown":
        result = analyzer.analyze(target)
        print(analyzer.to_markdown(result))
    else:
        print(f"未知命令: {cmd}")
        sys.exit(1)
