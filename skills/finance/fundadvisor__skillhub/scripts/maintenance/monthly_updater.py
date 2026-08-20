"""
每月第一个工作日自动更新脚本 v2.0
从天天基金网采集全量基金经理名单、管理产品、基金公司信息
自动检测并爬取新报告、投资观点、经理新闻
"""
import json
import os
import sys
import time
import re
from datetime import datetime, date, timedelta
import traceback
import hashlib  # @since 5.1.6: S5 fix - 数据完整性校验
# v9.0: 去除 dateutil/requests/bs4 顶层依赖（改为函数内惰性 import），
# 使 `import monthly_updater` 在零依赖环境可用（实际抓取时才需 requests/bs4）。

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(os.path.dirname(SCRIPT_DIR))
import sys as _sys; _sys.path.insert(0, os.path.dirname(SCRIPT_DIR))
from fund_advisor_paths import DATA_DIR, load_holdings, is_columnar, _decode_columnar  # noqa: E402


class MonthlyUpdater:
    """每月自动更新器 v2.0"""

    REPORT_TYPES = {
        'annual': ['年度报告', '年报'],
        'semi': ['半年度报告', '半年报'],
        'quarterly': ['季度报告', '季报', '第一季度', '第二季度', '第三季度', '第四季度']
    }

    def __init__(self, base_dir=None):
        # monthly_updater.py is 3 levels deep: scripts/maintenance/
        self.base_dir = base_dir or os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.data_dir = os.path.join(self.base_dir, 'data')
        self.meta_path = os.path.join(self.base_dir, '_meta.json')
        # v9.0: requests 惰性导入（零依赖环境可构造对象，仅抓取时需 requests）
        self.session = None
        try:
            import requests as _requests
            self.session = _requests.Session()
            self.session.headers.update({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Referer': 'https://fund.eastmoney.com/'
            })
        except ImportError:
            pass
        self.load_meta()

    def load_meta(self):
        """加载元数据"""
        try:
            with open(self.meta_path, 'r', encoding='utf-8') as f:
                self.meta = json.load(f)
        except Exception:
            self.meta = {}

    def save_meta(self):
        """保存元数据"""
        with open(self.meta_path, 'w', encoding='utf-8') as f:
            json.dump(self.meta, f, ensure_ascii=False, indent=2)

    def _safe_save_json(self, data, path):
        """v9.0: 从死代码归位（原缩进在 __main__ 块内不可见）— 写 JSON 前做 roundtrip 校验，防止半写状态"""
        tmp_path = path + ".tmp"
        try:
            with open(tmp_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            with open(tmp_path, 'r', encoding='utf-8') as f:
                json.load(f)  # 解析失败抛 JSONDecodeError
            if os.path.exists(path):
                os.replace(tmp_path, path)
            else:
                os.rename(tmp_path, path)
            return True
        except Exception as e:
            if os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                except Exception:
                    pass
            raise RuntimeError(f"JSON 写入失败 ({path}): {e}")

    def _validate_url(self, url):
        """v9.0: URL 校验：只允许 http/https + 域名白名单（防 SSRF）"""
        from urllib.parse import urlparse
        p = urlparse(url)
        if p.scheme not in ("http", "https"):
            raise ValueError(f"拒绝非 HTTP/HTTPS 协议: {p.scheme}")
        host = p.hostname
        if not host:
            raise ValueError(f"URL 缺少主机名: {url}")
        ALLOWED = {
            "fund.eastmoney.com", "fund.10jqka.com.cn", "fundgz.1234567.com.cn",
            "push2.eastmoney.com", "push2his.eastmoney.com",
            "api.fund.eastmoney.com", "akshare.akfamily.xyz",
        }
        if not any(host == d or host.endswith("." + d) for d in ALLOWED):
            raise ValueError(f"域名不在白名单: {host}")
        return url

    def _record_page_hash(self, url, content):
        """v9.0: 记录抓取页面的 SHA256 到 _meta.json"""
        if not isinstance(content, (str, bytes)):
            return
        content_bytes = content.encode("utf-8") if isinstance(content, str) else content
        page_hash = hashlib.sha256(content_bytes).hexdigest()
        self.meta.setdefault("page_hashes", {})[url] = {
            "sha256": page_hash,
            "size": len(content_bytes),
            "fetched_at": datetime.now().isoformat()
        }

    def get_first_workday_of_month(self, year=None, month=None):
        """获取指定月份的第一个工作日（v9.0: 纯 datetime 实现，去 dateutil 依赖）"""
        today = date.today() if year is None else date(year, month, 1)
        first_day = date(today.year, today.month, 1)
        d = first_day
        while d.weekday() >= 5:  # 周六(5)/周日(6) 顺延到周一
            d = d + timedelta(days=1)
        return d

    def is_first_workday(self):
        """检查今天是否是本月第一个工作日"""
        today = date.today()
        return today == self.get_first_workday_of_month(today.year, today.month)

    # ==================== 1. 采集基金经理名单 ====================

    def collect_all_managers(self):
        """采集全量基金经理数据"""
        print("\n[1/6] 采集全量基金经理名单...")

        all_managers = []
        try:
            import akshare as ak
            df = ak.fund_manager_em()
            print(f"  通过akshare获取到 {len(df)} 条记录")

            for _, row in df.iterrows():
                manager = {
                    'raw_id': str(row.get('序号', '')),
                    'manager_id': str(row.get('序号', '')),
                    'name': row.get('姓名', ''),
                    'company_name': row.get('所属公司', ''),
                    'current_fund_code': str(row.get('现任基金代码', '')).strip().zfill(6) if str(row.get('现任基金代码', '')).strip().isdigit() else '',
                    'current_fund_name': str(row.get('现任基金', '')) if str(row.get('现任基金', '')) != 'nan' else '',
                    'tenure_days': int(row.get('累计从业时间', 0)) if str(row.get('累计从业时间', 0)).isdigit() else 0,
                    'total_scale': float(row.get('现任基金资产总规模', 0)) if str(row.get('现任基金资产总规模', 0)).replace('.', '').isdigit() else 0,
                    'best_return': str(row.get('现任基金最佳回报', '')) if str(row.get('现任基金最佳回报', '')) != 'nan' else '',
                    'last_updated': datetime.now().strftime('%Y-%m-%d')
                }
                all_managers.append(manager)
        except Exception as e:
            print(f"  akshare采集失败: {e}")
            all_managers = self._collect_from_eastmoney()

        return all_managers

    def _collect_from_eastmoney(self):
        """从东方财富接口采集（备用）"""
        print("  回退到东方财富接口...")
        managers = []
        page = 1
        page_size = 50

        while True:
            try:
                url = "https://fund.eastmoney.com/Data/FundDataPortfolio_Interface.aspx"
                params = {'dt': '14', 'ft': 'all', 'pn': page_size, 'pi': page, 'sc': 'abbname', 'st': 'asc', 'mc': 'returnjson'}
                resp = self.session.get(url, params=params, timeout=30)
                match = re.search(r'returnjson\s*=\s*(\{.*?\});', resp.text, re.DOTALL)
                if not match:
                    break
                data = json.loads(match.group(1))
                items = data.get('data', []) or data.get('list', [])
                if not items:
                    break
                for item in items:
                    managers.append({
                        'manager_id': str(item.get('id', '')),
                        'name': item.get('name', ''),
                        'company_name': item.get('company', ''),
                        'current_fund_code': '',
                        'current_fund_name': '',
                        'tenure_days': 0,
                        'total_scale': 0,
                        'last_updated': datetime.now().strftime('%Y-%m-%d')
                    })
                if len(items) < page_size:
                    break
                page += 1
                time.sleep(0.5)
            except Exception as e:
                print(f"  东方财富接口失败: {e}")
                break
        return managers

    # ==================== 2. 检测新报告 ====================

    def detect_new_reports(self, managers):
        """检测自上次更新以来的新报告"""
        print("\n[2/6] 检测新报告...")

        last_update = self.meta.get('maintenance', {}).get('monthlyUpdate', None)
        if last_update:
            since_date = datetime.strptime(last_update, '%Y-%m-%d').date()
        else:
            # 默认检测最近3个月
            from dateutil.relativedelta import relativedelta
            since_date = (date.today() - relativedelta(months=3))

        print(f"  检测 {since_date} 以来的新报告...")

        new_reports = []
        fund_codes = set([m.get('current_fund_code') for m in managers if m.get('current_fund_code')])

        try:
            import akshare as ak
            for i, fund_code in enumerate(fund_codes):
                if not fund_code or fund_code == '0':
                    continue
                try:
                    df = ak.fund_announcement_report_em(symbol=fund_code)
                    for _, row in df.iterrows():
                        title = str(row.get('公告标题', ''))
                        report_date = str(row.get('公告日期', ''))
                        if not report_date or report_date == 'nan':
                            continue
                        try:
                            rdate = datetime.strptime(report_date, '%Y-%m-%d').date()
                            if rdate >= since_date and self._is_target_report(title):
                                new_reports.append({
                                    'fund_code': fund_code,
                                    'title': title,
                                    'date': report_date,
                                    'type': self._detect_report_type(title)
                                })
                        except Exception:
                            continue
                except Exception:
                    continue
                if (i + 1) % 100 == 0:
                    print(f"  已检测 {i+1}/{len(fund_codes)} 只基金...")
                time.sleep(0.1)
        except Exception as e:
            print(f"  报告检测异常: {e}")

        print(f"  发现 {len(new_reports)} 份新报告")
        return new_reports

    def _is_target_report(self, title):
        """判断是否为目标报告类型"""
        for keywords in self.REPORT_TYPES.values():
            if any(kw in title for kw in keywords):
                return True
        return False

    def _detect_report_type(self, title):
        """检测报告类型"""
        if '年度报告' in title or '年报' in title:
            return 'annual'
        if '半年度' in title or '半年报' in title:
            return 'semi'
        if '季度' in title or '季报' in title:
            return 'quarterly'
        return 'other'

    # ==================== 3. 爬取报告观点 ====================

    def scrape_report_opinions(self, new_reports):
        """爬取新报告的投资观点"""
        print("\n[3/6] 爬取报告观点...")

        if not new_reports:
            print("  无新报告，跳过")
            return

        opinions = []
        # 按基金去重，只取最新一份报告
        fund_reports = {}
        for r in new_reports:
            fc = r['fund_code']
            if fc not in fund_reports or r['date'] > fund_reports[fc]['date']:
                fund_reports[fc] = r

        for i, (fund_code, report) in enumerate(fund_reports.items()):
            try:
                opinion = self._scrape_single_report_opinion(fund_code, report)
                if opinion:
                    opinions.extend(opinion)
            except Exception as e:
                continue
            if (i + 1) % 50 == 0:
                print(f"  已处理 {i+1}/{len(fund_reports)} 只基金...")
            time.sleep(0.2)

        # 更新 manager_views.json
        if opinions:
            self._update_manager_views(opinions)
        print(f"  获取到 {len(opinions)} 条新观点")

    def _scrape_single_report_opinion(self, fund_code, report):
        """爬取单只基金的报告观点"""
        opinions = []

        # 构造天天基金报告URL
        report_type = report['type']
        if report_type == 'annual':
            url = f"https://fundf10.eastmoney.com/NDBG_{fund_code}.html"
        else:
            url = f"https://fundf10.eastmoney.com/JJJ_{fund_code}.html"

        try:
            if self.session is None:  # v9.0: requests 未装则降级
                import requests as _requests
                self.session = _requests.Session()
                self.session.headers.update({'User-Agent': 'Mozilla/5.0'})
            resp = self.session.get(url, timeout=10)
            try:
                from bs4 import BeautifulSoup  # v9.0: 惰性 import
            except ImportError:
                return []
            soup = BeautifulSoup(resp.text, 'html.parser')
            content = soup.find('div', class_='txt_content') or soup.find('div', id='ContentBody')
            if not content:
                return opinions

            text = content.get_text()

            # 提取投资观点段落
            patterns = [
                r'后[市下][展看法][：:]*\s*([^\n]{50,})',
                r'投资[策略思路][：:]*\s*([^\n]{50,})',
                r'运作[分析][：:]*\s*([^\n]{50,})',
                r'基金[经理认为]+[：:]*\s*([^\n]{50,})',
            ]

            for pattern in patterns:
                matches = re.findall(pattern, text)
                for match in matches:
                    clean_text = self._clean_text(match)
                    if len(clean_text) > 20:
                        opinions.append({
                            'fund_code': fund_code,
                            'report_title': report['title'],
                            'report_date': report['date'],
                            'report_type': report['type'],
                            'views': clean_text,
                            'source': '天天基金网'
                        })
                        break

        except Exception as e:
            pass

        return opinions

    def _clean_text(self, text):
        """清理文本，去除模板痕迹"""
        text = re.sub(r'^[\s,，、]+', '', text)
        text = re.sub(r'[\s,，、]+$', '', text)
        text = re.sub(r'我们的想法比较简单[，,]?', '', text)
        text = re.sub(r'我觉得吧[，,]?', '', text)
        return text.strip()

    def _update_manager_views(self, new_opinions):
        """更新manager_views.json"""
        views_path = os.path.join(self.data_dir, 'manager_views.json')
        existing = {'views': [], 'meta': {}}

        if os.path.exists(views_path):
            try:
                with open(views_path, 'r', encoding='utf-8') as f:
                    existing = json.load(f)
            except (json.JSONDecodeError, OSError, ValueError, KeyError, TypeError):
                pass

        existing_views = existing.get('views', [])
        # 去重
        seen = set()
        unique_opinions = []
        for o in new_opinions:
            key = (o.get('fund_code'), o.get('report_date'))
            if key not in seen:
                seen.add(key)
                unique_opinions.append(o)

        existing_views.extend(unique_opinions)

        existing['views'] = existing_views
        existing['meta'] = {
            'total_views': len(existing_views),
            'last_update': datetime.now().strftime('%Y-%m-%d'),
            'source': '天天基金网'
        }

        with open(views_path, 'w', encoding='utf-8') as f:
            json.dump(existing, f, ensure_ascii=False, indent=2)
        print(f"  manager_views.json 已更新")

    # ==================== 4. 爬取经理新闻 ====================

    def scrape_manager_news(self, managers):
        """爬取TOP 100基金经理新闻"""
        print("\n[4/6] 爬取基金经理新闻...")

        # 取管理规模TOP 100
        top_managers = sorted(managers, key=lambda x: x.get('total_scale', 0), reverse=True)[:100]
        print(f"  采集TOP {len(top_managers)} 基金经理新闻")

        all_news = []
        for i, m in enumerate(top_managers):
            try:
                news = self._scrape_single_manager_news(m)
                if news:
                    all_news.append(news)
            except Exception:
                continue
            if (i + 1) % 20 == 0:
                print(f"  已处理 {i+1}/{len(top_managers)} 位经理...")
            time.sleep(0.3)

        # 保存
        if all_news:
            news_path = os.path.join(self.data_dir, 'manager_news.json')
            with open(news_path, 'w', encoding='utf-8') as f:
                json.dump({'news': all_news, 'meta': {
                    'total': len(all_news),
                    'last_update': datetime.now().strftime('%Y-%m-%d'),
                    'source': '天天基金网'
                }}, f, ensure_ascii=False, indent=2)
            print(f"  manager_news.json 已保存 {len(all_news)} 条")

    def _scrape_single_manager_news(self, manager):
        """爬取单个经理的新闻"""
        name = manager.get('name', '')
        manager_id = manager.get('manager_id', '')

        if not name:
            return None

        news_item = {
            'manager_id': manager_id,
            'manager_name': name,
            'company': manager.get('company_name', ''),
            'articles': []
        }

        # 搜索天天基金网新闻
        try:
            search_url = "https://so.eastmoney.com/Search/GetSearchHost"
            params = {'keyword': f"{name} 基金经理", 'type': '0', 'pageindex': 1, 'pagesize': 5}
            resp = self.session.get(search_url, params=params, timeout=10)
            data = resp.json()
            if data.get('data'):
                for item in data['data'].get('headlines', []):
                    news_item['articles'].append({
                        'title': item.get('Title', ''),
                        'date': item.get('PublishTime', '')[:10] if item.get('PublishTime') else '',
                        'summary': item.get('Summary', '')[:100]
                    })
        except (json.JSONDecodeError, OSError, ValueError, KeyError, TypeError):
            pass

        return news_item if news_item['articles'] else None

    # ==================== 5. 蒸馏字段 ====================

    def redistill_fields(self, managers):
        """重新蒸馏投资风格、股票池、债券池、基金池、基础设施投资"""
        print("\n[5/6] 重新蒸馏字段...")

        # 加载持仓数据
        holdings_map = self._load_holdings()

        # 加载外部数据
        external_map = self._load_external_data()

        distilled = []
        for m in managers:
            mid = m.get('manager_id', '')
            fund_code = m.get('current_fund_code', '')

            # 获取持仓
            holdings = holdings_map.get(fund_code, [])

            # 投资风格计算
            investment_style = self._calculate_style(holdings, m)

            # 股票池提取
            stock_pool = self._extract_stock_pool(holdings)

            # 债券池提取
            bond_pool = self._extract_bond_pool(holdings)

            # 基金池（同一经理管理的其他基金）
            fund_pool = self._extract_fund_pool(m, managers)

            # 基础设施投资检测
            infrastructure = self._detect_infrastructure(holdings)

            # 行业分布
            sectors = self._detect_sectors(stock_pool)

            # 合并字段
            d = m.copy()
            d['investment_style'] = investment_style
            d['stock_pool'] = stock_pool
            d['bond_pool'] = bond_pool
            d['fund_pool'] = fund_pool
            d['infrastructure_investment'] = infrastructure
            d['sectors'] = sectors
            d['sector_description'] = f"重点布局{sectors[0]}行业" if sectors else "均衡配置"

            # 外部数据
            ext = external_map.get(fund_code, {})
            if ext:
                d['rating'] = ext.get('rating')
                d['risk_metrics'] = ext.get('risk_metrics')
                d['profit_probability'] = ext.get('profit_probability')

            # 阶段判断
            tenure = m.get('tenure_days', 0)
            if tenure < 180:
                d['fund_stage'] = '萌芽期'
            elif tenure < 365 * 2:
                d['fund_stage'] = '成长期'
            elif tenure < 365 * 5:
                d['fund_stage'] = '成熟期'
            else:
                d['fund_stage'] = '老牌期'

            d['stage_description'] = self._get_stage_desc(d['fund_stage'])
            d['investment_advice'] = self._get_advice(investment_style)
            d['risk_warning'] = self._get_warning(investment_style)
            d['suitable_investors'] = self._get_suitable(investment_style)
            d['investment_period'] = self._get_period(investment_style)
            d['strengths'] = self._get_strengths(d)

            distilled.append(d)

        print(f"  蒸馏完成 {len(distilled)} 条记录")
        return distilled

    def _load_holdings(self):
        """加载持仓数据（统一经 load_holdings 解码各历史格式）"""
        holdings_map = {}
        try:
            for h in load_holdings():
                fc = h.get('fund_code', '')
                if fc not in holdings_map:
                    holdings_map[fc] = []
                holdings_map[fc].append(h)
        except (ValueError, KeyError, TypeError):
            pass
        return holdings_map

    def _load_external_data(self):
        """加载外部数据（external_data.json 各分区为嵌套列式压缩，需分别解码）"""
        external_map = {}
        try:
            path = os.path.join(self.data_dir, 'external_data.json')
            if not os.path.exists(path):
                return external_map
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            def _section(name):
                sec = data.get(name, [])
                if is_columnar(sec):
                    return _decode_columnar(sec).get('items', [])
                return sec if isinstance(sec, list) else []

            for r in _section('ratings'):
                fc = r.get('fund_code', '')
                if fc:
                    external_map[fc] = {'rating': r}
            for a in _section('analysis'):
                fc = a.get('fund_code', '')
                if fc and fc in external_map:
                    external_map[fc]['risk_metrics'] = {
                        'sharpe_ratio': a.get('sharpe_ratio'),
                        'max_drawdown': a.get('max_drawdown'),
                        'annual_volatility': a.get('annual_volatility')
                    }
            for p in _section('profit_probability'):
                fc = p.get('fund_code', '')
                period = p.get('holding_period', '')
                if fc and fc in external_map:
                    if '满1年' in period:
                        external_map[fc]['profit_probability'] = external_map[fc].get('profit_probability', {})
                        external_map[fc]['profit_probability']['1year'] = {
                            'prob': p.get('profit_probability'),
                            'avg_return': p.get('avg_return')
                        }
        except (json.JSONDecodeError, OSError, ValueError, KeyError, TypeError, AttributeError):
            pass
        return external_map

    def _calculate_style(self, holdings, manager):
        """从持仓计算投资风格"""
        # 如果有真实持仓数据，基于集中度和行业判断
        if holdings:
            total_weight = sum(h.get('weight', 0) for h in holdings)
            count = len(holdings)
            avg_weight = total_weight / count if count > 0 else 0

            # 高集中度+成长行业 = 成长型
            if count <= 8 and avg_weight > 5:
                # 进一步判断行业
                sectors = self._detect_sectors([h.get('stock_name', '') for h in holdings])
                if any(s in sectors for s in ['科技', '新能源', '医药']):
                    return '成长型'

            # 低集中度+价值行业 = 价值型
            if count >= 12 and avg_weight < 4:
                return '价值型'

        # 回退：从基金名猜
        fund_name = manager.get('current_fund_name', '')
        if any(kw in fund_name for kw in ['成长', '积极', '激进', '科技', '创新']):
            return '成长型'
        if any(kw in fund_name for kw in ['价值', '稳健', '红利', '低波']):
            return '价值型'
        return '均衡型'

    def _extract_stock_pool(self, holdings):
        """提取股票池"""
        stocks = []
        seen = set()
        for h in holdings:
            name = h.get('stock_name', '')
            if name and name not in seen:
                seen.add(name)
                stocks.append(name)
        return stocks[:20]  # 最多20只

    def _extract_bond_pool(self, holdings):
        """提取债券池"""
        bonds = {'国债': [], '企业债': [], '可转债': []}
        seen = {'国债': set(), '企业债': set(), '可转债': set()}

        for h in holdings:
            name = h.get('stock_name', '')
            if not name:
                continue
            if '国债' in name and name not in seen['国债']:
                bonds['国债'].append(name)
                seen['国债'].add(name)
            elif any(kw in name for kw in ['转债', '可转债']):
                if name not in seen['可转债']:
                    bonds['可转债'].append(name)
                    seen['可转债'].add(name)
            elif any(kw in name for kw in ['债', '券']):
                if name not in seen['企业债']:
                    bonds['企业债'].append(name)
                    seen['企业债'].add(name)

        return bonds

    def _extract_fund_pool(self, manager, all_managers):
        """提取基金池（同一经理管理的其他基金）"""
        manager_id = manager.get('manager_id', '')
        manager_name = manager.get('name', '')
        fund_pool = []

        for m in all_managers:
            if m.get('manager_id') == manager_id and m.get('name') == manager_name:
                fc = m.get('current_fund_code', '')
                fn = m.get('current_fund_name', '')
                if fc and fc != manager.get('current_fund_code'):
                    fund_pool.append({'fund_code': fc, 'fund_name': fn})

        return fund_pool[:5]  # 最多5只

    def _detect_infrastructure(self, holdings):
        """检测基础设施投资"""
        infra_keywords = ['高速', '铁路', '公路', '桥梁', '港口', '机场', '水电', '燃气', '供暖', 'REITs', '仓储', '物流']
        for h in holdings:
            name = h.get('stock_name', '')
            if any(kw in name for kw in infra_keywords):
                return True
        return False

    def _detect_sectors(self, stock_names):
        """从股票名检测行业"""
        sector_keywords = {
            '科技': ['科技', '软', '硬', '电子', '通信', '计算机', '半导体', '芯片', 'AI', '人工智能'],
            '新能源': ['新能源', '光伏', '锂', '电池', '储能', '电动车', '汽车'],
            '消费': ['酒', '食品', '饮料', '家电', '商贸', '旅游', '酒店'],
            '医药': ['医药', '医疗', '生物', '疫苗', '中药', '健康'],
            '金融': ['银行', '保险', '券商', '信托', '地产', '物业'],
            '制造': ['机械', '化工', '材料', '军工', '航空', '制造', '设备'],
        }

        detected = []
        for name in stock_names:
            for sector, keywords in sector_keywords.items():
                if any(kw in name for kw in keywords) and sector not in detected:
                    detected.append(sector)
        return detected[:3]

    def _get_advice(self, style):
        advices = {
            '成长型': "波动较大，建议闲置资金配置，避免追涨杀跌，长期持有效果更佳。",
            '价值型': "建议长期持有，享受复利增长，适合养老金、教育金规划。",
            '均衡型': "不赌单一方向，适应不同市场环境，适合定投和一次性配置。"
        }
        return advices.get(style, '')

    def _get_warning(self, style):
        warnings = {
            '成长型': "高波动品种，短期回撤可能较大，请评估自身风险承受能力。",
            '价值型': "注意估值波动，价值回归需要时间，需保持耐心。",
            '均衡型': "均衡配置不等于无风险，市场大幅下跌时仍可能受损。"
        }
        return warnings.get(style, '')

    def _get_suitable(self, style):
        suitable = {
            '成长型': '积极型投资者，能承受较大波动，追求长期高收益',
            '价值型': '稳健型投资者，注重风险控制，追求稳定回报',
            '均衡型': '平衡型投资者，希望收益与风险平衡'
        }
        return suitable.get(style, '平衡型投资者')

    def _get_period(self, style):
        periods = {
            '成长型': '3-5年以上',
            '价值型': '1-3年',
            '均衡型': '2-5年'
        }
        return periods.get(style, '3年')

    def _get_stage_desc(self, stage):
        descs = {
            '萌芽期': '新基金，建仓期运作，需要时间验证',
            '成长期': '风格形成，业绩弹性较大',
            '成熟期': '业绩稳定，风格清晰',
            '老牌期': '历经牛熊，长期稳健'
        }
        return descs.get(stage, '')

    def _get_strengths(self, m):
        strengths = []
        tenure = m.get('tenure_days', 0)
        if tenure > 365 * 5:
            strengths.append(f"{tenure//365}年投资经验")
        elif tenure > 365 * 3:
            strengths.append(f"近{tenure//365}年任职经验")
        style = m.get('investment_style', '均衡型')
        if style == '成长型':
            strengths.append("成长投资能力")
        elif style == '价值型':
            strengths.append("价值挖掘能力")
        else:
            strengths.append("均衡配置能力")
        return strengths[:3]

    # ==================== 6. 保存数据 ====================

    def save_data(self, managers_distilled, companies):
        """保存所有数据"""
        print("\n[6/6] 保存数据...")

        # 保存原始采集数据
        raw_path = os.path.join(self.data_dir, '全市场基金经理名录_天天基金.json')
        raw_data = [[
            m.get('raw_id', ''),
            m.get('name', ''),
            '',
            m.get('company_name', ''),
            ','.join([f.get('fund_code', '') for f in m.get('funds', [])]) if m.get('funds') else '',
            ','.join([f.get('fund_name', '') for f in m.get('funds', [])]) if m.get('funds') else '',
            str(m.get('tenure_days', 0)),
            m.get('best_return', ''),
            m.get('current_fund_code', ''),
            m.get('current_fund_name', ''),
            '',
            ''
        ] for m in managers_distilled]
        with open(raw_path, 'w', encoding='utf-8') as f:
            json.dump({'raw': raw_data, 'meta': {
                'total_count': len(raw_data),
                'last_update': datetime.now().strftime('%Y-%m-%d'),
                'source': '天天基金网'
            }}, f, ensure_ascii=False, indent=2)
        print(f"  原始数据: {raw_path}")

        # 保存蒸馏后经理数据（v9.0: 用 db_format 统一列式格式，查询工具可读）
        managers_path = os.path.join(self.data_dir, 'fund_managers_distilled.json')
        from data_collection.db_format import write_managers_distilled
        cols = list(managers_distilled[0].keys()) if managers_distilled else None
        write_managers_distilled(managers_path, managers_distilled,
                                 meta={'total_count': len(managers_distilled),
                                       'last_update': datetime.now().strftime('%Y-%m-%d'),
                                       'source': '天天基金网'},
                                 columns=cols)
        print(f"  经理数据: {managers_path} ({len(managers_distilled)}人)")

        # 保存公司数据
        companies_path = os.path.join(self.data_dir, 'fund_companies_distilled.json')
        try:
            with open(companies_path, 'r', encoding='utf-8') as f:
                existing = json.load(f)
            # 兼容三种历史格式: 纯数组 / {'companies':[...]} / {'items':[...]}(列存解码后)
            if isinstance(existing, list):
                prev = existing
            elif isinstance(existing, dict):
                prev = existing.get('companies') or existing.get('items') or []
            else:
                prev = []
            existing_companies = {c.get('name'): c for c in prev if isinstance(c, dict)}
            for c in companies:
                name = c.get('name')
                if name in existing_companies:
                    existing_companies[name].update(c)
                else:
                    existing_companies[name] = c
            companies = list(existing_companies.values())
        except (json.JSONDecodeError, OSError, ValueError, KeyError, TypeError, AttributeError):
            pass

        # v9.0: 用 db_format 统一列式格式（查询工具可读）
        from data_collection.db_format import write_companies_distilled
        cols = list(companies[0].keys()) if companies else None
        write_companies_distilled(companies_path, companies,
                                  meta={'total_count': len(companies),
                                        'last_update': datetime.now().strftime('%Y-%m-%d'),
                                        'source': '天天基金网'},
                                  columns=cols)
        print(f"  公司数据: {companies_path} ({len(companies)}家)")

    def collect_companies(self, managers):
        """从经理数据提取公司"""
        company_map = {}
        for m in managers:
            company_name = m.get('company_name', '')
            if not company_name:
                continue
            if company_name not in company_map:
                company_map[company_name] = {
                    'name': company_name,
                    'manager_count': 0,
                    'total_scale': 0,
                    'manager_ids': []
                }
            company_map[company_name]['manager_count'] += 1
            company_map[company_name]['total_scale'] += m.get('total_scale', 0)
            mid = m.get('manager_id')
            if mid:
                company_map[company_name]['manager_ids'].append(mid)

        return list(company_map.values())

    # ==================== 主流程 ====================

    def run(self, force=False):
        """执行月度更新"""
        today = date.today()
        first_workday = self.get_first_workday_of_month(today.year, today.month)

        print("=" * 60)
        print("基金经理数据月度更新 v2.0")
        print(f"日期: {today.strftime('%Y-%m-%d')} ({today.strftime('%A')})")
        print(f"本月第一个工作日: {first_workday.strftime('%Y-%m-%d')}")
        print("=" * 60)

        if not force and not self.is_first_workday():
            print(f"\n今天不是本月第一个工作日，跳过")
            print(f"下次更新: {first_workday}")
            return

        start_time = time.time()

        try:
            # 1. 采集经理名单
            managers_raw = self.collect_all_managers()

            if not managers_raw:
                print("采集失败")
                return

            # 按经理去重
            manager_map = {}
            for m in managers_raw:
                mid = m.get('manager_id', '')
                if not mid:
                    continue
                if mid not in manager_map:
                    m['funds'] = []
                    manager_map[mid] = m
                fc = m.get('current_fund_code', '')
                fn = m.get('current_fund_name', '')
                if fc and fc not in [f.get('fund_code') for f in manager_map[mid].get('funds', [])]:
                    manager_map[mid].setdefault('funds', []).append({'fund_code': fc, 'fund_name': fn})

            managers = list(manager_map.values())
            print(f"去重后: {len(managers)} 位基金经理")

            # 2. 检测新报告
            new_reports = self.detect_new_reports(managers)

            # 3. 爬取报告观点
            self.scrape_report_opinions(new_reports)

            # 4. 爬取经理新闻
            self.scrape_manager_news(managers)

            # 5. 重新蒸馏字段
            managers_distilled = self.redistill_fields(managers)

            # 6. 提取公司
            companies = self.collect_companies(managers_distilled)

            # 7. 保存
            self.save_data(managers_distilled, companies)

            # 更新元数据
            self.meta['maintenance'] = self.meta.get('maintenance', {})
            self.meta['maintenance']['lastUpdate'] = datetime.now().strftime('%Y-%m-%d')
            self.meta['maintenance']['monthlyUpdate'] = datetime.now().strftime('%Y-%m-%d')
            self.save_meta()

            elapsed = time.time() - start_time
            print(f"\n更新完成! 耗时: {elapsed:.1f}秒")

        except Exception as e:
            print(f"\n更新异常: {e}")
            traceback.print_exc()


def main():
    updater = MonthlyUpdater()
    force = '--force' in sys.argv or '-f' in sys.argv
    updater.run(force=force)


if __name__ == "__main__":
    main()

