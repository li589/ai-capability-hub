# -*- coding: utf-8 -*-
"""
可视化报告生成器
生成ASCII/文本格式的分析报告和图表
"""

import json
import re
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from pathlib import Path


class ASCIIChart:
    """ASCII图表生成器"""

    @staticmethod
    def bar_chart(data: Dict[str, float],
                  title: str = "",
                  width: int = 40,
                  show_values: bool = True) -> str:
        """
        生成水平条形图

        Args:
            data: 数据字典 {label: value}
            title: 图表标题
            width: 最大条形宽度
            show_values: 是否显示数值

        Returns:
            ASCII图表字符串
        """
        if not data:
            return "无数据"

        lines = []

        if title:
            lines.append(title)
            lines.append("-" * len(title))

        max_label_len = max(len(str(k)) for k in data.keys())
        max_value = max(abs(v) for v in data.values()) if data else 1

        for label, value in data.items():
            label_str = str(label).ljust(max_label_len)
            bar_len = int(abs(value) / max_value * width) if max_value != 0 else 0
            bar = "█" * bar_len
            value_str = f"{value:+.2f}" if isinstance(value, float) else f"{value}"

            if value < 0:
                lines.append(f"{label_str} │ {value_str:>10} {bar}")
            else:
                lines.append(f"{label_str} │ {bar} {value_str:>10}")

        return "\n".join(lines)

    @staticmethod
    def vertical_bar(data: List[Tuple[str, float]],
                     title: str = "",
                     height: int = 15) -> str:
        """
        生成垂直条形图

        Args:
            data: 数据列表 [(label, value)]
            title: 图表标题
            height: 图表高度

        Returns:
            ASCII图表字符串
        """
        if not data:
            return "无数据"

        lines = []

        if title:
            lines.append(title)
            lines.append("-" * len(title))

        max_value = max(abs(v) for _, v in data) if data else 1
        labels = [str(label) for label, _ in data]
        max_label_len = max(len(l) for l in labels) if labels else 0

        # 生成图表网格
        grid = [[" " for _ in data] for _ in range(height)]

        for col, (label, value) in enumerate(data):
            bar_height = int(abs(value) / max_value * height) if max_value != 0 else 0
            if value >= 0:
                for row in range(height):
                    if row >= height - bar_height:
                        grid[row][col] = "█"
            else:
                for row in range(height):
                    if row < bar_height:
                        grid[row][col] = "▓"

        # 输出
        for row in range(height - 1, -1, -1):
            row_str = "".join(grid[row])
            lines.append(f"│{row_str}│")

        # 标签
        lines.append("└" + "─" * len(data) + "┘")
        label_line = ""
        for i, label in enumerate(labels):
            label_center = len(label) // 2
            offset = i - label_center
            if offset >= 0:
                label_line += label[:len(data)]
            else:
                label_line += " " * abs(offset) + label[:len(data)]
        lines.append(label_line)

        return "\n".join(lines)

    @staticmethod
    def pie_chart(data: Dict[str, float], title: str = "") -> str:
        """
        生成饼图（简化文本版）

        Args:
            data: 数据字典
            title: 图表标题

        Returns:
            ASCII饼图
        """
        if not data:
            return "无数据"

        lines = []

        if title:
            lines.append(title)
            lines.append("-" * len(title))

        total = sum(data.values())
        if total == 0:
            return "总和为0"

        # 简化饼图
        symbols = ["●", "○", "◆", "◇", "■", "□", "▲", "△", "★", "☆"]

        for i, (label, value) in enumerate(data.items()):
            pct = value / total * 100
            symbol = symbols[i % len(symbols)]
            lines.append(f"  {symbol} {label:<15} {pct:>5.1f}%  {'█' * int(pct / 5)}")

        return "\n".join(lines)

    @staticmethod
    def line_chart(data: List[Tuple[str, float]],
                   title: str = "",
                   width: int = 50,
                   height: int = 10) -> str:
        """
        生成折线图

        Args:
            data: 数据列表 [(time, value)]
            title: 图表标题
            width: 图表宽度
            height: 图表高度

        Returns:
            ASCII折线图
        """
        if not data or len(data) < 2:
            return "数据点不足"

        lines = []

        if title:
            lines.append(title)
            lines.append("-" * len(title))

        times = [str(t) for t, _ in data]
        values = [v for _, v in data]

        max_val = max(values)
        min_val = min(values)
        val_range = max_val - min_val if max_val != min_val else 1

        # 创建网格
        grid = [[" " for _ in range(width)] for _ in range(height)]

        # 绘制折线
        for i in range(len(data)):
            x = int(i / (len(data) - 1) * (width - 1))
            y = int((values[i] - min_val) / val_range * (height - 1))
            grid[height - 1 - y][x] = "●"

        # 绘制线条
        for i in range(len(data) - 1):
            x1 = int(i / (len(data) - 1) * (width - 1))
            x2 = int((i + 1) / (len(data) - 1) * (width - 1))
            y1 = int((values[i] - min_val) / val_range * (height - 1))
            y2 = int((values[i + 1] - min_val) / val_range * (height - 1))

            if x1 == x2:
                grid[height - 1 - max(y1, y2)][x1] = "│"
            else:
                for x in range(min(x1, x2), max(x1, x2) + 1):
                    if 0 <= x < width:
                        grid[height - 1 - max(y1, y2)][x] = "─"

        # 输出网格
        for row in grid:
            lines.append("│" + "".join(row) + "│")

        # X轴标签
        label_step = max(1, len(times) // min(5, len(times)))
        x_labels = ""
        for i in range(0, len(times), label_step):
            x_labels += times[i][:8].center(width // min(5, len(times)))
        lines.append("└" + "─" * width + "┘")
        lines.append(x_labels[:width])

        # Y轴标签
        lines.append(f"最大值: {max_val}  最小值: {min_val}")

        return "\n".join(lines)


class ReportFormatter:
    """报告格式化器"""

    @staticmethod
    def format_company_report(company_data: Dict[str, Any]) -> str:
        """
        格式化公司分析报告

        Args:
            company_data: 公司数据

        Returns:
            格式化的报告文本
        """
        lines = []

        # 标题
        name = company_data.get('name', company_data.get('stock_name', '未知公司'))
        code = company_data.get('code', company_data.get('stock_code', ''))

        lines.append("\n" + "=" * 70)
        lines.append(f"  {name} ({code}) 综合分析报告")
        lines.append("=" * 70)
        lines.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        # 基本信息
        if 'basic_info' in company_data:
            lines.append("\n【基本信息】")
            info = company_data['basic_info']
            for k, v in info.items():
                lines.append(f"  {k}: {v}")

        # 财务指标
        if 'financials' in company_data:
            lines.append("\n【财务指标】")
            financials = company_data['financials']

            # 生成图表
            if 'revenue' in financials and 'profit' in financials:
                chart_data = {
                    '营业收入': financials.get('revenue', 0) / 1e8,
                    '净利润': financials.get('profit', 0) / 1e8,
                    '总资产': financials.get('total_assets', 0) / 1e8,
                    '净资产': financials.get('net_assets', 0) / 1e8
                }
                lines.append("\n" + ASCIIChart.bar_chart(chart_data, "主要财务数据 (亿元)", width=30))

        # 估值指标
        if 'valuation' in company_data:
            lines.append("\n【估值指标】")
            val = company_data['valuation']
            for k, v in val.items():
                lines.append(f"  {k}: {v}")

        # 股东信息
        if 'holders' in company_data:
            lines.append("\n【股东信息】")
            holders = company_data['holders']
            if 'top_10_holders' in holders:
                lines.append("  前十大股东:")
                for i, h in enumerate(holders['top_10_holders'][:5], 1):
                    lines.append(f"    {i}. {h.get('name', '')} - 持股{h.get('shares', 0):.2f}%")

        # 机构评级
        if 'rating' in company_data:
            lines.append("\n【机构评级】")
            rating = company_data['rating']
            if isinstance(rating, dict):
                lines.append(f"  综合评级: {rating.get('overall', 'N/A')}")
                if 'target_price' in rating:
                    lines.append(f"  目标价: {rating['target_price']}")
            else:
                lines.append(f"  {rating}")

        lines.append("\n" + "=" * 70)

        return "\n".join(lines)

    @staticmethod
    def format_financial_comparison(financials: Dict[str, Any]) -> str:
        """
        格式化财务对比报告

        Args:
            financials: 财务对比数据

        Returns:
            格式化报告
        """
        lines = []

        lines.append("\n" + "=" * 70)
        lines.append("  财务数据对比报告")
        lines.append("=" * 70)

        periods = financials.get('periods', [])
        metrics = financials.get('metrics', {})

        if not periods:
            lines.append("\n无数据")
            return "\n".join(lines)

        lines.append(f"\n报告期: {' | '.join(periods)}")

        # 关键指标表格
        lines.append("\n┌─────────────────────────────────────────────────────────────┐")

        metric_names = {
            'BASIC_EPS': '每股收益(元)',
            'TOTAL_OPERATE_INCOME': '营业收入(亿)',
            'PARENT_NETPROFIT': '净利润(亿)',
            'WEIGHTAVG_ROE': '加权ROE(%)',
            'XSMLL': '毛利率(%)',
            'MGJYXJJE': '每股现金流(元)'
        }

        for metric_key, metric_name in metric_names.items():
            if metric_key in metrics:
                values = metrics[metric_key]
                val_strs = []

                for period in periods:
                    val = values.get(period)
                    if val is not None:
                        if metric_key in ['BASIC_EPS', 'MGJYXJJE']:
                            val_strs.append(f"¥{val:>8.2f}")
                        elif metric_key in ['WEIGHTAVG_ROE', 'XSMLL']:
                            val_strs.append(f"{val:>8.2f}%")
                        else:
                            val_strs.append(f"¥{val/1e8:>7.2f}亿")
                    else:
                        val_strs.append("      N/A")

                lines.append(f"│ {metric_name:<20} {'│ '.join(val_strs)} │")

        lines.append("└─────────────────────────────────────────────────────────────┘")

        # 趋势图表
        if 'revenue' in metrics and len(periods) >= 2:
            chart_data = [(p, metrics['revenue'].get(p, 0) / 1e8) for p in periods]
            lines.append("\n" + ASCIIChart.line_chart(chart_data, "营业收入趋势 (亿元)", width=40, height=8))

        lines.append("\n" + "=" * 70)

        return "\n".join(lines)

    @staticmethod
    def format_portfolio_report(portfolio: Dict[str, Any]) -> str:
        """
        格式化投资组合报告

        Args:
            portfolio: 组合数据

        Returns:
            格式化报告
        """
        lines = []

        lines.append("\n" + "=" * 70)
        lines.append("  投资组合分析报告")
        lines.append("=" * 70)

        name = portfolio.get('name', portfolio.get('portfolio_name', '未知组合'))
        lines.append(f"\n组合名称: {name}")

        # 业绩表现
        if 'performance' in portfolio:
            lines.append("\n【业绩表现】")
            perf = portfolio['performance']

            if 'cumulative_return' in perf:
                lines.append(f"  累计收益: {perf['cumulative_return']:+.2f}%")
            if 'annualized_return' in perf:
                lines.append(f"  年化收益: {perf['annualized_return']:+.2f}%")

            # 周期表现图表
            period_data = []
            for period in ['1month', '3month', '6month', '1year', '3year']:
                if period in perf:
                    period_labels = {'1month': '近1月', '3month': '近3月', '6month': '近6月',
                                   '1year': '近1年', '3year': '近3年'}
                    period_data.append((period_labels.get(period, period), perf[period]))

            if period_data:
                lines.append("\n各周期表现:")
                lines.append(ASCIIChart.bar_chart(dict(period_data), width=25, show_values=True))

        # 资产配置
        if 'allocation' in portfolio:
            lines.append("\n【资产配置】")
            alloc = portfolio['allocation']

            # 饼图
            pie_data = {}
            for asset_type in ['stocks', 'bonds', 'funds', 'cash']:
                if asset_type in alloc and alloc[asset_type] > 0:
                    labels = {'stocks': '股票', 'bonds': '债券', 'funds': '基金', 'cash': '现金'}
                    pie_data[labels.get(asset_type, asset_type)] = alloc[asset_type]

            if pie_data:
                lines.append(ASCIIChart.pie_chart(pie_data))

        # 持仓明细
        if 'positions' in portfolio:
            lines.append("\n【持仓明细】")
            positions = portfolio['positions']

            lines.append(f"  {'名称':<20} {'代码':<8} {'权重':>8} {'类型':<6}")
            lines.append("  " + "-" * 50)

            for p in positions[:10]:
                name_str = (p.get('name', '') or p.get('fund_name', ''))[:18]
                code_str = p.get('code', p.get('fund_code', ''))
                weight = p.get('weight', 0)
                ptype = p.get('type', p.get('asset_type', ''))
                lines.append(f"  {name_str:<20} {code_str:<8} {weight:>7.2f}% {ptype:<6}")

            if len(positions) > 10:
                lines.append(f"  ... 还有{len(positions) - 10}只持仓")

        # 风险指标
        if 'risk_metrics' in portfolio:
            lines.append("\n【风险指标】")
            risk = portfolio['risk_metrics']

            risk_items = []
            for k, v in risk.items():
                if v:
                    labels = {'sharpe_ratio': '夏普比率', 'max_drawdown': '最大回撤',
                             'volatility': '波动率', 'calmar_ratio': '卡玛比率'}
                    risk_items.append((labels.get(k, k), v))

            for label, value in risk_items:
                if 'ratio' in label.lower() or 'sharpe' in label.lower():
                    lines.append(f"  {label}: {value:.2f}")
                else:
                    lines.append(f"  {label}: {value:.2f}%")

        lines.append("\n" + "=" * 70)

        return "\n".join(lines)

    @staticmethod
    def format_news_report(news_data: Dict[str, Any]) -> str:
        """
        格式化新闻舆情报告

        Args:
            news_data: 新闻数据

        Returns:
            格式化报告
        """
        lines = []

        lines.append("\n" + "=" * 70)
        lines.append("  新闻舆情分析报告")
        lines.append("=" * 70)

        code = news_data.get('stock_code', '')
        sentiment = news_data.get('sentiment', 'neutral')
        score = news_data.get('score', 0)

        sentiment_labels = {'positive': '偏正面', 'negative': '偏负面', 'neutral': '中性'}
        sentiment_icons = {'positive': '↑', 'negative': '↓', 'neutral': '→'}

        lines.append(f"\n股票代码: {code}")
        lines.append(f"舆情倾向: {sentiment_labels.get(sentiment, '未知')} {sentiment_icons.get(sentiment, '')}")
        lines.append(f"情感评分: {score:.2f} (范围-1到+1)")

        # 统计
        if 'positive_count' in news_data:
            lines.append(f"\n正面新闻: {news_data['positive_count']}条")
            lines.append(f"负面新闻: {news_data['negative_count']}条")
            lines.append(f"中性新闻: {news_data['neutral_count']}条")

            # 情感分布图
            total = news_data.get('total_news', 1)
            pos_pct = news_data['positive_count'] / total * 100
            neg_pct = news_data['negative_count'] / total * 100
            neu_pct = news_data['neutral_count'] / total * 100

            lines.append(f"\n情感分布:")
            chart_data = {'正面': pos_pct, '负面': neg_pct, '中性': neu_pct}
            lines.append(ASCIIChart.bar_chart(chart_data, width=30))

        # 最新新闻
        if 'latest_news' in news_data:
            lines.append("\n【最新新闻】")
            for i, news in enumerate(news_data['latest_news'][:5], 1):
                title = news.get('title', '')[:40]
                source = news.get('source', '')
                time_str = news.get('publish_time', '')[:10]
                lines.append(f"  {i}. [{time_str}] {title}")
                lines.append(f"     来源: {source}")

        lines.append("\n" + "=" * 70)

        return "\n".join(lines)


class ASCIIReportExporter:
    """报告导出器"""

    @staticmethod
    def export_to_json(data: Dict[str, Any], file_path: str) -> str:
        """
        导出为JSON

        Args:
            data: 数据
            file_path: 保存路径

        Returns:
            保存路径
        """
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        return str(path)

    @staticmethod
    def export_to_markdown(report: str, file_path: str) -> str:
        """
        导出为Markdown

        Args:
            report: 报告文本
            file_path: 保存路径

        Returns:
            保存路径
        """
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, 'w', encoding='utf-8') as f:
            f.write(report)

        return str(path)

    @staticmethod
    def export_to_text(report: str, file_path: str) -> str:
        """
        导出为纯文本

        Args:
            report: 报告文本
            file_path: 保存路径

        Returns:
            保存路径
        """
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        # 移除ANSI转义码
        clean_report = re.sub(r'\x1b\[[0-9;]*m', '', report)

        with open(path, 'w', encoding='utf-8') as f:
            f.write(clean_report)

        return str(path)


def generate_analysis_report(data_type: str, data: Dict[str, Any]) -> str:
    """
    生成综合分析报告

    Args:
        data_type: 数据类型 (company, financial, portfolio, news)
        data: 数据

    Returns:
        格式化的报告文本
    """
    formatter = ReportFormatter()

    generators = {
        'company': formatter.format_company_report,
        'financial': formatter.format_financial_comparison,
        'portfolio': formatter.format_portfolio_report,
        'news': formatter.format_news_report
    }

    generator = generators.get(data_type)
    if not generator:
        return f"不支持的报告类型: {data_type}"

    return generator(data)


# CLI测试
if __name__ == "__main__":
    # 测试图表
    chart = ASCIIChart()

    print("=== 水平条形图 ===")
    data = {"苹果": 45, "香蕉": 30, "橙子": 25}
    print(chart.bar_chart(data, "水果销量", width=30))

    print("\n=== 饼图 ===")
    data = {"股票": 60, "债券": 25, "现金": 15}
    print(chart.pie_chart(data, "资产配置"))

    print("\n=== 折线图 ===")
    data = [("1月", 100), ("2月", 120), ("3月", 115), ("4月", 130), ("5月", 145)]
    print(chart.line_chart(data, "月度趋势", width=40, height=8))

    # 测试报告
    print("\n=== 报告格式化测试 ===")
    portfolio = {
        'name': '稳健增长组合',
        'performance': {
            'cumulative_return': 25.6,
            'annualized_return': 12.3,
            '1month': 2.5,
            '3month': 8.3,
            '6month': 15.2,
            '1year': 25.6
        },
        'allocation': {
            'stocks': 60,
            'bonds': 30,
            'cash': 10
        },
        'positions': [
            {'name': '贵州茅台', 'code': '600519', 'weight': 8.5, 'type': 'stock'},
            {'name': '宁德时代', 'code': '300750', 'weight': 7.2, 'type': 'stock'},
            {'name': '招商银行', 'code': '600036', 'weight': 6.0, 'type': 'stock'}
        ],
        'risk_metrics': {
            'sharpe_ratio': 1.85,
            'max_drawdown': -12.5,
            'volatility': 8.3
        }
    }

    formatter = ReportFormatter()
    print(formatter.format_portfolio_report(portfolio))
