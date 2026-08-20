# -*- coding: utf-8 -*-
"""
研究报告全流程生成器 v4.0
编排"数据采集 → 分析压缩 → 报告写作 → 图表生成 → 多格式导出"完整流程。

核心流程：
1. 数据采集：爬取网页/解析文件/查询API
2. 分析压缩：提取关键信息，压缩为结构化摘要
3. 报告写作：模板填充 + 数据注入 + 自然语言衔接
4. 图表生成：自动识别数据生成趋势图/柱状图/饼图
5. 多格式导出：Markdown → PDF/Word/PPT/HTML

最终产出：图文并茂、有理有据的研究报告
"""

import os
import re
import json
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum

SKILL_DATA_DIR = Path(__file__).parent.parent / "data"
REPORTS_OUTPUT_DIR = SKILL_DATA_DIR / "generated_reports"
REPORTS_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# ==================== 配置结构 ====================

class ReportTheme(str, Enum):
    """报告主题"""
    STOCK_RESEARCH = "stock_research"
    INDUSTRY_ANALYSIS = "industry_analysis"
    FUND_EVALUATION = "fund_evaluation"
    INSTITUTION_SURVEY = "institution_survey"
    MARKET_WEEKLY = "market_weekly"
    ANNOUNCEMENT_BRIEF = "announcement_brief"
    CUSTOM = "custom"


class OutputFormat(str, Enum):
    MARKDOWN = "markdown"
    PDF = "pdf"
    DOCX = "docx"
    PPTX = "pptx"
    HTML = "html"
    ALL = "all"


@dataclass
class ReportConfig:
    """研究报告生成配置"""
    theme: ReportTheme = ReportTheme.STOCK_RESEARCH
    title: str = ""
    subtitle: str = ""
    author: str = "cn-financial-scraper"

    # 数据源
    urls: List[str] = field(default_factory=list)  # 要爬取的URL
    files: List[str] = field(default_factory=list)  # 要解析的文件
    stock_codes: List[str] = field(default_factory=list)  # 股票代码
    fund_codes: List[str] = field(default_factory=list)  # 基金代码
    keywords: List[str] = field(default_factory=list)  # 搜索关键词
    institution_types: List[str] = field(default_factory=list)  # 机构类型
    custom_data: Dict[str, Any] = field(default_factory=dict)  # 自定义数据

    # 分析配置
    focus_dimension: str = "全面"  # 财务 / 风险 / 行业 / 政策 / 事件 / 全面
    max_pages: int = 10  # 目标页数
    include_charts: bool = True
    include_tables: bool = True
    include_risk: bool = True

    # 输出配置
    output_formats: List[OutputFormat] = field(default_factory=lambda: [OutputFormat.MARKDOWN])
    output_dir: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {k: v.value if isinstance(v, Enum) else v for k, v in self.__dict__.items()}


@dataclass
class ReportResult:
    """报告生成结果"""
    config: ReportConfig
    title: str
    template_id: str
    markdown_content: str = ""
    chart_paths: List[str] = field(default_factory=list)
    output_files: Dict[str, str] = field(default_factory=dict)  # {format: path}
    stats: Dict[str, Any] = field(default_factory=dict)
    data_sources: Dict[str, Any] = field(default_factory=dict)
    created_at: str = ""

    def to_summary(self) -> str:
        """生成结果摘要。"""
        lines = [
            f"📊 研究报告已生成",
            f"标题: {self.title}",
            f"模板: {self.template_id}",
            f"字数: {len(self.markdown_content):,}",
            f"图表: {len(self.chart_paths)}张",
            f"输出文件: {len(self.output_files)}个",
        ]
        for fmt, path in self.output_files.items():
            lines.append(f"  - [{fmt.upper()}]: {path}")
        return '\n'.join(lines)


# ==================== 生成器主体 ====================

class ResearchReportGenerator:
    """
    研究报告全流程生成器。
    编排5个阶段：采集 → 压缩 → 写作 → 图表 → 导出。
    """

    def __init__(self, output_dir: str = ""):
        self.output_dir = Path(output_dir) if output_dir else REPORTS_OUTPUT_DIR
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate(self, config: ReportConfig) -> ReportResult:
        """
        生成研究报告。

        Args:
            config: 报告配置

        返回: ReportResult
        """
        start_time = datetime.now()
        result = ReportResult(
            config=config,
            title=config.title or self._auto_title(config),
            template_id=config.theme.value,
            created_at=start_time.strftime("%Y-%m-%d %H:%M:%S"),
        )

        print(f"🚀 开始生成报告: {result.title}")

        # Phase 1: 数据采集
        print("📥 Phase 1/5: 数据采集...")
        collected_data = self._collect_data(config)
        result.data_sources = {
            "urls_used": len(config.urls),
            "files_parsed": len(config.files),
            "stocks_queried": len(config.stock_codes),
            "items_collected": len(collected_data.get("items", [])),
            "total_chars": len(str(collected_data)),
        }
        print(f"   采集: {result.data_sources['items_collected']} 条数据")

        # Phase 2: 分析压缩
        print("🔍 Phase 2/5: 分析压缩...")
        compressed = self._compress_data(collected_data, config)
        print(f"   压缩: {len(str(compressed)):,} 字符")

        # Phase 3: 报告写作
        print("✍️ Phase 3/5: 报告写作...")
        written = self._write_report(compressed, config)
        result.markdown_content = written.get("markdown", "")
        print(f"   写作: {len(result.markdown_content):,} 字符")

        # Phase 4: 图表生成
        if config.include_charts:
            print("📊 Phase 4/5: 图表生成...")
            result.chart_paths = self._generate_charts(collected_data, compressed, config)
            print(f"   图表: {len(result.chart_paths)} 张")

            # 如果有图表，重新注入到报告中
            if result.chart_paths:
                result.markdown_content = self._inject_charts_to_markdown(
                    result.markdown_content, result.chart_paths
                )

        # Phase 5: 多格式导出
        print("📦 Phase 5/5: 导出...")
        result.output_files = self._export(result, config)
        print(f"   导出: {len(result.output_files)} 种格式")

        # 统计
        elapsed = (datetime.now() - start_time).total_seconds()
        result.stats = {
            "elapsed_seconds": elapsed,
            "markdown_chars": len(result.markdown_content),
            "chart_count": len(result.chart_paths),
            "output_formats": list(result.output_files.keys()),
            "data_items": result.data_sources["items_collected"],
            "template": config.theme.value,
        }

        print(f"✅ 报告生成完成! ({elapsed:.1f}s)")
        return result

    def quick_report(self, source: Any,
                     theme: Union[str, ReportTheme] = ReportTheme.STOCK_RESEARCH,
                     title: str = "",
                     focus: str = "全面") -> ReportResult:
        """
        快速生成报告（从单个来源）。

        Args:
            source: URL / 文件路径 / 文本内容 / 股票代码
            theme: 报告主题
            title: 报告标题
            focus: 关注维度

        返回: ReportResult
        """
        if isinstance(theme, str):
            theme = ReportTheme(theme)

        config = ReportConfig(
            theme=theme,
            title=title,
            focus_dimension=focus,
        )

        # 自动识别 source 类型
        if isinstance(source, str):
            if source.startswith(('http://', 'https://')):
                config.urls = [source]
            elif os.path.isfile(source):
                config.files = [source]
            elif re.match(r'^\d{6}$', source):
                config.stock_codes = [source]
            else:
                config.custom_data = {"raw_text": source}

        return self.generate(config)

    # ---------- Phase 1: 数据采集 ----------

    def _collect_data(self, config: ReportConfig) -> Dict[str, Any]:
        """采集所有数据源。"""
        collected: Dict[str, Any] = {"items": [], "financial": {}, "metadata": {}}

        # 爬取 URL
        for url in config.urls:
            try:
                item = self._scrape_url(url)
                if item:
                    collected["items"].append(item)
            except Exception as e:
                collected["items"].append({"url": url, "error": str(e)})

        # 解析文件
        for fp in config.files:
            try:
                item = self._parse_file(fp)
                if item:
                    collected["items"].append(item)
            except Exception as e:
                collected["items"].append({"file": fp, "error": str(e)})

        # 查询股票
        for code in config.stock_codes:
            try:
                item = self._query_stock(code)
                if item:
                    collected["items"].append(item)
            except Exception as e:
                collected["items"].append({"stock": code, "error": str(e)})

        # 查询基金
        for code in config.fund_codes:
            try:
                item = self._query_fund(code)
                if item:
                    collected["items"].append(item)
            except Exception as e:
                collected["items"].append({"fund": code, "error": str(e)})

        # 搜索关键词
        for kw in config.keywords:
            try:
                items = self._search_keyword(kw)
                collected["items"].extend(items)
            except Exception:
                pass

        # 自定义数据
        if config.custom_data:
            collected["items"].append(config.custom_data)

        return collected

    def _scrape_url(self, url: str) -> Optional[Dict[str, Any]]:
        """爬取 URL。"""
        try:
            from scraper import FinancialPageScraper
            scraper = FinancialPageScraper()
            content = scraper.scrape_url(url)
            if content:
                return {"source": url, "type": "webpage", "content": str(content)[:5000]}
        except ImportError:
            pass
        return None

    def _parse_file(self, file_path: str) -> Optional[Dict[str, Any]]:
        """解析文件。"""
        try:
            from enhanced_parser import MultiFormatParser
            parser = MultiFormatParser()
            result = parser.parse(file_path)
            return {"source": file_path, "type": "file", **result}
        except ImportError:
            try:
                from document_parser import parse_document
                result = parse_document(file_path)
                return {"source": file_path, "type": "file", **result}
            except ImportError:
                pass
        return None

    def _query_stock(self, code: str) -> Optional[Dict[str, Any]]:
        """查询股票数据。"""
        try:
            from comprehensive_report_scraper import ComprehensiveReportManager
            mgr = ComprehensiveReportManager()
            data = mgr.get_all_reports(code)
            if data:
                return {"source": code, "type": "stock", "code": code,
                       "data": {k: str(v)[:1000] for k, v in (data or {}).items()}}
        except ImportError:
            pass
        return None

    def _query_fund(self, code: str) -> Optional[Dict[str, Any]]:
        """查询基金数据。"""
        try:
            from http_utils import fetch_text
            url = f"https://fund.eastmoney.com/f10/F10DataApi.aspx?type=lsjz&code={code}&page=1&per=10"
            text = fetch_text(url)
            if text:
                return {"source": code, "type": "fund", "code": code, "content": text[:3000]}
        except ImportError:
            pass
        return None

    def _search_keyword(self, keyword: str) -> List[Dict[str, Any]]:
        """搜索关键词。"""
        items = []
        try:
            from announcement_scraper import AnnouncementManager
            mgr = AnnouncementManager()
            results = mgr.search(keyword, limit=5)
            for r in results:
                items.append({"source": keyword, "type": "announcement", **r})
        except ImportError:
            pass
        return items

    # ---------- Phase 2: 分析压缩 ----------

    def _compress_data(self, collected: Dict[str, Any],
                       config: ReportConfig) -> Dict[str, Any]:
        """压缩采集的数据。"""
        try:
            from content_compressor import compress_content, CompressConfig

            items = collected.get("items", [])
            if not items:
                return {"summary": "无数据", "key_points": ["未采集到有效数据"]}

            # 合并所有文本
            texts = []
            for item in items:
                content = item.get("content") or item.get("text_content") or json.dumps(item, ensure_ascii=False)
                texts.append(content)

            combined = "\n\n---\n\n".join(texts[:30])
            cc = CompressConfig(focus=config.focus_dimension, max_pages=3)
            result = compress_content(combined, focus=config.focus_dimension)

            return {
                "title": result.title,
                "summary": result.summary,
                "key_points": result.key_points,
                "financial": result.financial_highlights,
                "risks": result.risk_summary,
                "structured_report": result.structured_report,
            }
        except ImportError:
            items = collected.get("items", [])
            return {
                "summary": f"共采集 {len(items)} 条数据",
                "key_points": [],
                "financial": {},
                "risks": [],
                "raw_items": items,
            }

    # ---------- Phase 3: 报告写作 ----------

    def _write_report(self, compressed: Dict[str, Any],
                      config: ReportConfig) -> Dict[str, Any]:
        """撰写报告。"""
        try:
            from financial_writer import FinancialWriter, WriterConfig
            writer = FinancialWriter()

            # 映射压缩结果到报告数据
            report_data = {
                "report_title": config.title or compressed.get("title", "研究报告"),
                "report_date": datetime.now().strftime("%Y-%m-%d"),
                "author": config.author,
                "摘要": compressed.get("summary", ""),
                "核心要点": compressed.get("key_points", []),
                "财务数据": compressed.get("financial", {}),
                "风险提示": compressed.get("risks", []),
            }

            # 合并自定义数据
            if config.custom_data:
                report_data.update(config.custom_data)

            wc = WriterConfig(
                template_id=config.theme.value,
                include_charts=config.include_charts,
                focus_dimension=config.focus_dimension,
            )
            return writer.write(report_data, wc)
        except ImportError:
            # 直接使用模板渲染
            try:
                from report_templates import render_template
                md = render_template(config.theme.value, compressed, config.title)
                return {"markdown": md}
            except ImportError:
                return {"markdown": f"# {config.title}\n\n{compressed.get('summary', '')}"}

    # ---------- Phase 4: 图表生成 ----------

    def _generate_charts(self, collected: Dict[str, Any],
                         compressed: Dict[str, Any],
                         config: ReportConfig) -> List[str]:
        """生成图表。"""
        charts = []

        try:
            from financial_writer import ChartBuilder, ChartConfig as CC
            builder = ChartBuilder()

            # 1. 财务数据柱状图
            fin = compressed.get("financial", {})
            if fin and isinstance(fin, dict):
                numeric = {}
                for k, v in list(fin.items())[:8]:
                    try:
                        numeric[k] = float(v)
                    except (ValueError, TypeError):
                        pass
                if numeric:
                    path = builder.bar_chart(
                        numeric,
                        CC(title="核心财务指标", color_palette="finance")
                    )
                    if path and not path.startswith("[图表"):
                        charts.append(path)

            # 2. 从收集的数据中提取可图表化的数据
            for item in collected.get("items", []):
                chart_data = item.get("chart_data")
                if chart_data and isinstance(chart_data, dict):
                    path = builder.bar_chart(
                        chart_data,
                        CC(title=item.get("name", "数据对比"))
                    )
                    if path and not path.startswith("[图表"):
                        charts.append(path)

        except ImportError:
            pass

        return charts

    def _inject_charts_to_markdown(self, markdown: str,
                                    chart_paths: List[str]) -> str:
        """将图表图片引用注入到 Markdown 中。"""
        chart_dir = "charts"
        for i, cp in enumerate(chart_paths):
            fname = Path(cp).name
            img_ref = f"\n\n![图表 {i+1}]({chart_dir}/{fname})\n\n*图 {i+1}: 数据可视化*\n"

            # 在第一个 ## 标题后插入图表
            sec_match = list(re.finditer(r'^## .+$', markdown, re.MULTILINE))
            if i < len(sec_match):
                insert_pos = sec_match[i].end()
                markdown = markdown[:insert_pos] + img_ref + markdown[insert_pos:]
            else:
                markdown += img_ref

        return markdown

    # ---------- Phase 5: 多格式导出 ----------

    def _export(self, result: ReportResult, config: ReportConfig) -> Dict[str, str]:
        """导出为多种格式。"""
        output_files = {}
        base_name = re.sub(r'[^\w\u4e00-\u9fff]', '_', result.title)[:60]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # 保存 Markdown
        md_path = str(self.output_dir / f"{base_name}_{timestamp}.md")
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(result.markdown_content)
        output_files["markdown"] = md_path

        # 导出其他格式
        for fmt in config.output_formats:
            if fmt == OutputFormat.MARKDOWN:
                continue  # 已保存

            try:
                if fmt == OutputFormat.DOCX:
                    docx_path = self._export_docx(result, base_name, timestamp)
                    if docx_path:
                        output_files["docx"] = docx_path
                elif fmt == OutputFormat.PPTX:
                    pptx_path = self._export_pptx(result, base_name, timestamp)
                    if pptx_path:
                        output_files["pptx"] = pptx_path
                elif fmt == OutputFormat.HTML:
                    html_path = self._export_html(result, base_name, timestamp)
                    if html_path:
                        output_files["html"] = html_path
                elif fmt == OutputFormat.PDF:
                    pdf_path = self._export_pdf(result, base_name, timestamp)
                    if pdf_path:
                        output_files["pdf"] = pdf_path
            except Exception as e:
                print(f"   ⚠️ {fmt.value} 导出失败: {e}")

        return output_files

    def _export_docx(self, result: ReportResult, base_name: str,
                     timestamp: str) -> Optional[str]:
        """导出 Word。"""
        try:
            from report_exporter import WordExporter
            exporter = WordExporter()
            if exporter.docx_available:
                doc = exporter.create_document()
                if doc:
                    doc.add_heading(result.title, 0)
                    # 将 Markdown 段落转换为 Word 段落
                    for para in result.markdown_content.split('\n\n'):
                        if para.startswith('#'):
                            heading_match = re.match(r'^#+', para)
                            level = len(heading_match.group()) if heading_match else 1  # v4.4.0: None 安全
                            doc.add_heading(para.lstrip('#').strip(), min(level, 3))
                        elif para.strip():
                            doc.add_paragraph(para.strip())

                    path = str(self.output_dir / f"{base_name}_{timestamp}.docx")
                    doc.save(path)
                    return path
        except ImportError:
            pass
        return None

    def _export_pptx(self, result: ReportResult, base_name: str,
                     timestamp: str) -> Optional[str]:
        """导出 PPT。"""
        try:
            from report_exporter import PPTExporter
            exporter = PPTExporter()
            if exporter.pptx_available:
                prs = exporter.create_presentation()
                if prs:
                    # 标题页
                    slide_layout = prs.slide_layouts[0]
                    slide = prs.slides.add_slide(slide_layout)
                    slide.shapes.title.text = result.title

                    # 内容页（按 ## 分段）
                    sections = re.split(r'\n## ', result.markdown_content)
                    for section in sections[1:6]:  # 最多5页内容
                        lines = section.split('\n', 1)
                        sec_title = lines[0].strip()
                        sec_content = lines[1][:500] if len(lines) > 1 else ""
                        slide_layout = prs.slide_layouts[1]
                        slide = prs.slides.add_slide(slide_layout)
                        slide.shapes.title.text = sec_title[:100]

                    path = str(self.output_dir / f"{base_name}_{timestamp}.pptx")
                    prs.save(path)
                    return path
        except ImportError:
            pass
        return None

    def _export_html(self, result: ReportResult, base_name: str,
                     timestamp: str) -> str:
        """导出 HTML。"""
        html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{result.title}</title>
<style>
body {{ font-family: "Microsoft YaHei", "SimHei", sans-serif; max-width: 900px; margin: 0 auto; padding: 20px; line-height: 1.8; color: #333; }}
h1 {{ color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 10px; }}
h2 {{ color: #2980b9; margin-top: 30px; }}
table {{ border-collapse: collapse; width: 100%; margin: 15px 0; }}
th, td {{ border: 1px solid #ddd; padding: 8px 12px; text-align: left; }}
th {{ background-color: #3498db; color: white; }}
img {{ max-width: 100%; height: auto; }}
blockquote {{ border-left: 4px solid #3498db; padding-left: 15px; color: #555; margin: 15px 0; }}
</style>
</head>
<body>
{self._md_to_html(result.markdown_content)}
<hr>
<p><em>报告由 cn-financial-scraper v4.0 自动生成 | {result.created_at}</em></p>
</body>
</html>"""
        path = str(self.output_dir / f"{base_name}_{timestamp}.html")
        with open(path, 'w', encoding='utf-8') as f:
            f.write(html)
        return path

    def _export_pdf(self, result: ReportResult, base_name: str,
                    timestamp: str) -> Optional[str]:
        """导出 PDF（v6.0.0: Playwright 渲染 HTML → 真实 PDF）。"""
        # 先导出 HTML，再尝试转换
        html_path = self._export_html(result, base_name, timestamp)
        pdf_path = str(self.output_dir / f"{base_name}_{timestamp}.pdf")

        # v6.0.0: 首选 Playwright（中文渲染好，已随浏览器模块提供）
        try:
            from playwright.sync_api import sync_playwright
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                page.goto(f"file:///{Path(html_path).resolve().as_posix()}")
                page.pdf(path=pdf_path, format="A4", print_background=True,
                         margin={"top": "15mm", "bottom": "15mm",
                                 "left": "15mm", "right": "15mm"})
                browser.close()
            if os.path.exists(pdf_path):
                return pdf_path
        except Exception:
            pass

        # 次选 wkhtmltopdf（外部工具）
        try:
            import subprocess
            subprocess.run(
                ["wkhtmltopdf", "--encoding", "UTF-8", html_path, pdf_path],
                capture_output=True, timeout=30
            )
            if os.path.exists(pdf_path):
                return pdf_path
        except Exception:
            pass

        # 如果无法生成 PDF，返回 HTML
        print("   💡 PDF 需要 Playwright 或 wkhtmltopdf，已导出 HTML 替代")
        return html_path

    # ---------- 辅助方法 ----------

    def _auto_title(self, config: ReportConfig) -> str:
        """自动生成标题。"""
        theme_names = {
            ReportTheme.STOCK_RESEARCH: "个股深度研究报告",
            ReportTheme.INDUSTRY_ANALYSIS: "行业分析报告",
            ReportTheme.FUND_EVALUATION: "基金评价报告",
            ReportTheme.INSTITUTION_SURVEY: "机构调研报告",
            ReportTheme.MARKET_WEEKLY: "市场周度观察报告",
            ReportTheme.ANNOUNCEMENT_BRIEF: "公告解读报告",
        }
        base = theme_names.get(config.theme, "研究报告")

        if config.stock_codes:
            return f"{base}: {config.stock_codes[0]}"
        if config.fund_codes:
            return f"{base}: {config.fund_codes[0]}"

        return f"{base} ({datetime.now().strftime('%Y-%m-%d')})"

    def _md_to_html(self, md: str) -> str:
        """简易 Markdown → HTML 转换。"""
        html = md
        # 标题
        html = re.sub(r'^### (.+)$', r'<h3>\1</h3>', html, flags=re.MULTILINE)
        html = re.sub(r'^## (.+)$', r'<h2>\1</h2>', html, flags=re.MULTILINE)
        html = re.sub(r'^# (.+)$', r'<h1>\1</h1>', html, flags=re.MULTILINE)
        # 粗体
        html = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', html)
        # 图片
        html = re.sub(r'!\[(.+?)\]\((.+?)\)', r'<img src="\2" alt="\1">', html)
        # 引用
        html = re.sub(r'^> (.+)$', r'<blockquote>\1</blockquote>', html, flags=re.MULTILINE)
        # 分隔线
        html = re.sub(r'^---$', '<hr>', html, flags=re.MULTILINE)
        # 列表
        html = re.sub(r'^- (.+)$', r'<li>\1</li>', html, flags=re.MULTILINE)
        # 段落
        html = re.sub(r'\n\n', '</p><p>', html)
        html = f'<p>{html}</p>'
        return html


# ==================== 便捷函数 ====================

_generator = ResearchReportGenerator()


def generate_research_report(source: Any,
                              theme: str = "stock_research",
                              title: str = "",
                              focus: str = "全面",
                              output_formats: Optional[List[str]] = None) -> ReportResult:
    """
    一键生成研究报告。

    Args:
        source: URL/文件路径/文本/股票代码
        theme: stock_research / industry_analysis / fund_evaluation / ...
        title: 报告标题
        focus: 关注维度（财务/风险/行业/政策/事件/全面）
        output_formats: 输出格式列表 ['markdown', 'pdf', 'docx', 'pptx', 'html']
    """
    config = ReportConfig(
        theme=ReportTheme(theme),
        title=title,
        focus_dimension=focus,
    )

    # 设置输出格式
    if output_formats:
        config.output_formats = [OutputFormat(f) for f in output_formats if f != "markdown"]

    # 识别 source
    if isinstance(source, str):
        if source.startswith(('http://', 'https://')):
            config.urls = [source]
        elif os.path.isfile(source):
            config.files = [source]
        elif re.match(r'^\d{6}$', source):
            config.stock_codes = [source]
        else:
            config.custom_data = {"raw_text": source}

    return _generator.generate(config)


def quick_report(source: Any, theme: str = "stock_research",
                 title: str = "", focus: str = "全面") -> ReportResult:
    """快速生成报告（别名）。"""
    return _generator.quick_report(source, ReportTheme(theme), title, focus)


# ==================== CLI 入口 ====================

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("研究报告生成器 v4.0")
        print("\n用法:")
        print("  python research_report_generator.py <来源> [主题] [标题]")
        print()
        print("来源: URL / 文件路径 / 股票代码 / 文本")
        print("主题: stock_research / industry_analysis / fund_evaluation / "
              "institution_survey / market_weekly / announcement_brief")
        print()
        print("示例:")
        print("  python research_report_generator.py 600519 stock_research \"贵州茅台深度研报\"")
        print("  python research_report_generator.py https://example.com/report")
        print("  python research_report_generator.py \"这是一段分析文本...\"")
        sys.exit(1)

    source = sys.argv[1]
    theme = sys.argv[2] if len(sys.argv) > 2 else "stock_research"
    title = sys.argv[3] if len(sys.argv) > 3 else ""

    result = generate_research_report(source, theme=theme, title=title)

    print(result.to_summary())
    print(f"\n--- 报告预览 (前800字) ---")
    preview = result.markdown_content[:800]
    print(preview)
    print(f"\n... 全文 {len(result.markdown_content):,} 字，详见输出文件。")
