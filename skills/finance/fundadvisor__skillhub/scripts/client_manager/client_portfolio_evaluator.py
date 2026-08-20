"""
持仓评测与调整建议 v1.0
根据客户持仓出具专业评测报告和调整建议
"""
import json
import logging
import os
import random
import sys as _sys
from datetime import datetime
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
DATA_DIR = SCRIPT_DIR.parent.parent / "data"
_sys.path.insert(0, str(SCRIPT_DIR.parent))
from fund_advisor_paths import load_json_data  # noqa: E402

logger = logging.getLogger(__name__)


class ClientPortfolioEvaluator:
    """客户持仓评测器"""

    def __init__(self, data_dir=None):
        self.data_dir = data_dir or DATA_DIR
        self._load_data()

    def _load_data(self):
        """加载数据（列式压缩格式经 load_json_data 透明解码）"""
        self.managers_db = {}
        self.holdings_db = {}

        try:
            managers_path = self.data_dir / 'fund_managers_distilled.json'
            if managers_path.exists():
                data = load_json_data(str(managers_path))
                items = data.get('managers', data.get('items', []))
                for m in items:
                    # shipped 蒸馏数据可能缺少 current_fund_code 字段，
                    # 此时按 name 建索引（按基金代码反查会落空，风格回退持仓自带值，不编造）
                    code = m.get('current_fund_code', '') or m.get('name', '')
                    if code:
                        self.managers_db[code] = m
                if not self.managers_db:
                    logger.warning("fund_managers_distilled.json 加载为空（键名/格式不匹配？）")
        except Exception as e:
            logger.warning("加载经理数据失败: %s", e)

    def evaluate_portfolio(self, holdings: list, user_profile: dict = None) -> dict:
        """
        评测持仓

        Args:
            holdings: 持仓列表 [{fund_code, shares, cost, purchase_date, ...}]
            user_profile: 用户画像（可选）

        Returns:
            dict: {
                'overall_score': int,       # 综合评分 0-100
                'risk_assessment': str,     # 风险评估
                'diversification': str,    # 分散度
                'adjustment_suggestions': list,
                'loss_warning': bool,
                'report': str
            }
        """
        if not holdings:
            return {
                'overall_score': 0,
                'risk_assessment': '无法评估',
                'diversification': '无持仓',
                'adjustment_suggestions': ['请先添加持仓记录'],
                'loss_warning': False,
                'report': '暂无持仓记录，请先添加您的基金持仓。'
            }

        # 1. 计算集中度
        concentration = self._assess_concentration(holdings)

        # 2. 风险评估
        risk_level = self._assess_risk(holdings, user_profile)

        # 3. 计算综合评分
        score = self._calculate_score(concentration, risk_level, holdings)

        # 4. 生成调整建议
        suggestions = self._generate_suggestions(holdings, concentration, risk_level)

        # 5. 检查损失警告
        loss_warning = self._check_loss_warning(holdings)

        # 6. 生成报告
        report = self._generate_report(
            holdings, score, concentration, risk_level, suggestions, loss_warning
        )

        return {
            'overall_score': score,
            'risk_assessment': risk_level,
            'diversification': concentration,
            'adjustment_suggestions': suggestions,
            'loss_warning': loss_warning,
            'report': report
        }

    def _assess_concentration(self, holdings: list) -> dict:
        """评估持仓集中度"""
        if not holdings:
            return {'level': '无', 'score': 0, 'details': ''}

        # 计算各持仓占比
        total_value = sum(h.get('current_value', 0) for h in holdings)

        if total_value == 0:
            return {'level': '未知', 'score': 50, 'details': '无法计算'}

        concentrations = []
        for h in holdings:
            value = h.get('current_value', 0)
            pct = (value / total_value * 100) if total_value > 0 else 0
            concentrations.append({'name': h.get('fund_name', h.get('fund_code', '')), 'pct': pct})

        # 按占比排序
        concentrations.sort(key=lambda x: x['pct'], reverse=True)

        # 判断集中度等级
        top_pct = concentrations[0]['pct'] if concentrations else 0
        top3_pct = sum(c['pct'] for c in concentrations[:3])

        if top_pct > 50:
            level = '过高'
            score = 20
        elif top_pct > 30 or top3_pct > 80:
            level = '偏高'
            score = 40
        elif top_pct > 20 or top3_pct > 60:
            level = '适中'
            score = 70
        else:
            level = '分散'
            score = 90

        details = f"最大持仓 {top_pct:.1f}%，前3合计 {top3_pct:.1f}%"

        return {
            'level': level,
            'score': score,
            'details': details,
            'breakdown': concentrations
        }

    def _assess_risk(self, holdings: list, user_profile: dict = None) -> dict:
        """评估风险"""
        if not holdings:
            return {'level': '无法评估', 'score': 50, 'details': ''}

        # 从持仓中分析风险特征
        high_risk_count = 0
        medium_risk_count = 0
        low_risk_count = 0

        for h in holdings:
            style = h.get('style', '')
            fund_code = h.get('fund_code', '')

            # 查数据库获取风格
            if fund_code in self.managers_db:
                style = self.managers_db[fund_code].get('investment_style', style)

            if style in ['成长型', '激进型']:
                high_risk_count += 1
            elif style in ['均衡型']:
                medium_risk_count += 1
            else:
                low_risk_count += 1

        total = len(holdings)
        high_risk_ratio = high_risk_count / total if total > 0 else 0

        # 用户风险偏好
        user_risk = 'moderate'
        if user_profile:
            risk_map = {'conservative': 1, 'moderate': 2, 'aggressive': 3}
            user_risk = risk_map.get(user_profile.get('risk_tolerance', 'moderate'), 2)

        # 判断风险等级
        if high_risk_ratio > 0.6 or (high_risk_ratio > 0.4 and user_risk < 3):
            level = '高风险'
            score = 25
        elif high_risk_ratio > 0.3:
            level = '中风险'
            score = 55
        else:
            level = '低风险'
            score = 80

        details = f"成长型{high_risk_count}只/均衡型{medium_risk_count}只/价值型{low_risk_count}只"

        return {
            'level': level,
            'score': score,
            'details': details,
            'high_risk_ratio': high_risk_ratio
        }

    def _calculate_score(self, concentration: dict, risk: dict, holdings: list) -> int:
        """计算综合评分"""
        conc_score = concentration.get('score', 50)
        risk_score = risk.get('score', 50)

        # 收益评分
        total_profit_pct = 0
        for h in holdings:
            profit_pct = h.get('profit_pct', 0)
            if profit_pct > 20:
                profit_score = 90
            elif profit_pct > 10:
                profit_score = 75
            elif profit_pct > 0:
                profit_score = 60
            elif profit_pct > -10:
                profit_score = 45
            else:
                profit_score = 25
            total_profit_pct += profit_score

        profit_score = total_profit_pct / len(holdings) if holdings else 50

        # 加权平均
        final_score = int(conc_score * 0.25 + risk_score * 0.35 + profit_score * 0.4)

        return max(0, min(100, final_score))

    def _generate_suggestions(self, holdings: list, concentration: dict, risk: dict) -> list:
        """生成调整建议"""
        suggestions = []

        # 集中度建议
        conc_level = concentration.get('level', '')
        if conc_level == '过高':
            suggestions.append("持仓过于集中，建议分散到更多标的降低风险。")
        elif conc_level == '偏高':
            suggestions.append("集中度偏高，可以考虑适当增加其他标的。")

        # 风险建议
        risk_level = risk.get('level', '')
        if '高风险' in risk_level:
            suggestions.append("组合整体风险偏高，建议增加一些稳健型产品平衡。")

        # 亏损处理
        for h in holdings:
            profit_pct = h.get('profit_pct', 0)
            fund_name = h.get('fund_name', h.get('fund_code', ''))

            if profit_pct < -15:
                suggestions.append(f"{fund_name}亏损较大({profit_pct:.1f}%)，建议检视是否继续持有。")
            elif profit_pct > 30:
                suggestions.append(f"{fund_name}收益较高({profit_pct:.1f}%)，可考虑分批止盈。")

        # 风格平衡
        styles = [h.get('style', '') for h in holdings]
        if '成长型' not in styles and '激进型' not in styles:
            # 全部是稳健型，可以适当加一点进攻性
            suggestions.append("组合全是稳健型产品，可以适当配置一些成长型增加收益弹性。")
        elif sum(1 for s in styles if s in ['成长型', '激进型']) > len(styles) * 0.6:
            suggestions.append("成长风格占比过高，建议增加价值型产品平衡风险。")

        if not suggestions:
            suggestions.append("持仓结构合理，继续持有即可。")

        return suggestions

    def _check_loss_warning(self, holdings: list) -> bool:
        """检查是否需要损失警告"""
        for h in holdings:
            profit_pct = h.get('profit_pct', 0)
            if profit_pct < -15:
                return True
        return False

    def _generate_report(self, holdings: list, score: int, concentration: dict,
                         risk: dict, suggestions: list, loss_warning: bool) -> str:
        """生成评测报告"""
        lines = []

        # 标题
        lines.append("\n" + "=" * 60)
        lines.append("  持仓综合评测报告")
        lines.append(f"  生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        lines.append("=" * 60)

        # 评分
        if score >= 80:
            grade = "优秀"
        elif score >= 60:
            grade = "良好"
        elif score >= 40:
            grade = "一般"
        else:
            grade = "需优化"

        lines.append(f"\n【综合评分】{score}分 ({grade})")

        # 风险评估
        lines.append(f"\n【风险评估】{risk.get('level', '未知')}")
        lines.append(f"  {risk.get('details', '')}")

        # 集中度
        lines.append(f"\n【集中度】{concentration.get('level', '未知')}")
        lines.append(f"  {concentration.get('details', '')}")

        # 持仓明细
        lines.append(f"\n【持仓明细】")
        lines.append("-" * 60)

        for h in holdings:
            name = h.get('fund_name', '')
            code = h.get('fund_code', '')
            profit_pct = h.get('profit_pct', 0)
            profit = h.get('profit', 0)
            style = h.get('style', '未知')

            marker = '🟢' if profit_pct > 0 else ('🔴' if profit_pct < 0 else '⚪')

            lines.append(f"\n  {marker} {name}({code})")
            lines.append(f"     风格: {style} | 收益: {profit_pct:+.2f}% ({profit:+.2f}万)")

        # 调整建议
        lines.append(f"\n【调整建议】")
        for i, s in enumerate(suggestions, 1):
            lines.append(f"  {i}. {s}")

        # 警告
        if loss_warning:
            lines.append(f"\n  ⚠️ 注意：部分持仓亏损较大，建议关注。")

        lines.append("\n" + "=" * 60)
        lines.append("  风险提示：投资有风险，以上建议仅供参考。")
        lines.append("=" * 60 + "\n")

        return "\n".join(lines)

    def compare_with_benchmark(self, holdings: list, benchmark: str = '沪深300') -> dict:
        """与基准比较

        注意：本地未接入指数行情源，无法获取基准真实收益。
        不得使用硬编码常数冒充基准——拿不到时如实返回"基准数据不可用"。
        """
        # 计算组合收益率
        total_profit_pct = 0
        for h in holdings:
            total_profit_pct += h.get('profit_pct', 0)

        avg_profit_pct = total_profit_pct / len(holdings) if holdings else 0

        return {
            'benchmark': benchmark,
            'portfolio_return': round(avg_profit_pct, 2),
            'benchmark_return': None,
            'outperformance': None,
            'verdict': None,
            'note': '基准数据不可用（未接入指数行情源），仅展示组合收益，不做跑赢/跑输判断'
        }


def main():
    """测试"""
    evaluator = ClientPortfolioEvaluator()

    print("=== 持仓评测测试 ===\n")

    # 模拟持仓数据
    holdings = [
        {
            'fund_code': '000858',
            'fund_name': '五粮液',
            'shares': 10000,
            'cost': 95.0,
            'current_nav': 84.03,
            'current_value': 840300,
            'profit': -109700,
            'profit_pct': -11.55,
            'style': '价值型'
        },
        {
            'fund_code': '300750',
            'fund_name': '宁德时代',
            'shares': 1000,
            'cost': 450.0,
            'current_nav': 411.16,
            'current_value': 411160,
            'profit': -38840,
            'profit_pct': -8.63,
            'style': '成长型'
        },
        {
            'fund_code': '600519',
            'fund_name': '贵州茅台',
            'shares': 100,
            'cost': 1350.0,
            'current_nav': 1290.20,
            'current_value': 129020,
            'profit': -5980,
            'profit_pct': -4.43,
            'style': '价值型'
        },
        {
            'fund_code': '110022',
            'fund_name': '易方达消费行业',
            'shares': 50000,
            'cost': 2.8,
            'current_nav': 2.929,
            'current_value': 146450,
            'profit': 6450,
            'profit_pct': 4.61,
            'style': '均衡型'
        }
    ]

    result = evaluator.evaluate_portfolio(holdings)
    print(result['report'])

    # 基准比较
    comparison = evaluator.compare_with_benchmark(holdings)
    print(f"\n【与{comparison['benchmark']}比较】")
    print(f"  组合收益: {comparison['portfolio_return']:+.2f}%")
    print(f"  基准收益: {comparison['benchmark_return']:+.2f}%")
    print(f"  超额收益: {comparison['outperformance']:+.2f}% ({comparison['verdict']})")


if __name__ == '__main__':
    main()