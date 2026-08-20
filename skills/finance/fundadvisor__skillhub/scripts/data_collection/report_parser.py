"""
定期报告解析脚本
解析年报、半年报、季报中的持仓和观点数据

每次更新从最新的两个报告获取：
- 年度报告：每年4月30日前发布（上年度）
- 半年报告：每年8月31日前发布（上半年）
- 季度报告：每季度结束后15个工作日内发布
"""
import re
import json
import time
from datetime import datetime

class ReportParser:
    """定期报告解析器"""

    def __init__(self):
        self.quarter_map = {
            '03-31': 'Q1',
            '06-30': 'Q2',
            '09-30': 'Q3',
            '12-31': 'Q4'
        }
        self.report_schedule = {
            'annual': {'months': [4], 'deadline': '04-30'},
            'semi_annual': {'months': [8], 'deadline': '08-31'},
            'quarterly': {'months': [4, 7, 10, 1], 'deadline': None}
        }

    def parse_annual_report(self, report_text):
        """
        解析年报文本，提取关键信息

        返回:
            dict: 包含投资风格、重仓股、观点等
        """
        result = {
            'report_type': 'annual',
            'investment_style': '',
            'investment_goal': '',
            'investment_scope': '',
            'top_stocks': [],
            'top_bonds': [],
            'manager_views': [],
            'parsed_at': time.strftime('%Y-%m-%d')
        }

        # 提取投资目标
        goal_pattern = r'投资目标[:：]\s*(.+?)(?:\n|；)'
        goal_match = re.search(goal_pattern, report_text)
        if goal_match:
            result['investment_goal'] = goal_match.group(1).strip()

        # 提取投资范围
        scope_pattern = r'投资范围[:：]\s*(.+?)(?:\n|；)'
        scope_match = re.search(scope_pattern, report_text)
        if scope_match:
            result['investment_scope'] = scope_match.group(1).strip()

        # 提取十大重仓股
        stock_section = self._extract_section(report_text, '股票投资组合', '重仓股')
        if stock_section:
            result['top_stocks'] = self._parse_top_stocks(stock_section)

        # 提取债券投资组合
        bond_section = self._extract_section(report_text, '债券投资组合', '重仓债券')
        if bond_section:
            result['top_bonds'] = self._parse_top_bonds(bond_section)

        # 提取基金经理观点
        view_section = self._extract_section(report_text, '管理人报告', '投资策略')
        if view_section:
            result['manager_views'] = self._parse_views(view_section)

        return result

    def parse_quarter_report(self, report_text):
        """
        解析季报文本
        """
        result = {
            'report_type': 'quarter',
            'top_stocks': [],
            'top_bonds': [],
            'manager_views': [],
            'parsed_at': time.strftime('%Y-%m-%d')
        }

        # 季报相对简短，主要提取持仓和观点
        stock_section = self._extract_section(report_text, '股票组合', '占净值')
        if stock_section:
            result['top_stocks'] = self._parse_top_stocks(stock_section)

        view_section = self._extract_section(report_text, '运作分析', '展望')
        if view_section:
            result['manager_views'] = self._parse_views(view_section)

        return result

    def parse_semi_annual_report(self, report_text):
        """
        解析半年报文本
        半年报结构与年报类似，但内容相对简化
        """
        result = {
            'report_type': 'semi_annual',
            'investment_style': '',
            'investment_goal': '',
            'investment_scope': '',
            'top_stocks': [],
            'top_bonds': [],
            'manager_views': [],
            'parsed_at': time.strftime('%Y-%m-%d')
        }

        # 提取投资目标（半年报通常没有）
        goal_pattern = r'投资目标[:：]\s*(.+?)(?:\n|；)'
        goal_match = re.search(goal_pattern, report_text)
        if goal_match:
            result['investment_goal'] = goal_match.group(1).strip()

        # 提取投资范围
        scope_pattern = r'投资范围[:：]\s*(.+?)(?:\n|；)'
        scope_match = re.search(scope_pattern, report_text)
        if scope_match:
            result['investment_scope'] = scope_match.group(1).strip()

        # 提取十大重仓股
        stock_section = self._extract_section(report_text, '股票投资组合', '重仓股')
        if stock_section:
            result['top_stocks'] = self._parse_top_stocks(stock_section)

        # 提取债券投资组合
        bond_section = self._extract_section(report_text, '债券投资组合', '重仓债券')
        if bond_section:
            result['top_bonds'] = self._parse_top_bonds(bond_section)

        # 提取基金经理观点
        view_section = self._extract_section(report_text, '管理人报告', '投资策略')
        if view_section:
            result['manager_views'] = self._parse_views(view_section)

        return result

    def get_latest_reports(self, report_date_list):
        """
        获取最新的两个报告

        参数:
            report_date_list: 报告日期列表

        返回:
            list: 最新的两个报告日期
        """
        sorted_dates = sorted(report_date_list, reverse=True)
        return sorted_dates[:2]

    def _extract_section(self, text, start_keyword, end_keyword):
        """提取文本段落"""
        pattern = rf'{start_keyword}[：:]*([\s\S]*?)(?={end_keyword}|$)'
        match = re.search(pattern, text)
        if match:
            return match.group(1)
        return ''

    def _parse_top_stocks(self, section_text):
        """解析前十大重仓股"""
        stocks = []

        # 匹配股票名称和持仓比例
        # 格式如：1、贵州茅台  占净值比 5.2%
        lines = section_text.split('\n')
        for line in lines[:10]:  # 取前10
            name_match = re.search(r'[一-龥]{2,10}', line)
            weight_match = re.search(r'[\d.]+%', line)

            if name_match and weight_match:
                stocks.append({
                    'name': name_match.group(),
                    'weight': weight_match.group()
                })

        return stocks

    def _parse_top_bonds(self, section_text):
        """解析前十大重仓债券"""
        bonds = []

        lines = section_text.split('\n')
        for line in lines[:10]:
            name_match = re.search(r'[一-龥]{2,15}', line)
            weight_match = re.search(r'[\d.]+%', line)

            if name_match and weight_match:
                bonds.append({
                    'name': name_match.group(),
                    'weight': weight_match.group()
                })

        return bonds

    def _parse_views(self, section_text):
        """解析基金经理观点"""
        views = []

        # 提取段落中的核心观点
        sentences = re.split(r'[。；]', section_text)
        for sent in sentences:
            if len(sent) > 20:  # 过滤短句
                views.append(sent.strip())

        return views[:5]  # 最多取5条

    def get_report_quarter(self, report_date):
        """根据报告日期判断季度"""
        month_day = f"{report_date.month:02d}-{report_date.day:02d}"
        return self.quarter_map.get(month_day, 'Q?')

    def save_holdings(self, holdings_data, filepath):
        """保存持仓数据"""
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump({'holdings': holdings_data, 'meta': {
                'total_records': len(holdings_data),
                'last_update': time.strftime('%Y-%m-%d'),
                'report_seasons': ['2025年报', '2026一季报']
            }}, f, ensure_ascii=False, indent=2)

def main():
    parser = ReportParser()

    # 示例：解析一段年报文本
    sample_text = """
    投资目标：在严格控制风险的前提下，追求超过业绩比较基准的投资回报。

    投资范围：股票资产占基金资产的比例为60%-95%；
    港股通标的股票占股票资产的0-50%；
    权证占基金资产净值的0-3%。

    股票投资组合：
    1、贵州茅台 占净值比 5.2%
    2、五粮液 占净值比 4.8%
    3、宁德时代 占净值比 4.5%

    管理人报告：
    2025年，市场整体呈现震荡上行格局。我们坚持价值投资理念，
    在科技板块估值回调过程中逐步加仓，看好AI应用端的中长期发展。
    """

    result = parser.parse_annual_report(sample_text)
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()