"""
定制财经报告生成器 v1.0
生成日报、周报、半月报、月报、季度报告
内容：财经资讯精炼汇总 + 所持有产品分析
"""
import json
from datetime import datetime, timedelta
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
import sys as _sys; _sys.path.insert(0, str(SCRIPT_DIR.parent))
from fund_advisor_paths import DATA_DIR  # noqa: E402


class ReportGenerator:
    """定制财经报告生成器"""

    REPORT_TYPES = {
        'daily': {
            'name': '日报',
            'days': 1,
            'news_count': 5,
            'include_charts': False,
            'depth': 'brief'
        },
        'weekly': {
            'name': '周报',
            'days': 7,
            'news_count': 15,
            'include_charts': True,
            'depth': 'standard'
        },
        'biweekly': {
            'name': '半月报',
            'days': 15,
            'news_count': 20,
            'include_charts': True,
            'depth': 'detailed'
        },
        'monthly': {
            'name': '月报',
            'days': 30,
            'news_count': 30,
            'include_charts': True,
            'depth': 'comprehensive'
        },
        'quarterly': {
            'name': '季度报告',
            'days': 90,
            'news_count': 50,
            'include_charts': True,
            'depth': 'full'
        }
    }

    # v10.0: 报告内容模块（可自由组合）
    MODULES = {
        'news': '财经要闻',
        'holdings': '持仓业绩',
        'manager_views': '基金经理观点',
        'psychology': '客户心理状态',
        'follow': '跟仓信号',
        'allocation': '配置建议',
        'outlook': '市场展望',
        'risk': '风险提示',
    }
    # 各报告类型的默认模块（向后兼容旧行为：news+holdings+outlook+risk）
    DEFAULT_MODULES = {
        'daily': ['news', 'holdings', 'outlook', 'risk'],
        'weekly': ['news', 'holdings', 'outlook', 'risk'],
        'biweekly': ['news', 'holdings', 'manager_views', 'outlook', 'risk'],
        'monthly': ['news', 'holdings', 'manager_views', 'allocation', 'outlook', 'risk'],
        'quarterly': ['news', 'holdings', 'manager_views', 'psychology', 'follow',
                      'allocation', 'outlook', 'risk'],
    }
    # 模板 → 头部/尾部/详细度差异
    TEMPLATES = {
        'standard': {'title': '基金投资', 'footer': True, 'depth_bonus': 0},
        'concise': {'title': '基金投资', 'footer': False, 'depth_bonus': -1},
        'professional': {'title': '基金投资', 'footer': True, 'depth_bonus': 1},
    }

    def __init__(self, data_dir=None):
        self.data_dir = data_dir or DATA_DIR
        self._init_modules()

    def _init_modules(self):
        """初始化依赖模块"""
        self._news_advisor = None
        self._performance_tracker = None
        self._quant_analyzer = None

    @property
    def news_advisor(self):
        if self._news_advisor is None:
            try:
                import sys
                sys.path.insert(0, str(SCRIPT_DIR.parent))
                from news_advisor import NewsAdvisor
                self._news_advisor = NewsAdvisor(data_dir=str(self.data_dir))
            except Exception:
                self._news_advisor = None
        return self._news_advisor

    @property
    def performance_tracker(self):
        if self._performance_tracker is None:
            try:
                import sys
                sys.path.insert(0, str(SCRIPT_DIR.parent))
                from performance_tracker import PerformanceTracker
                self._performance_tracker = PerformanceTracker(data_dir=str(self.data_dir))
            except Exception:
                self._performance_tracker = None
        return self._performance_tracker

    @property
    def quant_analyzer(self):
        if self._quant_analyzer is None:
            try:
                import sys
                sys.path.insert(0, str(SCRIPT_DIR.parent))
                from fund_quant_analyzer import FundQuantAnalyzer
                self._quant_analyzer = FundQuantAnalyzer(data_dir=str(self.data_dir))
            except Exception:
                self._quant_analyzer = None
        return self._quant_analyzer

    def generate_report(self, user_id: str = None, report_type: str = 'weekly',
                        holdings: list = None, include_news: bool = True,
                        modules: list = None, template: str = 'standard',
                        client_id: str = None) -> str:
        """
        生成报告（v10.0: 支持内容模块自由组合与模板选择，旧签名向后兼容）

        Args:
            user_id: 用户ID（用于获取持仓与画像）
            report_type: 报告类型 (daily/weekly/biweekly/monthly/quarterly)
            holdings: 持仓列表（如果不提供，会尝试获取）
            include_news: 是否包含财经新闻（兼容旧参数，等价于 modules 含 'news'）
            modules: 内容模块列表，可选项见 MODULES；
                     缺省使用该报告类型的 DEFAULT_MODULES
            template: 模板 (standard/concise/professional)
            client_id: 客户ID（报告归属，缺省取 user_id）

        Returns:
            str: 格式化报告
        """
        config = self.REPORT_TYPES.get(report_type, self.REPORT_TYPES['weekly'])
        report_name = config['name']
        client_id = client_id or user_id

        # 模块解析（兼容旧 include_news 参数）
        if modules is None:
            modules = list(self.DEFAULT_MODULES.get(report_type, self.DEFAULT_MODULES['weekly']))
            if not include_news and 'news' in modules:
                modules.remove('news')
        unknown = [m for m in modules if m not in self.MODULES]
        if unknown:
            modules = [m for m in modules if m in self.MODULES]
        tpl = self.TEMPLATES.get(template, self.TEMPLATES['standard'])
        effective_depth = self._depth_rank(config['depth']) + tpl['depth_bonus']
        config = dict(config, depth=self._depth_name(effective_depth))

        lines = []

        # 报告头部
        lines.append(self._generate_header(report_type, config, tpl))

        # 各内容模块
        if 'news' in modules:
            lines.append(self._generate_news_section(config))
        if holdings or user_id:
            if 'holdings' in modules:
                lines.append(self._generate_holdings_section(user_id, holdings, config))
            if 'manager_views' in modules:
                lines.append(self._generate_manager_views_section(holdings or [], config))
            if 'psychology' in modules:
                lines.append(self._generate_psychology_section(client_id, config))
            if 'follow' in modules:
                lines.append(self._generate_follow_section(holdings or [], config))
            if 'allocation' in modules:
                lines.append(self._generate_allocation_section(client_id, holdings or [], config))
        elif any(m in modules for m in ('manager_views', 'psychology', 'follow', 'allocation')):
            lines.append("\n  （暂无持仓，跳过持仓相关模块）")
        if 'outlook' in modules:
            lines.append(self._generate_market_outlook(config))
        if 'risk' in modules:
            lines.append(self._generate_risk_warning())
        if tpl['footer']:
            lines.append(self._generate_footer())

        return "\n".join(lines)

    @staticmethod
    def _depth_rank(depth: str) -> int:
        return {'brief': 0, 'standard': 1, 'detailed': 2,
                'comprehensive': 3, 'full': 4}.get(depth, 1)

    @staticmethod
    def _depth_name(rank: int) -> str:
        return {0: 'brief', 1: 'standard', 2: 'detailed',
                3: 'comprehensive', 4: 'full'}.get(max(0, min(rank, 4)), 'standard')

    # ── v10.0 新模块：经理观点 / 心理状态 / 跟仓信号 / 配置建议 ──

    def _generate_manager_views_section(self, holdings: list, config: dict) -> str:
        """持仓基金的基金经理观点（基于季报观点蒸馏）"""
        lines = ["\n" + "-" * 70, "【基金经理观点】", "-" * 70]
        codes = [str(h.get('fund_code', '')).zfill(6) for h in (holdings or [])]
        if not codes:
            lines.append("  （暂无持仓，无法关联经理观点）")
            return "\n".join(lines)
        try:
            import sys as _sys
            _sys.path.insert(0, str(SCRIPT_DIR.parent / 'analysis'))
            from manager_persona import ManagerPersona
            persona_engine = ManagerPersona(data_dir=self.data_dir)
            shown = 0
            for code in codes[:5]:
                persona = persona_engine.build(fund_code=code)
                if not persona:
                    continue
                v = persona['views'][0] if persona['views'] else None
                if v and (v.get('views') or v.get('outlook')):
                    text = (v.get('outlook') or v.get('views') or '').strip()
                    lines.append(f"\n  👤 {persona['name']}（{persona['fund']['name']}）"
                                 f"[{v.get('report_title') or v.get('report_date') or '定期报告'}]")
                    lines.append(f"    {text[:160]}")
                    shown += 1
            if not shown:
                lines.append("  （经理季报观点暂未入库，可运行 view_collector.py 采集）")
        except Exception:
            lines.append("  （经理观点模块暂不可用）")
        return "\n".join(lines)

    def _generate_psychology_section(self, client_id: str, config: dict) -> str:
        """客户心理状态（行为偏差画像）"""
        lines = ["\n" + "-" * 70, "【客户心理状态】", "-" * 70]
        if not client_id:
            lines.append("  （未指定客户，跳过）")
            return "\n".join(lines)
        try:
            import sys as _sys
            _sys.path.insert(0, str(SCRIPT_DIR))
            from behavioral_profile import BehavioralBiasEngine
            eng = BehavioralBiasEngine(data_dir=self.data_dir)
            assessment = eng.assess(client_id=client_id)
            if not assessment.get('data_sources'):
                lines.append(f"  客户「{client_id}」暂无行为画像数据，建议先完成 10 题行为问卷。")
                return "\n".join(lines)
            lines.append(f"  心理类型: {assessment['investor_type']}（{assessment['type_description']}）")
            top = assessment['dominant_biases']
            labels = assessment['bias_labels']
            parts = [f"{labels[k]} {assessment['bias_scores'][k]:.0f}" for k in top]
            lines.append(f"  主要偏差: {'、'.join(parts)}")
            tone = assessment['communication_guide']['tone']
            lines.append(f"  沟通要点: {tone[:120]}")
        except Exception:
            lines.append("  （心理模块暂不可用）")
        return "\n".join(lines)

    def _generate_follow_section(self, holdings: list, config: dict) -> str:
        """跟仓信号（持仓变动/经理变动）"""
        lines = ["\n" + "-" * 70, "【跟仓信号】", "-" * 70]
        codes = [str(h.get('fund_code', '')).zfill(6) for h in (holdings or [])]
        if not codes:
            lines.append("  （暂无持仓，无法生成跟仓信号）")
            return "\n".join(lines)
        try:
            import sys as _sys
            _sys.path.insert(0, str(SCRIPT_DIR.parent / 'analysis'))
            from manager_follower import ManagerFollower
            follower = ManagerFollower(data_dir=self.data_dir)
            result = follower.get_follow_signals(fund_codes=codes)
            sigs = result.get('signals', [])
            if not sigs:
                lines.append(f"  （{result.get('meta', {}).get('quarter', '')} 暂无跟仓信号）")
                return "\n".join(lines)
            level_icon = {'high': '🔴', 'medium': '🟠', 'low': '🟡', 'info': '⚪'}
            for s in sigs[:8]:
                lines.append(f"  {level_icon.get(s.get('level'), '⚪')} "
                             f"{s.get('fund_name', s.get('fund_code'))}: {s.get('message', '')[:110]}")
        except Exception:
            lines.append("  （跟仓模块暂不可用）")
        return "\n".join(lines)

    def _generate_allocation_section(self, client_id: str, holdings: list, config: dict) -> str:
        """配置建议（基于画像/持仓结构）"""
        lines = ["\n" + "-" * 70, "【配置建议】", "-" * 70]
        try:
            # 客户画像（若已建立）
            suggestion = None
            if client_id:
                import sys as _sys
                _sys.path.insert(0, str(SCRIPT_DIR))
                from user_profile_manager import UserProfileManager
                mgr = UserProfileManager(data_dir=self.data_dir)
                profile = mgr.get_profile(client_id)
                if profile.get('risk_tolerance') or profile.get('age'):
                    from user_profile_manager import UserQuantitativeAssessment
                    assessor = UserQuantitativeAssessment(data_dir=self.data_dir)
                    r = assessor.assess_investment_profile(
                        age=profile.get('age'),
                        risk_tolerance=profile.get('risk_tolerance'),
                        investment_amount=profile.get('investment_amount'),
                        investment_horizon=profile.get('investment_horizon'))
                    alloc = r['recommended_allocation']
                    suggestion = (f"基于客户画像（{r['risk_level']}，"
                                  f"{r['suitable_style']}），建议股/债/现金配置："
                                  f"{alloc['stocks']}% / {alloc['bonds']}% / {alloc['cash']}%")
            if not suggestion:
                suggestion = ("暂无客户画像，建议先完成风险问卷（score_risk_profile / "
                              "build_allocation_plan 生成三层配置方案）。")
            lines.append(f"  {suggestion}")
        except Exception:
            lines.append("  （配置建议模块暂不可用）")
        return "\n".join(lines)

    def generate_portfolio_report(self, user_id: str, holdings: list,
                                   report_type: str = 'comprehensive',
                                   include_visualization: bool = True) -> str:
        """
        生成持仓组合报告（含可视化）

        Args:
            user_id: 用户ID
            holdings: 持仓列表 [{fund_code, fund_name, shares, cost, current_nav, profit, profit_pct}, ...]
            report_type: 报告类型
            include_visualization: 是否包含可视化

        Returns:
            str: 格式化报告
        """
        lines = []

        # 报告头部
        now = datetime.now()
        lines.append("\n" + "=" * 70)
        lines.append("  投资组合分析报告")
        lines.append("=" * 70)
        lines.append(f"  生成时间: {now.strftime('%Y-%m-%d %H:%M')}")
        lines.append(f"  用户ID: {user_id}")
        lines.append("=" * 70)

        # 持仓概览
        lines.append("\n【持仓概览】")
        total_invested = 0
        total_value = 0
        total_profit = 0

        for h in holdings:
            cost = h.get('cost', 0)
            shares = h.get('shares', 0)
            current_nav = h.get('current_nav', 0)
            profit = h.get('profit', 0)
            profit_pct = h.get('profit_pct', 0)

            invested = cost * shares
            value = current_nav * shares

            total_invested += invested
            total_value += value
            total_profit += profit

        overall_return_pct = (total_profit / total_invested * 100) if total_invested > 0 else 0

        lines.append(f"  持仓数量: {len(holdings)}只")
        lines.append(f"  总投入: ¥{total_invested:,.2f}")
        lines.append(f"  当前总价值: ¥{total_value:,.2f}")
        lines.append(f"  总盈亏: ¥{total_profit:,.2f} ({overall_return_pct:+.2f}%)")

        # 可视化图表
        if include_visualization:
            lines.append("\n【资产配置可视化】")
            lines.append(self._generate_visualization_chart(holdings))

        # 持仓明细
        lines.append("\n【持仓明细】")
        lines.append(f"  {'基金名称':<20} {'代码':<8} {'持仓成本':>10} {'当前净值':>10} {'盈亏':>12} {'收益率':>8}")
        lines.append("  " + "-" * 80)

        for h in holdings:
            fund_name = h.get('fund_name', '')[:18]
            fund_code = h.get('fund_code', '')
            cost = h.get('cost', 0)
            current_nav = h.get('current_nav', 0)
            profit = h.get('profit', 0)
            profit_pct = h.get('profit_pct', 0)

            profit_str = f"¥{profit:+,.2f}"
            pct_str = f"{profit_pct:+.2f}%"

            lines.append(f"  {fund_name:<20} {fund_code:<8} ¥{cost:>9.3f} ¥{current_nav:>9.3f} {profit_str:>11} {pct_str:>7}")

        # 亏损分析
        loss_holdings = [h for h in holdings if h.get('profit', 0) < 0]
        gain_holdings = [h for h in holdings if h.get('profit', 0) >= 0]

        if loss_holdings:
            lines.append("\n【亏损持仓分析】")
            for h in loss_holdings:
                fund_name = h.get('fund_name', '')
                fund_code = h.get('fund_code', '')
                profit_pct = h.get('profit_pct', 0)
                lines.append(f"  ⚠️ {fund_name}（{fund_code}）: 亏损 {abs(profit_pct):.2f}%")

        if gain_holdings:
            lines.append("\n【盈利持仓分析】")
            for h in gain_holdings:
                fund_name = h.get('fund_name', '')
                fund_code = h.get('fund_code', '')
                profit_pct = h.get('profit_pct', 0)
                lines.append(f"  ✅ {fund_name}（{fund_code}）: 盈利 {profit_pct:.2f}%")

        # 基金经理信息
        lines.append("\n【持仓基金基金经理】")
        try:
            from .invitation_engine import InvitationEngine
            engine = InvitationEngine(data_dir=self.data_dir)

            fund_codes = [h.get('fund_code', '') for h in holdings]
            managers = []
            for code in fund_codes:
                if code in engine.funds_db:
                    m = engine.funds_db[code]
                    if m not in managers:
                        managers.append(m)

            for m in managers[:5]:
                name = m.get('name', '')
                company = m.get('company_name', '')
                fund = m.get('current_fund_name', '')
                style = m.get('investment_style', '')
                lines.append(f"  👤 {name} ({company})")
                lines.append(f"      管理基金: {fund}")
                lines.append(f"      投资风格: {style}")
        except Exception:
            lines.append("  （基金经理信息暂时无法获取）")

        # 风险评估
        lines.append("\n【风险评估】")
        if overall_return_pct < -10:
            lines.append("  ⚠️ 当前组合亏损较大，建议适当控制风险")
            lines.append("  💡 建议：分散投资，避免过于集中")
        elif overall_return_pct < 0:
            lines.append("  ⚠️ 当前组合小幅亏损，建议保持观察")
            lines.append("  💡 建议：长期持有，等待市场反弹")
        else:
            lines.append("  ✅ 当前组合盈利，保持稳健")
            lines.append("  💡 建议：适时获利了结，锁定收益")

        # 建议
        lines.append("\n【投资建议】")
        lines.append("  1. 建议分散投资，不要把所有资金放在少数几只基金上")
        lines.append("  2. 设定合理的止盈止损点，避免情绪化操作")
        lines.append("  3. 长期持有优质基金，减少频繁交易")
        lines.append("  4. 关注基金经理变动，及时调整持仓")

        # 报告尾部
        lines.append("\n" + "=" * 70)
        lines.append("  报告仅供参考，不构成投资建议")
        lines.append(f"  生成时间: {now.strftime('%Y-%m-%d %H:%M')}")
        lines.append("=" * 70)

        return "\n".join(lines)

    def _generate_visualization_chart(self, holdings: list) -> str:
        """生成可视化图表（ASCII格式）"""
        lines = []

        # 计算各基金占比
        total_value = sum(h.get('current_nav', 0) * h.get('shares', 0) for h in holdings)

        if total_value == 0:
            return "  （无法计算资产配置）"

        # 饼图数据
        chart_data = []
        for h in holdings:
            value = h.get('current_nav', 0) * h.get('shares', 0)
            pct = value / total_value * 100
            name = h.get('fund_name', '')[:8]
            chart_data.append((name, pct))

        # 排序
        chart_data.sort(key=lambda x: -x[1])

        # 绘制饼图
        symbols = ['●', '○', '◆', '◇', '■', '□', '▲', '△', '★', '☆']

        lines.append("")
        lines.append("  资产配置饼图：")
        lines.append("  " + "-" * 40)

        for i, (name, pct) in enumerate(chart_data[:5]):
            symbol = symbols[i % len(symbols)]
            bar_len = int(pct / 2)
            bar = "█" * bar_len
            lines.append(f"  {symbol} {name:<8} {pct:>5.1f}% {bar}")

        if len(chart_data) > 5:
            remaining = sum(p for _, p in chart_data[5:])
            lines.append(f"  ... 其他 {len(chart_data) - 5} 只基金合计: {remaining:.1f}%")

        # 收益柱状图
        lines.append("")
        lines.append("  收益分布图：")
        lines.append("  " + "-" * 40)

        max_profit = max(abs(h.get('profit', 0)) for h in holdings) if holdings else 1
        scale = 30 / max_profit if max_profit > 0 else 1

        for h in holdings:
            name = h.get('fund_name', '')[:8]
            profit = h.get('profit', 0)

            if profit >= 0:
                bar_len = int(profit * scale)
                bar = "█" * bar_len
                lines.append(f"  {name:<8} │ {bar} +¥{profit:,.0f}")
            else:
                bar_len = int(abs(profit) * scale)
                bar = "▓" * bar_len
                lines.append(f"  {name:<8} │ {bar} -¥{abs(profit):,.0f}")

        return "\n".join(lines)

    def _generate_header(self, report_type: str, config: dict, tpl: dict = None) -> str:
        """生成报告头部（v10.0: 支持模板差异）"""
        now = datetime.now()
        report_name = config['name']
        tpl = tpl or self.TEMPLATES['standard']

        lines = []
        lines.append("\n" + "=" * 70)
        lines.append(f"  {tpl['title']}{report_name}")
        lines.append(f"  生成时间: {now.strftime('%Y-%m-%d %H:%M')}")
        lines.append(f"  报告周期: {self._get_period_text(report_type)}")
        if tpl is self.TEMPLATES.get('professional', tpl):
            lines.append(f"  模板: professional | 模块: {config.get('depth', 'standard')}")
        lines.append("=" * 70)

        return "\n".join(lines)

    def _get_period_text(self, report_type: str) -> str:
        """获取周期描述"""
        period_map = {
            'daily': '今日',
            'weekly': '最近一周',
            'biweekly': '最近半月',
            'monthly': '最近一月',
            'quarterly': '最近一季度'
        }
        return period_map.get(report_type, '最近一周')

    def _generate_news_section(self, config: dict) -> str:
        """生成财经新闻部分"""
        lines = []
        lines.append("\n" + "-" * 70)
        lines.append("【财经要闻】")
        lines.append("-" * 70)

        if self.news_advisor:
            try:
                self.news_advisor.crawl_news()
                news_report = self.news_advisor.format_news_report(limit=config['news_count'])
                lines.append(news_report)
            except Exception as e:
                lines.append(f"  （暂无新闻数据）")
        else:
            lines.append("  （新闻模块不可用）")

        # 今日市场情绪
        if self.news_advisor:
            try:
                sentiment = self.news_advisor.get_market_sentiment()
                sentiment_map = {
                    'bull': '乐观 🟢',
                    'bear': '谨慎 🔴',
                    'neutral': '平稳 ⚪',
                    'uncertain': '不明 ⚪'
                }
                sentiment_text = sentiment_map.get(sentiment, '平稳 ⚪')
                lines.append(f"\n  市场情绪：{sentiment_text}")
            except Exception:
                pass

        return "\n".join(lines)

    def _generate_holdings_section(self, user_id: str, holdings: list, config: dict) -> str:
        """生成持仓分析部分"""
        lines = []
        lines.append("\n" + "-" * 70)
        lines.append("【持仓业绩】")
        lines.append("-" * 70)

        # 获取持仓
        if not holdings and user_id and self.performance_tracker:
            try:
                holdings = self.performance_tracker.get_holdings()
            except Exception:
                holdings = []

        if not holdings:
            lines.append("  暂无持仓记录")
            return "\n".join(lines)

        # 分析持仓
        if self.performance_tracker:
            try:
                analysis = self.performance_tracker.analyze_portfolio_performance()
                if 'error' not in analysis:
                    # 汇总
                    total_value = analysis.get('total_value', 0)
                    total_profit = analysis.get('total_profit', 0)
                    total_profit_pct = analysis.get('total_profit_pct', 0)

                    lines.append(f"\n  总市值: {total_value:.2f}万元")
                    marker = '🟢' if total_profit >= 0 else '🔴'
                    lines.append(f"  总收益: {marker} {total_profit:+.2f}万元 ({total_profit_pct:+.2f}%)")

                    lines.append("\n  持仓明细：")
                    lines.append("  " + "-" * 50)

                    for h in analysis.get('holdings', []):
                        name = h.get('fund_name', '')[:15]
                        code = h.get('fund_code', '')
                        profit_pct = h.get('profit_pct', 0)
                        profit = h.get('profit', 0)
                        days = h.get('holding_days', 0)

                        m = '🟢' if profit_pct > 0 else ('🔴' if profit_pct < 0 else '⚪')
                        lines.append(f"\n  {m} {name:<12} ({code})")
                        lines.append(f"     持有{days}天 | 收益: {profit_pct:+.2f}% ({profit:+.2f}万)")

                    # 量化信号
                    if config['depth'] in ['standard', 'detailed', 'comprehensive', 'full']:
                        lines.append("\n  量化信号：")
                        lines.append("  " + "-" * 50)
                        for h in analysis.get('holdings', [])[:3]:
                            code = h.get('fund_code', '')
                            name = h.get('fund_name', '')[:12]
                            if self.quant_analyzer:
                                try:
                                    result = self.quant_analyzer.analyze_fund(code, client_risk='稳健型')
                                    signal = result.get('signal', 'neutral')
                                    signal_emoji = {'bullish': '📈', 'bearish': '📉', 'neutral': '➡️'}
                                    signal_text = signal_emoji.get(signal, '➡️')
                                    lines.append(f"  {signal_text} {name}: {signal}")
                                except Exception:
                                    pass

            except Exception as e:
                lines.append(f"\n  （持仓分析暂时不可用）")
        else:
            # 简化显示
            for h in holdings:
                name = h.get('fund_name', h.get('fund_code', ''))
                profit_pct = h.get('profit_pct', 0)
                marker = '🟢' if profit_pct > 0 else ('🔴' if profit_pct < 0 else '⚪')
                lines.append(f"\n  {marker} {name}: {profit_pct:+.2f}%")

        return "\n".join(lines)

    def _generate_market_outlook(self, config: dict) -> str:
        """生成市场展望部分（v10.0: 优先数据驱动，无数据时回退内置文本）"""
        lines = []
        lines.append("\n" + "-" * 70)
        lines.append("【市场展望】")
        lines.append("-" * 70)

        # 数据驱动：宏观指标 + 新闻情绪（best effort；指标 data_source=akshare 才算真实数据）
        try:
            import sys as _sys
            _sys.path.insert(0, str(SCRIPT_DIR.parent / 'analysis'))
            from macro_analyzer import MacroAnalyzer
            ma = MacroAnalyzer(data_dir=self.data_dir)
            cond = ma.analyze_macro_conditions()
            is_real = (cond.get('key_indicators', {}).get('gdp', {})
                       .get('data_source') == 'akshare')
            if is_real:
                lines.append(f"\n  【宏观状态】{cond.get('status')}：{cond.get('description')}（综合分 {cond.get('score')}）")
                ki = cond.get('key_indicators', {})
                gdp, cpi, pmi = ki.get('gdp', {}), ki.get('cpi', {}), ki.get('pmi', {})
                lines.append(f"    · GDP同比 {gdp.get('yoy')}%（{gdp.get('status', '')}）")
                lines.append(f"    · CPI同比 {cpi.get('yoy')}%（{cpi.get('status', '')}）")
                pmi_val = (pmi.get('manufacturing') or {}).get('value')
                if pmi_val is not None:
                    lines.append(f"    · PMI {pmi_val}（{'荣枯线以上' if pmi_val >= 50 else '荣枯线以下'}）")
                if cond.get('policy_suggestion'):
                    lines.append(f"    · 政策方向：{cond['policy_suggestion']}")
            if self.news_advisor:
                try:
                    sentiment = self.news_advisor.get_market_sentiment()
                    smap = {'bull': '乐观 🟢', 'bear': '谨慎 🔴', 'neutral': '平稳 ⚪',
                            'uncertain': '不明 ⚪'}
                    lines.append(f"  市场情绪：{smap.get(sentiment, '平稳 ⚪')}")
                except Exception:
                    pass
            if is_real:
                return "\n".join(lines)
        except Exception:
            pass

        # 回退：内置展望文本（保持旧行为）
        depth = config['depth']

        if depth in ['brief']:
            lines.append("\n  市场整体平稳，建议保持均衡配置。")
            lines.append("  关注科技、新能源等成长板块机会。")
        elif depth in ['standard', 'detailed']:
            lines.append("\n  【短期展望】")
            lines.append("  市场整体震荡，建议保持均衡配置。")
            lines.append("  科技板块短期有压力，但长期逻辑不变。")
            lines.append("\n  【行业机会】")
            lines.append("  🚀 科技：AI应用持续发酵，关注国产替代")
            lines.append("  🚀 新能源：渗透率提升，估值合理")
            lines.append("  🚀 消费：估值修复，下半年可能有表现")
            lines.append("\n  【风险提示】")
            lines.append("  ⚠️ 高估值成长股注意回调风险")
            lines.append("  ⚠️ 周期性板块关注宏观数据")
        else:  # comprehensive, full
            lines.append("\n  【宏观环境】")
            lines.append("  货币政策：稳健偏松，流动性合理充裕")
            lines.append("  财政政策：积极发力，基建投资提速")
            lines.append("  外部环境：美联储降息预期，外部压力缓解")
            lines.append("\n  【短期展望】(一周内)")
            lines.append("  市场整体震荡偏强，结构性机会为主")
            lines.append("  科技板块情绪较高，注意追高风险")
            lines.append("\n  【中期展望】(一个月内)")
            lines.append("  政策面预期向好，市场有望企稳")
            lines.append("  消费板块估值修复可期")
            lines.append("\n  【长期展望】(一季度内)")
            lines.append("  经济复苏态势不变，A股中枢有望抬升")
            lines.append("  科技成长仍是主线，关注业绩兑现")
            lines.append("\n  【行业机会】")
            lines.append("  🚀 科技：AI应用、半导体国产替代")
            lines.append("  🚀 新能源：储能、光伏降本")
            lines.append("  🚀 消费：品牌服饰、家电")
            lines.append("  🚀 医药：创新药、医疗器械")
            lines.append("\n  【风险提示】")
            lines.append("  ⚠️ 全球通胀反复风险")
            lines.append("  ⚠️ 地缘政治扰动")
            lines.append("  ⚠️ 高估值赛道回调压力")

        return "\n".join(lines)

    def _generate_risk_warning(self) -> str:
        """生成风险提示"""
        lines = []
        lines.append("\n" + "-" * 70)
        lines.append("【风险提示】")
        lines.append("-" * 70)
        lines.append("\n  以上内容仅供参考，不构成投资建议。")
        lines.append("  投资基金有风险，过往业绩不代表未来表现。")
        lines.append("  请根据自身风险承受能力做出投资决策。")
        lines.append("  市场有风险，投资需谨慎。")
        return "\n".join(lines)

    def _generate_footer(self) -> str:
        """生成报告尾部"""
        lines = []
        lines.append("\n" + "=" * 70)
        lines.append(f"  报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        lines.append("  如需调整报告内容或频率，请告诉我。")
        lines.append("=" * 70 + "\n")
        return "\n".join(lines)

    def save_report(self, user_id: str, report_type: str, content: str = None,
                    modules: list = None, template: str = 'standard') -> str:
        """保存报告到文件（v10.0: 记录 modules/template）"""
        if content is None:
            content = self.generate_report(user_id, report_type, modules=modules,
                                           template=template)

        # 生成文件名
        date_str = datetime.now().strftime('%Y-%m-%d')
        filename = f"report_{report_type}_{date_str}_{user_id or 'general'}.json"

        # 保存
        report_path = self.data_dir / 'reports' / filename
        report_path.parent.mkdir(parents=True, exist_ok=True)

        report_data = {
            'user_id': user_id,
            'report_type': report_type,
            'content': content,
            'modules': modules or list(self.DEFAULT_MODULES.get(
                report_type, self.DEFAULT_MODULES['weekly'])),
            'template': template,
            'generated_at': datetime.now().isoformat()
        }

        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, ensure_ascii=False, indent=2)

        return str(report_path)


def main():
    """测试"""
    generator = ReportGenerator()

    print("=== 报告生成器测试 ===\n")

    # 测试生成各种报告
    for report_type in ['daily', 'weekly', 'monthly', 'quarterly']:
        print(f"\n--- {report_type.upper()} REPORT ---\n")
        report = generator.generate_report(
            user_id='test_user',
            report_type=report_type,
            include_news=True
        )
        print(report[:500] + "..." if len(report) > 500 else report)
        print()


if __name__ == '__main__':
    main()