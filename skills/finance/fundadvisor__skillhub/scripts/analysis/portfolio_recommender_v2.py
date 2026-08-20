"""
投资组合推荐引擎 v2.0
根据用户画像（年龄、风险承受能力、预期收益、投资时长、投资偏好、金额）
推荐1-3套基金组合方案
"""
import json
import logging
import os
import sys as _sys
from datetime import datetime
from pathlib import Path

# 路径推断
SCRIPT_DIR = Path(__file__).resolve().parent
DATA_DIR = SCRIPT_DIR.parent.parent / "data"
_sys.path.insert(0, str(SCRIPT_DIR.parent))
from fund_advisor_paths import load_json_data  # noqa: E402

logger = logging.getLogger(__name__)


class PortfolioRecommenderV2:
    """投资组合推荐引擎 v2.0 — 支持多维度输入和多套餐推荐"""

    def __init__(self, data_dir=None):
        self.data_dir = data_dir or DATA_DIR
        self.managers_db = {}
        self.companies_db = {}
        self._load_data()

    def _load_data(self):
        """加载数据库（列式压缩格式经 load_json_data 透明解码）"""
        self.manager_fields_missing = False
        try:
            path = self.data_dir / 'fund_managers_distilled.json'
            if path.exists():
                data = load_json_data(str(path))
                items = data.get('managers', data.get('items', []))
                for m in items:
                    key = m.get('manager_id', '')
                    if key:
                        self.managers_db[key] = m
                if not self.managers_db:
                    logger.warning("fund_managers_distilled.json 加载为空（键名/格式不匹配？），推荐功能不可用")
                # shipped 蒸馏数据可能只有 manager_id/name/company_name/total_scale/best_return
                # 五字段，缺少 current_fund_code/investment_style 时方案生成须降级并如实标注
                elif not any(m.get('current_fund_code') for m in items[:200]):
                    self.manager_fields_missing = True
                    logger.warning("经理数据缺少 current_fund_code/investment_style 字段，"
                                   "基金方案生成将降级（无法挑选具体基金）")
        except Exception as e:
            logger.warning("加载经理数据失败: %s", e)

        try:
            path = self.data_dir / 'fund_companies_distilled.json'
            if path.exists():
                data = load_json_data(str(path))
                # 该文件可能是纯 list 或带 companies/items 键的 dict
                items = data if isinstance(data, list) else data.get('companies', data.get('items', []))
                for c in items:
                    key = c.get('company_id', '') or c.get('name', '')
                    if key:
                        self.companies_db[key] = c
                if not self.companies_db:
                    logger.warning("fund_companies_distilled.json 加载为空")
        except Exception as e:
            logger.warning("加载公司数据失败: %s", e)

    # ==================== 风险画像分析 ====================

    def analyze_risk_profile(self, age, risk_tolerance, investment_period, max_loss):
        """分析用户风险画像"""
        stock_ratio = self._age_to_stock_ratio(age)
        bond_ratio = 100 - stock_ratio

        risk_multiplier = {
            '保守型': 0.5, '稳健型': 0.75, '平衡型': 1.0,
            '积极型': 1.25, '激进型': 1.5
        }
        multiplier = risk_multiplier.get(risk_tolerance, 1.0)
        stock_ratio = min(100, int(stock_ratio * multiplier))

        if investment_period < 1:
            stock_ratio = min(stock_ratio, 20)
        elif investment_period < 3:
            stock_ratio = min(stock_ratio, 50)
        elif investment_period >= 5:
            stock_ratio = min(stock_ratio + 10, 95)

        if max_loss < 5:
            stock_ratio = min(stock_ratio, 30)
        elif max_loss < 10:
            stock_ratio = min(stock_ratio, 50)
        elif max_loss > 20:
            stock_ratio = min(stock_ratio + 10, 95)

        bond_ratio = 100 - stock_ratio

        if stock_ratio >= 70:
            style_preference = '成长型'
        elif stock_ratio >= 40:
            style_preference = '均衡型'
        else:
            style_preference = '价值型'

        return {
            'stock_ratio': stock_ratio,
            'bond_ratio': bond_ratio,
            'style_preference': style_preference,
            'investment_horizon': investment_period,
            'max_loss_tolerance': max_loss,
            'risk_level': risk_tolerance,
            'age': age
        }

    def _age_to_stock_ratio(self, age):
        """基于年龄计算偏股比例"""
        ratio = max(10, min(90, 100 - age))
        return ratio

    # ==================== 预期收益匹配 ====================

    def _match_target_return(self, target_return, style_preference):
        """
        根据预期收益匹配基金风格
        target_return: 年化预期收益（%）
        """
        if target_return <= 5:
            return '价值型', '纯债/货币'
        elif target_return <= 10:
            if style_preference == '价值型':
                return '价值型', '偏债混合/二级债'
            return '均衡型', '灵活配置/偏股混合'
        elif target_return <= 15:
            return '均衡型', '偏股混合/灵活配置'
        elif target_return <= 25:
            return '成长型', '股票型/偏股混合'
        else:
            return '激进型', '股票型/指数型'

    # ==================== 偏好筛选 ====================

    def _filter_by_preferences(self, managers, preferences):
        """
        根据投资偏好筛选经理/基金
        preferences: dict {
            'preferred_companies': list[str],  # 偏好基金公司
            'preferred_managers': list[str],   # 偏好基金经理
            'preferred_funds': list[str],      # 偏好基金代码
            'exclude_companies': list[str],    # 排除基金公司
            'exclude_managers': list[str],     # 排除基金经理
            'sectors': list[str],              # 偏好行业
            'styles': list[str],               # 偏好风格
        }
        """
        if not preferences:
            return managers

        filtered = []
        for m in managers:
            # 排除项
            if preferences.get('exclude_companies'):
                if any(c in m.get('company_name', '') for c in preferences['exclude_companies']):
                    continue
            if preferences.get('exclude_managers'):
                if any(c == m.get('name', '') for c in preferences['exclude_managers']):
                    continue

            # 偏好项（至少满足一项）
            matched = False
            if preferences.get('preferred_companies'):
                if any(c in m.get('company_name', '') for c in preferences['preferred_companies']):
                    matched = True
            if preferences.get('preferred_managers'):
                if any(c == m.get('name', '') for c in preferences['preferred_managers']):
                    matched = True
            if preferences.get('preferred_funds'):
                if m.get('current_fund_code', '') in preferences['preferred_funds']:
                    matched = True
            if preferences.get('sectors'):
                sector = m.get('sector_description', '')
                if any(s in sector for s in preferences['sectors']):
                    matched = True
            if preferences.get('styles'):
                if m.get('investment_style', '') in preferences['styles']:
                    matched = True

            # 如果有偏好条件但没匹配，排除
            has_preference = any([
                preferences.get('preferred_companies'),
                preferences.get('preferred_managers'),
                preferences.get('preferred_funds'),
                preferences.get('sectors'),
                preferences.get('styles'),
            ])
            if has_preference and not matched:
                continue

            filtered.append(m)

        return filtered

    # ==================== 核心推荐逻辑 ====================

    def recommend_portfolio_v2(self, age, risk_tolerance, target_return, investment_period,
                                max_loss, investment_amount, preferences=None):
        """
        推荐投资组合 v2.0

        参数:
            age: 年龄
            risk_tolerance: 风险承受能力（保守型/稳健型/平衡型/积极型/激进型）
            target_return: 年化预期收益（%），如 12
            investment_period: 投资时长（年）
            max_loss: 可承担最大亏损（%）
            investment_amount: 投资金额（万元）
            preferences: dict, 投资偏好（可选）

        返回:
            list[dict]: 1-3套推荐组合
        """
        # 1. 分析风险画像
        profile = self.analyze_risk_profile(age, risk_tolerance, investment_period, max_loss)

        # 2. 匹配预期收益
        matched_style, fund_types = self._match_target_return(target_return, profile['style_preference'])

        # 3. 获取候选基金
        candidates = self._get_candidates(profile['style_preference'], matched_style, preferences)

        # 4. 生成1-3套组合方案
        schemes = self._generate_schemes(
            candidates, profile, matched_style, fund_types,
            investment_amount, preferences
        )

        result = {
            'profile': profile,
            'target_return': target_return,
            'schemes': schemes,
            'preferences': preferences or {},
            'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M')
        }
        # 数据降级如实标注：经理数据缺基金代码/风格字段时无法挑选具体基金，
        # 不得静默输出"共 0 套"
        if not schemes:
            if getattr(self, 'manager_fields_missing', False):
                result['data_degraded'] = True
                result['note'] = ("本地经理数据缺少基金代码/投资风格字段，无法生成具体基金方案"
                                  "（数据降级，非无合适基金）。请更新数据后重试。")
            elif not self.managers_db:
                result['data_degraded'] = True
                result['note'] = "本地经理数据未加载，无法生成推荐方案（数据不可用）。"
        return result

    def _get_candidates(self, style_preference, matched_style, preferences):
        """获取候选基金经理"""
        managers = list(self.managers_db.values())

        # 按风格过滤
        styles = [style_preference, matched_style]
        if matched_style == '激进型':
            styles.append('成长型')
        elif matched_style in ['成长型', '均衡型']:
            styles.append('均衡型')

        filtered = [m for m in managers if m.get('investment_style', '') in styles
                    and m.get('tenure_years', 0) > 0]

        # 应用偏好筛选
        filtered = self._filter_by_preferences(filtered, preferences or {})

        # 排序
        filtered.sort(key=lambda x: (
            -x.get('tenure_years', 0),
            -x.get('total_scale', 0) if 10 < x.get('total_scale', 0) < 500 else 0,
            {'成熟期': 3, '老牌期': 4, '成长期': 2, '萌芽期': 1}.get(x.get('fund_stage', ''), 0)
        ))

        return filtered[:50]

    def _generate_schemes(self, candidates, profile, matched_style, fund_types,
                          investment_amount, preferences):
        """生成1-3套组合方案"""
        schemes = []

        # 方案1：稳健方案（债券为主，股票为辅）
        if profile['bond_ratio'] >= 30 or profile['stock_ratio'] <= 50:
            scheme = self._build_scheme(
                name='稳健型方案',
                description='以债券和货币基金为主，适当配置蓝筹股基金，追求稳健收益',
                style='价值型',
                stock_ratio=min(profile['stock_ratio'], 40),
                candidates=candidates,
                investment_amount=investment_amount,
                max_loss=profile['max_loss_tolerance']
            )
            if scheme:
                schemes.append(scheme)

        # 方案2：平衡方案（股债均衡）
        scheme = self._build_scheme(
            name='平衡型方案',
            description='股债均衡配置，灵活调整，追求中等收益',
            style='均衡型',
            stock_ratio=min(profile['stock_ratio'], 70),
            candidates=candidates,
            investment_amount=investment_amount,
            max_loss=profile['max_loss_tolerance']
        )
        if scheme:
            schemes.append(scheme)

        # 方案3：进取方案（股票为主）
        if profile['stock_ratio'] >= 60:
            scheme = self._build_scheme(
                name='进取型方案',
                description='以股票型基金为主，配置部分指数型和QDII，追求高收益',
                style='成长型',
                stock_ratio=min(profile['stock_ratio'], 95),
                candidates=candidates,
                investment_amount=investment_amount,
                max_loss=profile['max_loss_tolerance']
            )
            if scheme:
                schemes.append(scheme)

        return schemes[:3]  # 最多3套

    def _build_scheme(self, name, description, style, stock_ratio, candidates,
                      investment_amount, max_loss):
        """构建单套方案"""
        # 计算股债金额
        stock_amount = int(investment_amount * stock_ratio / 100)
        bond_amount = investment_amount - stock_amount

        # 分配基金类型
        if style in ['成长型', '激进型']:
            stock_allocation = {
                'stock_funds': 0.7,
                'index_funds': 0.2,
                'qdii_funds': 0.1,
            }
        elif style in ['价值型']:
            stock_allocation = {
                'stock_funds': 0.3,
                'index_funds': 0.4,
                'money_funds': 0.3,
            }
        else:  # 均衡型
            stock_allocation = {
                'stock_funds': 0.5,
                'index_funds': 0.3,
                'qdii_funds': 0.1,
                'money_funds': 0.1,
            }

        # 选基金
        funds = []
        fund_count = 0
        for category, ratio in stock_allocation.items():
            amount = stock_amount * ratio if category == 'stock_funds' else (bond_amount * ratio if category in ['bond_funds', 'money_funds'] else stock_amount * ratio)
            if amount < 1:
                continue

            count = max(1, min(3, int(amount / 5)))
            selected = []

            for m in candidates:
                if len(selected) >= count:
                    break
                code = m.get('current_fund_code', '')
                name_fund = m.get('current_fund_name', '')
                if not code or any(f['fund_code'] == code for f in selected):
                    continue

                # 过滤：排除定开产品、ETF、公募REITs、养老Y份额
                excluded_keywords = ['定开', '定期开放', 'ETF', 'REITs', '养老Y', 'Y类份额']
                if any(kw in name_fund for kw in excluded_keywords):
                    continue

                # 风险过滤
                warning = m.get('risk_warning', '')
                if max_loss < 10 and '高波动' in warning:
                    continue

                selected.append({
                    'fund_code': code,
                    'fund_name': name_fund,
                    'manager': m.get('name', ''),
                    'company': m.get('company_name', ''),
                    'style': m.get('investment_style', ''),
                    'sector': m.get('sector_description', ''),
                    'tenure_years': m.get('tenure_years', 0),
                    'suggested_amount': round(amount / count, 1),
                    'nav': m.get('current_nav', 1.0),
                })
                fund_count += 1

            if selected:
                funds.append({
                    'category': category,
                    'allocated_amount': round(amount, 1),
                    'allocated_ratio': round(ratio * 100, 1),
                    'fund_count': len(selected),
                    'funds': selected
                })

        if not funds:
            return None

        return {
            'name': name,
            'description': description,
            'style': style,
            'stock_ratio': stock_ratio,
            'bond_ratio': 100 - stock_ratio,
            'stock_amount': stock_amount,
            'bond_amount': bond_amount,
            'total_amount': investment_amount,
            'funds': funds,
        }

    # ==================== 输出格式化 ====================

    def format_portfolio_report_v2(self, result):
        """格式化组合推荐报告"""
        lines = []
        profile = result['profile']
        schemes = result.get('schemes', [])
        target = result.get('target_return', 0)
        preferences = result.get('preferences', {})

        lines.append('\n' + '=' * 70)
        lines.append('  基金投资组合推荐报告 v2.0')
        lines.append('=' * 70)

        # 客户画像
        lines.append(f"\n【您的投资画像】")
        lines.append(f"  年龄: {profile.get('age', 0)}岁")
        lines.append(f"  风险承受: {profile.get('risk_level', '')}")
        lines.append(f"  预期年化收益: {target}%")
        lines.append(f"  投资周期: {profile.get('investment_horizon', 0)}年")
        lines.append(f"  最大可承受亏损: {profile.get('max_loss_tolerance', 0)}%")
        lines.append(f"  建议风格: {profile.get('style_preference', '')}")

        # 偏好
        if preferences and any([preferences.get(k) for k in ['preferred_companies', 'preferred_managers', 'sectors']]):
            lines.append(f"\n【投资偏好】")
            if preferences.get('preferred_companies'):
                lines.append(f"  偏好公司: {', '.join(preferences['preferred_companies'])}")
            if preferences.get('preferred_managers'):
                lines.append(f"  偏好经理: {', '.join(preferences['preferred_managers'])}")
            if preferences.get('sectors'):
                lines.append(f"  偏好行业: {', '.join(preferences['sectors'])}")

        # 方案列表
        lines.append(f"\n【推荐组合方案】共 {len(schemes)} 套")
        if result.get('data_degraded') and result.get('note'):
            lines.append(f"  ⚠️ {result['note']}")
        for i, scheme in enumerate(schemes, 1):
            lines.append(f"\n{'─' * 70}")
            lines.append(f"  方案{i}：{scheme['name']}")
            lines.append(f"  说明: {scheme['description']}")
            lines.append(f"  风格: {scheme['style']} | 股债比例: {scheme['stock_ratio']}%/{scheme['bond_ratio']}%")

            lines.append(f"\n  【资产配置】")
            lines.append(f"    股票类: {scheme['stock_amount']:.1f}万元 ({scheme['stock_ratio']}%)")
            lines.append(f"    债券类: {scheme['bond_amount']:.1f}万元 ({scheme['bond_ratio']}%)")

            lines.append(f"\n  【基金配置明细】")
            for cat_funds in scheme.get('funds', []):
                cat_name = {
                    'stock_funds': '股票型',
                    'bond_funds': '债券型',
                    'money_funds': '货币基金',
                    'qdii_funds': 'QDII海外',
                    'index_funds': '指数型'
                }.get(cat_funds['category'], cat_funds['category'])

                lines.append(f"\n    ▶ {cat_name} ({cat_funds['allocated_amount']:.1f}万元)")
                for f in cat_funds.get('funds', []):
                    lines.append(f"      {f['fund_code']} {f['fund_name']}")
                    lines.append(f"        经理: {f['manager']} | 公司: {f['company']}")
                    lines.append(f"        建议买入: {f['suggested_amount']}万元")

        # 风险提示
        lines.append(f"\n{'─' * 70}")
        lines.append(f"\n【风险提示】")
        lines.append(f"  以上推荐仅供参考，不构成投资建议。")
        lines.append(f"  投资基金有风险，请评估自身风险承受能力后决策。")
        lines.append(f"  建议分散投资，不要把鸡蛋放在一个篮子里。")
        lines.append(f"  可设置止盈止损线，达到条件后自动提醒调仓。")

        lines.append('\n' + '=' * 70)
        lines.append(f"生成时间: {result.get('generated_at', '')}")
        lines.append('=' * 70 + '\n')

        return '\n'.join(lines)


def main():
    """测试"""
    recommender = PortfolioRecommenderV2()
    print(f"加载了 {len(recommender.managers_db)} 位基金经理")

    # 测试：完整参数
    result = recommender.recommend_portfolio_v2(
        age=35,
        risk_tolerance='积极型',
        target_return=15,
        investment_period=5,
        max_loss=20,
        investment_amount=20,
        preferences={
            'preferred_companies': ['华夏', '易方达'],
            'sectors': ['科技', '新能源'],
        }
    )

    print(recommender.format_portfolio_report_v2(result))


if __name__ == '__main__':
    main()