"""
天天基金网数据采集脚本
从天天基金网采集基金经理、持仓等数据
"""
import urllib.request,urllib.error,urllib.parse
import json
import re
import time

import json,csv

try:
    from bs4 import BeautifulSoup
except ImportError:
    BeautifulSoup = None

#!/usr/bin/env python3
"""
天天基金网数据采集脚本
从天天基金网采集基金经理、持仓等数据
"""
import urllib.request, urllib.error, urllib.parse
import json
import re
import time

try:
    from bs4 import BeautifulSoup
except ImportError:
    BeautifulSoup = None


class EastMoneyCollector:
    """天天基金数据采集器"""

    def __init__(self, timeout=30, max_retries=3):
        self.base_url = "https://fund.eastmoney.com"
        self._headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': 'https://fund.eastmoney.com/',
            'Accept': 'text/html,application/json,*/*',
        }
        self._timeout = timeout
        self._max_retries = max_retries

    def _http_get(self, url, timeout=None):
        """带指数退避重试的 HTTP GET"""
        t = timeout or self._timeout
        for attempt in range(self._max_retries):
            try:
                req = urllib.request.Request(url, headers=self._headers)
                with urllib.request.urlopen(req, timeout=t) as resp:
                    return resp.read().decode('utf-8', errors='replace')
            except Exception as e:
                if attempt == self._max_retries - 1:
                    raise
                time.sleep(2 ** attempt)
        return ''

    def get_all_managers(self, fund_type='all', page=1, page_size=50):
        """
        获取基金经理列表

        参数:
            fund_type: all/gp/hh/zq/sy (全部/股票/混合/债券/收益)
            page: 页码
            page_size: 每页数量
        """
        params = {
            'dt': '14', 'ft': fund_type,
            'pn': page_size, 'pi': page,
            'sc': 'abbname', 'st': 'asc',
            'mc': 'returnjson'
        }
        query_string = urllib.parse.urlencode(params)
        url = f"https://fund.eastmoney.com/Data/FundDataPortfolio_Interface.aspx?{query_string}"

        try:
            text = self._http_get(url, timeout=25)
            match = re.search(r'returnjson\s*=\s*(\{.*?\});', text, re.DOTALL)
            if match:
                data = json.loads(match.group(1))
                return self._parse_manager_list(data)
        except Exception as e:
            print(f"[ERROR] 获取经理列表失败 (fund_type={fund_type}, page={page}): {e}")

        return []

    def _parse_manager_list(self, data):
        """解析经理列表数据"""
        managers = []
        try:
            items = data.get('data', []) or data.get('list', [])
            for item in items:
                manager = {
                    'manager_id': str(item.get('id', '')),
                    'name': item.get('name', ''),
                    'company_id': item.get('companyid', ''),
                    'company_name': item.get('company', ''),
                    'fund_count': item.get('fundcount', 0),
                    'total_scale': item.get('totalscale', 0),
                    'incept_date': item.get('incepdate', '')
                }
                managers.append(manager)
        except Exception as e:
            print(f"[ERROR] 解析经理数据失败: {e}")

        return managers

    def get_manager_detail(self, manager_id):
        """
        获取基金经理详情

        参数:
            manager_id: 经理代码
        """
        if BeautifulSoup is None:
            return {}

        url = f"https://fund.eastmoney.com/manager/{manager_id}.html"
        try:
            html = self._http_get(url)
            soup = BeautifulSoup(html, 'html.parser')

            detail = {}
            name_elem = soup.find('div', class_='name')
            if name_elem:
                detail['name'] = name_elem.get_text().strip()

            info_box = soup.find('div', class_='info-box')
            if info_box:
                for li in info_box.find_all('li'):
                    text = li.get_text()
                    if '管理规模' in text:
                        m = re.search(r'[\d.]+', text)
                        if m:
                            detail['scale'] = m.group()
                    elif '任职时间' in text:
                        m = re.search(r'\d+年', text)
                        if m:
                            detail['tenure'] = m.group()

            fund_table = soup.find('table', class_='fund-table')
            if fund_table:
                funds = []
                for row in fund_table.find_all('tr')[1:]:
                    cols = row.find_all('td')
                    if len(cols) >= 5:
                        fund = {
                            'code': cols[0].get_text().strip(),
                            'name': cols[1].get_text().strip(),
                            'type': cols[2].get_text().strip(),
                            'scale': cols[3].get_text().strip(),
                            'tenure': cols[4].get_text().strip()
                        }
                        funds.append(fund)
                detail['fund_list'] = funds

            return detail
        except Exception as e:
            print(f"[ERROR] 获取经理详情失败 ({manager_id}): {e}")
            return {}

    def get_fund_holdings(self, fund_code):
        """
        获取基金持仓数据（十大股票、十大债券）
        """
        url = f"https://fund.eastmoney.com/pingzhongdata/{fund_code}.js"
        try:
            text = self._http_get(url)
            holdings = {}

            stock_match = re.search(r'stockCodes\s*=\s*\[(.*?)\]', text)
            if stock_match:
                codes = re.findall(r'["\'](\d+)["\']', stock_match.group(1))
                holdings['stock_codes'] = codes

            bond_match = re.search(r'zqCodes\s*=\s*["\'](.*?)["\']', text)
            if bond_match:
                codes = bond_match.group(1).split(',')
                holdings['bond_codes'] = [c.strip() for c in codes if c.strip()]

            return holdings
        except Exception as e:
            print(f"[ERROR] 获取持仓失败 ({fund_code}): {e}")
            return {}

    def get_fund_info(self, fund_code):
        """获取基金基本信息"""
        url = f"https://fund.eastmoney.com/pingzhongdata/{fund_code}.js"
        try:
            text = self._http_get(url)
            info = {'code': fund_code}

            name_match = re.search(r"fS_name\s*=\s*[\"'](.*?)[\"']", text)
            if name_match:
                info['name'] = name_match.group(1)

            for period in ['1n', '6y', '3y', '1y', '1m']:
                match = re.search(rf"syl_{period}\s*=\s*[\"']?([\d.]+)[\"']?", text)
                if match:
                    info[f'return_{period}'] = float(match.group(1))

            return info
        except Exception as e:
            print(f"[ERROR] 获取基金信息失败 ({fund_code}): {e}")
            return {}

    def save_managers(self, managers, filepath):
        """保存经理数据到JSON文件"""
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump({
                'managers': managers,
                'meta': {
                    'total_count': len(managers),
                    'last_update': time.strftime('%Y-%m-%d'),
                    'source': '天天基金网'
                }
            }, f, ensure_ascii=False, indent=2)


def main():
    collector = EastMoneyCollector()

    print("正在采集基金经理列表...")
    all_managers = []
    for fund_type in ['all', 'gp', 'hh', 'zq', 'sy']:
        managers = collector.get_all_managers(fund_type=fund_type, page=1)
        all_managers.extend(managers)
        print(f"  {fund_type}: 获取 {len(managers)} 位经理")
        time.sleep(1)

    # 去重
    seen = set()
    unique_managers = []
    for m in all_managers:
        if m['manager_id'] not in seen:
            seen.add(m['manager_id'])
            unique_managers.append(m)

    print(f"\n共获取 {len(unique_managers)} 位基金经理")

    if unique_managers:
        collector.save_managers(unique_managers, '../data/fund_managers.json')
        print("数据已保存到 ../data/fund_managers.json")


if __name__ == "__main__":
    main()
