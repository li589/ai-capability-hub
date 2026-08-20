# -*- coding: utf-8 -*-
"""
自适应页面解析器 v2.0
当页面结构变化时，自动尝试多种解析策略确保数据获取
"""

import json
import re
from typing import Dict, List, Optional, Any

try:
    from bs4 import BeautifulSoup
    HAS_BS4 = True
except ImportError:
    HAS_BS4 = False
    BeautifulSoup = None


def _parse_html_tables_stdlib(html: str) -> List[List[List[str]]]:
    """无 BeautifulSoup 时的轻量 HTML 表格提取（table -> rows -> cells）。"""
    tables = []
    for table_match in re.findall(r"<table[^>]*>(.*?)</table>", html, re.S | re.I):
        rows = []
        for row_match in re.findall(r"<tr[^>]*>(.*?)</tr>", table_match, re.S | re.I):
            cells = []
            for cell_match in re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", row_match, re.S | re.I):
                text = re.sub(r"<[^>]+>", "", cell_match)
                text = re.sub(r"\s+", " ", text).strip()
                cells.append(text)
            if cells:
                rows.append(cells)
        if rows:
            tables.append(rows)
    return tables


class AdaptivePageParser:
    """
    自适应页面解析器 v2.0

    当页面结构变化时，自动尝试多种解析策略：
    1. CSS选择器匹配
    2. 表格解析
    3. 列表解析
    4. JSON提取
    5. 正则匹配
    """

    def __init__(self):
        pass

    def parse_table(self, html: str, selectors: List[str] = None) -> List[Dict]:
        """解析HTML表格"""
        if not html:
            return []

        if not HAS_BS4:
            results = []
            for table_rows in _parse_html_tables_stdlib(html):
                if not table_rows:
                    continue
                headers = table_rows[0]
                for row in table_rows[1:]:
                    item = {}
                    for i, cell in enumerate(row):
                        if i < len(headers):
                            item[headers[i]] = cell
                        else:
                            item[f"col_{i}"] = cell
                    if item:
                        results.append(item)
            return results

        soup = BeautifulSoup(html, 'html.parser')
        tables = []

        if selectors:
            for sel in selectors:
                tables.extend(soup.select(sel))
            # Fallback: 如果选择器没匹配到，尝试所有表格
            if not tables:
                tables = soup.find_all('table')
        else:
            tables = soup.find_all('table')

        results = []
        for table in tables:
            rows = table.find_all('tr')
            if not rows:
                continue

            # 提取表头
            header_row = rows[0]
            header_cells = header_row.find_all(['th', 'td'])
            headers = [cell.get_text(strip=True) for cell in header_cells]

            # 提取数据行
            for row in rows[1:]:
                cells = row.find_all(['td', 'th'])
                if cells and headers:
                    row_data = {}
                    for i, cell in enumerate(cells):
                        if i < len(headers):
                            row_data[headers[i]] = cell.get_text(strip=True)
                        else:
                            row_data[f'col_{i}'] = cell.get_text(strip=True)
                    if row_data:
                        results.append(row_data)

        return results

    def parse_institution_list(self, html: str) -> List[Dict]:
        """解析金融机构列表页面"""
        if not html:
            return []

        results = []

        # 方法1: 表格解析（多种选择器）
        selectors = ['table.institution-list', 'table.list', 'table.data', 'table']
        table_data = self.parse_table(html, selectors)
        results.extend(table_data)

        if not HAS_BS4:
            return results

        # 方法2: 列表解析
        soup = BeautifulSoup(html, 'html.parser')
        list_items = soup.select('ul.institution-list li, ul.list li, .institution-item, li')
        for item in list_items:
            text = item.get_text(strip=True)
            if text:
                results.append({'name': text, 'raw': text})

        # 方法3: div结构解析
        div_items = soup.select('div.institution, div.item, div.data-row')
        for div in div_items:
            name_elem = div.select_one('.name, .title, td:first-child')
            code_elem = div.select_one('.code, .id, td:nth-child(2)')
            if name_elem:
                item = {'name': name_elem.get_text(strip=True)}
                if code_elem:
                    item['code'] = code_elem.get_text(strip=True)
                results.append(item)

        # 去重 - 使用第一个非空值作为key
        seen = set()
        unique_results = []
        for r in results:
            # 使用任意非空的value作为key
            key = None
            for v in r.values():
                if v:
                    key = str(v)[:50]  # 截断避免过长
                    break
            if key and key not in seen:
                seen.add(key)
                unique_results.append(r)

        return unique_results

    def parse_product_list(self, html: str) -> List[Dict]:
        """解析金融产品列表页面"""
        if not html:
            return []

        results = []

        # 方法1: 表格解析
        selectors = ['table.product-list', 'table.fund-list', 'table.etf-list', 'table']
        table_data = self.parse_table(html, selectors)
        results.extend(table_data)

        if not HAS_BS4:
            return results

        # 方法2: 链接提取（基金代码常见格式）
        soup = BeautifulSoup(html, 'html.parser')
        links = soup.select('a[href]')
        for link in links:
            href = link.get('href', '')
            text = link.get_text(strip=True)
            code_match = re.search(r'/(\d{6})\.html', href)
            if code_match and text:
                results.append({
                    'code': code_match.group(1),
                    'name': text,
                    'url': href
                })

        # 去重
        seen = set()
        unique_results = []
        for r in results:
            code = r.get('code', '')
            if code and code not in seen:
                seen.add(code)
                unique_results.append(r)

        return unique_results

    def parse_any(self, html: str) -> Any:
        """通用解析入口"""
        if not html:
            return None

        # 尝试表格解析
        table_result = self.parse_table(html)
        if table_result:
            return table_result

        if not HAS_BS4:
            return None

        # 尝试列表解析
        soup = BeautifulSoup(html, 'html.parser')
        items = soup.select('li, div.item')
        if items:
            return [{'text': item.get_text(strip=True)} for item in items[:50]]

        return None


# 快捷函数
def parse_institutions(html: str) -> List[Dict]:
    """解析机构列表"""
    parser = AdaptivePageParser()
    return parser.parse_institution_list(html)


def parse_products(html: str) -> List[Dict]:
    """解析产品列表"""
    parser = AdaptivePageParser()
    return parser.parse_product_list(html)


def parse_page(html: str, page_type: str = 'auto') -> Any:
    """通用页面解析"""
    parser = AdaptivePageParser()
    if page_type == 'institution':
        return parser.parse_institution_list(html)
    elif page_type == 'product':
        return parser.parse_product_list(html)
    else:
        return parser.parse_any(html)


if __name__ == '__main__':
    # 测试
    test_html = '''
    <table class="institution-list">
        <tr><th>名称</th><th>代码</th><th>类型</th></tr>
        <tr><td>易方达基金</td><td>EF</td><td>基金管理公司</td></tr>
        <tr><td>中信证券</td><td>ZX</td><td>证券公司</td></tr>
    </table>
    '''

    parser = AdaptivePageParser()
    result = parser.parse_institution_list(test_html)
    print(f"解析结果: {len(result)} 条")
    for r in result:
        print(f"  {r}")
