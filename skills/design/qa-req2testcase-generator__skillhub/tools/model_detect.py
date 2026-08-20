#!/usr/bin/env python3
"""
V5.0(4.13.0): 模型能力分级模块 — 已废弃

HIGH/LOW 分档已废除,统一为 standard 单一模式。
此模块仅保留用于旧批次路径(p6_batch_info/prep_prompt P6)的兼容性。
classify() 和 get_batch_size() 仍可调用但不再用于控制主流程。

用法(兼容):
    from tools.model_detect import classify
    tier = classify("minimax-m2.5")
    # → "LOW" (仅用于旧批次路径)
"""

import re

__version__ = "5.0"  # V4.13.0: HIGH/LOW 分档已废除,仅保留兼容

# HIGH 白名单：已确认有大上下文（≥128K）+ 强推理能力的模型
# 不在白名单中的模型全部走 LOW（引导卡模式）
HIGH_TIER_WHITELIST = [
    "claude",     # Anthropic Claude 全系列
    "gpt-4",      # OpenAI GPT-4 系列 (含 gpt-4o, gpt-4-turbo 等)
    "kimi",       # Moonshot Kimi 系列
    "glm",        # 智谱 GLM 系列
    "gemini",     # Google Gemini 系列
    "deepseek",   # DeepSeek V3/R1 系列
]


def classify(model_name: str) -> str:
    """模型名→档位。白名单匹配 → HIGH，其余 → LOW。

    Args:
        model_name: 模型名称字符串（如 "minimax-m2.5", "claude-opus-4-7"）

    Returns:
        "HIGH" 或 "LOW"
    """
    if not model_name:
        return "LOW"

    name = model_name.lower().strip()

    for key in HIGH_TIER_WHITELIST:
        if key in name:
            return "HIGH"

    # 不在白名单 → LOW（保守策略，确保质量底线）
    return "LOW"


def get_batch_size(tier: str, total_test_points: int) -> int:
    """根据模型档位返回推荐的批次大小。

    Args:
        tier: "HIGH" 或 "LOW"
        total_test_points: 总测试点数

    Returns:
        每批测试点数
    """
    if tier == "HIGH":
        if total_test_points <= 20:
            return total_test_points
        return min(25, max(15, total_test_points // 4))
    else:  # LOW
        if total_test_points <= 3:
            return total_test_points
        return min(5, max(3, total_test_points // 10))


__all__ = ["classify", "get_batch_size", "HIGH_TIER_WHITELIST"]
