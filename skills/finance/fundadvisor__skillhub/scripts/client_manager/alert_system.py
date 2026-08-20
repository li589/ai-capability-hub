"""
投资告警系统 v1.0
每天量化分析持仓，触及止盈止损立即提醒
独立触发，不合并在报告中
"""
import json
from datetime import datetime, date, timedelta
from pathlib import Path
import random

SCRIPT_DIR = Path(__file__).resolve().parent
DATA_DIR = SCRIPT_DIR.parent.parent / "data"


class AlertSystem:
    """投资告警系统"""

    # 默认阈值
    DEFAULT_STOP_LOSS = -10.0  # -10%
    DEFAULT_STOP_PROFIT = 20.0  # +20%
    DEFAULT_DAILY_CHANGE = 3.0  # 日涨跌3%

    def __init__(self, data_dir=None):
        self.data_dir = data_dir or DATA_DIR
        self.alerts_path = self.data_dir / 'alert_history.json'
        self.settings_path = self.data_dir / 'alert_settings.json'
        self._load_alerts()
        self._load_settings()

    def _load_alerts(self):
        """加载告警历史"""
        try:
            if self.alerts_path.exists():
                with open(self.alerts_path, 'r', encoding='utf-8') as f:
                    self.alerts = json.load(f)
            else:
                self.alerts = []
        except Exception:
            self.alerts = []

    def _save_alerts(self):
        """保存告警历史"""
        try:
            with open(self.alerts_path, 'w', encoding='utf-8') as f:
                json.dump(self.alerts, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def _load_settings(self):
        """加载告警设置"""
        try:
            if self.settings_path.exists():
                with open(self.settings_path, 'r', encoding='utf-8') as f:
                    self.settings = json.load(f)
            else:
                self.settings = {'users': {}}
        except Exception:
            self.settings = {'users': {}}

    def _save_settings(self):
        """保存告警设置"""
        try:
            with open(self.settings_path, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def set_user_alert_settings(self, user_id: str, stop_loss: float = None,
                                 stop_profit: float = None, daily_change: float = None):
        """设置用户告警阈值"""
        if user_id not in self.settings['users']:
            self.settings['users'][user_id] = {}

        if stop_loss is not None:
            self.settings['users'][user_id]['stop_loss'] = -abs(stop_loss)

        if stop_profit is not None:
            self.settings['users'][user_id]['stop_profit'] = abs(stop_profit)

        if daily_change is not None:
            self.settings['users'][user_id]['daily_change'] = abs(daily_change)

        self._save_settings()

    def get_user_settings(self, user_id: str) -> dict:
        """获取用户告警设置"""
        user_settings = self.settings['users'].get(user_id, {})

        return {
            'stop_loss': user_settings.get('stop_loss', self.DEFAULT_STOP_LOSS),
            'stop_profit': user_settings.get('stop_profit', self.DEFAULT_STOP_PROFIT),
            'daily_change': user_settings.get('daily_change', self.DEFAULT_DAILY_CHANGE)
        }

    def check_alerts(self, user_id: str, holdings: list, market_data: dict = None) -> list:
        """
        检查告警

        Args:
            user_id: 用户ID
            holdings: 持仓列表 [{fund_code, fund_name, cost, current_nav, shares, ...}]
            market_data: 市场数据 {fund_code: {nav, daily_change, ...}}

        Returns:
            list: 触发的告警列表
        """
        user_settings = self.get_user_settings(user_id)
        triggered_alerts = []

        for holding in holdings:
            fund_code = holding.get('fund_code', '')
            fund_name = holding.get('fund_name', fund_code)
            cost = holding.get('cost', 0)
            shares = holding.get('shares', 0)
            purchase_date = holding.get('purchase_date', '')

            # 获取当前净值
            if market_data and fund_code in market_data:
                current_nav = market_data[fund_code].get('nav')
                daily_change = market_data[fund_code].get('daily_change', 0)
            else:
                # 通过业绩跟踪获取
                current_nav = holding.get('current_nav')
                daily_change = holding.get('daily_change', 0)

            if current_nav is None or cost is None or cost == 0:
                continue

            # 计算累计收益率
            cumulative_change = (current_nav - cost) / cost * 100

            # 计算年化收益率（如果知道购买日期）
            annual_return = None
            if purchase_date:
                try:
                    purchase_dt = datetime.strptime(purchase_date, '%Y-%m-%d')
                    holding_days = (datetime.now() - purchase_dt).days
                    if holding_days > 0:
                        annual_return = (current_nav / cost - 1) / (holding_days / 365) * 100
                except Exception:
                    pass

            # 止损检查
            stop_loss = user_settings['stop_loss']
            if cumulative_change <= stop_loss:
                alert = self._create_alert(
                    user_id=user_id,
                    alert_type='stop_loss',
                    fund_code=fund_code,
                    fund_name=fund_name,
                    trigger_value=cumulative_change,
                    threshold=stop_loss,
                    holding=holding,
                    annual_return=annual_return,
                    message=f"⚠️ 【止损提醒】{fund_name}已亏损{abs(cumulative_change):.1f}%，触及止损线{stop_loss:.1f}%"
                )
                triggered_alerts.append(alert)

            # 止盈检查
            stop_profit = user_settings['stop_profit']
            if cumulative_change >= stop_profit:
                alert = self._create_alert(
                    user_id=user_id,
                    alert_type='stop_profit',
                    fund_code=fund_code,
                    fund_name=fund_name,
                    trigger_value=cumulative_change,
                    threshold=stop_profit,
                    holding=holding,
                    annual_return=annual_return,
                    message=f"🎯 【止盈提醒】{fund_name}已盈利{cumulative_change:.1f}%，触及止盈线{stop_profit:.1f}%"
                )
                triggered_alerts.append(alert)

            # 日涨跌检查
            daily_threshold = user_settings['daily_change']
            if abs(daily_change) >= daily_threshold:
                direction = "大涨" if daily_change > 0 else "大跌"
                alert = self._create_alert(
                    user_id=user_id,
                    alert_type='daily_change',
                    fund_code=fund_code,
                    fund_name=fund_name,
                    trigger_value=daily_change,
                    threshold=daily_threshold,
                    holding=holding,
                    message=f"📊 【日涨跌提醒】{fund_name}今日{direction}{abs(daily_change):.1f}%"
                )
                triggered_alerts.append(alert)

        # 保存告警
        if triggered_alerts:
            self.alerts.extend(triggered_alerts)
            self._trim_alerts()
            self._save_alerts()

        return triggered_alerts

    def _create_alert(self, user_id: str, alert_type: str, fund_code: str,
                      fund_name: str, trigger_value: float, threshold: float,
                      holding: dict = None, annual_return: float = None,
                      message: str = None) -> dict:
        """创建告警"""
        alert = {
            'id': f"{user_id}_{fund_code}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            'user_id': user_id,
            'alert_type': alert_type,
            'fund_code': fund_code,
            'fund_name': fund_name,
            'trigger_value': round(trigger_value, 2),
            'threshold': round(threshold, 2),
            'current_nav': holding.get('current_nav') if holding else None,
            'cost': holding.get('cost') if holding else None,
            'annual_return': round(annual_return, 2) if annual_return else None,
            'message': message or self._generate_default_message(alert_type, fund_name, trigger_value),
            'timestamp': datetime.now().isoformat(),
            'acknowledged': False
        }

        return alert

    def _generate_default_message(self, alert_type: str, fund_name: str, trigger_value: float) -> str:
        """生成默认告警消息"""
        if alert_type == 'stop_loss':
            return f"⚠️ 【止损提醒】{fund_name}已亏损{abs(trigger_value):.1f}%，建议关注"
        elif alert_type == 'stop_profit':
            return f"🎯 【止盈提醒】{fund_name}已盈利{trigger_value:.1f}%，是否考虑止盈？"
        elif alert_type == 'daily_change':
            direction = "大涨" if trigger_value > 0 else "大跌"
            return f"📊 【日涨跌提醒】{fund_name}今日{direction}{abs(trigger_value):.1f}%"
        return f"📢 【告警】{fund_name}触发告警，当前{trigger_value:+.1f}%"

    def get_unacknowledged_alerts(self, user_id: str) -> list:
        """获取未确认的告警"""
        return [a for a in self.alerts
                if a.get('user_id') == user_id and not a.get('acknowledged', False)]

    def acknowledge_alert(self, user_id: str, alert_id: str) -> bool:
        """确认告警"""
        for alert in self.alerts:
            if alert.get('id') == alert_id and alert.get('user_id') == user_id:
                alert['acknowledged'] = True
                alert['acknowledged_at'] = datetime.now().isoformat()
                self._save_alerts()
                return True
        return False

    def get_alert_history(self, user_id: str = None, days: int = 30) -> list:
        """获取告警历史"""
        cutoff = datetime.now() - timedelta(days=days)

        alerts = self.alerts
        if user_id:
            alerts = [a for a in alerts if a.get('user_id') == user_id]

        alerts = [a for a in alerts
                  if datetime.fromisoformat(a['timestamp']) >= cutoff]

        # 按时间倒序
        alerts.sort(key=lambda x: x['timestamp'], reverse=True)

        return alerts

    def _trim_alerts(self):
        """修剪告警历史，保持最近1000条"""
        if len(self.alerts) > 1000:
            self.alerts = self.alerts[-1000:]

    def format_alert_message(self, alert: dict) -> str:
        """格式化告警消息"""
        lines = []
        lines.append(f"\n{'='*60}")
        lines.append(f"  {alert['message']}")
        lines.append(f"{'='*60}")

        lines.append(f"\n  基金：{alert['fund_name']} ({alert['fund_code']})")

        if alert.get('trigger_value'):
            trigger = alert['trigger_value']
            if trigger > 0:
                lines.append(f"  当前收益：🟢 {trigger:+.2f}%")
            else:
                lines.append(f"  当前收益：🔴 {trigger:+.2f}%")

        if alert.get('annual_return'):
            lines.append(f"  年化收益：{alert['annual_return']:+.2f}%")

        lines.append(f"  触发时间：{alert['timestamp']}")

        # 建议
        alert_type = alert.get('alert_type')
        if alert_type == 'stop_loss':
            lines.append(f"\n  💡 建议：")
            lines.append(f"     - 止损触发，建议减仓或转换")
            lines.append(f"     - 不要在最低点割肉，考虑分批卖出")
            lines.append(f"     - 检视该基金投资逻辑是否变化")
        elif alert_type == 'stop_profit':
            lines.append(f"\n  💡 建议：")
            lines.append(f"     - 止盈触发，可以考虑分批卖出")
            lines.append(f"     - 锁定部分利润，落袋为安")
            lines.append(f"     - 可以留一部分仓位继续观察")
        elif alert_type == 'daily_change':
            lines.append(f"\n  💡 建议：")
            lines.append(f"     - 注意市场波动风险")
            lines.append(f"     - 避免追涨杀跌")

        lines.append(f"\n  操作：回复'确认'标记为已读，回复'详情'获取更多信息")

        return "\n".join(lines)

    def format_pending_alerts(self, user_id: str) -> str:
        """格式化待处理告警列表"""
        alerts = self.get_unacknowledged_alerts(user_id)

        if not alerts:
            return "\n📬 暂无待处理告警\n"

        lines = []
        lines.append(f"\n📬 您有 {len(alerts)} 条待处理告警：")

        for i, alert in enumerate(alerts, 1):
            emoji = self._get_alert_emoji(alert['alert_type'])
            lines.append(f"\n  {i}. {emoji} {alert['fund_name']}")
            lines.append(f"     {alert['message']}")
            lines.append(f"     {alert['timestamp'][:16]}")

        lines.append("\n  回复 '确认1' '确认2' ... 来标记已读")
        lines.append("  回复 '全部确认' 标记全部已读")

        return "\n".join(lines)

    def _get_alert_emoji(self, alert_type: str) -> str:
        """获取告警类型emoji"""
        return {
            'stop_loss': '⚠️',
            'stop_profit': '🎯',
            'daily_change': '📊'
        }.get(alert_type, '📢')

    def daily_check(self, user_id: str, holdings: list, market_data: dict = None) -> list:
        """
        执行每日检查

        Args:
            user_id: 用户ID
            holdings: 持仓列表
            market_data: 市场数据

        Returns:
            list: 触发的告警
        """
        # 获取用户设置
        user_settings = self.get_user_settings(user_id)

        # 执行检查
        triggered = self.check_alerts(user_id, holdings, market_data)

        # 按优先级排序
        priority_order = {'stop_loss': 0, 'stop_profit': 1, 'daily_change': 2}
        triggered.sort(key=lambda x: (priority_order.get(x['alert_type'], 99), x['timestamp']))

        return triggered


class AlertScheduler:
    """告警调度器 - 用于定时执行每日检查"""

    def __init__(self, data_dir=None):
        self.data_dir = data_dir or DATA_DIR
        self.alert_system = AlertSystem(data_dir=data_dir)

    def run_daily_check(self, user_id: str, holdings: list, market_data: dict = None) -> list:
        """运行每日检查"""
        return self.alert_system.daily_check(user_id, holdings, market_data)

    def schedule_check(self, user_id: str, interval_hours: int = 24):
        """安排定期检查"""
        # 这个方法可以与外部调度系统集成
        # 例如：由 cron / Windows 任务计划定期调用 run_daily_check
        pass


def main():
    """测试"""
    alert_system = AlertSystem()

    print("=== 告警系统测试 ===\n")

    # 设置告警
    alert_system.set_user_alert_settings(
        user_id='test_user',
        stop_loss=10.0,
        stop_profit=20.0,
        daily_change=3.0
    )

    settings = alert_system.get_user_settings('test_user')
    print(f"用户告警设置: {settings}\n")

    # 模拟持仓数据
    holdings = [
        {
            'fund_code': '000858',
            'fund_name': '五粮液',
            'cost': 95.0,
            'current_nav': 84.03,
            'shares': 10000,
            'purchase_date': '2025-01-15'
        },
        {
            'fund_code': '300750',
            'fund_name': '宁德时代',
            'cost': 450.0,
            'current_nav': 411.16,
            'shares': 1000,
            'purchase_date': '2025-02-01'
        }
    ]

    # 执行检查
    alerts = alert_system.daily_check('test_user', holdings)

    if alerts:
        print(f"触发 {len(alerts)} 条告警：\n")
        for alert in alerts:
            print(alert_system.format_alert_message(alert))
    else:
        print("暂无告警触发\n")

    # 显示待处理告警
    print(alert_system.format_pending_alerts('test_user'))


if __name__ == '__main__':
    main()