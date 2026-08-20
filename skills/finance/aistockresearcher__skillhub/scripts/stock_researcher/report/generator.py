#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PDF报告生成器
PDF Report Generator
"""

import os
import json
import time
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime, date

# PDF生成
try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image
    from reportlab.lib import colors
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    PDF_AVAILABLE = True
except ImportError:
    try:
        from fpdf import FPDF
        PDF_AVAILABLE = True
    except ImportError:
        PDF_AVAILABLE = False

# ── v4.4 中文字体配置 ──
def _detect_chinese_ttf() -> str:
    import platform, os
    candidates = []
    if platform.system() == "Windows":
        windir = os.environ.get("WINDIR", "C:\\Windows")
        candidates = [
            os.path.join(windir, "Fonts", "simhei.ttf"),
            os.path.join(windir, "Fonts", "SIMHEI.TTF"),
            os.path.join(windir, "Fonts", "simsun.ttc"),
            os.path.join(windir, "Fonts", "msyh.ttf"),
        ]
    else:
        candidates = [
            "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
            "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
            "/System/Library/Fonts/PingFang.ttc",
        ]
    for p in candidates:
        if os.path.isfile(p):
            return p
    return ""

_CHINESE_TTF = _detect_chinese_ttf()
_REGISTERED_CN_FONT = "ChineseFont"
_HAS_CN_FONT = False

if _CHINESE_TTF and PDF_AVAILABLE:
    try:
        pdfmetrics.registerFont(TTFont(_REGISTERED_CN_FONT, _CHINESE_TTF))
        _HAS_CN_FONT = True
    except Exception:
        pass

def _cn_font() -> str:
    return _REGISTERED_CN_FONT if _HAS_CN_FONT else "Helvetica"


class ReportGenerator:
    """
    PDF报告生成器

    支持三种报告类型：
    - 短期报告（1-5日）：技术面为主、资金面、新闻舆情
    - 中期报告（20-60日）：估值分析、均线趋势、机构持仓
    - 长期报告（120+日）：基本面、行业发展、DCF内在价值
    """

    def __init__(self, output_dir: str = None):
        self.output_dir = output_dir or Path(__file__).resolve().parents[2] / "data"
        self.output_dir = Path(self.output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.elements = []
        self.styles = None
        self._cn = "Helvetica"

        if PDF_AVAILABLE:
            try:
                self.styles = getSampleStyleSheet()
                cn = _cn_font()
                if _HAS_CN_FONT:
                    self._cn = cn
                    # 添加中文字体段落样式
                    self.styles.add(ParagraphStyle('CnNormal', parent=self.styles['Normal'],
                                                   fontName=cn, fontSize=10, leading=16))
                    self.styles.add(ParagraphStyle('CnTitle', parent=self.styles['Title'],
                                                   fontName=cn, fontSize=24, spaceAfter=20))
                    self.styles.add(ParagraphStyle('CnHeading1', parent=self.styles['Heading1'],
                                                   fontName=cn, fontSize=16, spaceAfter=10))
                    self.styles.add(ParagraphStyle('CnHeading2', parent=self.styles['Heading2'],
                                                   fontName=cn, fontSize=14, spaceAfter=8))
            except Exception:
                pass

    def add_title(self, title: str):
        """添加标题"""
        if PDF_AVAILABLE and self.styles:
            style = self.styles.get('CnTitle') if _HAS_CN_FONT else self.styles.get('Title')
            self.elements.append(Paragraph(title, style))
            self.elements.append(Spacer(1, 10*mm))
        else:
            self.elements.append(f"\n{'='*60}\n{title}\n{'='*60}\n")

    def add_section(self, title: str):
        """添加章节"""
        if PDF_AVAILABLE and self.styles:
            style = self.styles.get('CnHeading1') if _HAS_CN_FONT else self.styles.get('Heading1')
            self.elements.append(Paragraph(title, style))
            self.elements.append(Spacer(1, 5*mm))
        else:
            self.elements.append(f"\n{'-'*50}\n{title}\n{'-'*50}\n")

    def add_subsection(self, title: str):
        """添加子章节"""
        if PDF_AVAILABLE and self.styles:
            style = self.styles.get('CnHeading2') if _HAS_CN_FONT else self.styles.get('Heading2')
            self.elements.append(Paragraph(title, style))
        else:
            self.elements.append(f"\n{title}\n")

    def add_text(self, text: str):
        """添加文本"""
        if PDF_AVAILABLE and self.styles:
            style = self.styles.get('CnNormal') if _HAS_CN_FONT else self.styles.get('Normal')
            self.elements.append(Paragraph(text, style))
        else:
            self.elements.append(f"{text}\n")

    def add_table(self, data: List[List], col_widths=None):
        """添加表格"""
        cn = _cn_font()
        if PDF_AVAILABLE:
            table = Table(data, colWidths=col_widths)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, -1), cn),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('FONTSIZE', (0, 1), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ]))
            self.elements.append(table)
            self.elements.append(Spacer(1, 5*mm))
        else:
            for row in data:
                self.elements.append(" | ".join(str(c) for c in row) + "\n")

    def add_page_break(self):
        """添加分页"""
        self.elements.append(PageBreak())

    def build(self, output_path: str):
        """生成PDF文件"""
        if PDF_AVAILABLE:
            doc = SimpleDocTemplate(output_path, pagesize=A4)
            doc.build(self.elements)
        else:
            # 降级为文本文件
            txt_path = output_path.replace(".pdf", ".txt")
            with open(txt_path, "w", encoding="utf-8") as f:
                content = []
                for e in self.elements:
                    if hasattr(e, 'text'):
                        content.append(e.text)
                    elif isinstance(e, str):
                        content.append(e)
                f.write("\n".join(content))
            output_path = txt_path
        print(f"[生成] 报告已保存: {output_path}")
        return output_path

    def generate_short_report(self, stock_data: Dict, tech_data: Dict, money_data: Dict,
                              sentiment_data: Dict, prediction: Dict) -> str:
        """
        生成短期报告

        Args:
            stock_data: 股票行情数据
            tech_data: 技术分析数据
            money_data: 资金流向数据
            sentiment_data: 情绪数据
            prediction: 预测数据

        Returns:
            str: PDF文件路径
        """
        self.elements = []
        today = date.today().strftime("%Y-%m-%d")

        # 标题
        code = stock_data.get("code", "")
        name = stock_data.get("name", code)
        self.add_title(f"【短期投资价值报告】{name}({code}) {today}")

        # 行情概览
        self.add_section("一、行情概览")
        price = stock_data.get("price", 0)
        change_pct = stock_data.get("change_pct", 0)
        table_data = [
            ["指标", "数值"],
            ["股票代码", code],
            ["股票名称", name],
            ["当前价格", f"{price:.2f}"],
            ["涨跌幅", f"{change_pct:+.2f}%"],
            ["换手率", f"{money_data.get('turnover', 0):.2f}%"],
            ["主力净流入", f"{money_data.get('main_net_flow', 0):.0f}万"],
        ]
        self.add_table(table_data)

        # 技术分析
        self.add_section("二、技术分析")
        ma_status = tech_data.get("ma_arrangement", "未知")
        rsi = tech_data.get("rsi14", 50)
        macd_signal = "金叉" if tech_data.get("macd_hist", 0) > 0 else "死叉"

        table_data = [
            ["指标", "数值", "信号"],
            ["均线状态", ma_status, tech_data.get("tech_signal", "")],
            ["RSI(14)", f"{rsi:.1f}", "超买" if rsi > 70 else ("超卖" if rsi < 30 else "正常")],
            ["MACD", macd_signal, f"柱状图: {tech_data.get('macd_hist', 0):.4f}"],
            ["技术评分", f"{tech_data.get('tech_score', 0):.0f}", tech_data.get("tech_signal", "")],
        ]
        self.add_table(table_data)

        # 资金流向
        self.add_section("三、资金流向")
        flow_direction = money_data.get("direction", "中性")
        flow_ratio = money_data.get("flow_ratio", 0)
        table_data = [
            ["指标", "数值"],
            ["主力净流入", f"{money_data.get('main_net_flow', 0):.0f}万"],
            ["净流入占比", f"{flow_ratio:.4f}%"],
            ["资金方向", flow_direction],
            ["资金评分", f"{money_data.get('score', 0)}"],
        ]
        self.add_table(table_data)

        # 情绪分析
        self.add_section("四、新闻舆情")
        sentiment_label = sentiment_data.get("sentiment_label", "中性")
        table_data = [
            ["指标", "数值"],
            ["舆情判断", sentiment_label],
            ["情绪评分", f"{sentiment_data.get('sentiment_score', 0):.0f}"],
            ["正面新闻", f"{sentiment_data.get('news_positive', 0)}条"],
            ["负面新闻", f"{sentiment_data.get('news_negative', 0)}条"],
        ]
        self.add_table(table_data)

        # 短期预测
        self.add_section("五、短期预测")
        short = prediction.get("short_term", {})
        table_data = [
            ["指标", "数值"],
            ["预测信号", short.get("signal", "中性")],
            ["预测涨跌幅", f"{short.get('predicted_return', 0):+.2f}%"],
            ["上涨概率", f"{short.get('prob_up', 50):.1f}%"],
            ["置信度", f"{short.get('confidence', 0.5):.0%}"],
            ["关键因素", ", ".join(short.get('key_factors', [])[:3])],
            ["操作建议", short.get('suggestion', '')],
        ]
        self.add_table(table_data)

        # 风险提示
        self.add_section("六、风险提示")
        self.add_text("1. 本报告仅供参考，不构成投资建议")
        self.add_text("2. 短期波动较大，投资需谨慎")
        self.add_text("3. 市场有风险，请控制仓位")

        # 生成PDF
        output_path = self.output_dir / f"short_report_{today}_{code}.pdf"
        return self.build(str(output_path))

    def generate_medium_report(self, stock_data: Dict, tech_data: Dict, val_data: Dict,
                               fundamental_data: Dict, prediction: Dict) -> str:
        """
        生成中期报告

        Args:
            stock_data: 股票行情数据
            tech_data: 技术分析数据
            val_data: 估值数据
            fundamental_data: 基本面数据
            prediction: 预测数据

        Returns:
            str: PDF文件路径
        """
        self.elements = []
        today = date.today().strftime("%Y-%m-%d")

        code = stock_data.get("code", "")
        name = stock_data.get("name", code)
        self.add_title(f"【中期投资价值报告】{name}({code}) {today}")

        # 行情概览
        self.add_section("一、行情概览")
        table_data = [
            ["指标", "数值"],
            ["股票代码", code],
            ["股票名称", name],
            ["当前价格", f"{stock_data.get('price', 0):.2f}"],
            ["涨跌幅", f"{stock_data.get('change_pct', 0):+.2f}%"],
            ["MA20", f"{tech_data.get('ma20', 0):.2f}"],
            ["MA60", f"{tech_data.get('ma60', 0):.2f}"],
        ]
        self.add_table(table_data)

        # 均线趋势
        self.add_section("二、均线趋势分析")
        ma_arrangement = tech_data.get("ma_arrangement", "混乱")
        ma_status = "多头排列" if ma_arrangement == "多头排列" else "空头排列" if ma_arrangement == "空头排列" else "震荡整理"
        table_data = [
            ["指标", "数值"],
            ["MA5", f"{tech_data.get('ma5', 0):.2f}"],
            ["MA10", f"{tech_data.get('ma10', 0):.2f}"],
            ["MA20", f"{tech_data.get('ma20', 0):.2f}"],
            ["MA60", f"{tech_data.get('ma60', 0):.2f}"],
            ["均线状态", ma_status],
        ]
        self.add_table(table_data)

        # 估值分析
        self.add_section("三、估值分析")
        pe = val_data.get("pe", 0)
        pb = val_data.get("pb", 0)
        pe_pct = val_data.get("pe_percentile", 50)
        pb_pct = val_data.get("pb_percentile", 50)
        table_data = [
            ["指标", "数值", "历史分位"],
            ["市盈率(PE)", f"{pe:.2f}", f"{pe_pct:.0f}%"],
            ["市净率(PB)", f"{pb:.2f}", f"{pb_pct:.0f}%"],
            ["估值信号", val_data.get("val_signal", "中性"), ""],
            ["估值状态", val_data.get("valuation_state", "正常"), ""],
        ]
        self.add_table(table_data)

        # 基本面
        self.add_section("四、基本面分析")
        roe = fundamental_data.get("roe", 0)
        table_data = [
            ["指标", "数值"],
            ["净资产收益率(ROE)", f"{roe:.2f}%"],
            ["每股收益(EPS)", f"{fundamental_data.get('eps', 0):.2f}"],
            ["每股净资产(BVPS)", f"{fundamental_data.get('bvps', 0):.2f}"],
            ["Graham Number", f"{val_data.get('graham_number', 0):.2f}"],
        ]
        self.add_table(table_data)

        # 中期预测
        self.add_section("五、中期预测")
        medium = prediction.get("medium_term", {})
        table_data = [
            ["指标", "数值"],
            ["预测信号", medium.get("signal", "中性")],
            ["预测涨跌幅", f"{medium.get('predicted_return', 0):+.2f}%"],
            ["10%分位数", f"{medium.get('p10', 0):+.2f}%"],
            ["50%分位数", f"{medium.get('p50', 0):+.2f}%"],
            ["90%分位数", f"{medium.get('p90', 0):+.2f}%"],
            ["操作建议", medium.get('suggestion', '')],
        ]
        self.add_table(table_data)

        # 风险提示
        self.add_section("六、风险提示")
        self.add_text("1. 本报告仅供参考，不构成投资建议")
        self.add_text("2. 中期趋势可能反复，注意仓位管理")
        self.add_text("3. 请关注宏观经济变化")

        output_path = self.output_dir / f"medium_report_{today}_{code}.pdf"
        return self.build(str(output_path))

    def generate_long_report(self, stock_data: Dict, fundamental_data: Dict,
                             buffett_analysis: Dict, graham_analysis: Dict,
                             lynch_analysis: Dict, prediction: Dict,
                             value_investing: Dict = None) -> str:
        """
        生成长期报告（v5.0: 新增价值投资决策整合章节）

        Args:
            stock_data: 股票行情数据
            fundamental_data: 基本面数据
            buffett_analysis: 巴菲特分析
            graham_analysis: 格雷厄姆分析
            lynch_analysis: 林奇分析
            prediction: 预测数据
            value_investing: v5.0 价值投资决策整合结果

        Returns:
            str: PDF文件路径
        """
        self.elements = []
        today = date.today().strftime("%Y-%m-%d")

        code = stock_data.get("code", "")
        name = stock_data.get("name", code)
        self.add_title(f"【长期投资价值报告】{name}({code}) {today}")

        # 行情概览
        self.add_section("一、基本信息")
        table_data = [
            ["指标", "数值"],
            ["股票代码", code],
            ["股票名称", name],
            ["当前价格", f"{stock_data.get('price', 0):.2f}"],
        ]
        self.add_table(table_data)

        # 巴菲特分析
        self.add_section("二、巴菲特价值分析")
        table_data = [
            ["指标", "数值"],
            ["ROE", f"{buffett_analysis.get('roe', 0):.2f}%"],
            ["营业利润率", f"{buffett_analysis.get('operating_margin', 0):.2f}%"],
            ["护城河评分", f"{buffett_analysis.get('moat_score', 0):.0f}"],
            ["内在价值", f"{buffett_analysis.get('intrinsic_value', 0):.2f}"],
            ["安全边际", f"{buffett_analysis.get('margin_of_safety', 0):.1f}%"],
            ["综合评分", f"{buffett_analysis.get('buffett_score', 0):.0f}"],
            ["信号", buffett_analysis.get('signal', '中性')],
        ]
        self.add_table(table_data)

        # 格雷厄姆分析
        self.add_section("三、格雷厄姆分析")
        table_data = [
            ["指标", "数值"],
            ["Graham Number", f"{graham_analysis.get('graham_number', 0):.2f}"],
            ["NCAV", f"{graham_analysis.get('ncav', 0):.2f}"],
            ["流动比率", f"{graham_analysis.get('current_ratio', 0):.2f}"],
            ["资产负债率", f"{graham_analysis.get('debt_ratio', 0):.1f}%"],
            ["安全边际", f"{graham_analysis.get('margin_of_safety', 0):.1f}%"],
            ["综合评分", f"{graham_analysis.get('graham_score', 0):.0f}"],
        ]
        self.add_table(table_data)

        # 林奇分析
        self.add_section("四、彼得林奇成长分析")
        table_data = [
            ["指标", "数值"],
            ["营收增长率", f"{lynch_analysis.get('revenue_growth', 0):.1f}%"],
            ["EPS增长率", f"{lynch_analysis.get('eps_growth', 0):.1f}%"],
            ["CAGR", f"{lynch_analysis.get('cagr', 0):.1f}%"],
            ["PEG", f"{lynch_analysis.get('peg', 0):.2f}"],
            ["负债率", f"{lynch_analysis.get('debt_ratio', 0):.1f}%"],
            ["综合评分", f"{lynch_analysis.get('lynch_score', 0):.0f}"],
        ]
        self.add_table(table_data)

        # 长期预测
        self.add_section("五、长期预测")
        long_term = prediction.get("long_term", {})
        table_data = [
            ["指标", "数值"],
            ["预测信号", long_term.get("signal", "中性")],
            ["预测涨跌幅", f"{long_term.get('predicted_return', 0):+.2f}%"],
            ["上涨概率", f"{long_term.get('prob_up', 50):.1f}%"],
            ["关键因素", ", ".join(long_term.get("key_factors", [])[:3])],
            ["操作建议", long_term.get('suggestion', '')],
        ]
        self.add_table(table_data)

        # v5.0 新增：价值投资决策整合
        if value_investing and not value_investing.get("error"):
            self.add_section("六、价值投资决策整合（v5.0）")
            vi = value_investing
            table_data = [
                ["指标", "数值"],
                ["综合裁决", vi.get("verdict", "持有")],
                ["加权评分", f"{vi.get('weighted_score', 0):.1f}/100"],
                ["置信度", f"{vi.get('confidence', 0):.1f}/100"],
                ["公允价值区间", f"¥{vi.get('fair_value_range', [0,0,0])[0]} - ¥{vi.get('fair_value_range', [0,0,0])[2]}"],
                ["安全边际", f"{vi.get('margin_of_safety', 0):.1f}%"],
            ]
            self.add_table(table_data)

            # 6 模块评分明细
            self.add_text("6 模块评分明细:")
            breakdown = vi.get("breakdown", {})
            labels = {"dcf": "DCF估值", "moat": "护城河", "financial_health": "财务健康",
                      "management": "管理层", "industry": "行业吸引力", "factor": "量化因子"}
            for k, v in breakdown.items():
                self.add_text(f"  • {labels.get(k, k)}: {v.get('score', 0)}/100（权重 {v.get('weight', 0)*100:.0f}%）")

            if vi.get("strengths"):
                self.add_text("核心优势:")
                for s in vi["strengths"]:
                    self.add_text(f"  ✅ {s}")
            if vi.get("risks"):
                self.add_text("主要风险:")
                for r in vi["risks"]:
                    self.add_text(f"  ⚠️ {r}")
            if vi.get("narrative"):
                self.add_text(f"推演: {vi['narrative']}")

        # 风险提示
        risk_section = "七" if (value_investing and not value_investing.get("error")) else "六"
        self.add_section(f"{risk_section}、风险提示")
        self.add_text("1. 本报告仅供参考，不构成投资建议")
        self.add_text("2. 长期投资需关注基本面变化")
        self.add_text("3. 请定期审视持仓，适时调整")

        output_path = self.output_dir / f"long_report_{today}_{code}.pdf"
        return self.build(str(output_path))