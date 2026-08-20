#!/usr/bin/env python3
"""
LLM 驱动的聊天分析模块
在规则分析基础上，使用大模型生成更人性化、更准确的分析结果
支持兼容 OpenAI 接口的任何大模型（DeepSeek、通义千问、OpenAI 等）
"""

import json
import re
import time
from datetime import datetime
import os
from typing import Dict, List, Any, Optional


def get_llm_client(config: Dict[str, Any]):
    """获取 LLM 客户端（兼容 OpenAI 接口）"""
    llm_config = config.get('llm', {})
    if not llm_config.get('enabled'):
        return None

    api_key = llm_config.get('api_key', '')
    if not api_key:
        return None

    try:
        from openai import OpenAI
        client = OpenAI(
            api_key=api_key,
            base_url=llm_config.get('base_url', 'https://api.deepseek.com'),
            timeout=llm_config.get('timeout', 30)
        )
        return client
    except ImportError:
        return None


def call_llm(client, model: str, messages: List[Dict], temperature: float = 0.7) -> Optional[str]:
    """调用 LLM API，返回响应文本"""
    try:
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"  [LLM API错误] {e}")
        return None


# ============================================================
# 提示词工程
# ============================================================

SYSTEM_PROMPT = """你是一个专业的微信聊天记录分析师，擅长从聊天内容中分析人物性格、情感状态和潜在风险。

分析维度：
1. MBTI人格类型推断（16种类型）
2. 大五人格五维分析（开放/尽责/外向/宜人/神经质）
3. 情感状态总结（正面/负面/中性趋势 + 具体情绪词）
4. 风险预警（职场甩锅/杀猪盘/HR不当/猪队友）
5. 对话预测（对方下一步可能说什么）
6. 场景判断（恋爱/工作/交友/商务/日常）

输出要求：
- 说人话，不要学术腔
- 每个维度的结论要给出具体依据（引用聊天中的原话）
- 风险预警要给出置信度（低/中/高）
- 对话预测要给出2-3个不同风格的回复建议
- 如果是中文聊天，用中文输出
"""

USER_ANALYZE_TPL = """请分析以下微信聊天记录：

【聊天内容】
{chat_content}

【分析要求】
1. MBTI人格类型 + 置信度（%）+ 简短说明
2. 大五人格五个维度的得分（0-100）+ 每个维度的关键特征词
3. 情感状态总结（整体倾向 + 具体情绪）+ 正面/负面消息占比
4. 风险预警（如果有的话）：类型 + 置信度 + 匹配关键词 + 应对话术建议
5. 对话预测：对方下一步可能说什么（1-2句）+ 2个不同风格的回复建议
6. 场景判断：这是什么类型的对话（恋爱/工作/交友/商务/日常）
7. 一个简短总结（50字以内）

请用JSON格式输出，字段名如下：
mbti (type/name/confidence), big_five (openness/conscientiousness/extraversion/agreeableness/neuroticism),
sentiment (trend/summary/positive_ratio/negative_ratio),
risks (array of {{type/description/risk_level/matched_keywords/response_strategies}}),
prediction (next_message/suggestions array),
scenario, summary
"""

USER_SUMMARY_TPL = """请为以下聊天记录生成一份简短的人类可读的分析报告（300字以内）：

【聊天内容摘要】
- 总消息数：{total}
- 对方消息：{other}
- 你的消息：{self}

【关键聊天片段】
{highlights}

请用"说人话"的方式撰写，包含：
1. 对方是一个什么样的人（性格画像）
2. 这段关系/对话的状态
3. 建议采取的行动

用中文输出。"""


# ============================================================
# 核心分析类
# ============================================================

class LLMAnalyzer:
    """LLM 驱动的聊天分析器（兼容 OpenAI 接口的任何大模型）"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.client = get_llm_client(config)
        llm_config = config.get('llm', {})
        self.model = llm_config.get('model', 'deepseek-chat')
        self.temperature = llm_config.get('temperature', 0.7)

    def is_available(self) -> bool:
        """是否可用（已配置API且已启用）"""
        return self.client is not None

    def _format_chat(self, messages: List[Dict[str, Any]], max_msgs: int = 100) -> str:
        """格式化聊天记录用于prompt"""
        lines = []
        for i, m in enumerate(messages[:max_msgs]):
            sender = "我" if m.get('sender') == 'self' else "对方"
            content = m.get('content', '').strip()
            ts = m.get('timestamp', '')
            if ts:
                try:
                    dt = datetime.fromisoformat(ts)
                    ts_str = dt.strftime('%m-%d %H:%M')
                except Exception:
                    ts_str = ts[:10]
                lines.append(f"[{ts_str}] {sender}：{content}")
            else:
                lines.append(f"{sender}：{content}")

        if len(messages) > max_msgs:
            lines.append(f"...（共 {len(messages)} 条消息，以上为最近 {max_msgs} 条）")

        return '\n'.join(lines)

    def _extract_json_from_response(self, text: str) -> Optional[Dict]:
        """从响应中提取JSON，支持多种格式"""
        if not text:
            return None

        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        for pattern in [r'```(?:json)?\s*([\s\S]*?)\s*```', r'(\{[\s\S]*?\})']:
            for m in re.finditer(pattern, text):
                candidate = m.group(1).strip()
                try:
                    return json.loads(candidate)
                except json.JSONDecodeError:
                    continue
        return None

    def analyze(self, messages: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """使用 LLM 分析聊天记录"""
        if not self.is_available():
            return None

        if not messages:
            return None

        chat_content = self._format_chat(messages)
        user_prompt = USER_ANALYZE_TPL.format(chat_content=chat_content)

        messages_payload = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt}
        ]

        response = call_llm(
            self.client, self.model, messages_payload,
            temperature=self.temperature
        )

        if not response:
            return None

        parsed = self._extract_json_from_response(response)
        if not parsed:
            return {
                'raw_analysis': response,
                'summary': response[:200] if len(response) > 200 else response,
                'mbti': {'type': '未知', 'name': '需要更多数据', 'confidence': 0},
                'big_five': {'openness': 50, 'conscientiousness': 50, 'extraversion': 50, 'agreeableness': 50, 'neuroticism': 50},
                'sentiment': {'trend': '未知', 'summary': '分析失败', 'positive_ratio': 50},
                'risks': [],
                'prediction': {'next_message': '无法预测', 'suggestions': []},
                'scenario': '未知',
            }

        parsed['raw_analysis'] = response
        return parsed

    def generate_summary(self, messages: List[Dict], stats: Dict) -> Optional[str]:
        """生成人类可读的分析报告"""
        if not self.is_available():
            return None

        if not messages:
            return None

        highlights = []
        for m in messages[:50]:
            content = m.get('content', '').strip()
            if len(content) > 5 and len(content) < 100:
                sender = "我" if m.get('sender') == 'self' else "对方"
                highlights.append(f"{sender}：{content}")

        highlight_text = '\n'.join(highlights[:10]) if highlights else "（聊天内容较少）"

        user_prompt = USER_SUMMARY_TPL.format(
            total=stats.get('total_messages', 0),
            other=stats.get('other_messages', 0),
            self=stats.get('self_messages', 0),
            highlights=highlight_text
        )

        messages_payload = [
            {"role": "system", "content": "你是一个友善的聊天记录分析师，用口语化的中文撰写分析报告。"},
            {"role": "user", "content": user_prompt}
        ]

        response = call_llm(
            self.client, self.model, messages_payload,
            temperature=0.8
        )
        return response

    def predict_responses(self, messages: List[Dict], scenario: str = "") -> Optional[List[str]]:
        """预测对方的回复 + 给出建议回复"""
        if not self.is_available():
            return None

        if not messages:
            return None

        chat_content = self._format_chat(messages, max_msgs=30)

        prompt = f"""根据以下微信聊天内容，预测对方看到你的最后一条消息后可能的回复（1-2句），然后给出你可以说的话（2个风格：真诚型、机智型）。

聊天记录：
{chat_content}

场景类型：{scenario or '未知'}

请用JSON格式输出：
{{
  "predicted_reply": "对方可能的回复",
  "suggestions": [
    {{"style": "真诚型", "text": "你的回复"}},
    {{"style": "机智型", "text": "你的回复"}}
  ]
}}
"""
        response = call_llm(
            self.client, self.model,
            [{"role": "user", "content": prompt}],
            temperature=0.8
        )

        if not response:
            return None

        parsed = self._extract_json_from_response(response)
        if parsed:
            return parsed
        return None


def enhance_results(
    rule_results: Dict[str, Any],
    messages: List[Dict],
    config: Dict[str, Any]
) -> Dict[str, Any]:
    """
    用 LLM 分析增强规则分析结果

    流程：
    1. 如果 LLM 可用：先用 LLM 分析，再与规则分析合并（LLM 优先）
    2. 如果 LLM 不可用：纯规则分析结果
    """
    llm_analyzer = LLMAnalyzer(config)

    if not llm_analyzer.is_available():
        return {
            **rule_results,
            'analysis_mode': 'rule_only',
            'ai_enhanced': False,
            'llm_available': False,
        }

    llm_results = llm_analyzer.analyze(messages)

    summary = llm_analyzer.generate_summary(
        messages,
        rule_results.get('stats', {})
    )

    if llm_results:
        combined = {**rule_results}

        if llm_results.get('mbti'):
            combined['mbti'] = llm_results['mbti']

        if llm_results.get('big_five'):
            combined['big_five'] = llm_results['big_five']

        if llm_results.get('sentiment'):
            combined['sentiment'] = llm_results['sentiment']

        if llm_results.get('risks'):
            combined['risks'] = llm_results['risks']

        if llm_results.get('prediction'):
            combined['prediction'] = llm_results['prediction']

        if llm_results.get('scenario'):
            combined['scenario'] = llm_results['scenario']

        combined['summary'] = summary or llm_results.get('summary', '')
        combined['raw_ai_analysis'] = llm_results.get('raw_analysis', '')
        combined['analysis_mode'] = 'llm_primary'
        combined['ai_enhanced'] = True
        combined['llm_available'] = True

        return combined
    else:
        return {
            **rule_results,
            'summary': summary or rule_results.get('summary', ''),
            'analysis_mode': 'rule_fallback',
            'ai_enhanced': False,
            'llm_available': True,
        }
