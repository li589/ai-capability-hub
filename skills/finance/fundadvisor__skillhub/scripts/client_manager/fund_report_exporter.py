# -*- coding: utf-8 -*-
"""
基金报告导出器 v1.0 — Word / PDF / 增强 Excel
支持：单产品 / 多产品 / 投资组合，含绩效数据 + 分析报告 + 图表
"""
import os, math, json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional

SCRIPT_DIR = Path(__file__).resolve().parent
import sys as _sys; _sys.path.insert(0, str(SCRIPT_DIR.parent))
from fund_advisor_paths import DATA_DIR  # noqa: E402


# ── 中文字体检测 ──
def _detect_cn_ttf():
    import platform
    candidates = []
    if platform.system() == "Windows":
        wd = os.environ.get("WINDIR", "C:\\Windows")
        candidates = [os.path.join(wd, "Fonts", f) for f in
                      ["simhei.ttf", "SIMHEI.TTF", "simsun.ttc", "msyh.ttf"]]
    else:
        candidates = ["/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
                      "/System/Library/Fonts/PingFang.ttc"]
    for p in candidates:
        if os.path.isfile(p): return p
    return ""

_CN_TTF = _detect_cn_ttf()


class FundReportExporter:
    """基金报告导出器 — Word/PDF/Excel 多格式"""

    def __init__(self, output_dir=None):
        self.output_dir = Path(output_dir or DATA_DIR / "reports")
        self.output_dir.mkdir(parents=True, exist_ok=True)

    # ═══════════════════════════════════════════
    #  Excel 导出（增强版：多 Sheet + 绩效 + 图表）
    # ═══════════════════════════════════════════

    def export_excel(self, funds: List[Dict], output_path: str = None,
                     mode: str = "portfolio", title: str = "基金分析报告") -> str:
        """导出增强 Excel 报告。

        Args:
            funds: 基金列表，每项含 fund_code/fund_name/amount/nav/perf(可选)
            mode: single(单产品) / multi(多产品) / portfolio(投资组合)
            title: 报告标题
        """
        try:
            import openpyxl
            from openpyxl.styles import Font, PatternFill, Alignment, Border, Side, numbers
            from openpyxl.chart import BarChart, PieChart, LineChart, Reference
            from openpyxl.utils import get_column_letter
        except ImportError:
            return "请安装 openpyxl: pip install openpyxl"

        if not output_path:
            ts = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_path = str(self.output_dir / f'fund_report_{ts}.xlsx')

        wb = openpyxl.Workbook()
        CN = "宋体"
        hdr_font = Font(name=CN, bold=True, size=11, color="FFFFFF")
        hdr_fill = PatternFill("solid", fgColor="2F5496")
        hdr_align = Alignment(horizontal="center", vertical="center", wrap_text=True)
        cell_align = Alignment(horizontal="center", vertical="center")
        border = Border(left=Side("thin"), right=Side("thin"),
                        top=Side("thin"), bottom=Side("thin"))
        title_font = Font(name=CN, bold=True, size=16, color="2F5496")

        # ── Sheet 1: 总览 ──
        ws = wb.active; ws.title = "报告总览"
        ws.merge_cells("A1:F1")
        c = ws["A1"]; c.value = title; c.font = title_font; c.alignment = Alignment(horizontal="center")
        ws["A2"] = f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        ws["A2"].font = Font(name=CN, size=10, color="666666")

        # 总资产汇总
        total_invested = sum(f.get("amount", 0) or 0 for f in funds)
        total_value = sum(f.get("market_value", (f.get("amount", 0) or 0) * (f.get("current_nav", 1) or 1)) for f in funds)
        total_profit = total_value - total_invested
        overview = [
            ["指标", "数值"], ["基金数量", len(funds)], ["总投入(元)", round(total_invested, 2)],
            ["总市值(元)", round(total_value, 2)], ["总盈亏(元)", round(total_profit, 2)],
            ["总收益率(%)", round(total_profit / total_invested * 100, 2) if total_invested > 0 else 0],
        ]
        for i, (k, v) in enumerate(overview):
            c1 = ws.cell(row=i + 4, column=1, value=k)
            c2 = ws.cell(row=i + 4, column=2, value=v)
            c1.font = Font(name=CN, bold=True, size=11); c2.font = Font(name=CN, size=11)
            c1.border = c2.border = border

        # ── Sheet 2: 持仓明细 ──
        ws2 = wb.create_sheet("持仓明细")
        headers = ["序号", "基金代码", "基金名称", "投入金额(元)", "持有份额", "当前净值", "持仓市值(元)", "盈亏(元)", "收益率(%)"]
        if mode == "single":
            headers.extend(["Sharpe", "MaxDD(%)", "评级"])
        for ci, h in enumerate(headers, 1):
            c = ws2.cell(row=1, column=ci, value=h)
            c.font = hdr_font; c.fill = hdr_fill; c.alignment = hdr_align; c.border = border

        for ri, f in enumerate(funds):
            r = ri + 2
            amt = f.get("amount", 0) or 0
            nav = f.get("current_nav", 1) or 1
            shares = f.get("shares", amt / nav if nav > 0 else 0) or 0
            mv = shares * nav
            profit = mv - amt
            pct = profit / amt * 100 if amt > 0 else 0
            vals = [ri + 1, f.get("fund_code", ""), f.get("fund_name", ""),
                    round(amt, 2), round(shares, 4), round(nav, 4),
                    round(mv, 2), round(profit, 2), round(pct, 2)]
            if mode == "single":
                perf = f.get("perf", {})
                vals.extend([perf.get("sharpe", 0), perf.get("max_drawdown", 0), perf.get("rating", "")])
            for ci, v in enumerate(vals, 1):
                c = ws2.cell(row=r, column=ci, value=v)
                c.font = Font(name=CN, size=10); c.alignment = cell_align; c.border = border
                if ci == 8:  # 盈亏列着色
                    c.font = Font(name=CN, size=10, color="008000" if isinstance(v, (int, float)) and v >= 0 else "FF0000")

        # 列宽
        widths = [6, 12, 20, 14, 12, 10, 14, 12, 11]
        if mode == "single": widths.extend([10, 10, 8])
        for i, w in enumerate(widths, 1):
            ws2.column_dimensions[get_column_letter(i)].width = w

        # ── Sheet 3: 业绩分析 ──
        if any(f.get("perf") for f in funds):
            ws3 = wb.create_sheet("业绩分析")
            ph = ["基金名称"] + ["年化收益(%)", "年化波动(%)", "Sharpe", "Sortino", "Calmar",
                                  "最大回撤(%)", "Alpha(%)", "Beta", "评级"]
            for ci, h in enumerate(ph, 1):
                c = ws3.cell(row=1, column=ci, value=h)
                c.font = hdr_font; c.fill = hdr_fill; c.alignment = hdr_align; c.border = border
            for ri, f in enumerate(funds):
                r = ri + 2; p = f.get("perf", {})
                vals = [f.get("fund_name", ""),
                        p.get("annual_return", 0), p.get("annual_volatility", 0),
                        p.get("sharpe", 0), p.get("sortino", 0), p.get("calmar", 0),
                        p.get("max_drawdown", 0), p.get("alpha", 0), p.get("beta", 1),
                        p.get("rating", "")]
                for ci, v in enumerate(vals, 1):
                    c = ws3.cell(row=r, column=ci, value=v)
                    c.font = Font(name=CN, size=10); c.alignment = cell_align; c.border = border
            for i, w in enumerate([18, 12, 12, 8, 8, 8, 10, 8, 6, 6], 1):
                ws3.column_dimensions[get_column_letter(i)].width = w

            # 添加柱状图（收益率对比）
            if len(funds) > 1:
                chart = BarChart()
                chart.type = "col"; chart.title = "基金收益率对比"; chart.y_axis.title = "年化收益率(%)"
                data_ref = Reference(ws3, min_col=2, min_row=0, max_row=len(funds) + 1)
                cats_ref = Reference(ws3, min_col=1, min_row=2, max_row=len(funds) + 1)
                chart.add_data(data_ref, titles_from_data=True)
                chart.set_categories(cats_ref); chart.width = 20; chart.height = 12
                ws3.add_chart(chart, "A" + str(len(funds) + 4))

        # ── Sheet 4: 资产配置 ──
        if mode == "portfolio" and len(funds) >= 2:
            ws4 = wb.create_sheet("资产配置")
            ws4.merge_cells("A1:E1"); ws4["A1"] = "资产配置分析"
            ws4["A1"].font = title_font
            pie_data = [("基金名称", "占比(%)")]
            for f in funds[:15]:
                pie_data.append((f.get("fund_name", "")[:15],
                                 round((f.get("amount", 0) or 0) / total_invested * 100, 1) if total_invested > 0 else 0))
            for ri, (name, pct) in enumerate(pie_data):
                ws4.cell(row=ri + 3, column=1, value=name).font = Font(name=CN, size=10)
                ws4.cell(row=ri + 3, column=2, value=pct).font = Font(name=CN, size=10)
            if len(funds) >= 2:
                pie = PieChart(); pie.title = "资产配置饼图"
                dref = Reference(ws4, min_col=2, min_row=3, max_row=len(funds) + 2)
                cref = Reference(ws4, min_col=1, min_row=4, max_row=len(funds) + 2)
                pie.add_data(dref, titles_from_data=True); pie.set_categories(cref)
                pie.width = 18; pie.height = 14
                ws4.add_chart(pie, "D3")

        wb.save(output_path)
        return str(output_path)

    # ═══════════════════════════════════════════
    #  Word 导出
    # ═══════════════════════════════════════════

    def export_word(self, funds: List[Dict], output_path: str = None,
                    title: str = "基金分析报告") -> str:
        """导出 Word 报告。"""
        try:
            from docx import Document
            from docx.shared import Pt, Inches, Cm, RGBColor
            from docx.enum.text import WD_ALIGN_PARAGRAPH
        except ImportError:
            return "请安装 python-docx: pip install python-docx"

        if not output_path:
            ts = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_path = str(self.output_dir / f'fund_report_{ts}.docx')

        doc = Document()
        # 设置默认字体
        style = doc.styles["Normal"]
        style.font.name = "Times New Roman"; style.font.size = Pt(11)
        rPr = style.element.get_or_add_rPr()
        NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
        rF = rPr.makeelement(f"{{{NS}}}rFonts", {})
        for attr, val in [("ascii", "Times New Roman"), ("hAnsi", "Times New Roman"),
                           ("eastAsia", "宋体"), ("cs", "Times New Roman")]:
            rF.set(f"{{{NS}}}{attr}", val)
        rPr.insert(0, rF)

        # 标题
        h = doc.add_heading(title, 0); h.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.add_run(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}").italic = True

        # 总览表
        total_invested = sum(f.get("amount", 0) or 0 for f in funds)
        total_value = sum(f.get("market_value", (f.get("amount", 0) or 0) * (f.get("current_nav", 1) or 1)) for f in funds)
        doc.add_heading("一、资产总览", 1)
        t = doc.add_table(rows=7, cols=2); t.style = "Light Grid Accent 1"
        for ri, (k, v) in enumerate([("基金数量", len(funds)), ("总投入(元)", f"{total_invested:,.2f}"),
                                      ("总市值(元)", f"{total_value:,.2f}"),
                                      ("总盈亏(元)", f"{total_value - total_invested:,.2f}"),
                                      ("总收益率", f"{(total_value/total_invested-1)*100:.2f}%" if total_invested > 0 else "0%"),
                                      ("报告日期", datetime.now().strftime('%Y-%m-%d'))]):
            t.rows[ri].cells[0].text = k; t.rows[ri].cells[1].text = str(v)

        # 持仓明细
        doc.add_heading("二、持仓明细", 1)
        for i, f in enumerate(funds, 1):
            amt = f.get("amount", 0) or 0; nav = f.get("current_nav", 1) or 1
            shares = f.get("shares", amt / nav) or 0; mv = shares * nav
            profit = mv - amt
            p = doc.add_paragraph()
            p.add_run(f"{i}. {f.get('fund_name','')} ({f.get('fund_code','')})").bold = True
            p.add_run(f"\n  投入: ¥{amt:,.2f} | 份额: {shares:,.2f} | 净值: {nav:.4f}")
            p.add_run(f"\n  市值: ¥{mv:,.2f} | 盈亏: ¥{profit:+,.2f} ({profit/amt*100:+.2f}%)" if amt > 0 else "")

        # 业绩分析
        if any(f.get("perf") for f in funds):
            doc.add_heading("三、业绩分析", 1)
            for f in funds:
                p = f.get("perf", {})
                if not p: continue
                doc.add_heading(f"  {f.get('fund_name','')}", 2)
                perf_text = (f"年化收益: {p.get('annual_return',0):.2f}% | "
                             f"Sharpe: {p.get('sharpe',0):.2f} | 最大回撤: {p.get('max_drawdown',0):.2f}% | "
                             f"评级: {p.get('rating','N/A')}")
                doc.add_paragraph(perf_text)

        # 风险提示
        doc.add_heading("四、风险提示", 1)
        doc.add_paragraph("1. 以上分析仅供参考，不构成投资建议。")
        doc.add_paragraph("2. 基金投资有风险，过往业绩不代表未来表现。")
        doc.add_paragraph("3. 请根据自身风险承受能力做出投资决策。")

        doc.save(output_path)
        return str(output_path)

    # ═══════════════════════════════════════════
    #  PDF 导出（通过 Word 转换或 reportlab）
    # ═══════════════════════════════════════════

    def export_pdf(self, funds: List[Dict], output_path: str = None,
                   title: str = "基金分析报告") -> str:
        """导出 PDF 报告。优先使用 reportlab，回退到 Word 转换。"""
        if not output_path:
            ts = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_path = str(self.output_dir / f'fund_report_{ts}.pdf')

        # 尝试 reportlab
        try:
            return self._export_pdf_reportlab(funds, output_path, title)
        except ImportError:
            pass

        # 回退：生成 Word 后提示手动转换
        docx_path = output_path.replace('.pdf', '.docx')
        result = self.export_word(funds, docx_path, title)
        if result and not result.startswith("请安装"):
            print(f"[PDF] 已生成 Word 文件: {docx_path}")
            print("[PDF] 请使用 Word/WPS/LibreOffice 另存为 PDF")
        return result

    def _export_pdf_reportlab(self, funds, output_path, title):
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import mm
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        from reportlab.lib import colors
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont

        cn_font = "Helvetica"
        if _CN_TTF:
            try:
                pdfmetrics.registerFont(TTFont("CnFont", _CN_TTF))
                cn_font = "CnFont"
            except Exception:
                pass

        doc = SimpleDocTemplate(output_path, pagesize=A4)
        elements = []
        styles = getSampleStyleSheet()
        cn_n = ParagraphStyle('cn', fontName=cn_font, fontSize=10, leading=16)
        cn_h1 = ParagraphStyle('cnh1', fontName=cn_font, fontSize=18, spaceAfter=12)
        cn_h2 = ParagraphStyle('cnh2', fontName=cn_font, fontSize=14, spaceAfter=8)

        elements.append(Paragraph(title, cn_h1))
        elements.append(Paragraph(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", cn_n))
        elements.append(Spacer(1, 10 * mm))

        total_inv = sum(f.get("amount", 0) or 0 for f in funds)
        total_val = sum(f.get("market_value", (f.get("amount", 0) or 0)) for f in funds)
        t = Table([["指标", "数值"], ["基金数量", str(len(funds))],
                    ["总投入", f"{total_inv:,.2f}"], ["总市值", f"{total_val:,.2f}"]],
                  colWidths=[150, 300])
        t.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                               ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                               ('FONTNAME', (0, 0), (-1, -1), cn_font),
                               ('FONTSIZE', (0, 0), (-1, -1), 10),
                               ('GRID', (0, 0), (-1, -1), 1, colors.black)]))
        elements.append(t); elements.append(Spacer(1, 10 * mm))

        elements.append(Paragraph("持仓明细", cn_h2))
        for f in funds:
            elements.append(Paragraph(
                f"{f.get('fund_name','')} ({f.get('fund_code','')}) — "
                f"投入: ¥{(f.get('amount',0) or 0):,.2f}", cn_n))

        elements.append(Spacer(1, 10 * mm))
        elements.append(Paragraph("风险提示：以上内容仅供参考，不构成投资建议。", cn_n))

        doc.build(elements)
        return output_path


# ── 便捷入口 ──

def export_fund_report(funds: List[Dict], fmt: str = "excel",
                       output_path: str = None, title: str = "基金分析报告") -> str:
    """一键导出基金报告。
    Args:
        funds: [{fund_code, fund_name, amount, current_nav, shares?, perf?}, ...]
        fmt: excel / word / pdf / all
    """
    exporter = FundReportExporter()
    if fmt == "excel":
        return exporter.export_excel(funds, output_path, title=title)
    elif fmt == "word":
        return exporter.export_word(funds, output_path, title=title)
    elif fmt == "pdf":
        return exporter.export_pdf(funds, output_path, title=title)
    elif fmt == "all":
        results = {}
        for f in ["excel", "word", "pdf"]:
            results[f] = getattr(exporter, f"export_{f}")(funds, title=title)
        return results
    return "未知格式"


if __name__ == "__main__":
    # 测试
    test_funds = [
        {"fund_code": "000001", "fund_name": "华夏成长混合", "amount": 50000, "current_nav": 1.398,
         "perf": {"annual_return": 12.5, "sharpe": 1.2, "sortino": 1.8, "calmar": 1.5, "max_drawdown": 15.3, "alpha": 3.2, "beta": 0.85, "rating": "A"}},
        {"fund_code": "110011", "fund_name": "易方达中小盘", "amount": 30000, "current_nav": 2.15,
         "perf": {"annual_return": 18.2, "sharpe": 1.5, "sortino": 2.1, "calmar": 2.0, "max_drawdown": 20.1, "alpha": 5.1, "beta": 0.92, "rating": "A+"}},
        {"fund_code": "519688", "fund_name": "交银精选", "amount": 20000, "current_nav": 0.89,
         "perf": {"annual_return": -3.5, "sharpe": -0.3, "sortino": -0.4, "calmar": -0.2, "max_drawdown": 28.5, "alpha": -2.1, "beta": 1.05, "rating": "C"}},
    ]
    e = FundReportExporter()
    # 测试 Excel
    xlsx_path = e.export_excel(test_funds, title="基金投资组合分析报告")
    print(f"Excel: {xlsx_path}")
    # 测试 Word
    docx_path = e.export_word(test_funds, title="基金投资组合分析报告")
    print(f"Word: {docx_path}")
