"""
宏观经济分析模块 v1.0
为客户经理和基金经理提供宏观经济分析支持
分析维度：GDP、CPI、PPI、PMI、货币政策、财政政策、流动性、汇率等
"""
import json
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, List, Any

# 路径推断
SCRIPT_DIR = Path(__file__).resolve().parent
import sys as _sys; _sys.path.insert(0, str(SCRIPT_DIR.parent))
from fund_advisor_paths import DATA_DIR  # noqa: E402


class MacroIndicator:
    """宏观经济指标"""

    def __init__(self, name_cn, name_en, unit, current_value, previous_value,
                 change_pct, trend, description, signal=None):
        self.name_cn = name_cn
        self.name_en = name_en
        self.unit = unit
        self.current_value = current_value
        self.previous_value = previous_value
        self.change_pct = change_pct
        self.trend = trend  # 'up', 'down', 'stable'
        self.description = description
        self.signal = signal  # 'positive', 'negative', 'neutral'

    def to_dict(self):
        return {
            'name_cn': self.name_cn,
            'name_en': self.name_en,
            'unit': self.unit,
            'current_value': self.current_value,
            'previous_value': self.previous_value,
            'change_pct': self.change_pct,
            'trend': self.trend,
            'description': self.description,
            'signal': self.signal
        }


class MacroAnalyzer:
    """
    宏观经济分析器 v1.0
    支持GDP、CPI、PPI、PMI、货币政策、财政政策、流动性、汇率等分析
    """

    # 指标中文名映射
    INDICATOR_NAMES = {
        'gdp': '国内生产总值',
        'cpi': '居民消费价格指数',
        'ppi': '工业生产者出厂价格',
        'pmi': '采购经理指数',
        'm2': '广义货币供应量',
        '社融': '社会融资规模',
        '存款准备金率': '存款准备金率',
        'LPR': '贷款市场报价利率',
        'mlf': '中期借贷便利',
        '外汇储备': '外汇储备',
        '人民币汇率': '人民币汇率',
        '进出口': '进出口贸易',
        '工业增加值': '工业增加值',
        '固投': '固定资产投资',
        '消费': '社会消费品零售',
        '房价指数': '房价指数',
        '房地产投资': '房地产投资',
        '出口': '出口额',
        '进口': '进口额',
        '贸易顺差': '贸易顺差',
    }

    def __init__(self, data_dir=None):
        self.data_dir = data_dir or DATA_DIR
        self.cache = {}
        self.last_update = None
        # v6.0: 加载真实宏观数据（akshare），失败则回退到原模拟值
        self._real_macro = self._load_real_macro()

    def _load_real_macro(self) -> dict:
        """v6.0: 从 multi_source akshare 加载真实宏观指标。失败返回 {}。"""
        try:
            import sys as _sys
            from pathlib import Path as _Path
            _scripts = _Path(__file__).resolve().parents[1]
            if str(_scripts) not in _sys.path:
                _sys.path.insert(0, str(_scripts))
            _sys.path.insert(0, str(_scripts / "data_collection"))
            from multi_source.akshare_provider import AkshareProvider
            r = AkshareProvider().fetch_macro()
            if r.available and isinstance(r.data, dict):
                return r.data
        except Exception:
            pass
        return {}

    def _real(self, key, default=None):
        """取真实宏观指标值"""
        v = self._real_macro.get(key)
        return v if v is not None else default

    def _load_external_data(self) -> dict:
        """加载外部数据"""
        try:
            path = self.data_dir / 'external_data.json'
            if path.exists():
                with open(path, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception:
            pass
        return {}

    # ==================== 指标数据获取 ====================

    def get_gdp_data(self) -> Dict:
        """获取GDP数据（v6.0: 优先 akshare 真实值，回退模拟）"""
        _real_yoy = self._real("gdp_yoy", 5.2)
        return {
            'current_quarter': '最新',
            'yoy': _real_yoy,  # 同比（v6.0 真实）
            'qoq': 1.6,  # 环比
            'cum_ytd': 5.0,  # 累计
            'target': 5.0,  # 目标
            'status': '符合预期' if 4.5 <= _real_yoy <= 5.5 else ('超预期' if _real_yoy > 5.5 else '低于预期'),
            'data_source': 'akshare' if self._real("gdp_yoy") is not None else 'mock',
            'components': {
                '第一产业': {'yoy': 3.5, 'contribution': 0.8},
                '第二产业': {'yoy': 5.8, 'contribution': 2.4},
                '第三产业': {'yoy': 5.1, 'contribution': 2.0}
            }
        }

    def get_cpi_data(self) -> Dict:
        """获取CPI数据（v6.0: 优先 akshare 真实值）"""
        _real_yoy = self._real("cpi_yoy", 0.3)
        return {
            'current_month': '最新',
            'yoy': _real_yoy,
            'mom': -0.1,
            'core_cpi': 0.5,
            'food': 0.1,
            'non_food': 0.4,
            'status': '低位运行' if _real_yoy < 1 else ('温和' if _real_yoy < 3 else '偏高'),
            'impact': '通缩压力' if _real_yoy < 0 else '温和',
            'data_source': 'akshare' if self._real("cpi_yoy") is not None else 'mock',
        }

    def get_ppi_data(self) -> Dict:
        """获取PPI数据（v6.0: 优先 akshare 真实值）"""
        _real_yoy = self._real("ppi_yoy", -2.5)
        return {
            'current_month': '最新',
            'yoy': _real_yoy,
            'mom': 0.2,
            'status': '负值区间' if _real_yoy < 0 else '正值区间',
            'impact': '企业盈利承压' if _real_yoy < 0 else '企业盈利改善',
            'data_source': 'akshare' if self._real("ppi_yoy") is not None else 'mock',
        }

    def get_pmi_data(self) -> Dict:
        """获取PMI数据（v6.0: 优先 akshare 真实值）"""
        _real_pmi = self._real("pmi", 50.8)
        return {
            'manufacturing': {
                'value': _real_pmi,
                'status': '扩张区间' if _real_pmi >= 50 else '收缩区间',
                'new_orders': 51.2,
                'output': 51.5,
                'employment': 49.8
            },
            'non_manufacturing': {
                'value': 52.5,
                'status': '扩张区间',
                'business_activity': 52.8,
                'new_orders': 52.0
            },
            'data_source': 'akshare' if self._real("pmi") is not None else 'mock',
        }

    def get_money_supply_data(self) -> Dict:
        """获取货币供应量数据（v6.0: 优先 akshare 真实值）"""
        _real_m2 = self._real("m2_yoy", 8.3)
        _real_m1 = self._real("m1_yoy", 5.2)
        return {
            'M2': {
                'value': 315.0,  # 万亿
                'yoy': _real_m2,
                'mom': 0.2,
                'status': '平稳增长' if 7 <= _real_m2 <= 10 else ('偏快' if _real_m2 > 10 else '偏慢')
            },
            'M1': {
                'value': 68.5,
                'yoy': _real_m1,
                'status': '活化不足' if _real_m1 < 5 else '活化改善'
            },
            'M0': {
                'value': 12.8,
                'yoy': 12.5,
                'status': '流通增加'
            },
            'data_source': 'akshare' if self._real("m2_yoy") is not None else 'mock',
        }

    def get_interest_rate_data(self) -> Dict:
        """获取利率数据（v6.0: 优先 akshare 真实 LPR）"""
        _real_lpr1 = self._real("lpr_1y", 3.45)
        _real_lpr5 = self._real("lpr_5y", 3.95)
        return {
            'policy_rate': {
                '7天逆回购': 1.8,
                'MLF': 2.5,
                'LPR1Y': _real_lpr1,
                'LPR5Y': _real_lpr5,
                'status': '宽松导向'
            },
            'market_rate': {
                'SHIBOR隔夜': 1.75,
                'SHIBOR1年': 2.25,
                '国债10Y': 2.15,
                'status': '利率下行'
            }
        }

    def get_reserve_ratio_data(self) -> Dict:
        """获取存款准备金率数据"""
        return {
            '大型机构': 10.5,
            '中小机构': 7.5,
            'last_cut': '2024-09',
            'next_expected': '2026Q2',
            'status': '有下调空间'
        }

    def get_exchange_rate_data(self) -> Dict:
        """获取汇率数据"""
        return {
            'USD_CNY': 7.25,
            'EUR_CNY': 7.85,
            'JPY_CNY': 0.048,
            'trend': '小幅贬值',
            'status': '波动可控'
        }

    def get_trade_data(self) -> Dict:
        """获取贸易数据"""
        return {
            'current_month': '2026-04',
            '出口': {
                'value': 3100,  # 亿美元
                'yoy': 5.2
            },
            '进口': {
                'value': 2300,
                'yoy': 3.8
            },
            'trade_balance': {
                'value': 800,
                'status': '顺差扩大'
            }
        }

    def get_industrial_data(self) -> Dict:
        """获取工业数据"""
        return {
            '工业增加值': {
                'yoy': 6.2,
                'status': '恢复增长'
            },
            '用电量': {
                'yoy': 5.8,
                'status': '平稳'
            },
            '货运量': {
                'yoy': 4.5,
                'status': '恢复'
            }
        }

    def get_real_estate_data(self) -> Dict:
        """获取房地产数据"""
        return {
            '投资': {'yoy': -8.5, 'status': '继续探底'},
            '销售': {'yoy': -15.2, 'status': '需求不足'},
            '价格': {'yoy': -3.2, 'status': '环比降幅收窄'},
            '到位资金': {'yoy': -18.5, 'status': '资金紧张'},
            '总体判断': '行业调整周期，政策支持下企稳迹象'
        }

    def get_social_finance_data(self) -> Dict:
        """获取社会融资数据"""
        return {
            '存量': 385.0,  # 万亿
            'yoy': 9.2,
            '新增': {
                '人民币贷款': 18.5,
                '企业债券': 3.2,
                '政府债券': 5.8,
                '表外融资': -1.5
            },
            'status': '结构改善'
        }

    # ==================== 综合分析 ====================

    def analyze_macro_conditions(self) -> Dict:
        """综合分析宏观经济形势"""
        gdp = self.get_gdp_data()
        cpi = self.get_cpi_data()
        ppi = self.get_ppi_data()
        pmi = self.get_pmi_data()
        money = self.get_money_supply_data()
        interest = self.get_interest_rate_data()
        trade = self.get_trade_data()
        estate = self.get_real_estate_data()
        sf = self.get_social_finance_data()

        # 综合评分（0-100）
        score = 50

        # GDP贡献
        if gdp['yoy'] >= 5.0:
            score += 10
        elif gdp['yoy'] < 4.5:
            score -= 10

        # 通胀状况
        if cpi['yoy'] < 0:
            score -= 5  # 通缩风险
        elif 0.5 <= cpi['yoy'] <= 2.0:
            score += 5  # 温和通胀
        else:
            score -= 5  # 过热或过冷

        # PMI状况
        if pmi['manufacturing']['value'] >= 50:
            score += 5
        else:
            score -= 5

        # 货币环境
        if money['M2']['yoy'] > 8:
            score += 5  # 宽松

        # 房地产
        if estate['投资']['yoy'] < -10:
            score -= 10

        # 贸易
        if trade['trade_balance']['value'] > 0:
            score += 5

        score = max(0, min(100, score))

        # 宏观状态判断
        if score >= 70:
            status = '经济景气'
            description = '经济运行平稳，结构持续优化'
        elif score >= 50:
            status = '经济承压'
            description = '面临下行压力，但政策支持力度加大'
        elif score >= 30:
            status = '经济偏弱'
            description = '内外需不足，经济活跃度偏低'
        else:
            status = '经济低迷'
            description = '需要更强有力的宏观政策支持'

        # 政策建议
        if score < 50:
            policy_suggestion = '建议货币政策继续保持宽松，财政政策加力提效'
        elif score >= 70:
            policy_suggestion = '宏观政策保持稳定，避免大水漫灌'
        else:
            policy_suggestion = '宏观政策相机抉择，根据数据动态调整'

        return {
            'score': score,
            'status': status,
            'description': description,
            'policy_suggestion': policy_suggestion,
            'key_indicators': {
                'gdp': gdp,
                'cpi': cpi,
                'ppi': ppi,
                'pmi': pmi,
                'money_supply': money,
                'interest_rate': interest,
                'trade': trade,
                'real_estate': estate,
                'social_finance': sf
            },
            'analyzed_at': datetime.now().strftime('%Y-%m-%d %H:%M')
        }

    def analyze_policy_direction(self) -> Dict:
        """分析政策方向"""
        interest = self.get_interest_rate_data()
        money = self.get_money_supply_data()
        reserve = self.get_reserve_ratio_data()

        directions = []

        # 货币政策方向
        if interest['policy_rate']['7天逆回购'] < 2.0:
            directions.append({
                'type': '货币政策',
                'direction': '宽松',
                'detail': '逆回购利率处于低位，流动性保持充裕',
                'strength': '中等'
            })
        else:
            directions.append({
                'type': '货币政策',
                'direction': '中性',
                'detail': '政策利率稳定，流动性合理适度',
                'strength': '温和'
            })

        # 准备金率
        if reserve['next_expected']:
            directions.append({
                'type': '准备金率',
                'direction': '可能下调',
                'detail': f'上次调整{reserve["last_cut"]}，下次可能在{reserve["next_expected"]}',
                'strength': '弱'
            })

        # 财政政策
        directions.append({
            'type': '财政政策',
            'direction': '积极',
            'detail': '赤字率和专项债规模保持较高水平，基建投资托底',
            'strength': '强'
        })

        # 房地产政策
        directions.append({
            'type': '房地产政策',
            'direction': '支持',
            'detail': '多地取消限购限贷，房贷利率持续下调，政策空间打开',
            'strength': '中等'
        })

        # 资本市场政策
        directions.append({
            'type': '资本市场政策',
            'direction': '呵护',
            'detail': '引导长期资金入市，完善分红机制，稳定市场预期',
            'strength': '中等'
        })

        return {
            'policy_count': len(directions),
            'directions': directions,
            'overall_direction': '宽松+积极',
            'impact_on_market': '流动性改善，利率下行，权益资产受益'
        }

    def analyze_liquidity(self) -> Dict:
        """分析流动性状况"""
        money = self.get_money_supply_data()
        interest = self.get_interest_rate_data()

        # 流动性评分
        score = 50

        # M2增速
        if money['M2']['yoy'] > 10:
            score += 15
        elif money['M2']['yoy'] > 8:
            score += 10
        elif money['M2']['yoy'] < 7:
            score -= 10

        # 利率水平
        if interest['market_rate']['SHIBOR隔夜'] < 1.5:
            score += 10
        elif interest['market_rate']['SHIBOR隔夜'] > 2.5:
            score -= 10

        # M1增速（反映实体活化度）
        if money['M1']['yoy'] > 8:
            score += 5
        elif money['M1']['yoy'] < 3:
            score -= 5

        score = max(0, min(100, score))

        if score >= 70:
            status = '流动性充裕'
        elif score >= 50:
            status = '流动性合理'
        elif score >= 30:
            status = '流动性偏紧'
        else:
            status = '流动性紧张'

        return {
            'score': score,
            'status': status,
            'm2_yoy': money['M2']['yoy'],
            'shibor_overnight': interest['market_rate']['SHIBOR隔夜'],
            'bond_yield_10y': interest['market_rate']['国债10Y'],
            'assessment': f'{status}，{"资金面宽松" if score > 60 else "资金面平稳" if score > 40 else "资金面偏紧"}',
            'implications': {
                'stock_market': '利好' if score > 60 else '中性',
                'bond_market': '利好' if score > 50 else '偏利空',
                'real_estate': '边际改善' if score > 40 else '仍承压'
            }
        }

    def analyze_sector_correlation(self, sector: str) -> Dict:
        """
        分析宏观因素对特定板块的影响
        sector: 科技、消费、金融、地产、医药、制造、军工、新能源等
        """
        macro = self.analyze_macro_conditions()
        policy = self.analyze_policy_direction()
        liquidity = self.analyze_liquidity()

        # 板块-宏观因素映射
        sector_correlations = {
            '科技': {
                'gdp_weight': 0.3,
                'policy_weight': 0.4,
                'liquidity_weight': 0.3,
                'positive_factors': ['政策支持', '产业升级', '创新驱动'],
                'negative_factors': ['出口承压', '技术封锁', '估值偏高'],
                'macro_sensitivity': '高'
            },
            '消费': {
                'gdp_weight': 0.5,
                'policy_weight': 0.2,
                'liquidity_weight': 0.3,
                'positive_factors': ['消费升级', '扩大内需', '促销费政策'],
                'negative_factors': ['就业压力', '收入放缓', '消费意愿低'],
                'macro_sensitivity': '高'
            },
            '金融': {
                'gdp_weight': 0.4,
                'policy_weight': 0.4,
                'liquidity_weight': 0.2,
                'positive_factors': ['资本市场改革', '利率下行', '流动性宽松'],
                'negative_factors': ['资产质量压力', '息差收窄', '风险暴露'],
                'macro_sensitivity': '中'
            },
            '地产': {
                'gdp_weight': 0.5,
                'policy_weight': 0.4,
                'liquidity_weight': 0.1,
                'positive_factors': ['政策支持', '利率下行', '估值低位'],
                'negative_factors': ['销售疲软', '资金紧张', '信心不足'],
                'macro_sensitivity': '极高'
            },
            '医药': {
                'gdp_weight': 0.3,
                'policy_weight': 0.4,
                'liquidity_weight': 0.3,
                'positive_factors': ['老龄化', '政策支持', '刚性需求'],
                'negative_factors': ['集采压力', '研发风险', '估值调整'],
                'macro_sensitivity': '低'
            },
            '制造': {
                'gdp_weight': 0.5,
                'policy_weight': 0.3,
                'liquidity_weight': 0.2,
                'positive_factors': ['产业升级', '出口韧性', '设备更新'],
                'negative_factors': ['需求放缓', '成本压力', '外需疲软'],
                'macro_sensitivity': '中'
            },
            '军工': {
                'gdp_weight': 0.2,
                'policy_weight': 0.5,
                'liquidity_weight': 0.3,
                'positive_factors': ['国防支出增加', '国际局势', '政策支持'],
                'negative_factors': ['采购节奏', '定价压力', '透明度低'],
                'macro_sensitivity': '低'
            },
            '新能源': {
                'gdp_weight': 0.3,
                'policy_weight': 0.5,
                'liquidity_weight': 0.2,
                'positive_factors': ['双碳政策', '成本下降', '渗透率提升'],
                'negative_factors': ['竞争加剧', '产能过剩', '出口受限'],
                'macro_sensitivity': '中'
            }
        }

        sector_info = sector_correlations.get(sector, sector_correlations['制造'])

        # 计算综合得分
        score = (
            macro['score'] * sector_info['gdp_weight'] +
            (80 if policy['overall_direction'] == '宽松+积极' else 50) * sector_info['policy_weight'] +
            liquidity['score'] * sector_info['liquidity_weight']
        )
        score = int(score)

        # 判断宏观环境对板块的影响
        if score >= 70:
            outlook = '乐观'
            recommendation = '宏观环境支持，可适度配置'
        elif score >= 50:
            outlook = '中性'
            recommendation = '宏观环境一般，精选个股为主'
        else:
            outlook = '谨慎'
            recommendation = '宏观承压，控制仓位，等待政策加码'

        return {
            'sector': sector,
            'macro_score': score,
            'outlook': outlook,
            'recommendation': recommendation,
            'sensitivity': sector_info['macro_sensitivity'],
            'positive_factors': sector_info['positive_factors'],
            'negative_factors': sector_info['negative_factors'],
            'macro_conditions': {
                'economic_status': macro['status'],
                'policy_direction': policy['overall_direction'],
                'liquidity_status': liquidity['status']
            },
            'analyzed_at': datetime.now().strftime('%Y-%m-%d %H:%M')
        }

    def get_economic_calendar(self) -> List[Dict]:
        """获取近期重要经济数据发布时间"""
        today = datetime.now()
        calendar = []

        # 模拟日历，实际应用中应联网获取
        events = [
            {'date': (today + timedelta(days=3)).strftime('%Y-%m-%d'), 'event': '中国CPI数据发布', 'importance': '高'},
            {'date': (today + timedelta(days=5)).strftime('%Y-%m-%d'), 'event': '中国进出口数据发布', 'importance': '高'},
            {'date': (today + timedelta(days=7)).strftime('%Y-%m-%d'), 'event': '中国金融数据发布(M2/社融)', 'importance': '高'},
            {'date': (today + timedelta(days=10)).strftime('%Y-%m-%d'), 'event': '中国GDP数据发布', 'importance': '极高'},
            {'date': (today + timedelta(days=12)).strftime('%Y-%m-%d'), 'event': '美联储议息会议', 'importance': '高'},
            {'date': (today + timedelta(days=15)).strftime('%Y-%m-%d'), 'event': '中国LPR数据发布', 'importance': '中'},
            {'date': (today + timedelta(days=18)).strftime('%Y-%m-%d'), 'event': '中国PMI数据发布', 'importance': '高'},
        ]

        for e in events:
            calendar.append({
                'date': e['date'],
                'event': e['event'],
                'importance': e['importance'],
                'days_until': (datetime.strptime(e['date'], '%Y-%m-%d') - today).days
            })

        return sorted(calendar, key=lambda x: x['days_until'])

    # ==================== 格式化输出 ====================

    def format_macro_report(self, analysis: Dict = None) -> str:
        """格式化宏观经济分析报告"""
        if not analysis:
            analysis = self.analyze_macro_conditions()

        lines = []
        lines.append('\n' + '=' * 70)
        lines.append('  宏观经济分析报告')
        lines.append('=' * 70)

        # 总体评价
        lines.append(f"\n【总体评价】")
        lines.append(f"  宏观评分: {analysis['score']}/100")
        lines.append(f"  运行状态: {analysis['status']}")
        lines.append(f"  基本判断: {analysis['description']}")
        lines.append(f"  政策建议: {analysis['policy_suggestion']}")

        # 核心指标
        ki = analysis.get('key_indicators', {})
        lines.append(f"\n【核心指标】")

        # GDP
        gdp = ki.get('gdp', {})
        lines.append(f"  GDP: {gdp.get('yoy', 0)}% 同比 | {gdp.get('qoq', 0)}% 环比 | {gdp.get('cum_ytd', 0)}% 累计")
        lines.append(f"       目标{gdp.get('target', 0)}% | 状态: {gdp.get('status', '')}")

        # CPI/PPI
        cpi = ki.get('cpi', {})
        ppi = ki.get('ppi', {})
        lines.append(f"  CPI: {cpi.get('yoy', 0)}% 同比 | 核心{cpi.get('core_cpi', 0)}% | {cpi.get('status', '')}")
        lines.append(f"  PPI: {ppi.get('yoy', 0)}% 同比 | {ppi.get('status', '')}")

        # PMI
        pmi = ki.get('pmi', {})
        mfg = pmi.get('manufacturing', {})
        non_mfg = pmi.get('non_manufacturing', {})
        lines.append(f"  制造业PMI: {mfg.get('value', 0)} | {mfg.get('status', '')}")
        lines.append(f"  非制造业PMI: {non_mfg.get('value', 0)} | {non_mfg.get('status', '')}")

        # 货币
        money = ki.get('money_supply', {})
        lines.append(f"  M2: {money.get('M2', {}).get('value', 0)}万亿 | {money.get('M2', {}).get('yoy', 0)}%")

        # 利率
        interest = ki.get('interest_rate', {})
        policy = interest.get('policy_rate', {})
        market = interest.get('market_rate', {})
        lines.append(f"  政策利率: 7天逆回购{policy.get('7天逆回购', 0)}% | LPR1Y{policy.get('LPR1Y', 0)}%")
        lines.append(f"  市场利率: SHIBOR隔夜{market.get('SHIBOR隔夜', 0)}% | 10Y国债{market.get('国债10Y', 0)}%")

        # 贸易
        trade = ki.get('trade', {})
        lines.append(f"  出口: {trade.get('出口', {}).get('value', 0)}亿美元 | {trade.get('出口', {}).get('yoy', 0)}%")
        lines.append(f"  进口: {trade.get('进口', {}).get('value', 0)}亿美元 | {trade.get('进口', {}).get('yoy', 0)}%")
        lines.append(f"  顺差: {trade.get('trade_balance', {}).get('value', 0)}亿美元 | {trade.get('trade_balance', {}).get('status', '')}")

        # 房地产
        estate = ki.get('real_estate', {})
        lines.append(f"  房地产: 投资{estate.get('投资', {}).get('yoy', 0)}% | 销售{estate.get('销售', {}).get('yoy', 0)}%")
        lines.append(f"  总体: {estate.get('总体判断', '')}")

        lines.append(f"\n【分析时间】{analysis.get('analyzed_at', '')}")
        lines.append('\n' + '=' * 70)

        return '\n'.join(lines)

    def format_sector_macro_report(self, sector: str) -> str:
        """格式化板块宏观分析报告"""
        analysis = self.analyze_sector_correlation(sector)

        lines = []
        lines.append('\n' + '=' * 70)
        lines.append(f'  板块宏观分析报告 — {sector}')
        lines.append('=' * 70)

        lines.append(f"\n【宏观评分】{analysis['macro_score']}/100")
        lines.append(f"  前景判断: {analysis['outlook']}")
        lines.append(f"  配置建议: {analysis['recommendation']}")
        lines.append(f"  宏观敏感度: {analysis['sensitivity']}")

        lines.append(f"\n【有利因素】")
        for f in analysis['positive_factors']:
            lines.append(f"  ✓ {f}")

        lines.append(f"\n【不利因素】")
        for f in analysis['negative_factors']:
            lines.append(f"  ✗ {f}")

        mc = analysis.get('macro_conditions', {})
        lines.append(f"\n【宏观环境】")
        lines.append(f"  经济状态: {mc.get('economic_status', '')}")
        lines.append(f"  政策方向: {mc.get('policy_direction', '')}")
        lines.append(f"  流动性: {mc.get('liquidity_status', '')}")

        lines.append(f"\n【分析时间】{analysis.get('analyzed_at', '')}")
        lines.append('\n' + '=' * 70)

        return '\n'.join(lines)

    def format_policy_report(self) -> str:
        """格式化政策分析报告"""
        policy = self.analyze_policy_direction()

        lines = []
        lines.append('\n' + '=' * 70)
        lines.append('  宏观政策分析报告')
        lines.append('=' * 70)

        lines.append(f"\n【总体方向】{policy['overall_direction']}")
        lines.append(f"  对市场影响: {policy['impact_on_market']}")

        lines.append(f"\n【政策动向】")
        for d in policy['directions']:
            lines.append(f"  {d['type']}: {d['direction']} ({d['strength']})")
            lines.append(f"    {d['detail']}")

        return '\n'.join(lines)

    def format_liquidity_report(self) -> str:
        """格式化流动性分析报告"""
        liq = self.analyze_liquidity()

        lines = []
        lines.append('\n' + '=' * 70)
        lines.append('  流动性分析报告')
        lines.append('=' * 70)

        lines.append(f"\n【流动性评分】{liq['score']}/100")
        lines.append(f"  状态: {liq['status']}")
        lines.append(f"  评估: {liq['assessment']}")

        lines.append(f"\n【关键指标】")
        lines.append(f"  M2同比: {liq['m2_yoy']}%")
        lines.append(f"  SHIBOR隔夜: {liq['shibor_overnight']}%")
        lines.append(f"  10Y国债: {liq['bond_yield_10y']}%")

        lines.append(f"\n【市场影响】")
        for k, v in liq.get('implications', {}).items():
            lines.append(f"  {k}: {v}")

        return '\n'.join(lines)

    def format_economic_calendar_report(self) -> str:
        """格式化经济日历报告"""
        calendar = self.get_economic_calendar()

        lines = []
        lines.append('\n' + '=' * 70)
        lines.append('  重要经济数据日历')
        lines.append('=' * 70)

        for e in calendar[:10]:
            importance_marker = '🔴' if e['importance'] == '极高' else ('🟠' if e['importance'] == '高' else '🟡')
            lines.append(f"\n  {importance_marker} {e['date']} | {e['event']}")
            lines.append(f"      距离: {e['days_until']}天")

        lines.append('\n' + '=' * 70)

        return '\n'.join(lines)


# ==================== 集成到对话引擎的支持函数 ====================

def get_macro_summary() -> str:
    """获取宏观分析摘要（用于对话）"""
    analyzer = MacroAnalyzer()
    analysis = analyzer.analyze_macro_conditions()

    policy = analyzer.analyze_policy_direction()
    liq = analyzer.analyze_liquidity()

    summary = f"""当前宏观经济形势：

📊 宏观评分：{analysis['score']}/100（{analysis['status']}）
{analysis['description']}

📈 核心数据：
• GDP同比{analysis['key_indicators'].get('gdp', {}).get('yoy', 0)}%，目标{analysis['key_indicators'].get('gdp', {}).get('target', 0)}%
• CPI{analysis['key_indicators'].get('cpi', {}).get('yoy', 0)}%，PPI{analysis['key_indicators'].get('ppi', {}).get('yoy', 0)}%
• 制造业PMI{analysis['key_indicators'].get('pmi', {}).get('manufacturing', {}).get('value', 0)}

💰 政策方向：{policy['overall_direction']}
{policy['impact_on_market']}

💧 流动性：{liq['status']}
{liq['assessment']}

⚠️ {analysis['policy_suggestion']}"""

    return summary


def get_sector_macro_analysis(sector: str) -> str:
    """获取板块宏观分析（用于对话）"""
    analyzer = MacroAnalyzer()
    return analyzer.format_sector_macro_report(sector)


# ==================== 测试 ====================

if __name__ == '__main__':
    analyzer = MacroAnalyzer()

    print("=== 宏观经济分析报告 ===")
    print(analyzer.format_macro_report())

    print("\n=== 板块宏观分析 ===")
    print(analyzer.format_sector_macro_report('科技'))

    print("\n=== 政策分析 ===")
    print(analyzer.format_policy_report())

    print("\n=== 流动性分析 ===")
    print(analyzer.format_liquidity_report())

    print("\n=== 经济日历 ===")
    print(analyzer.format_economic_calendar_report())