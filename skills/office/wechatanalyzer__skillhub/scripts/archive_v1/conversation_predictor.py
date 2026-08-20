#!/usr/bin/env python3
"""
对话预测器 - 基于MiroFish群体智能引擎的增强对话预测
支持多方案话术生成和场景模拟
"""

import json
import uuid
from typing import Dict, List, Any, Optional
from datetime import datetime


class ConversationPredictor:
    """
    基于MiroFish OASIS模拟引擎的对话预测器
    通过模拟对话场景生成多方案预测话术
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.mirofish_config = config.get('mirofish', {})
        self.enabled = self.mirofish_config.get('enabled', False)

    def predict(self, messages: List[Dict], mbti: str = None, big_five: Dict = None,
               scenario: str = None, context: Dict = None) -> Dict[str, Any]:
        """
        生成对话预测

        Args:
            messages: 聊天记录消息列表
            mbti: MBTI人格类型
            big_five: 大五人格数据
            scenario: 场景类型（romantic/work/social/important）
            context: 额外的上下文信息

        Returns:
            包含多方案预测话术的字典
        """
        if not self.enabled:
            return self._rule_based_predict(messages, mbti, scenario)

        try:
            return self._mirofish_predict(messages, mbti, big_five, scenario, context)
        except Exception as e:
            # 降级到规则预测
            return self._rule_based_predict(messages, mbti, scenario)

    def _mirofish_predict(self, messages: List[Dict], mbti: str, big_five: Dict,
                          scenario: str, context: Dict) -> Dict[str, Any]:
        """
        使用MiroFish OASIS模拟引擎进行预测
        """
        # 构建对话上下文
        dialogue_context = self._build_context(messages, mbti, scenario)

        # 模拟多个Agent响应
        agents = self._generate_virtual_agents(mbti, big_five, scenario)

        # 生成多方案话术
        responses = self._simulate_responses(dialogue_context, agents, scenario)

        return {
            'next_message': responses[0] if responses else '好的',
            'alternatives': responses[1:4] if len(responses) > 1 else responses,
            'based_on': 'mirofish_simulation',
            'scenario': scenario,
            'agents_simulated': len(agents),
            'confidence': 0.85
        }

    def _build_context(self, messages: List[Dict], mbti: str, scenario: str) -> str:
        """构建对话上下文字符串"""
        recent = messages[-10:] if len(messages) >= 10 else messages
        lines = []

        for msg in recent:
            sender = msg.get('sender', 'unknown')
            content = msg.get('content', '')
            lines.append(f"{sender}: {content}")

        context = '\n'.join(lines)

        # 添加场景描述
        scenario_desc = {
            'romantic': '浪漫约会场景',
            'work': '工作沟通场景',
            'social': '日常社交场景',
            'important': '重要事项对接场景'
        }.get(scenario, '日常对话场景')

        return f"【{scenario_desc}】当前对话：\n{context}"

    def _generate_virtual_agents(self, mbti: str, big_five: Dict,
                                  scenario: str) -> List[Dict]:
        """
        生成虚拟Agent进行模拟
        基于MBTI和场景生成不同性格的Agent
        """
        agents = []

        # 基于MBTI生成不同风格的Agent
        mbti_styles = {
            'E': ['主动热情型', '活泼开朗型'],
            'I': ['内敛思考型', '沉稳理性型'],
            'S': ['务实实际型', '踏实稳健型'],
            'N': ['创新想象型', '理想主义型'],
            'T': ['逻辑分析型', '理性决策型'],
            'F': ['情感共鸣型', '善解人意型'],
            'J': ['计划组织型', '果断执行型'],
            'P': ['灵活适应型', '开放随性型']
        }

        # 根据MBTI生成3-5个Agent
        if mbti and len(mbti) >= 4:
            styles = []
            for i, dim in enumerate(['E', 'S', 'T', 'J']):
                if mbti[i] == dim:
                    styles.extend(mbti_styles.get(dim, []))

            # 确保有足够多的Agent
            while len(styles) < 4:
                styles.append('中立观望型')

            for i, style in enumerate(styles[:4]):
                agents.append({
                    'id': i,
                    'name': f'模拟Agent_{i+1}',
                    'style': style,
                    'mbti': mbti
                })
        else:
            # 默认Agent
            default_styles = ['主动进攻型', '防守回应型', '中立观望型', '情感共鸣型']
            for i, style in enumerate(default_styles):
                agents.append({
                    'id': i,
                    'name': f'模拟Agent_{i+1}',
                    'style': style,
                    'mbti': mbti or 'ENFP'
                })

        return agents

    def _simulate_responses(self, context: str, agents: List[Dict],
                           scenario: str) -> List[str]:
        """
        模拟Agent响应
        这里是一个简化版本，实际项目中会调用OASIS引擎
        """
        responses = []

        # 针对每个Agent生成响应
        for agent in agents:
            style = agent.get('style', '')

            if scenario == 'romantic':
                if '主动' in style or '热情' in style:
                    responses.append('我真的很想见你，我们什么时候可以一起吃饭？')
                elif '内敛' in style or '沉稳' in style:
                    responses.append('好的，那家餐厅确实不错，我查查有没有优惠')
                elif '情感' in style:
                    responses.append('和你聊天真的很开心，希望你今天过得顺利')
                else:
                    responses.append('嗯，收到，我看看时间安排')

            elif scenario == 'work':
                if '主动' in style or '进攻' in style:
                    responses.append('这个任务我来负责推进，有问题随时找我')
                elif '务实' in style or '踏实' in style:
                    responses.append('好的，我先按计划执行，有进展再汇报')
                elif '逻辑' in style or '理性' in style:
                    responses.append('分析一下：这个方案可行性 85%，建议按步骤推进')
                else:
                    responses.append('收到，我这边配合处理')

            elif scenario == 'social':
                if '主动' in style or '热情' in style:
                    responses.append('周末聚会算我一个！大家好久没聚了')
                elif '内敛' in style or '沉稳' in style:
                    responses.append('聚会可以，我尽量调整时间参加')
                elif '创新' in style or '想象' in style:
                    responses.append('有没有什么新鲜的活动？我想尝试点不一样的')
                else:
                    responses.append('好的，到时候见')

            else:  # important or default
                if '主动' in style:
                    responses.append('收到，我马上处理，有结果第一时间反馈')
                elif '防守' in style:
                    responses.append('好的，我确认一下情况再回复你')
                elif '情感' in style:
                    responses.append('别担心，这个事情我会重点关注的')
                else:
                    responses.append('明白，我去跟进一下')

        # 去重并保持顺序
        unique_responses = []
        for r in responses:
            if r not in unique_responses:
                unique_responses.append(r)

        return unique_responses[:5]

    def _rule_based_predict(self, messages: List[Dict], mbti: str,
                          scenario: str) -> Dict[str, Any]:
        """
        基于规则的对话预测（无MiroFish时的降级方案）
        """
        # 获取最近的消息
        last_msg = messages[-1] if messages else {}
        last_content = last_msg.get('content', '').lower()

        # 基于场景和最近消息生成预测
        predictions = []

        if scenario == 'romantic':
            if any(w in last_content for w in ['吃饭', '餐厅', '美食']):
                predictions = ['那我们周六一起去吃吧', '你喜欢什么菜系？', '好的，我查查附近有什么好吃的']
            elif any(w in last_content for w in ['想', '见', '约会']):
                predictions = ['我也是，好想见你', '那我们约个时间？', '期待见面']
            else:
                predictions = ['嗯嗯，好的', '那太好了', '我也这么觉得']

        elif scenario == 'work':
            if any(w in last_content for w in ['任务', '项目', '完成']):
                predictions = ['好的，我尽快处理', '收到，我今天完成', '没问题，我来跟进']
            elif any(w in last_content for w in ['会议', '讨论', '开会']):
                predictions = ['好的，我会准备好材料', '收到，我准时参加', '会议议题能提前发我吗']
            else:
                predictions = ['收到，我处理一下', '好的明白了', '我确认一下再回复']

        elif scenario == 'social':
            if any(w in last_content for w in ['聚会', '一起', '玩']):
                predictions = ['好啊，算我一个', '这次聚会有什么安排？', '好的，到时候见']
            elif any(w in last_content for w in ['周末', '放假']):
                predictions = ['周末有什么计划？', '打算休息一下，你呢', '难得的休息日']
            else:
                predictions = ['哈哈', '确实', '好吧']

        else:  # important
            if any(w in last_content for w in ['确认', '截止']):
                predictions = ['收到，我马上确认', '好的，我核实后回复', '我这边确认一下']
            elif any(w in last_content for w in ['紧急', '重要', '必须']):
                predictions = ['收到，优先处理', '我马上处理', '明白，立即执行']
            else:
                predictions = ['好的，收到', '明白', '我去处理']

        return {
            'next_message': predictions[0],
            'alternatives': predictions[1:],
            'based_on': 'rule_based',
            'scenario': scenario,
            'confidence': 0.7
        }

    def generate_response_strategies(self, scenario: str, mbti: str = None,
                                    risk_type: str = None) -> Dict[str, List[str]]:
        """
        生成多方案应对策略话术

        Args:
            scenario: 场景类型
            mbti: 对方MBTI
            risk_type: 风险类型（如果有）

        Returns:
            包含防守型、进攻型、外交型话术的字典
        """
        strategies = {
            'defensive': [],  # 防守型
            'offensive': [],  # 进攻型
            'diplomatic': []   # 外交型
        }

        # 如果有风险类型，使用专门的风险应对话术
        if risk_type:
            strategies = self._get_risk_strategies(risk_type)
        else:
            # 基于场景生成话术
            if scenario == 'romantic':
                strategies['defensive'] = [
                    '我理解你的想法，但我觉得我们还是先做朋友比较好',
                    '谢谢你的关心，我现在暂时不想改变现状',
                    '我觉得我们应该多了解一下对方'
                ]
                strategies['offensive'] = [
                    '你最近是不是有什么心事？感觉你话里有话',
                    '我觉得我们应该好好谈谈',
                    '你对这段关系的期待是什么？'
                ]
                strategies['diplomatic'] = [
                    '谢谢你的喜欢，但我觉得我们需要更多时间',
                    '我也觉得你人很好，但我还没准备好',
                    '让我们先保持现在的关系，慢慢了解'
                ]

            elif scenario == 'work':
                strategies['defensive'] = [
                    '收到，我先按现有流程处理',
                    '我这边确认一下具体要求',
                    '好的，我先记录一下'
                ]
                strategies['offensive'] = [
                    '这个需求当初没有明确说过',
                    '我们是否需要开个会讨论一下责任划分？',
                    '请问有书面的变更需求吗？'
                ]
                strategies['diplomatic'] = [
                    '我理解这个需求紧急，但我们需要评估一下影响',
                    '好的，我配合处理，但可能需要一些时间',
                    '我们一起看看怎么解决这个问题'
                ]

            elif scenario == 'social':
                strategies['defensive'] = [
                    '谢谢邀请，但我这周可能有安排',
                    '我再看看时间，确认了告诉你',
                    '最近有点忙，下次一定'
                ]
                strategies['offensive'] = [
                    '你总是这样，每次都说下次',
                    '为什么每次都是我配合你？',
                    '你对这次聚会有多认真？'
                ]
                strategies['diplomatic'] = [
                    '好主意，但我需要确认一下时间',
                    '我很想去，但那天可能有事',
                    '下次提前约我，我一定来'
                ]

            else:  # important
                strategies['defensive'] = [
                    '收到，我会重点关注这件事',
                    '我先记录一下，有问题及时同步',
                    '明白，我这边会优先处理'
                ]
                strategies['offensive'] = [
                    '这个问题我们需要明确一下责任',
                    '请问具体的时间节点是什么？',
                    '是否需要开个会确认一下各方职责？'
                ]
                strategies['diplomatic'] = [
                    '好的，我配合处理，有进展及时汇报',
                    '我先了解一下具体情况',
                    '我们保持沟通，有问题随时协调'
                ]

        return strategies

    def _get_risk_strategies(self, risk_type: str) -> Dict[str, List[str]]:
        """获取风险类型的专门应对话术"""
        strategies = {
            'work_shirt': {
                'defensive': [
                    '我理解这个情况，让我先看一下相关记录',
                    '我们是否可以回顾一下当时的沟通记录？',
                    '好的，我先整理一下这个问题的背景'
                ],
                'offensive': [
                    '请问您这边是否有书面确认过这个需求？',
                    '这个情况我需要向领导汇报一下',
                    '我们可能需要HR或者上级来确认一下责任'
                ],
                'diplomatic': [
                    '我理解您的立场，让我们一起看看怎么解决这个问题',
                    '感谢您的反馈，我会跟进处理的',
                    '我们配合一下，先把问题解决'
                ]
            },
            'pig_butcher': {
                'defensive': [
                    '我需要和家人商量一下',
                    '我对这个不太懂，不敢轻易尝试',
                    '最近资金比较紧张，暂时不考虑'
                ],
                'offensive': [
                    '请问这个平台有正规资质吗？',
                    '能介绍一下这个项目的风险吗？',
                    '我怎么验证这个投资的真实性？'
                ],
                'diplomatic': [
                    '听起来不错，但我得先研究研究',
                    '好的，我先看看资料',
                    '我最近在忙别的项目，以后再说吧'
                ]
            },
            'hr_bad': {
                'defensive': [
                    '我需要咨询一下专业人士的意见',
                    '我查一下劳动法的规定',
                    '我考虑一下这个方案'
                ],
                'offensive': [
                    '请问有书面的offer吗？',
                    '这个待遇和面试时说的不太一样',
                    '我可以了解一下公司的正规流程吗？'
                ],
                'diplomatic': [
                    '我理解公司的考量，但这个条件我需要再沟通一下',
                    '这个我需要和家人商量一下',
                    '我可以先考虑一下吗？'
                ]
            },
            'teammate_trouble': {
                'defensive': [
                    '好的，我这边先做备份',
                    '我增加一些检查环节',
                    '我单独测试一下'
                ],
                'offensive': [
                    '这个问题可能会影响用户',
                    '建议我们先解决这个风险',
                    '我需要向领导报备一下这个情况'
                ],
                'diplomatic': [
                    '我们一起检查一下有没有其他问题吧',
                    '我这边帮你多测几遍',
                    '我看一下能不能优化一下'
                ]
            }
        }

        return strategies.get(risk_type, {'defensive': [], 'offensive': [], 'diplomatic': []})
