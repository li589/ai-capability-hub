#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Rule loading and merging for AI text detection and rewriting."""

import json
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

# 默认规则文件路径
DEFAULT_RULES_FILE = Path(__file__).parent.parent / "resources" / "zh_rules.json"
ARCHIVED_RULES_FILE = Path(__file__).parent.parent / "resources" / "zh_rules_archived.json"


class RuleSet:
    """Container for all detection and rewriting rules."""
    
    def __init__(self, rules_data: Dict[str, Any]):
        self.data = rules_data
    
    @property
    def replacements(self) -> Dict[str, str]:
        """替换规则：短语 -> 替换文本"""
        return self.data.get("replacements", {})
    
    @property
    def sentence_patterns(self) -> List[Dict[str, str]]:
        """句子级改写模式列表"""
        return self.data.get("sentence_patterns", [])
    
    @property
    def ai_jargon(self) -> List[str]:
        """AI 高频词汇列表"""
        return self.data.get("ai_jargon", [])
    
    @property
    def puffery_phrases(self) -> List[str]:
        """夸大性短语"""
        return self.data.get("puffery_phrases", [])
    
    @property
    def marketing_speak(self) -> List[str]:
        """宣传性语言"""
        return self.data.get("marketing_speak", [])
    
    @property
    def vague_attributions(self) -> List[str]:
        """模糊归因"""
        return self.data.get("vague_attributions", [])
    
    @property
    def hedging_phrases(self) -> List[str]:
        """模棱两可表达"""
        return self.data.get("hedging_phrases", [])
    
    @property
    def chatbot_artifacts(self) -> List[str]:
        """聊天机器人痕迹"""
        return self.data.get("chatbot_artifacts", [])
    
    @property
    def citation_bugs(self) -> List[str]:
        """引用痕迹"""
        return self.data.get("citation_bugs", [])
    
    @property
    def knowledge_cutoff(self) -> List[str]:
        """知识截止表述"""
        return self.data.get("knowledge_cutoff", [])
    
    @property
    def markdown_artifacts(self) -> List[str]:
        """Markdown 痕迹"""
        return self.data.get("markdown_artifacts", [])
    
    @property
    def negative_parallelisms(self) -> List[str]:
        """否定平行结构"""
        return self.data.get("negative_parallelisms", [])
    
    @property
    def superficial_verbs(self) -> List[str]:
        """肤浅动词"""
        return self.data.get("superficial_verbs", [])
    
    @property
    def filler_phrases(self) -> List[str]:
        """填充短语"""
        return self.data.get("filler_phrases", [])
    
    @property
    def rule_of_three_patterns(self) -> List[str]:
        """三点式结构"""
        return self.data.get("rule_of_three_patterns", [])
    
    @property
    def list_markers(self) -> List[str]:
        """列表标记"""
        return self.data.get("list_markers", [])
    
    @property
    def punctuation(self) -> Dict[str, int]:
        """标点阈值配置"""
        return self.data.get("punctuation", {})
    
    @property
    def rhetorical_patterns(self) -> List[str]:
        """反问句模式"""
        return self.data.get("rhetorical_patterns", [])
    
    @property
    def sentence_starters(self) -> List[str]:
        """句首连接词"""
        return self.data.get("sentence_starters", [])

    # ========== zh_rules_archived.json properties (21 keys) ==========

    @property
    def metaphor_cliche_ban(self) -> List[Dict[str, str]]:
        """比喻通感套路禁用模式列表"""
        return self.data.get("metaphor_cliche_ban", [])

    @property
    def english_translation_ban(self) -> List[Dict[str, str]]:
        """英式翻译腔禁用词列表"""
        return self.data.get("english_translation_ban", [])

    @property
    def banned_words_v2(self) -> Dict[str, Any]:
        """五类违禁词新版（cat1~cat5，每类含 entries + ai_performance + human_alt）"""
        return self.data.get("banned_words_v2", {})

    @property
    def punctuation_rules(self) -> Dict[str, Any]:
        """标点与格式净化规则（含禁令与例外）"""
        return self.data.get("punctuation_rules", {})

    @property
    def human_voice_bank(self) -> Dict[str, Any]:
        """活人感词库（按功能分类）"""
        return self.data.get("human_voice_bank", {})

    @property
    def connector_replacements(self) -> Dict[str, Any]:
        """连接词替换表（替代「此外/同时」等AI连接词）"""
        return self.data.get("connector_replacements", {})

    @property
    def false_sublimation(self) -> List[str]:
        """虚假升华句式列表"""
        return self.data.get("false_sublimation", [])

    @property
    def tier2_circuit_breaker(self) -> Dict[str, Any]:
        """二级熔断：单次可接受，连续出现或偷懒概括时必修"""
        return self.data.get("tier2_circuit_breaker", {})

    @property
    def rewrite_tier_ops(self) -> Dict[str, Any]:
        """分层改写操作清单（low_risk / medium_risk / high_risk）"""
        return self.data.get("rewrite_tier_ops", {})

    @property
    def final_qa_checklist(self) -> Dict[str, Any]:
        """终审质检清单（negative / positive 检查项）"""
        return self.data.get("final_qa_checklist", {})

    @property
    def noun_replacements(self) -> Dict[str, Any]:
        """名词替换表（规避黑话与套话）"""
        return self.data.get("noun_replacements", {})

    @property
    def structural_problems(self) -> Dict[str, Any]:
        """结构性问题清单（九维诊断框架）"""
        return self.data.get("structural_problems", {})

    @property
    def verb_replacements(self) -> Dict[str, Any]:
        """动词替换表（去除空洞抽象）"""
        return self.data.get("verb_replacements", {})

    @property
    def style_contrast_rules(self) -> Dict[str, Any]:
        """四组文体对比场景规则"""
        return self.data.get("style_contrast_rules", {})

    @property
    def human_injection_techniques(self) -> Dict[str, Any]:
        """人味注入四大技巧（主观性/口语化/节奏感/细节）"""
        return self.data.get("human_injection_techniques", {})

    @property
    def tier1_circuit_breaker(self) -> Dict[str, Any]:
        """一级熔断：出现即删改（零容忍）的正则模式"""
        return self.data.get("tier1_circuit_breaker", {})

    @property
    def ai_vs_human_framework(self) -> Dict[str, Any]:
        """AI味vs人类味结构化对比框架（四维度×7项）"""
        return self.data.get("ai_vs_human_framework", {})

    @property
    def syntax_structures(self) -> Dict[str, Any]:
        """句法结构库（节奏控制/逻辑强化/文采提升/特殊功能）"""
        return self.data.get("syntax_structures", {})

    @property
    def new_ai_flavor_2025(self) -> Dict[str, Any]:
        """2025-2026新型AI味补漏模式"""
        return self.data.get("new_ai_flavor_2025", {})

    @property
    def adjective_replacements(self) -> Dict[str, Any]:
        """形容词替换表（消除夸大与模糊）"""
        return self.data.get("adjective_replacements", {})

    @property
    def tier3_gray_zone(self) -> Dict[str, Any]:
        """三级灰区：语境敏感词，本身无罪罪在滥用"""
        return self.data.get("tier3_gray_zone", {})


@lru_cache(maxsize=4)
def load_rules(file_path: Union[str, Path] = None) -> RuleSet:
    """加载规则文件，返回 RuleSet 实例。
    
    加载流程：先加载主规则文件（zh_rules.json），再合并归档规则文件
    （zh_rules_archived.json）。两个文件的顶层 key 零重叠，合并后
    RuleSet.data 包含两者的全部规则。
    
    使用 LRU 缓存（maxsize=4），避免每次实例化都重新解析大 JSON。
    """
    path = Path(file_path) if file_path else DEFAULT_RULES_FILE
    if not path.exists():
        raise FileNotFoundError(f"Rules file not found: {path}")
    
    def _load_json(file_path: Path) -> dict:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    
    try:
        data = _load_json(path)
    except json.JSONDecodeError as e:
        raise json.JSONDecodeError(
            "[规则文件格式错误] JSON 解析失败：{}\n"
            "→ 建议：请检查规则文件是否为合法 JSON，可使用 jsonlint 或在线 JSON 验证工具检查，"
            "错误位置 {}".format(path, e.pos),
            e.doc, e.pos
        ) from e
    
    # 省略号统一：将 replacements 键中的 ……(U+2026) 替换为 ASCII ...，
    # 使其与 utils.clean_text() 的省略号正常化保持一致
    if "replacements" in data and isinstance(data["replacements"], dict):
        norm = {}
        for k, v in data["replacements"].items():
            nk = k.replace('\u2026', '...')
            norm[nk] = v
        data["replacements"] = norm
    
    # 合并归档规则集（与主规则集 key 零重叠，直接 update 即可）
    if path == DEFAULT_RULES_FILE and ARCHIVED_RULES_FILE.exists():
        try:
            archived = _load_json(ARCHIVED_RULES_FILE)
            overlap = set(data.keys()) & set(archived.keys())
            if overlap:
                # 如有重叠 key，归档规则覆盖主规则（未来若改名后出现重叠的预期行为）
                import warnings
                warnings.warn(
                    f"Archived rules overlap with main rules: {overlap}. "
                    f"Archived values will override."
                )
            data.update(archived)
        except json.JSONDecodeError as e:
            # 归档文件损坏不影响主规则加载，降级为仅主规则
            import warnings
            warnings.warn(
                f"Failed to load archived rules from {ARCHIVED_RULES_FILE}: {e}. "
                f"Continuing with main rules only."
            )
    
    return RuleSet(data)


# Whitelist of allowed keys for user-supplied rules (must match RuleSet properties)
ALLOWED_RULE_KEYS = {
    "replacements", "sentence_patterns", "ai_jargon", "puffery_phrases",
    "marketing_speak", "vague_attributions", "hedging_phrases", "chatbot_artifacts",
    "citation_bugs", "knowledge_cutoff", "markdown_artifacts", "negative_parallelisms",
    "superficial_verbs", "filler_phrases", "rule_of_three_patterns", "list_markers",
    "punctuation", "rhetorical_patterns", "sentence_starters", "post_cleanup",
    # zh_rules_archived.json keys (21 modules, zero overlap with main rules)
    "metaphor_cliche_ban", "english_translation_ban", "banned_words_v2",
    "punctuation_rules", "human_voice_bank", "connector_replacements",
    "false_sublimation", "tier2_circuit_breaker", "rewrite_tier_ops",
    "final_qa_checklist", "noun_replacements", "structural_problems",
    "verb_replacements", "style_contrast_rules", "human_injection_techniques",
    "tier1_circuit_breaker", "ai_vs_human_framework", "syntax_structures",
    "new_ai_flavor_2025", "adjective_replacements", "tier3_gray_zone",
}


def _filter_user_rules(user_rules: Dict[str, Any]) -> Dict[str, Any]:
    """Strip unknown/unauthorized keys from user-supplied rules to prevent injection."""
    rejected = [k for k in user_rules if k not in ALLOWED_RULE_KEYS]
    if rejected:
        import warnings
        warnings.warn(f"Ignored unauthorized rule keys: {rejected}")
    return {k: v for k, v in user_rules.items() if k in ALLOWED_RULE_KEYS}


def merge_rules(base: RuleSet, user_rules: Dict[str, Any]) -> RuleSet:
    """合并用户自定义规则到基础规则集。"""
    merged = base.data.copy()
    for key, value in user_rules.items():
        if key in merged:
            if isinstance(merged[key], list) and isinstance(value, list):
                if value == []:
                    merged[key] = []
                else:
                    merged[key].extend(value)
            elif isinstance(merged[key], dict) and isinstance(value, dict):
                merged[key].update(value)
            else:
                merged[key] = value
        else:
            merged[key] = value
    return RuleSet(merged)


def _validate_rules_path(file_path: Union[str, Path]) -> Path:
    """Validate that a user-supplied rules path is within the resources directory."""
    resolved = Path(file_path).resolve()
    resources_dir = (Path(__file__).parent.parent / "resources").resolve()
    try:
        resolved.relative_to(resources_dir)
    except ValueError:
        raise ValueError(
            "[路径安全限制] 自定义规则文件必须在 resources/ 目录内。\n"
            "→ 被拒绝的路径：{}\n"
            "→ 建议：请将自定义规则文件放入 resources/ 目录下，或使用默认规则。".format(file_path)
        )
    if not resolved.exists():
        raise FileNotFoundError(
            "[自定义规则文件缺失] 文件不存在：{}\n"
            "→ 建议：请检查文件路径是否正确，或移除 -r 参数使用默认规则。".format(resolved)
        )
    return resolved


def load_rules_with_user(user_rules_path: Optional[Union[str, Path]] = None) -> RuleSet:
    """加载默认规则，并可选地合并用户提供的规则文件。"""
    base = load_rules()
    if user_rules_path:
        safe_path = _validate_rules_path(user_rules_path)
        with open(safe_path, "r", encoding="utf-8") as f:
            user_data = json.load(f)
        # Only allow whitelisted keys in user rules
        user_data = _filter_user_rules(user_data)
        return merge_rules(base, user_data)
    return base
