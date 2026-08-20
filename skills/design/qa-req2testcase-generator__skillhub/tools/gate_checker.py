#!/usr/bin/env python3
"""
Gate 8项质量检查模块 — gate_checker.py
对 P6 生成的测试用例执行 8 项质量门检查（G1-G7），确保用例质量达标。

版本: 1.3.0 (V4.7.0: G1放宽+G1.5新增)
日期: 2026-05-20

Gate 检查位置：
  1. p6_save_batch: 每批次保存时执行 G1+G1.5+G2+G5 快速检查（代码正则）
  2. p7_code_check: 全部用例合并后执行 G1-G7 全量检查（含G1.5）

8项检查清单：
  G1   步骤具体性   [BLOCK]  正则+关键词匹配：必须包含具体路径+按钮+输入值
  G1.5 末位步骤可观测性 [BLOCK]  末位步骤必须引用可观测对象（替代验证/检查禁止词守卫）
  G2   期望断言性   [BLOCK]  禁止模式匹配：9种模糊表述
  G3   业务流程覆盖 [BLOCK]  A类≥3步+B类不冒烟
  G4   冒烟用例来源 [WARNING] 冒烟用例必须可追溯到A类
  G5   禁止模式检测 [BLOCK]  Jaccard相似度检测+5种违规模式
  G6   步骤原子性   [BLOCK]  合并操作检测
  G7   P5-P6可追溯性 [WARNING] 路径节点逐级验证

用法:
    from gate_checker import run_gate_checks, evaluate_gate

    results = run_gate_checks(cases, p5_test_points)
    evaluation = evaluate_gate(results)

    # 快速检查子集
    results = run_gate_checks(cases, p5_test_points, check_ids=["G1", "G2", "G5"])

无外部依赖，仅使用 Python 标准库。
"""

import re
import json
from collections import defaultdict
from typing import Any, Dict, List, Optional, Set, Tuple


# V4.6.14: 从统一配置导入禁句列表
try:
    from config.forbidden_words import (
        L1_ABSOLUTE, L1_PATTERNS, L2_CONTEXTUAL,
        G2_PATTERNS, has_context_signal, check_forbidden_words,
        P7_CHECK_WORDS,
    )
    _USING_UNIFIED_CONFIG = True
except ImportError:
    _USING_UNIFIED_CONFIG = False
    # 兼容：未安装配置时使用内联定义
    L1_PATTERNS = [
        r'正常加载\s*[，。；]?', r'验证成功\s*[，。；]?', r'符合业务规则\s*[，。；]?',
        r'符合预期\s*[，。；]?', r'功能正常\s*[，。；]?', r'数据正确\s*[，。；]?',
        r'操作成功\s*[，。；]?', r'展示完整\s*[，。；]?', r'流程正确\s*[，。；]?',
        r'结果正确\s*[，。；]?', r'处理正常\s*[，。；]?', r'结果符合\s*[，。；]?',
    ]
    def has_context_signal(text):
        import re
        if re.search(r'「[^」]+」', text): return True
        quantifiable = [r'\d+\s*条', r'\d+\s*次', r'\d+\s*个', r'\d+%', r'\d+\s*秒']
        for p in quantifiable:
            if re.search(p, text): return True
        strong_ui = [r'红色边框', r'绿色边框', r'页面跳转', r'变为', r'新增\d+条']
        for p in strong_ui:
            if re.search(p, text): return True
        return False


# ============================================================
# 版本与常量
# ============================================================

__version__ = "1.3.0"

# 检查级别
LEVEL_BLOCK = "BLOCK"      # 阻断级，不通过则整批驳回
LEVEL_WARNING = "WARNING"  # 警告级，需人工确认

# Gate 检查状态
STATUS_PASSED = "PASSED"
STATUS_FAILED = "FAILED"
STATUS_WARNING = "WARNING"
STATUS_ERROR = "ERROR"


# ============================================================
# V4.6.14: P6硬校验修复指导字典
# ============================================================
HARD_CHECK_GUIDANCE = {
    "steps_template": {
        "priority": 1,
        "message": "步骤过于模板化，缺乏具体操作。请从P5.description提取具体操作顺序，引用P1场景中的UI元素名称（如「点击『提交审批』按钮」而非「点击提交按钮」），加入具体测试数据值。",
    },
    "unique_ratio_low": {
        "priority": 2,
        "message": "步骤唯一率低于阈值，存在复制其他用例steps的情况。每个用例必须基于其source_test_point生成独特步骤，禁止复制粘贴。",
    },
    "expected_empty": {
        "priority": 0,  # 最高优先级
        "message": "期望结果为空。请检查是否输出嵌套结构（如case['fields']['expected_results']）。应输出扁平结构：case['expected_results']='1. xxx'。",
    },
    "forbidden_word": {
        "priority": 1,
        "message": "包含禁止词。请将模糊描述替换为具体验证点，如「弹出Toast提示'操作成功'」而非「操作成功」。如果禁止词出现在引号内UI文案中（如「操作成功」），请保留具体文案。",
    },
    "smoke_ratio_invalid": {
        "priority": 2,
        "message": "冒烟用例占比不符合规则（期望10%-20%，保底3条）。请确保P0+active+main_flow用例标注为is_smoke=true。",
    },
    "steps_expect_mismatch": {
        "priority": 1,
        "message": "步骤数与期望结果数偏差过大或期望覆盖率低于60%。请确保：1)步骤-期望偏差≤2；2)期望数≥步骤数×60%；3)P0用例步骤=期望必须1:1对应。",
    },
    "missing_required_field": {
        "priority": 0,
        "message": "缺少必填字段。请检查19列字段是否完整输出，特别注意：case_id、title、preconditions、steps、expected_results、priority、is_smoke不得为空。",
    },
    "p5_reference_missing": {
        "priority": 1,
        "message": "remarks中缺少P5引用标注。请在remarks中添加格式如：步骤引用:P5.description;规则引用:P5.related_rules[...]。",
    },
}

# 指导文本优先级排序（数字越小优先级越高）
GUIDANCE_PRIORITY = [
    "expected_empty",
    "missing_required_field",
    "forbidden_word",
    "steps_template",
    "steps_expect_mismatch",
    "p5_reference_missing",
    "smoke_ratio_invalid",
    "unique_ratio_low",
]


def get_guided_feedback(check_codes: list, max_return: int = 2) -> list:
    """
    V4.6.14: 根据校验错误码生成带修复指导的反馈。
    
    Args:
        check_codes: 校验错误码列表
        max_return: 最多返回的指导数量（避免token膨胀）
    
    Returns:
        list: 排序后的指导文本列表，每条带💡前缀
    """
    feedbacks = []
    for code in check_codes:
        if code in HARD_CHECK_GUIDANCE:
            guidance = HARD_CHECK_GUIDANCE[code]
            feedbacks.append((guidance["priority"], f"💡 {guidance['message']}"))
    
    # 按优先级排序
    feedbacks.sort(key=lambda x: x[0])
    
    # 返回前max_return条
    return [msg for _, msg in feedbacks[:max_return]]


# ============================================================
# 辅助函数
# ============================================================

def _get_case_field(case: dict, field: str, default: Any = "") -> Any:
    """
    安全获取用例字段值。
    支持多层级取值：
      1. 顶层字段（扁平结构）
      2. case["fields"][field]（嵌套结构，Agent常见输出格式）
      3. 别名映射

    Args:
        case: 用例 dict
        field: 字段名
        default: 默认值

    Returns:
        字段值，不存在则返回 default
    """
    if not isinstance(case, dict):
        return default

    # 1. 顶层字段（扁平结构）
    val = case.get(field)
    if val is not None:
        return val

    # 2. 嵌套 fields 结构（V4.6.12 Bugfix: Agent输出嵌套格式时读取）
    nested_fields = case.get("fields")
    if isinstance(nested_fields, dict):
        val = nested_fields.get(field)
        if val is not None:
            return val

    # 3. 常见别名映射
    alias_map = {
        "steps": ["test_steps", "step", "操作步骤"],
        "expected_results": ["expected_result", "expected", "期望结果", "预期结果"],
        "case_id": ["id", "test_case_id", "用例编号"],
        "title": ["name", "test_case_name", "用例名称"],
        "source_test_point": ["source_testpoint", "test_point_id", "来源测试点"],
        "is_smoke": ["smoke", "is_smoke_test", "冒烟"],
    }

    aliases = alias_map.get(field, [])
    for alias in aliases:
        val = case.get(alias)
        if val is not None:
            return val
        # 也检查嵌套fields的别名
        if isinstance(nested_fields, dict):
            val = nested_fields.get(alias)
            if val is not None:
                return val

    return default


def _is_smoke(value: Any) -> bool:
    """
    判断是否为冒烟用例标记。
    支持多种格式：bool / str("是"/"否"/"true"/"false") / int(1/0)
    """
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in ("是", "true", "yes", "1", "y")
    if isinstance(value, int):
        return value == 1
    return False


def _extract_step_lines(steps_text: str) -> list:
    """
    从步骤文本中提取编号步骤行。

    Args:
        steps_text: 步骤文本（可能包含编号前缀）

    Returns:
        list[str]: 去除编号前缀后的步骤内容列表
    """
    if not isinstance(steps_text, str) or not steps_text.strip():
        return []

    lines = []
    for line in steps_text.split('\n'):
        line = line.strip()
        if line and re.match(r'^\d+[\.\、）)]', line):
            # 去除编号前缀
            content = re.sub(r'^\d+[\.\、）)]\s*', '', line)
            lines.append(line)  # 保留原始行（含编号），用于报告
    # V4.15.51: 无编号步骤 fallback — 部分P6生成用例的步骤不带编号前缀,
    # 纯靠换行分隔,导致 _extract_step_lines 返回0 → G3误报步骤数不足。
    if not lines:
        lines = [l.strip() for l in steps_text.split('\n') if l.strip()]
    return lines


def _extract_step_contents(steps_text: str) -> list:
    """
    提取步骤内容（去除编号前缀）。
    """
    if not isinstance(steps_text, str) or not steps_text.strip():
        return []

    contents = []
    for line in steps_text.split('\n'):
        line = line.strip()
        if line and re.match(r'^\d+[\.\、）)]', line):
            content = re.sub(r'^\d+[\.\、）)]\s*', '', line)
            contents.append(content)
    # V4.15.51: 无编号步骤 fallback
    if not contents:
        contents = [l.strip() for l in steps_text.split('\n') if l.strip()]
    return contents


def _make_result(check_id: str, name: str, level: str,
                 status: str, detail: str, issues: list) -> dict:
    """构造标准 Gate 检查结果"""
    return {
        "check_id": check_id,
        "name": name,
        "level": level,
        "status": status,
        "detail": detail,
        "issues": issues,
    }


def _jaccard_similarity(set_a: set, set_b: set) -> float:
    """
    计算两个集合的 Jaccard 相似度。
    Jaccard(A, B) = |A ∩ B| / |A ∪ B|
    """
    if not set_a and not set_b:
        return 0.0
    union = set_a | set_b
    if not union:
        return 0.0
    return len(set_a & set_b) / len(union)


# ============================================================
# G1: 步骤具体性检查
# ============================================================


# V4.6.17: G1修复建议生成器
def _generate_g1_fix(line: str, valid_elements: set) -> str:
    """V4.7.0: 根据模糊步骤行生成具体修复建议（不再建议替换验证/确认/检查，这些是测试天然用语）"""
    fixes = []
    if '构造' in line:
        fixes.append('将「构造」替换为具体操作：在输入框中输入/选择下拉项')
    if '相关' in line:
        fixes.append('将「相关XX」替换为具体名称，如：点击「提交审批」按钮')
    if valid_elements:
        sample = list(valid_elements)[:3]
        fixes.append(f'可用的P5元素：{"、".join(sample)}')
    if not fixes:
        fixes.append('建议：增加引号包裹的具体按钮名或字段名，如：点击「XX」')
    return '；'.join(fixes)


# ============================================================
# V4.7.0: Gate 修复示例生成器 — 为 Gate 问题生成 before/after 示例
# ============================================================

def _build_fix_example(issue_type: str, line: str, case_id: str = "", extra: dict = None) -> dict:
    """
    为 Gate 问题生成带 before/after 对比的修复示例。

    Args:
        issue_type: 问题类型 ("vague" / "banned" / "duplicate_steps" / "non_atomic")
        line: 原始步骤/问题文本
        case_id: 用例ID（用于建议文字中引用）
        extra: 额外上下文（如相似度百分比、拆分建议等）

    Returns:
        dict: {"before": "...", "after": "...", "description": "..."}
    """
    if issue_type == "vague":
        # G1: 步骤模糊 → 给出具体化示例
        # V4.15.14: 使用 case-specific P5 元素（替代占位符）
        p5_elements = (extra or {}).get("p5_elements", [])
        if '查看' in line or '观察' in line:
            after = line.strip()[:60].replace('查看', '查看页面弹出提示框，确认').replace('观察', '查看页面弹出提示框，确认') + '显示预期结果'
            return {
                "before": line.strip()[:60],
                "after": after,
                "description": "将「查看/观察」替换为具体可观测对象：查看页面弹出提示框、查看列表新增记录数等",
                "priority": "P1"
            }
        if p5_elements:
            elem = p5_elements[0]
            return {
                "before": line.strip()[:60],
                "after": f"{line.strip()[:40]}「{elem}」",
                "description": f"在步骤中增加引号包裹的 UI 元素「{elem}」以具体化操作对象",
                "priority": "P1"
            }
        return {
            "before": line.strip()[:60],
            "after": "在步骤中增加「」引号包裹的具体 UI 元素名（按钮名/字段名），如：点击「查询」按钮",
            "description": "在步骤中增加引号包裹的具体按钮名或字段名",
            "priority": "P1"
        }

    elif issue_type == "banned":
        # G1: 禁止短语 → 给出具体替换
        return {
            "before": line.strip()[:60],
            "after": "进入首页→营销管理→协同分润",
            "description": "将模糊表达替换为具体菜单路径（格式：A→B→C）",
            "priority": "P1"
        }

    elif issue_type == "duplicate_steps":
        # G5: 步骤重复 → 给出差异化建议
        count = (extra or {}).get("count", 0)
        similarity = (extra or {}).get("similarity", "高")
        return {
            "before": f"{count}条用例步骤几乎完全相同",
            "after": f"每条用例在步骤1-2中嵌入不同的测试数据或前置条件，例如：\n  TC-001: '输入正常值100'\n  TC-002: '输入边界值0'\n  TC-003: '输入超限值150'",
            "description": f"步骤相似度{similarity}。建议为每条用例注入差异化测试数据/前置条件，使步骤至少有30%的字面差异",
            "priority": "P0"
        }

    elif issue_type == "non_atomic":
        # G6: 步骤非原子 → 给出拆分示例
        extra = extra or {}
        merged_action = extra.get("merged_action", "操作")
        return {
            "before": line.strip()[:80],
            "after": f"拆分为:\n(1) {line.strip()[:40].split('并')[0].strip()}\n(2) 等待结果/确认出现\n(3) {line.strip()[:40].split('并')[-1].strip() if '并' in line else '检查结果'}",
            "description": f"「{merged_action}」包含了多个操作。建议拆分为独立的原子步骤，每步只做一件事",
            "priority": "P1"
        }

    elif issue_type == "copy_title":
        # G5: 步骤复制title
        return {
            "before": "步骤文本与用例标题高度相似",
            "after": "在步骤中使用具体操作动词（点击/输入/选择/进入），而非照搬标题描述。例如：步骤='进入XX页面，点击YY按钮'，标题='验证XX功能'",
            "description": "步骤不是标题的复述，应是具体的操作序列",
            "priority": "P1"
        }

    elif issue_type == "last_step_vague":
        # G1.5: 末位步骤模糊
        return {
            "before": line.strip()[:60],
            "after": "查看列表新增1条记录，确认数据与输入一致",
            "description": "末位步骤需要包含具体的可观测对象（列表/弹窗/提示文案/数据指标），而非仅'查看''确认'",
            "priority": "P1"
        }

    # 默认
    return {"before": line[:80], "after": "[请根据业务场景补充具体描述]", "description": "建议增加具体操作对象或可观测描述", "priority": "P2"}


def _get_p5_context_hint(case: dict, p5_test_points: list) -> str:
    """从P5测试点提取该用例对应的上下文提示"""
    src = _get_case_field(case, "source_test_point", "") or case.get("source_test_point", "")
    if not src:
        return ""
    for tp in (p5_test_points or []):
        if tp.get("id", "") == src:
            desc = tp.get("description", "")
            precond = tp.get("precondition", "")
            page = tp.get("page_path", {})
            if isinstance(page, dict):
                page = page.get("full_path", "")
            return f"P5: {desc[:60]} [路径:{page[:40]}]" if page else f"P5: {desc[:60]}"
    return ""


# ============================================================
def gate_g1_step_concreteness(cases: list, p5_test_points: list) -> dict:
    """
    G1 步骤具体性 [BLOCK] (V4.6.17增强：菜单路径白名单、确认分级豁免、suggested_fix+p5_hint)

    检查标准：每条步骤必须包含以下之一：
      1. 具体页面路径（来自 P5 page_path 或 菜单导航格式A→B→C）
      2. 具体按钮/元素名称（引号内 或 来自 P5 ui_elements）
      3. 具体输入值（引号内 或 来自 P5 operations_chain.data_value）

    禁止模式：
      - "进入相关功能页面"
      - "进入相关页面"
      - "进入对应页面"
      - "验证XX功能"
      - "执行相关操作"
      - "检查系统响应"

    V4.6.17豁免：
      - 菜单路径格式（A→B→C 含至少2个→）→ 不判定为禁止
      - "确认"仅在无具体内容时禁止（如"确认操作"禁止，"确认输入框显示50"放行）
    """
    # 从 P5 提取合法的页面路径、按钮名、字段名（用于正面匹配）
    valid_page_paths = set()
    valid_element_names = set()
    valid_data_values = set()

    for tp in p5_test_points:
        # 页面路径
        pp = tp.get("page_path", {})
        if isinstance(pp, dict):
            full_path = pp.get("full_path", "")
            if full_path:
                valid_page_paths.add(full_path)
                for seg in full_path.split("→"):
                    seg = seg.strip()
                    if seg:
                        valid_page_paths.add(seg)
            for h in pp.get("hierarchy", []):
                valid_page_paths.add(h)
        elif isinstance(pp, str):
            valid_page_paths.add(pp)
            for seg in pp.split("→"):
                seg = seg.strip()
                if seg:
                    valid_page_paths.add(seg)

        # UI 元素名称
        ui = tp.get("ui_elements", {})
        if isinstance(ui, dict):
            for btn in ui.get("buttons", []):
                if isinstance(btn, dict) and btn.get("name"):
                    valid_element_names.add(btn["name"])
                elif isinstance(btn, str):
                    valid_element_names.add(btn)
            for inp in ui.get("inputs", []):
                if isinstance(inp, dict) and inp.get("name"):
                    valid_element_names.add(inp["name"])
                elif isinstance(inp, str):
                    valid_element_names.add(inp)
            for sel in ui.get("selectors", []):
                if isinstance(sel, dict) and sel.get("name"):
                    valid_element_names.add(sel["name"])
                elif isinstance(sel, str):
                    valid_element_names.add(sel)
            # V4.15.13: 增加 labels 收集（原遗漏，50个P5 labels 对G1不可见）
            for lbl in ui.get("labels", []):
                if isinstance(lbl, dict) and lbl.get("name"):
                    valid_element_names.add(lbl["name"])
                elif isinstance(lbl, str):
                    valid_element_names.add(lbl)

        # 操作数据值
        for op in tp.get("operations_chain", []):
            if isinstance(op, dict):
                if op.get("data_value"):
                    valid_data_values.add(str(op["data_value"]))
                if op.get("target_element"):
                    valid_element_names.add(op["target_element"])

    # V4.7.0: 从P5提取 field_checklist 作为"已具体引用"的白名单
    valid_field_names = set()
    for tp in p5_test_points:
        fcl = tp.get("field_checklist", [])
        if isinstance(fcl, list):
            for fn in fcl:
                if isinstance(fn, str) and fn.strip():
                    valid_field_names.add(fn.strip())

    # V4.7.0: 简化禁止模式 — 只禁止真正无意义的模糊短语（移除"验证XX功能""检查系统响应"）
    # "验证""确认""检查""观察"是测试场景天然用语，不再禁止
    BANNED_PATTERNS = [
        (r'进入相关功能页面', '进入具体菜单路径，如：进入首页→营销管理→协同分润'),
        (r'进入相关页面', '进入具体菜单路径，如：进入首页→营销管理→协同分润'),
        (r'进入对应页面', '进入具体菜单路径，如：进入首页→营销管理→协同分润'),
        (r'执行相关操作', '替换为具体操作动词+目标，如：点击「提交」按钮'),
    ]
    
    # V4.6.17: 确认分级豁免规则
    # "确认"禁止场景：无具体内容的确认（如"确认操作""确认结果"）
    # "确认"放行场景：有具体对象（如"确认主办单位默认回填""确认"提交审批"弹窗"）
    CONFIRM_BANNED_RE = re.compile(r'^\s*\d+[\.\)、]\s*确认\s*$')
    CONFIRM_ALLOWED_RE = re.compile(r'点击.*确认|确认.*["“”「」]|在.*确认|确认.*弹窗|确认.*输入|确认.*显示|'
                                     r'确认.*按钮|确认.*提示|确认.*回填|确认.*展示')
    # 确认+通用词（无具体业务内容）→ 不放行
    CONFIRM_GENERIC_WORDS = frozenset({'操作', '结果', '数据', '内容', '信息', '状态', '功能', '页面', '流程'})

    def _is_confirm_with_content(line):
        """确认后有实质性业务内容（非通用词）"""
        import re as _re
        if CONFIRM_ALLOWED_RE.search(line):
            return True
        m = _re.search(r'确认(.+)', line)
        if m:
            rest = m.group(1).strip()
            for gw in CONFIRM_GENERIC_WORDS:
                rest = rest.replace(gw, '')
            return len(rest) >= 3
        return False
    
    # V4.6.17: 菜单路径白名单（含至少2个→的导航路径不判定为模糊）
    MENU_PATH_RE = re.compile(r'进入\s*[\u4e00-\u9fa5a-zA-Z0-9]+(?:→|->)[\u4e00-\u9fa5a-zA-Z0-9]+(?:→|->)[\u4e00-\u9fa5a-zA-Z0-9]+')

    issues = []
    for c in cases:
        steps_text = str(_get_case_field(c, "steps", ""))
        step_lines = _extract_step_lines(steps_text)
        step_contents = _extract_step_contents(steps_text)

        # V4.7.0: 识别末位步骤（最后一条非空步骤），用于豁免
        last_idx = len(step_lines) - 1

        for idx, line in enumerate(step_lines):
            # V4.6.17: 菜单路径白名单检查
            if MENU_PATH_RE.search(line):
                continue

            # V4.6.17: 确认分级豁免
            if '确认' in line and _is_confirm_with_content(line):
                continue

            # V4.7.0: 末位步骤豁免（查看结果类步骤天然难以引用具体按钮）
            # 只要包含可观测对象（列表/页面/提示框/弹窗/toast/结果/显示/出现），视为有具体性
            if idx == last_idx and step_contents:
                last_step_content = step_contents[idx] if idx < len(step_contents) else line
                OBSERVABLE_PATTERNS = [
                    r'(?:页面|弹窗|对话框|提示框|toast|消息|通知)',
                    r'(?:列表|表格|数据|记录|行数|记录数)',
                    r'(?:显示|展示|出现|弹出|跳转|返回|可见)',
                    r'(?:查看|观察到|看到|检查|验证|确认)',
                ]
                if any(re.search(p, last_step_content) for p in OBSERVABLE_PATTERNS):
                    continue  # 末位步骤含可观测对象，豁免引号要求

            # 检查是否命中禁止模式
            is_banned = False
            for bp_pattern, suggested_fix in BANNED_PATTERNS:
                if re.search(bp_pattern, line):
                    is_banned = True
                    issues.append({
                        "case_id": _get_case_field(c, "case_id", "?"),
                        "line": line[:80],
                        "violation": f"禁止短语: {bp_pattern}",
                        "matched_rule": f"G1禁止模式列表",
                        "suggested_fix": suggested_fix,
                        "fix_example": _build_fix_example("banned", line, _get_case_field(c, "case_id", "?")),
                        "type": "banned",
                    })
                    break

            if is_banned:
                continue

            # 检查是否有具体内容（正面匹配）
            has_concrete = False

            # 检查引号内容
            quoted = re.findall(r'[「""\u201c]([^「""\u201d]{1,30})[」""\u201d]', line)
            if quoted:
                has_concrete = True

            # 检查路径格式 A→B 或 A->B
            if re.search(r'[\u4e00-\u9fa5a-zA-Z0-9]+(?:→|->)[\u4e00-\u9fa5a-zA-Z0-9]+', line):
                has_concrete = True

            # 检查是否引用了P5 field_checklist中的字段名（V4.7.0: 视为已具体引用）
            for fn in valid_field_names:
                if fn and len(fn) >= 2 and fn in line:
                    has_concrete = True
                    break

            # 检查是否引用了P5中的具体元素
            for elem in valid_element_names:
                if elem and elem in line:
                    has_concrete = True
                    break

            # 检查是否有具体输入值（V4.6.17: 放宽中文空格要求）
            if re.search(r'(?:输入|填写|录入|设置|填)', line):
                # 有输入动作，检查是否有值
                if quoted or re.search(r'(?:输入|填写|录入|设置|填).{1,30}', line):
                    has_concrete = True

            # V4.15.13: 数据搜索/定位步骤豁免（"找到X记录""查找X数据"是测试数据准备的自然描述）
            if re.search(r'(?:找到|查找|搜索|定位)\s*.{1,35}(?:记录|数据|信息|行|条目|详情|入口|草稿|数据|页面)', line):
                has_concrete = True

            # V4.15.13: 操作动词+UI对象通用模式（即使对象名不在P5中也视为具体）
            if re.search(r'(?:点击|选择|勾选|拖拽|双击)\s*.{0,8}(?:按钮|菜单|选项|标签|图标|链接|记录|数据|详情|入口|弹窗|页面|人员|实体|项目|条目)', line):
                has_concrete = True
            # V4.15.16: 选择/操作+业务实体豁免（"选择员工""选择客户""切换项目"）
            if re.search(r'(?:选择|切换|指定|分配)\s*.{0,8}(?:第\s*(?:\d+|[一二三四五六七八九十两]).{0,6}|[一二三四五六七八九十两]\s*(?:名|位|个|条)|[\u4e00-\u9fa5]{2,4}(?:部门|团队|人员|单位|角色|账号|用户|项目|模块|功能))', line):
                has_concrete = True
            # V4.15.16: 选择/删除+业务实体通用豁免（排除泛词）
            if re.search(r'(?:选择|删除)\s*(?:[\u4e00-\u9fa5]{2,5})(?:[A-Z]?\d*)?\s*$', line):
                # "选择员工""删除员工A" — 在列表中选/删项是通用UI操作
                # 排除泛词
                _generic = r'(?:操作|结果|数据|内容|信息|状态|功能|页面|流程|记录|模式|任务)$'
                if not re.search(_generic, line.strip()):
                    has_concrete = True
            # V4.15.13: 操作+数量+对象模式
            if re.search(r'(?:添加|删除|新增|移除|选择|修改|切换|勾选)\s*.{0,6}(?:\d+|[一二三四五两第])\s*.{0,10}(?:行|条|个|组|配置|人员|实体|记录|项目|条目)', line):
                has_concrete = True
            # V4.15.16: 添加/删除+任意对象豁免（无数量修饰也视为具体操作）
            if re.search(r'(?:添加|删除|移除)\s*.{0,15}?(?:人员|实体|记录|数据|项目|条目|配置|行|条)', line):
                has_concrete = True
            # V4.15.17: 移除/调整 at end-of-line（倒装句如"将XX从流程中移除"）
            if re.search(r'(?:移除|调整)\s*$', line.strip()):
                has_concrete = True

            # V4.15.16: 扩展操作动词豁免（补充/修正/保存/弹出/进入/审批/执行/下载/对比/留空/提示/刷新/不添加）
            # V4.15.17: 扩展（打开/清空/完善/不做/未做/修改/删除）
            if re.search(r'(?:补充|修正|保存|弹出|进入|审批|通过|执行|下载|对比|留空|置空|提示|刷新|不添加|未添加|提交|导出|模拟|同步|维护|关闭|查询|发送|找到|打开|清空|完善|不做|未做|修改|删除|观察|推送|调整)\s*.{0,30}', line):
                has_concrete = True

            # V4.15.16: 记录/查看/对比+任意对象容错（不再要求UI中介词）
            if re.search(r'(?:记录|查看|对比|观察)\s*.{1,30}(?:数据|数量|状态|结果|时间|信息|记录|字段|内容|顺序|名称|值|详情|类型|级别|方式|操作|日志|请求|页面|人员|项目|和|与|及|区域|变化|超时|异常|\d+)', line):
                has_concrete = True

            # V4.15.14: 异步操作等待豁免（导出/加载/刷新是合理的等待步骤）
            if re.search(r'等待.{0,25}?(?:完成|加载|响应|刷新|处理|结束|导出|下载|推送|显示|超时|同步|发送|返回|跳转|消失|重试)', line):
                has_concrete = True
            # V4.15.17: 时间等待豁免
            if re.search(r'等待\s*\d+\s*(?:分钟|秒|小时)', line):
                has_concrete = True
            # V4.15.17: 超时状态豁免（网络超时/会话超时等描述性短语）
            if re.search(r'(?:网络|会话|请求|连接|接口|响应|系统).{0,5}超时', line):
                has_concrete = True

            # V4.15.14: 数据记录/观察豁免（"记录列表总条数""观察系统提示"有具体对象）
            if re.search(r'(?:记录|观察|查看).{0,5}(?:列表|表格|页面|弹窗|提示|系统).{0,10}(?:条数|总条数|数据|内容|状态|提示|变化|耗时|标识|字段)', line):
                has_concrete = True

            # === V4.15.18: G1残余豁免扩展（基于集成测试20条样本模式）===
            # 1. 数值修改操作："将X从N改为M" / "将X改为N"
            if re.search(r'将.{0,20}(?:从|由)\s*\d+.*?(?:改|修改|调整|设为|设置为)\s*\d+', line):
                has_concrete = True
            # 2. 保持N不变模式
            if re.search(r'保持.{0,20}(?:不变|原值|原样)', line):
                has_concrete = True
            # 3. 重新选择+具体对象
            if re.search(r'重新(?:选择|选取|勾选|输入|填写).{0,20}(?:产品|员工|项目|客户|选项|内容|数据)', line):
                has_concrete = True
            # 4. 括号内补充说明（如"改为10（远小于单位比例60%）"）→ 有数值+具体操作
            if re.search(r'（.{1,30}）$', line) and re.search(r'\d+', line):
                has_concrete = True
            # 5. 核对/检查+字段列表
            if re.search(r'核对.{0,30}?(?:字段|值|比例|金额|数量|名称|编号)', line):
                has_concrete = True

            # V4.15.14: UI状态变更豁免（"默认显示tab""确认激活"是具体可观测状态）
            if re.search(r'(?:(?:默认|已)?显示|激活|选中|高亮|禁用|启用).{0,10}(?:tab|标签|按钮|字段|区域|选项|状态|菜单)', line):
                has_concrete = True

            # === V4.15.20: 剥离法最后防线（不枚举动词，检测剩余实质性内容）===
            if not has_concrete:
                _ALL_VERBS = r'(?:点击|查看|选择|输入|确认|打开|切换|勾选|拖拽|上传|下载|翻页|跳转|进入|返回|导航|搜索|筛选|过滤|定位|查找|新增|删除|修改|编辑|更新|保存|提交|保留|清空|置空|启用|停用|刷新|导入|导出|复制|粘贴|展开|折叠|添加|移除|调整|核对|填写|录入|发送|批量|取消|关闭|滚动|等待|导出|推送|同步|上传|获取)'
                _GENERIC_NOUNS = r'(?:页面|列表|表格|按钮|数据|内容|信息|选项|记录|结果|该条|该项|该行|对应|相关|的|每页|所有|全部|当前|已|未|不|可以|需要|是否|进行|开始|继续|完成|结束|其中|其他|其余|指定|特定)'
                _stripped = re.sub(_ALL_VERBS, '', line)
                _stripped = re.sub(_GENERIC_NOUNS, '', _stripped)
                _stripped = re.sub(r'[\d,.\s：:，,。；;、（）()「」\[\]【】《》]+', '', _stripped)
                if len(_stripped.strip()) >= 2:
                    has_concrete = True  # 剥离后仍有≥2个实质字符→有具体内容

            if not has_concrete:
                # V4.6.17: 确认有具体对象时放行
                if '确认' in line and _is_confirm_with_content(line):
                    has_concrete = True
            if not has_concrete:
                # V4.6.17: 输入类动作放宽（允许"输入XX"无引号版本）
                if re.search(r'(?:输入|填写|录入|设置|填)', line) and len(line.strip()) > 8:
                    has_concrete = True
            if not has_concrete:
                # 放行一些常见的安全步骤
                pass_keywords = [
                    "登录", "Token", "权限", "浏览器", "URL", "接口",
                    "登录系统", "打开浏览器", "使用账号", "以管理员",
                    "切换到", "账号", "密码",
                ]
                # V4.13.6: 业务场景白名单(非UI操作但合理的步骤, BUG-2修复:拆字面量/正则)
                G1_BIZ_LITERALS = [
                    "打开下载的Excel文件", "Excel文件-Sheet",
                    "OA系统", "CRM系统", "ERP系统",
                    "断开网络连接", "恢复网络连接",
                    "日终批次", "定时任务",
                    "分润申请记录", "审批记录",
                    "查看收到的邮件", "收到系统通知",
                ]
                G1_BIZ_REGEX = [
                    re.compile(r"等待.*执行完成"),
                    re.compile(r"模拟.*回调"),
                ]
                biz_ok = any(lit in line for lit in G1_BIZ_LITERALS) or any(rx.search(line) for rx in G1_BIZ_REGEX)
                if not biz_ok and not any(kw in line for kw in pass_keywords):
                    # V4.6.17: 生成针对性的修复建议
                    suggested_fix = _generate_g1_fix(line, valid_element_names)
                    p5_hint = _get_p5_context_hint(c, p5_test_points)
                    issues.append({
                        "case_id": _get_case_field(c, "case_id", "?"),
                        "line": line[:80],
                        "violation": "步骤缺乏具体操作对象（无引号内容、无路径、无P5元素引用）",
                        "suggested_fix": suggested_fix,
                        "fix_example": _build_fix_example("vague", line, _get_case_field(c, "case_id", "?"), {"p5_elements": list(valid_element_names)[:5]}),
                        "p5_hint": p5_hint,
                        "type": "vague",
                    })

    # 判定状态
    banned_count = sum(1 for i in issues if i.get("type") == "banned")
    vague_count = sum(1 for i in issues if i.get("type") == "vague")
    total_issues = len(issues)

    if banned_count > 0 or total_issues > max(len(cases) * 0.3, 3):
        status = STATUS_FAILED
    elif total_issues > 0:
        status = STATUS_WARNING
    else:
        status = STATUS_PASSED

    return _make_result(
        "G1", "步骤具体性", LEVEL_BLOCK,
        status,
        f"{total_issues} 条步骤不够具体（禁止:{banned_count} 模糊:{vague_count}）" if total_issues else "全部步骤包含具体操作对象",
        issues[:30],
    )


# ============================================================
# G1.5: 末位步骤可观测性（V4.7.0 新增）
# ============================================================

def gate_g1_5_last_step_observability(cases: list, p5_test_points: list) -> dict:
    """
    G1.5 末位步骤可观测性 [BLOCK]

    替代 G1 移除"验证/确认/检查/观察"禁止词后的质量守门机制。
    要求：每个用例的最后一步必须包含可观测的具体对象。

    可观测对象包括：
      - 具体UI元素：页面/弹窗/对话框/提示框/toast/消息/通知/列表/表格
      - 具体数据指标：行数/记录数/文案/状态变化/字段值
      - 引用格式：\u300c\u300d引号内容 或 P5字段名

    不通过的末位步骤示例：
      - "查看结果" — 无具体对象
      - "观察页面" — 无具体内容
      - "确认操作完成" — 通用词
    """
    issues = []

    for c in cases:
        steps_text = str(_get_case_field(c, "steps", ""))
        step_contents = _extract_step_contents(steps_text)
        if not step_contents:
            continue

        last_step = step_contents[-1]
        case_id = _get_case_field(c, "case_id", "?")

        # 1. 引号内容检测
        quoted = re.findall(r'[\u300c\u300d\"\"\u201c]([^\u300c\u300d\"\"\u201d]{1,30})[\u300d\u300d\"\"\u201d]', last_step)
        if quoted:
            continue  # 有引号内容，通过

        # 2. P5字段名匹配
        valid_fields = set()
        for tp in (p5_test_points or []):
            fcl = tp.get("field_checklist", [])
            if isinstance(fcl, list):
                for fn in fcl:
                    if isinstance(fn, str) and len(fn.strip()) >= 2:
                        valid_fields.add(fn.strip())
        if any(fn in last_step for fn in valid_fields):
            continue  # 引用了P5字段名，通过

        # 3. 可观测UI对象检测 (V4.15.13: 扩展"表单"+"是否有"模式)
        OBSERVABLE_UI = [
            r'(?:弹窗|对话框|提示框|toast|消息提示|通知|表单)',
            r'(?:页面|列表|表格|区域|模块).{0,10}(?:显示|展示|出现|弹出|跳转|是否有|包含|记录|数据)',
            r'(?:列表|表格).{0,5}(?:新增|删除|更新|刷新)',
            r'(?:分页|页码|Sheet|下拉框|复选框|单选框)',
            r'\u300c[^\u300d]+\u300d',
        ]
        if any(re.search(p, last_step) for p in OBSERVABLE_UI):
            continue

        # 4. 可观测数据指标检测
        OBSERVABLE_DATA = [
            r'(?:行数|记录数|条数|数量|金额|比例|状态).{0,8}(?:正确|一致|为|等于|显示|变化)',
            r'(?:红色|绿色|橙色|置灰|高亮|禁用|启用)',
            r'(?:提示|文案|文字|内容|信息)\s*(?:显示|为|正确)',
            # V4.7.1: 安全/边界/编码领域术语 — 本身就是具体可观测结果
            r'(?:转义|截断|过滤|编码|解码|序列化|反序列化|注入|XSS|SQL|CSRF)',
            r'(?:脱敏|掩码|遮蔽|隐藏)',
            r'(?:加密|解密|签名|验签|哈希)',
            r'(?:超时|重试|熔断|降级)',
            # V4.15.13: 数据对比/显示完整性豁免
            r'(?:对比|比对|比较|核对).{0,20}(?:一致|匹配|相同|正确|相符)',
            r'(?:字符|文字|字段|内容).{0,8}(?:完整|无乱码|正确|格式|方式|有无)',
            # V4.15.16: 时间相关可观测指标
            r'(?:时间戳|耗时|加载时间|渲染时间|响应时间)',
            # V4.15.16: 字段结构可观测指标
            r'(?:字段|列|表头).{0,8}(?:名称|顺序|排列|格式|类型)',
            # V4.15.39: 性能监控类可观测指标
            r'(?:CPU|内存|磁盘|网络).{0,8}(?:使用率|占用率|利用率).{0,5}(?:[>≥<≤]\s*\d+%|\d+%)',
            r'(?:QPS|TPS|吞吐量|并发数|连接数).{0,8}(?:[≤≥>]\s*\d+|达到|超过)',
            r'(?:错误率|失败率|成功率|可用率).{0,5}(?:[<>≤≥]\s*\d+%|\d+%)',
            r'(?:响应时间|延迟|耗时).{0,8}(?:[<>≤≥]\s*\d+\s*(?:ms|秒|s))',
            # V4.15.56: 异常场景状态描述词豁免（"网络中断"/"系统无响应"等为合理异常描述）
            r'(?:中断|无响应|异常|故障|宕机|不可用|挂起|卡死).{0,5}(?:$|。|，)',
            r'(?:系统|服务器|服务|接口|网络|数据库).{0,8}(?:异常|故障|中断|无响应|宕机|不可用)',
            r'(?:在|出现|发生|导致).{0,12}(?:异常|故障|中断|错误|失败)',
        ]
        if any(re.search(p, last_step) for p in OBSERVABLE_DATA):
            continue

        # 5. V4.7.2: 操作性末位步骤豁免 — 选择/点击/输入等操作本身改变界面状态，可观测
        # 使用 re.search (非 match)，因为步骤行可能有编号前缀
        OPERATIONAL_ACTIONS = r'(?:选择|点击|输入|填写|录入|勾选|拖拽|切换|删除|上传|下载|提交|保存|取消|审批|同意|拒绝|关闭|启用|停用|打开|搜索|筛选|导出|导入|查看|刷新|对比|记录|找到|修改|进入|尝试|检查|核对|校验|核实|验证|观察|模拟|确认|查询|调整|移除|复制|验算|准备|等待)'
        if re.search(OPERATIONAL_ACTIONS, last_step):
            continue

        # V4.13.6: G1.5条件白名单(BUG-3修复:break+标志位, 非continue)
        G15_WHITELIST = [
            (re.compile(r"查看.*(?:状态|结果).*[为是显示弹出一致正确相等相符保留]"), "末位有具体值"),
            (re.compile(r"确认.*(?:结果|状态).*[为是显示弹出一致正确相等相符保留]"), "末位有具体值"),
            (re.compile(r"查看.*列表.*\d+.*条"), "末位有具体数量"),
            # V4.15.16: 确认+数量限定豁免
            (re.compile(r"确认.*(?:只有|仅|仅剩|仅显示)\s*.{1,15}(?:保留|存在|显示|可见)"), "确认+数量限定"),
            # V4.15.16: 进入/查看+对象豁免
            (re.compile(r"(?:进入|打开|查看)\s*.{1,20}(?:页面|弹窗|列表|表单|详情|记录)"), "导航/查看操作"),
            # V4.15.17: 检查是否有值白名单
            (re.compile(r"检查.{1,20}(?:是否|有无|有没有).{1,10}(?:值|数据|内容|字段|记录)"), "检查是否有值"),
            # V4.15.39: 业务操作术语豁免
            (re.compile(r"(?:手工)?(?:补录|导入|导出|审核|审批|推送|同步|归档|备份).{1,20}"), "业务操作+对象"),
            # V4.15.41: 通用操作成功确认短语豁免
            (re.compile(r"(?:确认|验证|检查|查看).{0,10}(?:提交|保存|删除|创建|修改|更新|取消)(?:成功|完成|已生效|通过)"), "操作成功确认"),
            # V4.15.41: 数据操作结果豁免
            (re.compile(r"(?:提交|保存|删除|创建|修改|更新).{0,20}(?:成功|完成|已生效|通过)"), "数据操作结果"),
            # V4.15.50: 业务操作结果词豁免（提交成功/新增成功/校验通过/回填成功等）
            (re.compile(r"(?:提交|新增|保存|修改|删除|创建|更新|校验|验证|回填|同步|推送|导出|导入)(?:成功|完成|通过|已生效|正确|一致|完整|无异常)"), "业务操作结果"),
        ]
        g15_hit = False
        for pattern, _desc in G15_WHITELIST:
            if pattern.search(last_step):
                g15_hit = True
                break
        if g15_hit:
            continue

        # 6. 不通过：末位步骤缺乏可观测对象
        issues.append({
            "case_id": case_id,
            "last_step": last_step[:80],
            "violation": "末位步骤缺乏可观测的具体对象（无引号内容、无P5字段名、无可观测UI/数据指标）",
            "diagnostic": f"末位步骤「{last_step[:60]}」缺乏可观测对象。建议:(1)添加「」引号内的具体UI文案;(2)补充可量化数据(行数/金额/状态变化);(3)使用具体操作结果(如'确认提交成功'替代'确认成功')",
            "fix_example": _build_fix_example("last_step_vague", last_step, case_id),
        })

    total_issues = len(issues)
    if total_issues > max(len(cases) * 0.2, 2):
        status = STATUS_FAILED
    elif total_issues > 0:
        status = STATUS_WARNING
    else:
        status = STATUS_PASSED

    return _make_result(
        "G1.5", "末位步骤可观测性", LEVEL_BLOCK,
        status,
        f"{total_issues} 条用例末位步骤缺乏可观测对象" if total_issues else "所有用例末位步骤包含可观测对象",
        issues[:20],
    )


# ============================================================
# G2: 期望断言性检查
# ============================================================

def _has_specificity_signal(text: str) -> bool:
    """
    检测文本中是否包含具体性信号（V4.6.11改进）。

    有以下任一信号即返回True（表示虽然含有禁止词，但内容足够具体）：
    1. 「」引号包裹的具体文案
    2. 可量化数字词组（如"新增8条"、"显示3条"、"共50%"、"耗时2秒"）
    3. 强UI信号（颜色+元素组合，如"红色边框"、"绿色提示框"）
       或2个以上弱UI信号（如"弹窗"+"提交"）
    """
    # Signal 1: 「」引号内有内容
    if re.search(r'「[^」]+」', text):
        return True

    # Signal 2: 可量化数字词组（数字+量词/单位）
    quantifiable_patterns = [
        r'\d+\s*条',        # 新增8条、显示3条、共10条
        r'\d+\s*次',        # 共5次、点击3次
        r'\d+\s*个',        # 共4个、新增2个
        r'\d+%%',             # 50%、80%
        r'\d+\s*秒',        # 耗时3秒
        r'\d+\s*分钟',       # 耗时5分钟
        r'\d+\s*px',        # 100px
        r'共\s*\d+',        # 共10条、共200元
        r'变为\s*\d+',      # 变为8条
        r'增加\s*\d+',      # 增加3条
        r'减少\s*\d+',      # 减少2条
    ]
    for pat in quantifiable_patterns:
        if re.search(pat, text):
            return True

    # Signal 3: 强UI信号（颜色+元素）→ 单个即算
    strong_ui_patterns = [
        r'红色边框', r'绿色边框', r'蓝色边框',
        r'红色提示', r'绿色提示', r'橙色警告',
        r'红色图标', r'绿色图标',
        r'弹窗关闭', r'弹窗打开',
        r'输入框禁用', r'输入框启用',
        r'按钮置灰', r'按钮高亮',
        r'页面跳转',
    ]
    for pat in strong_ui_patterns:
        if re.search(pat, text):
            return True

    # Signal 3b: 弱UI信号 → 需要2个以上才能算1个信号
    weak_ui_elements = [
        '弹窗', '输入框', '按钮', '下拉框', '复选框', '单选框',
        '列表', '表格', '菜单', '导航', '标签页', '对话框',
        '提示', '警告', '消息', '表单', '字段', '页面', '区域',
    ]
    weak_count = sum(1 for el in weak_ui_elements if el in text)
    if weak_count >= 2:
        return True

    return False


def gate_g2_expected_assertiveness(cases: list) -> dict:
    """
    G2 期望断言性 [BLOCK]

    检查标准：每条期望结果不得包含以下禁止模式（9种模糊表述）。
    但若命中禁止词的同时包含具体性信号（有「」引号/可量化数字/强UI信号），则不算模糊。

    禁止模式（9种模糊表述）：
      1. "正常加载"
      2. "验证成功"
      3. "符合业务规则"
      4. "符合预期"
      5. "功能正常"
      6. "数据正确"
      7. "操作成功"
      8. "展示完整"
      9. "流程正确"

    具体性信号（命中禁止词时有以下任一信号即放过）：
      - 信号1：「」引号内有文案（如「操作成功」）
      - 信号2：可量化数字词组（如"新增8条"、"共50%"、"耗时3秒"）
      - 信号3：强UI信号（颜色+元素，如"红色边框"、"绿色提示框"）
        或2个以上弱UI信号（如"弹窗"+"提交"）
    """
    # V4.6.14: 从统一配置导入禁止模式（L1正则模式）
    # BANNED = L1_PATTERNS  # 直接用配置中的列表

    # V4.15.5: 【待具化】占位符BLOCK检测 — 任何含占位符的期望结果直接BLOCK
    placeholder_blocked = []
    for c in cases:
        exp = str(_get_case_field(c, "expected_results", ""))
        if "【待具化" in exp:
            placeholder_blocked.append({
                "case_id": _get_case_field(c, "case_id", "?"),
                "line": "(含占位符)",
                "pattern": "【待具化】占位符",
                "hint": "期望结果含【待具化】占位符，用例不完整，请用具体的可观测行为描述替换",
            })
    if placeholder_blocked:
        return _make_result(
            "G2", "期望断言性-占位符", LEVEL_BLOCK,
            STATUS_FAILED,
            f"{len(placeholder_blocked)}/{len(cases)} 条期望结果含【待具化】占位符(用例不完整)",
            placeholder_blocked,
        )

    # V4.15.8: 弱验证词检测
    import re as _wv_re
    weak_issues = []
    for c in cases:
        exp = str(_get_case_field(c, "expected_results", ""))
        cid = _get_case_field(c, "case_id", "?")
        if "一致" in exp:
            # V4.15.18: 扩展has_explicit正则（与.*一致|和.*相同|.*与.*值相等）
            has_explicit = bool(_wv_re.search(r'显示为.*,.*显示为|字段.*=.*字段|等于|与.*一致|和.*相同|.*与.*值相等', exp))
            if not has_explicit:
                weak_issues.append({"case_id": cid, "line": "(含'一致')", "pattern": "弱验证词-一致", "hint": "需明确指代对象，如'字段A值与字段B值相等'"})
        if "无异常" in exp:
            has_explicit = bool(_wv_re.search(r'不显示|不提示|无.*弹窗|无.*报错', exp))
            if not has_explicit:
                weak_issues.append({"case_id": cid, "line": "(含'无异常')", "pattern": "弱验证词-无异常", "hint": "需具体化，如'页面无报错弹窗'"})
    if weak_issues:
        # V4.15.8: 不提前return，与后续L1检查合并（防短路跳过禁止词检测）
        pass

    issues = []
    for c in cases:
        expected_text = str(_get_case_field(c, "expected_results", ""))
        if not expected_text.strip():
            # V4.6.12改进：加调试信息，帮助定位是格式问题还是真的为空
            available_fields = [k for k in c.keys() if k not in ("id",)]
            issues.append({
                "case_id": _get_case_field(c, "case_id", "?"),
                "line": "(空)",
                "pattern": "期望结果为空",
                "diagnosis": f"实际可用字段: {available_fields}",
                "hint": "如果列表中无expected_results字段，可能是嵌套在fields中或字段名错误",
            })
            continue

        lines = [l.strip() for l in expected_text.split('\n')
                 if l.strip() and re.match(r'^\d+[\.\、）)]', l.strip())]

        # 如果没有编号格式，检查整段
        if not lines:
            lines = [l.strip() for l in expected_text.split('\n') if l.strip()]

        for line in lines:
            for pattern in L1_PATTERNS:
                if re.search(pattern, line):
                    # V4.7.1改进：有禁止词但行内或整段有具体性信号 → 不报
                    if _has_specificity_signal(line) or _has_specificity_signal(expected_text):
                        break  # 有具体性，不算模糊，跳过
                    issues.append({
                        "case_id": _get_case_field(c, "case_id", "?"),
                        "line": line[:80],
                        "pattern": re.sub(r'\\s\*\[，。；\]\?', '', pattern),
                    })
                    break  # 每行只报一次

    # V4.15.8: 合并弱验证词到主issues（在return前，不短路）
    if weak_issues:
        issues.extend(weak_issues)

    ratio = len(issues) / max(len(cases), 1)

    if ratio > 0.20:
        status = STATUS_FAILED
    elif issues:
        status = STATUS_WARNING
    else:
        status = STATUS_PASSED

    return _make_result(
        "G2", "期望断言性", LEVEL_BLOCK,
        status,
        f"{len(issues)}/{len(cases)} 条期望结果含模糊表述({ratio:.1%})" if issues else "全部期望结果包含具体断言",
        issues[:30],
    )


# ============================================================
# G3: 业务流程覆盖检查
# ============================================================

def gate_g3_business_flow_coverage(cases: list, p5_test_points: list) -> dict:
    """
    G3 业务流程覆盖 [BLOCK]

    检查标准：
      1. 每个功能至少有 1 个 A 类测试点（category = main_flow/branch/integration）
      2. 分级步骤数门槛(FIX⑤ V5.x):
         - A类(main_flow/branch/integration/permission/state_migration): ≥2步→PASS, ≤1步→BLOCK
         - B类(field_validation/boundary): ≥1步→PASS, 0步→BLOCK
         - ≤1步问题属BLOCK级,不可被 --force 绕过
      3. B 类（field_validation/boundary）不能标记为冒烟用例
    """
    import re as _g3_re
    issues = []

    # === V4.15.18: 短ID→完整ID容错映射（支持TP-NNN和ETP-N变体）===
    _short_to_full_map = {}
    for _tp in p5_test_points:
        _full_id = _tp.get('id', '') if isinstance(_tp, dict) else ''
        for _m in _g3_re.finditer(r'(?:TP|ETP)-(?:\d{1,})$', _full_id):
            _short_to_full_map[_m.group(0)] = _full_id

    # 按 source_test_point 分组
    tp_cases = defaultdict(list)
    for c in cases:
        src = str(_get_case_field(c, "source_test_point", "") or c.get("source_test_point", ""))
        # V4.15.18: 短ID容错→使用完整ID作为分组键
        _key = src if src in {_tp.get('id','') for _tp in p5_test_points if isinstance(_tp, dict)} else _short_to_full_map.get(src, src)
        tp_cases[_key].append(c)

    # 构建 P5 测试点索引
    p5_map = {tp.get("id", ""): tp for tp in p5_test_points if isinstance(tp, dict)}

    # A类分类
    A_CLASS_CATEGORIES = frozenset({
        "main_flow", "branch", "integration", "permission", "state_migration",
    })
    B_CLASS_CATEGORIES = frozenset({
        "field_validation", "boundary",
    })

    # 检查1：每个 P5 active 测试点至少有 1 条用例
    # === V4.15.28: 构建索引→完整ID映射（case_id回退V2用）===
    _g3_index_to_full = {}
    for _g3_idx, _g3_tp in enumerate(p5_test_points):
        if isinstance(_g3_tp, dict) and _g3_tp.get('id'):
            _g3_index_to_full[_g3_idx] = _g3_tp['id']

    for tp in p5_test_points:
        if not isinstance(tp, dict):
            continue
        if tp.get("status", "active") != "active":
            continue
        tp_id = tp.get("id", "")
        if tp_id and tp_id not in tp_cases:
            # === V4.15.18-G3 fallback: case_id反推（处理source_test_point与tp_file不一致）===
            _g3_fallback_found = False
            _g3_suffix = _g3_re.search(r'(?:TP|ETP)-(?:\d{1,})$', tp_id)
            if _g3_suffix:
                _g3_suffix_str = _g3_suffix.group(0)
                for c in cases:
                    _g3_cid = str(_get_case_field(c, "case_id", ""))
                    if _g3_suffix_str in _g3_cid:
                        tp_cases.setdefault(tp_id, []).append(c)
                        _g3_fallback_found = True
            # === V4.15.28-G3: 回退V2 — case_id含数字索引但非TP编号(LLM误用tp_index) ===
            if not _g3_fallback_found:
                for c in cases:
                    _g3_cid = str(_get_case_field(c, "case_id", ""))
                    # 从case_id提取纯数字索引(如 "REQ-...-075-TC-001" → 75)
                    _g3_num_m = _g3_re.search(r'[_-](\d{2,4})(?=-TC-)', _g3_cid)
                    if _g3_num_m:
                        _g3_num = int(_g3_num_m.group(1))
                        _g3_full = _g3_index_to_full.get(_g3_num, '')
                        if _g3_full and _g3_full == tp_id:
                            tp_cases.setdefault(tp_id, []).append(c)
                            _g3_fallback_found = True
            if not _g3_fallback_found:
                issues.append({
                    "test_point": tp_id,
                    "issue": "P5 active 测试点未被 P6 覆盖",
                    "type": "coverage_gap",
                    # V4.15.18: 标记是否为格式不匹配（短ID→完整ID可映射=格式问题）
                    "source_matched": any(
                        str(c.get("source_test_point", "")).strip() in _short_to_full_map
                        for c in cases if _short_to_full_map.get(
                            str(c.get("source_test_point", "")).strip(), '') == tp_id
                    )
                })

    # 检查2：分级步骤数门槛 (FIX⑥ V5.x)
    #   A类(main_flow/branch/integration/permission/state_migration): ≥2步→PASS, ≤1步→BLOCK
    #   B类(field_validation/boundary): ≥1步→PASS, 0步→BLOCK
    #   ≤1步问题属BLOCK级,不可被 --force 绕过(由P7 BLOCK数据层守卫保证)
    for c in cases:
        src = str(_get_case_field(c, "source_test_point", "") or c.get("source_test_point", ""))
        # V4.15.18: 短ID容错（L1102第二处）
        _matched_src = src if src in p5_map else _short_to_full_map.get(src, src)
        tp = p5_map.get(_matched_src, {})
        category = (tp.get("category", "") or "").lower() if isinstance(tp, dict) else ""

        steps_text = str(_get_case_field(c, "steps", ""))
        step_lines = _extract_step_lines(steps_text)
        n_steps = len(step_lines)

        if category in A_CLASS_CATEGORIES:
            if n_steps <= 1:
                issues.append({
                    "case_id": _get_case_field(c, "case_id", "?"),
                    "issue": f"A类用例步骤数 {n_steps} ≤1（category={category}，要求≥2步）",
                    "type": "a_class_step_short",
                })
        elif category in B_CLASS_CATEGORIES:
            if n_steps == 0:
                issues.append({
                    "case_id": _get_case_field(c, "case_id", "?"),
                    "issue": f"B类用例步骤数 0（category={category}，要求≥1步）",
                    "type": "b_class_step_empty",
                })

    # 检查3：B类不能标记为冒烟
    for c in cases:
        is_smoke = _is_smoke(_get_case_field(c, "is_smoke", ""))
        if not is_smoke:
            continue

        src = str(_get_case_field(c, "source_test_point", "") or c.get("source_test_point", ""))
        tp = p5_map.get(src, {})
        category = (tp.get("category", "") or "").lower() if isinstance(tp, dict) else ""

        if category in B_CLASS_CATEGORIES:
            issues.append({
                "case_id": _get_case_field(c, "case_id", "?"),
                "issue": f"B类({category})测试点不应标记为冒烟用例",
                "type": "b_class_smoke",
            })

    return _make_result(
        "G3", "业务流程覆盖", LEVEL_BLOCK,
        STATUS_FAILED if issues else STATUS_PASSED,
        f"{len(issues)} 项覆盖问题" if issues else "业务流程覆盖完整",
        issues[:20],
    )


# ============================================================
# G4: 冒烟用例来源检查
# ============================================================

def calculate_smoke_count(total_count: int) -> tuple:
    """
    V4.7.0: 冒烟用例数量计算 — 统一为比例标准 10%-20%。
    最小保底 3 条（避免小模块冒烟为 0）。

    Returns:
        tuple: (min_expected, max_expected)
    """
    if total_count == 0:
        return (0, 0)
    smoke_min = max(3, round(total_count * 0.10))
    smoke_max = round(total_count * 0.20)
    return (smoke_min, smoke_max)


def gate_g4_smoke_source(cases: list, p5_test_points: list) -> dict:
    """
    G4 冒烟用例来源 [WARNING]

    检查标准：
      1. 冒烟用例必须可追溯到 A 类（main_flow/branch/integration/permission）
      2. 冒烟用例的 priority 应为 P0
      3. 冒烟用例的步骤必须包含具体路径（G1规则）
      4. 冒烟用例数量必须符合线性插值公式（V4.6.14新增）
    """
    A_CLASS_CATEGORIES = frozenset({
        "main_flow", "branch", "integration", "permission", "state_migration",
    })

    p5_map = {tp.get("id", ""): tp for tp in p5_test_points if isinstance(tp, dict)}

    # === V4.15.18: 短ID→完整ID容错映射 ===
    import re as _g4_re
    _g4_short_to_full = {}
    for _tp in p5_test_points:
        _fid = _tp.get('id', '') if isinstance(_tp, dict) else ''
        for _m in _g4_re.finditer(r'(?:TP|ETP)-(?:\d{1,})$', _fid):
            _g4_short_to_full[_m.group(0)] = _fid

    issues = []
    smoke_cases = [c for c in cases if _is_smoke(_get_case_field(c, "is_smoke", ""))]

    for c in smoke_cases:
        case_id = _get_case_field(c, "case_id", "?")
        src = str(_get_case_field(c, "source_test_point", "") or c.get("source_test_point", ""))
        # V4.15.18: 短ID容错 + case_id反推fallback
        _g4_src = src if src in p5_map else _g4_short_to_full.get(src, src)
        tp = p5_map.get(_g4_src, {})
        if not tp:
            _g4_cid = str(_get_case_field(c, "case_id", ""))
            _g4_m = _g4_re.search(r'TP-(\d{3})', _g4_cid)
            if _g4_m:
                _g4_tp_idx = int(_g4_m.group(1))
                for _g4_tp_id, _g4_tp_data in p5_map.items():
                    if _g4_tp_id.endswith(f"-TP-{_g4_tp_idx:03d}"):
                        tp = _g4_tp_data
                        break
        category = (tp.get("category", "") or "").lower() if isinstance(tp, dict) else ""
        priority = str(_get_case_field(c, "priority", ""))

        # 检查1：冒烟必须来自A类
        if category not in A_CLASS_CATEGORIES:
            issues.append({
                "case_id": case_id,
                "issue": f"冒烟用例的P5分类为「{category}」，非A类（main_flow/branch/integration等）",
                "type": "non_a_class_smoke",
            })

        # 检查2：冒烟应为P0或P1
        if priority and priority not in ("P0", "P1"):
            issues.append({
                "case_id": case_id,
                "issue": f"冒烟用例优先级为「{priority}」，建议为P0或P1",
                "type": "smoke_not_p0_p1",
            })

    # V4.7.0: 冒烟数量校验（统一为10%-20%比例标准）
    active_cases = [c for c in cases if _get_case_field(c, "status", "") != "disabled"]
    total_count = len(active_cases)
    smoke_cases = [c for c in active_cases if _is_smoke(_get_case_field(c, "is_smoke", ""))]
    actual_smoke = len(smoke_cases)
    expected_min, expected_max = calculate_smoke_count(total_count)

    if total_count > 0 and (actual_smoke < expected_min or actual_smoke > expected_max):
        issues.append({
            "case_id": "_smoke_ratio_",
            "issue": f"冒烟用例数量{actual_smoke}不在期望范围{expected_min}-{expected_max}（总用例{total_count}条，期望比例10%-20%，保底3条）",
            "type": "smoke_ratio_invalid",
        })

    return _make_result(
        "G4", "冒烟用例来源", LEVEL_WARNING,
        STATUS_WARNING if issues else STATUS_PASSED,
        f"{len(issues)} 项冒烟来源问题" if issues else "冒烟用例均可追溯到A类",
        issues[:20],
    )


# ============================================================
# G5: 禁止模式检测
# ============================================================

def gate_g5_banned_patterns(cases: list) -> dict:
    """
    G5 禁止模式检测 [WARNING]

    检测以下 5 种禁止模式：
      ① 步骤直接复制测试点 title（Jaccard相似度 > 0.5）
      ② "进入相关功能页面"
      ③ "验证XX功能" 作为步骤开头
      ④ "如有""若无""假设" 等条件性词汇
      ⑤ 3条以上不同用例步骤完全相同
    """
    issues = []

    # 收集所有用例的步骤文本（用于重复检测⑤）
    all_steps_text = {}

    for c in cases:
        case_id = _get_case_field(c, "case_id", "?")
        steps_text = str(_get_case_field(c, "steps", ""))
        title = str(_get_case_field(c, "title", ""))

        # ① 步骤与title相似度检测（Jaccard相似度）
        step_words = set(re.findall(r'[\u4e00-\u9fa5]{2,}', steps_text))
        title_words = set(re.findall(r'[\u4e00-\u9fa5]{2,}', title))
        if step_words and title_words and len(step_words) > 3:
            jaccard = _jaccard_similarity(step_words, title_words)
            if jaccard > 0.5:
                issues.append({
                    "case_id": case_id,
                    "violation": f"步骤与title高度相似(Jaccard={jaccard:.2f})",
                    "fix_example": _build_fix_example("copy_title", steps_text, case_id, {"similarity": f"{jaccard:.0%}"}),
                    "type": "copy_title",
                })

        step_lines = _extract_step_lines(steps_text)

        for line in step_lines:
            # ② 禁止模式："进入相关功能页面"
            if re.search(r'进入相关(?:功能)?页面', line):
                issues.append({
                    "case_id": case_id,
                    "line": line[:80],
                    "violation": "禁止模式：进入相关功能页面",
                    "type": "banned_phrase",
                })

            # ③ 禁止模式："验证XX功能" 开头
            content = re.sub(r'^\d+[\.\、）)]\s*', '', line)
            if re.match(r'验证.{1,6}功能', content):
                issues.append({
                    "case_id": case_id,
                    "line": line[:80],
                    "violation": "禁止模式：验证XX功能",
                    "type": "banned_phrase",
                })

            # ④ 条件性词汇
            if re.search(r'如有|若无|假设|假如|如果.{1,6}则', line):
                issues.append({
                    "case_id": case_id,
                    "line": line[:80],
                    "violation": "禁止模式：条件性词汇",
                    "type": "conditional",
                })

        # 记录用例步骤（用于 ⑤ 重复检测）
        normalized_steps = "\n".join(step_lines)
        if normalized_steps.strip():
            all_steps_text.setdefault(normalized_steps, []).append(case_id)

    # ⑤ V4.7.1: 数据值归一化豁免 — 步骤结构相同但数据不同时豁免
    # 仅当 ≥5 条归一化后仍完全相同时才报违规
    def _normalize_step_data(steps_text: str) -> str:
        """将步骤中的数据值替换为占位符，用于结构相似性比较"""
        import re as _re
        t = steps_text
        # 替换引号内容:「XX」→ 「{VALUE}」
        t = _re.sub(r'「[^」]{1,30}」', '「{VALUE}」', t)
        # 替换数字（不含步骤编号）: 150 → {NUM}
        t = _re.sub(r'(?<![#\d])\d+(?![\d\-])', '{NUM}', t)
        # 替换特定值: 测试客户A / 特殊字符<script>等 → {VALUE}
        t = _re.sub(r'测试[客户|数据|值|用户][\w]*', '{VALUE}', t)
        return t

    # 收集归一化后的步骤用于 ⑤ 检测
    normalized_steps_map = {}  # normalized_steps → [(case_id, original_steps)]
    for c in cases:
        cid = _get_case_field(c, "case_id", "?")
        steps_text = str(_get_case_field(c, "steps", ""))
        step_lines = _extract_step_lines(steps_text)
        normalized = "\n".join(step_lines)
        norm_key = _normalize_step_data(normalized)
        if norm_key.strip():
            normalized_steps_map.setdefault(norm_key, []).append((cid, normalized))

    for norm_key, entries in normalized_steps_map.items():
        if len(entries) < 3:
            continue  # V4.15.37: 阈值5→3（<3条视为结构相似）
        
        # V4.15.39: 按source_tp分组，仅同TP内≥3条结构相似才判定
        _cid_to_tp = {}
        for _c in cases:
            _cid_to_tp[_get_case_field(_c, "case_id", "")] = _get_case_field(_c, "source_test_point", "")
        _tp_groups = {}
        for _cid, _norm in entries:
            _tp = _cid_to_tp.get(_cid, "")
            _tp_groups.setdefault(_tp, []).append((_cid, _norm))
        # 标记是否有同TP内≥3条的group
        _cross_tp_only = True
        for _tp, _tp_entries in _tp_groups.items():
            if len(_tp_entries) >= 3:
                _cross_tp_only = False
                break
        if _cross_tp_only:
            continue  # 全是跨TP的相似,不判定为问题
        
        case_ids = [e[0] for e in entries]
        # 检查原始步骤是否真的完全相同（未归一化前就相同 → 真重复）
        raw_steps_set = set(e[1] for e in entries)
        if len(raw_steps_set) <= 1:
            # 归一化前后都相同 → 先检查语义差异豁免(V4.15.52)
            # 当同一TP内步骤完全相同但preconditions和expected_results都不同时
            # 视为语义不同的正常用例（如异常场景测试：OA异常/类型错误/空数据）
            _cids_set = set(case_ids)
            if len(_cids_set) >= 2 and len(_cids_set) <= 5:
                _preconds = []
                _expecteds = []
                for c in cases:
                    if _get_case_field(c, "case_id", "") in _cids_set:
                        _preconds.append(str(_get_case_field(c, "preconditions", "")).strip())
                        _expecteds.append(str(_get_case_field(c, "expected_results", "")).strip())
                _unique_preconds = len(set(p for p in _preconds if p))
                _unique_expecteds = len(set(e for e in _expecteds if e))
                if _unique_preconds == len(_cids_set) and _unique_expecteds == len(_cids_set):
                    # preconditions和expected各不同 → 语义不同 → 豁免G5 BLOCK
                    continue
        else:
            # V4.15.50: 数据驱动测试豁免 — 归一化后相同但原始仅数据值不同
            # 检查所有原始步骤去掉数据值后是否结构完全一致
            _raw_steps = list(raw_steps_set)
            if len(_raw_steps) >= 2:
                _struct_only = re.sub(r'[\u300c][^\u300d]+[\u300d]', '{DATA}', _raw_steps[0])
                _struct_only = re.sub(r'\d+', '{N}', _struct_only)
                _all_same_structure = all(
                    re.sub(r'\d+', '{N}', re.sub(r'[\u300c][^\u300d]+[\u300d]', '{DATA}', s)) == _struct_only
                    for s in _raw_steps[1:]
                )
                if _all_same_structure:
                    # 仅数据值不同 → 数据驱动测试 → 完全豁免
                    continue
            # 归一化后相同但原始不同 → 结构相似，数据不同，降级为 WARNING
            issues.append({
                "case_ids": case_ids[:5],
                "violation": f"{len(case_ids)}条用例步骤结构相似（数据值不同），建议检查是否需要更多差异化",
                "fix_example": _build_fix_example("duplicate_steps", norm_key, case_ids[0], {"count": len(case_ids), "similarity": "结构"}),
                "type": "similar_structure_warning",
            })
            continue

        # V4.7.0: 检查是否全部来自 risk_verification/exception 且同源
        # 基于 cases 列表临时构建 case_meta（使用 entries 中的数据）
        case_meta = {}
        for c in cases:
            cid = _get_case_field(c, "case_id", "?")
            cat = _get_case_field(c, "test_category", "") or _get_case_field(c, "category", "")
            src = _get_case_field(c, "source_test_point", "")
            case_meta[cid] = {"category": cat, "source": src}
        categories = [case_meta.get(cid, {}).get("category", "") for cid in case_ids]
        sources = [case_meta.get(cid, {}).get("source", "") for cid in case_ids]
        all_risk_or_exc = all(c in ("risk_verification", "exception") for c in categories)
        same_source = len(set(s for s in sources if s)) <= 1
        if all_risk_or_exc and same_source:
            continue
        issues.append({
            "case_ids": case_ids[:5],
            "violation": f"{len(case_ids)}条用例步骤完全相同",
            "fix_example": _build_fix_example("duplicate_steps", norm_key, case_ids[0], {"count": len(case_ids), "similarity": "完全一致"}),
            "type": "duplicate_steps",
        })

    return _make_result(
        "G5", "禁止模式检测", LEVEL_WARNING,
        STATUS_FAILED if issues else STATUS_PASSED,
        f"{len(issues)} 项禁止模式违规" if issues else "无禁止模式",
        issues[:30],
    )


# ============================================================
# G6: 步骤原子性检查
# ============================================================

def gate_g6_step_atomicity(cases: list) -> dict:
    """
    G6 步骤原子性 [BLOCK]

    检查标准：每条步骤只做一件事。
    禁止模式：
      - "点击XX并验证YY"（操作+验证合并）
      - "输入XX后点击YY"（两个操作合并）
      - "登录并进入XX页面"（两个操作合并）
      - "选择XX后填写YY"（选择+输入合并）

    例外：允许 "导航至A→B→C"（导航链路是一个逻辑步骤）
    """
    # 合并操作检测模式
    MERGE_PATTERNS = [
        (r'点击.{1,20}并(?:验证|检查|确认)', '点击+验证合并'),
        (r'输入.{1,20}(?:后|然后|之后).{0,5}(?:点击|提交|选择)', '输入+操作合并'),
        (r'登录.{1,20}并进入', '登录+导航合并'),
        (r'选择.{1,20}(?:并|后).{0,5}(?:填写|输入)', '选择+输入合并'),
    ]

    # 允许的复合操作（不算合并）
    ALLOWED_COMPOUND = [
        r'[\u4e00-\u9fa5]+(?:→|->)[\u4e00-\u9fa5]+',  # 导航链路 A→B→C
        r'导航至',  # 导航动作本身
    ]

    # V4.7.0: 允许的合并模式豁免（标准测试流程中的合理复合操作）
    ALLOWED_MERGE = [
        # 下载验证模式：点击导出/下载后检查结果（标准测试流程，拆了反而不自然）
        r'(?:点击|按下).{1,15}(?:导出|下载).{1,15}(?:检查|确认|查看).{1,20}(?:行数|内容|数据|文件)',
        # 导航→确认模式：点击按钮后确认弹窗（弹窗是点击的直接结果）
        r'点击.{1,20}(?:后|并)确认.{1,20}(?:弹窗|对话框|提示)',
    ]

    issues = []
    for c in cases:
        steps_text = str(_get_case_field(c, "steps", ""))
        step_lines = _extract_step_lines(steps_text)

        for line in step_lines:
            # 先检查是否为允许的复合操作
            is_allowed = any(re.search(p, line) for p in ALLOWED_COMPOUND)
            if is_allowed:
                continue

            # V4.7.0: 检查是否为允许的合并模式（下载验证/导航确认）
            if any(re.search(p, line) for p in ALLOWED_MERGE):
                continue

            for pattern, desc in MERGE_PATTERNS:
                if re.search(pattern, line):
                    issues.append({
                        "case_id": _get_case_field(c, "case_id", "?"),
                        "line": line[:80],
                        "violation": f"步骤非原子：{desc}",
                        "fix_example": _build_fix_example("non_atomic", line, _get_case_field(c, "case_id", "?"), {"merged_action": desc}),
                    })
                    break

    return _make_result(
        "G6", "步骤原子性", LEVEL_BLOCK,
        STATUS_FAILED if issues else STATUS_PASSED,
        f"{len(issues)} 条步骤非原子" if issues else "全部步骤满足原子性",
        issues[:20],
    )


# ============================================================
# G8: 步骤-期望映射检查 (V4.6.14新增)
# ============================================================

def gate_g8_steps_expect_mapping(cases: list) -> dict:
    """
    G8 步骤-期望映射 [BLOCK] (V4.6.14新增)

    检查标准：
      1. P0用例：步骤数必须等于期望结果数（1:1，不允许偏差）
      2. P1/P2/P3用例：
         - 允许偏差：|步骤数 - 期望数| ≤ 2
         - 硬性底线：期望覆盖率 = 期望数/步骤数 ≥ 60%
    
    注意：此检查与Prompt中的规则保持一致，Prompt已更新为：
    "步骤数与期望结果数允许±2偏差(但期望覆盖率≥60%),P0用例不允许偏差"
    """
    issues = []
    for c in cases:
        steps_text = str(_get_case_field(c, "steps", ""))
        expected_text = str(_get_case_field(c, "expected_results", ""))
        priority = str(_get_case_field(c, "priority", "P2"))
        case_id = _get_case_field(c, "case_id", "?")
        
        # 提取编号行
        def extract_lines(text):
            lines = [l.strip() for l in text.split('\n') 
                     if l.strip() and re.match(r'^\d+[\.、\）)]', l.strip())]
            return lines
        
        s_lines = extract_lines(steps_text)
        e_lines = extract_lines(expected_text)
        s_count = len(s_lines)
        e_count = len(e_lines)
        
        if s_count == 0 or e_count == 0:
            # 空的情况由其他检查处理（G1/G2已有空值检查）
            continue
        
        # P0用例：必须1:1对应
        if priority == "P0":
            if s_count != e_count:
                issues.append({
                    "case_id": case_id,
                    "steps_count": s_count,
                    "expect_count": e_count,
                    "deviation": s_count - e_count,
                    "violation": f"P0用例步骤数({s_count})必须等于期望结果数({e_count})，当前偏差{s_count - e_count}",
                    "type": "p0_mismatch",
                })
            continue
        
        # P1/P2/P3用例：允许±2偏差，但期望覆盖率≥60%
        diff = abs(s_count - e_count)
        coverage = e_count / s_count if s_count > 0 else 0
        
        # 检查1：偏差是否超过2
        if diff > 2:
            issues.append({
                "case_id": case_id,
                "steps_count": s_count,
                "expect_count": e_count,
                "deviation": diff,
                "coverage": f"{coverage*100:.1f}%",
                "violation": f"步骤数({s_count})与期望结果数({e_count})偏差{diff}超过2",
                "type": "deviation_exceeded",
            })
        # 检查2：期望覆盖率是否低于60%
        elif coverage < 0.6:
            issues.append({
                "case_id": case_id,
                "steps_count": s_count,
                "expect_count": e_count,
                "coverage": f"{coverage*100:.1f}%",
                "violation": f"期望覆盖率{e_count}/{s_count}={coverage*100:.1f}%低于60%底线",
                "type": "coverage_too_low",
            })
    
    return _make_result(
        "G8", "步骤-期望映射", LEVEL_BLOCK,
        STATUS_FAILED if issues else STATUS_PASSED,
        f"{len(issues)} 条用例步骤-期望映射不合规" if issues else "全部用例步骤-期望映射合规",
        issues[:30],
    )


# ============================================================
# G7: P5-P6 可追溯性检查
# ============================================================

def gate_g7_traceability(cases: list, p5_test_points: list) -> dict:
    """
    G7 P5-P6 可追溯性 [WARNING]

    检查标准：P6 中的操作路径/字段名/按钮名必须在 P5 中找到对应。
    发现无源字段 → 标记为「⚠️ 疑似脑补」，需人工确认。

    与 G4 的区别：
      G4 检查冒烟用例是否来自A类
      G7 检查所有操作路径（包括无引号的）是否有 P5 page_path 对应

    检查逻辑（路径节点逐级验证）：
      1. 提取 P6 步骤中的所有导航路径
      2. 将路径拆分为节点
      3. 逐级检查每个节点是否在 P5 page_path hierarchy 中
      4. 未匹配节点数 ≥ 2 时标记为疑似脑补
    """
    # 从 P5 构建页面路径集合
    valid_paths = set()
    valid_element_names = set()

    for tp in p5_test_points:
        if not isinstance(tp, dict):
            continue

        # 页面路径
        pp = tp.get("page_path", {})
        if isinstance(pp, dict):
            full = pp.get("full_path", "")
            if full:
                for segment in re.split(r'(?:→|->)', full):
                    segment = segment.strip()
                    if segment:
                        valid_paths.add(segment)
            for h in pp.get("hierarchy", []):
                valid_paths.add(h)
        elif isinstance(pp, str):
            for segment in re.split(r'(?:→|->)', pp):
                segment = segment.strip()
                if segment:
                    valid_paths.add(segment)

        # UI 元素名
        ui = tp.get("ui_elements", {})
        if isinstance(ui, dict):
            for btn in ui.get("buttons", []):
                name = btn.get("name", "") if isinstance(btn, dict) else btn
                if name:
                    valid_element_names.add(name)
            for inp in ui.get("inputs", []):
                name = inp.get("name", "") if isinstance(inp, dict) else inp
                if name:
                    valid_element_names.add(name)

        # 字段规格名
        for fs in tp.get("field_specs", []):
            if isinstance(fs, dict):
                name = fs.get("name", fs.get("field_name", ""))
                if name:
                    valid_element_names.add(name)

        # 操作链目标元素
        for op in tp.get("operations_chain", []):
            if isinstance(op, dict) and op.get("target_element"):
                valid_element_names.add(op["target_element"])

    issues = []
    for c in cases:
        case_id = _get_case_field(c, "case_id", "?")
        steps_text = str(_get_case_field(c, "steps", ""))
        expected_text = str(_get_case_field(c, "expected_results", ""))
        full_text = steps_text + " " + expected_text

        # 检查1：导航路径可追溯
        nav_patterns = [
            r'进入([\u4e00-\u9fa5]+(?:→|->)[\u4e00-\u9fa5]+)',
            r'导航至([\u4e00-\u9fa5]+(?:→|->)[\u4e00-\u9fa5]+)',
            r'(?:进入|打开|访问)([\u4e00-\u9fa5]{2,10}(?:页面|列表|模块|弹窗))',
        ]

        for pattern in nav_patterns:
            matches = re.findall(pattern, full_text)
            for match in matches:
                # 检查路径中的每个节点是否在 P5 page_path 中
                segments = re.split(r'(?:→|->)', match)
                unmatched = [s for s in segments if s.strip() and s.strip() not in valid_paths]
                # === V4.15.18: 路径子串匹配容错 ===
                _fuzzy_unmatched = []
                for _s in unmatched:
                    _s_clean = _s.strip()
                    if not any(_s_clean in v or v in _s_clean for v in valid_paths if v):
                        _fuzzy_unmatched.append(_s_clean)
                if len(_fuzzy_unmatched) >= 2:
                    issues.append({
                        "case_id": case_id,
                        "path": match,
                        "unmatched_segments": _fuzzy_unmatched,
                        "issue": f"⚠️ 疑似脑补：路径「{match}」中的 {'、'.join(unmatched)} 不在P5 page_path中",
                        "type": "path_mismatch",
                    })

        # 检查2：引号内的名称可追溯（G4级别增强）
        quoted_names = re.findall(r'[「""\u201c]([^「""\u201d]{1,30})[」""\u201d]', full_text)
        generic_names = {
            # V4.15.22: 系统入口路径白名单（多入口导航不在P5 page_path中）
            "系统中心",
            "继续", "跳过", "确定", "取消", "关闭", "返回", "提交",
            "保存", "删除", "编辑", "搜索", "重置", "下一步", "上一步",
            "是", "否", "确认", "完成", "开始", "结束", "查询",
            # 常见状态值（非UI元素，不应判定为脑补）
            "待审核", "已通过", "已驳回", "已取消", "进行中", "已完成",
            "待处理", "已提交", "草稿", "生效", "失效", "已结束",
            "启用", "停用", "正常", "异常", "审批完成", "待审批",
            # 常见业务实体/数据值（非UI元素）
            "设备",
        }
        for name in quoted_names:
            if (name not in generic_names and len(name) >= 2
                    and name not in valid_element_names and name not in valid_paths):
                # === V4.15.20: 系统通用提示文案检测（不针对具体需求）===
                _SYS_MSG = r'(?:暂无|没有|无权限|失败|成功|错误|异常|超时|重试|过期|无效|数据|网络|系统|服务器|会话|连接|加载|请稍后|请重试|请检查|请联系|请确认|正在|已|未|无此|不存在)'
                # 通用非UI元素豁免：分页信息/数值格式/短数据值
                _NON_UI = bool(re.match(r'^(?:\d+/\d+|第\d+页|\d+条/页|\d+页/\d+|\d+条|共\d+[条页]|\d+[-~]\d+[条页])$', name))
                # V4.15.21: 业务数据值豁免（公司名/产品名/测试假数据）
                _BUSINESS_DATA = bool(re.match(
                    r'(?:公司|分公司|集团|基金|有限|股份|证券|债券|投顾|顾问|营业部|银行|保险|信托|期货)(?:\d+)?$'
                    r'|^[a-zA-Z]{1,5}$'  # 纯短英文测试假数据
                    r'|^\d+(?:条|元|万|亿|个|%|季度|年|月|日|页|次|笔|家|号|分|秒|小时|分钟)$',  # 带单位的数值
                    name))
                if (_NON_UI
                    or _BUSINESS_DATA  # 业务数据值（公司名/产品名/测试数据）
                    or len(name) >= 8  # 完整短句（≥8字）
                    or (len(name) >= 6 and re.search(r'[，。；！？、]', name))  # 带标点
                    or re.search(_SYS_MSG, name)):  # 系统状态关键词
                    continue  # 豁免
                # 进一步模糊匹配：P5中是否包含该名称的子串
                fuzzy_match = any(name in v or v in name for v in (valid_element_names | valid_paths) if v)
                if not fuzzy_match:
                    issues.append({
                        "case_id": case_id,
                        "name": name,
                        "issue": f"⚠️ 疑似脑补：「{name}」不在P5的ui_elements/field_specs/page_path中",
                        "type": "element_mismatch",
                    })

    # V4.15.39: 高频未匹配词统计 — 同一名词≥5次单独提示
    from collections import Counter
    _unmatched_names = [i.get("name", "") for i in issues if i.get("type") == "element_mismatch"]
    _name_counts = Counter(n for n in _unmatched_names if n)
    for _term, _count in _name_counts.most_common():
        if _count >= 5:
            issues.append({
                "term": _term,
                "count": _count,
                "issue": f"⚠️ 高频术语：「{_term}」出现{_count}次但不在P5定义中，请确认P5 ui_elements是否遗漏此核心模块定义",
                "type": "high_freq_term",
            })

    # V4.15.42: 降级 WARNING→INFO (业务通用术语如"审批中""团队维度"不应被标记为脑补)
    return _make_result(
        "G7", "P5-P6可追溯性", "INFO",
        STATUS_PASSED,
        f"{len(issues)} 处路径/元素无P5来源（需人工确认）" if issues else "所有操作路径可追溯到P5",
        issues[:30],
    )


# ============================================================
# V4.13.9-S4: G9-G13 新增检查项
# ============================================================

DATA_KEYWORDS_V9 = {
    # V4.15.12: 扩充高频词，原文大多含"已登录""登录""账号"等基础词但旧词典不收录
    # V4.15.12-review: 移除"条"(过短,匹配"条件"等)和"正常"(过泛)，改用"系统正常"
    "account": ["测试账号","登录账号","已授权","操作权限","角色","已登录","登录","账号","账户","管理","权限"],
    "fund": ["初始金额","账户余额","资金池","清算数据"],
    "config": ["分润规则","费率配置","已配置","已创建","已生效","已打开","运行","系统正常"],
    "data": ["测试数据","初始数据","已录入","预置","创建","准备","数据"],
    "status": ["审批通过","已签约","在有效期","客户归属"],
}

def check_G9_data_preconditions(cases, **_kwargs):
    results = []
    for case in cases:
        # V4.15.12: 使用 _get_case_field 兼容嵌套 fields 结构（修复 case_id=? 的字段映射 bug）
        preconditions = str(_get_case_field(case, "preconditions", ""))
        cid = _get_case_field(case, "case_id", "?")
        if not preconditions:
            results.append({"case_id": cid, "status": STATUS_FAILED, "reason": "preconditions字段为空"})
        else:
            has_keyword = False
            for dim_kws in DATA_KEYWORDS_V9.values():
                for kw in dim_kws:
                    if kw in preconditions:
                        has_keyword = True
                        break
                if has_keyword:
                    break
            if has_keyword:
                results.append({"case_id": cid, "status": STATUS_PASSED})
            else:
                results.append({"case_id": cid, "status": STATUS_WARNING, "reason": f"前置条件未检测到明确的数据准备关键词(维度包含:{list(DATA_KEYWORDS_V9.keys())})"})
    return results


def check_G10_dependency(cases, **_kwargs):
    import re
    results = []
    # V4.15.12: 过滤 None case_id + 使用 _get_case_field 兼容嵌套 fields 结构
    case_ids = {_get_case_field(c, "case_id") for c in cases if _get_case_field(c, "case_id")}
    for case in cases:
        cid = _get_case_field(case, "case_id", "?")
        steps_text = json.dumps(_get_case_field(case, "steps", []), ensure_ascii=False)
        referenced = []
        for other_cid in case_ids:
            if other_cid == cid:
                continue
            if re.search(r'\b' + re.escape(other_cid) + r'\b', steps_text):
                referenced.append(other_cid)
        if referenced and not case.get("depends_on"):
            results.append({"case_id": cid, "status": STATUS_WARNING, "reason": f"用例引用了{referenced}但未声明depends_on依赖"})
        else:
            results.append({"case_id": cid, "status": STATUS_PASSED})
    # 批量升级: >30%未声明依赖 → BLOCK
    fail_count = sum(1 for r in results if r["status"] == STATUS_WARNING)
    if fail_count > len(cases) * 0.3:
        for r in results:
            if r["status"] == STATUS_WARNING:
                r["status"] = STATUS_FAILED
                r["level"] = LEVEL_BLOCK
                r["reason"] += " [系统级:依赖缺失占比>{:.0%}]".format(fail_count/len(cases))
    return results


def check_G11_req_traceability(cases, p5_test_points, **_kwargs):
    if not p5_test_points:
        return [{"status": STATUS_WARNING, "reason": "p5_test_points为空,无法验证需求追溯(上游P5可能未运行)"}]
    def _get_tp_id(tp):
        for key in ("id","tp_id","test_point_id","point_id"):
            if tp.get(key): return tp[key]
        return ""
    def _get_req_tag(tp):
        for key in ("req_tag","requirement_id","source_scenario"):
            if tp.get(key): return tp[key]
        return ""
    # V4.15.45 方案A: RISK/PCI类为横切关注点(来源P3风险识别/P4合规识别),
    # 不对应单一需求条目,豁免REQ追溯。以p5层category(规范英文值)为主 + ID前缀兵底(防category分配不一致)。
    def _is_risk_pci(tp):
        category = str(tp.get("category", "") or "")
        if category in ("risk_verification", "pci_verification"):
            return True
        tp_id = str(_get_tp_id(tp))
        # 匹配ID前缀: ^R\d+-(如R1-001,本任务task_20260711实跑P5输出RISK类即此格式) / PCI- / RISK-(兵底兼容)
        # 注: requirement-TP-xxx / REQ-xxx 不会被 ^R\d+- 命中(R后必须跟数字+连字符),不误伤需求类
        if re.match(r'^R\d+-', tp_id) or tp_id.startswith("PCI-") or tp_id.startswith("RISK-"):
            return True
        return False
    tp_req_map = {_get_tp_id(tp): _get_req_tag(tp) for tp in p5_test_points}
    # 豁免集: p5层判定为RISK/PCI的tp_id
    exempt_ids = {_get_tp_id(tp) for tp in p5_test_points if _is_risk_pci(tp) and _get_tp_id(tp)}
    tp_coverage = {}
    for case in cases:
        # V4.15.45修复: case对象无tp_id字段,只有source_test_point(值"requirement-TP-001"),
        # 与p5_test_points的id格式一致。此前读case.get("tp_id")恒为空串,导致268条全映射到"",
        # tp_coverage仅剩1个空key,误报"1/1未关联REQ_ID占比100%"。与同文件其他函数读法对齐。
        tp_id = str(_get_case_field(case, "source_test_point", "") or case.get("source_test_point", "")).strip()
        # V4.15.45 方案A: RISK/PCI类豁免追溯,不计入tp_coverage
        if tp_id in exempt_ids:
            continue
        if tp_id not in tp_coverage:
            tp_coverage[tp_id] = tp_req_map.get(tp_id, "")
    exempt_count = len([1 for tp_id in exempt_ids if tp_id])
    # V4.15.45 边界防御: 若所有TP都是RISK/PCI(tp_coverage为空),直接PASS
    if not tp_coverage:
        return [{"status": STATUS_PASSED, "summary": f"本任务仅含RISK/PCI类TP({exempt_count}个横切关注点),无需REQ追溯", "exempt_risk_pci_count": exempt_count}]
    missing_tps = [(tp, req) for tp, req in tp_coverage.items() if not req]
    # V4.15.45 有声豁免: 将RISK/PCI豁免信息同步到返回结果,避免无声跳过掩盖真问题
    _exempt_note = f"; {exempt_count}个RISK/PCI类TP豁免(来源P3/P4横切关注点)" if exempt_count else ""
    if len(missing_tps) > len(tp_coverage) * 0.5:
        return [{"status": STATUS_WARNING, "reason": f"{len(missing_tps)}/{len(tp_coverage)} 需求类TP未关联REQ_ID(占比{int(len(missing_tps)/max(len(tp_coverage),1)*100)}%),请检查P5→需求追溯链路{_exempt_note}", "exempt_risk_pci_count": exempt_count}]
    if missing_tps:
        return [{"tp_ids": [tp for tp,_ in missing_tps], "status": STATUS_FAILED, "reason": f"{len(missing_tps)}个需求类TP未关联需求编号(REQ){_exempt_note}", "exempt_risk_pci_count": exempt_count}]
    return [{"status": STATUS_PASSED, "summary": f"所有需求类TP均追溯至需求{_exempt_note}", "exempt_risk_pci_count": exempt_count}]


def check_G12_boundary_coverage(_cases, p5_test_points, **_kwargs):
    """G12 边界值覆盖 [WARNING]。V4.15.18: 动态阈值(加权平均) + TP<5绝对数量兜底"""
    total_tps = len(p5_test_points or [])
    if total_tps == 0:
        return [{"status": STATUS_WARNING, "reason": "无TP数据,无法评估边界值覆盖"}]

    boundary_count = sum(1 for tp in (p5_test_points or [])
                         if tp.get("category") in ("boundary","边界")
                         or "边界" in str(tp.get("category","")))

    # === V4.15.18: TP<5时使用绝对数量判定 ===
    if total_tps < 5:
        if boundary_count >= 1:
            return [{"status": STATUS_PASSED, "reason": f"boundary{boundary_count}个(TP总数{total_tps}<5,绝对数量合格)"}]
        return [{"status": STATUS_WARNING, "reason": f"boundary=0(TP总数{total_tps}<5),建议至少补充1个边界值场景"}]

    # === V4.15.18: 加权平均动态阈值（避免if/elif冲突）===
    main_flow_ratio = sum(1 for tp in (p5_test_points or [])
                          if tp.get("category") == "main_flow") / total_tps
    data_ratio = sum(1 for tp in (p5_test_points or [])
                     if tp.get("category") in ("data_consistency", "boundary")) / total_tps
    boundary_threshold = (0.10 * main_flow_ratio +
                          0.20 * data_ratio +
                          0.15 * max(0, 1 - main_flow_ratio - data_ratio))

    ratio = boundary_count / total_tps
    if ratio < boundary_threshold:
        return [{"status": STATUS_WARNING, "level": LEVEL_WARNING,
                 "reason": f"boundary TP占比仅{ratio:.1%}(<{boundary_threshold:.0%}),建议补充边界值场景"}]
    return [{"status": STATUS_PASSED, "reason": f"boundary占比{ratio:.1%}合格(阈值{boundary_threshold:.0%})"}]


def check_G13_priority_distribution(cases, **_kwargs):
    total = len(cases)
    if total == 0:
        return [{"status": STATUS_PASSED}]
    p0_count = sum(1 for c in cases if c.get("priority") == "P0")
    p0_ratio = p0_count / total
    issues = []
    
    # V4.15.5: P0 正向覆盖检查 — P0中必须包含main_flow类正向流程用例
    p0_cases = [c for c in cases if c.get("priority") == "P0"]
    p0_positive = [c for c in p0_cases if c.get("source_test_point", "").startswith("requirement-TP")
                   or "正向流程" in str(c.get("title", ""))
                   or "正常流程" in str(c.get("title", ""))]
    p0_risk_only = [c for c in p0_cases if "RISK-" in c.get("case_id", "")
                    or "PCI-" in c.get("case_id", "")]
    if p0_count > 0 and len(p0_positive) == 0 and len(p0_risk_only) == p0_count:
        issues.append({
            "status": STATUS_WARNING,
            "level": LEVEL_WARNING,
            "reason": f"{p0_count}条P0用例全部来自RISK/PCI类,缺少核心正向流程覆盖"
        })
    
    if p0_ratio > 0.25:
        issues.append({"status": STATUS_FAILED, "level": LEVEL_BLOCK, "reason": f"P0占比{p0_ratio:.1%}严重超标(>25%)"})
    elif p0_ratio > 0.20:
        issues.append({"status": STATUS_WARNING, "level": LEVEL_WARNING, "reason": f"P0占比{p0_ratio:.1%}偏高(>20%),建议优化"})
    elif p0_ratio < 0.10 and total > 10:
        issues.append({"status": STATUS_WARNING, "reason": f"P0占比{p0_ratio:.1%}偏低(<10%),核心覆盖可能不足"})
    
    if not issues:
        return [{"status": STATUS_PASSED, "reason": f"P0占比{p0_ratio:.1%}合格"}]
    return issues


# ============================================================
# V4.14.0-P5: Description 质量门禁（BLOCK+WARNING 双级）
# ============================================================
# 指标：
#   - description 字数 < 80字       → BLOCK
#   - 前置条件 < 2维度              → BLOCK
#   - 操作动词 = 0                  → WARNING
#   - 具体数据 = 0                  → WARNING

PRECONDITION_DIMS = {
    "环境": ["环境", "系统", "页面", "模块", "菜单", "功能", "首页"],
    "数据": ["数据", "记录", "账户", "客户", "债券", "产品", "订单", "金额"],
    "状态": ["已", "状态", "完成", "审批", "生效", "到期", "通过"],
    "权限": ["权限", "角色", "登录", "授权", "访问"],
    "配置": ["规则", "比例", "费率", "配置", "参数"],
}

ACTION_VERBS = ["点击", "输入", "选择", "提交", "保存", "删除", "修改",
                "验证", "检查", "确认", "查询", "搜索", "导出", "导入"]

# V4.15.36: P5 门禁降级白名单 —— 有完整操作链的 TP 不因描述短被 block
DESC_GATE_DOWNGRADE_CATEGORIES = frozenset(["risk_verification", "pci_verification"])


def check_p5_description_quality(test_points):
    """P5 description 质量门禁（BLOCK+WARNING双级）

    V4.15.36: 增加 step_expected_pairs 降级机制
    - 有完整操作链（>=2步，来源 operations_chain）的 TP，即使描述短也降级 BLOCK→WARNING
    - risk_verification / pci_verification 两类不享受降级（描述是唯一信息源）

    Args:
        test_points: P5 测试点列表（每个含 description / id / category / step_expected_pairs / operations_chain 字段）

    Returns:
        list[dict]: 每个 TP 的检查结果，含 tp_id / char_count / dim_hits / issues / downgraded
            issues 中每项: {"level": "BLOCK"|"WARNING", "reason": str}
    """
    results = []
    for tp in test_points:
        desc = tp.get("description", "") if isinstance(tp, dict) else ""
        desc = desc or ""
        tp_id = tp.get("id", "?") if isinstance(tp, dict) else "?"
        issues = []
        char_count = len(desc.strip())

        # 字数检查 BLOCK
        if char_count < 80:
            issues.append({"level": "BLOCK", "reason": f"字数{char_count}<80"})

        # 前置条件完整性 BLOCK（5维度，至少命中1维度 — V4.15.23从≥2降为≥1）
        dim_hits = sum(1 for dim, kws in PRECONDITION_DIMS.items()
                       if any(kw in desc for kw in kws))
        if dim_hits < 1:
            issues.append({"level": "BLOCK", "reason": f"前置条件仅命中{dim_hits}/5维度(<1)"})

        # 操作动词 WARNING
        if not any(v in desc for v in ACTION_VERBS):
            issues.append({"level": "WARNING", "reason": "缺少具体操作动词"})

        # 具体数据 WARNING（数字/引号文案/日期/金额/编号）
        has_data = bool(
            re.search(r'\d', desc)
            or re.search(r'[「『"\u201c][^」』"\u201d]{1,30}[」』"\u201d]', desc)
        )
        if not has_data:
            issues.append({"level": "WARNING", "reason": "缺少具体测试数据"})

        # V4.15.36: step_expected_pairs 降级判断
        # 有完整操作链（>=2步，非fallback模板）的 TP，描述短不影响质量
        downgraded = False
        has_block = any(i["level"] == "BLOCK" for i in issues)
        if has_block and isinstance(tp, dict):
            category = tp.get("category", "") or ""
            sep = tp.get("step_expected_pairs", [])
            ops_chain = tp.get("operations_chain", [])

            # V4.15.37: 额外检查——RISK/PCI TP 即使category不在排除列表，也按ID前缀排除
            _tp_id = tp.get("id", "") or ""
            _is_risk_pci_by_id = _tp_id.startswith("RISK-") or _tp_id.startswith("PCI-")

            # 降级条件（全部满足）:
            # 1. step_expected_pairs >= 2步
            # 2. 来源是 operations_chain（非 fallback 模板）
            # 3. category 不在降级排除列表（risk_verification/pci_verification）
            # 4. 非 RISK-/PCI- TP（V4.15.37: ID前缀二次排除，防御category分配不一致）
            if (isinstance(sep, list) and len(sep) >= 2
                    and isinstance(ops_chain, list) and len(ops_chain) > 0
                    and category not in DESC_GATE_DOWNGRADE_CATEGORIES
                    and not _is_risk_pci_by_id):
                # 检查步骤不含占位符（{diff}等模板标记）
                steps_text = "".join(s.get("step", "") for s in sep if isinstance(s, dict))
                if "{diff}" not in steps_text:
                    # 降级: BLOCK → WARNING
                    for issue in issues:
                        if issue["level"] == "BLOCK":
                            issue["level"] = "WARNING"
                            issue["reason"] += " [V4.15.36降级:有完整操作链>=2步]"
                    downgraded = True
                    # 描述仍过短(<30字)时追加提示
                    if char_count < 30:
                        issues.append({"level": "WARNING",
                                       "reason": f"描述仅{char_count}字(已降级放行,建议后续补充)"})

        results.append({
            "tp_id": tp_id,
            "char_count": char_count,
            "dim_hits": dim_hits,
            "issues": issues,
            "downgraded": downgraded,
        })
    return results


# V4.13.9-S4: G9-G13 注册表（4元组: id, name, level, fn）
GATE_CHECKS = [
    ("G9",  "数据前置条件", LEVEL_BLOCK,   check_G9_data_preconditions),
    ("G10", "依赖关系声明", LEVEL_WARNING,  check_G10_dependency),
    ("G11", "需求追溯",     LEVEL_BLOCK,   check_G11_req_traceability),
    ("G12", "边界值覆盖",   LEVEL_WARNING,  check_G12_boundary_coverage),
    ("G13", "P0优先级分布", LEVEL_WARNING,  check_G13_priority_distribution),
]


def _adapt_gate_result(check_id: str, name: str, default_level: str, raw) -> dict:
    """V4.13.9-S4: 将 G9-G13 的 list 输出归一化为标准 Gate 结果 dict，
    以兼容 evaluate_gate / format_gate_report。

    - status: 任一 FAILED→FAILED; 否则任一 WARNING→WARNING; 否则 PASSED
    - level:  FAILED 时取失败项显式 level 的最强者(BLOCK 优先)，无显式则用注册默认 level
    - issues: 收集所有非 PASSED 项
    """
    if not isinstance(raw, list):
        raw = [raw]
    has_failed = any(r.get("status") == STATUS_FAILED for r in raw)
    has_warning = any(r.get("status") == STATUS_WARNING for r in raw)
    if has_failed:
        overall_status = STATUS_FAILED
        failed_levels = [r.get("level") for r in raw
                         if r.get("status") == STATUS_FAILED and r.get("level")]
        if LEVEL_BLOCK in failed_levels:
            level = LEVEL_BLOCK
        elif failed_levels:
            level = failed_levels[0]
        else:
            level = default_level
    elif has_warning:
        overall_status = STATUS_WARNING
        level = LEVEL_WARNING
    else:
        overall_status = STATUS_PASSED
        level = default_level
    issues = [r for r in raw if r.get("status") != STATUS_PASSED]
    reasons = [str(r.get("reason") or r.get("summary"))
               for r in raw if (r.get("reason") or r.get("summary"))]
    if overall_status == STATUS_PASSED:
        detail = reasons[0] if reasons else f"{name}检查通过"
    else:
        detail = "; ".join(reasons[:5]) if reasons else f"{name}检查未通过"
    return _make_result(check_id, name, level, overall_status, detail, issues)


# ============================================================
# Gate 检查集成入口
# ============================================================

def run_gate_checks(cases: list, p5_test_points: list,
                    check_ids: list = None) -> list:
    """
    执行 Gate 7项检查（或指定子集）。

    Args:
        cases: P6 生成的用例列表
        p5_test_points: P5 测试点列表
        check_ids: 要执行的检查ID列表，None表示全部

    Returns:
        list[dict]: 检查结果列表
    """
    all_checks = [
        ("G1", lambda: gate_g1_step_concreteness(cases, p5_test_points)),
        ("G1.5", lambda: gate_g1_5_last_step_observability(cases, p5_test_points)),
        ("G2", lambda: gate_g2_expected_assertiveness(cases)),
        ("G3", lambda: gate_g3_business_flow_coverage(cases, p5_test_points)),
        ("G4", lambda: gate_g4_smoke_source(cases, p5_test_points)),
        ("G5", lambda: gate_g5_banned_patterns(cases)),
        ("G6", lambda: gate_g6_step_atomicity(cases)),
        ("G7", lambda: gate_g7_traceability(cases, p5_test_points)),
        # G8已废弃(V4.6.17): 与orchestrator C2检查重复，移除
    ]

    results = []
    for check_id, check_fn in all_checks:
        if check_ids and check_id not in check_ids:
            continue
        try:
            result = check_fn()
            results.append(result)
        except Exception as e:
            results.append({
                "check_id": check_id,
                "name": f"{check_id}检查",
                "level": LEVEL_BLOCK,
                "status": STATUS_ERROR,
                "detail": f"检查执行异常: {str(e)}",
                "issues": [],
            })

    # V4.13.9-S4: 执行 G9-G13 扩展检查（list 输出经适配器归一化）
    for check_id, name, level, fn in GATE_CHECKS:
        if check_ids and check_id not in check_ids:
            continue
        try:
            raw = fn(cases, p5_test_points=p5_test_points)
            results.append(_adapt_gate_result(check_id, name, level, raw))
        except Exception as e:
            results.append({
                "check_id": check_id,
                "name": f"{name}检查",
                "level": level,
                "status": STATUS_ERROR,
                "detail": f"检查执行异常: {str(e)}",
                "issues": [],
            })

    return results


def evaluate_gate(results: list) -> dict:
    """
    评估 Gate 检查结果，判定整体通过/失败。

    Returns:
        dict: {
            "status": "PASS" | "FAIL" | "PARTIAL",
            "block_failed": int,
            "warnings": int,
            "action_required": "NONE" | "RETRY_P6" | "RETRY_P5" | "MANUAL_REVIEW",
            "summary": str,
            "failed_checks": list,
            "warning_checks": list,
            "results_summary": dict,
        }
    """
    if not results:
        return {
            "status": "PASS",
            "block_failed": 0,
            "warnings": 0,
            "action_required": "NONE",
            "summary": "无检查结果",
            "failed_checks": [],
            "warning_checks": [],
            "results_summary": {},
        }

    block_failed = [r for r in results
                    if r.get("status") == STATUS_FAILED and r.get("level") == LEVEL_BLOCK]
    warnings = [r for r in results
                if r.get("status") in (STATUS_WARNING, STATUS_FAILED)
                and r.get("level") == LEVEL_WARNING]
    errors = [r for r in results if r.get("status") == STATUS_ERROR]

    # 构建结果摘要
    results_summary = {}
    for r in results:
        results_summary[r["check_id"]] = {
            "name": r["name"],
            "status": r["status"],
            "level": r["level"],
            "detail": r.get("detail") or r.get("message", ""),
        }

    if block_failed or errors:
        # V4.7.2: 构建最小修复集 — 收集所有 BLOCK issue 涉及的 case_id，按频率排序
        all_fix_ids = []
        for r in block_failed + errors:
            for iss in r.get("issues", []):
                # 单个 case_id
                cid = iss.get("case_id", "")
                if cid and not cid.startswith("_"):
                    all_fix_ids.append(cid)
                # 多个 case_ids (如 G5 duplicate_steps)
                cids = iss.get("case_ids", [])
                if isinstance(cids, list):
                    all_fix_ids.extend(cids)
        from collections import Counter
        id_counter = Counter(all_fix_ids)
        # 按出现频率排序（同一 case_id 出现在多个 BLOCK → 高优先级）
        sorted_ids = sorted(id_counter.items(), key=lambda x: -x[1])
        minimal_fix = {
            "top_fix_targets": [{"case_id": cid, "blocks_involved": cnt} for cid, cnt in sorted_ids[:10]],
            "total_affected_cases": len(id_counter),
            "hint": "优先修复 top_fix_targets 中的用例（同一用例触发多个BLOCK → 高优先级）" if sorted_ids else "无具体case_id信息，请根据 failed_checks 检查对应 Gate 规则"
        }

        # 判断是 P5 还是 P6 的问题
        p5_issues = [r for r in (block_failed + errors)
                     if r.get("check_id") == "G3"]
        if p5_issues:
            action = "RETRY_P5"
        else:
            action = "RETRY_P6"

        return {
            "status": "FAIL",
            "block_failed": len(block_failed) + len(errors),
            "warnings": len(warnings),
            "action_required": action,
            "summary": f"Gate不通过: {len(block_failed) + len(errors)} 项BLOCK级别失败",
            "failed_checks": [r["check_id"] for r in block_failed + errors],
            "warning_checks": [r["check_id"] for r in warnings],
            "minimal_fix_set": minimal_fix,
            "results_summary": results_summary,
        }
    elif warnings:
        return {
            "status": "PARTIAL",
            "block_failed": 0,
            "warnings": len(warnings),
            "action_required": "MANUAL_REVIEW",
            "summary": f"Gate部分通过: {len(warnings)} 项WARNING需人工确认",
            "failed_checks": [],
            "warning_checks": [r["check_id"] for r in warnings],
            "results_summary": results_summary,
        }
    else:
        return {
            "status": "PASS",
            "block_failed": 0,
            "warnings": 0,
            "action_required": "NONE",
            "summary": "Gate全部通过",
            "failed_checks": [],
            "warning_checks": [],
            "results_summary": results_summary,
        }


def format_gate_report(results: list, evaluation: dict) -> str:
    """
    生成人类可读的 Gate 检查报告。

    Args:
        results: run_gate_checks 返回的结果列表
        evaluation: evaluate_gate 返回的评估结果

    Returns:
        str: 格式化的报告文本
    """
    status_icons = {
        STATUS_PASSED: "✅",
        STATUS_FAILED: "❌",
        STATUS_WARNING: "⚠️",
        STATUS_ERROR: "💥",
    }
    overall_icons = {
        "PASS": "✅",
        "FAIL": "🔴",
        "PARTIAL": "🟡",
    }

    lines = [
        "=" * 60,
        f"Gate 7项检查报告 {overall_icons.get(evaluation['status'], '❓')} {evaluation['status']}",
        "=" * 60,
        f"总结: {evaluation['summary']}",
        f"动作: {evaluation['action_required']}",
        "-" * 60,
    ]

    for r in results:
        icon = status_icons.get(r["status"], "?")
        level_tag = f"[{r['level']}]"
        lines.append(f"  {icon} {r['check_id']} {r['name']} {level_tag} — {r['status']}")
        lines.append(f"     {r.get('detail') or r.get('message', '')}")

        if r.get("issues"):
            for issue in r["issues"][:5]:
                if "line" in issue:
                    lines.append(f"     · {issue.get('case_id', '?')}: {issue['line'][:60]}")
                elif "issue" in issue:
                    lines.append(f"     · {issue.get('case_id', issue.get('test_point', '?'))}: {issue['issue'][:60]}")
                elif "violation" in issue:
                    lines.append(f"     · {issue.get('case_id', '?')}: {issue['violation'][:60]}")
            if len(r["issues"]) > 5:
                lines.append(f"     ... 共 {len(r['issues'])} 项问题")

    lines.append("-" * 60)
    lines.append(f"BLOCK失败: {evaluation['block_failed']} 项")
    lines.append(f"WARNING: {evaluation['warnings']} 项")
    lines.append("=" * 60)

    return "\n".join(lines)


# ============================================================
# 自检：快速验证脚本
# ============================================================

if __name__ == "__main__":
    # 构建模拟 P5 测试点
    p5_test_points = [
        {
            "id": "TP-001",
            "title": "发起债券投顾分润申请",
            "category": "main_flow",
            "priority": "P0",
            "status": "active",
            "page_path": {
                "full_path": "首页→营销管理→协同分润→债券投顾",
                "hierarchy": ["首页", "营销管理", "协同分润", "债券投顾"],
            },
            "operations_chain": [
                {"step": 1, "action_type": "navigate", "target_element": "首页→营销管理→协同分润→债券投顾"},
                {"step": 2, "action_type": "click", "target_element": "「发起分润申请」按钮"},
                {"step": 3, "action_type": "input", "target_element": "「创收比例(%)」输入框", "data_value": "50"},
                {"step": 4, "action_type": "click", "target_element": "「提交」按钮"},
            ],
            "ui_elements": {
                "buttons": [{"name": "发起分润申请"}, {"name": "提交"}],
                "inputs": [{"name": "创收比例(%)"}, {"name": "分润说明"}],
            },
            "field_specs": [
                {"name": "创收比例(%)", "type": "number"},
                {"name": "分润说明", "type": "text"},
            ],
        },
        {
            "id": "TP-002",
            "title": "创收比例字段校验",
            "category": "field_validation",
            "priority": "P2",
            "status": "active",
            "page_path": {"full_path": "首页→营销管理→协同分润→债券投顾", "hierarchy": ["首页", "营销管理"]},
            "operations_chain": [
                {"step": 1, "action_type": "navigate", "target_element": "分润申请弹窗"},
            ],
            "ui_elements": {
                "inputs": [{"name": "创收比例(%)"}],
            },
            "field_specs": [
                {"name": "创收比例(%)", "type": "number"},
            ],
        },
    ]

    # 构建模拟 P6 用例（含正常用例 + 各种问题用例）
    cases = [
        # ✅ 正常用例（A类，应通过所有检查）
        {
            "case_id": "TC-001",
            "title": "发起债券投顾分润申请完整流程",
            "source_test_point": "TP-001",
            "is_smoke": "是",
            "priority": "P0",
            "steps": (
                "1. 导航至首页→营销管理→协同分润→债券投顾\n"
                "2. 点击「发起分润申请」按钮\n"
                "3. 在「创收比例(%)」输入框输入50\n"
                "4. 点击「提交」按钮"
            ),
            "expected_results": (
                "1. 提示「分润申请提交成功」\n"
                "2. 列表新增1条状态为「待审核」的记录\n"
                "3. 弹窗自动关闭"
            ),
        },
        # ❌ G1违规：步骤模糊
        {
            "case_id": "TC-002",
            "title": "验证分润功能",
            "source_test_point": "TP-001",
            "is_smoke": False,
            "steps": (
                "1. 进入相关功能页面\n"
                "2. 执行相关操作\n"
                "3. 检查系统响应"
            ),
            "expected_results": (
                "1. 正常加载\n"
                "2. 功能正常\n"
                "3. 操作成功"
            ),
        },
        # ❌ G2违规：期望模糊
        {
            "case_id": "TC-003",
            "title": "分润申请提交",
            "source_test_point": "TP-001",
            "is_smoke": False,
            "steps": (
                "1. 导航至首页→营销管理→协同分润→债券投顾\n"
                "2. 点击「发起分润申请」按钮\n"
                "3. 在「创收比例(%)」输入框输入30"
            ),
            "expected_results": (
                "1. 验证成功\n"
                "2. 数据正确\n"
                "3. 符合预期"
            ),
        },
        # ❌ G3违规：B类标记冒烟
        {
            "case_id": "TC-004",
            "title": "创收比例字段边界值校验",
            "source_test_point": "TP-002",
            "is_smoke": "是",
            "steps": (
                "1. 打开分润申请弹窗\n"
                "2. 在「创收比例(%)」输入框输入-1"
            ),
            "expected_results": (
                "1. 输入框红色边框\n"
                "2. 提示「创收比例不能为负数」"
            ),
        },
        # ❌ G5违规：步骤与title高度相似 + 条件性词汇
        {
            "case_id": "TC-005",
            "title": "创收比例字段边界值校验测试验证",
            "source_test_point": "TP-002",
            "is_smoke": False,
            "steps": (
                "1. 创收比例字段边界值校验测试验证的步骤内容\n"
                "2. 如有异常则跳过"
            ),
            "expected_results": (
                "1. 边界值校验通过\n"
                "2. 数据符合预期"
            ),
        },
        # ❌ G6违规：步骤非原子
        {
            "case_id": "TC-006",
            "title": "分润申请编辑",
            "source_test_point": "TP-001",
            "is_smoke": False,
            "steps": (
                "1. 导航至首页→营销管理→协同分润→债券投顾\n"
                "2. 点击「编辑」按钮并验证页面加载\n"
                "3. 输入分润说明后点击「保存」"
            ),
            "expected_results": (
                "1. 页面正常展示\n"
                "2. 编辑弹窗打开\n"
                "3. 保存成功"
            ),
        },
        # ❌ G7违规：路径无P5来源
        {
            "case_id": "TC-007",
            "title": "审批流程测试",
            "source_test_point": "TP-001",
            "is_smoke": False,
            "steps": (
                "1. 导航至系统设置→权限管理→用户管理→角色配置\n"
                "2. 点击「新增角色」按钮\n"
                "3. 填写「角色名称」为管理员"
            ),
            "expected_results": (
                "1. 页面正常展示\n"
                "2. 新增弹窗打开\n"
                "3. 角色创建成功"
            ),
        },
        # ✅ 正常用例2
        {
            "case_id": "TC-008",
            "title": "创收比例正常值输入",
            "source_test_point": "TP-002",
            "is_smoke": False,
            "steps": (
                "1. 导航至首页→营销管理→协同分润→债券投顾\n"
                "2. 点击「发起分润申请」按钮\n"
                "3. 在「创收比例(%)」输入框输入50"
            ),
            "expected_results": (
                "1. 债券投顾页面正常展示\n"
                "2. 弹窗打开，表单字段可见\n"
                "3. 输入框显示50，无校验错误"
            ),
        },
    ]

    print("=" * 70)
    print("Gate 7项检查 - 自测验证")
    print("=" * 70)

    # 执行全量检查
    results = run_gate_checks(cases, p5_test_points)
    evaluation = evaluate_gate(results)

    # 打印报告
    report = format_gate_report(results, evaluation)
    print(report)

    # 统计
    print("\n📊 检查结果统计:")
    passed_count = sum(1 for r in results if r["status"] == STATUS_PASSED)
    total_count = len(results)
    pass_rate = passed_count / total_count if total_count > 0 else 0
    print(f"   通过: {passed_count}/{total_count} ({pass_rate:.1%})")
    print(f"   整体状态: {evaluation['status']}")
    print(f"   动作: {evaluation['action_required']}")

    # 快速检查子集测试
    print("\n" + "=" * 70)
    print("快速检查子集 (G1+G2+G5) - 自测验证")
    print("=" * 70)

    quick_results = run_gate_checks(cases, p5_test_points, check_ids=["G1", "G2", "G5"])
    quick_eval = evaluate_gate(quick_results)
    quick_report = format_gate_report(quick_results, quick_eval)
    print(quick_report)

    print("\n✅ 自测完成")
