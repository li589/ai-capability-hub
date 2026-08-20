"""
投资产品业绩跟踪引擎 v1.0
跟踪用户持有基金的业绩表现，提供继续持有或调整建议
"""
import json
import logging
import os
import sys as _sys
import time
import random
from datetime import datetime, date, timedelta
from collections import defaultdict

# 可选依赖：缺失时网络类功能自动降级，不影响本地功能（保持"零依赖"宣称成立）
try:
    import requests
except ImportError:  # pragma: no cover
    requests = None
try:
    from dateutil.rrule import rrule, WEEKLY, MONTHLY, MO, TU
except ImportError:  # pragma: no cover
    rrule = WEEKLY = MONTHLY = MO = TU = None

# 使用相对于脚本位置的路径，增强跨平台兼容性
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(SCRIPT_DIR)), "data")
_sys.path.insert(0, os.path.dirname(SCRIPT_DIR))
from fund_advisor_paths import load_json_data  # noqa: E402

logger = logging.getLogger(__name__)


class PerformanceTracker:
    """业绩跟踪引擎"""

    def __init__(self, data_dir=None):
        self.data_dir = data_dir or DATA_DIR
        self.managers_db = {}
        if requests is not None:
            self.session = requests.Session()
            self.session.headers.update({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Referer': 'https://fund.eastmoney.com/'
            })
        else:
            self.session = None  # requests 未安装：网络功能降级，本地功能不受影响
        self._load_data()

    def _holdings_path(self, user_id=None):
        """获取持仓文件路径，支持按用户隔离存到 CLIENTS_DIR，兼容旧版全局文件"""
        if user_id:
            client_dir = os.path.join(self.data_dir, 'clients', user_id)
            os.makedirs(client_dir, exist_ok=True)
            return os.path.join(client_dir, 'holdings.json')
        return os.path.join(self.data_dir, 'user_holdings.json')

    def _load_data(self):
        """加载本地数据库（列式压缩格式经 load_json_data 透明解码）"""
        try:
            path = os.path.join(self.data_dir, 'fund_managers_distilled.json')
            if os.path.exists(path):
                data = load_json_data(path)
                items = data.get('managers', data.get('items', []))
                for m in items:
                    # shipped 蒸馏数据可能缺少 current_fund_code 字段，
                    # 此时按 manager_id 建索引（无法按基金代码反查，属数据降级，不编造映射）
                    key = m.get('current_fund_code', '') or m.get('manager_id', '')
                    if key:
                        self.managers_db[key] = m
                if not self.managers_db:
                    logger.warning("fund_managers_distilled.json 加载为空（键名/格式不匹配？）")
        except Exception as e:
            logger.warning("加载经理数据失败: %s", e)

    # ==================== 持仓录入 ====================

    def add_holding(self, fund_code, shares, cost, purchase_date=None, user_id=None):
        """
        添加持仓记录

        参数:
            fund_code: 基金代码
            shares: 持有份额
            cost: 成本价（每份）
            purchase_date: 购买日期，格式YYYY-MM-DD

        返回:
            dict: 添加结果
        """
        if purchase_date is None:
            purchase_date = date.today().strftime('%Y-%m-%d')

        # 验证基金是否存在
        fund_info = self.get_fund_info(fund_code)
        if not fund_info:
            return {'success': False, 'error': f'未找到基金: {fund_code}'}

        # 获取当前净值
        nav, nav_date = self.get_latest_nav(fund_code)

        holding = {
            'fund_code': fund_code,
            'fund_name': fund_info.get('fund_name', ''),
            'shares': shares,
            'cost': cost,
            'purchase_date': purchase_date,
            'add_date': datetime.now().strftime('%Y-%m-%d'),
            'nav': nav,
            'nav_date': nav_date
        }

        # 加载或创建持仓文件（支持按用户隔离）
        holdings_path = self._holdings_path(user_id)
        existing = []
        if os.path.exists(holdings_path):
            try:
                with open(holdings_path, 'r', encoding='utf-8') as f:
                    existing = json.load(f)
            except (json.JSONDecodeError, OSError, ValueError, KeyError, TypeError):
                existing = []

        # 检查是否已存在
        for i, h in enumerate(existing):
            if h.get('fund_code') == fund_code and h.get('purchase_date') == purchase_date:
                # 更新
                existing[i] = holding
                updated = True
                break
        else:
            existing.append(holding)
            updated = False

        with open(holdings_path, 'w', encoding='utf-8') as f:
            json.dump(existing, f, ensure_ascii=False, indent=2)

        return {
            'success': True,
            'updated': updated,
            'holding': holding,
            'nav': nav,
            'nav_date': nav_date
        }

    def remove_holding(self, fund_code, purchase_date=None, user_id=None):
        """删除持仓记录"""
        holdings_path = self._holdings_path(user_id)
        if not os.path.exists(holdings_path):
            return {'success': False, 'error': '无持仓记录'}

        with open(holdings_path, 'r', encoding='utf-8') as f:
            existing = json.load(f)

        original_len = len(existing)
        if purchase_date:
            existing = [h for h in existing if not (h.get('fund_code') == fund_code and h.get('purchase_date') == purchase_date)]
        else:
            existing = [h for h in existing if h.get('fund_code') != fund_code]

        if len(existing) == original_len:
            return {'success': False, 'error': '未找到对应记录'}

        with open(holdings_path, 'w', encoding='utf-8') as f:
            json.dump(existing, f, ensure_ascii=False, indent=2)

        return {'success': True, 'removed': original_len - len(existing)}

    def get_holdings(self, user_id=None):
        """获取当前所有持仓（user_id=None 时读取全局文件以兼容旧数据）"""
        holdings_path = self._holdings_path(user_id)
        if os.path.exists(holdings_path):
            try:
                with open(holdings_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, OSError, ValueError, KeyError, TypeError):
                return []
        return []

    # ==================== 反馈设置 ====================

    def set_feedback_preference(self, frequency, notify_time='09:00', enabled=True):
        """
        设置业绩反馈频率和提醒时间

        参数:
            frequency: 'daily' | 'weekly' | 'monthly' | 'none'
            notify_time: 提醒时间，格式HH:MM
            enabled: 是否启用

        返回:
            dict: 设置结果
        """
        settings_path = os.path.join(self.data_dir, 'feedback_settings.json')
        settings = {
            'frequency': frequency,
            'notify_time': notify_time,
            'enabled': enabled,
            'last_feedback': None,
            'next_feedback': self._calculate_next_feedback(frequency, notify_time),
            'updated_at': datetime.now().strftime('%Y-%m-%d %H:%M')
        }

        with open(settings_path, 'w', encoding='utf-8') as f:
            json.dump(settings, f, ensure_ascii=False, indent=2)

        return {'success': True, 'settings': settings}

    def get_feedback_preference(self):
        """获取反馈设置"""
        settings_path = os.path.join(self.data_dir, 'feedback_settings.json')
        if os.path.exists(settings_path):
            try:
                with open(settings_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, OSError, ValueError, KeyError, TypeError):
                pass
        return {'frequency': 'none', 'enabled': False}

    def _calculate_next_feedback(self, frequency, notify_time):
        """计算下次反馈时间"""
        now = datetime.now()
        hour, minute = map(int, notify_time.split(':'))

        if frequency == 'daily':
            next_day = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            if next_day <= now:
                from datetime import timedelta
                next_day += timedelta(days=1)
            return next_day.strftime('%Y-%m-%d %H:%M')

        elif frequency == 'weekly':
            # 每周一早上
            days_ahead = (7 - now.weekday()) % 7
            if days_ahead == 0 and now.weekday() != 0:
                days_ahead = 7
            elif days_ahead == 0:
                days_ahead = 7
            from datetime import timedelta
            next_week = now + timedelta(days=days_ahead)
            return next_week.replace(hour=hour, minute=minute, second=0, microsecond=0).strftime('%Y-%m-%d %H:%M')

        elif frequency == 'monthly':
            # 每月第一个工作日
            year = now.year
            month = now.month + 1
            if month > 12:
                month = 1
                year += 1
            first = date(year, month, 1)
            if rrule is None:
                # dateutil 未安装：退化为"下月1日"（近似，不阻断功能）
                return datetime(year, month, 1, hour, minute).strftime('%Y-%m-%d %H:%M')
            first_weekday = rrule(WEEKLY, dtstart=first, byweekday=MO)[0]
            if first_weekday.weekday() > 4:
                first_weekday = rrule(WEEKLY, dtstart=first, byweekday=TU)[0]
            return first_weekday.replace(hour=hour, minute=minute, second=0, microsecond=0).strftime('%Y-%m-%d %H:%M')

        return None

    def record_feedback_sent(self):
        """记录已发送反馈"""
        settings_path = os.path.join(self.data_dir, 'feedback_settings.json')
        if os.path.exists(settings_path):
            with open(settings_path, 'r', encoding='utf-8') as f:
                settings = json.load(f)
        else:
            settings = {}

        settings['last_feedback'] = datetime.now().strftime('%Y-%m-%d %H:%M')
        settings['next_feedback'] = self._calculate_next_feedback(
            settings.get('frequency', 'none'),
            settings.get('notify_time', '09:00')
        )

        with open(settings_path, 'w', encoding='utf-8') as f:
            json.dump(settings, f, ensure_ascii=False, indent=2)

    def check_feedback_due(self):
        """检查是否该发送反馈"""
        settings = self.get_feedback_preference()
        if not settings.get('enabled') or settings.get('frequency') == 'none':
            return False

        now = datetime.now()
        next_feedback = settings.get('next_feedback')
        if not next_feedback:
            return False

        next_dt = datetime.strptime(next_feedback, '%Y-%m-%d %H:%M')
        return now >= next_dt

    def generate_feedback_report(self):
        """生成反馈报告（用于发送）"""
        if not self.check_feedback_due():
            return None

        analysis = self.analyze_portfolio_performance()
        if 'error' in analysis:
            return None

        advice = self.generate_portfolio_adjustment_advice(analysis)

        report = self.format_performance_report(analysis)

        # 集成财经新闻调仓提示
        try:
            from news_advisor import NewsAdvisor
            news_advisor = NewsAdvisor()
            news_advisor.crawl_news()
            report += '\n' + news_advisor.format_news_report(limit=10)
        except Exception:
            pass

        report += '\n' + self.format_adjustment_report(advice)

        # 记录已发送
        self.record_feedback_sent()

        return report

    def format_feedback_settings_report(self):
        """格式化反馈设置报告"""
        settings = self.get_feedback_preference()

        freq_map = {
            'daily': '每日',
            'weekly': '每周',
            'monthly': '每月',
            'none': '关闭'
        }

        lines = []
        lines.append('\n【业绩反馈设置】')
        lines.append(f"  反馈频率: {freq_map.get(settings.get('frequency', 'none'), '关闭')}")
        lines.append(f"  提醒时间: {settings.get('notify_time', '09:00')}")
        lines.append(f"  状态: {'已开启' if settings.get('enabled') else '已关闭'}")
        if settings.get('last_feedback'):
            lines.append(f"  上次反馈: {settings.get('last_feedback')}")
        if settings.get('next_feedback'):
            lines.append(f"  下次反馈: {settings.get('next_feedback')}")
        lines.append('')
        lines.append('设置命令示例：')
        lines.append('  设为每日反馈: set_feedback("daily", "09:00")')
        lines.append('  设为每周反馈: set_feedback("weekly", "09:00")')
        lines.append('  设为每月反馈: set_feedback("monthly", "09:00")')
        lines.append('  关闭反馈: set_feedback("none")')

        return '\n'.join(lines)

    # ==================== 净值获取 ====================

    def get_latest_nav(self, fund_code):
        """获取最新净值"""
        try:
            url = f"https://fund.eastmoney.com/pingzhongdata/{fund_code}.js"
            resp = self.session.get(url, timeout=10)
            text = resp.text

            # 解析基金名称
            name_match = __import__('re').search(r'fS_name\s*=\s*["\'](.+?)["\']', text)
            fund_name = name_match.group(1) if name_match else ''

            # 解析最新净值
            nav_match = __import__('re').search(r'data_netWorthTrend\s*=\s*\[([\d.,]+)', text)
            if nav_match:
                nav_str = nav_match.group(1).split(',')[-1]
                nav = float(nav_str)
            else:
                nav = None

            # 解析净值日期
            date_match = __import__('re').search(r'data_netWorthTrend_date\s*=\s*\[([\d,]+)', text)
            if date_match:
                dates = date_match.group(1).split(',')
                if dates:
                    timestamp = int(dates[-1]) / 1000
                    nav_date = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d')
            else:
                nav_date = None

            return nav, nav_date

        except Exception as e:
            return None, None

    def get_historical_nav(self, fund_code, days=90):
        """获取历史净值用于计算收益"""
        try:
            url = f"https://fund.eastmoney.com/pingzhongdata/{fund_code}.js"
            resp = self.session.get(url, timeout=10)
            text = resp.text

            # 解析历史净值
            import re
            nav_match = re.search(r'data_netWorthTrend\s*=\s*\[([\d.,]+)', text)
            date_match = re.search(r'data_netWorthTrend_date\s*=\s*\[([\d,]+)', text)

            if nav_match and date_match:
                navs = [float(x) for x in nav_match.group(1).split(',')]
                timestamps = [int(x) / 1000 for x in date_match.group(1).split(',')]

                # 取最近days天的数据
                end_idx = len(navs)
                start_idx = max(0, end_idx - days)

                result = []
                for i in range(start_idx, end_idx):
                    result.append({
                        'date': datetime.fromtimestamp(timestamps[i]).strftime('%Y-%m-%d'),
                        'nav': navs[i]
                    })
                return result
        except (json.JSONDecodeError, OSError, ValueError, KeyError, TypeError):
            pass
        return []

    def get_fund_info(self, fund_code):
        """获取基金基本信息"""
        # 先查本地
        if fund_code in self.managers_db:
            m = self.managers_db[fund_code]
            return {
                'fund_code': fund_code,
                'fund_name': m.get('current_fund_name', ''),
                'manager': m.get('name', ''),
                'company': m.get('company_name', ''),
                'style': m.get('investment_style', '')
            }

        # 从网络获取
        try:
            url = f"https://fund.eastmoney.com/pingzhongdata/{fund_code}.js"
            resp = self.session.get(url, timeout=10)
            text = resp.text

            import re
            name_match = re.search(r'fS_name\s*=\s*["\'](.+?)["\']', text)
            code_match = re.search(r'fS_code\s*=\s*["\'](\d+)["\']', text)

            if name_match:
                return {
                    'fund_code': code_match.group(1) if code_match else fund_code,
                    'fund_name': name_match.group(1),
                    'manager': '',
                    'company': '',
                    'style': ''
                }
        except (json.JSONDecodeError, OSError, ValueError, KeyError, TypeError):
            pass

        return None

    # ==================== 业绩分析 ====================

    def analyze_performance(self, holding):
        """分析单只基金的业绩"""
        fund_code = holding.get('fund_code')
        shares = holding.get('shares', 0)
        cost = holding.get('cost', 0)
        purchase_date = holding.get('purchase_date', '')

        if not fund_code or shares <= 0 or cost <= 0:
            return {'error': '参数不完整'}

        # 获取最新净值
        nav, nav_date = self.get_latest_nav(fund_code)

        # 如果无法获取净值，使用成本作为估算（标记为估算）
        if nav is None:
            # 尝试从本地数据获取最近的估算净值
            fund_info = self.get_fund_info(fund_code)
            nav = cost  # 暂时用成本作为估算
            nav_date = '净值待更新'
            is_estimated = True
        else:
            is_estimated = False

        # 计算收益
        current_value = shares * nav
        cost_value = shares * cost
        profit = current_value - cost_value
        profit_pct = (profit / cost_value * 100) if cost_value > 0 else 0

        # 持有天数
        purchase_dt = datetime.strptime(purchase_date, '%Y-%m-%d') if purchase_date else date.today()
        holding_days = (datetime.now() - purchase_dt).days
        holding_years = holding_days / 365

        # 年化收益
        annual_return = ((nav / cost - 1) / holding_years * 100) if holding_years > 0 else 0

        # 计算最大回撤（标准峰谷定义：峰值须先于谷值，running peak）
        historical = self.get_historical_nav(fund_code, days=90)
        max_drawdown = 0
        if historical:
            navs = [h['nav'] for h in historical]
            peak = navs[0]
            for v in navs:
                if v > peak:
                    peak = v
                if peak > 0:
                    dd = (peak - v) / peak * 100
                    if dd > max_drawdown:
                        max_drawdown = dd

        # 获取基金信息
        fund_info = self.get_fund_info(fund_code)

        return {
            'fund_code': fund_code,
            'fund_name': fund_info.get('fund_name', '') if fund_info else '',
            'manager': fund_info.get('manager', '') if fund_info else '',
            'company': fund_info.get('company', '') if fund_info else '',
            'style': fund_info.get('style', '') if fund_info else '',
            'shares': shares,
            'cost': cost,
            'current_nav': nav,
            'nav_date': nav_date,
            'is_estimated': is_estimated,
            'current_value': round(current_value, 2),
            'cost_value': round(cost_value, 2),
            'profit': round(profit, 2),
            'profit_pct': round(profit_pct, 2),
            'holding_days': holding_days,
            'holding_years': round(holding_years, 1),
            'annual_return': round(annual_return, 2),
            'max_drawdown_90d': round(max_drawdown, 2),
            'purchase_date': purchase_date
        }

    def analyze_portfolio_performance(self, user_id=None):
        """分析整个组合的业绩"""
        holdings = self.get_holdings(user_id=user_id)
        if not holdings:
            return {'error': '暂无持仓记录'}

        results = []
        total_value = 0
        total_cost = 0
        total_profit = 0

        for h in holdings:
            analysis = self.analyze_performance(h)
            if 'error' not in analysis:
                results.append(analysis)
                total_value += analysis.get('current_value', 0)
                total_cost += analysis.get('cost_value', 0)
                total_profit += analysis.get('profit', 0)

        if not results:
            return {'error': '无法获取任何持仓数据'}

        total_profit_pct = (total_profit / total_cost * 100) if total_cost > 0 else 0

        return {
            'holdings': results,
            'total_value': round(total_value, 2),
            'total_cost': round(total_cost, 2),
            'total_profit': round(total_profit, 2),
            'total_profit_pct': round(total_profit_pct, 2),
            'holding_count': len(results),
            'analyzed_at': datetime.now().strftime('%Y-%m-%d %H:%M')
        }

    # ==================== 调整建议 ====================

    def generate_adjustment_advice(self, holding_analysis):
        """生成调整建议"""
        if 'error' in holding_analysis:
            return {'error': holding_analysis['error']}

        fund_code = holding_analysis.get('fund_code')
        fund_name = holding_analysis.get('fund_name', '')

        # 净值为成本估算（离线/数据缺失）时，不生成任何基于盈亏阈值的建议
        if holding_analysis.get('is_estimated'):
            return {
                'fund_code': fund_code,
                'fund_name': fund_name,
                'profit_pct': None,
                'action': '数据不可用',
                'advice': ['当前净值未能获取，所示估值基于成本估算，暂不生成盈亏类建议。'
                           '请恢复网络或更新数据后重试。'],
                'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M')
            }

        profit_pct = holding_analysis.get('profit_pct', 0)
        annual_return = holding_analysis.get('annual_return', 0)
        max_drawdown = holding_analysis.get('max_drawdown_90d', 0)
        style = holding_analysis.get('style', '均衡型')

        advice = []
        action = '持有'

        # 基于收益率的建议
        if profit_pct > 30:
            advice.append('收益已超过30%，建议考虑部分止盈，锁定利润。')
            action = '考虑止盈'
        elif profit_pct > 15:
            advice.append('收益表现良好，建议适度持有，等待趋势延续。')
            action = '继续持有'
        elif profit_pct > 0:
            advice.append('目前小幅盈利，建议设置移动止损，保护已有收益。')
            action = '持有/微调'
        elif profit_pct > -10:
            advice.append('短期波动，正常现象。拉长周期看，优质基金通常能修复。')
            action = '持有'
        elif profit_pct > -20:
            if style == '成长型':
                advice.append('成长风格波动较大，如风险承受可接受，建议坚持定投。')
            else:
                advice.append('回撤较大，需评估是否在风险承受范围内。')
            action = '评估是否持有'
        else:
            advice.append('亏损超过20%，建议认真评估：该基金逻辑是否变化？是否需要转换？')
            action = '建议转换或止损'

        # 基于年化收益的建议
        if annual_return > 20:
            advice.append('年化收益超过20%，表现优秀，可继续持有。')
        elif annual_return < -15:
            advice.append('年化收益较差，建议关注是否有更优替代选择。')
            action = '考虑转换'

        # 基于回撤的建议
        if max_drawdown > 15:
            advice.append(f'近90天最大回撤{max_drawdown:.1f}%，波动较大，请关注风险。')

        # 互动引导
        advice.append('你对这个基金有什么看法？是否考虑调整？')

        return {
            'fund_code': fund_code,
            'fund_name': fund_name,
            'profit_pct': profit_pct,
            'action': action,
            'advice': advice,
            'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M')
        }

    def generate_portfolio_adjustment_advice(self, portfolio_analysis):
        """生成组合整体调整建议"""
        if 'error' in portfolio_analysis:
            return portfolio_analysis

        results = portfolio_analysis.get('holdings', [])
        total_profit_pct = portfolio_analysis.get('total_profit_pct', 0)

        overall_advice = []
        actions = []

        # 组合整体分析
        if total_profit_pct > 20:
            overall_advice.append('组合整体收益良好，建议适度分散，不要过于集中。')
            actions.append('考虑部分止盈')
        elif total_profit_pct > 0:
            overall_advice.append('组合目前小幅盈利，保持现有配置。')
            actions.append('继续持有')
        elif total_profit_pct > -10:
            overall_advice.append('市场波动正常，建议保持定投，平滑成本。')
            actions.append('保持定投')
        else:
            overall_advice.append('组合整体承压，建议检视各基金的逻辑是否还在。')
            actions.append('检视组合')

        # 个体建议汇总
        action_count = defaultdict(int)
        for h in results:
            analysis = self.generate_adjustment_advice(h)
            if 'error' not in analysis:
                action_count[analysis.get('action', '持有')] += 1

        # 建议
        if action_count.get('考虑止盈', 0) > 0:
            overall_advice.append(f'有{action_count["考虑止盈"]}只基金建议考虑止盈。')
        if action_count.get('建议转换或止损', 0) > 0:
            overall_advice.append(f'有{action_count["建议转换或止损"]}只基金建议转换或止损。')
        if action_count.get('考虑转换', 0) > 0:
            overall_advice.append(f'有{action_count["考虑转换"]}只基金建议转换。')

        overall_advice.append('总体而言，建议保持资产配置均衡，不追涨杀跌。')

        return {
            'total_profit_pct': total_profit_pct,
            'overall_action': actions[0] if actions else '持有',
            'overall_advice': overall_advice,
            'individual_actions': dict(action_count),
            'individual_advice': [self.generate_adjustment_advice(h) for h in results],
            'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M')
        }

    # ==================== v6.0 增强：漂移+信号调仓（委托 portfolio_rebalancer）====================

    def generate_enhanced_adjustment_advice(self, client_id="default"):
        """v6.0 增强调仓建议：漂移再平衡 + 信号驱动（非仅 profit 阈值）。

        向后兼容：旧 generate_portfolio_adjustment_advice 不受影响。
        需先通过 confirm_baseline 锁定持仓快照；若未确认，回退到旧 profit 阈值建议。
        """
        try:
            import sys as _sys
            from pathlib import Path as _Path
            _scripts = _Path(__file__).resolve().parents[1]
            if str(_scripts) not in _sys.path:
                _sys.path.insert(0, str(_scripts))
            from portfolio_rebalancer import PortfolioRebalancer, format_rebalance_report
            rb = PortfolioRebalancer()
            report = rb.generate_rebalance_report(client_id)
            if "error" in report:
                # 回退到旧 profit 阈值建议
                analysis = self.analyze_portfolio_performance()
                return self.generate_portfolio_adjustment_advice(analysis)
            return {"report_dict": report, "report_text": format_rebalance_report(report)}
        except Exception as e:
            # 回退
            analysis = self.analyze_portfolio_performance()
            return self.generate_portfolio_adjustment_advice(analysis)

    # ==================== 量化分析调仓建议 ====================

    def generate_quant_adjustment_advice(self, client_risk='稳健型'):
        """
        基于基金量化分析模型生成调仓建议

        参数:
            client_risk: 客户风险偏好（保守型/稳健型/平衡型/积极型/激进型）

        返回:
            dict: 量化调仓建议
        """
        try:
            from fund_quant_analyzer import FundQuantAnalyzer
        except ImportError:
            return {'error': '无法导入量化分析模块'}

        # 获取当前持仓
        holdings = self.get_holdings()
        if not holdings:
            return {'error': '暂无持仓记录'}

        # 初始化分析器
        analyzer = FundQuantAnalyzer(data_dir=self.data_dir)

        # 分析整个组合
        portfolio_analysis = analyzer.analyze_portfolio(holdings, client_risk)

        return portfolio_analysis

    def format_quant_adjustment_report(self, portfolio_analysis):
        """格式化量化调仓建议报告"""
        if 'error' in portfolio_analysis:
            return f"错误: {portfolio_analysis['error']}"

        try:
            from fund_quant_analyzer import FundQuantAnalyzer
        except ImportError:
            return f"错误: 无法导入量化分析模块"

        analyzer = FundQuantAnalyzer(data_dir=self.data_dir)
        return analyzer.format_portfolio_analysis_report(portfolio_analysis)

    # ==================== 输出格式化 ====================

    def format_performance_report(self, analysis):
        """格式化业绩报告"""
        if 'error' in analysis:
            return f"错误: {analysis['error']}"

        lines = []
        lines.append('\n' + '=' * 70)
        lines.append('  基金业绩追踪报告')
        lines.append('=' * 70)

        total_value = analysis.get('total_value', 0)
        total_cost = analysis.get('total_cost', 0)
        total_profit = analysis.get('total_profit', 0)
        total_profit_pct = analysis.get('total_profit_pct', 0)

        lines.append(f"\n【组合概览】")
        lines.append(f"  基金数量: {analysis.get('holding_count', 0)}只")
        lines.append(f"  总市值: {total_value:.2f}万元")
        lines.append(f"  总成本: {total_cost:.2f}万元")
        lines.append(f"  总收益: {total_profit:+.2f}万元 ({total_profit_pct:+.2f}%)")

        # 盈亏颜色标识（文字描述）
        if total_profit_pct > 0:
            lines.append(f"  状态: 盈利 🟢")
        elif total_profit_pct < 0:
            lines.append(f"  状态: 亏损 🔴")
        else:
            lines.append(f"  状态: 持平 ⚪")

        lines.append(f"\n【持仓明细】")
        lines.append('-' * 70)

        any_estimated = False
        for h in analysis.get('holdings', []):
            profit_pct = h.get('profit_pct', 0)
            marker = '🟢' if profit_pct > 0 else ('🔴' if profit_pct < 0 else '⚪')

            lines.append(f"\n{marker} {h.get('fund_name', '')} ({h.get('fund_code', '')})")
            lines.append(f"   持有: {h.get('holding_days', 0)}天 | 经理: {h.get('manager', 'N/A')}")
            if h.get('is_estimated'):
                any_estimated = True
                lines.append(f"   份额: {h.get('shares', 0):.2f}份 | 成本: {h.get('cost', 0):.3f} | 当前: 净值待更新")
                lines.append(f"   ⚠️ 净值为估算（按成本计），收益不可用")
            else:
                lines.append(f"   份额: {h.get('shares', 0):.2f}份 | 成本: {h.get('cost', 0):.3f} | 当前: {h.get('current_nav', 0):.3f}")
                lines.append(f"   市值: {h.get('current_value', 0):.2f}万元 | 收益: {h.get('profit', 0):+.2f}万元 ({h.get('profit_pct', 0):+.2f}%)")
                lines.append(f"   年化: {h.get('annual_return', 0):+.2f}% | 近90日最大回撤: {h.get('max_drawdown_90d', 0):.2f}%")

        if any_estimated:
            lines.append('\n⚠️ 部分持仓净值未能获取，组合总收益为成本估算值，仅供参考。')

        lines.append('\n' + '=' * 70)
        lines.append(f"生成时间: {analysis.get('analyzed_at', '')}")
        lines.append('=' * 70 + '\n')

        return '\n'.join(lines)

    def format_adjustment_report(self, advice):
        """格式化调整建议报告"""
        if 'error' in advice:
            return f"错误: {advice['error']}"

        lines = []
        lines.append('\n' + '=' * 70)
        lines.append('  组合调整建议')
        lines.append('=' * 70)

        lines.append(f"\n【整体评估】")
        lines.append(f"  组合收益: {advice.get('total_profit_pct', 0):+.2f}%")
        lines.append(f"  建议操作: {advice.get('overall_action', '持有')}")

        lines.append(f"\n【建议】")
        for i, a in enumerate(advice.get('overall_advice', []), 1):
            lines.append(f"  {i}. {a}")

        lines.append(f"\n【个股建议】")
        lines.append('-' * 70)

        for ind_adv in advice.get('individual_advice', []):
            if 'error' in ind_adv:
                continue
            lines.append(f"\n{ind_adv.get('fund_name', '')} ({ind_adv.get('fund_code', '')})")
            ind_pct = ind_adv.get('profit_pct')
            if ind_pct is None:
                lines.append(f"  当前收益: N/A（净值估算）")
            else:
                lines.append(f"  当前收益: {ind_pct:+.2f}%")
            lines.append(f"  建议操作: {ind_adv.get('action', '持有')}")
            for a in ind_adv.get('advice', []):
                lines.append(f"  - {a}")

        lines.append('\n' + '=' * 70)
        lines.append(f"生成时间: {advice.get('generated_at', '')}")
        lines.append('风险提示: 投资有风险，决策需谨慎，以上建议仅供参考。')
        lines.append('=' * 70 + '\n')

        return '\n'.join(lines)


def main():
    """测试"""
    tracker = PerformanceTracker()

    print('业绩跟踪引擎 v1.0')
    print(f'加载了 {len(tracker.managers_db)} 只基金数据')

    # 测试1: 录入持仓
    print('\n--- 测试1: 添加模拟持仓 ---')
    result = tracker.add_holding('001924', 10000, 1.5, '2025-01-15')
    print(f"添加结果: {result}")

    # 测试2: 业绩分析
    print('\n--- 测试2: 业绩分析 ---')
    analysis = tracker.analyze_portfolio_performance()
    print(tracker.format_performance_report(analysis))

    # 测试3: 调整建议
    if 'error' not in analysis:
        advice = tracker.generate_portfolio_adjustment_advice(analysis)
        print(tracker.format_adjustment_report(advice))


if __name__ == '__main__':
    main()