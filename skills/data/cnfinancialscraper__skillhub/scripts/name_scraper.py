# -*- coding: utf-8 -*-
"""
金融机构名字爬虫增强模块
支持通过机构名称爬取网站信息，包含反爬、翻译和双语展示功能
"""

import json
import re
import time
import random
import hashlib
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime

# Scrapling导入
try:
    from scrapling.fetchers import StealthyFetcher, DynamicFetcher
    from scrapling.parser import Selector
    SCRAPLING_AVAILABLE = True
except ImportError:
    SCRAPLING_AVAILABLE = False
    Selector = Any  # type: ignore  # forward reference fallback

try:
    from playwright.sync_api import sync_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False

# 数据目录
SKILL_DATA_DIR = Path(__file__).parent.parent / "data"

# 常用URL模式（从机构名称推断官网）
URL_PATTERNS = {
    # 政策性银行
    "国家开发银行": "https://www.cdb.com.cn",
    # 中国进出口银行（官网为政府域名，已移除）
    "中国农业发展银行": "https://www.adbc.com.cn",
    # 国有商业银行
    "工商银行": "https://www.icbc.com.cn",
    "建设银行": "https://www.ccb.com",
    "农业银行": "https://www.abchina.com",
    "中国银行": "https://www.boc.cn",
    "交通银行": "https://www.bankcomm.com",
    "邮储银行": "https://www.psbc.com",
    # 股份制银行
    "招商银行": "https://www.cmbchina.com",
    "中信银行": "https://www.citicbank.com",
    "浦发银行": "https://www.spdb.com.cn",
    "兴业银行": "https://www.cib.com.cn",
    "民生银行": "https://www.cmbc.com.cn",
    "平安银行": "https://bank.pingan.com",
    "光大银行": "https://www.cebbank.com",
    "华夏银行": "https://www.hxb.com.cn",
    "广发银行": "https://www.cgbchina.com.cn",
    "北京银行": "https://www.bankofbeijing.com.cn",
    "上海银行": "https://www.bankofshanghai.com",
    "江苏银行": "https://www.jsbchina.cn",
    "南京银行": "https://www.njcb.com.cn",
    "杭州银行": "https://www.hzbank.com.cn",
    "宁波银行": "https://www.nbbank.com.cn",
    # 保险公司
    "中国人寿": "https://www.chinalife.com.cn",
    "中国平安": "https://www.pingan.com.cn",
    "中国太保": "https://www.cpic.com.cn",
    "中国人保": "https://www.picc.com.cn",
    "新华保险": "https://www.newchina-life.com",
    "泰康保险": "https://www.taikang.com",
    "友邦保险": "https://www.aia.com.cn",
    # 基金公司
    "易方达": "https://www.efunds.com.cn",
    "华夏基金": "https://www.chinaamc.com",
    "广发基金": "https://www.gffunds.com.cn",
    "嘉实基金": "https://www.jsfund.cn",
    "南方基金": "https://www.nffund.com.cn",
    "博时基金": "https://www.bosera.com",
    "招商基金": "https://www.cmfchina.com",
    "工银基金": "https://www.icbcfs.com",
    "建信基金": "https://www.ccbfund.cn",
    "富国基金": "https://www.fullgoal.com.cn",
    "鹏华基金": "https://www.phfund.com.cn",
    "汇添富基金": "https://www.htffund.com",
    "中欧基金": "https://www.zofund.com",
    "兴证全球基金": "https://www.xqglobal.com",
    # 证券公司
    "中信证券": "https://www.cs.ecitic.com",
    "中信建投证券": "https://www.csc108.com",
    "国泰君安证券": "https://www.gtja.com",
    "华泰证券": "https://www.htsc.com.cn",
    "广发证券": "https://www.gf.com.cn",
    "招商证券": "https://www.newone.com.cn",
    "海通证券": "https://www.htsec.com",
    "国信证券": "https://www.guosen.com.cn",
    "东方证券": "https://www.dfzq.com.cn",
    "兴业证券": "https://www.xyzq.com.cn",
    "银河证券": "https://www.chinastock.com.cn",
    "长江证券": "https://www.95579.com",
    "中金公司": "https://www.cicc.com",
    "光大证券": "https://www.ebscn.com",
    "平安证券": "https://stock.pingan.com",
    "方正证券": "https://www.foundersc.com",
    # 信托公司
    "中信信托": "https://www.zxxt.com.cn",
    "平安信托": "https://www.paxt.com.cn",
    "中融信托": "https://www.zhongrongtrust.com",
    "华润信托": "https://www.crhtrust.com.cn",
    "外贸信托": "https://www.fotacn.com",
    # 外资银行
    "汇丰银行": "https://www.hsbc.com.cn",
    "渣打银行": "https://www.standardchartered.com.cn",
    "花旗银行": "https://www.citibank.com.cn",
    "摩根大通银行": "https://www.jpmorganchina.com.cn",
    "高盛集团": "https://www.goldmansachs.com.cn",
    "瑞银证券": "https://www.ubs.com/cn/zh.html",
    "野村证券": "https://www.nomura.com",
    # 外资保险公司
    "安盛保险": "https://www.axa.com.cn",
    "安联保险": "https://www.allianz.com.cn",
    "友邦保险": "https://www.aia.com.cn",
    # 外资资产管理公司
    "贝莱德资产管理": "https://www.blackrock.com.cn",
    "瑞银资产管理": "https://www.ubs.com/global/en/asset-management.html",
}

# 外资机构名称映射（用于翻译）
FOREIGN_INSTITUTION_TRANSLATIONS = {
    "汇丰银行": "HSBC Holdings plc",
    "渣打银行": "Standard Chartered plc",
    "花旗银行": "Citibank N.A.",
    "摩根大通银行": "JPMorgan Chase & Co.",
    "摩根士丹利": "Morgan Stanley",
    "高盛集团": "Goldman Sachs Group Inc.",
    "德意志银行": "Deutsche Bank AG",
    "瑞士银行": "UBS Group AG",
    "法国巴黎银行": "BNP Paribas SA",
    "法兴银行": "Société Générale SA",
    "东方汇理银行": "Crédit Agricole CIB",
    "瑞穗银行": "Mizuho Financial Group",
    "三菱日联金融": "Mitsubishi UFJ Financial Group",
    "三井住友金融": "Sumitomo Mitsui Financial Group",
    "友利银行": "Woori Bank",
    "韩亚银行": "Hana Bank",
    "新韩银行": "Shinhan Bank",
    "星展银行": "DBS Bank",
    "华侨银行": "OCBC Bank",
    "大华银行": "UOB Bank",
    "东亚银行": "Bank of East Asia",
    "恒生银行": "Hang Seng Bank",
    "安盛保险": "AXA SA",
    "安联保险": "Allianz SE",
    "忠利保险": "Generali Group",
    "保德信保险": "Prudential Financial Inc.",
    "大都会保险": "MetLife Inc.",
    "友邦保险": "AIA Group Limited",
    "宏利保险": "Manulife Financial",
    "安达保险": "Chubb Limited",
    "信利保险": "Zurich Insurance Group",
    "英杰华保险": "Aviva",
    "耆卫保险": "Old Mutual",
    "日本生命保险": "Nippon Life Insurance",
    "第一生命保险": "Dai-ichi Life Insurance",
    "明治安田保险": "Meiji Yasuda Life Insurance",
    "野村证券": "Nomura Holdings Inc.",
    "大和证券": "Daiwa Securities Group Inc.",
    "瑞穗证券": "Mizuho Securities",
    "三菱日联证券": "Mitsubishi UFJ Securities",
    "高盛高华证券": "Goldman Sachs Gao Hua",
    "汇丰前海证券": "HSBC Qianhai Securities",
    "法巴证券": "BNP Paribas Securities",
    "法兴证券": "Société Générale Securities",
    "东方汇理期货": "Crédit Agricole CIB Futures",
    "瑞银期货": "UBS Futures",
    "汇丰资产管理": "HSBC Global Asset Management",
    "瑞银资产管理": "UBS Asset Management",
    "摩根资产管理": "JPMorgan Asset Management",
    "贝莱德资产管理": "BlackRock",
    "道富环球投资管理": "State Street Global Advisors",
    "富达国际资产管理": "Fidelity International",
    "景顺资产管理": "Invesco",
    "安联资产管理": "Allianz Global Investors",
}

# 反爬设置
DEFAULT_DELAY = (1.5, 3.5)  # 随机延迟范围（秒）
MAX_RETRIES = 2
REQUEST_TIMEOUT = 30000  # 30秒


class AntiCrawlFetcher:
    """带反爬功能的爬取器"""

    def __init__(self):
        self.fetcher = None
        self.last_request_time = 0
        self.request_count = 0
        self.failed_domains = set()  # 记录失败域名，避免重复请求

    def _random_delay(self):
        """随机延迟"""
        delay = random.uniform(*DEFAULT_DELAY)
        time.sleep(delay)

    def _update_last_request(self):
        """更新最后请求时间"""
        self.last_request_time = time.time()
        self.request_count += 1

    def fetch(self, url: str, use_dynamic: bool = False,
             headers: Dict = None, retry_count: int = 0) -> Optional[Selector]:
        """
        带反爬的爬取

        Args:
            url: 目标URL
            use_dynamic: 是否使用动态渲染
            headers: 自定义请求头
            retry_count: 当前重试次数

        Returns:
            Selector对象或None
        """
        if not SCRAPLING_AVAILABLE:
            return None

        self._random_delay()

        try:
            if self.fetcher is None:
                self.fetcher = StealthyFetcher()

            # 构建请求头
            request_headers = {
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
                "Accept-Encoding": "gzip, deflate, br",
                "DNT": "1",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1",
            }
            if headers:
                request_headers.update(headers)

            # 尝试使用动态爬取
            if use_dynamic:
                try:
                    page = DynamicFetcher.fetch(
                        url,
                        headless=True,
                        network_idle=True,
                        solve_cloudflare=True,
                        timeout=REQUEST_TIMEOUT
                    )
                    self._update_last_request()

                    # scrapling 0.2.x 兼容
                    if hasattr(page, 'html_content'):
                        page.html = page.html_content
                    elif hasattr(page, 'body') and isinstance(page.body, str):
                        page.html = page.body

                    return page
                except Exception as e:
                    if retry_count < MAX_RETRIES:
                        wait_time = random.uniform(5, 15)
                        print(f"[反爬] 动态爬取失败，{wait_time:.1f}秒后重试: {url}")
                        time.sleep(wait_time)
                        return self.fetch(url, use_dynamic, headers, retry_count + 1)
                    else:
                        print(f"[反爬] 动态爬取最终失败: {url}")
                        return None

            # 使用隐式请求（默认）
            page = self.fetcher.fetch(
                url,
                headless=True,
                solve_cloudflare=True,
                timeout=REQUEST_TIMEOUT
            )
            self._update_last_request()

            # scrapling 0.2.x 兼容：注入 .html 属性
            if hasattr(page, 'html_content'):
                page.html = page.html_content
            elif hasattr(page, 'body') and isinstance(page.body, str):
                page.html = page.body

            return page

        except Exception as e:
            print(f"[反爬] 爬取失败 ({retry_count + 1}/{MAX_RETRIES + 1}): {url}")
            print(f"[错误] {str(e)[:100]}")

            if retry_count < MAX_RETRIES:
                wait_time = random.uniform(5, 15)
                print(f"[反爬] {wait_time:.1f}秒后重试...")
                time.sleep(wait_time)
                return self.fetch(url, use_dynamic, headers, retry_count + 1)

            return None


class InstitutionNameScraper:
    """通过机构名称爬取网站内容的爬取器"""

    def __init__(self):
        self.fetcher = AntiCrawlFetcher()
        self._institution_cache = {}  # 机构信息缓存
        self._load_institution_data()

    def _load_institution_data(self):
        """加载所有机构数据"""
        data_files = [
            "institutions.json",
            "foreign_institution_list.json",
            "policy_bank_list.json",
            "state_owned_bank_list.json",
            "joint_stock_bank_list.json",
            "city_commercial_bank_list.json",
            "rural_commercial_bank_list.json",
            "insurance_list.json",
            "fund_company_list.json",
            "securities_list.json",
            "trust_company_list.json",
            "private_fund_list.json",
            "financial_lease_list.json",
            "city_investment_list.json",
        ]

        for filename in data_files:
            filepath = SKILL_DATA_DIR / filename
            if filepath.exists():
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        # 提取institutions数组
                        if "institutions" in data:
                            for inst in data["institutions"]:
                                self._institution_cache[inst.get("name", "")] = {
                                    **inst,
                                    "source_file": filename
                                }
                except Exception as e:
                    print(f"[警告] 加载{filename}失败: {e}")

    def find_institution(self, name: str) -> Optional[Dict]:
        """
        通过名称查找机构信息

        Args:
            name: 机构名称（支持模糊匹配）

        Returns:
            机构信息字典
        """
        if not name:
            return None

        # 精确匹配
        if name in self._institution_cache:
            return self._institution_cache[name]

        # 模糊匹配
        name_lower = name.lower()
        for inst_name, inst_info in self._institution_cache.items():
            if name_lower in inst_name.lower() or inst_name.lower() in name_lower:
                return inst_info

        # 关键词匹配
        keywords = name.replace("基金", "").replace("证券", "").replace("银行", "").replace("保险", "").strip()
        if keywords and len(keywords) >= 2:
            for inst_name, inst_info in self._institution_cache.items():
                if keywords in inst_name or inst_name in keywords:
                    return inst_info

        return None

    def get_institution_url(self, name: str) -> Optional[str]:
        """
        获取机构官网URL

        Args:
            name: 机构名称

        Returns:
            官网URL或None
        """
        # 优先从预定义URL模式获取
        if name in URL_PATTERNS:
            return URL_PATTERNS[name]

        # 从URL模式中查找包含关键词的
        for pattern_name, url in URL_PATTERNS.items():
            if name in pattern_name or pattern_name in name:
                return url

        return None

    def is_foreign_institution(self, name: str) -> bool:
        """判断是否为外资机构"""
        return name in FOREIGN_INSTITUTION_TRANSLATIONS

    def get_english_name(self, name: str) -> Optional[str]:
        """获取机构英文名称"""
        return FOREIGN_INSTITUTION_TRANSLATIONS.get(name)

    def scrape_by_name(self, name: str, use_dynamic: bool = True) -> Dict[str, Any]:
        """
        通过机构名称爬取网站内容

        Args:
            name: 机构名称
            use_dynamic: 是否使用动态渲染

        Returns:
            爬取结果字典
        """
        result = {
            "name": name,
            "scrape_time": time.strftime("%Y-%m-%d %H:%M:%S"),
            "url": None,
            "success": False,
            "content": {},
            "error": None,
            "is_foreign": self.is_foreign_institution(name),
            "english_name": self.get_english_name(name),
        }

        # 查找机构信息
        inst_info = self.find_institution(name)
        if inst_info:
            result["institution_info"] = inst_info

        # 获取URL
        url = self.get_institution_url(name)
        if not url:
            result["error"] = f"未找到机构'{name}'的官网URL"
            return result

        result["url"] = url
        print(f"[爬虫] 正在爬取: {name} -> {url}")

        # 爬取内容
        page = self.fetcher.fetch(url, use_dynamic=use_dynamic)
        if page is None:
            result["error"] = "爬取失败，请检查网络或URL是否可访问"
            return result

        result["success"] = True

        # 提取页面内容
        content = self._extract_page_content(page, url)
        result["content"] = content

        # 如果是外资机构，处理双语展示
        if result["is_foreign"]:
            result["bilingual_content"] = self._generate_bilingual_content(content, name)

        return result

    def _extract_page_content(self, page: Selector, url: str) -> Dict[str, Any]:
        """提取页面内容"""
        content = {
            "title": "",
            "main_content": "",
            "about": "",
            "products": [],
            "contact": {},
        }

        try:
            # 提取标题
            for sel in ["h1", ".site-title", "[class*='title']", "title"]:
                try:
                    el = page.css_first(sel)
                    if el:
                        content["title"] = el.text().strip()[:200]
                        break
                except:
                    continue

            # 如果没拿到标题，尝试从meta获取
            if not content["title"]:
                try:
                    meta_title = page.re_search(r'<title[^>]*>([^<]+)</title>')
                    if meta_title:
                        content["title"] = meta_title.group(1).strip()
                except:
                    pass

            # 提取主要文本内容
            text_selectors = [
                "main",
                "article",
                ".main-content",
                "[class*='content']",
                "[class*='about']",
                ".container",
            ]

            for sel in text_selectors:
                try:
                    el = page.css_first(sel)
                    if el:
                        text = el.text().strip()
                        if len(text) > 100:  # 至少100字符
                            content["main_content"] = text[:3000]  # 限制长度
                            break
                except:
                    continue

            # 提取关于我们/简介
            about_patterns = [
                r'(?:关于我们|关于我们|公司简介|Company Profile|About Us)[：:\s]*([^\n]{100,500})',
                r'(?:我们是谁|Our Story)[：:\s]*([^\n]{50,300})',
            ]

            for pattern in about_patterns:
                match = page.re_search(pattern)
                if match:
                    content["about"] = match.group(1).strip()
                    break

            # 如果还没获取到about，尝试从main_content中提取
            if not content["about"] and content["main_content"]:
                about_match = re.search(r'(?:关于我们|关于我们|公司简介)[：:\s]*([^\n]{50,300})', content["main_content"])
                if about_match:
                    content["about"] = about_match.group(1).strip()

            # 提取联系信息
            contact_patterns = {
                "phone": r'(\d{3,4}[-\s]?\d{7,8}|\d{3}[-\s]?\d{4}[-\s]?\d{4})',
                "email": r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})',
                "address": r'(?:地址|Address)[：:\s]*([^\n]{10,100})',
            }

            for key, pattern in contact_patterns.items():
                match = page.re_search(pattern)
                if match:
                    content["contact"][key] = match.group(1).strip()

        except Exception as e:
            print(f"[警告] 内容提取失败: {e}")

        return content

    def _generate_bilingual_content(self, content: Dict, name: str) -> Dict[str, Any]:
        """生成双语内容"""
        bilingual = {
            "institution": name,
            "english_name": self.get_english_name(name),
            "title": {},
            "about": {},
            "main_content": {},
        }

        # 标题翻译（简化处理，实际项目中可接入翻译API）
        if content.get("title"):
            bilingual["title"] = {
                "zh": content["title"],
                "en": self._translate_to_english(content["title"], name),
            }

        # 关于信息双语
        if content.get("about"):
            bilingual["about"] = {
                "zh": content["about"],
                "en": self._translate_to_english(content["about"], name),
            }

        # 主要内容双语
        if content.get("main_content"):
            bilingual["main_content"] = {
                "zh": content["main_content"][:1500] if len(content["main_content"]) > 1500 else content["main_content"],
                "en": self._translate_to_english(content["main_content"][:1500] if len(content["main_content"]) > 1500 else content["main_content"], name),
            }

        return bilingual

    def _translate_to_english(self, text: str, institution_name: str) -> str:
        """
        将中文文本翻译为英文（简化版本）
        实际项目中应接入专业翻译API（如百度翻译、Google翻译等）
        """
        if not text:
            return ""

        # 简短翻译映射（实际项目中应接入翻译API）
        translation_mapping = {
            "关于我们": "About Us",
            "公司简介": "Company Profile",
            "联系我们": "Contact Us",
            "产品中心": "Products",
            "新闻中心": "News",
            "投资者关系": "Investor Relations",
            "人才招聘": "Careers",
            "企业文化": "Corporate Culture",
            "发展历程": "Our Story",
            "组织架构": "Organization",
            "社会责任": "Corporate Social Responsibility",
            "公司地址": "Address",
            "联系电话": "Tel",
            "电子邮箱": "Email",
        }

        # 检查是否是简短文本
        for zh, en in translation_mapping.items():
            if zh in text[:10]:
                return en

        # 对于长文本，返回原文+说明（实际应接入翻译API）
        if len(text) > 100:
            return f"[English Translation of Chinese Text]\n{text[:500]}..."

        return f"[Translated] {text}"

    def format_bilingual_display(self, result: Dict[str, Any]) -> str:
        """
        格式化双语展示内容

        Args:
            result: 爬取结果

        Returns:
            格式化字符串
        """
        if not result.get("success"):
            return f"❌ 爬取失败: {result.get('error', '未知错误')}"

        name = result.get("name", "")
        english_name = result.get("english_name", "")

        output = []
        output.append(f"\n{'='*60}")
        output.append(f"🏦 机构名称: {name}")
        if english_name:
            output.append(f"🌐 English: {english_name}")
        output.append(f"{'='*60}\n")

        # 外资机构双语展示
        if result.get("is_foreign") and result.get("bilingual_content"):
            bc = result["bilingual_content"]

            output.append("【公司简介 / Company Profile】\n")

            if bc.get("about"):
                about = bc["about"]
                output.append(f"🇨🇳 中文: {about.get('zh', '')}")
                output.append(f"🇺🇸 EN: {about.get('en', '')}")
            else:
                output.append("(暂无公司简介 / No profile available)")

            output.append(f"\n{'─'*60}")

            if bc.get("main_content"):
                content = bc["main_content"]
                output.append("\n【主要内容 / Main Content】\n")
                output.append(f"🇨🇳 中文:\n{content.get('zh', '')}")
                output.append(f"\n🇺🇸 EN:\n{content.get('en', '')}")

        else:
            # 国内机构单语展示
            content = result.get("content", {})

            if content.get("title"):
                output.append(f"📌 标题: {content['title']}\n")

            if content.get("about"):
                output.append(f"\n📋 关于我们:\n{content['about']}")

            if content.get("main_content"):
                output.append(f"\n📄 主要内容:\n{content['main_content'][:800]}...")

            if content.get("contact"):
                output.append(f"\n📞 联系方式:")
                for k, v in content["contact"].items():
                    output.append(f"  {k}: {v}")

        output.append(f"\n{'='*60}")
        output.append(f"🕐 爬取时间: {result.get('scrape_time', '')}")
        output.append(f"🔗 来源: {result.get('url', '')}")
        output.append(f"{'='*60}")

        return "\n".join(output)


def scrape_institution_by_name(name: str, use_dynamic: bool = True) -> Dict[str, Any]:
    """
    通过机构名称爬取信息的便捷函数

    Args:
        name: 机构名称
        use_dynamic: 是否使用动态渲染

    Returns:
        爬取结果
    """
    scraper = InstitutionNameScraper()
    result = scraper.scrape_by_name(name, use_dynamic=use_dynamic)
    return result


def scrape_institution_by_url(url: str, use_dynamic: bool = True) -> Dict[str, Any]:
    """
    通过URL直接爬取网站内容

    Args:
        url: 目标URL
        use_dynamic: 是否使用动态渲染

    Returns:
        爬取结果
    """
    result = {
        "scrape_time": time.strftime("%Y-%m-%d %H:%M:%S"),
        "url": url,
        "success": False,
        "content": {},
        "error": None,
        "is_foreign": False,
        "english_name": None,
    }

    # 从URL推断机构名称
    url_lower = url.lower()
    inferred_name = None

    # 尝试从URL域名匹配已知机构
    for name, pattern_url in URL_PATTERNS.items():
        if pattern_url.lower() in url_lower or url_lower in pattern_url.lower():
            inferred_name = name
            break

    # 检查是否是外资机构
    if inferred_name:
        result["is_foreign"] = is_foreign_institution(inferred_name)
        result["english_name"] = FOREIGN_INSTITUTION_TRANSLATIONS.get(inferred_name)
        result["inferred_name"] = inferred_name

    # 爬取
    fetcher = AntiCrawlFetcher()
    page = fetcher.fetch(url, use_dynamic=use_dynamic)

    if page is None:
        result["error"] = "爬取失败，请检查URL或网络连接"
        return result

    result["success"] = True

    # 提取内容
    scraper = InstitutionNameScraper()
    content = scraper._extract_page_content(page, url)
    result["content"] = content

    # 如果是外资机构，处理双语展示
    if result["is_foreign"]:
        result["bilingual_content"] = scraper._generate_bilingual_content(content, inferred_name or url)

    return result


def is_foreign_institution(name: str) -> bool:
    """判断是否为外资机构"""
    return name in FOREIGN_INSTITUTION_TRANSLATIONS


def scrape_institution(input_str: str, use_dynamic: bool = True) -> Dict[str, Any]:
    """
    智能爬取入口 - 自动识别输入是URL还是机构名称

    Args:
        input_str: URL或机构名称
        use_dynamic: 是否使用动态渲染

    Returns:
        爬取结果
    """
    # 判断是URL还是名称
    is_url = (
        "http://" in input_str.lower() or
        "https://" in input_str.lower() or
        ".com" in input_str.lower() or
        ".cn" in input_str.lower() or
        ".org" in input_str.lower() or
        "/" in input_str and len(input_str) > 20  # 简单判断URL格式
    )

    if is_url:
        return scrape_institution_by_url(input_str, use_dynamic=use_dynamic)
    else:
        return scrape_institution_by_name(input_str, use_dynamic=use_dynamic)


def format_scraping_result(result: Dict[str, Any], bilingual: bool = True) -> str:
    """
    格式化爬取结果

    Args:
        result: 爬取结果
        bilingual: 是否双语展示

    Returns:
        格式化字符串
    """
    scraper = InstitutionNameScraper()

    if bilingual and result.get("is_foreign"):
        return scraper.format_bilingual_display(result)
    else:
        # 非双语格式
        if not result.get("success"):
            return f"❌ 爬取失败: {result.get('error', '未知错误')}"

        output = []
        output.append(f"\n🏦 {result.get('name', '')}")
        output.append(f"🔗 {result.get('url', '')}\n")

        content = result.get("content", {})
        if content.get("title"):
            output.append(f"📌 标题: {content['title']}\n")
        if content.get("about"):
            output.append(f"📋 关于: {content['about'][:300]}...")
        if content.get("main_content"):
            output.append(f"📄 内容: {content['main_content'][:500]}...")

        return "\n".join(output)


# CLI入口
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("用法:")
        print("  python name_scraper.py <机构名称>           # 爬取单个机构")
        print("  python name_scraper.py --list <名称列表>    # 批量爬取")
        print("  python name_scraper.py --search <关键词>    # 搜索机构")
        print("\n示例:")
        print('  python name_scraper.py "汇丰银行"')
        print('  python name_scraper.py "易方达基金"')
        print('  python name_scraper.py --search "基金"')
        sys.exit(1)

    scraper = InstitutionNameScraper()

    if sys.argv[1] == "--search":
        # 搜索机构
        if len(sys.argv) < 3:
            print("请提供搜索关键词")
            sys.exit(1)
        keyword = sys.argv[2]
        print(f"\n搜索关键词: {keyword}")
        print("="*50)

        for inst_name in sorted(scraper._institution_cache.keys()):
            if keyword in inst_name:
                info = scraper._institution_cache[inst_name]
                print(f"  ✅ {inst_name} ({info.get('code', '')}) - {info.get('source_file', '')}")
        print(f"\n共找到匹配结果")

    elif sys.argv[1] == "--list":
        # 批量爬取
        if len(sys.argv) < 3:
            print("请提供名称列表文件")
            sys.exit(1)
        file_path = sys.argv[2]
        with open(file_path, 'r', encoding='utf-8') as f:
            names = [line.strip() for line in f if line.strip()]

        print(f"\n开始批量爬取 {len(names)} 个机构...")
        for name in names:
            result = scraper.scrape_by_name(name)
            print(format_scraping_result(result))
            time.sleep(random.uniform(2, 5))

    else:
        # 单个爬取
        name = sys.argv[1]
        print(f"\n正在爬取: {name}")
        result = scraper.scrape_by_name(name)
        print(format_scraping_result(result))