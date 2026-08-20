"""
横向对比与可视化引擎 v2.0
支持基金经理/基金产品多维度对比，导出ASCII图表
"""
import json
import os
import math
from datetime import datetime

# 使用相对于脚本位置的路径，增强跨平台兼容性
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
import sys as _sys; _sys.path.insert(0, os.path.dirname(SCRIPT_DIR))
from fund_advisor_paths import DATA_DIR, load_json_data, load_holdings  # noqa: E402

# 支持 .json.gz 压缩格式加载
try:
    from fund_advisor.data_loader import load_json
except ImportError:
    import gzip
    def load_json(file_path, encoding="utf-8"):
        """回退方案：手动支持 .json.gz"""
        import pathlib
        p = pathlib.Path(file_path)
        gz = p.with_suffix(p.suffix + ".gz") if not p.suffix.endswith(".gz") else p
        if gz.exists():
            with gzip.open(gz, "rt", encoding=encoding) as f:
                return json.load(f)
        with open(p, "r", encoding=encoding) as f:
            return json.load(f)


class ComparisonEngine:
    """横向对比引擎 v2.0"""

    def __init__(self, data_dir=None):
        self.data_dir = data_dir or DATA_DIR
        self.managers_db = {}
        self.companies_db = {}
        self.holdings_db = {}
        self.load_databases()

    def load_databases(self):
        """加载数据库（支持 .json 和 .json.gz 格式；列式压缩经 load_json_data 解码）"""
        # 基金经理档案
        try:
            path = os.path.join(self.data_dir, 'fund_managers_distilled.json')
            data = load_json_data(path)
            items = data.get('managers', data.get('items', []))
            for m in items:
                key = m.get('manager_id', '')
                if key:
                    self.managers_db[key] = m
            if not self.managers_db:
                print("警告: fund_managers_distilled.json 加载为空（键名/格式不匹配？）")
        except FileNotFoundError:
            pass  # 文件不存在时静默跳过
        except Exception as e:
            print(f"加载经理数据失败: {e}")

        # 基金公司档案
        try:
            path = os.path.join(self.data_dir, 'fund_companies_distilled.json')
            data = load_json_data(path)
            # 该文件可能是纯 list 或带 companies/items 键的 dict
            items = data if isinstance(data, list) else data.get('companies', data.get('items', []))
            for c in items:
                key = c.get('company_id', '') or c.get('name', '')
                if key:
                    self.companies_db[key] = c
            if not self.companies_db:
                print("警告: fund_companies_distilled.json 加载为空")
        except FileNotFoundError:
            pass
        except Exception as e:
            print(f"加载公司数据失败: {e}")

        # 持仓数据（统一经 load_holdings 解码各历史格式）
        try:
            for h in load_holdings():
                fc = h.get('fund_code', '')
                if fc:
                    if fc not in self.holdings_db:
                        self.holdings_db[fc] = []
                    self.holdings_db[fc].append(h)
        except Exception as e:
            print(f"加载持仓数据失败: {e}")

    # ==================== 基金经理对比 ====================

    def compare_managers(self, manager_ids_or_names, top_n=5, metrics=None):
        """
        对比多位基金经理

        参数:
            manager_ids_or_names: 经理ID或姓名列表
            top_n: 每组最多显示多少条
            metrics: 要对比的指标

        返回:
            对比结果
        """
        if metrics is None:
            metrics = ['company', 'tenure', 'scale', 'best_return',
                       'current_fund', 'concentration', 'top_holdings']

        # 解析输入（可能是ID也可能是姓名）
        managers = []
        skipped = []
        for identifier in manager_ids_or_names:
            m = self._find_manager(identifier)
            if m:
                managers.append(m)
            else:
                skipped.append(identifier)

        if len(managers) < 2:
            detail = ''
            if skipped:
                skipped_str = ', '.join(skipped)
                detail = f'（未找到: {skipped_str}）'
            return {'error': f'需要至少2位基金经理进行对比{detail}'}

        warnings = []
        if skipped:
            skipped_str = ', '.join(skipped)
            warnings.append(f'未找到以下经理，已跳过: {skipped_str}')

        # 构建对比表格
        result = {
            'type': 'manager_comparison',
            'managers': [],
            'headers': ['指标'] + [m.get('name', '') for m in managers],
            'rows': [],
        }
        if warnings:
            result['warnings'] = warnings

        for metric in metrics:
            row = {'metric': self._get_metric_label(metric), 'values': []}
            for m in managers:
                row['values'].append(self._get_manager_metric(m, metric))
            result['rows'].append(row)

        # 计算相似度
        if len(managers) == 2:
            result['similarity'] = self._calculate_similarity(managers[0], managers[1])

        return result

    def _find_manager(self, identifier):
        """查找经理（按ID或姓名）"""
        # 先按ID查
        if identifier in self.managers_db:
            return self.managers_db[identifier]

        # 按姓名查
        for m in self.managers_db.values():
            name = m.get('name', '')
            if name == identifier or identifier in name:
                return m
        return None

    def _get_metric_label(self, metric):
        labels = {
            'company': '所属公司',
            'tenure': '从业年限',
            'scale': '管理规模',
            'best_return': '任职最佳回报',
            'current_fund': '现任基金',
            'concentration': '前十重仓集中度',
            'top_holdings': '前三大重仓股',
            'style': '投资风格',
            'stage': '产品阶段',
            'sectors': '重点行业',
            'advice': '投资建议',
            'suitable': '适合投资者',
            'warning': '风险提示'
        }
        return labels.get(metric, metric)

    def _manager_holdings(self, manager):
        """取该经理现任基金的十大重仓（股票级明细行）"""
        code = str(manager.get('current_fund_code', '')).zfill(6)
        if not code.strip('0'):
            return []
        rows = self.holdings_db.get(code) or self.holdings_db.get(code.lstrip('0')) or []
        return rows

    def _get_manager_metric(self, manager, metric):
        if metric == 'company':
            return manager.get('company_name', '-')
        elif metric == 'best_return':
            br = manager.get('best_return')
            return f'{br}%' if br not in (None, '') else '-'
        elif metric == 'current_fund':
            return manager.get('current_fund_name', '-')
        elif metric == 'concentration':
            rows = self._manager_holdings(manager)
            if not rows:
                return '-'
            total = sum(float(r.get('weight') or 0) for r in rows[:10])
            return f'{total:.1f}%'
        elif metric == 'top_holdings':
            rows = self._manager_holdings(manager)
            if not rows:
                return '-'
            names = [r.get('stock_name') or r.get('stock_code', '') for r in rows[:3]]
            return '、'.join(names)
        elif metric == 'style':
            return manager.get('investment_style', '均衡型')
        elif metric == 'tenure':
            years = manager.get('tenure_years')
            if years is None:
                try:
                    years = float(manager.get('tenure_days') or 0) / 365
                except (TypeError, ValueError):
                    years = 0
            return f'{years:.1f}年'
        elif metric == 'scale':
            scale = manager.get('total_scale', 0)
            if scale > 10000:
                return f'{scale/10000:.1f}万亿'
            elif scale > 0:
                return f'{scale:.0f}亿'
            return '-'
        elif metric == 'stage':
            return manager.get('fund_stage', '-')
        elif metric == 'sectors':
            sectors = manager.get('sectors', [])
            return '、'.join(sectors) if sectors else manager.get('sector_description', '-')
        elif metric == 'advice':
            return manager.get('investment_advice', '-')[:30] + '...'
        elif metric == 'suitable':
            return manager.get('suitable_investors', '-')
        elif metric == 'warning':
            return manager.get('risk_warning', '-')[:20] + '...'
        elif metric == 'stock_count':
            stocks = manager.get('stock_pool', [])
            return f'{len(stocks)}只'
        elif metric == 'infra':
            infra = manager.get('infrastructure_investment', False)
            return '有' if infra else '无'
        return '-'

    def _calc_tenure_years(self, m):
        try:
            if m.get('tenure_years') is not None:
                return float(m['tenure_years'])
            return float(m.get('tenure_days') or 0) / 365
        except (TypeError, ValueError):
            return 0.0

    def _calculate_similarity(self, m1, m2):
        """计算两位经理的相似度（基于真实档案与持仓数据）"""
        score = 0
        details = []

        # 1. 持仓重叠 (40%)
        s1 = {str(r.get('stock_code', '')) for r in self._manager_holdings(m1)[:10]}
        s2 = {str(r.get('stock_code', '')) for r in self._manager_holdings(m2)[:10]}
        s1.discard('')
        s2.discard('')
        if s1 and s2:
            overlap = len(s1 & s2) / len(s1 | s2)
            score += overlap * 40
            if s1 & s2:
                details.append(f'重仓股重叠 {len(s1 & s2)} 只')
        else:
            score += 10

        # 2. 从业年限 (20%)
        y1, y2 = self._calc_tenure_years(m1), self._calc_tenure_years(m2)
        if abs(y1 - y2) < 3:
            score += 20
            details.append(f'从业年限接近({y1:.1f}年 vs {y2:.1f}年)')
        elif abs(y1 - y2) < 5:
            score += 10

        # 3. 管理规模接近度 (20%)
        sc1 = float(m1.get('total_scale') or 0)
        sc2 = float(m2.get('total_scale') or 0)
        if sc1 > 0 and sc2 > 0:
            ratio = min(sc1, sc2) / max(sc1, sc2)
            score += ratio * 20
            if ratio > 0.5:
                details.append('管理规模量级接近')

        # 4. 同一公司 (20%)
        if m1.get('company_name') and m1.get('company_name') == m2.get('company_name'):
            score += 20
            details.append(f'同属{m1["company_name"]}')

        return {
            'score': round(score, 1),
            'level': '高' if score > 70 else '中' if score > 40 else '低',
            'details': details
        }

    # ==================== 基金公司对比 ====================

    def compare_companies(self, company_ids_or_names, metrics=None):
        """对比多家基金公司"""
        if metrics is None:
            metrics = ['type', 'scale', 'manager_count', 'style', 'rating']

        # 解析输入
        companies = []
        for identifier in company_ids_or_names:
            c = self._find_company(identifier)
            if c:
                companies.append(c)

        if len(companies) < 2:
            return {'error': '需要至少2家基金公司进行对比'}

        result = {
            'type': 'company_comparison',
            'companies': [],
            'headers': ['指标'] + [c.get('name', '') for c in companies],
            'rows': []
        }

        for metric in metrics:
            row = {'metric': self._get_company_metric_label(metric), 'values': []}
            for c in companies:
                row['values'].append(self._get_company_metric(c, metric))
            result['rows'].append(row)

        return result

    def _find_company(self, identifier):
        """查找公司（按ID或名称）"""
        if identifier in self.companies_db:
            return self.companies_db[identifier]
        for c in self.companies_db.values():
            name = c.get('name', '')
            short = c.get('short_name', '')
            if identifier in name or name in identifier or identifier == short:
                return c
        return None

    def _get_company_metric_label(self, metric):
        labels = {
            'type': '公司类型',
            'scale': '管理规模',
            'manager_count': '基金经理数',
            'style': '主导风格',
            'rating': '平均评级',
            'sectors': '重点行业'
        }
        return labels.get(metric, metric)

    def _get_company_metric(self, company, metric):
        if metric == 'type':
            return company.get('type', '公募')
        elif metric == 'scale':
            scale = company.get('total_scale', 0)
            if scale > 10000:
                return f'{scale/10000:.1f}万亿'
            elif scale > 0:
                return f'{scale:.0f}亿'
            return '-'
        elif metric == 'manager_count':
            return f"{company.get('manager_count', 0)}人"
        elif metric == 'style':
            return company.get('dominant_style', '-')
        elif metric == 'rating':
            rating = company.get('rating_info', {})
            if rating.get('has_data'):
                return f"{rating.get('avg_star', 0):.1f}星"
            return '-'
        elif metric == 'sectors':
            sectors = company.get('sector_focus', [])
            return '、'.join(sectors) if sectors else '-'
        return '-'

    # ==================== 排名 ====================

    def rank_managers(self, criteria='tenure', top_n=10, filters=None):
        """
        基金经理排名

        criteria: tenure(从业年限) / scale(规模) / style(风格)
        """
        managers = list(self.managers_db.values())

        # 过滤
        if filters:
            if 'style' in filters:
                managers = [m for m in managers if m.get('investment_style') == filters['style']]
            if 'company' in filters:
                managers = [m for m in managers if filters['company'] in m.get('company_name', '')]

        # 排序
        if criteria == 'tenure':
            managers.sort(key=lambda x: x.get('tenure_years', 0), reverse=True)
        elif criteria == 'scale':
            managers.sort(key=lambda x: x.get('total_scale', 0), reverse=True)

        return [{
            'manager_id': m.get('manager_id'),
            'name': m.get('name'),
            'company': m.get('company_name'),
            'fund': m.get('current_fund_name'),
            'style': m.get('investment_style'),
            'tenure_years': m.get('tenure_years', 0),
            'scale': m.get('total_scale', 0),
            'sectors': m.get('sectors', [])
        } for m in managers[:top_n]]

    def rank_companies(self, criteria='scale', top_n=10):
        """基金公司排名"""
        companies = list(self.companies_db.values())

        if criteria == 'scale':
            companies.sort(key=lambda x: x.get('total_scale', 0), reverse=True)

        return [{
            'company_id': c.get('company_id'),
            'name': c.get('name'),
            'short_name': c.get('short_name'),
            'type': c.get('type'),
            'total_scale': c.get('total_scale', 0),
            'manager_count': c.get('manager_count', 0),
            'dominant_style': c.get('dominant_style'),
        } for c in companies[:top_n]]

    # ==================== 可视化导出 ====================

    def generate_ascii_chart(self, data_type, data_ids, chart_type='table'):
        """
        生成ASCII可视化图表

        参数:
            data_type: 'manager' / 'company'
            data_ids: 数据ID列表
            chart_type: 'table' / 'bar' / 'radar'
        """
        if data_type == 'manager':
            comparison = self.compare_managers(data_ids)
        else:
            comparison = self.compare_companies(data_ids)

        if 'error' in comparison:
            return comparison['error']

        lines = []
        lines.append('\n' + '=' * 70)
        lines.append(f"  {data_type == 'manager' and '基金经理对比' or '基金公司对比'}")
        lines.append('=' * 70 + '\n')

        # 表头
        headers = comparison['headers']
        col_widths = [max(len(str(h)) for h in headers)]
        for row in comparison['rows']:
            for i, v in enumerate(row['values']):
                col_widths[i + 1] = max(col_widths[i + 1] if i + 1 < len(col_widths) else 0,
                                         len(str(v)), 6)

        # 打印表头
        header_line = '| ' + ' | '.join(str(h).ljust(col_widths[i]) for i, h in enumerate(headers)) + ' |'
        lines.append(header_line)
        lines.append('|' + '|'.join(['-' * (w + 2) for w in col_widths]) + '|')

        # 打印数据行
        for row in comparison['rows']:
            line = '| ' + f"{row['metric']}".ljust(col_widths[0])
            for i, v in enumerate(row['values']):
                line += ' | ' + str(v).ljust(col_widths[i + 1])
            line += ' |'
            lines.append(line)

        # 相似度
        if 'similarity' in comparison:
            sim = comparison['similarity']
            lines.append('')
            lines.append(f"相似度: {sim['score']}分 ({sim['level']})")
            for d in sim['details']:
                lines.append(f"  - {d}")

        lines.append('\n' + '=' * 70)

        return '\n'.join(lines)

    def generate_style_distribution_chart(self, managers=None):
        """
        生成投资风格分布ASCII图

        返回类似:
        成长型  ████████████  45%
        价值型  ██████          25%
        均衡型  ██████████████  30%
        """
        if managers is None:
            managers = list(self.managers_db.values())

        styles = {}
        for m in managers:
            style = m.get('investment_style', '均衡型')
            styles[style] = styles.get(style, 0) + 1

        total = len(managers)
        if total == 0:
            return '无数据'

        lines = ['\n投资风格分布:']
        lines.append('-' * 40)

        for style in ['成长型', '价值型', '均衡型']:
            count = styles.get(style, 0)
            pct = count / total * 100
            bar_len = int(pct / 2)
            bar = '█' * bar_len
            lines.append(f'{style.ljust(6)} {bar.ljust(50)} {pct:5.1f}% ({count}人)')

        lines.append('-' * 40)
        lines.append(f'共{total}位基金经理')

        return '\n'.join(lines)

    def generate_company_scale_chart(self, top_n=10):
        """生成基金公司规模排行ASCII图"""
        companies = self.rank_companies('scale', top_n)

        if not companies:
            return '无数据'

        max_scale = max(c.get('total_scale', 1) for c in companies)

        lines = ['\n基金公司规模排行 (Top %d):' % top_n]
        lines.append('-' * 50)

        for i, c in enumerate(companies, 1):
            scale = c.get('total_scale', 0)
            bar_len = int(scale / max_scale * 40)
            bar = '█' * bar_len
            name = c.get('short_name', c.get('name', ''))[:8]
            if scale > 10000:
                scale_str = f'{scale/10000:.1f}万亿'
            else:
                scale_str = f'{scale:.0f}亿'
            lines.append(f'{i:2d}. {name.ljust(8)} {bar.ljust(40)} {scale_str}')

        lines.append('-' * 50)

        return '\n'.join(lines)

    def generate_manager_ranking_table(self, criteria='tenure', top_n=10, style_filter=None):
        """生成经理排名表格"""
        filters = {'style': style_filter} if style_filter else None
        managers = self.rank_managers(criteria, top_n, filters)

        if not managers:
            return '无数据'

        lines = ['\n基金经理排名 (Top %d):' % top_n]
        if style_filter:
            lines.append(f'风格: {style_filter}')
        lines.append('-' * 70)
        lines.append(f"{'排名':^4} {'姓名':^8} {'公司':^10} {'基金':^12} {'风格':^6} {'年限':^6}")
        lines.append('-' * 70)

        for i, m in enumerate(managers, 1):
            name = m.get('name', '')[:8]
            company = m.get('company', '')[:10]
            fund = m.get('fund', '')[:12]
            style = m.get('style', '-')[:6]
            tenure = f"{m.get('tenure_years', 0):.1f}年"
            lines.append(f'{i:^4} {name:^8} {company:^10} {fund:^12} {style:^6} {tenure:^6}')

        lines.append('-' * 70)

        return '\n'.join(lines)

    # ==================== 替代基金查找 ====================

    def find_alternatives(self, manager_id_or_name, top_n=5):
        """查找同类替代基金"""
        target = self._find_manager(manager_id_or_name)
        if not target:
            return {'error': '未找到该基金经理'}

        target_style = target.get('investment_style', '')
        target_sectors = set(target.get('sectors', []))
        target_id = target.get('manager_id', '')

        candidates = []
        for mid, m in self.managers_db.items():
            if mid == target_id:
                continue

            # 风格相同
            if m.get('investment_style', '') != target_style:
                continue

            # 计算相似度
            score = 50  # 基础分：风格相同
            m_sectors = set(m.get('sectors', []))
            if target_sectors and m_sectors:
                overlap = len(target_sectors & m_sectors) / len(target_sectors | m_sectors)
                score += overlap * 50

            candidates.append({
                'manager_id': mid,
                'name': m.get('name'),
                'company': m.get('company_name'),
                'fund': m.get('current_fund_name'),
                'style': m.get('investment_style'),
                'similarity_score': round(score, 1)
            })

        candidates.sort(key=lambda x: x['similarity_score'], reverse=True)
        return candidates[:top_n]


def main():
    """测试"""
    engine = ComparisonEngine()

    print('=' * 60)
    print('横向对比引擎 v2.0')
    print('=' * 60)
    print(f'加载了 {len(engine.managers_db)} 位基金经理')
    print(f'加载了 {len(engine.companies_db)} 家基金公司')

    # 测试对比
    print(engine.generate_ascii_chart('manager', ['1', '2']))

    # 测试风格分布
    print(engine.generate_style_distribution_chart())

    # 测试经理排名
    print(engine.generate_manager_ranking_table('tenure', 10))


if __name__ == '__main__':
    main()