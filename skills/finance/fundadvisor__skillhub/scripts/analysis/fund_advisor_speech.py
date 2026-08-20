"""
基金经理话术引擎 v5.5
纯本地运行，使用本地数据 + 扩展词库 + 模板生成
有人的感觉，避免AI味。零依赖，无需外部API。
"""
import json
import random
import re
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
import sys as _sys; _sys.path.insert(0, str(SCRIPT_DIR.parent))
from fund_advisor_paths import DATA_DIR  # noqa: E402


class FundAdvisorSpeech:
    # 语气词开头（口语化，自然）
    HEDGES = [
        "说实话", "客观讲", "我认为", "我的看法", "大概", "可能",
        "依我看", "我个人感觉", "不瞒你说", "跟你讲", "我这人直",
        "我就直说了", "你问我", "嗯这事儿", "你像问", "没跟你绕弯子"
    ]

    # 开场白（自信亲切）
    OPENERS = [
        "我直接说重点。", "这个我得好好说说。", "这个问题我很熟悉。",
        "我分几个方面来解答。", "这个我来说两句。", "哎这个问题",
        "你算问对人了。", "这个我有发言权。", "我跟你好好聊聊。",
        "这事儿我不陌生。", "说到这个。", "先说结论吧。",
        "你算问对人了，我跟你说。", "这个问题我有想法。"
    ]

    # 共情词（亏损安抚）
    EMPATHY = [
        "这种心情我理解。", "我知道你着急。", "没关系的，慢慢来。",
        "其实不用太担心。", "这种情况很常见。", "亏钱了谁都难受。",
        "我理解你的感受。", "这种波动确实让人不安。", "没人的钱是大风刮来的。",
        "你的心情我懂。", "我知道这不好受。", "哎，谁亏钱都会焦虑。"
    ]

    # 兴奋词（盈利时）
    EXCITEMENT = [
        "这个方向我很看好！", "这正是我重点配置的！",
        "这个机会我也在关注！", "这个赛道非常有潜力！",
        "这个我可太有信心了。", "跟你说这个我很兴奋。",
        "这个必须重点讲。", "这正是我的强项。", "这个必须说两句！"
    ]

    # 口语填充词（让话更像人）
    FILLERS = [
        "嗯", "这个", "那个", "就是说", "然后呢",
        "反正我是这么想的", "大概就这意思", "你懂的",
        "这么跟你说吧", "说白了", "说实在的"
    ]

    # 互动引导词
    INTERACTIVE = [
        "你问我怎么看？", "你想深入了解哪块？", "有没有听明白？",
        "我说明白了吗？", "你要不要我再展开讲讲？",
        "你有什么想法？", "你觉得呢？", "咱可以再聊聊细节。",
        "还有什么想问的？"
    ]

    # 亏损安抚中间句
    LOSS_MID = {
        20: "这种级别的下跌确实很煎熬。但说实话，危机时刻往往反而蕴含机会。",
        10: "10%以上的下跌确实让人难受。但波动是市场的常态，关键看怎么应对。",
        5: "近期的调整确实超出预期。我建议你不要在最低点卖出，那样反而锁定亏损。",
        0: "短期波动在所难免。这种时候最忌讳的就是割肉离场。"
    }

    # 盈利话术中间句
    GAIN_MID = {
        30: "30%以上的收益非常可观！但如果你是长期持有，建议不要轻易止盈。",
        15: "这个收益相当不错。我建议你保持仓位，不要被短期波动洗出去。",
        0: "恭喜取得正收益！继续保持，市场的奖励通常会眷顾有耐心的人。"
    }

    def __init__(self, data_dir=None):
        self.data_dir = Path(data_dir) if data_dir else DATA_DIR
        self._load_data()

    def _load_data(self):
        """加载本地数据（透明支持列式压缩）"""
        self.managers_db = {}
        self.views_db = {}

        # 使用统一的数据加载器处理列式压缩格式
        try:
            from fund_advisor_paths import load_json_data
            data = load_json_data('fund_managers_distilled.json')
            for m in data.get('managers', data.get('items', [])):
                key = m.get('name', '')
                if key:
                    self.managers_db[key] = m
        except Exception:
            pass

        # 加载经理观点
        try:
            path = self.data_dir / 'manager_views.json'
            if path.exists():
                with open(str(path), 'r', encoding='utf-8') as f:
                    data = json.load(f)
                for v in data.get('views', data.get('items', [])):
                    fc = v.get('fc', v.get('fund_code', ''))
                    if fc:
                        if fc not in self.views_db:
                            self.views_db[fc] = []
                        self.views_db[fc].append(v)
        except Exception:
            pass

    def find_manager(self, name=None, fund_code=None, company=None, top_n=5):
        """查找经理"""
        if not name and not fund_code:
            return []

        results = []
        seen = set()

        for key, m in self.managers_db.items():
            n = m.get('name', '')
            if name:
                kw = name.strip()
                if not (kw in n or n in kw or kw.replace(' ', '') in n.replace(' ', '')):
                    continue

            key_str = (n, m.get('company_name', ''), m.get('current_fund_code', ''))
            if key_str in seen:
                continue
            seen.add(key_str)
            results.append(m)

        if fund_code:
            results = [r for r in results if str(r.get('current_fund_code', '')) == str(fund_code)]
        if company:
            results = [r for r in results if company in r.get('company_name', '')]

        return results[:top_n]

    def _r(self, lst):
        """随机选一个"""
        return random.choice(lst) if lst else ''

    def _first_sentence(self, text):
        """提取第一句完整的话"""
        if not text:
            return ''
        m = re.search(r'[^。！？.]{5,}[。！？.。]', str(text).strip())
        if m:
            s = m.group()
            s = re.sub(r'^[，、\s]+', '', s)
            return s
        return str(text).strip()[:50] if len(str(text).strip()) >= 5 else str(text).strip()

    def _detect_style_from_name(self, name):
        """从基金名判断风格"""
        if any(kw in name for kw in ['成长', '积极', '激进', '科技', '创新', '新兴']):
            return '成长型'
        if any(kw in name for kw in ['价值', '稳健', '红利', '低波', '平衡']):
            return '价值型'
        return '均衡型'

    def ask(self, question, manager_name=None, fund_code=None, online=False,
            client_risk='稳健型', loss_pct=None, gain_pct=None):
        """主入口"""
        managers = self.find_manager(name=manager_name, fund_code=fund_code, top_n=1)
        if not managers:
            return self._not_found(manager_name or fund_code or '?')

        mgr = managers[0]
        q = question or ''

        # 亏损场景
        if any(kw in q for kw in ['亏', '跌', '回撤', '缩水', '绿', '浮亏']):
            return self._answer_loss(mgr, loss_pct or self._extract_pct(q), client_risk, online)
        # 盈利场景
        if any(kw in q for kw in ['涨', '赚', '飘红', '盈利', '收益', '浮盈']):
            return self._answer_gain(mgr, gain_pct or self._extract_pct(q), client_risk, online)
        # 净值查询
        if any(kw in q for kw in ['净值', '估值', '行情', '表现']):
            return self._answer_nav(mgr, online)
        # 持仓查询
        if any(kw in q for kw in ['重仓', '持仓', '买了什么', '仓位', '股票']):
            return self._answer_holdings(mgr, online)
        # 风险匹配/推荐
        if any(kw in q for kw in ['推荐', '配置', '怎么买', '适合', '风险']):
            return self._answer_recommend(mgr, client_risk, online)
        # 投资观点
        if any(kw in q for kw in ['观点', '展望', '想法', '判断', '怎么看', '大盘', '市场']):
            return self._answer_views(mgr, online)
        # 自我介绍/默认
        return self._answer_profile(mgr, online)

    def _not_found(self, identifier):
        return (f'数据库里没找到「{identifier}」这位基金经理。'
                f'可能名字有出入，或者不在我们的覆盖范围内。'
                f'你可以提供更多信息，比如他所在的基金公司，这样我能更准确地找到他。')

    def _extract_pct(self, text):
        """从文本提取百分比"""
        m = re.search(r'(-?\d+(?:\.\d+)?)\s*%', str(text))
        return float(m.group(1)) if m else None

    def _answer_profile(self, mgr, online=False):
        """自我介绍"""
        name = mgr.get('name', '')
        company = mgr.get('company_name', '')
        fund_name = mgr.get('current_fund_name', '')
        fund_code = mgr.get('current_fund_code', '')
        style = mgr.get('investment_style', self._detect_style_from_name(fund_name))
        tenure = mgr.get('tenure_years', 0)
        sector = mgr.get('sector_description', '')
        stage = mgr.get('fund_stage', '')

        parts = []

        # 自然开场
        if random.random() < 0.3:
            parts.append(self._r(self.OPENERS))

        # 基本信息
        parts.append(f'我是{name}，在{company}工作。')
        if tenure > 0:
            parts.append(f'在这个市场里干了{round(tenure)}年了。')

        # 风格
        style_desc = {
            '成长型': '我偏成长风格，喜欢挖掘科技、新能源这些赛道的机 会。波动大一些，但我觉得长期回报会更好。',
            '价值型': '我比较注重估值和安全边际，追求稳稳的幸福。不求最快，但求最稳。',
            '均衡型': '我风格比较均衡，不赌单一方向。涨的时候跟上，跌的时候控制回撤。'
        }
        parts.append(style_desc.get(style, ''))

        # 行业
        if sector:
            parts.append(sector.replace('重点布局', '我重点看').replace('行业', '这块的机会。'))

        # 随机加互动
        if random.random() < 0.4:
            parts.append(self._r(self.INTERACTIVE))

        return ''.join(parts)

    def _answer_loss(self, mgr, loss_pct, client_risk, online=False):
        """亏损安抚"""
        name = mgr.get('name', '')
        company = mgr.get('company_name', '')
        fund_name = mgr.get('current_fund_name', '')
        style = mgr.get('investment_style', self._detect_style_from_name(fund_name))
        sector = mgr.get('sector_description', '')

        parts = []

        # 共情开头
        if random.random() < 0.7:
            parts.append(self._r(self.EMPATHY))

        # 亏损程度判断
        if loss_pct is not None:
            for threshold in sorted(self.LOSS_MID.keys(), reverse=True):
                if loss_pct >= threshold:
                    parts.append(self.LOSS_MID[threshold])
                    break
        else:
            parts.append(self.LOSS_MID[0])

        # 结合经理风格
        if style == '成长型':
            parts.append(f'{name}的风格偏成长，近期压力不小。但拉长时间看，成长赛道的中长期逻辑没变。')
        elif style == '价值型':
            parts.append(f'{name}的风格偏稳健，回撤控制能力较强。这种时候反而是优化结构的机会。')
        else:
            parts.append(f'{name}的风格比较均衡，应对市场波动有自己的办法。')

        # 结合行业
        if sector and random.random() < 0.5:
            parts.append(f'他重仓的{sector.replace("重点布局", "").replace("行业", "")}近期确实受影响，但基本面没变。')

        # 建议
        parts.append('我建议你不要在低位割肉，保持定投，平滑成本。')
        if random.random() < 0.3:
            parts.append('有什么问题可以随时问我。')

        return ''.join(parts)

    def _answer_gain(self, mgr, gain_pct, client_risk, online=False):
        """盈利话术"""
        name = mgr.get('name', '')
        fund_name = mgr.get('current_fund_name', '')
        style = mgr.get('investment_style', self._detect_style_from_name(fund_name))

        parts = []

        # 恭喜开头
        if random.random() < 0.6:
            parts.append(self._r(self.EXCITEMENT))
        else:
            parts.append('恭喜你！')

        # 盈利程度
        if gain_pct is not None:
            for threshold in sorted(self.GAIN_MID.keys(), reverse=True):
                if gain_pct >= threshold:
                    parts.append(self.GAIN_MID[threshold])
                    break
        else:
            parts.append(self.GAIN_MID[0])

        # 风格相关
        if style == '成长型':
            parts.append('成长风格近期表现不错，但波动也大。建议保持仓位的同时，也要注意控制风险。')
        elif style == '价值型':
            parts.append('价值风格走的是稳健路线，继续持有问题不大。')
        else:
            parts.append('均衡配置的效果正在显现，继续保持就好。')

        # 风险提示
        if random.random() < 0.4:
            parts.append('不过市场随时可能有变化，别太贪，见好就收一部分也是可以的。')

        # 互动
        if random.random() < 0.3:
            parts.append(self._r(self.INTERACTIVE))

        return ''.join(parts)

    def _answer_nav(self, mgr, online=False):
        """净值查询"""
        fund_name = mgr.get('current_fund_name', '')
        fund_code = mgr.get('current_fund_code', '')

        parts = []
        if random.random() < 0.5:
            parts.append(self._r(self.HEDGES) + '，')

        parts.append('我现在手头没有实时净值数据。')
        parts.append(f'你想看{fund_name}（{fund_code}）的估算净值的话，')
        parts.append('可以直接去天天基金网、支付宝或者微信理财通搜一下，实时估值都有。')
        parts.append('估值这东西会有点偏差，但参考价值还是有的。')

        return ''.join(parts)

    def _answer_holdings(self, mgr, online=False):
        """持仓查询"""
        name = mgr.get('name', '')
        fund_name = mgr.get('current_fund_name', '')
        stock_pool = mgr.get('stock_pool', [])
        sector = mgr.get('sector_description', '')

        parts = []

        if random.random() < 0.5:
            parts.append(self._r(self.OPENERS) + ' ')
        parts.append(f'问{name}的持仓？我直接说重点：\n\n')
        parts.append(f'{fund_name}主要配置了')

        if stock_pool and len(stock_pool) > 0:
            if len(stock_pool) <= 5:
                parts.append('、'.join(stock_pool))
            else:
                parts.append('、'.join(stock_pool[:5]))
                parts.append(f'等{len(stock_pool)}只股票')
            parts.append('为核心标的。')
        else:
            parts.append('这些股票，可以在季报里看到详细持仓。')

        if sector:
            parts.append(f'\n行业上{sector}。')

        # 自然引导互动
        if random.random() < 0.4:
            parts.append(f'\n\n你想了解哪只股票的具体情况？')

        return ''.join(parts)

    def _answer_views(self, mgr, online=False):
        """投资观点"""
        name = mgr.get('name', '')
        fund_code = mgr.get('current_fund_code', '')
        sector = mgr.get('sector_description', '')
        style = mgr.get('investment_style', '')
        views = self.views_db.get(fund_code, [])

        parts = []

        # 开场
        if random.random() < 0.5:
            parts.append(self._r(self.HEDGES) + '，')
        parts.append('说说我的观点：\n\n')

        # 如果有真实观点，优先用
        if views:
            for v in views:
                view_text = v.get('v', '')
                if view_text and len(view_text) > 10:
                    parts.append('「' + self._first_sentence(view_text) + '」')
                    if random.random() < 0.4:
                        parts.append('\n\n' + self._r(self.INTERACTIVE))
                    return ''.join(parts)

        # 没有真实观点，用风格+行业生成
        if sector:
            sector_clean = sector.replace('重点布局', '').replace('行业', '')
            views_templates = {
                '科技': f'科技这块，我还是比较有信心的。半导体国产替代的逻辑没变，AI应用端的空间还很大。我会继续精选个股，不追热点。',
                '新能源': f'新能源渗透率还在提升，储能、光伏降本趋势没变。竞争格局在分化，我更看好具备成本优势的龙头企业。',
                '消费': f'消费复苏节奏比大家预期的慢，但我认为估值已经反映了很多悲观预期。品牌力和渠道力强的公司值得关注。',
                '医药': f'医药板块调整时间不短了，部分个股估值有吸引力。创新药和器械国产替代是长期逻辑。',
                '金融': f'金融板块压舱石作用还在，估值低、分红高。弹性一般，但安全性好。',
                '制造': f'制造业升级是大趋势，高端制造、军工差异化我看好的。'
            }
            for key, tmpl in views_templates.items():
                if key in sector:
                    parts.append(tmpl)
                    if random.random() < 0.4:
                        parts.append('\n\n' + self._r(self.INTERACTIVE))
                    return ''.join(parts)

        # 默认
        parts.append('我对市场保持关注，精选个股、均衡配置是我的策略。')
        parts.append('\n\n' + self._r(self.INTERACTIVE))

        return ''.join(parts)

    def _answer_recommend(self, mgr, client_risk, online=False):
        """风险匹配/推荐"""
        name = mgr.get('name', '')
        fund_name = mgr.get('current_fund_name', '')
        style = mgr.get('investment_style', self._detect_style_from_name(fund_name))
        stage = mgr.get('fund_stage', '')
        suitable = mgr.get('suitable_investors', '')
        period = mgr.get('investment_period', '')
        warning = mgr.get('risk_warning', '')

        parts = []

        parts.append('说到适不适合，我来说说：\n\n')

        if suitable:
            parts.append(suitable + '\n\n')
        if style:
            style_match = {
                '成长型': '这只基金属于成长风格，波动会大一些，但收益弹性也大。',
                '价值型': '这只基金属于价值风格，走势稳健，回撤控制好。',
                '均衡型': '这只基金属于均衡风格，不走极端，适合作为核心配置。'
            }
            parts.append(style_match.get(style, ''))
            parts.append('\n')

        if stage:
            stage_desc = {
                '萌芽期': '产品比较新，需要时间验证。',
                '成长期': '风格正在形成，业绩弹性较大。',
                '成熟期': '业绩比较稳定，风格清晰。',
                '老牌期': '历经牛熊考验，长期业绩可参考性高。'
            }
            parts.append(stage_desc.get(stage, ''))
            parts.append('\n')

        if period:
            parts.append(f'建议投资周期：{period}。')

        if warning and random.random() < 0.5:
            parts.append(f'\n\n提醒一下：{warning}')

        if random.random() < 0.4:
            parts.append('\n\n' + self._r(self.INTERACTIVE))

        return ''.join(parts)


def main():
    """测试"""
    gen = FundAdvisorSpeech()

    # 测试查询
    print('=== 测试话术生成 ===\n')

    mgr = gen.find_manager(name='艾邦妮')
    if mgr:
        print(f'找到经理: {mgr[0].get("name")}\n')

        print('【自我介绍】')
        print(gen.ask('你是谁', manager_name='艾邦妮'))
        print()

        print('【亏损安抚】')
        print(gen.ask('亏了15%怎么办', manager_name='艾邦妮'))
        print()

        print('【持仓查询】')
        print(gen.ask('你的持仓是什么', manager_name='艾邦妮'))
        print()

        print('【投资观点】')
        print(gen.ask('你怎么看市场', manager_name='艾邦妮'))
    else:
        print('未找到艾邦妮')


if __name__ == '__main__':
    main()