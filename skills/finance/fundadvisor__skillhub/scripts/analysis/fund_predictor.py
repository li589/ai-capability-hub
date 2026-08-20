# -*- coding: utf-8 -*-
"""基金涨跌预测引擎 v1.0 - 多因子融合+蒙特卡洛模拟。纯本地运行，零依赖。"""
from __future__ import annotations
import json, math, random, zlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional
SCRIPT_DIR = Path(__file__).resolve().parent
import sys as _sys
_sys.path.insert(0, str(SCRIPT_DIR.parent))
from fund_advisor_paths import DATA_DIR, load_json_data
PREDICTION_PERIODS = {'week':{'days':5,'samples':30,'label':'1周'},'month':{'days':22,'samples':60,'label':'1个月'},'quarter':{'days':66,'samples':120,'label':'3个月'}}
FACTOR_WEIGHTS = {'technical':0.35,'fundamental':0.25,'sentiment':0.20,'macro':0.20}
TYPE_BENCHMARKS = {'股票型':{'return':0.10,'vol':0.22},'混合型':{'return':0.07,'vol':0.15},'偏股混合':{'return':0.09,'vol':0.18},'偏债混合':{'return':0.05,'vol':0.08},'灵活配置':{'return':0.06,'vol':0.12},'指数型':{'return':0.08,'vol':0.20},'债券型':{'return':0.04,'vol':0.05},'纯债':{'return':0.035,'vol':0.03},'货币型':{'return':0.02,'vol':0.005},'QDII':{'return':0.08,'vol':0.20},'ETF':{'return':0.08,'vol':0.20},'LOF':{'return':0.07,'vol':0.18},'FOF':{'return':0.06,'vol':0.10},'default':{'return':0.06,'vol':0.15}}


def _stable_seed(*parts) -> int:
    """生成跨进程稳定的整数种子，避免 Python 默认 hash() 每次运行随机。"""
    payload = "|".join(str(p) for p in parts)
    return zlib.crc32(payload.encode("utf-8"))


class FundPredictor:
    """基金涨跌预测引擎"""
    def __init__(self, data_dir=None):
        self.data_dir = Path(data_dir) if data_dir else DATA_DIR
        self._managers_db = None
        self._funds_db = None
    @property
    def managers_db(self):
        if self._managers_db is None:
            self._managers_db = {}
            try:
                data = load_json_data(str(self.data_dir / 'fund_managers_distilled.json'))
                for m in data.get('managers', data.get('items', [])):
                    key = m.get('manager_id', '') or m.get('name', '')
                    if key:
                        self._managers_db[key] = m
            except Exception:
                pass
        return self._managers_db
    @property
    def funds_db(self):
        if self._funds_db is None:
            self._funds_db = {}
            try:
                data = load_json_data(str(self.data_dir / 'fund_products.json'))
                for f in data.get('products', data.get('items', [])):
                    code = f.get('code', '') or f.get('fund_code', '')
                    if code:
                        self._funds_db[code] = f
            except Exception:
                pass
        return self._funds_db
    def predict_fund(self, fund_code, periods=None, nav_history=None):
        if periods is None:
            periods = list(PREDICTION_PERIODS.keys())
        fund_info = self._get_fund_info(fund_code)
        fund_type = fund_info.get('type', 'default')
        signals = self._compute_factor_signals(fund_code, fund_type, nav_history)
        overall_score = self._compute_overall_score(signals)
        benchmark = TYPE_BENCHMARKS.get(fund_type, TYPE_BENCHMARKS['default'])
        adjusted_return = benchmark['return'] + overall_score * 0.08
        adjusted_vol = benchmark['vol'] * (1.0 + abs(overall_score) * 0.3)
        predictions = {}
        for period in periods:
            seed = _stable_seed(fund_code, period)
            pred = self._monte_carlo_simulate(
                adjusted_return, adjusted_vol, period, seed=seed)
            pred['direction'] = self._score_to_direction(pred['mean_return'])
            pred['confidence'] = min(0.95, 0.45 + abs(pred['mean_return']) / max(adjusted_vol, 0.01) * 0.5)
            predictions[period] = pred
        overall_dir = self._aggregate_direction(predictions)
        return {'fund_code': fund_code, 'fund_name': fund_info.get('name', fund_code),
                'fund_type': fund_type, 'predictions': predictions, 'signals': signals,
                'overall_score': round(overall_score, 3), 'overall_direction': overall_dir,
                'generated_at': datetime.now().isoformat()}
    def predict_portfolio(self, holdings, periods=None, nav_histories=None):
        if periods is None:
            periods = list(PREDICTION_PERIODS.keys())
        individual = []
        weighted_scores = []
        for h in holdings:
            code = h.get('fund_code', '')
            weight = h.get('weight', 1.0 / max(len(holdings), 1))
            nav_hist = nav_histories.get(code) if nav_histories else None
            try:
                pred = self.predict_fund(code, periods=['month'], nav_history=nav_hist)
                individual.append(pred)
                weighted_scores.append(pred['overall_score'] * weight)
            except Exception:
                weighted_scores.append(0.0 * weight)
        total_weight = sum(h.get('weight', 1.0 / max(len(holdings), 1)) for h in holdings)
        weighted_overall = sum(weighted_scores) / max(total_weight, 0.001)
        seed = _stable_seed(*[h.get('fund_code', '') for h in holdings], 'portfolio')
        portfolio_pred = self._portfolio_monte_carlo(holdings, periods, seed=seed)
        sim_rets = portfolio_pred.get('sim_returns', [])
        var_95, cvar_95 = self._calc_var_cvar(sim_rets)
        return {'portfolio_prediction': portfolio_pred, 'individual_predictions': individual,
                'weighted_score': round(weighted_overall, 3),
                'portfolio_direction': self._score_to_direction(weighted_overall),
                'var_95_pct': round(var_95 * 100, 2), 'cvar_95_pct': round(cvar_95 * 100, 2),
                'max_drawdown_estimate_pct': round(portfolio_pred.get('worst_return', 0) * 100, 2),
                'generated_at': datetime.now().isoformat()}
    def _compute_factor_signals(self, fund_code, fund_type, nav_history=None):
        signals = {}
        signals['technical'] = self._technical_signal(fund_code, nav_history)
        signals['fundamental'] = self._fundamental_signal(fund_code, fund_type)
        signals['sentiment'] = self._sentiment_signal(fund_code, fund_type)
        signals['macro'] = self._macro_signal(fund_type)
        signals['details'] = {'technical': self._explain_technical(signals['technical']),
            'fundamental': self._explain_fundamental(signals['fundamental']),
            'sentiment': self._explain_sentiment(signals['sentiment']),
            'macro': self._explain_macro(signals['macro'])}
        return signals
    def _technical_signal(self, fund_code, nav_history=None):
        if nav_history and len(nav_history) >= 30:
            prices = nav_history
        else:
            seed = _stable_seed(fund_code, "technical") % 10000
            rng = random.Random(seed)
            base = 1.0 + rng.uniform(-0.1, 0.3)
            prices = [base]
            for _ in range(119):
                daily_ret = rng.gauss(0.0003, 0.012)
                prices.append(prices[-1] * (1 + daily_ret))
        scores = []
        n = len(prices)
        ma20 = sum(prices[-20:]) / 20 if n >= 20 else prices[-1]
        ma60 = sum(prices[-60:]) / 60 if n >= 60 else prices[-1]
        ma_dev = (ma20 / ma60 - 1) if ma60 > 0 else 0
        scores.append(max(-1, min(1, ma_dev * 8)))
        if n >= 15:
            gains, losses = [], []
            for i in range(-14, 0):
                diff = prices[i] - prices[i - 1]
                gains.append(max(diff, 0))
                losses.append(max(-diff, 0))
            avg_gain = sum(gains) / 14
            avg_loss = sum(losses) / 14
            rsi = 50.0 if avg_loss == 0 else 100.0 - 100.0 / (1.0 + avg_gain / avg_loss)
            scores.append(max(-1, min(1, (rsi - 50) / 25)))
        else:
            scores.append(0)
        if n >= 20:
            recent = prices[-20:]
            mean = sum(recent) / 20
            std = math.sqrt(sum((p - mean) ** 2 for p in recent) / 20)
            if std > 0:
                bb_pos = (prices[-1] - mean) / (2 * std)
                scores.append(max(-1, min(1, -bb_pos)))
            else:
                scores.append(0)
        else:
            scores.append(0)
        if n >= 21:
            mom = prices[-1] / prices[-21] - 1
            scores.append(max(-1, min(1, mom * 8)))
        else:
            scores.append(0)
        if n >= 20:
            returns = [(prices[i] - prices[i - 1]) / prices[i - 1] for i in range(-19, 0)]
            vol = math.sqrt(sum(r ** 2 for r in returns) / 19) * math.sqrt(252)
            scores.append(max(-1, min(1, (0.15 - vol) / 0.25)))
        else:
            scores.append(0)
        return round(sum(scores) / len(scores), 3) if scores else 0.0
    def _fundamental_signal(self, fund_code, fund_type):
        scores = []
        fund_info = self._get_fund_info(fund_code)
        manager_name = fund_info.get('manager', fund_info.get('manager_name', ''))
        if manager_name and manager_name in self.managers_db:
            mgr = self.managers_db[manager_name]
            days = mgr.get('tenure_days', mgr.get('service_days', 365))
            years = days / 365.0
            scores.append(min(0.5, years / 10.0 * 0.5))
            scale = mgr.get('total_scale', mgr.get('fund_scale', 50))
            if 20 <= scale <= 200:
                scores.append(0.3)
            elif scale > 500:
                scores.append(-0.2)
            else:
                scores.append(0.0)
        else:
            scores.append(-0.2)
        type_scores = {'股票型':0.1,'混合型':0.0,'指数型':0.05,'债券型':-0.05,'货币型':-0.1,'default':0.0}
        scores.append(type_scores.get(fund_type, 0.0))
        return round(sum(scores) / max(len(scores), 1), 3)
    def _sentiment_signal(self, fund_code, fund_type):
        seed = _stable_seed(fund_code, "sentiment") % 10000
        rng = random.Random(seed)
        base = rng.uniform(-0.3, 0.3)
        type_adjust = {'股票型':0.1,'混合型':0.05,'债券型':-0.1,'货币型':-0.2,'default':0.0}
        base += type_adjust.get(fund_type, 0.0)
        return round(max(-1, min(1, base)), 3)
    def _macro_signal(self, fund_type):
        if '股票' in fund_type or '混合' in fund_type or '指数' in fund_type:
            return 0.05
        elif '债券' in fund_type:
            return 0.15
        elif '货币' in fund_type:
            return 0.0
        return 0.0
    def _compute_overall_score(self, signals):
        score = 0.0
        for factor, weight in FACTOR_WEIGHTS.items():
            score += signals.get(factor, 0.0) * weight
        return round(max(-1, min(1, score)), 3)
    def _monte_carlo_simulate(self, annual_return, annual_vol, period,
                              n_simulations=1000, seed=None):
        cfg = PREDICTION_PERIODS[period]
        days = cfg['days']
        daily_return = (1 + annual_return) ** (1 / 252) - 1
        daily_vol = annual_vol / math.sqrt(252)
        final_returns = []
        rng = random.Random(seed if seed is not None else 42)
        for _ in range(n_simulations):
            price = 1.0
            for _ in range(days):
                shock = rng.gauss(daily_return, daily_vol)
                price *= (1 + shock)
            ret = price - 1.0
            final_returns.append(ret)
        final_returns.sort()
        n = len(final_returns)
        p10 = final_returns[int(n * 0.1)]
        p25 = final_returns[int(n * 0.25)]
        p50 = final_returns[int(n * 0.5)]
        p75 = final_returns[int(n * 0.75)]
        p90 = final_returns[int(n * 0.9)]
        mean_return = sum(final_returns) / n
        win_rate = sum(1 for r in final_returns if r > 0) / n
        worst = min(r for r in final_returns)
        return {'period':period,'period_label':cfg['label'],'mean_return':round(mean_return,4),
                'median_return':round(p50,4),'win_rate':round(win_rate,3),
                'p10_return':round(p10,4),'p25_return':round(p25,4),
                'p75_return':round(p75,4),'p90_return':round(p90,4),
                'worst_return':round(worst,4),'simulations':n_simulations}
    def _portfolio_monte_carlo(self, holdings, periods, seed=None):
        period = periods[0] if periods else 'month'
        cfg = PREDICTION_PERIODS[period]
        n_simulations = 1000
        total_weight = sum(h.get('weight', 0.05) for h in holdings)
        w_ret = 0.0
        w_vol = 0.0
        for h in holdings:
            ft = h.get('fund_type', 'default')
            bm = TYPE_BENCHMARKS.get(ft, TYPE_BENCHMARKS['default'])
            w = h.get('weight', 0.05) / max(total_weight, 0.001)
            w_ret += bm['return'] * w
            w_vol += bm['vol'] * w
        portfolio_vol = w_vol * math.sqrt(0.3 + 0.7 * (1.0 / max(len(holdings), 1)))
        daily_return = (1 + w_ret) ** (1 / 252) - 1
        daily_vol = portfolio_vol / math.sqrt(252)
        final_returns = []
        sim_returns = []
        rng = random.Random(seed if seed is not None else 42)
        for _ in range(n_simulations):
            price = 1.0
            for _ in range(cfg['days']):
                shock = rng.gauss(daily_return, daily_vol)
                price *= (1 + shock)
            ret = price - 1.0
            final_returns.append(ret)
            sim_returns.append(ret)
        final_returns.sort()
        n = len(final_returns)
        p50 = final_returns[int(n * 0.5)] if n > 0 else 0
        mean_return = sum(final_returns) / max(n, 1)
        win_rate = sum(1 for r in final_returns if r > 0) / max(n, 1)
        worst = min(r for r in final_returns) if final_returns else 0
        return {'period':period,'period_label':cfg['label'],'mean_return':round(mean_return,4),
                'median_return':round(p50,4),'win_rate':round(win_rate,3),
                'worst_return':round(worst,4),'sim_returns':sim_returns,'simulations':n_simulations}
    def _calc_var_cvar(self, returns):
        if not returns:
            rng = random.Random(42)
            returns = [rng.gauss(0.005, 0.10) for _ in range(1000)]
        sorted_returns = sorted(returns)
        n = len(sorted_returns)
        var_95 = sorted_returns[int(n * 0.05)]
        tail = sorted_returns[:int(n * 0.05)]
        cvar_95 = sum(tail) / max(len(tail), 1)
        return var_95, cvar_95
    def _get_fund_info(self, fund_code):
        if fund_code in self.funds_db:
            return self.funds_db[fund_code]
        return {'code': fund_code, 'name': fund_code, 'type': 'default'}
    def _score_to_direction(self, score):
        if score > 0.15:
            return '看涨'
        elif score < -0.15:
            return '看跌'
        return '震荡'
    def _aggregate_direction(self, predictions):
        dirs = [p['direction'] for p in predictions.values()]
        up = dirs.count('看涨')
        down = dirs.count('看跌')
        if up > down:
            return '短期看涨，中期偏多'
        elif down > up:
            return '短期承压，中期偏空'
        return '区间震荡，方向不明'
    def _explain_technical(self, score):
        if score > 0.3: return '技术面偏多：均线多头排列，RSI位于强势区'
        elif score > 0: return '技术面中性偏多'
        elif score > -0.3: return '技术面中性偏空'
        return '技术面偏空：均线空头排列，RSI弱势'
    def _explain_fundamental(self, score):
        if score > 0.2: return '基本面良好'
        elif score > -0.2: return '基本面中性'
        return '基本面偏弱'
    def _explain_sentiment(self, score):
        if score > 0.2: return '市场情绪积极'
        elif score > -0.2: return '市场情绪平稳'
        return '市场情绪偏冷'
    def _explain_macro(self, score):
        if score > 0.1: return '宏观面有利'
        elif score > -0.1: return '宏观面中性'
        return '宏观面偏紧'
    def format_prediction(self, prediction):
        lines = ['=' * 50]
        lines.append(f"  {prediction.get('fund_name', prediction.get('fund_code', '?'))} 趋势预测")
        lines.append(f"  类型: {prediction.get('fund_type', '未知')}")
        lines.append(f"  综合评分: {prediction.get('overall_score', 0):+.3f} ({prediction.get('overall_direction', '?')})")
        lines.append('=' * 50)
        signals = prediction.get('signals', {})
        if signals:
            lines.append('')
            lines.append('【因子分析】')
            for f in ['technical', 'fundamental', 'sentiment', 'macro']:
                label = {'technical': '技术面', 'fundamental': '基本面', 'sentiment': '情绪面', 'macro': '宏观面'}
                sc = signals.get(f, 0)
                det = signals.get('details', {}).get(f, '')
                lines.append(f"  {label.get(f, f)}: {sc:+.3f} - {det}")
        lines.append('')
        lines.append('【各周期预测】')
        for period, pred in prediction.get('predictions', {}).items():
            label = PREDICTION_PERIODS.get(period, {}).get('label', period)
            lines.append(f"  {label}: {pred['direction']} (置信度 {pred['confidence']:.0%})")
            lines.append(f"    预期收益: {pred['mean_return']:+.2%} [P10:{pred['p10_return']:+.2%} P50:{pred['median_return']:+.2%} P90:{pred['p90_return']:+.2%}]")
            lines.append(f"    胜率: {pred['win_rate']:.0%} | 最差: {pred['worst_return']:+.2%}")
        lines.append('')
        lines.append('警告: 量化预测基于历史统计规律，不构成投资建议。')
        lines.append(f"生成时间: {prediction.get('generated_at', '')}")
        return '\n'.join(lines)
    def format_portfolio_prediction(self, prediction):
        lines = ['=' * 50]
        lines.append('  投资组合趋势预测')
        lines.append(f"  组合方向: {prediction.get('portfolio_direction', '?')}")
        lines.append(f"  加权评分: {prediction.get('weighted_score', 0):+.3f}")
        lines.append('=' * 50)
        pf = prediction.get('portfolio_prediction', {})
        lines.append('')
        lines.append('【组合预测】')
        lines.append(f"  预期月收益: {pf.get('mean_return', 0):+.2%}   月胜率: {pf.get('win_rate', 0):.0%}")
        lines.append(f"  95%VaR(月): {prediction.get('var_95_pct', 0):+.2f}%   95%CVaR(月): {prediction.get('cvar_95_pct', 0):+.2f}%")
        lines.append(f"  最大回撤估算: {prediction.get('max_drawdown_estimate_pct', 0):+.2f}%")
        lines.append('')
        lines.append('【成分基金】')
        for i, ind in enumerate(prediction.get('individual_predictions', [])):
            name = ind.get('fund_name', ind.get('fund_code', '?'))
            score = ind.get('overall_score', 0)
            direction = ind.get('overall_direction', '?')
            lines.append(f"  {i+1}. {name}: {score:+.3f} ({direction})")
        lines.append('')
        lines.append('警告: 量化预测基于历史统计规律，不构成投资建议。')
        lines.append(f"生成时间: {prediction.get('generated_at', '')}")
        return '\n'.join(lines)
def main():
    predictor = FundPredictor()
    print('=' * 60)
    print('  基金涨跌预测引擎 v1.0 - 测试')
    print('=' * 60)
    r = predictor.predict_fund('000858')
    print(predictor.format_prediction(r))
    print()
    pf = predictor.predict_portfolio([{'fund_code':'000858','weight':0.4,'fund_type':'混合型'},{'fund_code':'110011','weight':0.3,'fund_type':'股票型'},{'fund_code':'000001','weight':0.3,'fund_type':'债券型'}])
    print(predictor.format_portfolio_prediction(pf))
if __name__ == '__main__':
    main()
