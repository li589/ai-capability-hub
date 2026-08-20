#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
📘 cn-financial-scraper 技能说明文档生成器
生成该 Skill 的完整功能说明 Word 文档到桌面
"""

from __future__ import annotations
import sys, os, json, zipfile
from datetime import datetime
from pathlib import Path
from xml.sax.saxutils import escape

SCRIPT_DIR = Path(__file__).resolve().parent
DATA_DIR = SCRIPT_DIR.parent / "data"
sys.path.insert(0, str(SCRIPT_DIR))

DESKTOP = Path.home() / "Desktop"
OUTPUT = DESKTOP / "cn-financial-scraper_技能说明文档.docx"

# ──── Word XML 模板 ────
CONTENT_TYPES = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
  <Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>
</Types>"""
RELS = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
</Relationships>"""
WORD_RELS = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>
</Relationships>"""
STYLES = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:styles xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:docDefaults>
    <w:rPrDefault><w:rPr><w:rFonts w:ascii="Microsoft YaHei" w:eastAsia="Microsoft YaHei" w:hAnsi="Microsoft YaHei"/><w:sz w:val="21"/></w:rPr></w:rPrDefault>
    <w:pPrDefault><w:pPr><w:spacing w:after="160" w:line="259" w:lineRule="auto"/></w:pPr></w:pPrDefault>
  </w:docDefaults>
  <w:style w:type="paragraph" w:styleId="Heading1" w:default="0">
    <w:name w:val="heading 1"/><w:pPr><w:spacing w:before="360" w:after="120"/></w:pPr>
    <w:rPr><w:b/><w:sz w:val="36"/><w:color w:val="1F4E79"/></w:rPr>
  </w:style>
  <w:style w:type="paragraph" w:styleId="Heading2" w:default="0">
    <w:name w:val="heading 2"/><w:pPr><w:spacing w:before="240" w:after="80"/></w:pPr>
    <w:rPr><w:b/><w:sz w:val="28"/><w:color w:val="2E75B6"/></w:rPr>
  </w:style>
  <w:style w:type="paragraph" w:styleId="Heading3" w:default="0">
    <w:name w:val="heading 3"/><w:pPr><w:spacing w:before="200" w:after="60"/></w:pPr>
    <w:rPr><w:b/><w:sz w:val="24"/><w:color w:val="404040"/></w:rPr>
  </w:style>
  <w:style w:type="paragraph" w:styleId="Normal" w:default="1"><w:name w:val="Normal"/><w:rPr><w:sz w:val="21"/></w:rPr></w:style>
  <w:style w:type="table" w:styleId="TableGrid" w:default="0">
    <w:name w:val="Table Grid"/><w:tblPr><w:tblBorders>
      <w:top w:val="single" w:sz="4" w:space="0" w:color="auto"/>
      <w:left w:val="single" w:sz="4" w:space="0" w:color="auto"/>
      <w:bottom w:val="single" w:sz="4" w:space="0" w:color="auto"/>
      <w:right w:val="single" w:sz="4" w:space="0" w:color="auto"/>
      <w:insideH w:val="single" w:sz="4" w:space="0" w:color="auto"/>
      <w:insideV w:val="single" w:sz="4" w:space="0" w:color="auto"/>
    </w:tblBorders></w:tblPr>
  </w:style>
</w:styles>"""

def p(text, style="Normal"):
    return f'<w:p><w:pPr><w:pStyle w:val="{style}"/></w:pPr><w:r><w:rPr><w:rFonts w:ascii="Microsoft YaHei" w:eastAsia="Microsoft YaHei"/></w:rPr><w:t xml:space="preserve">{escape(text)}</w:t></w:r></w:p>'

def p_bold(text, style="Normal"):
    return f'<w:p><w:pPr><w:pStyle w:val="{style}"/></w:pPr><w:r><w:rPr><w:b/><w:rFonts w:ascii="Microsoft YaHei" w:eastAsia="Microsoft YaHei"/></w:rPr><w:t xml:space="preserve">{escape(text)}</w:t></w:r></w:p>'

def tr(cells, bold=False, color=""):
    b = '<w:b/>' if bold else ''
    c = f'<w:color w:val="{color}"/>' if color else ''
    cx = ''.join(
        f'<w:tc><w:tcPr><w:tcW w:w="0" w:type="auto"/></w:tcPr><w:p><w:r><w:rPr>{b}{c}<w:rFonts w:ascii="Microsoft YaHei" w:eastAsia="Microsoft YaHei"/></w:rPr><w:t xml:space="preserve">{escape(str(cell))}</w:t></w:r></w:p></w:tc>'
        for cell in cells
    )
    return f'<w:tr>{cx}</w:tr>'

def load_json_counts():
    counts = []
    total = 0
    for f in sorted(DATA_DIR.glob("*_list.json")):
        try:
            with open(f, 'r', encoding='utf-8') as fh:
                data = json.load(fh)
            insts = data.get('institutions', [])
            type_name = data.get('type_name', data.get('type', f.stem))
            count = len(insts)
            source = data.get('data_source', '')
            counts.append((type_name, count, source))
            total += count
        except Exception:
            counts.append((f.stem, 0, '读取失败'))
    return counts, total

def get_mcp_tools():
    return [
        ("query_institution", "查询机构名单", "按类型/关键词查询27大类1330家金融机构"),
        ("scrape_webpage", "网页爬取", "爬取指定URL，支持静态/动态渲染模式"),
        ("scrape_institution", "机构官网爬取", "按机构名自动查找URL并爬取官网"),
        ("parse_financial_product", "产品解析", "解析基金/ETF/FOF/股票/债券页面"),
        ("crawl_financial_news", "新闻资讯", "爬取东方财富/同花顺最新金融新闻"),
        ("search_announcements", "公告搜索", "搜索沪深两市上市公司公告"),
        ("download_announcement", "公告PDF下载", "下载公告PDF到本地"),
        ("query_broker_reports", "券商研报", "查询个股研报(评级/分析师/目标价)"),
        ("get_company_reports", "综合报告", "一站式获取年报+研报+公告"),
        ("parse_document", "文档解析", "解析PDF/Word/Excel文件内容"),
        ("export_stock_report", "研报导出", "导出PPT/PDF/Word/Excel多格式"),
        ("batch_crawl_institutions", "批量爬取", "按名称列表或类型批量爬取机构"),
        ("search_report_index", "索引搜索", "在全量报告索引中搜索关键词"),
        ("analyze_document", "文档分析", "深度分析金融文档(分类/元数据/章节/财务指标/风险)"),
        ("organize_documents", "文档整理", "批量整理文档目录(分类聚合+索引+汇总)"),
        ("compare_documents", "文档对比", "多文档并排对比(指标/规模/差异高亮)"),
    ]

def get_core_modules():
    return [
        ("scraper.py", "基础爬虫", "三级降级链(Scrapling→requests→缓存)，统一爬取入口"),
        ("http_utils.py", "HTTP基础设施", "统一限流/重试/会话复用/LRU缓存/请求抖动"),
        ("web_parser.py", "网页解析器", "基金/ETF/FOF/股票/债券/投顾组合解析"),
        ("name_scraper.py", "机构名爬虫", "机构名→URL查找，反爬+双语展示+外机构翻译"),
        ("institution_scraper.py", "机构爬虫", "金融机构官网产品信息爬取"),
        ("announcement_scraper.py", "公告爬虫", "搜索+页面扫描+PDF下载"),
        ("research_report_scraper.py", "券商研报", "评级/分析师/目标价查询"),
        ("company_report_scraper.py", "公司财报", "年报/半年报/季报爬取"),
        ("news_scraper.py", "新闻爬虫", "东方财富/同花顺新闻多源获取"),
        ("document_parser.py", "文档解析", "PDF/Word/Excel/TXT内容提取"),
        ("document_analyzer.py", "文档分析", "结构化深度分析+批量整理+多文档对比"),
        ("report_exporter.py", "报告导出", "PPT/PDF/Word/Excel多格式导出"),
        ("report_indexer.py", "报告索引", "SQLite全量索引+断点续扫"),
        ("batch_institution_crawler.py", "批量爬虫", "按名称/类型/文件批量爬取"),
        ("analyzer.py", "产品分析", "风险指标/投资风格/配置建议"),
        ("adaptive_parser_v2.py", "智能解析", "AI识别各类金融页面结构"),
        ("scrapable_registry.py", "可爬注册表", "URL映射维护+增量更新"),
        ("full_institution_crawler.py", "全量爬虫", "从监管机构获取完整名单"),
        ("realtime_monitor.py", "实时监控", "动态检测页面变化/新公告"),
        ("visualization_reporter.py", "可视化报告", "ASCII图表生成"),
    ]

def build_document():
    body = []
    counts, total = load_json_counts()
    tools = get_mcp_tools()
    modules = get_core_modules()

    # 封面
    body.append(p("cn-financial-scraper", "Heading1"))
    body.append(p("中国大陆金融数据爬取与分析综合工具 — 技能说明文档", "Heading2"))
    body.append(p(f"生成日期: {datetime.now().strftime('%Y年%m月%d日')}  |  版本: 2.6.0  |  最后更新: 2026-06-26", "Normal"))
    body.append(p("", "Normal"))
    body.append(p("─" * 60, "Normal"))
    body.append(p("", "Normal"))

    # 一、概览
    body.append(p("一、技能概览", "Heading1"))
    body.append(p("cn-financial-scraper 是一个专注于中国大陆金融数据的爬取与分析综合工具。它覆盖全量金融机构名单、A股上市公司报告、券商研报、公告下载、金融产品解析、文档分析整理等场景。", "Normal"))
    body.append(p("", "Normal"))
    body.append(p_bold(f"📊 总体规模: {total} 家金融机构，覆盖 {len(counts)} 个类别"))
    body.append(p_bold(f"🔧 MCP 工具: {len(tools)} 个，通过 MCP 协议暴露给 Claude Code"))
    body.append(p_bold(f"📁 核心模块: {len(modules)} 个 Python 模块"))
    body.append(p_bold(f"📦 数据文件: {len(counts)} 个 JSON 名单文件 + 1 个机构注册表"))
    body.append(p("", "Normal"))

    # 二、机构名单
    body.append(p("二、全量金融机构名单 (27大类)", "Heading1"))
    body.append(p(f"注册表文件: data/institution_registry.json（{total}家，紧凑列式存储）", "Normal"))
    body.append(p("", "Normal"))
    body.append('<w:tbl><w:tblPr><w:tblStyle w:val="TableGrid"/><w:tblW w:w="5000" w:type="pct"/></w:tblPr>')
    body.append(tr(["序号", "机构类别", "数量", "数据来源"], bold=True, color="1F4E79"))
    for i, (name, cnt, src) in enumerate(counts, 1):
        body.append(tr([str(i), name, str(cnt), src[:25]]))
    body.append('</w:tbl>')
    body.append(p("", "Normal"))

    # 三、MCP 工具
    body.append(p(f"三、MCP 工具清单 ({len(tools)}个)", "Heading1"))
    body.append(p("通过 MCP 协议暴露的工具，可在 Claude Code 中直接调用：", "Normal"))
    body.append(p("", "Normal"))
    body.append('<w:tbl><w:tblPr><w:tblStyle w:val="TableGrid"/><w:tblW w:w="5000" w:type="pct"/></w:tblPr>')
    body.append(tr(["#", "工具名称", "分类", "功能说明"], bold=True, color="1F4E79"))
    cat_names = ["机构查询", "网页爬取", "产品解析", "新闻资讯", "公告管理", "券商研报", "综合报告", "文档解析", "报告导出", "批量操作", "索引搜索", "文档分析"]
    cat_map = {
        "query_institution": 0, "scrape_webpage": 1, "scrape_institution": 1, "parse_financial_product": 2,
        "crawl_financial_news": 3, "search_announcements": 4, "download_announcement": 4,
        "query_broker_reports": 5, "get_company_reports": 6, "parse_document": 7,
        "export_stock_report": 8, "batch_crawl_institutions": 9, "search_report_index": 10,
        "analyze_document": 11, "organize_documents": 11, "compare_documents": 11,
    }
    for i, (name, cat, desc) in enumerate(tools, 1):
        cat_idx = cat_map.get(name, 0)
        body.append(tr([str(i), name, cat_names[cat_idx], desc]))
    body.append('</w:tbl>')
    body.append(p("", "Normal"))

    # 四、核心模块
    body.append(p("四、核心模块架构 (20个)", "Heading1"))
    body.append(p("", "Normal"))
    body.append('<w:tbl><w:tblPr><w:tblStyle w:val="TableGrid"/><w:tblW w:w="5000" w:type="pct"/></w:tblPr>')
    body.append(tr(["模块文件", "功能"], bold=True, color="1F4E79"))
    for name, cat, desc in modules:
        body.append(tr([name, desc]))
    body.append('</w:tbl>')
    body.append(p("", "Normal"))

    # 五、数据源
    body.append(p("五、数据来源", "Heading1"))
    body.append(p("• 行业协会公开名单 — 银行/保险/信托/金融租赁等持牌机构名单", "Normal"))
    body.append(p("• 行业协会公开名单 — 券商/基金/期货/外资机构名单", "Normal"))
    body.append(p("• 中国证券投资基金业协会 — 私募基金管理人名单", "Normal"))
    body.append(p("• 中国期货业协会 — 期货公司/风险管理子公司名单", "Normal"))
    body.append(p("• 中国财务公司协会 — 企业集团财务公司名单", "Normal"))
    body.append(p("• 东方财富 — 实时行情/财报/研报/新闻/公告数据", "Normal"))
    body.append(p("• 天天基金 — 基金净值/持仓/规模数据", "Normal"))
    body.append(p("• 各机构官网 — 银行/基金/券商官网产品信息", "Normal"))
    body.append(p("", "Normal"))

    # 六、爬取架构
    body.append(p("六、爬取架构", "Heading1"))
    body.append(p("三级降级链: Scrapling 隐身模式 → requests 标准请求 → 本地缓存", "Normal"))
    body.append(p("• 限流策略: 按域名独立限流(1~3s)，请求抖动(±30%)，指数退避(1.5x)", "Normal"))
    body.append(p("• 缓存机制: 按域名设置TTL(1~24h)，LRU内存缓存(128条)，文件缓存", "Normal"))
    body.append(p("• User-Agent: 桌面Chrome/移动端Safari随机切换", "Normal"))
    body.append(p("• 反爬对抗: Scrapling StealthyFetcher隐身注入，Playwright动态渲染", "Normal"))
    body.append(p("", "Normal"))

    # 七、文档分析整理
    body.append(p("七、文档分析整理系统", "Heading1"))
    body.append(p("• 单文档深度分析：自动分类(年报/研报/公告等)，提取标题/机构/日期/股票代码等元数据", "Normal"))
    body.append(p("• 章节结构化：按层级正则切分章节，提取财务指标(营收/净利/EPS/ROE等)、风险因素、术语表", "Normal"))
    body.append(p("• 批量整理：扫描目录逐份分析，按类别聚合，生成索引与汇总报告(data/document_index/)", "Normal"))
    body.append(p("• 多文档对比：并排提取相同维度(类型/日期/关键指标/规模)，高亮差异", "Normal"))
    body.append(p("", "Normal"))

    # 八、优化建议
    body.append(p("八、代码优化建议", "Heading1"))
    body.append(p("以下为代码审查发现的问题：", "Normal"))
    body.append(p("", "Normal"))
    body.append(p("1️⃣ 版本号不一致（已修复）", "Heading3"))
    body.append(p("__init__.py 中 __version__ 已从 2.1.0 修复为 2.6.0，与 _meta.json 一致。", "Normal"))
    body.append(p("", "Normal"))
    body.append(p("2️⃣ crawl_utils 模块缺失", "Heading3"))
    body.append(p("batch_institution_crawler.py 尝试导入 crawl_utils 模块，该模块不存在。导入失败有 try/except 兜底，但建议移除死代码或创建该模块。", "Normal"))
    body.append(p("", "Normal"))
    body.append(p("3️⃣ 招商银行URL错误（已修复）", "Heading3"))
    body.append(p("scrapable_registry.py 中招商银行URL已从 cmbc.com.cn（民生银行）修复为 cmbchina.com（招商银行）。", "Normal"))
    body.append(p("", "Normal"))
    body.append(p("4️⃣ 数据描述不一致（已修复）", "Heading3"))
    body.append(p("_meta.json 已更新描述：918家/17类 → 1330家/27大类，与实际数据一致。", "Normal"))
    body.append(p("", "Normal"))
    body.append(p("5️⃣ 导入模式不一致", "Heading3"))
    body.append(p("mcp_server.py 中 web_parser 使用 importlib.import_module 延迟加载，其他模块使用顶层 import。建议统一为顶层导入。", "Normal"))
    body.append(p("", "Normal"))
    body.append(p("6️⃣ 缺少单元测试", "Heading3"))
    body.append(p("整个项目无任何测试文件。建议为以下关键模块添加测试：scraper.py（爬取降级链）、http_utils.py（限流/缓存）、web_parser.py（产品解析）、document_analyzer.py（文档分析CRUD）。", "Normal"))
    body.append(p("", "Normal"))

    # 页脚
    body.append(p("─" * 60, "Normal"))
    body.append(p(f"文档自动生成于 {datetime.now().strftime('%Y-%m-%d %H:%M')}  |  Reasonix AI", "Normal"))
    body.append(p("本文档仅供参考，实际功能以代码为准。", "Normal"))

    return ''.join(body)

def generate():
    print("📘 正在生成 cn-financial-scraper 技能说明文档...")
    body = build_document()

    doc_xml = f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"
            xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
<w:body>
{body}
<w:sectPr><w:pgSz w:w="11906" w:h="16838"/><w:pgMar w:top="1440" w:right="1440" w:bottom="1440" w:left="1440" w:header="720" w:footer="720"/></w:sectPr>
</w:body>
</w:document>'''

    with zipfile.ZipFile(OUTPUT, 'w', zipfile.ZIP_DEFLATED) as docx:
        docx.writestr('[Content_Types].xml', CONTENT_TYPES)
        docx.writestr('_rels/.rels', RELS)
        docx.writestr('word/_rels/document.xml.rels', WORD_RELS)
        docx.writestr('word/document.xml', doc_xml.encode('utf-8'))
        docx.writestr('word/styles.xml', STYLES)

    size = os.path.getsize(OUTPUT)
    print(f"\n✅ 文档已生成!")
    print(f"📄 {OUTPUT}")
    print(f"📏 {size:,} 字节")

if __name__ == '__main__':
    generate()
