"""
基金经理邀请互动引擎 v2.0
从4200+基金经理中匹配合适的为用户答疑
支持根据用户持仓基金自动邀请对应基金经理
"""

import json
import random
from datetime import datetime
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
DATA_DIR = SCRIPT_DIR.parent.parent / "data"

import sys as _sys
_sys.path.insert(0, str(SCRIPT_DIR.parent))
from fund_advisor_paths import load_json_data, load_holdings  # noqa: E402


class InvitationEngine:
    """基金经理邀请互动引擎"""

    def __init__(self, data_dir=None):
        self.data_dir = data_dir or DATA_DIR
        self.managers_db = {}
        self.companies_db = {}
        self.funds_db = {}
        self.views_db = {}
        self._load_data()

    def _load_data(self):
        """加载数据（fund_managers/fund_companies 为列式压缩，统一经 load_json_data 解码）"""
        try:
            data = load_json_data('fund_managers_distilled.json')
            for m in data.get('items', data.get('managers', [])):
                name = m.get('name', '')
                if name:
                    # 派生 tenure_years，供筛选条件使用
                    if 'tenure_years' not in m:
                        try:
                            m['tenure_years'] = round(float(m.get('tenure_days') or 0) / 365, 1)
                        except (TypeError, ValueError):
                            m['tenure_years'] = 0
                    self.managers_db[name] = m
                # 也按基金代码建立索引
                fund_code = m.get('current_fund_code', '')
                if fund_code:
                    self.funds_db[fund_code] = m
        except Exception:
            pass

        try:
            data = load_json_data('fund_companies_distilled.json')
            for c in data.get('items', data.get('companies', [])):
                company_name = c.get('name', '')
                if company_name:
                    self.companies_db[company_name] = c
        except Exception:
            pass

        try:
            views_path = self.data_dir / 'manager_views.json'
            if views_path.exists():
                with open(views_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.views_db = data.get('views', [])
        except Exception:
            self.views_db = []

    def find_managers(self, criteria: dict = None, top_n: int = 5) -> list:
        """
        根据条件查找基金经理

        Args:
            criteria: 筛选条件 {
                'sector': str,       # 行业偏好
                'style': str,        # 投资风格
                'company': str,      # 基金公司
                'tenure_years_min': int,  # 最低任职年限
                'scale_min': int     # 最低管理规模
            }
            top_n: 返回数量

        Returns:
            list: 匹配的基金经理列表
        """
        if criteria is None:
            criteria = {}

        results = []

        for name, m in self.managers_db.items():
            # 筛选条件
            if criteria.get('sector'):
                sector = m.get('sector_description', '')
                if criteria['sector'] not in sector:
                    continue

            if criteria.get('style'):
                style = m.get('investment_style', '')
                if criteria['style'] not in style and criteria['style'] not in ['成长型', '价值型', '均衡型']:
                    continue

            if criteria.get('company'):
                company = m.get('company_name', '')
                if criteria['company'] not in company:
                    continue

            tenure = m.get('tenure_years', 0)
            if criteria.get('tenure_years_min') and tenure < criteria['tenure_years_min']:
                continue

            scale = m.get('total_scale', 0)
            if criteria.get('scale_min') and scale < criteria['scale_min']:
                continue

            results.append(m)

        # 排序：优先任职年限长的
        results.sort(key=lambda x: (
            -x.get('tenure_years', 0),
            -x.get('total_scale', 0) if x.get('total_scale', 0) > 0 else 0
        ))

        return results[:top_n]

    def find_by_holdings(self, holdings: list, top_n: int = 3) -> list:
        """
        根据用户持仓匹配基金经理

        Args:
            holdings: 用户持仓列表
            top_n: 返回数量

        Returns:
            list: 匹配的基金经理
        """
        # 从持仓中提取相关领域
        sectors = set()
        fund_codes = set()

        for h in holdings:
            code = h.get('fund_code')
            if code:
                fund_codes.add(code)

            # 尝试从持仓名称推断行业
            name = h.get('fund_name', '')
            if '消费' in name:
                sectors.add('消费')
            elif '科技' in name or '创新' in name:
                sectors.add('科技')
            elif '医药' in name:
                sectors.add('医药')
            elif '新能源' in name or '汽车' in name:
                sectors.add('新能源')
            elif '金融' in name or '银行' in name:
                sectors.add('金融')

        # 查找相关经理
        managers = []
        seen_companies = set()

        for sector in sectors:
            criteria = {'sector': sector}
            matched = self.find_managers(criteria, top_n=3)

            for m in matched:
                company = m.get('company_name', '')
                if company not in seen_companies:
                    managers.append(m)
                    seen_companies.add(company)

        # 如果不够，从热门经理补充
        if len(managers) < top_n:
            more = self.find_managers({'tenure_years_min': 3}, top_n=top_n * 2)
            for m in more:
                if len(managers) >= top_n:
                    break
                company = m.get('company_name', '')
                if company not in seen_companies:
                    managers.append(m)
                    seen_companies.add(company)

        return managers[:top_n]

    def get_manager_info(self, manager_name: str = None, fund_code: str = None) -> dict:
        """获取经理详细信息"""
        if fund_code:
            # 通过基金代码查找
            for name, m in self.managers_db.items():
                if m.get('current_fund_code') == fund_code:
                    return self._format_manager_info(m)
        elif manager_name:
            # 通过名字查找
            matched = self.find_managers({'style': manager_name}, top_n=1)
            if matched:
                return self._format_manager_info(matched[0])

            # 模糊匹配
            for name, m in self.managers_db.items():
                if manager_name in name or name in manager_name:
                    return self._format_manager_info(m)

        return {'error': '未找到该基金经理'}

    def _format_manager_info(self, m: dict) -> dict:
        """格式化经理信息"""
        name = m.get('name', '')
        company = m.get('company_name', '')
        fund_name = m.get('current_fund_name', '')
        fund_code = m.get('current_fund_code', '')
        style = m.get('investment_style', '')
        tenure = m.get('tenure_years', 0)
        sector = m.get('sector_description', '')
        stage = m.get('fund_stage', '')
        stock_pool = m.get('stock_pool', [])
        views = self._get_manager_views(fund_code)

        # 获取今日表现
        today_perf = self._get_today_performance(fund_code)

        # 获取相关新闻
        news = self._get_manager_news(name)

        return {
            'name': name,
            'company': company,
            'fund_name': fund_name,
            'fund_code': fund_code,
            'style': style,
            'tenure_years': tenure,
            'sector': sector,
            'stage': stage,
            'top_holdings': stock_pool[:5] if stock_pool else [],
            'recent_views': views[:3] if views else [],
            'today_performance': today_perf,
            'recent_news': news[:3] if news else [],
            'bio': self._generate_manager_bio(m)
        }

    def _get_manager_views(self, fund_code: str) -> list:
        """获取经理观点（v10.0: 兼容 fc/fund_code、v/views 新旧 schema）"""
        views = []
        for v in self.views_db:
            fc = str(v.get('fc') or v.get('fund_code') or '')
            if fc == str(fund_code):
                views.append({
                    'date': v.get('date', v.get('report_date', '')),
                    'view': (v.get('v') or v.get('views') or '')[:200]
                })
        return views

    def _get_today_performance(self, fund_code: str) -> dict:
        """获取今日表现（模拟）"""
        # 实际应该联网获取
        return {
            'estimate_change': round(random.uniform(-3, 5), 2),
            'source': '估算净值'
        }

    def _get_manager_news(self, manager_name: str) -> list:
        """获取经理相关新闻（模拟）"""
        # 实际应该爬取
        return [
            {'title': f'{manager_name}看好科技板块中长期机会', 'source': '天天基金网', 'date': '2026-05-20'},
            {'title': f'{manager_name}最新调仓路径曝光', 'source': '基金吧', 'date': '2026-05-18'}
        ]

    def _generate_manager_bio(self, m: dict) -> str:
        """生成经理简介"""
        name = m.get('name', '')
        company = m.get('company_name', '')
        tenure = m.get('tenure_years', 0)
        style = m.get('investment_style', '')
        sector = m.get('sector_description', '')

        bio = f"我是{name}，在{company}工作，管理基金已经{round(tenure, 1)}年了。"

        if style == '成长型':
            bio += "我的风格偏成长，喜欢挖掘科技、新能源这些赛道的超额收益。"
        elif style == '价值型':
            bio += "我的风格偏稳健，注重估值安全边际，追求稳稳的幸福。"
        else:
            bio += "我的风格比较均衡，不赌单一方向，涨时跟上跌时控制回撤。"

        if sector:
            sector_clean = sector.replace('重点布局', '').replace('行业', '')
            bio += f"我重点关注{sector_clean}的机会。"

        return bio

    def generate_introduction(self, manager_info: dict) -> str:
        """生成经理自我介绍"""
        bio = manager_info.get('bio', '')
        today = manager_info.get('today_performance', {})
        today_change = today.get('estimate_change', 0)

        lines = []
        lines.append(f"\n{'='*60}")

        if today_change > 0:
            lines.append(f"  📈 {manager_info['name']} 今日预计上涨 {today_change:.2f}%")
        elif today_change < 0:
            lines.append(f"  📉 {manager_info['name']} 今日预计下跌 {abs(today_change):.2f}%")
        else:
            lines.append(f"  ➡️ {manager_info['name']} 今日预计持平")

        lines.append(f"{'='*60}")
        lines.append(f"\n  【自我介绍】")
        lines.append(f"  {bio}")

        style = manager_info.get('style', '')
        if style:
            lines.append(f"\n  投资风格：{style}")

        tenure = manager_info.get('tenure_years', 0)
        if tenure:
            lines.append(f"  从业年限：{tenure:.1f}年")

        stage = manager_info.get('stage', '')
        if stage:
            lines.append(f"  产品阶段：{stage}")

        top_holdings = manager_info.get('top_holdings', [])
        if top_holdings:
            lines.append(f"\n  【十大重仓】")
            lines.append(f"  {', '.join(top_holdings[:5])}...")

        recent_views = manager_info.get('recent_views', [])
        if recent_views:
            lines.append(f"\n  【最新观点】")
            for v in recent_views[:1]:
                content = v.get('view', '')[:150]
                lines.append(f"  「{content}...」")

        lines.append(f"\n{'='*60}")

        return "\n".join(lines)

    def match_managers_for_question(self, user_id: str, question: str,
                                    holdings: list = None) -> list:
        """
        根据用户问题匹配基金经理

        Args:
            user_id: 用户ID
            question: 用户问题
            holdings: 用户持仓（用于匹配相关经理）

        Returns:
            list: 推荐的基金经理列表
        """
        # 分析问题主题
        topic = self._extract_question_topic(question)

        # 根据主题匹配
        if '科技' in question or '半导体' in question or 'AI' in question:
            criteria = {'sector': '科技'}
        elif '消费' in question or '白酒' in question or '食品' in question:
            criteria = {'sector': '消费'}
        elif '医药' in question or '医疗' in question:
            criteria = {'sector': '医药'}
        elif '新能源' in question or '光伏' in question or '汽车' in question:
            criteria = {'sector': '新能源'}
        elif '银行' in question or '金融' in question:
            criteria = {'sector': '金融'}
        else:
            criteria = {}

        # 查找经理
        managers = self.find_managers(criteria, top_n=5)

        # 如果持仓提供了额外线索，优先从持仓相关经理中选择
        if holdings:
            holding_managers = self.find_by_holdings(holdings, top_n=3)
            # 合并
            seen = set()
            combined = []
            for m in holding_managers:
                if m['name'] not in seen:
                    combined.append(m)
                    seen.add(m['name'])
            for m in managers:
                if m['name'] not in seen and len(combined) < 5:
                    combined.append(m)
                    seen.add(m['name'])
            managers = combined

        return managers[:5]

    def _extract_question_topic(self, question: str) -> str:
        """提取问题主题"""
        topics = ['科技', '消费', '医药', '新能源', '金融', '半导体', '白酒', '军工']
        for topic in topics:
            if topic in question:
                return topic
        return ''

    def invite_managers_for_products(self, holdings: list, user_id: str = "") -> str:
        """
        根据用户持有的基金产品自动邀请对应基金经理

        Args:
            holdings: 用户持仓列表 [{fund_code, fund_name}, ...]
            user_id: 用户ID

        Returns:
            邀请话术
        """
        if not holdings:
            return "您还没有持有任何基金，无法为您邀请基金经理。"

        # 根据持仓找到对应的基金经理
        managers_map = {}  # {manager_name: manager_info}

        for holding in holdings:
            fund_code = holding.get('fund_code', '')
            if not fund_code:
                continue

            # 通过基金代码找经理
            manager = self.funds_db.get(fund_code)
            if manager:
                name = manager.get('name', '')
                if name and name not in managers_map:
                    managers_map[name] = {
                        **manager,
                        'user_holding': holding.get('fund_name', '')
                    }
            else:
                # 模糊匹配：尝试从经理名中匹配
                fund_name = holding.get('fund_name', '')
                for mname, m in self.managers_db.items():
                    cf = m.get('current_fund_name', '')
                    if fund_name and (fund_name in cf or cf in fund_name):
                        if mname not in managers_map:
                            managers_map[mname] = {
                                **m,
                                'user_holding': holding.get('fund_name', '')
                            }

        if not managers_map:
            return f"抱歉，无法从您的 {len(holdings)} 只持仓中找到对应的基金经理。"

        managers = list(managers_map.values())

        # 生成邀请话术
        lines = []
        lines.append(f"\n📢 根据您持有的 {len(holdings)} 只基金，我为您邀请了 {len(managers)} 位相关基金经理：")
        lines.append("")

        for i, m in enumerate(managers, 1):
            name = m.get('name', '')
            company = m.get('company_name', '')
            holding_name = m.get('user_holding', '')
            fund = m.get('current_fund_name', '')
            style = m.get('investment_style', '')
            tenure = m.get('tenure_years', 0)

            lines.append(f"{i}. {name} 经理 ({company})")
            lines.append(f"   📌 管理基金：{fund}")
            lines.append(f"   📊 投资风格：{style}")
            lines.append(f"   ⏱️ 任职年限：{tenure:.1f}年")
            lines.append(f"   🏷️ 对应持仓：{holding_name}")

            # 今日表现
            today = self._get_today_performance(m.get('current_fund_code', ''))
            change = today.get('estimate_change', 0)
            if change > 0:
                lines.append(f"   今日：📈 +{change:.2f}%")
            elif change < 0:
                lines.append(f"   今日：📉 {change:.2f}%")
            else:
                lines.append(f"   今日：➡️ 持平")

            lines.append("")

        lines.append("-" * 60)
        lines.append("\n💬 您可以选择以下操作：")
        lines.append("  • '让第1位经理介绍一下他的投资风格'")
        lines.append("  • '让第1位经理介绍一下他的基金'")
        lines.append("  • '他现在持有哪些股票？'")
        lines.append("  • 直接问相关问题，我会帮您匹配最合适的经理回答。")

        return "\n".join(lines)

    def get_manager_self_introduction(self, manager_name: str = None, fund_code: str = None) -> str:
        """
        生成基金经理自我介绍

        Args:
            manager_name: 基金经理名字
            fund_code: 基金代码（二选一）

        Returns:
            自我介绍话术
        """
        manager = None

        if fund_code:
            manager = self.funds_db.get(fund_code)
        elif manager_name:
            # 精确匹配
            manager = self.managers_db.get(manager_name)
            # 模糊匹配
            if not manager:
                for name, m in self.managers_db.items():
                    if manager_name in name or name in manager_name:
                        manager = m
                        break

        if not manager:
            return f"抱歉，未找到名为 '{manager_name or fund_code}' 的基金经理。"

        name = manager.get('name', '')
        company = manager.get('company_name', '')
        fund_name = manager.get('current_fund_name', '')
        fund_code = manager.get('current_fund_code', '')
        style = manager.get('investment_style', '')
        tenure = manager.get('tenure_years', 0)
        sector = manager.get('sector_description', '')
        stage = manager.get('fund_stage', '')

        # 获取持仓
        top_holdings = manager.get('stock_pool', [])
        if not top_holdings:
            top_holdings = self._get_fund_holdings(fund_code)

        # 获取经理观点
        recent_view = self._get_manager_recent_view(fund_code)

        lines = []
        lines.append(f"\n{'='*60}")
        lines.append(f"  🎙️ 基金经理互动时间")
        lines.append(f"{'='*60}")

        # 自我介绍
        lines.append(f"\n👋 大家好，我是{name}。")
        lines.append(f"   我在{company}工作，管理基金已经{round(tenure, 1)}年了。")

        # 投资风格
        if style == '成长型':
            lines.append(f"   我的投资风格偏成长，喜欢挖掘科技、新能源这些赛道的超额收益。")
        elif style == '价值型':
            lines.append(f"   我的投资风格偏稳健，注重估值安全边际，追求稳稳的幸福。")
        else:
            lines.append(f"   我的风格比较均衡，不赌单一方向，涨时跟上跌时控制回撤。")

        # 行业专注
        if sector:
            sector_clean = sector.replace('重点布局', '').replace('行业', '')
            lines.append(f"   我重点关注{sector_clean}方向的机会。")

        # 产品阶段
        if stage:
            stage_desc = {
                '老牌期': '老牌劲旅，经历过市场考验，风格成熟稳健',
                '成熟期': '产品运作成熟，策略稳定，适合长期持有',
                '成长期': '正处于上升期，管理风格积极，追求超额收益'
            }.get(stage, stage)
            lines.append(f"   我管理的产品属于'{stage}'：{stage_desc}。")

        # 基金产品
        lines.append(f"\n📊 我目前管理的代表基金：")
        lines.append(f"   • {fund_name}（{fund_code}）")

        # 持仓信息
        if top_holdings:
            lines.append(f"\n📈 我的前十大重仓股：")
            for i, stock in enumerate(top_holdings[:10], 1):
                if isinstance(stock, dict):
                    lines.append(f"   {i}. {stock.get('name', stock)}")
                else:
                    lines.append(f"   {i}. {stock}")
            lines.append(f"\n   （以上为最近季度披露数据，仅供参考）")

        # 投资目标
        lines.append(f"\n🎯 我的投资目标：")
        if style == '成长型':
            lines.append(f"   追求长期资本增值，在控制回撤的前提下最大化收益。")
        elif style == '价值型':
            lines.append(f"   追求稳定收益，通过基本面分析挖掘被低估的价值。")
        else:
            lines.append(f"   追求稳健的绝对收益，强调风险控制和净值回撤管理。")

        # 投资建议
        advice = manager.get('investment_advice', '')
        if advice:
            lines.append(f"\n💡 给投资者的话：")
            lines.append(f"   {advice}")

        # 最新观点
        if recent_view:
            lines.append(f"\n📝 我的最新市场观点：")
            lines.append(f"   「{recent_view}」")

        lines.append(f"\n{'='*60}")
        lines.append(f"\n💬 您有什么想了解的吗？可以问我：")
        lines.append(f"   • '你的投资风格是什么？'")
        lines.append(f"   • '你现在的持仓有哪些？'")
        lines.append(f"   • '你对科技板块怎么看？'")
        lines.append(f"   • '你管理的产品适合什么样的投资者？'")

        return "\n".join(lines)

    def _get_fund_holdings(self, fund_code: str) -> list:
        """获取基金持仓（统一经 load_holdings 解码各历史格式）"""
        try:
            code = str(fund_code).zfill(6)
            rows = [r for r in load_holdings()
                    if str(r.get('fund_code', '')).zfill(6) == code]
            return [
                {'stock_code': r.get('stock_code', ''), 'stock_name': r.get('stock_name', ''),
                 'weight': r.get('weight', 0)}
                for r in rows[:10]
            ]
        except Exception:
            return []

    def _get_manager_recent_view(self, fund_code: str) -> str:
        """获取经理最近观点（manager_views.json 实际键: fund_code/views）"""
        for view in self.views_db:
            if str(view.get('fund_code', '')).zfill(6) == str(fund_code).zfill(6):
                return view.get('views', '')[:200]
        return ""

    def generate_manager_qa(self, manager_name: str, question: str) -> str:
        """
        生成基金经理回答用户问题

        Args:
            manager_name: 基金经理名字
            question: 用户问题

        Returns:
            回答话术
        """
        manager = self.managers_db.get(manager_name)
        if not manager:
            return f"抱歉，未找到名为 '{manager_name}' 的基金经理。"

        style = manager.get('investment_style', '')
        sector = manager.get('sector_description', '')

        # 分析问题类型，生成对应回答
        if any(kw in question for kw in ['风格', '特点', '怎么样', '投资理念']):
            return self._generate_style_answer(manager)
        elif any(kw in question for kw in ['持仓', '股票', '重仓', '买了什么']):
            return self._generate_holdings_answer(manager)
        elif any(kw in question for kw in ['板块', '行业', '科技', '消费', '医药']):
            return self._generate_sector_answer(manager, question)
        elif any(kw in question for kw in ['目标', '收益', '预期']):
            return self._generate_goal_answer(manager)
        elif any(kw in question for kw in ['风险', '回撤', '亏损']):
            return self._generate_risk_answer(manager)
        else:
            return self._generate_general_answer(manager, question)

    def _generate_style_answer(self, manager: dict) -> str:
        """生成投资风格回答"""
        name = manager.get('name', '')
        style = manager.get('investment_style', '')
        sector = manager.get('sector_description', '')
        tenure = manager.get('tenure_years', 0)

        hedges = ["说实话", "客观讲", "我认为", "跟你讲"]
        hedge = random.choice(hedges)

        lines = [f"【{name}的投资风格介绍】"]
        lines.append(f"\n{hedge}，我的风格是「{style}」。")

        if style == '成长型':
            lines.append(f"我偏好高成长赛道，像科技、新能源这些方向，目标是挖掘赛道里的超额收益。")
        elif style == '价值型':
            lines.append(f"我更注重估值安全边际，喜欢在低估值时买入，追求稳稳的收益。")
        else:
            lines.append(f"我的风格比较均衡，不押注单一方向，涨时跟上指数跌时控制回撤。")

        if sector:
            lines.append(f"\n在行业配置上，我重点关注{sector.replace('重点布局', '')}。")

        lines.append(f"\n我管理基金已经{round(tenure, 1)}年了，经历过市场的牛熊转换，风格比较成熟。")

        return "\n".join(lines)

    def _generate_holdings_answer(self, manager: dict) -> str:
        """生成持仓回答"""
        name = manager.get('name', '')
        fund_code = manager.get('current_fund_code', '')
        holdings = self._get_fund_holdings(fund_code)

        lines = [f"【{name}的持仓情况】"]
        lines.append(f"\n根据最新季度报告，我的前十大重仓股是：")

        if holdings:
            for i, stock in enumerate(holdings[:10], 1):
                if isinstance(stock, dict):
                    lines.append(f"  {i}. {stock.get('name', stock)} ({stock.get('pct', '')}%)")
                else:
                    lines.append(f"  {i}. {stock}")
            lines.append(f"\n持仓仅供参考，不构成投资建议。")
        else:
            lines.append(f"  抱歉，暂时无法获取详细持仓数据。")

        return "\n".join(lines)

    def _generate_sector_answer(self, manager: dict, question: str) -> str:
        """生成板块观点回答"""
        name = manager.get('name', '')
        sector = manager.get('sector_description', '')

        lines = [f"【{name}的市场观点】"]

        # 判断具体板块
        if '科技' in question or '半导体' in question or 'AI' in question:
            lines.append(f"\n关于科技和半导体板块，我认为这是长期确定性很强的方向。")
            lines.append(f"从全球产业链来看，国内科技企业正在快速追赶，国产替代的空间很大。")
            lines.append(f"短期波动在所难免，但中长期我依然看好。")
        elif '消费' in question or '白酒' in question:
            lines.append(f"\n关于消费板块，这是中国经济的基本盘。")
            lines.append(f"短期需求有压力，但龙头企业有品牌溢价，长期逻辑清晰。")
        elif '医药' in question:
            lines.append(f"\n关于医药板块，创新药是我长期看好的方向。")
            lines.append(f"人口老龄化带来持续需求，政策也在鼓励创新。")
        elif '新能源' in question:
            lines.append(f"\n关于新能源，这是全球能源转型的确定性方向。")
            lines.append(f"短期产能有过剩压力，但龙头企业竞争力强，中长期有机会。")
        else:
            lines.append(f"\n关于市场整体，我认为需要关注宏观经济和政策走向。")
            if sector:
                lines.append(f"从我重点关注的{sector.replace('重点布局', '')}来看，")

        lines.append(f"\n以上仅是我个人观点，不构成投资建议。")

        return "\n".join(lines)

    def _generate_goal_answer(self, manager: dict) -> str:
        """生成投资目标回答"""
        name = manager.get('name', '')
        style = manager.get('investment_style', '')

        lines = [f"【{name}的投资目标】"]

        if style == '成长型':
            lines.append(f"\n我的投资目标是追求长期资本增值。")
            lines.append(f"在控制回撤的前提下，尽量捕捉高成长赛道的超额收益。")
            lines.append(f"适合风险承受能力较强、追求长期高收益的投资者。")
        elif style == '价值型':
            lines.append(f"\n我的投资目标是追求稳定绝对收益。")
            lines.append(f"通过基本面分析挖掘被低估的价值，获取稳健回报。")
            lines.append(f"适合追求稳健收益、风险偏好较低的投资者。")
        else:
            lines.append(f"\n我的投资目标是追求稳健的绝对收益。")
            lines.append(f"强调风险控制，避免净值大幅回撤，同时保持一定收益弹性。")
            lines.append(f"适合追求稳健增值的投资者。")

        return "\n".join(lines)

    def _generate_risk_answer(self, manager: dict) -> str:
        """生成风险控制回答"""
        name = manager.get('name', '')
        advice = manager.get('investment_advice', '')
        risk_warning = manager.get('risk_warning', '')

        lines = [f"【{name}的风险控制】"]
        lines.append(f"\n关于风险控制，我是这么做的：")

        if advice:
            lines.append(f"  {advice}")

        if risk_warning:
            lines.append(f"\n⚠️ 风险提示：")
            lines.append(f"  {risk_warning}")

        return "\n".join(lines)

    def _generate_general_answer(self, manager: dict, question: str) -> str:
        """生成通用回答"""
        name = manager.get('name', '')
        fund_name = manager.get('current_fund_name', '')

        lines = [f"【{name}的回答】"]
        lines.append(f"\n您问的这个问题，我可以从我的角度回答一下。")
        lines.append(f"\n我管理{fund_name}，一直坚持自己的投资框架。")
        lines.append(f"\n您可以问我更具体的问题，比如我的投资风格、持仓情况、对某个板块的看法等。")

        return "\n".join(lines)

    def format_invitation(self, managers: list, question: str = None) -> str:
        """格式化邀请信息"""
        if not managers:
            return "抱歉，暂时没有找到合适的基金经理来回答您的问题。"

        lines = []

        if question:
            lines.append(f"\n📢 根据您的问题，我为您邀请了以下基金经理：")
        else:
            lines.append(f"\n📢 我为您邀请了以下基金经理，他们对您的投资方向比较了解：")

        lines.append("")

        for i, m in enumerate(managers, 1):
            name = m.get('name', '')
            company = m.get('company_name', '')
            fund = m.get('current_fund_name', '')
            style = m.get('investment_style', '')

            lines.append(f"{i}. {name} ({company})")
            lines.append(f"   管理基金：{fund}")
            lines.append(f"   投资风格：{style}")

            # 获取今日表现
            today = self._get_today_performance(m.get('current_fund_code', ''))
            change = today.get('estimate_change', 0)
            if change > 0:
                lines.append(f"   今日：📈 +{change:.2f}%")
            elif change < 0:
                lines.append(f"   今日：📉 {change:.2f}%")

            lines.append("")

        lines.append("-" * 60)
        lines.append("\n您想向哪位经理提问？可以告诉我：")
        lines.append("  '问第1位经理：科技板块后续怎么看？'")
        lines.append("  '让第2位经理介绍一下他的投资风格'")
        lines.append("  或者直接描述您的问题，我会帮您匹配最合适的经理。")

        return "\n".join(lines)


def main():
    """测试"""
    engine = InvitationEngine()

    print(f"加载了 {len(engine.managers_db)} 位基金经理")
    print(f"加载了 {len(engine.views_db)} 条经理观点")

    # 测试匹配
    print("\n--- 测试：用户问题关于科技 ---")
    managers = engine.match_managers_for_question(
        'test_user',
        '科技板块后续怎么看？',
        holdings=[{'fund_name': '华夏科技', 'fund_code': '001924'}]
    )
    print(engine.format_invitation(managers, '科技板块后续怎么看？'))

    # 测试经理介绍
    if managers:
        print("\n--- 测试：经理详细介绍 ---")
        info = engine.get_manager_info(manager_name=managers[0].get('name'))
        print(engine.generate_introduction(info))


if __name__ == '__main__':
    main()