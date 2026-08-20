"""
用户画像管理器 v2.0
管理客户的投资画像，包括年龄、金额、经验、风险承受等
新增客户量化评估模型和投资心态跟踪
"""
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict

SCRIPT_DIR = Path(__file__).resolve().parent
DATA_DIR = SCRIPT_DIR.parent.parent / "data"


class UserProfileManager:
    """用户画像管理器"""

    def __init__(self, data_dir=None):
        self.data_dir = data_dir or DATA_DIR
        self.profiles_path = self.data_dir / 'user_profiles.json'
        self.profiles = self._load_profiles()

    def _load_profiles(self) -> dict:
        """加载用户画像"""
        try:
            if self.profiles_path.exists():
                with open(self.profiles_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception:
            pass
        return {}

    def _save_profiles(self):
        """保存用户画像"""
        try:
            with open(self.profiles_path, 'w', encoding='utf-8') as f:
                json.dump(self.profiles, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def get_profile(self, user_id: str) -> dict:
        """获取用户画像"""
        if user_id not in self.profiles:
            self.profiles[user_id] = self._default_profile()
        return self.profiles[user_id]

    def _default_profile(self) -> dict:
        """默认画像"""
        return {
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat(),
            'age': None,
            'investment_amount': None,
            'investment_experience': 'unknown',  # beginner/intermediate/experienced
            'risk_tolerance': 'moderate',  # conservative/moderate/aggressive
            'investment_horizon': None,
            'target_companies': [],
            'preferred_sectors': [],
            'preferred_styles': [],
            'holdings': [],
            'stop_loss': -10.0,
            'stop_profit': 20.0,
            'feedback_frequency': 'weekly',
            'notes': '',
            'behavioral': None,  # v10.0: 行为偏差画像（BehavioralBiasEngine 产物）
        }

    def update_profile(self, user_id: str, updates: dict) -> dict:
        """更新用户画像"""
        if user_id not in self.profiles:
            self.profiles[user_id] = self._default_profile()

        self.profiles[user_id].update(updates)
        self.profiles[user_id]['updated_at'] = datetime.now().isoformat()

        self._save_profiles()

        return self.profiles[user_id]

    def update_from_conversation(self, user_id: str, message: str, entities: dict):
        """从对话中自动提取并更新画像"""
        profile = self.get_profile(user_id)
        updated = False

        # 从实体中提取
        if entities.get('age') and profile.get('age') is None:
            profile['age'] = entities['age']
            updated = True

        if entities.get('amount') and profile.get('investment_amount') is None:
            profile['investment_amount'] = entities['amount']
            updated = True

        if entities.get('risk_level') and profile.get('risk_tolerance') == 'moderate':
            profile['risk_tolerance'] = entities['risk_level']
            updated = True

        if entities.get('period') and profile.get('investment_horizon') is None:
            profile['investment_horizon'] = entities['period']
            updated = True

        if updated:
            profile['updated_at'] = datetime.now().isoformat()
            self._save_profiles()

        return profile

    def get_investment_profile_summary(self, user_id: str) -> str:
        """获取投资画像摘要"""
        profile = self.get_profile(user_id)

        parts = []

        if profile.get('age'):
            parts.append(f"{profile['age']}岁")

        exp_map = {
            'beginner': '投资新手',
            'intermediate': '有经验',
            'experienced': '老手'
        }
        exp = exp_map.get(profile.get('investment_experience', 'unknown'), '')
        if exp:
            parts.append(exp)

        risk_map = {
            'conservative': '保守型',
            'moderate': '平衡型',
            'aggressive': '积极型'
        }
        risk = risk_map.get(profile.get('risk_tolerance', 'moderate'), '平衡型')
        parts.append(risk)

        horizon = profile.get('investment_horizon')
        if horizon:
            parts.append(f"{horizon}年投资周期")

        amount = profile.get('investment_amount')
        if amount:
            parts.append(f"{amount}万资金")

        return " | ".join(parts) if parts else "尚未建立完整画像"

    def set_holdings(self, user_id: str, holdings: list):
        """设置持仓"""
        profile = self.get_profile(user_id)
        profile['holdings'] = holdings
        profile['updated_at'] = datetime.now().isoformat()
        self._save_profiles()

    def add_holding(self, user_id: str, holding: dict):
        """添加持仓"""
        profile = self.get_profile(user_id)
        holdings = profile.get('holdings', [])

        # 检查是否已存在
        for i, h in enumerate(holdings):
            if h.get('fund_code') == holding.get('fund_code'):
                holdings[i] = holding
                break
        else:
            holdings.append(holding)

        profile['holdings'] = holdings
        profile['updated_at'] = datetime.now().isoformat()
        self._save_profiles()

    def remove_holding(self, user_id: str, fund_code: str):
        """删除持仓"""
        profile = self.get_profile(user_id)
        holdings = profile.get('holdings', [])
        profile['holdings'] = [h for h in holdings if h.get('fund_code') != fund_code]
        profile['updated_at'] = datetime.now().isoformat()
        self._save_profiles()

    def get_recommendation_context(self, user_id: str) -> dict:
        """获取推荐所需的上下文"""
        profile = self.get_profile(user_id)

        return {
            'age': profile.get('age', 30),
            'risk_tolerance': profile.get('risk_tolerance', 'moderate'),
            'investment_amount': profile.get('investment_amount', 10),
            'investment_horizon': profile.get('investment_horizon', 3),
            'max_loss': abs(profile.get('stop_loss', -10)),
            'preferred_sectors': profile.get('preferred_sectors', []),
            'preferred_styles': profile.get('preferred_styles', []),
            'holdings': profile.get('holdings', [])
        }

    def set_stop_loss_profit(self, user_id: str, stop_loss: float = None, stop_profit: float = None):
        """设置止盈止损"""
        profile = self.get_profile(user_id)

        if stop_loss is not None:
            profile['stop_loss'] = -abs(stop_loss)  # 确保是负数

        if stop_profit is not None:
            profile['stop_profit'] = abs(stop_profit)  # 确保是正数

        profile['updated_at'] = datetime.now().isoformat()
        self._save_profiles()

    # ==================== v10.0: 行为偏差画像 ====================

    def assess_behavioral(self, client_id: str, answers: dict = None) -> dict:
        """结合行为问卷/情绪记录/导入历史评估客户行为偏差画像，并写入画像。

        Args:
            client_id: 客户ID
            answers: 行为问卷答案 {q1: 选项下标, ...}（缺省读取已保存的）

        Returns:
            dict: BehavioralBiasEngine.assess 的结果
        """
        try:
            sys.path.insert(0, str(Path(__file__).resolve().parent))
            from behavioral_profile import BehavioralBiasEngine
            eng = BehavioralBiasEngine(data_dir=self.data_dir)
            if answers:
                eng.save_answers(client_id, answers)
            assessment = eng.assess(client_id=client_id, answers=answers)
            profile = self.get_profile(client_id)
            profile['behavioral'] = assessment
            profile['updated_at'] = datetime.now().isoformat()
            self._save_profiles()
            return assessment
        except Exception:
            return {'error': '行为画像评估失败', 'client_id': client_id}

    def get_behavioral_summary(self, client_id: str) -> str:
        """渲染已保存的行为画像摘要（未评估则提示）"""
        profile = self.get_profile(client_id)
        b = profile.get('behavioral')
        if not b or b.get('error'):
            return (f"客户「{client_id}」尚未完成行为画像评估。"
                    f"可通过 assess_client_profile 工具提交 10 题行为问卷。")
        try:
            sys.path.insert(0, str(Path(__file__).resolve().parent))
            from behavioral_profile import BehavioralBiasEngine
            return BehavioralBiasEngine(data_dir=self.data_dir).format_report(b)
        except Exception:
            return f"心理类型: {b.get('investor_type', '未知')}"

    def format_profile_report(self, user_id: str) -> str:
        """格式化画像报告"""
        profile = self.get_profile(user_id)

        lines = []
        lines.append("\n【您的投资画像】")

        if profile.get('age'):
            lines.append(f"  年龄: {profile['age']}岁")

        exp_map = {
            'beginner': '投资新手',
            'intermediate': '有一定经验',
            'experienced': '经验丰富',
            'unknown': '待完善'
        }
        lines.append(f"  投资经验: {exp_map.get(profile.get('investment_experience', 'unknown'), '待完善')}")

        risk_map = {
            'conservative': '保守型（低风险）',
            'moderate': '平衡型（中风险）',
            'aggressive': '积极型（高风险）'
        }
        lines.append(f"  风险承受: {risk_map.get(profile.get('risk_tolerance', 'moderate'), '平衡型')}")

        if profile.get('investment_horizon'):
            lines.append(f"  投资周期: {profile['investment_horizon']}年")

        if profile.get('investment_amount'):
            lines.append(f"  投资金额: {profile['investment_amount']}万元")

        if profile.get('preferred_sectors'):
            lines.append(f"  偏好行业: {', '.join(profile['preferred_sectors'])}")

        lines.append(f"  止损线: {profile.get('stop_loss', -10):.1f}%")
        lines.append(f"  止盈线: {profile.get('stop_profit', 20):.1f}%")

        holdings = profile.get('holdings', [])
        if holdings:
            lines.append(f"  持仓数量: {len(holdings)}只")
        else:
            lines.append("  持仓数量: 暂无记录")

        lines.append("")
        lines.append("要修改画像中的任何信息，请告诉我。")

        return "\n".join(lines)


class UserQuantitativeAssessment:
    """
    客户量化评估模型 v1.0

    评估维度及权重：
    - 年龄 Age: 15%
    - 风险偏好 Risk preference: 25%
    - 投资金额 Investment amount: 10%
    - 投资周期 Investment horizon: 20%
    - 指定公司 Specified companies: 15%
    - 指定经理 Specified managers: 15%

    总分 0-100，分数越高风险承受能力越强
    """

    # 年龄与风险承受映射
    AGE_RISK_MAP = {
        (18, 25): {'score': 90, 'description': '青年期，风险承受能力强'},
        (26, 35): {'score': 80, 'description': '青壮年期，风险承受能力强'},
        (36, 45): {'score': 70, 'description': '中年期前期，风险承受能力中等偏强'},
        (46, 55): {'score': 55, 'description': '中年期，风险承受能力中等'},
        (56, 60): {'score': 40, 'description': '接近退休，风险承受能力较弱'},
        (61, 100): {'score': 25, 'description': '退休后，风险承受能力弱'}
    }

    # 风险偏好与分数映射
    RISK_TOLERANCE_MAP = {
        '保守型': {'score': 20, 'description': '低风险承受，追求稳健'},
        '平衡型': {'score': 50, 'description': '中等风险承受，追求均衡'},
        '积极型': {'score': 75, 'description': '中高风险承受，追求成长'},
        '激进型': {'score': 95, 'description': '高风险承受，追求高收益'}
    }

    # 投资周期与分数映射（越长越能承受波动）
    HORIZON_MAP = {
        (0, 1): {'score': 20, 'description': '短期资金，不宜重仓'},
        (1, 3): {'score': 40, 'description': '中期资金，可适度配置'},
        (3, 5): {'score': 65, 'description': '中长期资金，可承受一定波动'},
        (5, 10): {'score': 85, 'description': '长期资金，可承受较大波动'},
        (10, 100): {'score': 95, 'description': '超长期资金，适合高风险配置'}
    }

    # 投资金额与分数映射（金额越大抗风险能力越强）
    AMOUNT_MAP = {
        (0, 5): {'score': 30, 'description': '小额定投，压力小'},
        (5, 10): {'score': 45, 'description': '中额投资'},
        (10, 20): {'score': 60, 'description': '较大额投资'},
        (20, 50): {'score': 75, 'description': '大额投资'},
        (50, 1000): {'score': 90, 'description': '超大额投资，抗风险能力强'}
    }

    # 权重配置
    WEIGHTS = {
        'age': 0.15,
        'risk_tolerance': 0.25,
        'investment_amount': 0.10,
        'investment_horizon': 0.20,
        'target_companies': 0.15,
        'target_managers': 0.15
    }

    def __init__(self, data_dir=None):
        self.data_dir = data_dir or DATA_DIR
        self.companies_path = self.data_dir / 'fund_companies_distilled.json'
        self.managers_path = self.data_dir / 'fund_managers_distilled.json'
        self._load_data()

    def _load_data(self):
        """加载基金公司和经理数据用于验证指定公司/经理"""
        self.companies_db = {}
        self.managers_db = {}

        try:
            if self.companies_path.exists():
                with open(self.companies_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for company in data.get('companies', []):
                        self.companies_db[company.get('name', '')] = company
        except Exception:
            pass

        try:
            if self.managers_path.exists():
                with open(self.managers_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for manager in data.get('managers', []):
                        self.managers_db[manager.get('name', '')] = manager
        except Exception:
            pass

    def assess_investment_profile(
        self,
        age: int = None,
        risk_tolerance: str = None,
        investment_amount: float = None,
        investment_horizon: int = None,
        target_companies: List[str] = None,
        target_managers: List[str] = None
    ) -> dict:
        """
        评估用户投资画像

        Args:
            age: 年龄
            risk_tolerance: 风险偏好（保守型/平衡型/积极型/激进型）
            investment_amount: 投资金额（万元）
            investment_horizon: 投资周期（年）
            target_companies: 指定基金公司列表
            target_managers: 指定基金经理列表

        Returns:
            dict: 评估结果
        """
        scores = {}
        descriptions = {}

        # 1. 年龄评分 (15%)
        age_score = self._score_age(age)
        scores['age'] = age_score['score']
        descriptions['age'] = age_score['description']

        # 2. 风险偏好评分 (25%)
        risk_score = self._score_risk_tolerance(risk_tolerance)
        scores['risk_tolerance'] = risk_score['score']
        descriptions['risk_tolerance'] = risk_score['description']

        # 3. 投资金额评分 (10%)
        amount_score = self._score_amount(investment_amount)
        scores['investment_amount'] = amount_score['score']
        descriptions['investment_amount'] = amount_score['description']

        # 4. 投资周期评分 (20%)
        horizon_score = self._score_horizon(investment_horizon)
        scores['investment_horizon'] = horizon_score['score']
        descriptions['investment_horizon'] = horizon_score['description']

        # 5. 指定公司评分 (15%)
        company_score = self._score_companies(target_companies)
        scores['target_companies'] = company_score['score']
        descriptions['target_companies'] = company_score['description']

        # 6. 指定经理评分 (15%)
        manager_score = self._score_managers(target_managers)
        scores['target_managers'] = manager_score['score']
        descriptions['target_managers'] = manager_score['description']

        # 计算加权总分
        total_score = sum(scores[k] * self.WEIGHTS[k] for k in self.WEIGHTS)

        # 确定适合的投资风格
        suitable_style = self._determine_style(total_score)

        # 生成推荐配置
        recommended_allocation = self._generate_allocation(total_score)

        return {
            'total_score': round(total_score, 1),
            'risk_level': self._get_risk_level(total_score),
            'suitable_style': suitable_style,
            'scores': scores,
            'weights': self.WEIGHTS,
            'descriptions': descriptions,
            'recommended_allocation': recommended_allocation,
            'suitable_funds': self._recommend_funds(suitable_style, target_companies, target_managers)
        }

    def _score_age(self, age: int) -> dict:
        """年龄评分"""
        if age is None:
            return {'score': 50, 'description': '年龄未知，使用中等评分'}

        for (min_age, max_age), info in self.AGE_RISK_MAP.items():
            if min_age <= age <= max_age:
                return info

        return {'score': 50, 'description': '年龄超出范围，使用中等评分'}

    def _score_risk_tolerance(self, risk_tolerance: str) -> dict:
        """风险偏好评分"""
        if risk_tolerance is None:
            return {'score': 50, 'description': '风险偏好未知，使用中等评分'}

        return self.RISK_TOLERANCE_MAP.get(risk_tolerance, {'score': 50, 'description': '未知偏好'})

    def _score_amount(self, amount: float) -> dict:
        """投资金额评分"""
        if amount is None:
            return {'score': 50, 'description': '金额未知，使用中等评分'}

        for (min_amt, max_amt), info in self.AMOUNT_MAP.items():
            if min_amt <= amount < max_amt:
                return info

        return self.AMOUNT_MAP[(50, 1000)]

    def _score_horizon(self, horizon: int) -> dict:
        """投资周期评分"""
        if horizon is None:
            return {'score': 50, 'description': '周期未知，使用中等评分'}

        for (min_h, max_h), info in self.HORIZON_MAP.items():
            if min_h <= horizon < max_h:
                return info

        return self.HORIZON_MAP[(10, 100)]

    def _score_companies(self, companies: List[str]) -> dict:
        """指定公司评分"""
        if not companies:
            return {'score': 50, 'description': '无指定公司，使用中等评分'}

        valid_count = sum(1 for c in companies if c in self.companies_db)
        if valid_count == len(companies):
            return {'score': 70, 'description': f'指定的{len(companies)}家基金公司都有效'}
        elif valid_count > 0:
            return {'score': 55, 'description': f'{valid_count}/{len(companies)}家指定公司有效'}
        else:
            return {'score': 40, 'description': '指定的基金公司都不在数据库中，将扩大搜索范围'}

    def _score_managers(self, managers: List[str]) -> dict:
        """指定经理评分"""
        if not managers:
            return {'score': 50, 'description': '无指定经理，使用中等评分'}

        valid_count = sum(1 for m in managers if m in self.managers_db)
        if valid_count == len(managers):
            return {'score': 70, 'description': f'指定的{len(managers)}位基金经理都有效'}
        elif valid_count > 0:
            return {'score': 55, 'description': f'{valid_count}/{len(managers)}位指定经理有效'}
        else:
            return {'score': 40, 'description': '指定的基金经理都不在数据库中，将扩大搜索范围'}

    def _get_risk_level(self, total_score: float) -> str:
        """根据总分确定风险等级"""
        if total_score >= 80:
            return '激进型'
        elif total_score >= 65:
            return '积极型'
        elif total_score >= 45:
            return '平衡型'
        else:
            return '保守型'

    def _determine_style(self, total_score: float) -> str:
        """确定适合的投资风格"""
        if total_score >= 80:
            return '成长型'
        elif total_score >= 60:
            return '进取型'
        elif total_score >= 40:
            return '均衡型'
        else:
            return '稳健型'

    def _generate_allocation(self, total_score: float) -> dict:
        """生成推荐配置"""
        if total_score >= 80:
            return {'stocks': 80, 'bonds': 15, 'cash': 5}
        elif total_score >= 65:
            return {'stocks': 65, 'bonds': 25, 'cash': 10}
        elif total_score >= 45:
            return {'stocks': 45, 'bonds': 40, 'cash': 15}
        elif total_score >= 30:
            return {'stocks': 25, 'bonds': 55, 'cash': 20}
        else:
            return {'stocks': 10, 'bonds': 60, 'cash': 30}

    def _recommend_funds(self, style: str, companies: List[str] = None, managers: List[str] = None) -> list:
        """推荐基金列表"""
        recommended = []

        # 根据风格筛选
        style_map = {
            '成长型': ['成长型', '积极型'],
            '进取型': ['成长型', '进取型', '均衡型'],
            '均衡型': ['均衡型', '价值型'],
            '稳健型': ['稳健型', '平衡型', '价值型']
        }

        valid_styles = style_map.get(style, ['均衡型'])

        # 从数据库中筛选
        for company_name, company in self.companies_db.items():
            for product in company.get('products', [])[:3]:  # 每个公司最多3只
                product_style = product.get('investment_style', '')
                if product_style in valid_styles:
                    recommended.append({
                        'fund_code': product.get('fund_code', ''),
                        'fund_name': product.get('fund_name', ''),
                        'company': company_name,
                        'style': product_style,
                        'risk_level': product.get('risk_level', '')
                    })

        return recommended[:10]  # 最多返回10只

    def format_assessment_report(self, assessment: dict) -> str:
        """格式化评估报告"""
        lines = []
        lines.append("\n" + "=" * 60)
        lines.append("  客户量化评估报告")
        lines.append("=" * 60)
        lines.append("")

        # 总分和风险等级
        lines.append(f"【综合评分】{assessment['total_score']:.1f} 分")
        lines.append(f"【风险等级】{assessment['risk_level']}")
        lines.append(f"【适合风格】{assessment['suitable_style']}")
        lines.append("")

        # 分项评分
        lines.append("【分项评分】")
        score_names = {
            'age': '年龄因素',
            'risk_tolerance': '风险偏好',
            'investment_amount': '投资金额',
            'investment_horizon': '投资周期',
            'target_companies': '指定公司',
            'target_managers': '指定经理'
        }
        for key, name in score_names.items():
            score = assessment['scores'].get(key, 0)
            weight = assessment['weights'].get(key, 0)
            desc = assessment['descriptions'].get(key, '')
            lines.append(f"  {name}: {score:.0f}分 (权重{weight*100:.0f}%) - {desc}")
        lines.append("")

        # 推荐配置
        alloc = assessment['recommended_allocation']
        lines.append("【推荐配置】")
        lines.append(f"  股票型基金: {alloc['stocks']}%")
        lines.append(f"  债券型基金: {alloc['bonds']}%")
        lines.append(f"  货币基金: {alloc['cash']}%")
        lines.append("")

        # 推荐基金
        funds = assessment.get('suitable_funds', [])
        if funds:
            lines.append("【推荐基金】")
            for f in funds[:5]:
                lines.append(f"  • {f['fund_name']} ({f['fund_code']})")
                lines.append(f"    风格: {f['style']} | 公司: {f['company']}")
            lines.append("")

        lines.append("=" * 60)
        lines.append("  风险提示：以上内容仅供参考，不构成投资建议")
        lines.append("=" * 60)
        lines.append("")

        return "\n".join(lines)


def main():
    """测试"""
    assessment = UserQuantitativeAssessment()

    print("=== 客户量化评估模型测试 ===\n")

    # 测试完整评估
    result = assessment.assess_investment_profile(
        age=35,
        risk_tolerance='积极型',
        investment_amount=20,
        investment_horizon=5,
        target_companies=['华夏基金', '易方达'],
        target_managers=['张坤', '萧楠']
    )

    print(assessment.format_assessment_report(result))


if __name__ == '__main__':
    main()