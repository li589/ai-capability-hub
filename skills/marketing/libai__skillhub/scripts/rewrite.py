#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""AI text rewriting engine.

Optimized version with unified replacement regex, sentence patterns,
and synonym replacement support.
"""

import re
import random
import json
from typing import List, Tuple, Dict, Optional
from pathlib import Path

from rules import RuleSet, load_rules_with_user
from utils import get_sentences, clean_text


class AIRewriter:
    """AI文本改写器 - 支持短语替换、句式改写、同义词替换

    8步流水线与SKILL.md方法论映射：
    - 步骤1(Markdown清理)+2(Chatbot清理)+4(句子级正则) → 一阶：删废词（三步排雷法·搜黑话）
    - 步骤3(短语替换)+5(同义词替换)+6(破折号) → 二阶：换句式（三步排雷法·切长句）
    - 步骤7(长句拆分)+8(后处理) → 三阶：调结构（三步排雷法·加泥土 / 破式五层法·破句式+破结构层）
    - 步骤0/9(代码块提取/回填) → 保障层：代码块完整性保护
    """
    
    def __init__(
        self, 
        rules: Optional[RuleSet] = None, 
        user_rules_path: Optional[str] = None,
        synonyms_path: Optional[str] = None,
        random_seed: Optional[int] = None
    ):
        if rules is None:
            rules = load_rules_with_user(user_rules_path)
        self.rules = rules
        
        # 可配置随机种子（默认 None = 系统熵源；设具体值可复现结果）
        self._rng = random.Random(random_seed) if random_seed is not None else random
        
        # 构建统一替换正则
        self._repl_pattern, self._repl_map = self._build_unified_replacement()
        
        # 编译句子级改写模式（支持多模板）
        self._sentence_patterns = self._prepare_sentence_patterns()
        
        # 加载同义词库
        self.synonyms = self._load_synonyms(synonyms_path)
        self._synonym_pattern = self._build_synonym_pattern()
        
        # Chatbot结尾语：统一从 rules.chatbot_artifacts 加载
        self._chatbot_endings = list(self.rules.chatbot_artifacts)
        
        # 术语白名单 - 不进行同义词替换
        self._term_whitelist = {
            '人工智能', '深度学习', '机器学习', '神经网络', '自然语言处理',
            '计算机视觉', '知识图谱', '大数据', '物联网', '云计算',
            '区块链', '边缘计算', '强化学习', '迁移学习', '联邦学习',
            '图像识别', '语音识别', '人脸识别', '指纹识别',
            '智能城市', '智慧城市', '智能交通', '智慧交通',
            '智能医疗', '智慧医疗', '智能教育', '智慧教育',
            '数据分析', '数据挖掘', '数据科学',
            '算法', '模型', '系统', '平台', '架构',
            'API', 'SDK', 'AI', 'ML', 'NLP', 'CV',
            '实时', '动态', '自动化', '智能化',
        }
    
    def _build_unified_replacement(self) -> Tuple[Optional[re.Pattern], Dict[str, str]]:
        """构建统一替换正则，一次扫描所有替换
        
        添加中文词边界保护，避免短词匹配误伤长词：
        - 纯中文短词（<=3字）添加 (?:^|[^一-龥]) 前缀和 (?=[^一-龥]|$) 后缀
        - 确保"因此"不会误匹配"因此地"中的子串
        """
        replacements = self.rules.replacements
        if not replacements:
            return None, {}
        
        sorted_items = sorted(replacements.items(), key=lambda x: len(x[0]), reverse=True)
        
        parts = []
        repl_map = {}
        for old, new in sorted_items:
            if old:
                escaped = re.escape(old)
                # Add CJK word boundary for short pure-Chinese terms
                # Use \u4e00-\u9fff range in non-raw f-string for proper Unicode escape
                if re.match(r'^[一-龥]+$', old) and len(old) <= 3:
                    escaped = f'(?<![一-鿿]){escaped}(?![一-鿿])'
                parts.append(escaped)
                repl_map[old.lower()] = new
        
        if not parts:
            return None, {}
        
        pattern = re.compile('|'.join(parts), re.IGNORECASE)
        return pattern, repl_map
    
    def _prepare_sentence_patterns(self) -> List[Tuple[re.Pattern, List[str]]]:
        """编译句子级改写模式，每个模式对应多个可能的改写模板"""
        patterns = []
        for item in self.rules.sentence_patterns:
            pattern_str = item.get("pattern", "")
            rewrites = item.get("rewrites", [])
            if pattern_str and rewrites:
                try:
                    pat = re.compile(pattern_str, re.IGNORECASE | re.DOTALL)
                    patterns.append((pat, rewrites))
                except re.error:
                    continue
        return patterns
    
    def _load_synonyms(self, synonyms_path: Optional[str] = None) -> Dict[str, List[str]]:
        """加载同义词库，支持用户自定义 JSON 文件（仅限 resources/ 目录）"""
        if synonyms_path:
            resolved = Path(synonyms_path).resolve()
            resources_dir = (Path(__file__).parent.parent / 'resources').resolve()
            try:
                resolved.relative_to(resources_dir)
            except ValueError:
                raise ValueError(
                    "[路径安全限制] 同义词文件必须在 resources/ 目录内。\n"
                    "→ 被拒绝的路径：{}\n"
                    "→ 建议：请将自定义同义词文件放入 {} 目录下。".format(
                        synonyms_path, resources_dir
                    )
                )
            if not resolved.exists():
                raise FileNotFoundError(f"Synonyms file not found: {resolved}")
            try:
                with open(resolved, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except json.JSONDecodeError as e:
                raise json.JSONDecodeError(
                    "[同义词文件格式错误] JSON 解析失败：{}\n"
                    "→ 建议：请检查同义词文件是否为合法 JSON，位置 {}".format(
                        resolved, e.pos
                    ),
                    e.doc, e.pos
                ) from e
        
        default_path = Path(__file__).parent.parent / 'resources' / 'synonyms.json'
        if default_path.exists():
            try:
                with open(default_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except json.JSONDecodeError as e:
                raise json.JSONDecodeError(
                    "[默认同义词库格式错误] JSON 解析失败：{}\n"
                    "→ 建议：请检查 resources/synonyms.json 是否为合法 JSON，位置 {}".format(
                        default_path, e.pos
                    ),
                    e.doc, e.pos
                ) from e
        return {}
    
    def _build_synonym_pattern(self) -> Optional[re.Pattern]:
        """构建同义词匹配正则
        
        对短中文词（<=3字）添加 CJK 词边界保护，避免"因此"误匹配"因此地"中的子串。
        """
        if not self.synonyms:
            return None
        
        keys = sorted(self.synonyms.keys(), key=len, reverse=True)
        if not keys:
            return None
        
        parts = []
        for k in keys:
            if not k:
                continue
            escaped = re.escape(k)
            # CJK word boundary for short pure-Chinese terms
            if re.match(r'^[一-龥]+$', k) and len(k) <= 3:
                escaped = f'(?<![一-鿿]){escaped}(?![一-鿿])'
            parts.append(escaped)
        
        return re.compile('|'.join(parts))
    
    # 文体感知配置：不同文体对改写强度的容忍度不同
    STYLE_PRESETS = {
        "tech": {   # 技术文档：保守改写，保留术语，减少口语化
            "synonym_prob": 0.15,
            "split_long": False,
            "preserve_hedging": True,
        },
        "web": {    # 网文创作：激进改写，强口语化
            "synonym_prob": 0.40,
            "split_long": True,
            "preserve_hedging": False,
        },
        "academic": {  # 学术论文：极保守，仅去AI痕迹，不动术语
            "synonym_prob": 0.10,
            "split_long": False,
            "preserve_hedging": True,
        },
        "default": {
            "synonym_prob": 0.25,
            "split_long": True,
            "preserve_hedging": False,
        },
    }
    
    def rewrite(self, text: str, aggressive: bool = False, style: str = "default") -> Tuple[str, List[str]]:
        """改写文本，返回 (改写后文本, 变更列表)
        
        Args:
            text: 输入文本
            aggressive: 激进模式（覆盖文体预设的同义词概率）
            style: 文体模式 (tech/web/academic/default)，控制改写强度和策略
        
        重要：改写前提取代码块→对正文执行改写→回填代码块，确保代码块内容不被修改或删除。
        """
        changes = []
        text = clean_text(text)
        
        # 0. 提取并保护代码块（先于任何改写操作）
        text, code_blocks = self._extract_code_blocks(text)
        
        # ===== 一阶：删废词（三步排雷法·搜黑话）=====
        # 步骤1. Markdown清理（仅对正文）
        text, md_changes = self._clean_markdown(text)
        changes.extend(md_changes)
        
        # 步骤2. Chatbot痕迹清理
        text, chat_changes = self._clean_chatbot_artifacts(text)
        changes.extend(chat_changes)
        
        # ===== 二阶：换句式（三步排雷法·切长句）=====
        # 步骤3. 短语替换 - 使用统一正则
        if self._repl_pattern:
            text, count = self._apply_unified_replacement(text)
            if count > 0:
                changes.append(f"短语替换 ({count}处)")
        
        # 步骤4. 句子级模式改写（一阶·删废词——随机选择模板，仍属表层清理）
        for pattern, rewrites in self._sentence_patterns:
            text, cnt = self._apply_sentence_pattern(text, pattern, rewrites)
            if cnt > 0:
                changes.append(f"句式改写 ({cnt}处)")
        
        # 步骤5. 同义词替换（文体感知 + 激进模式 / 二阶·换句式）
        if self._synonym_pattern and self.synonyms:
            preset = self.STYLE_PRESETS.get(style, self.STYLE_PRESETS["default"])
        
        # Apply rewrite_tier_ops tier guidance (low/medium/high risk tier)
        tier_ops = self.rules.rewrite_tier_ops
        if isinstance(tier_ops, dict) and style == "default":
            # Auto-detect: if text has high-risk patterns, boost intensity
            high_risk_signal = False
            medium_risk_signal = False
            # Simple heuristic: check for tier1 circuit breaker patterns
            tier1 = self.rules.tier1_circuit_breaker
            if isinstance(tier1, dict):
                for p in tier1.get('patterns', []):
                    if isinstance(p, dict) and p.get('pattern'):
                        try:
                            if re.search(p['pattern'], text):
                                high_risk_signal = True
                                break
                        except re.error:
                            continue
            # Check for banned_words_v2
            if not high_risk_signal:
                banned_v2 = self.rules.banned_words_v2
                if isinstance(banned_v2, dict):
                    count = 0
                    for cat_key in banned_v2:
                        cat_data = banned_v2[cat_key]
                        if isinstance(cat_data, dict):
                            for entry in cat_data.get('entries', []):
                                if isinstance(entry, dict):
                                    pat = entry.get('pattern', '')
                                    if pat and re.search(re.escape(pat), text):
                                        count += 1
                    if count >= 6:
                        high_risk_signal = True
                    elif count >= 3:
                        medium_risk_signal = True
            
            if high_risk_signal and tier_ops.get('high_risk'):
                preset = dict(preset)
                preset['synonym_prob'] = 0.35
                preset['split_long'] = True
            elif medium_risk_signal and tier_ops.get('medium_risk'):
                preset = dict(preset)
                preset['synonym_prob'] = 0.30
                preset['split_long'] = True
            prob = 0.4 if aggressive else preset["synonym_prob"]
            text, count = self._replace_synonyms(text, prob)
            if count > 0:
                changes.append(f"同义词替换 ({count}处, 概率{prob:.0%})")
        
        # 步骤6. 破折号处理（二阶·换句式——AI高频破折号→逗号）
        old_dashes = text.count('——') + text.count('—')
        text = re.sub(r'——', '，', text)
        text = re.sub(r'—', '，', text)
        new_dashes = text.count('——') + text.count('—')
        if old_dashes > new_dashes:
            changes.append(f"替换破折号 ({old_dashes - new_dashes}处)")
        
        # ===== 三阶：调结构（三步排雷法·加泥土 / 破式五层法·破句式+破结构层）=====
        # 步骤7. 长句拆分（文体感知：学术/技术文档不拆分长句 / 破式五层法 L1·破句式）
        preset = self.STYLE_PRESETS.get(style, self.STYLE_PRESETS["default"])
        
        # Apply rewrite_tier_ops tier guidance (low/medium/high risk tier)
        tier_ops = self.rules.rewrite_tier_ops
        if isinstance(tier_ops, dict) and style == "default":
            # Auto-detect: if text has high-risk patterns, boost intensity
            high_risk_signal = False
            medium_risk_signal = False
            # Simple heuristic: check for tier1 circuit breaker patterns
            tier1 = self.rules.tier1_circuit_breaker
            if isinstance(tier1, dict):
                for p in tier1.get('patterns', []):
                    if isinstance(p, dict) and p.get('pattern'):
                        try:
                            if re.search(p['pattern'], text):
                                high_risk_signal = True
                                break
                        except re.error:
                            continue
            # Check for banned_words_v2
            if not high_risk_signal:
                banned_v2 = self.rules.banned_words_v2
                if isinstance(banned_v2, dict):
                    count = 0
                    for cat_key in banned_v2:
                        cat_data = banned_v2[cat_key]
                        if isinstance(cat_data, dict):
                            for entry in cat_data.get('entries', []):
                                if isinstance(entry, dict):
                                    pat = entry.get('pattern', '')
                                    if pat and re.search(re.escape(pat), text):
                                        count += 1
                    if count >= 6:
                        high_risk_signal = True
                    elif count >= 3:
                        medium_risk_signal = True
            
            if high_risk_signal and tier_ops.get('high_risk'):
                preset = dict(preset)
                preset['synonym_prob'] = 0.35
                preset['split_long'] = True
            elif medium_risk_signal and tier_ops.get('medium_risk'):
                preset = dict(preset)
                preset['synonym_prob'] = 0.30
                preset['split_long'] = True
        if aggressive or preset["split_long"]:
            text, split_count = self._split_long_sentences(text)
            if split_count > 0:
                changes.append(f"拆分长句 ({split_count}处)")
        
        # 步骤8. 后处理清理（三阶·调结构——收尾清理残缺口）
        text = self._post_process(text)
        
        # 9. 回填代码块到原位置
        text = self._restore_code_blocks(text, code_blocks)
        
        text = clean_text(text)
        return text, changes
    
    def _apply_unified_replacement(self, text: str) -> Tuple[str, int]:
        """应用统一替换正则"""
        total_count = 0
        
        def replacer(match):
            nonlocal total_count
            key = match.group(0).lower()
            replacement = self._repl_map.get(key, match.group(0))
            if replacement != match.group(0):
                total_count += 1
            return replacement
        
        text = self._repl_pattern.sub(replacer, text)
        return text, total_count
    
    def _apply_sentence_pattern(
        self, 
        text: str, 
        pattern: re.Pattern, 
        rewrites: List[str]
    ) -> Tuple[str, int]:
        """应用句子级正则改写，随机选择模板"""
        count = 0
        
        def replacer(match):
            nonlocal count
            template = self._rng.choice(rewrites)
            result = match.expand(template)
            if result != match.group(0):
                count += 1
            return result
        
        text, cnt = pattern.subn(replacer, text)
        return text, cnt
    
    def _replace_synonyms(self, text: str, probability: float = 0.3) -> Tuple[str, int]:
        """随机替换文本中的高频词"""
        if not self._synonym_pattern or not self.synonyms:
            return text, 0
        
        count = 0
        
        def replacer(match):
            nonlocal count
            word = match.group(0)
            
            if word in self._term_whitelist:
                return word
            
            if self._rng.random() > probability:
                return word
            
            candidates = self.synonyms.get(word, [])
            candidates = [c for c in candidates if c != word and c not in self._term_whitelist]
            
            if not candidates:
                return word
            
            count += 1
            return self._rng.choice(candidates)
        
        text = self._synonym_pattern.sub(replacer, text)
        return text, count
    
    # Placeholder markers for extracted code blocks
    _CODE_BLOCK_MARKER = "{{CODEBLOCK_%d}}"
    
    def _extract_code_blocks(self, text: str) -> Tuple[str, List[str]]:
        """提取 Markdown 代码块（```...```），替换为占位符。
        
        防止改写流水线删除/修改代码块内容。
        """
        code_blocks = []
        
        def _extract(m):
            code_blocks.append(m.group(0))
            return self._CODE_BLOCK_MARKER % (len(code_blocks) - 1)
        
        text = re.sub(r'```[\s\S]*?```', _extract, text)
        return text, code_blocks
    
    def _restore_code_blocks(self, text: str, code_blocks: List[str]) -> str:
        """将占位符替换回原始代码块。"""
        for i, block in enumerate(code_blocks):
            text = text.replace(self._CODE_BLOCK_MARKER % i, block)
        return text
    
    def _clean_markdown(self, text: str) -> Tuple[str, List[str]]:
        """清理Markdown格式 - 使用非贪婪匹配避免回溯"""
        changes = []
        
        # 移除粗体标记
        count = 0
        max_iter = 20
        while '**' in text and max_iter > 0:
            max_iter -= 1
            new_text = re.sub(r'\*\*([^*]+?)\*\*', r'\1', text)
            if new_text == text:
                break
            count += 1
            text = new_text
        if count > 0:
            changes.append(f"移除粗体标记 ({count}处)")
        
        # 移除标题标记
        headings = len(re.findall(r'^#{1,6}\s+', text, re.MULTILINE))
        if headings > 0:
            text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)
            changes.append(f"移除标题标记 ({headings}处)")
        
        # 移除代码块
        code_blocks = len(re.findall(r'```.*?```', text, re.DOTALL))
        if code_blocks > 0:
            text = re.sub(r'```.*?```', '', text, flags=re.DOTALL)
            changes.append(f"移除代码块 ({code_blocks}处)")
        
        # 移除行内代码
        inline_code = len(re.findall(r'`[^`]+?`', text))
        if inline_code > 0:
            text = re.sub(r'`([^`]+?)`', r'\1', text)
            changes.append(f"移除行内代码 ({inline_code}处)")
        
        # 移除分隔线
        hr_count = len(re.findall(r'^[-*_]{3,}\s*$', text, re.MULTILINE))
        if hr_count > 0:
            text = re.sub(r'^[-*_]{3,}\s*$', '', text, flags=re.MULTILINE)
            changes.append(f"移除分隔线 ({hr_count}处)")
        
        return text, changes
    
    def _clean_chatbot_artifacts(self, text: str) -> Tuple[str, List[str]]:
        """清理聊天机器人痕迹
        
        - 短词组（<4字）使用词边界正则避免子串误伤
        - 长词组（>=4字）使用简单子串匹配，自然语言中罕见误伤
        """
        changes = []
        
        for phrase in self._chatbot_endings:
            if not phrase or len(phrase) < 2:
                continue
            
            cjk_chars = sum(1 for c in phrase if '\u4e00' <= c <= '\u9fff')
            # Short phrases: use CJK boundary to avoid substring false positives
            if cjk_chars < 4:
                escaped = re.escape(phrase)
                pattern = re.compile(
                    f'(?<![\u4e00-\u9fff]){escaped}(?![\u4e00-\u9fff])'
                )
                if pattern.search(text):
                    text = pattern.sub('', text)
                    changes.append(f"移除chatbot痕迹: {phrase[:10]}...")
            else:
                # Long phrases: simple substring replacement, negligible false-positive risk
                if phrase in text:
                    text = text.replace(phrase, '')
                    changes.append(f"移除chatbot痕迹: {phrase[:10]}...")
        
        # Clean up double punctuation from removal
        text = re.sub(r'[，。]{2,}', '。', text)
        text = re.sub(r'[。]+', '。', text)
        
        return text, changes
    
    def _split_long_sentences(self, text: str) -> Tuple[str, int]:
        """拆分长句（激进模式）。
        
        优先在强语义边界（分号、转折连词：但/然而/不过/可是）处拆分；
        无强边界时才寻找自然停顿点（最后一个逗号），避免在第一个逗号处粗暴切断。
        """
        sentences = get_sentences(text)
        new_sentences = []
        split_count = 0
        
        for sent in sentences:
            if len(sent) <= 60:
                new_sentences.append(sent)
                continue
            
            # 优先级 1：强语义边界（分号 / 转折连词）
            strong_boundaries = [
                r'；',                                    # 中文分号
                r'(?<=[\u4e00-\u9fff])但(?![\u4e00-\u9fff])',  # 但（独立使用）
                r'(?<=[\u4e00-\u9fff])然而(?![\u4e00-\u9fff])',
                r'(?<=[\u4e00-\u9fff])不过(?![\u4e00-\u9fff])',
                r'(?<=[\u4e00-\u9fff])可是(?![\u4e00-\u9fff])',
            ]
            boundary_idx = -1
            for b_pattern in strong_boundaries:
                m = re.search(b_pattern, sent)
                if m:
                    boundary_idx = m.start()
                    break
            
            if boundary_idx > 0:
                part_a = sent[:boundary_idx].rstrip('，, ')
                part_b = sent[boundary_idx:].lstrip('，, ')
                if part_a and part_b:
                    new_sentences.append(part_a + '。')
                    new_sentences.append(part_b)
                    split_count += 1
                    continue
            
            # 优先级 2：找最后一个逗号（保持语义完整）
            commas = [m.start() for m in re.finditer(r'[，,]', sent)]
            if commas:
                # 选最后一个逗号且不超过前半部分 60 字
                last_valid = -1
                for idx in commas:
                    if idx < len(sent) - 3 and sent[:idx].count('') < 70:
                        last_valid = idx
                if last_valid > 10:  # 至少 10 字后才拆分
                    part_a = sent[:last_valid].rstrip('，, ')
                    part_b = sent[last_valid + 1:].lstrip('，, ')
                    if part_a and part_b:
                        new_sentences.append(part_a + '。')
                        new_sentences.append(part_b)
                        split_count += 1
                        continue
            
            new_sentences.append(sent)
        
        return ''.join(new_sentences), split_count
    
    def _post_process(self, text: str) -> str:
        """后处理：清理残留问题，优先读取 zh_rules.json 的 post_cleanup 配置"""
        cfg = self.rules.data.get('post_cleanup', {})
        
        # 修复标点问题：句号后不应有逗号
        if cfg.get('fix_broken_sentences', True):
            text = re.sub(r'。\s*[,，]+\s*', '。', text)
            text = re.sub(r'。\s*、\s*', '。', text)
        
        # 修复逗号后多余逗号
        if cfg.get('fix_duplicate_commas', True):
            text = re.sub(r'[,，]\s*[,，]+', '，', text)
        
        # 清理句首多余标点
        if cfg.get('remove_leading_comma', True):
            text = re.sub(r'([。\n])[,，、\s]+', r'\1', text)
            text = re.sub(r'^[,，、\s]+', '', text, flags=re.MULTILINE)
            text = re.sub(r'\n[,，、\s]+', '\n', text)
        
        # 清理句尾多余标点
        if cfg.get('fix_trailing_punctuation', True):
            text = re.sub(r'[,，、\s]+$', '', text, flags=re.MULTILINE)
            text = re.sub(r'[,，]+\s*([。！？])', r'\1', text)
        
        # 清理多余空格
        if cfg.get('remove_double_spaces', True):
            text = re.sub(r' {2,}', ' ', text)
            text = re.sub(r'\n{3,}', '\n\n', text)
        
        # 修复标点后多余空格
        if cfg.get('fix_space_after_punctuation', True):
            text = re.sub(r'([。！？，、；：])\s+', r'\1', text)
        
        # 清理残留问题
        if cfg.get('strip_orphan_punctuation', True):
            text = re.sub(r'\n[。！？，、；：]+\n', '\n', text)
            text = re.sub(r'^[。！？，、；：]+\s*$', '', text, flags=re.MULTILINE)
        
        if cfg.get('strip_residual_markdown', True):
            text = re.sub(r'\*{2,}', '', text)
            text = re.sub(r'[【\[\(][]\)]', '', text)
        
        # 修复特定短语问题
        if cfg.get('fix_common_phrases', True):
            text = re.sub(r'变成(当前|现在)', r'成为\1', text)
            text = re.sub(r'潜在安全危险', '安全隐患', text)
            text = re.sub(r'可能安全风险', '潜在安全风险', text)
        
        # 修复句式改写后的残留问题
        if cfg.get('fix_pattern_residue', True):
            text = re.sub(r'，此外还有', '，还有', text)
            text = re.sub(r'，此外并且', '，并且', text)
            text = re.sub(r'此外并且', '并且', text)
            text = re.sub(r'欠缺以', '不足以', text)
            text = re.sub(r'，同时也部分', '，部分', text)
        
        # 清理结尾残留
        if cfg.get('clean_trailing_clutter', True):
            text = re.sub(r'[。！？]\s*探讨\s*$', '。', text)
            text = re.sub(r'[。！？]\s*交流\s*$', '。', text)
        
        # 注入 human_voice_bank 活人感词库（概率性，不破坏原有结构）
        if cfg.get('inject_human_voice', True):
            voice_bank = self.rules.human_voice_bank
            if isinstance(voice_bank, dict):
                categories = voice_bank.get('categories', {})
                if isinstance(categories, dict):
                    all_phrases = []
                    for cat, phrases in categories.items():
                        if isinstance(phrases, list):
                            all_phrases.extend(phrases)
                    if all_phrases and len(get_sentences(text)) >= 5:
                        # Inject 1-2 phrases at paragraph start or after sentences
                        import random as _random
                        chosen = _random.sample(all_phrases, min(2, len(all_phrases)))
                        sentences = get_sentences(text)
                        if len(sentences) >= 4:
                            # Insert at a random sentence boundary (not first)
                            idx = _random.randint(1, len(sentences) - 2)
                            injection = chosen[0]
                            sentences[idx] = injection + '，' + sentences[idx]
                            text = ''.join(sentences)
        
        return text.strip()
