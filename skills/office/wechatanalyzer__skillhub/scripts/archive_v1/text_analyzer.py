#!/usr/bin/env python3
"""
文本分析器 - MBTI推断 + 大五人格 + 情感分析 + 行为模式分析
"""

import re
import json
from datetime import datetime
from collections import Counter
from typing import Dict, List, Tuple, Any

try:
    from .conversation_predictor import ConversationPredictor
    HAS_CONVERSATION_PREDICTOR = True
except ImportError:
    HAS_CONVERSATION_PREDICTOR = False


class TextAnalyzer:
    """微信聊天文本分析器"""

    # MBTI 特征词汇库 — 所有词条长度 >= 2 字符，避免单字符误判
    MBTI_KEYWORDS = {
        'E': {'energy': ['我们', '大家', '一起', '聚会', '朋友', '社交', '热闹', '聊天', '有趣', '参加']},
        'I': {'energy': ['自己', '独处', '安静', '思考', '看书', '一个人', '独自', '内向']},
        'S': {'sensing': ['具体', '实际', '事实', '数据', '真的', '确定', '发生', '做过', '经验']},
        'N': {'sensing': ['可能', '也许', '感觉', '想象', '未来', '如果', '大概', '觉得', '似乎']},
        'T': {'thinking': ['逻辑', '道理', '应该', '分析', '理性', '原因', '对错', '公平', '原则']},
        'F': {'thinking': ['感觉', '觉得', '情感', '在乎', '关心', '重要', '理解', '感受', '心意']},
        'J': {'judging': ['计划', '决定', '安排', '应该', '必须', '完成', '准时', '组织', '结构']},
        'P': {'judging': ['随性', '看情况', '再说', '到时候', '灵活', '慢慢来']}
    }

    # 大五人格特征词汇 — 所有词条长度 >= 2 字符
    BIGFIVE_KEYWORDS = {
        'openness': {
            'high': ['思考', '想象', '创意', '新颖', '好奇', '艺术', '哲学', '抽象', '有趣', '探索'],
            'low': ['实际', '传统', '习惯', '常规', '稳定', '保守', '按部就班']
        },
        'conscientiousness': {
            'high': ['计划', '安排', '准时', '完成', '认真', '负责', '组织', '效率', '目标'],
            'low': ['随意', '拖延', '马虎', '随便', '看心情', '无所谓', '差不多']
        },
        'extraversion': {
            'high': ['我们', '一起', '大家', '热闹', '聊天', '聚会', '朋友', '社交', '主动'],
            'low': ['自己', '安静', '独处', '思考', '内向', '一个人', '低调']
        },
        'agreeableness': {
            'high': ['谢谢', '感谢', '帮忙', '理解', '体贴', '关心', '温暖', '善良', '友好', '客气'],
            'low': ['但是', '不过', '可是', '不同意', '批评', '反驳', '质疑', '挑战']
        },
        'neuroticism': {
            'high': ['担心', '焦虑', '害怕', '紧张', '不安', '压力', '失眠', '烦恼', '难过'],
            'low': ['平静', '淡定', '冷静', '放松', '稳定', '随和', '乐观']
        }
    }

    # 风险识别特征词
    RISK_KEYWORDS = {
        'work_shirt': {  # 职场甩锅
            'keywords': ['不是我的问题', '我以为', '我不知道', '问别人', '找领导', '不归我管', '按规定', '流程问题', '沟通问题', '责任不在我', '你没说清楚', '我没收到', '等通知', '再等等'],
            'description': '对方可能正在推卸责任或拖延'
        },
        'pig_butcher': {  # 杀猪盘
            'keywords': ['投资', '赚钱', '高回报', '稳赚', '区块链', '虚拟币', '彩票', '赌博', '平台', '充值', '转账', '保证金', '税务', '账户异常', '安全账户', '代收', '帮忙', '不方便', '先借我'],
            'description': '对方可能正在实施诈骗'
        },
        'hr_bad': {  # HR不当人
            'keywords': ['试用期', '工资打折', '不加金', '末尾淘汰', '强制加班', '免费加班', '不签合同', '社保', '公积金', '绩效', '优化', '输送', '毕业', '向社会输送'],
            'description': '对方可能在进行不当用工行为'
        },
        'teammate_trouble': {  # 猪队友坑人
            'keywords': ['忘了', '不好意思', '不好意思哈', '抱歉', '打扰了', '我以为你知道', '别人也是这么做的', '大家都这样', '问题不大', '没事的', '没关系', '小问题', '差不多得了', '将就一下', '能跑就行', '先上线再说', '后面再改', '来不及了'],
            'description': '对方可能不负责任或敷衍了事'
        }
    }

    # 多方案话术预测
    RESPONSE_STRATEGIES = {
        'work_shirt': {
            'defensive': ['好的，我先记录一下这个情况', '我需要确认一下具体责任划分', '我们可以一起回顾一下流程', '请给我发邮件确认具体要求'],
            'offensive': ['这个情况我需要向领导汇报一下', '建议我们开个会明确一下责任', '我可以配合，但需要您先确认需求'],
            'diplomatic': ['我理解您的立场，我们看看怎么协作解决', '感谢您的反馈，我会跟进处理的', '好的，我这边会配合您的工作']
        },
        'pig_butcher': {
            'defensive': ['我需要考虑一下，和家里人商量一下', '我最近资金比较紧张', '我对这个不太懂，不敢轻易尝试'],
            'offensive': ['请问这个平台有正规资质吗？', '能问一下您的投资经验吗？', '我可以先了解一下这个项目吗？'],
            'diplomatic': ['听起来不错，但我得先研究研究', '好的，我先看看资料', '我最近在忙别的项目，以后再说吧']
        },
        'hr_bad': {
            'defensive': ['我需要咨询一下专业人士的意见', '我查一下劳动法的规定', '我考虑一下这个方案'],
            'offensive': ['请问有书面的offer吗？', '这个待遇和面试时说的不太一样', '我可以了解一下公司的正规流程吗？'],
            'diplomatic': ['我理解公司的考量，但这个条件我可能需要再沟通一下', '这个我需要和家人商量一下', '我可以先考虑一下吗？']
        },
        'teammate_trouble': {
            'defensive': ['好的，我这边先做备份', '我增加一些检查环节', '我单独测试一下'],
            'offensive': ['这个问题可能会影响用户', '建议我们先解决这个风险', '我需要向领导报备一下这个情况'],
            'diplomatic': ['我们一起检查一下有没有其他问题吧', '我这边帮你多测几遍', '我看一下能不能优化一下']
        }
    }

    # 情感词典 — 所有词条长度 >= 2 字符
    EMOTION_WORDS = {
        'positive': ['开心', '高兴', '快乐', '喜欢', '幸福', '优秀', '完美', '感谢', '谢谢', '不错', '期待', '希望', '哈哈', '嘿嘿', '嘻嘻', '太棒了', '绝了', '厉害', '可爱', '漂亮', '感动', '温馨', '舒服'],
        'negative': ['难过', '伤心', '生气', '愤怒', '讨厌', '担心', '焦虑', '害怕', '紧张', '不安', '压力', '烦恼', '郁闷', '沮丧', '失望', '无奈', '委屈', '痛苦', '崩溃', '绝望', '妈的'],
        'neutral': ['好吧', '随便', '还行', '一般', '普通', '正常']
    }

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.analysis_config = config.get('analysis', {})

    def analyze(self, messages: List[Dict]) -> Dict[str, Any]:
        """
        全面分析聊天记录

        Args:
            messages: 解析后的消息列表，每条消息包含 sender, content, timestamp

        Returns:
            分析结果字典
        """
        results = {
            'timestamp': datetime.now().isoformat(),
            'stats': self._analyze_stats(messages),
            'time_distribution': self._analyze_time_distribution(messages),
            'word_frequency': self._analyze_word_frequency(messages),
            'risks': self.analyze_risk_detection(messages),
        }

        # 提取对方的消息进行分析（排除自己的消息）
        other_messages = [m for m in messages if m.get('sender') != 'self']
        if other_messages:
            text = ' '.join([m.get('content', '') for m in other_messages])

            # MBTI分析
            if self.analysis_config.get('mbti_enabled', True):
                results['mbti'] = self._analyze_mbti(text)

            # 大五人格分析
            if self.analysis_config.get('bigfive_enabled', True):
                results['big_five'] = self._analyze_big_five(text)

            # 情感分析
            if self.analysis_config.get('sentiment_enabled', True):
                results['sentiment'] = self._analyze_sentiment(text)

            # 对话预测（多方案）
            if self.analysis_config.get('prediction_enabled', True):
                results['prediction'] = self._predict_next_message(text, results)

            # 场景分析
            results['scenario_analysis'] = self._analyze_scenario(messages, results)

        return results

    def _analyze_stats(self, messages: List[Dict]) -> Dict[str, int]:
        """分析基本统计数据"""
        total = len(messages)
        self_count = sum(1 for m in messages if m.get('sender') == 'self')
        other_count = total - self_count

        # 计算平均消息长度
        contents = [m.get('content', '') for m in messages if m.get('content')]
        avg_length = sum(len(c) for c in contents) / len(contents) if contents else 0

        # 计算对话持续时间
        timestamps = [m.get('timestamp') for m in messages if m.get('timestamp')]
        duration = None
        if len(timestamps) >= 2:
            try:
                start = datetime.fromisoformat(timestamps[0])
                end = datetime.fromisoformat(timestamps[-1])
                duration = (end - start).days
            except:
                pass

        return {
            'total_messages': total,
            'self_messages': self_count,
            'other_messages': other_count,
            'avg_message_length': round(avg_length, 1),
            'conversation_duration_days': duration
        }

    def _analyze_time_distribution(self, messages: List[Dict]) -> Dict[str, Any]:
        """分析时间分布"""
        hours = {'morning': 0, 'afternoon': 0, 'evening': 0, 'night': 0}
        weekdays = {i: 0 for i in range(7)}

        for msg in messages:
            ts = msg.get('timestamp')
            if not ts:
                continue
            try:
                dt = datetime.fromisoformat(ts)
                # 时间段
                h = dt.hour
                if 6 <= h < 12:
                    hours['morning'] += 1
                elif 12 <= h < 18:
                    hours['afternoon'] += 1
                elif 18 <= h < 24:
                    hours['evening'] += 1
                else:
                    hours['night'] += 1
                # 星期
                weekdays[dt.weekday()] += 1
            except:
                continue

        return {'hours': hours, 'weekdays': weekdays}

    def _analyze_word_frequency(self, messages: List[Dict]) -> List[Tuple[str, int]]:
        """分析词频"""
        stopwords = {'的', '了', '是', '在', '我', '你', '他', '她', '它', '这', '那', '有', '和', '就', '不', '也', '都', '要', '会', '可以', '能', '一个', '什么', '怎么', '为什么', '吗', '呢', '吧', '啊', '哦', '嗯', '哈', '哈哈', '嘿嘿', '嘻嘻', '。', '，', '！', '？', '...', '～'}

        words = []
        for msg in messages:
            content = msg.get('content', '')
            # 简单分词（按标点和空格分割）
            tokens = re.split(r'[，。！？、\s]+', content)
            for token in tokens:
                token = token.strip()
                if token and len(token) > 1 and token not in stopwords:
                    words.append(token)

        counter = Counter(words)
        return counter.most_common(50)

    def _analyze_mbti(self, text: str) -> Dict[str, Any]:
        """推断MBTI类型"""
        scores = {'E': 0, 'I': 0, 'S': 0, 'N': 0, 'T': 0, 'F': 0, 'J': 0, 'P': 0}

        for dimension, data in self.MBTI_KEYWORDS.items():
            for keyword in data.get('energy', []) + data.get('sensing', []) + data.get('thinking', []) + data.get('judging', []):
                if keyword in text:
                    scores[dimension] += 1

        # 确定每对的偏好
        preference = {
            'EvsI': 'E' if scores['E'] > scores['I'] else 'I',
            'SvsN': 'S' if scores['S'] > scores['N'] else 'N',
            'TvsF': 'T' if scores['T'] > scores['F'] else 'F',
            'JvsP': 'J' if scores['J'] > scores['P'] else 'P'
        }

        mbti_type = preference['EvsI'] + preference['SvsN'] + preference['TvsF'] + preference['JvsP']

        # MBTI类型名称和描述
        mbti_names = {
            'INTJ': ('建筑师', '独立思考者，战略性强'),
            'INTP': ('逻辑学家', '理性分析者，好奇心强'),
            'ENTJ': ('指挥官', '果断领导型，决策力强'),
            'ENTP': ('辩论家', '思维敏捷，善于创新'),
            'INFJ': ('倡导者', '理想主义者，洞察力强'),
            'INFP': ('调停者', '浪漫主义者，善解人意'),
            'ENFJ': ('主人公', '热情领导者，有感染力'),
            'ENFP': ('竞选者', '充满激情，创造力强'),
            'ISTJ': ('物流师', '尽职尽责，稳重可靠'),
            'ISFJ': ('守护者', '体贴细心，默默付出'),
            'ESTJ': ('总经理', '执行能力强，管理风格'),
            'ESFJ': ('供给者', '热情助人，人际导向'),
            'ISTP': ('鉴赏家', '实际动手，灵活变通'),
            'ISFP': ('艺术家', '敏感细腻，美感丰富'),
            'ESTP': ('企业家', '行动导向，适应力强'),
            'ESFP': ('表演者', '活泼开朗，享受当下')
        }

        name, desc = mbti_names.get(mbti_type, ('未知', '分析中'))

        # 计算置信度
        total_score = sum(scores.values())
        confidence = min(90, 50 + (total_score / 10) * 10) if total_score > 0 else 50

        return {
            'type': mbti_type,
            'name': name,
            'description': desc,
            'confidence': round(confidence, 1),
            'dimension_scores': scores,
            'preference': preference
        }

    def _analyze_big_five(self, text: str) -> Dict[str, float]:
        """分析大五人格"""
        scores = {k: {'high': 0, 'low': 0} for k in self.BIGFIVE_KEYWORDS.keys()}

        for dimension, keywords in self.BIGFIVE_KEYWORDS.items():
            for keyword in keywords.get('high', []):
                if keyword in text:
                    scores[dimension]['high'] += 1
            for keyword in keywords.get('low', []):
                if keyword in text:
                    scores[dimension]['low'] += 1

        # 计算百分比
        result = {}
        for dimension, score in scores.items():
            total = score['high'] + score['low']
            if total > 0:
                result[dimension] = round(score['high'] / total * 100, 1)
            else:
                result[dimension] = 50.0

        # 添加中文标签
        labels = {
            'openness': '开放性',
            'conscientiousness': '尽责性',
            'extraversion': '外向性',
            'agreeableness': '宜人性',
            'neuroticism': '神经质'
        }
        result['labels'] = labels

        return result

    def _analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """分析情感倾向"""
        pos_count = sum(1 for w in self.EMOTION_WORDS['positive'] if w in text)
        neg_count = sum(1 for w in self.EMOTION_WORDS['negative'] if w in text)
        neu_count = sum(1 for w in self.EMOTION_WORDS['neutral'] if w in text)

        total = pos_count + neg_count + neu_count
        if total == 0:
            return {
                'positive': 50.0,
                'negative': 50.0,
                'neutral': 50.0,
                'trend': 'stable',
                'emotional_words': []
            }

        return {
            'positive': round(pos_count / total * 100, 1),
            'negative': round(neg_count / total * 100, 1),
            'neutral': round(neu_count / total * 100, 1),
            'trend': 'up' if pos_count > neg_count else 'down' if neg_count > pos_count else 'stable',
            'emotional_words': {
                'positive': [w for w in self.EMOTION_WORDS['positive'] if w in text][:10],
                'negative': [w for w in self.EMOTION_WORDS['negative'] if w in text][:10]
            }
        }

    def _predict_next_message(self, text: str, results: Dict) -> Dict[str, str]:
        """预测对方下一步可能说的话"""
        predictions = []

        # 获取场景信息
        scenario = results.get('scenario_analysis', {}).get('primary', 'social')
        mbti = results.get('mbti', {}).get('type', '')
        big_five = results.get('big_five', {})

        # 优先使用ConversationPredictor（如果可用）
        if HAS_CONVERSATION_PREDICTOR:
            try:
                predictor = ConversationPredictor(self.config)
                pred_result = predictor.predict(
                    messages=[{'content': text, 'sender': 'other', 'timestamp': ''}],
                    mbti=mbti,
                    big_five=big_five,
                    scenario=scenario,
                    context=results
                )
                return pred_result
            except Exception:
                pass  # 降级到规则预测

        # 基于MBTI的预测
        mbti_predictions = {
            'INTJ': ['让我想想这个问题的逻辑', '我需要分析一下', '这不符合我的计划'],
            'INTP': ['理论上是这样', '让我理清思路', '我觉得这个问题的关键是'],
            'ENTJ': ['我来明确一下目标', '我们需要按步骤执行', '结论是'],
            'ENTP': ['这个角度很有趣', '我有一个新想法', '如果我们换个角度看'],
            'INFJ': ['我理解你的感受', '我希望我们能达成共识', '从长远来看'],
            'INFP': ['我觉得这很重要', '这让我想到了一些事', '希望我们能找到一个双方都接受的方案'],
            'ENFJ': ['你今天怎么样', '我们来聊聊', '我有个想法想和你分享'],
            'ENFP': ['太有趣了！', '你有没有想过', '让我们尝试点新鲜的'],
            'ISTJ': ['按照计划进行', '我们需要按步骤来', '事实是这样的'],
            'ISFJ': ['你还好吗', '我来帮你', '不用担心，有我在'],
            'ESTJ': ['我来安排一下', '我们按流程走', '效率很重要'],
            'ESFJ': ['大家一起讨论', '气氛有点沉闷啊', '有什么我能帮忙的吗'],
            'ISTP': ['让我看看怎么解决', '我试试看', '这很直接'],
            'ISFP': ['慢慢来', '你喜欢就好', '我觉得这样也不错'],
            'ESTP': ['走一步看一步', '先试试再说', '管他呢，做了再说'],
            'ESFP': ['太好玩了', '我们出去玩吧', '开心最重要']
        }

        if mbti in mbti_predictions:
            predictions.extend(mbti_predictions[mbti])

        # 基于情感的预测
        sentiment = results.get('sentiment', {})
        if sentiment.get('trend') == 'up':
            predictions.append('继续保持这样挺好的')
        elif sentiment.get('trend') == 'down':
            predictions.append('发生什么了吗？聊聊？')

        # 基于场景的预测
        if scenario == 'romantic':
            predictions.extend(['我也很期待', '那我们约个时间吧', '你有什么安排吗'])
        elif scenario == 'work':
            predictions.extend(['收到，我处理一下', '我确认一下情况', '好的'])

        # 基于最近话题的预测
        recent_words = [w for w, _ in results.get('word_frequency', [])[:10]]
        if '吃饭' in recent_words or '餐厅' in recent_words:
            predictions.append('一起去吃吗？')
        if '工作' in recent_words or '加班' in recent_words:
            predictions.append('工作顺利吗？')
        if '视频' in recent_words or '电影' in recent_words:
            predictions.append('最近看了什么好剧？')

        # 如果没有足够预测，使用默认
        if len(predictions) < 3:
            predictions.extend([
                '嗯嗯，好的',
                '怎么突然说起这个',
                '然后呢'
            ])

        return {
            'next_message': predictions[0],
            'alternatives': predictions[1:4],
            'based_on': 'mbti_sentiment_topics'
        }

    def analyze_risk_detection(self, messages: List[Dict]) -> Dict[str, Any]:
        """检测职场风险、杀猪盘、HR不当人、猪队友等场景"""
        text = ' '.join([m.get('content', '') for m in messages])

        risks = {}
        for risk_type, data in self.RISK_KEYWORDS.items():
            matched = [kw for kw in data['keywords'] if kw in text]
            if matched:
                risks[risk_type] = {
                    'detected': True,
                    'matched_keywords': matched,
                    'description': data['description'],
                    'risk_level': self._calculate_risk_level(matched, len(text)),
                    'response_strategies': self._generate_response_strategies(risk_type, matched)
                }

        return risks if risks else {'no_risk_detected': True}

    def _analyze_scenario(self, messages: List[Dict], results: Dict) -> Dict[str, Any]:
        """分析场景：恋爱/工作/交友/重要事项"""
        text = ' '.join([m.get('content', '') for m in messages])

        scenarios = {
            'romantic': {
                'keywords': ['喜欢', '爱', '想你', '约会', '吃饭', '电影', '逛街', '礼物', '生日', '纪念日', '晚安', '早安', '宝贝', '亲爱的', '甜蜜', '幸福'],
                'weight': 0
            },
            'work': {
                'keywords': ['工作', '加班', '项目', '开会', '报告', '方案', '客户', '领导', '同事', '工资', '晋升', '面试', '入职', '辞职', 'deadline'],
                'weight': 0
            },
            'social': {
                'keywords': ['朋友', '聚会', '一起', '玩', '游戏', '运动', '旅游', '美食', '分享', '八卦', '聊天', '有趣'],
                'weight': 0
            },
            'important': {
                'keywords': ['重要', '紧急', '确认', 'deadline', '截止', '必须', '完成', '交付', '审核', '签约', '合同', '付款', '转账'],
                'weight': 0
            }
        }

        # 计算每个场景的权重
        for scenario, data in scenarios.items():
            for keyword in data['keywords']:
                if keyword in text:
                    data['weight'] += 1

        # 确定主要场景
        sorted_scenarios = sorted(scenarios.items(), key=lambda x: x[1]['weight'], reverse=True)
        primary_scenario = sorted_scenarios[0][0] if sorted_scenarios[0][1]['weight'] > 0 else 'social'

        return {
            'primary': primary_scenario,
            'all_scenarios': {k: v['weight'] for k, v in scenarios.items()},
            'romantic_score': scenarios['romantic']['weight'],
            'work_score': scenarios['work']['weight'],
            'social_score': scenarios['social']['weight'],
            'important_score': scenarios['important']['weight'],
            'suggestions': self._generate_scenario_suggestions(primary_scenario, results)
        }

    def _generate_scenario_suggestions(self, scenario: str, results: Dict) -> Dict[str, List[str]]:
        """根据场景生成建议"""
        suggestions = {
            'romantic': {
                'dating': ['可以主动邀约，但要给对方留余地', '注意观察对方回复的积极程度', '保持适度的神秘感和新鲜感'],
                'monitoring': ['注意聊天频率变化', '关注情绪关键词的变化', '记录重要的纪念日和承诺']
            },
            'work': {
                'communication': ['重要事项要用书面确认', '及时记录决策和承诺', '明确责任边界'],
                'monitoring': ['识别甩锅信号', '注意加班频率变化', '关注态度突然变化']
            },
            'social': {
                'dating': ['保持真诚，不要过度奉承', '找到共同兴趣话题', '给对方适当的空间'],
                'monitoring': ['识别过度索取型朋友', '注意借钱相关话题', '观察承诺兑现情况']
            },
            'important': {
                'dating': ['重要事项必须书面确认', '及时跟进进度', '设置提醒节点'],
                'monitoring': ['识别拖延信号', '注意模糊承诺', '监控关键时间节点']
            }
        }

        mbti = results.get('mbti', {}).get('type', '')
        return suggestions.get(scenario, suggestions['social'])

    def _calculate_risk_level(self, matched: List[str], text_length: int) -> str:
        """计算风险等级"""
        ratio = len(matched) / max(text_length / 500, 1)  # 每500字一个关键词
        if ratio > 0.05 or len(matched) >= 3:
            return 'high'
        elif ratio > 0.02 or len(matched) >= 2:
            return 'medium'
        return 'low'

    def _generate_response_strategies(self, risk_type: str, matched: List[str]) -> Dict[str, List[str]]:
        """生成多方案应对话术"""
        strategies = self.RESPONSE_STRATEGIES.get(risk_type, {})

        return {
            'defensive': strategies.get('defensive', []),  # 防守型
            'offensive': strategies.get('offensive', []),  # 进攻型
            'diplomatic': strategies.get('diplomatic', [])  # 外交型
        }

    def analyze_conversation_pattern(self, messages: List[Dict]) -> Dict[str, Any]:
        """分析对话模式"""
        patterns = {
            'reply_speed': [],
            'message_length_variance': [],
            'initiation_ratio': {'self': 0, 'other': 0},
            'question_count': 0,
            'exclamation_count': 0
        }

        for i, msg in enumerate(messages):
            content = msg.get('content', '')

            # 消息长度变化
            patterns['message_length_variance'].append(len(content))

            # 问题数量
            if '?' in content or '？' in content:
                patterns['question_count'] += 1

            # 感叹号数量
            patterns['exclamation_count'] += content.count('!') + content.count('！')

            # 主动发起对话（每轮对话的第一条消息）
            if i == 0:
                if msg.get('sender') == 'self':
                    patterns['initiation_ratio']['self'] += 1
                else:
                    patterns['initiation_ratio']['other'] += 1
            elif i > 0:
                prev_ts = messages[i-1].get('timestamp')
                curr_ts = msg.get('timestamp')
                if prev_ts and curr_ts:
                    try:
                        prev_dt = datetime.fromisoformat(prev_ts)
                        curr_dt = datetime.fromisoformat(curr_ts)
                        gap = (curr_dt - prev_dt).total_seconds()
                        # 如果间隔超过2小时，算新一轮对话
                        if gap > 7200:
                            if msg.get('sender') == 'self':
                                patterns['initiation_ratio']['self'] += 1
                            else:
                                patterns['initiation_ratio']['other'] += 1
                    except:
                        pass

        # 计算统计值
        lengths = patterns['message_length_variance']
        return {
            'avg_message_length': sum(lengths) / len(lengths) if lengths else 0,
            'question_ratio': round(patterns['question_count'] / len(messages) * 100, 1) if messages else 0,
            'exclamation_ratio': round(patterns['exclamation_count'] / len(messages) * 100, 1) if messages else 0,
            'initiation_ratio': {
                'self': patterns['initiation_ratio']['self'],
                'other': patterns['initiation_ratio']['other']
            }
        }
