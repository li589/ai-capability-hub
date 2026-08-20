# -*- coding: utf-8 -*-
"""
标准库文档生成器（零 pip 依赖）
使用 zipfile + xml.etree.ElementTree 生成 .docx / .pptx / .xlsx 文件。
当 python-docx / python-pptx / openpyxl 未安装时作为 fallback。

依赖：Python 标准库 only（zipfile, xml.etree.ElementTree, io, os, datetime）

OOXML 格式说明：
  .docx / .pptx / .xlsx 均为 ZIP 打包的 XML 文件（Office Open XML / ECMA-376）
  无需 lxml，标准库 xml.etree.ElementTree 可完全满足。
"""
from __future__ import annotations

import zipfile
import io
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

try:
    from report_exporter import EXPORT_DIR
except Exception:
    EXPORT_DIR = Path(__file__).parent.parent / "data" / "exports"


# ─── 辅助工具 ────────────────────────────────────────────────────────────────

def _esc(s: Any) -> str:
    """XML 文本转义"""
    if s is None:
        return ""
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def _attr(obj: Any, key: str, default: Any = "") -> Any:
    """兼容 object.attr 和 dict['attr'] 两种访问方式"""
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)


def _row_esc(s: Any) -> str:
    """单元格文本（允许换行）"""
    return _esc(str(s) if s is not None else "")


# ─── DOCX 生成器 ────────────────────────────────────────────────────────────

class StdlibDocxWriter:
    """用标准库生成最小化 .docx（Word 2007+ 兼容）"""

    def export_comprehensive_report(self, data: Dict[str, Any],
                                   stock_code: str,
                                   output_path: str = "") -> str:
        """
        生成 Word 文档（.docx）

        结构：
          [Content_Types].xml
          _rels/.rels
          word/_rels/document.xml.rels
          word/document.xml       ← 标题 + 概览表 + 列表
          word/styles.xml
        """
        if not output_path:
            os.makedirs(EXPORT_DIR, exist_ok=True)
            output_path = str(EXPORT_DIR / f"{stock_code}_report.docx")

        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        summary = data.get("summary", {})
        stock_name = summary.get("stock_name", stock_code)
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # ── 构建 document.xml ────────────────────────────────────────────────
        body_parts: List[str] = []

        # 标题
        body_parts.append(
            f'<w:p><w:pPr><w:pStyle w:val="Heading"/><w:jc w:val="center"/></w:pPr>'
            f'<w:r><w:rPr><w:b/><w:sz w:val="36"/></w:rPr>'
            f'<w:t>{_esc(stock_name)} ({stock_code}) 综合分析报告</w:t></w:r></w:p>'
        )

        # 概览标题
        body_parts.append(
            f'<w:p><w:pPr><w:pStyle w:val="Heading1"/></w:pPr>'
            f'<w:r><w:rPr><w:b/></w:rPr><w:t>报告概览</w:t></w:r></w:p>'
        )

        # 概览表格（2列，7行）
        info_rows = [
            ("股票代码", stock_code),
            ("股票名称", stock_name),
            ("定期报告", f"{summary.get('periodic_count', 0)} 份"),
            ("券商研报", f"{summary.get('broker_count', 0)} 份"),
            ("公告", f"{summary.get('announcement_count', 0)} 份"),
            ("买入评级研报", "是" if summary.get('has_buy_rating') else "否"),
            ("生成时间", now),
        ]
        tbl_xml = (
            '<w:tbl>'
            '<w:tblPr><w:tblStyle w:val="TableGrid"/><w:tblW w:w="5000" w:type="dxa"/>'
            '<w:tblBorders>'
            '<w:top w:val="single" w:sz="4" w:color="auto"/><w:left w:val="single" w:sz="4" w:color="auto"/>'
            '<w:bottom w:val="single" w:sz="4" w:color="auto"/><w:right w:val="single" w:sz="4" w:color="auto"/>'
            '<w:insideH w:val="single" w:sz="4" w:color="auto"/><w:insideV w:val="single" w:sz="4" w:color="auto"/>'
            '</w:tblBorders>'
            '</w:tblPr>'
        )
        for k, v in info_rows:
            tbl_xml += (
                '<w:tr><w:tc><w:tcPr><w:tcW w:w="2000" w:type="dxa"/></w:tcPr>'
                f'<w:p><w:r><w:rPr><w:b/></w:rPr><w:t>{_esc(k)}</w:t></w:r></w:p></w:tc>'
                '<w:tc><w:tcPr><w:tcW w:w="3000" w:type="dxa"/></w:tcPr>'
                f'<w:p><w:r><w:t>{_esc(v)}</w:t></w:r></w:p></w:tc></w:tr>'
            )
        tbl_xml += '</w:tbl>'
        body_parts.append(tbl_xml)

        # 定期报告
        periodic = data.get("periodic_reports", [])
        if periodic:
            body_parts.append(
                f'<w:p><w:pPr><w:pStyle w:val="Heading1"/></w:pPr>'
                f'<w:r><w:rPr><w:b/></w:rPr><w:t>定期报告 ({len(periodic)} 份)</w:t></w:r></w:p>'
            )
            for p in periodic:
                title = _row_esc(_attr(p, 'title', ''))
                date = str(_attr(p, 'publish_date', ''))[:10]
                url = _row_esc(_attr(p, 'url', ''))
                body_parts.append(
                    # v1.1 修复：补 </w:pPr> 闭合标签（之前漏了，导致下载保存时 Word 严格解析失败）
                    f'<w:p><w:pPr><w:numPr><w:ilvl w:val="0"/><w:numId w:val="1"/></w:numPr></w:pPr>'
                    f'<w:r><w:t xml:space="preserve">{date} - {title}</w:t></w:r></w:p>'
                )
                if url:
                    body_parts.append(
                        f'<w:p><w:pPr><w:ind w:left="360"/></w:pPr>'
                        f'<w:r><w:rPr><w:color w:val="0563C1"/><w:u w:val="single"/></w:rPr>'
                        f'<w:t xml:space="preserve">链接: {url}</w:t></w:r></w:p>'
                    )

        # 券商研报
        broker = data.get("broker_reports", [])
        if broker:
            rating_stats = {"买入": 0, "增持": 0, "中性": 0, "减持": 0}
            for b in broker:
                r = _attr(b, 'rating', '')
                if r in rating_stats:
                    rating_stats[r] += 1
            body_parts.append(
                f'<w:p><w:pPr><w:pStyle w:val="Heading1"/></w:pPr>'
                f'<w:r><w:rPr><w:b/></w:rPr><w:t>券商研报 ({len(broker)} 份)</w:t></w:r></w:p>'
            )
            body_parts.append(
                f'<w:p><w:r><w:t>评级分布: '
                f"买入{rating_stats['买入']} 增持{rating_stats['增持']} "
                f"中性{rating_stats['中性']} 减持{rating_stats['减持']}</w:t></w:r></w:p>"
            )
            for b in broker:
                title = _row_esc(_attr(b, 'title', ''))
                date = str(_attr(b, 'publish_date', ''))[:10]
                broker_name = _row_esc(_attr(b, 'broker_name', ''))
                analyst = _row_esc(_attr(b, 'analyst', ''))
                rating = _row_esc(_attr(b, 'rating', ''))
                tp = _attr(b, 'target_price', 0)
                url = _row_esc(_attr(b, 'url', ''))
                body_parts.append(
                    f'<w:p><w:r><w:rPr><w:b/></w:rPr>'
                    f'<w:t xml:space="preserve">{date} [{rating}] {broker_name}</w:t></w:r>'
                    f'<w:r><w:t xml:space="preserve">：{title}</w:t></w:r></w:p>'
                )
                if analyst:
                    body_parts.append(
                        f'<w:p><w:pPr><w:ind w:left="360"/></w:pPr>'
                        f'<w:r><w:t xml:space="preserve">分析师: {analyst}</w:t></w:r></w:p>'
                    )
                if tp and float(tp) > 0:
                    body_parts.append(
                        f'<w:p><w:pPr><w:ind w:left="360"/></w:pPr>'
                        f'<w:r><w:t xml:space="preserve">目标价: ¥{float(tp):.2f}</w:t></w:r></w:p>'
                    )
                # v4.4.0: 添加原文链接
                if url:
                    body_parts.append(
                        f'<w:p><w:pPr><w:ind w:left="360"/></w:pPr>'
                        f'<w:r><w:rPr><w:color w:val="0563C1"/><w:u w:val="single"/></w:rPr>'
                        f'<w:t xml:space="preserve">链接: {url}</w:t></w:r></w:p>'
                    )

        # 公告
        announcements = data.get("announcements", [])
        if announcements:
            body_parts.append(
                f'<w:p><w:pPr><w:pStyle w:val="Heading1"/></w:pPr>'
                f'<w:r><w:rPr><w:b/></w:rPr><w:t>公告 ({len(announcements)} 条)</w:t></w:r></w:p>'
            )
            for a in announcements[:30]:
                title = _row_esc(_attr(a, 'title', ''))
                date = str(_attr(a, 'publish_date', ''))[:10]
                ann_type = _row_esc(_attr(a, 'announcement_type', ''))
                url = _row_esc(_attr(a, 'url', ''))
                body_parts.append(
                    f'<w:p><w:r><w:rPr><w:b/></w:rPr>'
                    f'<w:t xml:space="preserve">{date} [{ann_type}]</w:t></w:r>'
                    f'<w:r><w:t xml:space="preserve"> {title}</w:t></w:r></w:p>'
                )
                if url:
                    body_parts.append(
                        f'<w:p><w:pPr><w:ind w:left="360"/></w:pPr>'
                        f'<w:r><w:rPr><w:color w:val="0563C1"/><w:u w:val="single"/></w:rPr>'
                        f'<w:t xml:space="preserve">链接: {url}</w:t></w:r></w:p>'
                    )

        body_xml = '\n'.join(body_parts)

        # ── 构建各文件 ────────────────────────────────────────────────────────
        ct_xml = (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
            '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
            '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
            '<Default Extension="xml" ContentType="application/xml"/>'
            '<Override PartName="/word/document.xml" '
            'ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
            '<Override PartName="/word/styles.xml" '
            'ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>'
            '</Types>'
        )

        rels_xml = (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" '
            'Target="word/document.xml"/>'
            '</Relationships>'
        )

        doc_rels_xml = (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" '
            'Target="styles.xml"/>'
            '</Relationships>'
        )

        styles_xml = (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
            '<w:styles xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
            '<w:docDefaults>'
            # v1.1 修复：完整字体定义（4 个属性齐全 + hint + lang）
            #  - ascii/hAnsi: 拉丁字符（用 universal 的 Times New Roman）
            #  - eastAsia:    东亚字符（用 universal 的 宋体 SimSun，几乎所有 Windows/Mac 都有）
            #  - cs:          复杂脚本（阿拉伯/泰文等）
            #  - hint:        告诉 Word 优先按 eastAsia 处理 CJK 字符
            #  - lang:        显式语言，让 Word 知道这段是中文
            '<w:rPrDefault><w:rPr>'
            '<w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman" '
            'w:eastAsia="宋体" w:cs="Times New Roman" w:hint="eastAsia"/>'
            '<w:sz w:val="24"/><w:szCs w:val="24"/>'
            '<w:lang w:val="en-US" w:eastAsia="zh-CN" w:bidi="ar-SA"/>'
            '</w:rPr></w:rPrDefault>'
            '<w:pPrDefault><w:pPr><w:spacing w:after="160" w:line="312" w:lineRule="auto"/></w:pPr></w:pPrDefault>'
            '</w:docDefaults>'
            '<w:style w:type="paragraph" w:styleId="Normal" w:default="1">'
            '<w:name w:val="Normal"/><w:qFormat/>'
            '<w:pPr><w:spacing w:after="160"/></w:pPr>'
            '</w:style>'
            '<w:style w:type="paragraph" w:styleId="Heading">'
            '<w:name w:val="heading"/><w:basedOn w:val="Normal"/><w:qFormat/>'
            '<w:pPr><w:spacing w:before="240" w:after="120"/><w:jc w:val="center"/></w:pPr>'
            '<w:rPr><w:b/><w:sz w:val="32"/></w:rPr>'
            '</w:style>'
            '<w:style w:type="paragraph" w:styleId="Heading1">'
            '<w:name w:val="Heading1"/><w:basedOn w:val="Normal"/><w:qFormat/>'
            '<w:pPr><w:spacing w:before="300" w:after="120"/></w:pPr>'
            '<w:rPr><w:b/><w:sz w:val="28"/></w:rPr>'
            '</w:style>'
            '<w:style w:type="table" w:styleId="TableGrid">'
            '<w:name w:val="Table Grid"/><w:tblPr>'
            '<w:tblBorders>'
            '<w:top w:val="single" w:sz="4" w:color="auto"/><w:left w:val="single" w:sz="4" w:color="auto"/>'
            '<w:bottom w:val="single" w:sz="4" w:color="auto"/><w:right w:val="single" w:sz="4" w:color="auto"/>'
            '<w:insideH w:val="single" w:sz="4" w:color="auto"/><w:insideV w:val="single" w:sz="4" w:color="auto"/>'
            '</w:tblBorders>'
            '</w:tblPr>'
            '</w:style>'
            '<w:style w:type="numbering" w:styleId="ListParagraph">'
            '<w:name w:val="List Paragraph"/><w:basedOn w:val="Normal"/><w:qFormat/>'
            '<w:pPr><w:ind w:left="720" w:hanging="360"/></w:pPr>'
            '</w:style>'
            '</w:styles>'
        )

        numbering_xml = (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
            '<w:numbering xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
            '<w:abstractNum w:abstractNumId="0">'
            '<w:lvl w:ilvl="0"><w:start w:val="1"/><w:numFmt w:val="bullet"/>'
            '<w:lvlText w:val="•"/><w:lvlJc w:val="left"/>'
            '<w:pPr><w:ind w:left="720" w:hanging="360"/></w:pPr>'
            '</w:lvl>'
            '</w:abstractNum>'
            '<w:num w:numId="1"><w:abstractNumId w:val="0"/></w:num>'
            '</w:numbering>'
        )

        doc_body = (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
            '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" '
            'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
            '<w:body>'
            f'{body_xml}'
            '<w:sectPr><w:pgSz w:w="12240" w:h="15840"/><w:pgMar w:top="1440" w:right="1800" '
            'w:bottom="1440" w:left="1800" w:header="720" w:footer="720" w:gutter="0"/>'
            '</w:sectPr>'
            '</w:body></w:document>'
        )

        numbering_rels = (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId1" '
            'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/numbering" '
            'Target="numbering.xml"/>'
            '</Relationships>'
        )

        # ── 写入 ZIP ─────────────────────────────────────────────────────────
        with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            zf.writestr('[Content_Types].xml', ct_xml)
            zf.writestr('_rels/.rels', rels_xml)
            zf.writestr('word/_rels/document.xml.rels', doc_rels_xml)
            zf.writestr('word/document.xml', doc_body)
            zf.writestr('word/styles.xml', styles_xml)
            zf.writestr('word/numbering.xml', numbering_xml)
            zf.writestr('word/_rels/numbering.xml.rels', numbering_rels)

        print(f"[标准库 Docx] 已生成: {output_path}")
        return output_path


# ─── PPTX 生成器 ────────────────────────────────────────────────────────────

class StdlibPptxWriter:
    """用标准库生成最小化 .pptx（PowerPoint 2007+ 兼容）"""

    def export_comprehensive_report(self, data: Dict[str, Any],
                                   stock_code: str,
                                   output_path: str = "") -> str:
        """
        生成 PowerPoint 文档（.pptx）

        结构：
          [Content_Types].xml
          _rels/.rels
          ppt/_rels/presentation.xml.rels
          ppt/presentation.xml
          ppt/slideLayouts/slideLayout1.xml  (title)
          ppt/slideLayouts/slideLayout2.xml  (title+body)
          ppt/slides/slide1.xml  (标题页)
          ppt/slides/slide2.xml  (概览)
          ppt/slides/slide3.xml  (定期报告)
          ppt/slides/slide4.xml  (券商研报)
          ppt/slides/slide5.xml  (公告)
          ppt/theme/theme1.xml
        """
        if not output_path:
            os.makedirs(EXPORT_DIR, exist_ok=True)
            output_path = str(EXPORT_DIR / f"{stock_code}_report.pptx")

        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        summary = data.get("summary", {})
        stock_name = summary.get("stock_name", stock_code)
        now = datetime.now().strftime('%Y-%m-%d %H:%M')

        slides: List[str] = []

        # ── Slide 1: 标题页 ────────────────────────────────────────────────
        slides.append(
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
            '<p:sld xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main" '
            'xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main">'
            '<p:cSld><p:spTree>'
            '<p:sp><p:nvSpPr><p:cNvPr id="1" name="Title"/><p:cNvSpPr txBox="1"/>'
            '<p:nvPr/></p:nvSpPr>'
            '<p:spPr><a:xfrm><a:off x="457200" y="2746380"/><a:ext cx="8229600" cy="1143000"/>'
            '</a:xfrm><a:prstGeom prst="rect"><a:avLst/></a:prstGeom>'
            '<a:noFill/></p:spPr>'
            '<p:txBody><a:bodyPr anchor="ctr"/><a:lstStyle/><a:p>'
            '<a:pPr algn="ctr"/><a:r><a:rPr lang="zh-CN" sz="4400" b="1">'
            '<a:solidFill><a:schemeClr val="tx1"/></a:solidFill>'
            '<a:latin typeface="宋体"/><a:ea typeface="宋体"/>'
            '</a:rPr><a:t>{}</a:t></a:r></a:p>'
            '<a:p><a:pPr algn="ctr"/><a:r><a:rPr lang="zh-CN" sz="2000">'
            '<a:solidFill><a:schemeClr val="tx1"/></a:solidFill>'
            '<a:latin typeface="宋体"/><a:ea typeface="宋体"/>'
            '</a:rPr><a:t>生成时间: {}</a:t></a:r></a:p>'
            '</p:txBody></p:sp></p:spTree></p:cSld>'
            '<p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr></p:sld>'.format(
                _esc(f"{stock_name} ({stock_code}) 综合报告"), _esc(now)
            )
        )

        # ── Slide 2: 概览 ─────────────────────────────────────────────────
        overview_lines = [
            f"定期报告: {summary.get('periodic_count', 0)} 份",
            f"券商研报: {summary.get('broker_count', 0)} 份",
            f"公告: {summary.get('announcement_count', 0)} 份",
            f"买入评级研报: {'是' if summary.get('has_buy_rating') else '否'}",
            f"最新定期报告: {summary.get('latest_periodic_date', 'N/A')}",
            f"最新券商研报: {summary.get('latest_broker_date', 'N/A')}",
            f"最新公告: {summary.get('latest_announcement_date', 'N/A')}",
        ]
        body_content = "\n".join(
            f'<a:t xml:space="preserve">{_esc(line)}</a:t>'
            for line in overview_lines
        )
        slides.append(
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
            '<p:sld xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main" '
            'xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main">'
            '<p:cSld><p:spTree>'
            '<p:sp><p:nvSpPr><p:cNvPr id="2" name="Title"/><p:cNvSpPr txBox="1"/><p:nvPr/></p:nvSpPr>'
            '<p:spPr><a:xfrm><a:off x="457200" y="274638"/><a:ext cx="8229600" cy="857250"/>'
            '</a:xfrm><a:prstGeom prst="rect"><a:avLst/></a:prstGeom><a:noFill/></p:spPr>'
            '<p:txBody><a:bodyPr/><a:lstStyle/><a:p><a:pPr algn="ctr"/>'
            '<a:r><a:rPr lang="zh-CN" sz="3200" b="1"><a:solidFill><a:schemeClr val="tx1"/></a:solidFill>'
            '<a:latin typeface="宋体"/><a:ea typeface="宋体"/>'
            '</a:rPr><a:t>报告概览</a:t></a:r></a:p></p:txBody></p:sp>'
            '<p:sp><p:nvSpPr><p:cNvPr id="3" name="Content"/><p:cNvSpPr txBox="1"/><p:nvPr/></p:nvSpPr>'
            '<p:spPr><a:xfrm><a:off x="457200" y="1371600"/><a:ext cx="8229600" cy="4114800"/>'
            '</a:xfrm><a:prstGeom prst="rect"><a:avLst/></a:prstGeom><a:noFill/></p:spPr>'
            '<p:txBody><a:bodyPr/><a:lstStyle/><a:p>'
            + body_content +
            '</a:p></p:txBody></p:sp></p:spTree></p:cSld>'
            '<p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr></p:sld>'
        )

        # ── Slide 3: 定期报告 ───────────────────────────────────────────────
        periodic = data.get("periodic_reports", [])
        if periodic:
            p_lines = [f"共 {len(periodic)} 份定期报告", ""]
            for p in periodic[:10]:
                p_url = str(_attr(p, 'url', ''))
                p_entry = f"• {str(_attr(p,'publish_date',''))[:10]} - {_esc(_attr(p,'title',''))[:50]}"
                if p_url:
                    p_entry += f"  [{p_url}]"  # v4.4.0: PPT 添加原文链接
                p_lines.append(p_entry)
            content = "\n".join(f'<a:t xml:space="preserve">{_esc(l)}</a:t>' for l in p_lines)
            slides.append(_make_content_slide("定期报告", content, 3))

        # ── Slide 4: 券商研报 ───────────────────────────────────────────────
        broker = data.get("broker_reports", [])
        if broker:
            r_stats = {"买入": 0, "增持": 0, "中性": 0, "减持": 0}
            for b in broker:
                r = _attr(b, 'rating', '')
                if r in r_stats:
                    r_stats[r] += 1
            b_lines = [
                f"共 {len(broker)} 份研报",
                f"评级分布: 买入{r_stats['买入']} 增持{r_stats['增持']} 中性{r_stats['中性']} 减持{r_stats['减持']}",
                ""
            ]
            for b in broker[:8]:
                b_url = str(_attr(b, 'url', ''))
                b_entry = f"• [{_attr(b,'rating','')}] {_esc(_attr(b,'broker_name',''))}: {_esc(_attr(b,'title',''))[:40]}"
                if b_url:
                    b_entry += f"  [{b_url}]"  # v4.4.0: PPT 添加原文链接
                b_lines.append(b_entry)
            content = "\n".join(f'<a:t xml:space="preserve">{_esc(l)}</a:t>' for l in b_lines)
            slides.append(_make_content_slide("券商研报", content, 4))

        # ── Slide 5: 公告 ───────────────────────────────────────────────────
        announcements = data.get("announcements", [])
        if announcements:
            a_lines = [f"共 {len(announcements)} 条公告", ""]
            for a in announcements[:10]:
                a_url = str(_attr(a, 'url', ''))
                a_entry = f"• {str(_attr(a,'publish_date',''))[:10]} - {_esc(_attr(a,'title',''))[:50]}"
                if a_url:
                    a_entry += f"  [{a_url}]"  # v4.4.0: PPT 添加原文链接
                a_lines.append(a_entry)
            content = "\n".join(f'<a:t xml:space="preserve">{_esc(l)}</a:t>' for l in a_lines)
            slides.append(_make_content_slide("公告", content, 5))

        # ── 构建 PPTX ───────────────────────────────────────────────────────
        slide_xmls = "\n".join(slides)
        slide_ids = "".join(
            f'<p:sldId id="256{i + 1}" r:id="rId{i + 1}"/>'
            for i in range(len(slides))
        )
        slide_rels = "".join(
            f'<p:cSld id="256{i + 1}" r:id="rId{i + 1}"/>'
            for i in range(len(slides))
        )

        ct_xml = (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
            '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
            '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
            '<Default Extension="xml" ContentType="application/xml"/>'
            '<Override PartName="/ppt/presentation.xml" '
            'ContentType="application/vnd.openxmlformats-officedocument.presentationml.presentation.main+xml"/>'
            '<Override PartName="/ppt/slideMasters/slideMaster1.xml" '
            'ContentType="application/vnd.openxmlformats-officedocument.presentationml.slideMaster+xml"/>'
            '<Override PartName="/ppt/slideLayouts/slideLayout1.xml" '
            'ContentType="application/vnd.openxmlformats-officedocument.presentationml.slideLayout+xml"/>'
            '<Override PartName="/ppt/slideLayouts/slideLayout2.xml" '
            'ContentType="application/vnd.openxmlformats-officedocument.presentationml.slideLayout+xml"/>'
            '<Override PartName="/ppt/theme/theme1.xml" '
            'ContentType="application/vnd.openxmlformats-officedocument.theme+xml"/>'
        )
        for i in range(len(slides)):
            ct_xml += (
                f'<Override PartName="/ppt/slides/slide{i+1}.xml" '
                'ContentType="application/vnd.openxmlformats-officedocument.presentationml.slide+xml"/>'
            )
        ct_xml += '</Types>'

        pres_rels = (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId0" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideMaster" '
            'Target="slideMasters/slideMaster1.xml"/>'
            + "".join(
                f'<Relationship Id="rId{i+1}" '
                'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide" '
                f'Target="slides/slide{i+1}.xml"/>'
                for i in range(len(slides))
            ) +
            '<Relationship Id="rId100" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/theme" '
            'Target="theme/theme1.xml"/>'
            '</Relationships>'
        )

        pres_xml = (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
            '<p:presentation xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main" '
            'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" '
            'saveSubsetFonts="1">'
            '<p:sldMasterIdLst><p:sldMasterId id="2147483648" r:id="rId0"/></p:sldMasterIdLst>'
            '<p:sldIdLst>' + slide_ids + '</p:sldIdLst>'
            '<p:sldSz cx="9144000" cy="6858000" type="screen4x3"/>'
            '<p:notesSz cx="6858000" cy="9144000"/>'
            '</p:presentation>'
        )

        master_xml = (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
            '<p:sldMaster xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main" '
            'xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" '
            'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
            '<p:cSld><p:spTree><p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/>'
            '<p:nvPr/></p:nvGrpSpPr><p:grpSpPr>'
            '<a:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/><a:prstGeom prst="rect"><a:avLst/></a:prstGeom>'
            '</a:xfrm></p:grpSpPr></p:spTree></p:cSld>'
            '<p:clrMap bg1="lt1" tx1="dk1" bg2="lt2" tx2="dk2" accent1="accent1" accent2="accent2" '
            'accent3="accent3" accent4="accent4" accent5="accent5" accent6="accent6" hlink="hlink" folHlink="folHlink"/>'
            '</p:sldMaster>'
        )

        layout_xml = (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
            '<p:sldLayout xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main" '
            'xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" '
            'type="titleOnly" preserve="1">'
            '<p:cSld name="Title Only"><p:spTree><p:nvGrpSpPr><p:cNvPr id="1" name=""/>'
            '<p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr><p:grpSpPr>'
            '<a:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/>'
            '<a:prstGeom prst="rect"><a:avLst/></a:prstGeom></a:xfrm>'
            '</p:grpSpPr></p:spTree></p:cSld>'
            '<p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr></p:sldLayout>'
        )

        theme_xml = (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
            '<a:theme xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" '
            'name="Office Theme"><a:themeElements>'
            '<a:clrScheme name="Office">'
            '<a:dk1><a:sysClr val="windowText" lastClr="000000"/></a:dk1>'
            '<a:lt1><a:sysClr val="window" lastClr="FFFFFF"/></a:lt1>'
            '<a:dk2><a:srgbClr val="1F497D"/></a:dk2>'
            '<a:lt2><a:srgbClr val="EEECE1"/></a:lt2>'
            '<a:accent1><a:srgbClr val="4F81BD"/></a:accent1>'
            '<a:accent2><a:srgbClr val="C0504D"/></a:accent2>'
            '<a:accent3><a:srgbClr val="9BBB59"/></a:accent3>'
            '<a:accent4><a:srgbClr val="8064A2"/></a:accent4>'
            '<a:accent5><a:srgbClr val="4BACC6"/></a:accent5>'
            '<a:accent6><a:srgbClr val="F79646"/></a:accent6>'
            '<a:hlink><a:srgbClr val="0000FF"/></a:hlink>'
            '<a:folHlink><a:srgbClr val="800080"/></a:folHlink>'
            '</a:clrScheme>'
            # v1.1 修复：CJK 字体从空改为"宋体"（universal），避免 Mac/Linux/旧 Windows 下载后乱码
            '<a:fontScheme name="Office">'
            '<a:majorFont><a:latin typeface="Calibri"/><a:ea typeface="宋体"/><a:cs typeface="Calibri"/>'
            '</a:majorFont>'
            '<a:minorFont><a:latin typeface="Calibri"/><a:ea typeface="宋体"/><a:cs typeface="Calibri"/>'
            '</a:minorFont></a:fontScheme>'
            '<a:fmtScheme name="Office"><a:fillStyleLst><a:solidFill/><a:gradFill rotWithShape="1">'
            '<a:gsLst><a:gs pos="0"/><a:gs pos="1"/></a:gsLst>'
            '<a:lin><a:gradFill rotWithShape="1"/></a:lin></a:gradFill></a:fillStyleLst>'
            '<a:lnStyleLst><a:ln w="9525"><a:solidFill><a:schemeClr val="accent1"/></a:solidFill>'
            '<a:ln w="25400"><a:solidFill><a:schemeClr val="accent1"/></a:solidFill></a:ln>'
            '<a:ln w="38100"><a:solidFill><a:schemeClr val="accent1"/></a:solidFill></a:ln>'
            '</a:lnStyleLst><a:effectStyleLst><a:effectStyle><a:effectLst/></a:effectStyle>'
            '<a:effectStyle><a:effectLst/></a:effectStyle><a:effectStyle><a:effectLst/></a:effectStyle>'
            '</a:effectStyleLst><a:bgFillStyleLst><a:solidFill/><a:gradFill rotWithShape="1">'
            '<a:gsLst><a:gs pos="0"/><a:gs pos="1"/></a:gsLst>'
            '<a:lin rotWithShape="1"/></a:gradFill></a:bgFillStyleLst>'
            '</a:fmtScheme>'
            '</a:themeElements><a:objectDefaults/><a:extraClrSchemeLst/></a:theme>'
        )

        with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            zf.writestr('[Content_Types].xml', ct_xml)
            zf.writestr('_rels/.rels', (
                '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
                '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" '
                'Target="ppt/presentation.xml"/>'
                '</Relationships>'
            ))
            zf.writestr('ppt/_rels/presentation.xml.rels', pres_rels)
            zf.writestr('ppt/presentation.xml', pres_xml)
            zf.writestr('ppt/slideMasters/slideMaster1.xml', master_xml)
            zf.writestr('ppt/slideLayouts/slideLayout1.xml', layout_xml)
            zf.writestr('ppt/slideLayouts/slideLayout2.xml', layout_xml)
            zf.writestr('ppt/theme/theme1.xml', theme_xml)
            for i, slide_xml in enumerate(slides):
                zf.writestr(f'ppt/slides/slide{i+1}.xml', slide_xml)
            zf.writestr('ppt/_rels/slideLayout1.xml.rels', (
                '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
                '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                '<Relationship Id="rId1" '
                'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideMaster" '
                'Target="../slideMasters/slideMaster1.xml"/>'
                '</Relationships>'
            ))
            zf.writestr('ppt/_rels/slideLayout2.xml.rels', (
                '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
                '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                '<Relationship Id="rId1" '
                'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideMaster" '
                'Target="../slideMasters/slideMaster1.xml"/>'
                '</Relationships>'
            ))

        print(f"[标准库 Pptx] 已生成: {output_path}")
        return output_path


def _make_content_slide(title: str, content_xml: str, slide_id: int) -> str:
    """生成内容页幻灯片 XML"""
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
        '<p:sld xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main" '
        'xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main">'
        '<p:cSld><p:spTree>'
        '<p:sp><p:nvSpPr><p:cNvPr id="2" name="Title"/><p:cNvSpPr txBox="1"/><p:nvPr/></p:nvSpPr>'
        '<p:spPr><a:xfrm><a:off x="457200" y="274638"/><a:ext cx="8229600" cy="857250"/>'
        '</a:xfrm><a:prstGeom prst="rect"><a:avLst/></a:prstGeom><a:noFill/></p:spPr>'
        '<p:txBody><a:bodyPr/><a:lstStyle/><a:p><a:pPr algn="ctr"/>'
        '<a:r><a:rPr lang="zh-CN" sz="3200" b="1"><a:solidFill><a:schemeClr val="tx1"/></a:solidFill>'
        '<a:latin typeface="宋体"/><a:ea typeface="宋体"/>'
        '</a:rPr><a:t>{}</a:t></a:r></a:p></p:txBody></p:sp>'
        '<p:sp><p:nvSpPr><p:cNvPr id="3" name="Content"/><p:cNvSpPr txBox="1"/><p:nvPr/></p:nvSpPr>'
        '<p:spPr><a:xfrm><a:off x="457200" y="1371600"/><a:ext cx="8229600" cy="4800600"/>'
        '</a:xfrm><a:prstGeom prst="rect"><a:avLst/></a:prstGeom><a:noFill/></p:spPr>'
        '<p:txBody><a:bodyPr/><a:lstStyle/><a:p>'
        + content_xml +
        '</a:p></p:txBody></p:sp>'
        '</p:spTree></p:cSld>'
        '<p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr></p:sld>'.format(_esc(title))
    )


# ─── XLSX 生成器 ────────────────────────────────────────────────────────────

class StdlibXlsxWriter:
    """用标准库生成最小化 .xlsx（Excel 2007+ 兼容）"""

    def export_comprehensive_report(self, data: Dict[str, Any],
                                   stock_code: str,
                                   output_path: str = "") -> str:
        """
        生成 Excel 文档（.xlsx）

        结构：
          [Content_Types].xml
          _rels/.rels
          xl/workbook.xml
          xl/_rels/workbook.xml.rels
          xl/worksheets/sheet1.xml  (概览)
          xl/worksheets/sheet2.xml  (定期报告)
          xl/worksheets/sheet3.xml  (券商研报)
          xl/worksheets/sheet4.xml  (公告)
          xl/sharedStrings.xml
          xl/styles.xml
        """
        if not output_path:
            os.makedirs(EXPORT_DIR, exist_ok=True)
            output_path = str(EXPORT_DIR / f"{stock_code}_report.xlsx")

        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        summary = data.get("summary", {})
        stock_name = summary.get("stock_name", stock_code)
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        sheets: List[Dict] = []

        # ── Sheet 1: 报告概览 ───────────────────────────────────────────────
        s1_rows = [
            ["项目", "内容"],
            ["股票代码", stock_code],
            ["股票名称", stock_name],
            ["定期报告", f"{summary.get('periodic_count', 0)} 份"],
            ["券商研报", f"{summary.get('broker_count', 0)} 份"],
            ["公告", f"{summary.get('announcement_count', 0)} 份"],
            ["买入评级研报", "是" if summary.get('has_buy_rating') else "否"],
            ["最新定期报告", str(summary.get('latest_periodic_date', 'N/A'))],
            ["最新券商研报", str(summary.get('latest_broker_date', 'N/A'))],
            ["最新公告", str(summary.get('latest_announcement_date', 'N/A'))],
            ["生成时间", now],
        ]
        sheets.append(("报告概览", s1_rows))

        # ── Sheet 2: 定期报告 ───────────────────────────────────────────────
        periodic = data.get("periodic_reports", [])
        s2_rows = [["日期", "标题", "报告类型", "URL"]]
        for p in periodic:
            s2_rows.append([
                str(_attr(p, 'publish_date', ''))[:10],
                _row_esc(_attr(p, 'title', '')),
                _row_esc(_attr(p, 'report_type', '')),
                _row_esc(_attr(p, 'url', '')),
            ])
        sheets.append(("定期报告", s2_rows if len(s2_rows) > 1 else [["无数据"]]))

        # ── Sheet 3: 券商研报 ───────────────────────────────────────────────
        broker = data.get("broker_reports", [])
        s3_rows = [["日期", "标题", "券商", "分析师", "评级", "目标价", "目标涨幅", "URL"]]
        for b in broker:
            s3_rows.append([
                str(_attr(b, 'publish_date', ''))[:10],
                _row_esc(_attr(b, 'title', '')),
                _row_esc(_attr(b, 'broker_name', '')),
                _row_esc(_attr(b, 'analyst', '')),
                _row_esc(_attr(b, 'rating', '')),
                f"{float(_attr(b, 'target_price', 0)):.2f}" if _attr(b, 'target_price', 0) else "",
                f"{float(_attr(b, 'target_change_pct', 0)):.2f}%" if _attr(b, 'target_change_pct', 0) else "",
                _row_esc(_attr(b, 'url', '')),
            ])
        sheets.append(("券商研报", s3_rows if len(s3_rows) > 1 else [["无数据"]]))

        # ── Sheet 4: 公告 ───────────────────────────────────────────────────
        announcements = data.get("announcements", [])
        s4_rows = [["日期", "标题", "公告类型", "URL"]]
        for a in announcements:
            s4_rows.append([
                str(_attr(a, 'publish_date', ''))[:10],
                _row_esc(_attr(a, 'title', '')),
                _row_esc(_attr(a, 'announcement_type', '')),
                _row_esc(_attr(a, 'url', '')),
            ])
        sheets.append(("公告", s4_rows if len(s4_rows) > 1 else [["无数据"]]))

        # ── 构建共享字符串 ─────────────────────────────────────────────────
        all_strings: List[str] = []
        str_map: Dict[str, int] = {}

        def _si(s: str) -> str:
            nonlocal all_strings, str_map
            s = str(s)
            if s not in str_map:
                str_map[s] = len(all_strings)
                all_strings.append(s)
            return str(str_map[s])

        def _cell_row(vals: List[Any], row_idx: int, style: int = 0) -> str:
            cells = ""
            for col_idx, v in enumerate(vals):
                c = chr(65 + col_idx)  # A, B, C...
                sv = _si(v) if isinstance(v, str) else str(v)
                if isinstance(v, str):
                    cells += f'<c r="{c}{row_idx}" t="s"><v>{sv}</v></c>'
                else:
                    cells += f'<c r="{c}{row_idx}"><v>{sv}</v></c>'
            return f'<row r="{row_idx}">{cells}</row>'

        sheet_xmls: List[str] = []
        for sheet_idx, (sheet_name, rows) in enumerate(sheets):
            sheet_data = ""
            for ri, row in enumerate(rows, 1):
                sheet_data += _cell_row(row, ri, 1 if ri == 1 else 0)
            sheet_xmls.append(
                '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
                '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
                '<sheetData>' + sheet_data + '</sheetData></worksheet>'
            )

        shared_strings_xml = (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
            '<sst xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
            f'count="{len(all_strings)}" uniqueCount="{len(all_strings)}">'
            + "".join(f'<si><t>{_esc(s)}</t></si>' for s in all_strings)
            + '</sst>'
        )

        styles_xml = (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
            '<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
            '<fonts><font><sz val="11"/><name val="宋体"/></font>'
            '<font><sz val="11"/><b/><name val="宋体"/></font></fonts>'
            '<fills><fill><patternFill patternType="none"/></fill>'
            '<fill><patternFill patternType="gray125"/></fill>'
            '<fill><patternFill patternType="solid"><fgColor rgb="FFD9E1F2"/></patternFill></fill></fills>'
            '<borders><border><left/><right/><top/><bottom/><diagonal/></border>'
            '<border><left val="thin"><color rgb="FF000000"/></left>'
            '<right val="thin"><color rgb="FF000000"/></right>'
            '<top val="thin"><color rgb="FF000000"/></top>'
            '<bottom val="thin"><color rgb="FF000000"/></bottom><diagonal/></border>'
            '</borders>'
            '<cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs>'
            '<cellXfs>'
            '<xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"/>'
            '<xf numFmtId="0" fontId="1" fillId="2" borderId="1" xfId="0" applyFont="1" applyFill="1" applyBorder="1"/>'
            '</cellXfs></styleSheet>'
        )

        sheet_rels = "".join(
            f'<Relationship Id="rId{i+1}" '
            'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" '
            f'Target="worksheets/sheet{i+1}.xml"/>'
            for i in range(len(sheets))
        ) + '<Relationship Id="rId99" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/sharedStrings" Target="sharedStrings.xml"/>'

        workbook_xml = (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
            '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
            'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
            '<sheets>'
            + "".join(
                f'<sheet name="{_esc(name)}" sheetId="{i+1}" r:id="rId{i+1}"/>'
                for i, (name, _) in enumerate(sheets)
            )
            + '</sheets></workbook>'
        )

        ct_xml = (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
            '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
            '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
            '<Default Extension="xml" ContentType="application/xml"/>'
            '<Override PartName="/xl/workbook.xml" '
            'ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
            '<Override PartName="/xl/sharedStrings.xml" '
            'ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sharedStrings+xml"/>'
            '<Override PartName="/xl/styles.xml" '
            'ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>'
            + "".join(
                f'<Override PartName="/xl/worksheets/sheet{i+1}.xml" '
                'ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
                for i in range(len(sheets))
            )
            + '</Types>'
        )

        # ── 写入 ZIP ─────────────────────────────────────────────────────────
        with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            zf.writestr('[Content_Types].xml', ct_xml)
            zf.writestr('_rels/.rels', (
                '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
                '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                '<Relationship Id="rId1" '
                'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" '
                'Target="xl/workbook.xml"/>'
                '</Relationships>'
            ))
            zf.writestr('xl/_rels/workbook.xml.rels', (
                '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
                '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                + sheet_rels +
                '</Relationships>'
            ))
            zf.writestr('xl/workbook.xml', workbook_xml)
            zf.writestr('xl/styles.xml', styles_xml)
            zf.writestr('xl/sharedStrings.xml', shared_strings_xml)
            for i, sheet_xml in enumerate(sheet_xmls):
                zf.writestr(f'xl/worksheets/sheet{i+1}.xml', sheet_xml)

        print(f"[标准库 Xlsx] 已生成: {output_path}")
        return output_path
