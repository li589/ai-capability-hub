"""
定期报告观点采集脚本
从天天基金网爬取基金经理的投资观点和风格描述
"""
import akshare as ak
import requests
import json
import time
import re
from bs4 import BeautifulSoup
from datetime import datetime
import os

# 获取脚本所在目录的绝对路径
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(os.path.dirname(SCRIPT_DIR))
DATA_DIR = os.path.join(BASE_DIR, 'data')

class ReportCollector:
    """定期报告观点采集器"""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9'
        })

    def load_managers(self):
        """加载经理数据"""
        with open(f'{DATA_DIR}/fund_managers.json', 'r', encoding='utf-8') as f:
            return json.load(f)

    def save_managers(self, data):
        """保存经理数据"""
        with open(f'{DATA_DIR}/fund_managers.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def get_manager_reports(self, fund_code, limit=6):
        """获取基金经理报告列表"""
        reports = []

        try:
            df = ak.fund_announcement_report_em(symbol=fund_code)
            for _, row in df.head(limit).iterrows():
                reports.append({
                    'title': row.get('公告标题', ''),
                    'date': row.get('公告日期', ''),
                    'fund_name': row.get('基金名称', ''),
                    'report_id': row.get('报告ID', '')
                })
        except Exception as e:
            pass

        return reports

    def fetch_report_content(self, fund_code, report_title):
        """获取单份报告内容"""
        content = {
            'investment_views': [],
            'market_outlook': '',
            'strategy': ''
        }

        try:
            # 构造报告URL
            # 格式: https://fundf10.eastmoney.com/Benchmarks.aspx?type=1&code=000001
            # 或者从公告ID构造

            # 尝试直接搜索报告内容
            search_url = f"https://fundf10.eastmoney.com/f10/cls_{fund_code}.html"

            response = self.session.get(search_url, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')

            # 查找报告内容区域
            content_div = soup.find('div', class_='txt_content')
            if content_div:
                text = content_div.get_text(separator='\n', strip=True)

                # 提取投资观点
                view_match = re.search(r'管理人报告[：:]*([\s\S]*?)(?=重大\s*事项|$)', text)
                if view_match:
                    content['investment_views'] = self._extract_views(view_match.group(1))

                # 提取市场展望
                outlook_match = re.search(r'(?:后市\s*展望|市场\s*展望)[：:]*([\s\S]*?)(?=重大\s*事项|$)', text)
                if outlook_match:
                    content['market_outlook'] = outlook_match.group(1).strip()[:300]

        except Exception as e:
            pass

        return content

    def _extract_views(self, text, max_views=5):
        """提取关键观点"""
        sentences = re.split(r'[。；]', text)
        views = []

        for s in sentences:
            s = s.strip()
            if len(s) > 20 and not re.match(r'^[\d\s,.%]+$', s):
                # 排除纯数据行，保留有观点的句子
                keywords = ['认为', '看好', '配置', '投资', '机会', '风险', '策略', '市场', '关注']
                if any(kw in s for kw in keywords):
                    views.append(s)
            if len(views) >= max_views:
                break

        return views

    def get_fund_info(self, fund_code):
        """获取基金基本信息"""
        info = {
            'investment_goal': '',
            'investment_scope': '',
            'style_description': ''
        }

        try:
            # 从基金概况页面获取投资目标
            url = f"https://fund.eastmoney.com/fund/{fund_code}.html"
            response = self.session.get(url, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')

            text = soup.get_text()

            # 提取投资目标
            goal_match = re.search(r'投资目标[：:]\s*(.+?)(?:\n|；)', text)
            if goal_match:
                info['investment_goal'] = goal_match.group(1).strip()[:200]

            # 提取投资范围
            scope_match = re.search(r'投资范围[：:]\s*(.+?)(?:\n|；)', text)
            if scope_match:
                info['investment_scope'] = scope_match.group(1).strip()[:300]

            # 提取基金风格描述
            style_match = re.search(r'业绩比较基准[：:]\s*(.+?)(?:\n|；)', text)
            if style_match:
                info['style_description'] = style_match.group(1).strip()

        except Exception as e:
            pass

        return info

    def collect_reports_for_managers(self, managers, sample_size=500):
        """批量采集经理的报告观点"""
        print(f"开始采集 {sample_size} 位经理的报告观点...")

        updated_count = 0
        views_data = []

        for i, manager in enumerate(managers[:sample_size]):
            fund_code = str(manager.get('current_fund_code', ''))
            fund_name = manager.get('current_fund_name', '')
            manager_name = manager.get('name', '')

            if not fund_code or len(fund_code) < 6:
                continue

            # 获取基金基本信息
            fund_info = self.get_fund_info(fund_code)
            manager['investment_goal'] = fund_info.get('investment_goal', '')
            manager['investment_scope'] = fund_info.get('investment_scope', '')

            # 获取报告列表
            reports = self.get_manager_reports(fund_code, limit=4)

            manager_views = []
            for report in reports:
                # 获取报告内容
                content = self.fetch_report_content(fund_code, report.get('title', ''))
                if content.get('investment_views') or content.get('market_outlook'):
                    manager_views.append({
                        'report_date': report.get('date', ''),
                        'report_title': report.get('title', ''),
                        'views': content.get('investment_views', []),
                        'outlook': content.get('market_outlook', ''),
                        'strategy': content.get('strategy', '')
                    })

            if manager_views:
                manager['recent_views'] = manager_views
                updated_count += 1

                # 记录观点数据
                for view in manager_views:
                    views_data.append({
                        'manager_id': manager.get('manager_id'),
                        'manager_name': manager_name,
                        'company': manager.get('company_name'),
                        'fund_code': fund_code,
                        'fund_name': fund_name,
                        'report_date': view.get('report_date', ''),
                        'report_title': view.get('report_title', ''),
                        'views': ' '.join(view.get('views', [])),
                        'outlook': view.get('outlook', ''),
                        'strategy': view.get('strategy', '')
                    })

            if (i + 1) % 50 == 0:
                print(f"进度: {i+1}/{sample_size} (已更新{updated_count}个经理)")

            time.sleep(0.3)

        return updated_count, views_data

    def save_views_data(self, views_data):
        """保存观点数据"""
        views_file = os.path.join(DATA_DIR, 'manager_views.json')
        with open(views_file, 'w', encoding='utf-8') as f:
            json.dump({
                'views': views_data,
                'meta': {
                    'total_views': len(views_data),
                    'last_update': datetime.now().strftime('%Y-%m-%d'),
                    'source': '天天基金网'
                }
            }, f, ensure_ascii=False, indent=2)
        print(f"观点数据已保存: {views_file}")

def main():
    collector = ReportCollector()

    print("=" * 60)
    print("定期报告观点采集")
    print("=" * 60)

    # 加载经理数据
    data = collector.load_managers()
    managers = data.get('managers', [])
    print(f"共 {len(managers)} 个基金经理")

    # 采集报告观点
    updated_count, views_data = collector.collect_reports_for_managers(managers, sample_size=500)

    # 保存更新后的经理数据
    collector.save_managers(data)

    # 保存观点数据
    collector.save_views_data(views_data)

    print(f"\n采集完成!")
    print(f"更新经理数: {updated_count}")
    print(f"观点记录: {len(views_data)}")

if __name__ == "__main__":
    main()