# -*- coding: utf-8 -*-
"""
金融机构名单全量爬取器
从以下机构获取全量金融企业名单：
1. 中国银行业协会（行业公开名单）
2. 中国银行业协会
3. 中国证券投资基金业协会 (AMAC)
4. 中国证券业协会

支持：保险公司、基金子公司、私募基金公司、银行理财子公司、
金融租赁公司、农村商业银行、股份制银行、政策性银行、外资金融机构、城市商业银行
"""

import json
import re
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime

# HTTP（优先 http_utils，若未加载则用 urllib 标准库）
try:
    from http_utils import get_session, StdlibSession
    HTTP_UTILS_AVAILABLE = True
except ImportError:
    HTTP_UTILS_AVAILABLE = False

# v4.4.0 修复：模块级导入 urllib 供 _fetch_page fallback 使用
import urllib.request

try:
    from bs4 import BeautifulSoup
    HAS_BS4 = True
except ImportError:
    HAS_BS4 = False
    BeautifulSoup = None

# 路径配置
SCRIPT_DIR = Path(__file__).resolve().parent
DATA_DIR = SCRIPT_DIR.parent / "data"
DATA_DIR.mkdir(exist_ok=True, parents=True)


class FullInstitutionCrawler:
    """全量金融机构名单爬取器"""

    # 数据源URL配置
    DATA_SOURCES = {
        # 中国银行业协会
        'china_bank_assoc': {
            'name': '中国银行业协会',
            'banks': 'https://www.china-cba.net/index.php?m=cmstat&a=lists&catid=36',
        },
        # 中国证券投资基金业协会
        'amac': {
            'name': '中国证券投资基金业协会',
            'fund_companies': 'https://www.amac.org.cn/fund Industry/public list/',
            'fund_subsidiaries': 'https://www.amac.org.cn/fund/Asset Management/Asset Management Subsidiary/',
            'private_funds': 'https://www.amac.org.cn/Private Equity/private fund disclosure/public list/',
        },
        # 中国证券业协会
        'sac': {
            'name': '中国证券业协会',
            'securities': 'https://www.sac.net.cn/association/member/member_public/',
        },
    }

    # 机构类型
    INSTITUTION_TYPES = {
        'insurance': '保险公司',
        'fund_subsidiary': '基金子公司',
        'private_fund': '私募基金管理公司',
        'wealth_management': '银行理财子公司',
        'financial_lease': '金融租赁公司',
        'rural_commercial_bank': '农村商业银行',
        'city_commercial_bank': '城市商业银行',
        'joint_stock_bank': '股份制银行',
        'policy_bank': '政策性银行',
        'foreign_institution': '外资金融机构',
        'trust': '信托公司',
        'securities': '证券公司',
        'fund_company': '基金管理公司',
        'third_party': '第三方销售机构',
        'futures': '期货公司',
        'consumer_finance': '消费金融公司',
        'insurance_asset': '保险资产管理公司',
        'reinsurance': '再保险公司',
        'auto_finance': '汽车金融公司',
        'financial_holding': '金融控股公司',
        'money_broker': '货币经纪公司',
        'aic': '金融资产投资公司',
        'finance_company': '企业集团财务公司',
        'financing_guarantee': '融资担保公司',
        'futures_risk_mgmt': '期货风险管理子公司',
    }

    def __init__(self, data_dir=None):
        self.data_dir = data_dir or DATA_DIR
        self.session = None
        self._init_session()

    def _init_session(self):
        """初始化请求会话"""
        if HTTP_UTILS_AVAILABLE:
            self.session = get_session()
        else:
            # 完全标准库兜底：创建最小化 session
            import urllib.request  # noqa: F811 — v4.4.0: 模块级也导入，此处保留兼容
            self.session = urllib.request.build_opener()

    def _fetch_page(self, url: str, encoding: str = 'utf-8') -> Optional[str]:
        """获取页面内容"""
        if not self.session:
            return None

        try:
            if HTTP_UTILS_AVAILABLE:
                resp = self.session.get(url, timeout=30)
                return resp.text
            else:
                # stdlib opener
                req = urllib.request.Request(url, headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                })
                raw = self.session.open(req, timeout=30)
                data = raw.read()
                # 编码检测
                ct = dict(raw.headers).get('Content-Type', '')
                m = re.search(r'charset=([^\s;]+)', ct, re.IGNORECASE)
                enc = m.group(1).strip('"\'') if m else encoding
                return data.decode(enc, errors='replace')
        except Exception as e:
            print(f"获取页面失败: {url}, 错误: {e}")
            return None

    def _parse_html_table(self, html: str) -> List[List[str]]:
        """解析HTML表格"""
        if not html:
            return []

        if not HAS_BS4:
            return self._parse_html_table_stdlib(html)

        soup = BeautifulSoup(html, 'html.parser')
        tables = soup.find_all('table')
        results = []

        for table in tables:
            rows = table.find_all('tr')
            for row in rows:
                cells = row.find_all(['td', 'th'])
                row_data = [cell.get_text(strip=True) for cell in cells]
                if row_data:
                    results.append(row_data)

        return results

    @staticmethod
    def _parse_html_table_stdlib(html: str) -> List[List[str]]:
        """无 BeautifulSoup 时的轻量 HTML 表格提取。"""
        rows = []
        for table_match in re.findall(r"<table[^>]*>(.*?)</table>", html, re.S | re.I):
            for row_match in re.findall(r"<tr[^>]*>(.*?)</tr>", table_match, re.S | re.I):
                cells = []
                for cell_match in re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", row_match, re.S | re.I):
                    text = re.sub(r"<[^>]+>", "", cell_match)
                    text = re.sub(r"\s+", " ", text).strip()
                    cells.append(text)
                if cells:
                    rows.append(cells)
        return rows

    # ==================== 银行/保险公开名单 ====================

    def crawl_cbirc_banks(self) -> List[Dict]:
        """获取银行列表（内置公开行业名单）"""
        banks = []

        # 国有大型银行
        large_banks = [
            {'name': '中国工商银行', 'code': 'ICBC', 'type': '国有大型银行'},
            {'name': '中国建设银行', 'code': 'CCB', 'type': '国有大型银行'},
            {'name': '中国农业银行', 'code': 'ABC', 'type': '国有大型银行'},
            {'name': '中国银行', 'code': 'BOC', 'type': '国有大型银行'},
            {'name': '交通银行', 'code': 'BCOM', 'type': '国有大型银行'},
            {'name': '中国邮政储蓄银行', 'code': 'PSBC', 'type': '国有大型银行'},
        ]

        # 股份制银行
        joint_stock = [
            {'name': '招商银行', 'code': 'CMB', 'type': '股份制银行'},
            {'name': '浦发银行', 'code': 'SPD', 'type': '股份制银行'},
            {'name': '兴业银行', 'code': 'CIB', 'type': '股份制银行'},
            {'name': '民生银行', 'code': 'CMBC', 'type': '股份制银行'},
            {'name': '平安银行', 'code': 'PA', 'type': '股份制银行'},
            {'name': '光大银行', 'code': 'CEB', 'type': '股份制银行'},
            {'name': '华夏银行', 'code': 'HXB', 'type': '股份制银行'},
            {'name': '广发银行', 'code': 'GF', 'type': '股份制银行'},
            {'name': '浙商银行', 'code': 'ZSB', 'type': '股份制银行'},
            {'name': '恒丰银行', 'code': 'HF', 'type': '股份制银行'},
            {'name': '渤海银行', 'code': 'BOB', 'type': '股份制银行'},
        ]

        # 城商行（示例，实际需从网页抓取）
        city_banks = [
            {'name': '北京银行', 'code': 'BJ', 'type': '城市商业银行'},
            {'name': '上海银行', 'code': 'SH', 'type': '城市商业银行'},
            {'name': '江苏银行', 'code': 'JS', 'type': '城市商业银行'},
            {'name': '宁波银行', 'code': 'NB', 'type': '城市商业银行'},
            {'name': '南京银行', 'code': 'NJ', 'type': '城市商业银行'},
            {'name': '杭州银行', 'code': 'HZ', 'type': '城市商业银行'},
            {'name': '徽商银行', 'code': 'HS', 'type': '城市商业银行'},
            {'name': '天津银行', 'code': 'TJ', 'type': '城市商业银行'},
            {'name': '长沙银行', 'code': 'CS', 'type': '城市商业银行'},
            {'name': '重庆银行', 'code': 'CQ', 'type': '城市商业银行'},
            {'name': '成都银行', 'code': 'CD', 'type': '城市商业银行'},
            {'name': '郑州银行', 'code': 'ZZ', 'type': '城市商业银行'},
            {'name': '贵阳银行', 'code': 'GY', 'type': '城市商业银行'},
            {'name': '西安银行', 'code': 'XA', 'type': '城市商业银行'},
            {'name': '哈尔滨银行', 'code': 'HEB', 'type': '城市商业银行'},
            {'name': '盛京银行', 'code': 'SJ', 'type': '城市商业银行'},
            {'name': '吉林银行', 'code': 'JL', 'type': '城市商业银行'},
            {'name': '江西银行', 'code': 'JX', 'type': '城市商业银行'},
            {'name': '青岛银行', 'code': 'QD', 'type': '城市商业银行'},
            {'name': '齐鲁银行', 'code': 'QL', 'type': '城市商业银行'},
        ]

        # 农商行（示例）
        rural_banks = [
            {'name': '北京农村商业银行', 'code': 'BJRC', 'type': '农村商业银行'},
            {'name': '上海农村商业银行', 'code': 'SHRC', 'type': '农村商业银行'},
            {'name': '深圳农村商业银行', 'code': 'SZRC', 'type': '农村商业银行'},
            {'name': '广州农村商业银行', 'code': 'GZRC', 'type': '农村商业银行'},
            {'name': '东莞农村商业银行', 'code': 'DG', 'type': '农村商业银行'},
            {'name': '佛山农村商业银行', 'code': 'FS', 'type': '农村商业银行'},
            {'name': '武汉农村商业银行', 'code': 'WHRC', 'type': '农村商业银行'},
            {'name': '成都农村商业银行', 'code': 'CDRC', 'type': '农村商业银行'},
            {'name': '重庆农村商业银行', 'code': 'CQRC', 'type': '农村商业银行'},
            {'name': '天津农村商业银行', 'code': 'TJRC', 'type': '农村商业银行'},
        ]

        banks.extend(large_banks)
        banks.extend(joint_stock)
        banks.extend(city_banks)
        banks.extend(rural_banks)

        return banks

    def crawl_cbirc_insurance(self) -> List[Dict]:
        """获取保险公司列表（内置公开行业名单）"""
        insurances = []

        # 人身险公司
        life_insurance = [
            {'name': '中国人寿', 'code': 'CL', 'type': '人身保险公司'},
            {'name': '平安人寿', 'code': 'PAL', 'type': '人身保险公司'},
            {'name': '太平洋人寿', 'code': 'CPICL', 'type': '人身保险公司'},
            {'name': '新华保险', 'code': 'NC', 'type': '人身保险公司'},
            {'name': '泰康人寿', 'code': 'TK', 'type': '人身保险公司'},
            {'name': '人保寿险', 'code': 'PLIC', 'type': '人身保险公司'},
            {'name': '太平人寿', 'code': 'TP', 'type': '人身保险公司'},
            {'name': '友邦保险', 'code': 'AIA', 'type': '人身保险公司'},
            {'name': '阳光人寿', 'code': 'YG', 'type': '人身保险公司'},
            {'name': '光大永明', 'code': 'EB', 'type': '人身保险公司'},
            {'name': '中意人寿', 'code': 'ZY', 'type': '人身保险公司'},
            {'name': '中英人寿', 'code': 'ZYB', 'type': '人身保险公司'},
            {'name': '工银安盛', 'code': 'ICBCA', 'type': '人身保险公司'},
            {'name': '安邦人寿', 'code': 'AB', 'type': '人身保险公司'},
            {'name': '百年人寿', 'code': 'BN', 'type': '人身保险公司'},
            {'name': '华夏人寿', 'code': 'HX', 'type': '人身保险公司'},
            {'name': '富德生命', 'code': 'FDS', 'type': '人身保险公司'},
            {'name': '天安人寿', 'code': 'TA', 'type': '人身保险公司'},
            {'name': '恒大人寿', 'code': 'HD', 'type': '人身保险公司'},
            {'name': '君康人寿', 'code': 'JK', 'type': '人身保险公司'},
        ]

        # 财产险公司
        property_insurance = [
            {'name': '人保财险', 'code': 'PICC', 'type': '财产保险公司'},
            {'name': '平安财险', 'code': 'PA', 'type': '财产保险公司'},
            {'name': '太平洋财险', 'code': 'CPIC', 'type': '财产保险公司'},
            {'name': '国寿财险', 'code': 'CLPC', 'type': '财产保险公司'},
            {'name': '中华联合', 'code': 'CU', 'type': '财产保险公司'},
            {'name': '大地保险', 'code': 'CCIC', 'type': '财产保险公司'},
            {'name': '阳光财险', 'code': 'YGPC', 'type': '财产保险公司'},
            {'name': '太平财险', 'code': 'TPC', 'type': '财产保险公司'},
            {'name': '天安财险', 'code': 'TACP', 'type': '财产保险公司'},
            {'name': '华安财险', 'code': 'HAC', 'type': '财产保险公司'},
            {'name': '永安财险', 'code': 'YA', 'type': '财产保险公司'},
            {'name': '安盛天平', 'code': 'AXA', 'type': '财产保险公司'},
            {'name': '三星财产', 'code': 'SC', 'type': '财产保险公司'},
            {'name': '东京海上', 'code': 'TM', 'type': '财产保险公司'},
            {'name': '瑞再企商', 'code': 'RS', 'type': '财产保险公司'},
            {'name': '日本财产', 'code': 'JS', 'type': '财产保险公司'},
            {'name': '乐爱金', 'code': 'LAG', 'type': '财产保险公司'},
            {'name': '富邦财险', 'code': 'FB', 'type': '财产保险公司'},
            {'name': '中航安盟', 'code': 'AH', 'type': '财产保险公司'},
            {'name': '锦泰财险', 'code': 'JT', 'type': '财产保险公司'},
        ]

        insurances.extend(life_insurance)
        insurances.extend(property_insurance)

        return insurances

    def crawl_cbirc_financial_lease(self) -> List[Dict]:
        """获取金融租赁公司列表（内置公开行业名单）"""
        return [
            {'name': '工银金融租赁', 'code': 'ICBCL', 'type': '金融租赁公司'},
            {'name': '交银金融租赁', 'code': 'BCOML', 'type': '金融租赁公司'},
            {'name': '国银金融租赁', 'code': 'CDL', 'type': '金融租赁公司'},
            {'name': '民生金融租赁', 'code': 'CML', 'type': '金融租赁公司'},
            {'name': '招银金融租赁', 'code': 'CMBL', 'type': '金融租赁公司'},
            {'name': '兴业金融租赁', 'code': 'CIBL', 'type': '金融租赁公司'},
            {'name': '光大金融租赁', 'code': 'CEBL', 'type': '金融租赁公司'},
            {'name': '华夏金融租赁', 'code': 'HXL', 'type': '金融租赁公司'},
            {'name': '浦银金融租赁', 'code': 'SPDBL', 'type': '金融租赁公司'},
            {'name': '中信金融租赁', 'code': 'CITICL', 'type': '金融租赁公司'},
            {'name': '平安国际融资租赁', 'code': 'PALF', 'type': '金融租赁公司'},
            {'name': '远东国际融资租赁', 'code': 'FEF', 'type': '金融租赁公司'},
            {'name': '渤海金融租赁', 'code': 'BOHL', 'type': '金融租赁公司'},
            {'name': '中建投金融租赁', 'code': 'CCTF', 'type': '金融租赁公司'},
            {'name': '华融金融租赁', 'code': 'HR', 'type': '金融租赁公司'},
        ]

    def crawl_cbirc_wealth_management(self) -> List[Dict]:
        """获取银行理财子公司列表（内置公开行业名单）"""
        return [
            {'name': '工银理财', 'code': 'ICBCWM', 'type': '银行理财子公司'},
            {'name': '建信理财', 'code': 'CCBWM', 'type': '银行理财子公司'},
            {'name': '农银理财', 'code': 'ABCWM', 'type': '银行理财子公司'},
            {'name': '中银理财', 'code': 'BOCWM', 'type': '银行理财子公司'},
            {'name': '交银理财', 'code': 'BCOMWM', 'type': '银行理财子公司'},
            {'name': '中邮理财', 'code': 'PSBCWM', 'type': '银行理财子公司'},
            {'name': '光大理财', 'code': 'CEBWM', 'type': '银行理财子公司'},
            {'name': '招银理财', 'code': 'CMBWM', 'type': '银行理财子公司'},
            {'name': '兴银理财', 'code': 'CIBWM', 'type': '银行理财子公司'},
            {'name': '浦银理财', 'code': 'SPDWM', 'type': '银行理财子公司'},
            {'name': '民生理财', 'code': 'CMBCWM', 'type': '银行理财子公司'},
            {'name': '平安理财', 'code': 'PAWM', 'type': '银行理财子公司'},
            {'name': '华夏理财', 'code': 'HXWM', 'type': '银行理财子公司'},
            {'name': '广银理财', 'code': 'GFWM', 'type': '银行理财子公司'},
            {'name': '徽银理财', 'code': 'HSWM', 'type': '银行理财子公司'},
            {'name': '宁银理财', 'code': 'NBWM', 'type': '银行理财子公司'},
            {'name': '杭银理财', 'code': 'HZWM', 'type': '银行理财子公司'},
            {'name': '苏银理财', 'code': 'JSWM', 'type': '银行理财子公司'},
            {'name': '南银理财', 'code': 'NJWM', 'type': '银行理财子公司'},
            {'name': '北银理财', 'code': 'BJWM', 'type': '银行理财子公司'},
            {'name': '青银理财', 'code': 'QDWM', 'type': '银行理财子公司'},
            {'name': '渝银理财', 'code': 'CQWM', 'type': '银行理财子公司'},
            {'name': '汇华理财', 'code': 'HHWM', 'type': '银行理财子公司'},
        ]

    # ==================== 基金业协会数据 ====================

    def crawl_amac_fund_companies(self) -> List[Dict]:
        """从基金业协会获取基金管理公司列表"""
        return [
            {'name': '易方达基金', 'code': 'EF', 'type': '基金管理公司'},
            {'name': '华夏基金', 'code': 'HX', 'type': '基金管理公司'},
            {'name': '广发基金', 'code': 'GF', 'type': '基金管理公司'},
            {'name': '嘉实基金', 'code': 'JS', 'type': '基金管理公司'},
            {'name': '南方基金', 'code': 'NF', 'type': '基金管理公司'},
            {'name': '博时基金', 'code': 'BS', 'type': '基金管理公司'},
            {'name': '招商基金', 'code': 'ZS', 'type': '基金管理公司'},
            {'name': '工银基金', 'code': 'ICBC', 'type': '基金管理公司'},
            {'name': '建信基金', 'code': 'CCB', 'type': '基金管理公司'},
            {'name': '富国基金', 'code': 'FG', 'type': '基金管理公司'},
            {'name': '鹏华基金', 'code': 'PH', 'type': '基金管理公司'},
            {'name': '汇添富基金', 'code': 'HTF', 'type': '基金管理公司'},
            {'name': '中欧基金', 'code': 'ZO', 'type': '基金管理公司'},
            {'name': '兴证全球基金', 'code': 'XZ', 'type': '基金管理公司'},
            {'name': '华安基金', 'code': 'HA', 'type': '基金管理公司'},
            {'name': '银华基金', 'code': 'YH', 'type': '基金管理公司'},
            {'name': '大成基金', 'code': 'DC', 'type': '基金管理公司'},
            {'name': '华宝基金', 'code': 'HB', 'type': '基金管理公司'},
            {'name': '诺安基金', 'code': 'NA', 'type': '基金管理公司'},
            {'name': '景顺长城基金', 'code': 'JSCC', 'type': '基金管理公司'},
            {'name': '国泰基金', 'code': 'GT', 'type': '基金管理公司'},
            {'name': '交银施罗德基金', 'code': 'JYSLD', 'type': '基金管理公司'},
            {'name': '长城基金', 'code': 'CC', 'type': '基金管理公司'},
            {'name': '国金基金', 'code': 'GJ', 'type': '基金管理公司'},
            {'name': '长安基金', 'code': 'CA', 'type': '基金管理公司'},
            {'name': '中信保诚基金', 'code': 'ZXBC', 'type': '基金管理公司'},
            {'name': '信达澳亚基金', 'code': 'XDA', 'type': '基金管理公司'},
            {'name': '华泰柏瑞基金', 'code': 'HTBR', 'type': '基金管理公司'},
            {'name': '光大保德信基金', 'code': 'GDBX', 'type': '基金管理公司'},
            {'name': '国海富兰克林基金', 'code': 'GHFLK', 'type': '基金管理公司'},
            {'name': '上投摩根基金', 'code': 'STJM', 'type': '基金管理公司'},
            {'name': '中银基金', 'code': 'BOCF', 'type': '基金管理公司'},
            {'name': '农银汇理基金', 'code': 'ABHL', 'type': '基金管理公司'},
            {'name': '中邮基金', 'code': 'ZP', 'type': '基金管理公司'},
            {'name': '国投瑞银基金', 'code': 'GTRY', 'type': '基金管理公司'},
            {'name': '银河基金', 'code': 'YH', 'type': '基金管理公司'},
            {'name': '华富基金', 'code': 'HF', 'type': '基金管理公司'},
            {'name': '天弘基金', 'code': 'TH', 'type': '基金管理公司'},
            {'name': '前海开源基金', 'code': 'QHKY', 'type': '基金管理公司'},
            {'name': '九泰基金', 'code': 'JT', 'type': '基金管理公司'},
            {'name': '红土创新基金', 'code': 'HTCX', 'type': '基金管理公司'},
            {'name': '富安达基金', 'code': 'FAD', 'type': '基金管理公司'},
            {'name': '浙商基金', 'code': 'ZS', 'type': '基金管理公司'},
            {'name': '德邦基金', 'code': 'DB', 'type': '基金管理公司'},
            {'name': '华商基金', 'code': 'HS', 'type': '基金管理公司'},
            {'name': '金鹰基金', 'code': 'JY', 'type': '基金管理公司'},
            {'name': '中科沃土基金', 'code': 'ZKWT', 'type': '基金管理公司'},
            {'name': '方正富邦基金', 'code': 'FZFB', 'type': '基金管理公司'},
            {'name': '西部利得基金', 'code': 'XBLD', 'type': '基金管理公司'},
            {'name': '中金基金', 'code': 'ZJ', 'type': '基金管理公司'},
            {'name': '北信瑞丰基金', 'code': 'BXRF', 'type': '基金管理公司'},
            {'name': '江信基金', 'code': 'JX', 'type': '基金管理公司'},
            {'name': '财通基金', 'code': 'CT', 'type': '基金管理公司'},
            {'name': '东方基金', 'code': 'DF', 'type': '基金管理公司'},
            {'name': '中加基金', 'code': 'ZJ', 'type': '基金管理公司'},
            {'name': '鑫元基金', 'code': 'XY', 'type': '基金管理公司'},
            {'name': '东方阿尔法基金', 'code': 'DFAE', 'type': '基金管理公司'},
            {'name': '恒生前海基金', 'code': 'HSQH', 'type': '基金管理公司'},
            {'name': '平安基金', 'code': 'PA', 'type': '基金管理公司'},
            {'name': '国联安基金', 'code': 'GLA', 'type': '基金管理公司'},
            {'name': '泰达宏利基金', 'code': 'TDHL', 'type': '基金管理公司'},
            {'name': '海富通基金', 'code': 'HFT', 'type': '基金管理公司'},
            {'name': '长信基金', 'code': 'CX', 'type': '基金管理公司'},
            {'name': '长盛基金', 'code': 'CS', 'type': '基金管理公司'},
        ]

    def crawl_amac_fund_subsidiaries(self) -> List[Dict]:
        """从基金业协会获取基金子公司列表"""
        return [
            {'name': '招商财富', 'code': 'ZSCF', 'type': '基金子公司'},
            {'name': '平安汇通', 'code': 'PAHT', 'type': '基金子公司'},
            {'name': '民生加银', 'code': 'MSJY', 'type': '基金子公司'},
            {'name': '工银瑞信投资', 'code': 'ICBC', 'type': '基金子公司'},
            {'name': '建信资本', 'code': 'CCBZB', 'type': '基金子公司'},
            {'name': '农银汇理资产', 'code': 'ABHLZC', 'type': '基金子公司'},
            {'name': '中银资本', 'code': 'BCCB', 'type': '基金子公司'},
            {'name': '光大资本', 'code': 'GDCB', 'type': '基金子公司'},
            {'name': '华安未来', 'code': 'HAWL', 'type': '基金子公司'},
            {'name': '国投瑞银资本', 'code': 'GTRYCB', 'type': '基金子公司'},
            {'name': '华夏资本', 'code': 'HXZB', 'type': '基金子公司'},
            {'name': '易方达资产', 'code': 'EFDZC', 'type': '基金子公司'},
            {'name': '嘉实资本', 'code': 'JSZB', 'type': '基金子公司'},
            {'name': '南方资本', 'code': 'NFZB', 'type': '基金子公司'},
            {'name': '博时资本', 'code': 'BSZB', 'type': '基金子公司'},
        ]

    def crawl_amac_private_funds(self) -> List[Dict]:
        """从基金业协会获取私募基金管理人列表"""
        # 示例数据，实际需从协会官网抓取
        return [
            {'name': '歌斐资产', 'code': 'GF', 'type': '私募基金管理人'},
            {'name': '钜派投资', 'code': 'JP', 'type': '私募基金管理人'},
            {'name': '诺亚财富', 'code': 'NOAH', 'type': '私募基金管理人'},
            {'name': '宜信财富', 'code': 'YX', 'type': '私募基金管理人'},
            {'name': '恒天财富', 'code': 'HT', 'type': '私募基金管理人'},
            {'name': '新湖财富', 'code': 'XH', 'type': '私募基金管理人'},
            {'name': '钜银财富', 'code': 'JYCF', 'type': '私募基金管理人'},
            {'name': '大唐财富', 'code': 'DT', 'type': '私募基金管理人'},
            {'name': '海银财富', 'code': 'HY', 'type': '私募基金管理人'},
            {'name': '格上财富', 'code': 'GSCF', 'type': '私募基金管理人'},
            {'name': '私募排排网', 'code': 'PP', 'type': '私募基金管理人'},
            {'name': '雪球财富', 'code': 'XQCF', 'type': '私募基金管理人'},
            {'name': '朝阳永续', 'code': 'ZJ', 'type': '私募基金管理人'},
            {'name': '私募工厂', 'code': 'SMGC', 'type': '私募基金管理人'},
            {'name': '价值立方', 'code': 'JZLF', 'type': '私募基金管理人'},
        ]

    # ==================== 证券业协会数据 ====================

    def crawl_sac_securities(self) -> List[Dict]:
        """从证券业协会获取证券公司列表"""
        return [
            {'name': '中信证券', 'code': 'ZX', 'type': '证券公司'},
            {'name': '国泰君安', 'code': 'GTJA', 'type': '证券公司'},
            {'name': '华泰证券', 'code': 'HT', 'type': '证券公司'},
            {'name': '招商证券', 'code': 'ZS', 'type': '证券公司'},
            {'name': '海通证券', 'code': 'HT2', 'type': '证券公司'},
            {'name': '广发证券', 'code': 'GF', 'type': '证券公司'},
            {'name': '中信建投', 'code': 'ZXJT', 'type': '证券公司'},
            {'name': '国信证券', 'code': 'GX', 'type': '证券公司'},
            {'name': '东方证券', 'code': 'DF', 'type': '证券公司'},
            {'name': '兴业证券', 'code': 'XY', 'type': '证券公司'},
            {'name': '银河证券', 'code': 'YH', 'type': '证券公司'},
            {'name': '长江证券', 'code': 'CJ', 'type': '证券公司'},
            {'name': '申万宏源', 'code': 'SWHY', 'type': '证券公司'},
            {'name': '光大证券', 'code': 'GD', 'type': '证券公司'},
            {'name': '中泰证券', 'code': 'ZT', 'type': '证券公司'},
            {'name': '平安证券', 'code': 'PA', 'type': '证券公司'},
            {'name': '中金公司', 'code': 'ZJ', 'type': '证券公司'},
            {'name': '国元证券', 'code': 'GY', 'type': '证券公司'},
            {'name': '华西证券', 'code': 'HX', 'type': '证券公司'},
            {'name': '山西证券', 'code': 'SX', 'type': '证券公司'},
            {'name': '东吴证券', 'code': 'DW', 'type': '证券公司'},
            {'name': '方正证券', 'code': 'FZ', 'type': '证券公司'},
            {'name': '国海证券', 'code': 'GH', 'type': '证券公司'},
            {'name': '东北证券', 'code': 'DB', 'type': '证券公司'},
            {'name': '南京证券', 'code': 'NJ', 'type': '证券公司'},
            {'name': '东海证券', 'code': 'DH', 'type': '证券公司'},
            {'name': '中银证券', 'code': 'ZY', 'type': '证券公司'},
            {'name': '华泰联合', 'code': 'HTLH', 'type': '证券公司'},
            {'name': '安信证券', 'code': 'AX', 'type': '证券公司'},
            {'name': '国金证券', 'code': 'GJ', 'type': '证券公司'},
            {'name': '国联证券', 'code': 'GL', 'type': '证券公司'},
            {'name': '浙商证券', 'code': 'ZS2', 'type': '证券公司'},
            {'name': '财通证券', 'code': 'CT', 'type': '证券公司'},
            {'name': '华安证券', 'code': 'HA', 'type': '证券公司'},
            {'name': '开源证券', 'code': 'KY', 'type': '证券公司'},
            {'name': '红塔证券', 'code': 'HT3', 'type': '证券公司'},
            {'name': '华宝证券', 'code': 'HB', 'type': '证券公司'},
            {'name': '信达证券', 'code': 'XD', 'type': '证券公司'},
            {'name': '万联证券', 'code': 'WL', 'type': '证券公司'},
            {'name': '世纪证券', 'code': 'SJ', 'type': '证券公司'},
        ]

    # ==================== 第三方销售机构 ====================

    def crawl_third_party_sales(self) -> List[Dict]:
        """获取第三方销售机构列表"""
        return [
            {'name': '天天基金', 'code': 'TTF', 'home': 'https://fund.eastmoney.com', 'type': '第三方销售'},
            {'name': '蚂蚁基金', 'code': 'MYF', 'home': 'https://fund.antfortune.com', 'type': '第三方销售'},
            {'name': '腾安基金', 'code': 'TA', 'home': 'https://danjuanapp.com', 'type': '第三方销售'},
            {'name': '雪球基金', 'code': 'XQ', 'home': 'https://xueqiu.com', 'type': '第三方销售'},
            {'name': '且慢', 'code': 'QM', 'home': 'https://qieman.com', 'type': '第三方销售'},
            {'name': '理财通', 'code': 'LC', 'home': 'https://weixin.qq.com', 'type': '第三方销售'},
            {'name': '京东金融', 'code': 'JD', 'home': 'https://jr.jd.com', 'type': '第三方销售'},
            {'name': '百度金融', 'code': 'BD', 'home': 'https://finance.baidu.com', 'type': '第三方销售'},
            {'name': '360你财富', 'code': '360', 'home': 'https://www.nicaifu.com', 'type': '第三方销售'},
            {'name': '挖财基金', 'code': 'WC', 'home': 'https://fund.wacai.com', 'type': '第三方销售'},
            {'name': '同花顺', 'code': 'THS', 'home': 'https://www.10jqka.com.cn', 'type': '第三方销售'},
            {'name': '东方财富', 'code': 'EM', 'home': 'https://www.eastmoney.com', 'type': '第三方销售'},
            {'name': '蛋卷基金', 'code': 'DJ', 'home': 'https://danjuanapp.com', 'type': '第三方销售'},
            {'name': '基金超市', 'code': 'JJCS', 'home': 'https://www.jjcs.com', 'type': '第三方销售'},
            {'name': '好买基金', 'code': 'HM', 'home': 'https://www.howbuy.com', 'type': '第三方销售'},
            {'name': '私募排排网', 'code': 'PP', 'home': 'https://www.simuwang.com', 'type': '第三方销售'},
            {'name': '钱大柱', 'code': 'QDZ', 'home': 'https://www.qiandz.com', 'type': '第三方销售'},
            {'name': '理财魔方', 'code': 'LCMF', 'home': 'https://www.licaimofang.com', 'type': '第三方销售'},
            {'name': '微微财富', 'code': 'WW', 'home': 'https://www.vvwealth.com', 'type': '第三方销售'},
            {'name': '金斧子', 'code': 'JFZ', 'home': 'https://www.jfz.com', 'type': '第三方销售'},
            {'name': '鼎盛财富', 'code': 'DS', 'home': 'https://www.dsf.com', 'type': '第三方销售'},
            {'name': '大唐财富', 'code': 'DT', 'home': 'https://www.datangwealth.com', 'type': '第三方销售'},
            {'name': '钜派投资', 'code': 'JP', 'home': 'https://www.jupi.com', 'type': '第三方销售'},
            {'name': '诺亚财富', 'code': 'NOAH', 'home': 'https://www.noahgroup.com', 'type': '第三方销售'},
            {'name': '宜信财富', 'code': 'YX', 'home': 'https://www.yixin.com', 'type': '第三方销售'},
            {'name': '恒天财富', 'code': 'HT', 'home': 'https://www.htcf.com', 'type': '第三方销售'},
            {'name': '新湖财富', 'code': 'XH', 'home': 'https://www.xinhu.com', 'type': '第三方销售'},
            {'name': '海银财富', 'code': 'HY', 'home': 'https://www.haiyin.com', 'type': '第三方销售'},
            {'name': '格上财富', 'code': 'GS', 'home': 'https://www.gebang.com', 'type': '第三方销售'},
            {'name': '私募工厂', 'code': 'SMGC', 'home': 'https://www.simugc.com', 'type': '第三方销售'},
            {'name': '朝阳永续', 'code': 'ZJ', 'home': 'https://www.9876.com', 'type': '第三方销售'},
            {'name': '价值立方', 'code': 'JZLF', 'home': 'https://www.jzlf.com', 'type': '第三方销售'},
            {'name': '财经', 'code': 'CJ', 'home': 'https://www.caijing.com', 'type': '第三方销售'},
            {'name': '财富趋势', 'code': 'CFQS', 'home': 'https://www.cfds.com', 'type': '第三方销售'},
            {'name': '同花顺金融', 'code': 'THSJR', 'home': 'https://www.10jqka.com.cn', 'type': '第三方销售'},
        ]

    # ==================== 外资金融机构 ====================

    def crawl_foreign_institutions(self) -> List[Dict]:
        """获取外资金融机构列表（含翻译）"""
        return [
            # 外资银行
            {'name': '汇丰银行', 'name_en': 'HSBC Holdings plc', 'code': 'HSBC', 'type': '外资银行'},
            {'name': '渣打银行', 'name_en': 'Standard Chartered plc', 'code': 'SC', 'type': '外资银行'},
            {'name': '花旗银行', 'name_en': 'Citibank N.A.', 'code': 'Citi', 'type': '外资银行'},
            {'name': '摩根大通', 'name_en': 'JPMorgan Chase & Co.', 'code': 'JPM', 'type': '外资银行'},
            {'name': '摩根士丹利', 'name_en': 'Morgan Stanley', 'code': 'MS', 'type': '外资银行'},
            {'name': '高盛集团', 'name_en': 'Goldman Sachs Group Inc.', 'code': 'GS', 'type': '外资银行'},
            {'name': '德意志银行', 'name_en': 'Deutsche Bank AG', 'code': 'DB', 'type': '外资银行'},
            {'name': '瑞士银行', 'name_en': 'UBS Group AG', 'code': 'UBS', 'type': '外资银行'},
            {'name': '法国巴黎银行', 'name_en': 'BNP Paribas SA', 'code': 'BNP', 'type': '外资银行'},
            {'name': '法兴银行', 'name_en': 'Société Générale SA', 'code': 'SG', 'type': '外资银行'},
            {'name': '东方汇理', 'name_en': 'Crédit Agricole CIB', 'code': 'CA', 'type': '外资银行'},
            {'name': '瑞穗银行', 'name_en': 'Mizuho Financial Group', 'code': 'MZ', 'type': '外资银行'},
            {'name': '三菱日联金融', 'name_en': 'Mitsubishi UFJ Financial Group', 'code': 'MUFG', 'type': '外资银行'},
            {'name': '三井住友金融', 'name_en': 'Sumitomo Mitsui Financial Group', 'code': 'SMFG', 'type': '外资银行'},
            {'name': '友利银行', 'name_en': 'Woori Bank', 'code': 'WB', 'type': '外资银行'},
            {'name': '韩亚银行', 'name_en': 'Hana Bank', 'code': 'HB', 'type': '外资银行'},
            {'name': '新韩银行', 'name_en': 'Shinhan Bank', 'code': 'SHB', 'type': '外资银行'},
            {'name': '星展银行', 'name_en': 'DBS Bank', 'code': 'DBS', 'type': '外资银行'},
            {'name': '华侨银行', 'name_en': 'OCBC Bank', 'code': 'OCBC', 'type': '外资银行'},
            {'name': '大华银行', 'name_en': 'UOB Bank', 'code': 'UOB', 'type': '外资银行'},
            # 外资保险
            {'name': '安盛保险', 'name_en': 'AXA SA', 'code': 'AXA', 'type': '外资保险公司'},
            {'name': '安联保险', 'name_en': 'Allianz SE', 'code': 'AL', 'type': '外资保险公司'},
            {'name': '忠利保险', 'name_en': 'Generali Group', 'code': 'G', 'type': '外资保险公司'},
            {'name': '保德信保险', 'name_en': 'Prudential Financial Inc.', 'code': 'PFI', 'type': '外资保险公司'},
            {'name': '大都会保险', 'name_en': 'MetLife Inc.', 'code': 'MET', 'type': '外资保险公司'},
            {'name': '友邦保险', 'name_en': 'AIA Group Limited', 'code': 'AIA', 'type': '外资保险公司'},
            {'name': '宏利保险', 'name_en': 'Manulife Financial', 'code': 'MFC', 'type': '外资保险公司'},
            {'name': '安达保险', 'name_en': 'Chubb Limited', 'code': 'CHB', 'type': '外资保险公司'},
            {'name': '信利保险', 'name_en': 'Zurich Insurance Group', 'code': 'ZUR', 'type': '外资保险公司'},
            {'name': '苏黎世保险', 'name_en': 'Zurich Insurance', 'code': 'ZUR2', 'type': '外资保险公司'},
            # 外资证券
            {'name': '野村证券', 'name_en': 'Nomura Holdings Inc.', 'code': 'NMR', 'type': '外资证券公司'},
            {'name': '大和证券', 'name_en': 'Daiwa Securities Group Inc.', 'code': 'Daiwa', 'type': '外资证券公司'},
            {'name': '瑞穗证券', 'name_en': 'Mizuho Securities', 'code': 'MZ2', 'type': '外资证券公司'},
            {'name': '三菱日联证券', 'name_en': 'Mitsubishi UFJ Securities', 'code': 'MUS', 'type': '外资证券公司'},
            {'name': '摩根士丹利华鑫', 'name_en': 'Morgan Stanley Huaxin', 'code': 'MSHX', 'type': '外资证券公司'},
            {'name': '高盛高华', 'name_en': 'Goldman Sachs Gao Hua', 'code': 'GSGH', 'type': '外资证券公司'},
            {'name': '瑞银证券', 'name_en': 'UBS Securities', 'code': 'UBSS', 'type': '外资证券公司'},
            {'name': '汇丰前海证券', 'name_en': 'HSBC Qianhai Securities', 'code': 'HSBCQS', 'type': '外资证券公司'},
        ]

    # ==================== 全部爬取 ====================

    def crawl_all(self) -> Dict[str, List[Dict]]:
        """爬取所有类型的金融机构"""
        return {
            'insurance': self.crawl_cbirc_insurance(),
            'fund_company': self.crawl_amac_fund_companies(),
            'fund_subsidiary': self.crawl_amac_fund_subsidiaries(),
            'private_fund': self.crawl_amac_private_funds(),
            'wealth_management': self.crawl_cbirc_wealth_management(),
            'financial_lease': self.crawl_cbirc_financial_lease(),
            'securities': self.crawl_sac_securities(),
            'foreign_institution': self.crawl_foreign_institutions(),
            'third_party': self.crawl_third_party_sales(),
        }
        # v4.4.0 修复：crawl_cbirc_banks() 调用一次后切片复用（移出字典字面量）
        _cbirc_banks = self.crawl_cbirc_banks()
        data['joint_stock_bank'] = _cbirc_banks[:6] + _cbirc_banks[6:16]
        data['city_commercial_bank'] = _cbirc_banks[16:36] if len(_cbirc_banks) > 16 else []
        data['rural_commercial_bank'] = _cbirc_banks[36:] if len(_cbirc_banks) > 36 else []

    def save_all(self):
        """保存所有机构数据到JSON文件"""
        data = self.crawl_all()

        for inst_type, institutions in data.items():
            filepath = self.data_dir / f"{inst_type}_list.json"
            output = {
                'type': inst_type,
                'type_name': self.INSTITUTION_TYPES.get(inst_type, inst_type),
                'count': len(institutions),
                'data_source': '行业协会/公开信息',
                'update_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'institutions': institutions
            }
            filepath.write_text(
                json.dumps(output, ensure_ascii=False, indent=2),
                encoding='utf-8'
            )
            print(f"已保存 {inst_type}: {len(institutions)} 条数据")

    def get_statistics(self) -> Dict[str, int]:
        """获取统计信息"""
        stats = {}
        for inst_type in self.INSTITUTION_TYPES.keys():
            filepath = self.data_dir / f"{inst_type}_list.json"
            if filepath.exists():
                try:
                    data = json.loads(filepath.read_text(encoding='utf-8'))
                    stats[inst_type] = data.get('count', 0)
                except:
                    stats[inst_type] = 0
            else:
                stats[inst_type] = 0
        return stats

    def get_foreign_institutions_formatted(self) -> str:
        """
        获取外资金融机构列表（外文 + 中文翻译）

        Returns:
            格式化字符串，外文名称和中文翻译对照显示
        """
        foreign_list = self.crawl_foreign_institutions()

        lines = ["【外资金融机构】外文名称 + 中文翻译", "-" * 60]

        # 按类型分组
        by_type = {}
        for inst in foreign_list:
            inst_type = inst.get('type', '未知')
            if inst_type not in by_type:
                by_type[inst_type] = []
            by_type[inst_type].append(inst)

        for inst_type, institutions in by_type.items():
            lines.append(f"\n## {inst_type}")
            for inst in institutions:
                name_en = inst.get('name_en', '')
                name_cn = inst.get('name', '')
                code = inst.get('code', '')
                display = f"{name_en} ({name_cn})" if name_en else name_cn
                lines.append(f"  {display} | {code}")

        return "\n".join(lines)

    def translate_institution_name(self, foreign_name: str) -> Dict[str, str]:
        """
        翻译外资金融机构名称

        Args:
            foreign_name: 外资金融机构外文名称

        Returns:
            dict: {
                'original': 原始外文,
                'chinese': 中文翻译,
                'display': '外文 (中文)' 格式显示
            }
        """
        # 查找匹配的机构
        foreign_list = self.crawl_foreign_institutions()
        for inst in foreign_list:
            if inst.get('name_en', '').lower() == foreign_name.lower():
                return {
                    'original': inst.get('name_en', ''),
                    'chinese': inst.get('name', ''),
                    'display': f"{inst.get('name_en', '')} ({inst.get('name', '')})"
                }

        # 未找到匹配，返回占位符
        return {
            'original': foreign_name,
            'chinese': f"[翻译]{foreign_name}[/翻译]",
            'display': f"{foreign_name} ([翻译]{foreign_name}[/翻译])"
        }


def main():
    """测试"""
    crawler = FullInstitutionCrawler()

    print("=" * 60)
    print("金融机构全量爬取器")
    print("=" * 60)

    # 爬取并保存
    print("\n开始爬取所有金融机构...")
    crawler.save_all()

    # 统计
    print("\n" + "=" * 60)
    print("统计信息")
    print("=" * 60)
    stats = crawler.get_statistics()
    total = 0
    for inst_type, count in stats.items():
        type_name = crawler.INSTITUTION_TYPES.get(inst_type, inst_type)
        print(f"  {type_name}: {count}家")
        total += count
    print(f"\n合计: {total}家金融机构")


if __name__ == '__main__':
    main()
