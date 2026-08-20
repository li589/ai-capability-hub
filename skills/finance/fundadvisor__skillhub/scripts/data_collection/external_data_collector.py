"""
基金外部数据采集脚本
采集：基金评级、收益概率、风险指标、用户评价
"""
import akshare as ak
import json
import os
import time
from datetime import datetime

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(os.path.dirname(SCRIPT_DIR))
DATA_DIR = os.path.join(BASE_DIR, 'data')

class ExternalDataCollector:
    """外部数据采集器"""

    def __init__(self):
        self.cache = {}

    def collect_all(self):
        """采集所有外部数据"""
        print("=" * 60)
        print("开始采集外部数据")
        print("=" * 60)

        # 1. 基金评级数据
        print("\n[1/4] 采集基金评级数据...")
        ratings = self.collect_ratings()

        # 2. 基金详细分析数据
        print("\n[2/4] 采集基金详细分析数据...")
        analysis = self.collect_analysis()

        # 3. 收益概率数据
        print("\n[3/4] 采集收益概率数据...")
        profit_prob = self.collect_profit_probability()

        # 4. 天天基金用户评价（尝试获取）
        print("\n[4/4] 采集用户评价数据...")
        user_feedback = self.collect_user_feedback()

        # 保存所有数据
        output = {
            'ratings': ratings,
            'analysis': analysis,
            'profit_probability': profit_prob,
            'user_feedback': user_feedback,
            'meta': {
                'last_update': datetime.now().strftime('%Y-%m-%d'),
                'source': '天天基金网/雪球/晨星'
            }
        }

        output_path = f'{DATA_DIR}/external_data.json'
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output, f, ensure_ascii=False, indent=2)

        print(f"\n数据已保存: {output_path}")
        print(f"  评级记录: {len(ratings)}")
        print(f"  分析记录: {len(analysis)}")
        print(f"  收益概率: {len(profit_prob)}")
        print(f"  用户评价: {len(user_feedback)}")

        return output

    def collect_ratings(self):
        """采集基金评级"""
        ratings = []

        try:
            df = ak.fund_rating_all()
            print(f"  获取到 {len(df)} 条评级记录")

            for _, row in df.iterrows():
                code = str(row.get('代码', ''))
                ratings.append({
                    'fund_code': code,
                    'fund_name': row.get('简称', ''),
                    'manager': row.get('基金经理', ''),
                    'company': row.get('基金公司', ''),
                    'star_5_count': row.get('5星评级家数', 0),
                    'shanghai_star': row.get('上海证券', 0),
                    'cms_star': row.get('招商证券', 0),
                    'jajx_star': row.get('济安金信', 0),
                    'morning_star': row.get('晨星评级', 0),
                    'fee': row.get('手续费', 0),
                    'fund_type': row.get('类型', ''),
                })
        except Exception as e:
            print(f"  评级采集失败: {e}")

        return ratings

    def collect_analysis(self):
        """采集基金详细分析（夏普比率、回撤等）"""
        analysis = []

        # 先获取有评级的基金代码列表
        ratings_data = self.cache.get('ratings', [])
        if not ratings_data:
            try:
                df = ak.fund_rating_all()
                fund_codes = df['代码'].astype(str).unique().tolist()[:100]  # 限制数量避免太慢
            except (json.JSONDecodeError, OSError, ValueError, KeyError, TypeError):
                fund_codes = []
        else:
            fund_codes = list(set(r.get('fund_code', '') for r in ratings_data))[:100]

        print(f"  准备采集 {len(fund_codes)} 个基金的分析数据...")

        for i, code in enumerate(fund_codes):
            try:
                df = ak.fund_individual_analysis_xq(symbol=code)
                if not df.empty:
                    for _, row in df.iterrows():
                        analysis.append({
                            'fund_code': code,
                            'period': row.get('周期', ''),
                            'risk_return_ratio': row.get('较同类风险收益比', 0),
                            'anti_risk_ratio': row.get('较同类抗风险波动', 0),
                            'annual_volatility': row.get('年化波动率', 0),
                            'sharpe_ratio': row.get('年化夏普比率', 0),
                            'max_drawdown': row.get('最大回撤', 0),
                        })
            except (json.JSONDecodeError, OSError, ValueError, KeyError, TypeError):
                pass

            if (i + 1) % 20 == 0:
                print(f"  进度: {i+1}/{len(fund_codes)}")

            time.sleep(0.1)

        print(f"  获取到 {len(analysis)} 条分析记录")
        return analysis

    def collect_profit_probability(self):
        """采集收益概率"""
        profit_prob = []

        # 使用有评级的基金
        ratings_data = self.cache.get('ratings', [])
        if not ratings_data:
            try:
                df = ak.fund_rating_all()
                fund_codes = df['代码'].astype(str).unique().tolist()[:100]
            except (json.JSONDecodeError, OSError, ValueError, KeyError, TypeError):
                fund_codes = []
        else:
            fund_codes = list(set(r.get('fund_code', '') for r in ratings_data))[:100]

        print(f"  准备采集 {len(fund_codes)} 个基金的收益概率...")

        for i, code in enumerate(fund_codes):
            try:
                df = ak.fund_individual_profit_probability_xq(symbol=code)
                if not df.empty:
                    for _, row in df.iterrows():
                        profit_prob.append({
                            'fund_code': code,
                            'holding_period': row.get('持有时长', ''),
                            'profit_probability': row.get('盈利概率', 0),
                            'avg_return': row.get('平均收益', 0),
                        })
            except (json.JSONDecodeError, OSError, ValueError, KeyError, TypeError):
                pass

            if (i + 1) % 20 == 0:
                print(f"  进度: {i+1}/{len(fund_codes)}")

            time.sleep(0.1)

        print(f"  获取到 {len(profit_prob)} 条收益概率记录")
        return profit_prob

    def collect_user_feedback(self):
        """采集用户评价"""
        feedback = []

        # 天天基金网的用户评价接口可能需要更多探索
        # 目前先返回空列表，后续可以补充
        try:
            # 尝试从雪球获取基金讨论数据
            # 注意：这是一个占位，后续可根据实际接口补充
            pass
        except Exception as e:
            print(f"  用户评价采集跳过: {e}")

        return feedback


def main():
    collector = ExternalDataCollector()

    print("=" * 60)
    print("基金外部数据采集")
    print("内容：基金评级、收益概率、风险指标")
    print("=" * 60)

    data = collector.collect_all()

    # 展示示例
    print("\n" + "=" * 60)
    print("示例数据")
    print("=" * 60)

    if data.get('ratings'):
        print("\n【基金评级示例】")
        r = data['ratings'][0]
        print(f"  基金: {r['fund_name']}({r['fund_code']})")
        print(f"  晨星评级: {r['morning_star']}星")
        print(f"  招商评级: {r['cms_star']}星")
        print(f"  济安金信: {r['jajx_star']}星")
        print(f"  上海证券: {r['shanghai_star']}星")

    if data.get('analysis'):
        print("\n【基金分析示例】")
        a = data['analysis'][0]
        print(f"  周期: {a['period']}")
        print(f"  夏普比率: {a['sharpe_ratio']}")
        print(f"  最大回撤: {a['max_drawdown']}%")
        print(f"  年化波动率: {a['annual_volatility']}%")

    if data.get('profit_probability'):
        print("\n【收益概率示例】")
        p = data['profit_probability'][0]
        print(f"  持有时长: {p['holding_period']}")
        print(f"  盈利概率: {p['profit_probability']}%")
        print(f"  平均收益: {p['avg_return']}%")

    print("\n" + "=" * 60)
    print("采集完成!")
    print("=" * 60)


if __name__ == "__main__":
    main()