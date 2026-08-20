#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""learning — 自进化学习包 (v7.0 新增)

导出 LearningEngine。学习闭环：
记录建议 → 事后回填 → 统计命中 → 校准参数 → 更新规则库 → 下次建议用新参数。
"""
from .learning_engine import LearningEngine

__all__ = ["LearningEngine"]
