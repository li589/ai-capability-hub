"""
基金业协会数据采集脚本
从基金业协会官网采集公募基金管理人信息
"""
import requests
import json
import re
import time
from bs4 import BeautifulSoup

class AMACCollector:
    """基金业协会数据采集器"""

    def __init__(self):
        self.base_url = "https://www.amac.org.cn"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9'
        })

    def get_public_fund_companies(self):
        """
        获取公募基金管理人名单
        基金业协会官网的私募基金管理人页面包含公私募信息
        """
        companies = []

        # 尝试从天天基金网获取更全的基金公司数据（备用方案）
        try:
            return self._get_from_eastmoney()
        except Exception as e:
            print(f"天天基金数据获取失败: {e}")

        # 基金业协会官方渠道
        url = "https://gs.amac.org.cn/amac-infodisc/res/pof/manager/managerList.html"

        try:
            response = self.session.get(url, timeout=30)
            soup = BeautifulSoup(response.text, 'html.parser')

            # 查找基金公司表格
            table = soup.find('table', class_='table')
            if table:
                rows = table.find_all('tr')[1:]  # 跳过表头
                for row in rows:
                    cols = row.find_all('td')
                    if len(cols) >= 4:
                        company = {
                            'company_id': self._generate_company_id(cols[0].get_text()),
                            'name': cols[0].get_text().strip(),
                            'type': '公募',
                            'reg_date': cols[1].get_text().strip(),
                            'address': cols[2].get_text().strip()
                        }
                        companies.append(company)

        except Exception as e:
            print(f"基金业协会数据获取失败: {e}")

        return companies

    def _get_from_eastmoney(self):
        """
        从天天基金网获取基金公司数据作为主要来源
        基金业协会数据更新不及时，天天基金更全面
        """
        companies = []
        page = 1
        has_more = True

        while has_more:
            url = f"https://fund.eastmoney.com/company/default.html"
            response = self.session.get(url, timeout=30)
            soup = BeautifulSoup(response.text, 'html.parser')

            # 查找公司列表
            company_list = soup.find_all('div', class_='company-item')
            if not company_list:
                company_list = soup.find_all('tr', class_='tr')

            if not company_list:
                break

            for item in company_list:
                name_elem = item.find('a') or item.find('td', class_='name')
                if name_elem:
                    name = name_elem.get_text().strip()

                    scale_elem = item.find('span', class_='scale') or item.find('td', class_='scale')
                    scale = scale_elem.get_text().strip() if scale_elem else 'N/A'

                    companies.append({
                        'company_id': self._generate_company_id(name),
                        'name': name,
                        'type': '公募',
                        'scale': scale,
                        'source': '天天基金'
                    })

            # 检查是否有更多页
            next_page = soup.find('a', class_='next')
            if next_page:
                page += 1
            else:
                has_more = False

        return companies

    def _generate_company_id(self, name):
        """生成公司ID（取首字母缩写）"""
        import hashlib
        return f"C{hashlib.md5(name.encode()).hexdigest()[:6].upper()}"

    def get_manager_info_by_amac(self, company_name):
        """
        通过基金业协会查询某公司下的基金经理
        """
        url = f"https://gs.amac.org.cn/amac-infodisc/api/pof/manager"

        data = {
            "keyword": company_name,
            "primaryInvestType": "私募证券投资基金管理人",
            "page": 0,
            "size": 20
        }

        try:
            response = self.session.post(
                url,
                json=data,
                headers={'Content-Type': 'application/json'},
                timeout=30
            )
            result = response.json()
            return result.get('content', [])
        except Exception as e:
            print(f"查询失败: {e}")
            return []

    def save_companies(self, companies, filepath):
        """保存公司数据到JSON文件"""
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump({'companies': companies, 'meta': {
                'total_count': len(companies),
                'last_update': time.strftime('%Y-%m-%d'),
                'source': '基金业协会/天天基金'
            }}, f, ensure_ascii=False, indent=2)

def main():
    collector = AMACCollector()

    print("正在采集基金公司数据...")
    companies = collector.get_public_fund_companies()

    if companies:
        print(f"共获取 {len(companies)} 家基金公司")
        collector.save_companies(companies, '../data/fund_companies.json')
        print("数据已保存到 ../data/fund_companies.json")
    else:
        print("未能获取数据，请检查网络连接")

if __name__ == "__main__":
    main()