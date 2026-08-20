#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""用户画像模型 (v4.0.0 新增)

Risk Profile：保守/稳健/平衡/进取/激进 → 目标资产配置映射
持久化到 data/clients/{client_id}/profile.json
"""
from __future__ import annotations
import sys, json
from pathlib import Path
from typing import Dict, Optional
from dataclasses import dataclass, field

SKILL_DIR = Path(__file__).resolve().parents[3]
DATA_DIR = SKILL_DIR / "data" / "clients"

# 风险偏好 → 目标配置 {股票%, 债券%, 基金%, 现金%}
RISK_ALLOCATION = {
    "保守": {"stock": 10, "bond": 60, "fund": 20, "cash": 10},
    "稳健": {"stock": 25, "bond": 40, "fund": 25, "cash": 10},
    "平衡": {"stock": 40, "bond": 25, "fund": 25, "cash": 10},
    "进取": {"stock": 60, "bond": 10, "fund": 20, "cash": 10},
    "激进": {"stock": 75, "bond": 5, "fund": 15, "cash": 5},
}

# 风险偏好 → 建议投资时长范围(月)
RISK_DURATION = {
    "保守": (6, 12), "稳健": (12, 36), "平衡": (24, 60),
    "进取": (36, 84), "激进": (60, 120),
}


@dataclass
class UserProfile:
    client_id: str = ""
    risk_preference: str = "平衡"        # 保守/稳健/平衡/进取/激进
    expected_annual_return_pct: float = 8.0   # 预期年化收益率%
    investment_duration_months: int = 24       # 预期投资时长(月)
    total_amount: float = 0.0                  # 总投资金额
    liquidity_needs: str = "低"                # 流动性需求: 低/中/高
    constraints: str = ""                      # 特殊约束(如"不投白酒")

    def target_allocation(self) -> Dict[str, float]:
        return RISK_ALLOCATION.get(self.risk_preference,
                                   RISK_ALLOCATION["平衡"])

    def suggested_duration_range(self) -> tuple:
        return RISK_DURATION.get(self.risk_preference, (24, 60))

    def duration_match(self) -> str:
        lo, hi = self.suggested_duration_range()
        actual = self.investment_duration_months
        if lo <= actual <= hi:
            return "匹配"
        elif actual < lo:
            return f"偏短(建议≥{lo}月)"
        else:
            return f"偏长(建议≤{hi}月)"

    def to_dict(self) -> Dict:
        return {
            "client_id": self.client_id,
            "risk_preference": self.risk_preference,
            "expected_annual_return_pct": self.expected_annual_return_pct,
            "investment_duration_months": self.investment_duration_months,
            "total_amount": self.total_amount,
            "liquidity_needs": self.liquidity_needs,
            "constraints": self.constraints,
        }

    @classmethod
    def from_dict(cls, d: Dict) -> "UserProfile":
        return cls(
            client_id=d.get("client_id", ""),
            risk_preference=d.get("risk_preference", "平衡"),
            expected_annual_return_pct=d.get("expected_annual_return_pct", 8.0),
            investment_duration_months=d.get("investment_duration_months", 24),
            total_amount=d.get("total_amount", 0.0),
            liquidity_needs=d.get("liquidity_needs", "低"),
            constraints=d.get("constraints", ""),
        )


def profile_path(client_id: str) -> Path:
    return DATA_DIR / client_id / "profile.json"


def load_profile(client_id: str) -> Optional[UserProfile]:
    p = profile_path(client_id)
    if not p.exists():
        return None
    try:
        with open(p, "r", encoding="utf-8") as f:
            return UserProfile.from_dict(json.load(f))
    except Exception:
        return None


def save_profile(profile: UserProfile) -> bool:
    p = profile_path(profile.client_id)
    p.parent.mkdir(parents=True, exist_ok=True)
    try:
        with open(p, "w", encoding="utf-8") as f:
            json.dump(profile.to_dict(), f, ensure_ascii=False, indent=2)
        return True
    except Exception:
        return False
