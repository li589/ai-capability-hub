# -*- coding: utf-8 -*-
"""情景模拟器 (v8.0 新增)
=======================
交互式 What-If 分析引擎，纯标准库实现。

支持情景:
  - market_shock: 市场冲击模拟 ("如果沪深300再跌10%")
  - fund_swap: 换仓影响模拟 ("如果换掉A基金")
  - rate_change: 利率变化影响 ("如果加息50bp")
  - inflation_impact: 通胀侵蚀模拟 ("如果通胀上升2%")
  - sector_rotation: 板块轮动模拟 ("如果科技板块领涨")
  - contribution_change: 定投变化模拟 ("如果每月多投1000")

输出: 情景前后的组合指标对比（收益/回撤/波动/Sharpe 变化）
"""
from __future__ import annotations

import math
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any

_SCRIPTS = Path(__file__).resolve().parents[1]
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from fund_advisor_paths import DATA_DIR, load_json_data  # noqa: E402

# ── 情景模板 ──────────────────────────────────────────────────
SCENARIO_TEMPLATES = {
    "market_crash": {
        "name": "市场暴跌", "type": "equity_shock",
        "params": {"equity_shock": -0.20, "bond_shock": 0.02},
        "description": "假设权益市场下跌20%，债券上涨2%",
    },
    "rate_hike": {
        "name": "加息冲击", "type": "rate",
        "params": {"rate_delta_bps": 100, "equity_shock": -0.10, "bond_shock": -0.05},
        "description": "假设加息100bp，股债双杀",
    },
    "sector_boom": {
        "name": "板块领涨", "type": "sector_boom",
        "params": {"sector": "科技", "sector_return": 0.30, "other_return": 0.05},
        "description": "假设某板块大涨30%，其他板块仅涨5%",
    },
    "inflation_surge": {
        "name": "通胀上升", "type": "inflation",
        "params": {"inflation_delta": 0.03, "equity_shock": -0.10, "bond_shock": -0.08},
        "description": "假设通胀率上升3个百分点",
    },
    "currency_devaluation": {
        "name": "汇率贬值", "type": "currency",
        "params": {"fx_depreciation": 0.10, "qdii_return": 0.10, "domestic_shock": -0.05},
        "description": "假设人民币贬值10%，QDII受益，国内资产承压",
    },
}

# 各资产类型对不同冲击的敏感度（Beta）
SHOCK_SENSITIVITIES = {
    "股票型": {"equity": 1.0, "bond": 0.0, "rate": -0.3, "fx": 0.1},
    "偏股混合": {"equity": 0.80, "bond": 0.10, "rate": -0.25, "fx": 0.1},
    "混合型": {"equity": 0.55, "bond": 0.30, "rate": -0.20, "fx": 0.15},
    "偏债混合": {"equity": 0.20, "bond": 0.70, "rate": -0.40, "fx": 0.05},
    "债券型": {"equity": 0.05, "bond": 0.90, "rate": -0.50, "fx": 0.0},
    "纯债": {"equity": 0.0, "bond": 1.0, "rate": -0.55, "fx": 0.0},
    "指数型": {"equity": 1.0, "bond": 0.0, "rate": -0.25, "fx": 0.1},
    "ETF": {"equity": 1.0, "bond": 0.0, "rate": -0.25, "fx": 0.1},
    "QDII": {"equity": 0.70, "bond": 0.10, "rate": -0.15, "fx": 0.80},
    "货币型": {"equity": 0.0, "bond": 0.0, "rate": 0.10, "fx": 0.0},
    "default": {"equity": 0.50, "bond": 0.30, "rate": -0.20, "fx": 0.10},
}


class ScenarioSimulator:
    """情景模拟器 v8.0"""

    def __init__(self, data_dir: Optional[Path] = None):
        self.data_dir = Path(data_dir) if data_dir else DATA_DIR
        self._funds_db: Optional[Dict] = None

    @property
    def funds_db(self) -> Dict:
        if self._funds_db is None:
            self._funds_db = {}
            try:
                data = load_json_data(str(self.data_dir / 'fund_products.json'))
                for f in data.get('products', data.get('items', [])):
                    code = f.get('code', '') or f.get('fund_code', '')
                    if code:
                        self._funds_db[code] = f
            except Exception:
                pass
        return self._funds_db

    # ── 1. 市场冲击 ──────────────────────────────────────────
    def market_shock(
        self,
        holdings: List[Dict[str, Any]],
        equity_shock_pct: float = -20.0,
        bond_shock_pct: float = 2.0,
        total_assets: Optional[float] = None,
    ) -> Dict[str, Any]:
        """市场冲击模拟。

        Args:
            holdings: 持仓列表 [{"fund_code": "000001", "weight": 30, "amount": 30000}, ...]
            equity_shock_pct: 权益市场涨跌幅（%），负值=下跌
            bond_shock_pct: 债券市场涨跌幅（%）
            total_assets: 总资产（元），从 weight 推断时不需提供

        Returns:
            情景影响报告
        """
        equity_shock = equity_shock_pct / 100.0
        bond_shock = bond_shock_pct / 100.0

        total_weight = sum(h.get("weight", 0) for h in holdings) or 1.0
        if total_assets is None:
            total_assets = sum(h.get("amount", 0) for h in holdings) or 100000.0

        impacts = []
        total_loss = 0.0
        for h in holdings:
            code = h.get("fund_code", "")
            ftype = self._get_fund_type(code)
            sens = SHOCK_SENSITIVITIES.get(ftype, SHOCK_SENSITIVITIES["default"])

            # 冲击 = 权益敏感度 × 权益冲击 + 债券敏感度 × 债券冲击
            shock = sens["equity"] * equity_shock + sens["bond"] * bond_shock
            weight = h.get("weight", 0) / total_weight
            amount = h.get("amount", total_assets * weight)
            loss = amount * shock
            total_loss += loss

            impacts.append({
                "fund_code": code,
                "fund_name": h.get("name", h.get("fund_name", code)),
                "fund_type": ftype,
                "estimated_shock_pct": round(shock * 100, 2),
                "estimated_loss": round(loss, 2),
                "weight_pct": round(weight * 100, 1),
            })

        impact_pct = round(total_loss / max(total_assets, 0.01) * 100, 2)

        return {
            "scenario": f"权益市场变化{equity_shock_pct:+.1f}%, 债券市场变化{bond_shock_pct:+.1f}%",
            "total_assets_before": round(total_assets, 2),
            "total_assets_after": round(total_assets + total_loss, 2),
            "total_impact_amount": round(total_loss, 2),
            "total_impact_pct": impact_pct,
            "severity": self._severity(impact_pct),
            "holdings_impact": impacts,
            "worst_hit": max(impacts, key=lambda x: abs(x["estimated_loss"]), default={}),
            "generated_at": datetime.now().isoformat(),
        }

    # ── 2. 换仓模拟 ──────────────────────────────────────────
    def fund_swap(
        self,
        holdings: List[Dict[str, Any]],
        sell_code: str,
        buy_code: str,
        total_assets: Optional[float] = None,
    ) -> Dict[str, Any]:
        """换仓影响模拟。

        Args:
            holdings: 当前持仓
            sell_code: 要卖出的基金代码
            buy_code: 要买入的基金代码
            total_assets: 总资产
        """
        total_weight = sum(h.get("weight", 0) for h in holdings) or 1.0
        if total_assets is None:
            total_assets = sum(h.get("amount", 0) for h in holdings) or 100000.0

        sell_holding = next((h for h in holdings if h.get("fund_code") == sell_code), None)
        buy_holding = next((h for h in holdings if h.get("fund_code") == buy_code), None)

        if not sell_holding:
            return {"error": f"持仓中未找到基金 {sell_code}", "scenario": "换仓模拟"}

        sell_weight = sell_holding.get("weight", 0) / total_weight
        sell_amount = sell_holding.get("amount", total_assets * sell_weight)

        sell_type = self._get_fund_type(sell_code)
        buy_type = self._get_fund_type(buy_code)

        # v9.0: 复用 fee_calculator 计算费率（失败回退默认 0.5%/0.15%）
        sell_fee = sell_amount * 0.005
        buy_fee = sell_amount * 0.0015
        try:
            from analysis.fee_calculator import estimate_rebalance_cost
            fc = estimate_rebalance_cost(
                [{"name": sell_code, "amount": sell_amount, "fund_type": sell_type, "holding_days": 365}],
                [{"name": buy_code, "amount": sell_amount, "fund_type": buy_type}])
            if "total_fee" in fc:
                sell_fee = fc.get("sell_fee", sell_fee)
                buy_fee = fc.get("buy_fee", buy_fee)
        except Exception:
            pass
        total_fee = sell_fee + buy_fee
        # v9.0 修复: 买入金额 = 卖出净额（此前 sell_amount - sell_fee - buy_fee 双重扣费）
        net_sell = sell_amount - sell_fee
        buy_amount = max(net_sell, 0.0)

        # 估算类型变化影响
        type_change_note = ""
        if sell_type in ("股票型", "偏股混合") and buy_type in ("债券型", "纯债"):
            type_change_note = "⚠️ 从权益型切换到债券型，预期收益下降但波动降低"
        elif sell_type in ("债券型", "纯债") and buy_type in ("股票型", "偏股混合"):
            type_change_note = "⚡ 从债券型切换到权益型，预期收益上升但波动增大"

        return {
            "scenario": f"换仓: {sell_code}({sell_type}) → {buy_code}({buy_type})",
            "sell": {
                "code": sell_code,
                "name": sell_holding.get("name", sell_code),
                "type": sell_type,
                "amount": round(sell_amount, 2),
                "fee": round(sell_fee, 2),
            },
            "buy": {
                "code": buy_code,
                "name": buy_holding.get("name", buy_code) if buy_holding else buy_code,
                "type": buy_type,
                "amount": round(buy_amount, 2),
                "fee": round(buy_fee, 2),
            },
            "total_fee": round(total_fee, 2),
            "fee_pct": round(total_fee / max(sell_amount, 0.01) * 100, 2),
            "type_change": type_change_note,
            "generated_at": datetime.now().isoformat(),
        }

    # ── 3. 利率变化 ──────────────────────────────────────────
    def rate_change(
        self,
        holdings: List[Dict[str, Any]],
        rate_delta_bps: float = 100,
        total_assets: Optional[float] = None,
    ) -> Dict[str, Any]:
        """利率变化影响模拟。

        Args:
            rate_delta_bps: 利率变化（基点），100 = +1%
        """
        rate_shock = rate_delta_bps / 10000.0  # bps -> 小数

        total_weight = sum(h.get("weight", 0) for h in holdings) or 1.0
        if total_assets is None:
            total_assets = sum(h.get("amount", 0) for h in holdings) or 100000.0

        impacts = []
        total_impact = 0.0
        for h in holdings:
            code = h.get("fund_code", "")
            ftype = self._get_fund_type(code)
            sens = SHOCK_SENSITIVITIES.get(ftype, SHOCK_SENSITIVITIES["default"])
            shock = sens["rate"] * rate_shock * 100  # 转为百分比影响
            weight = h.get("weight", 0) / total_weight
            amount = h.get("amount", total_assets * weight)
            loss = amount * shock / 100
            total_impact += loss
            impacts.append({
                "fund_code": code,
                "fund_name": h.get("name", h.get("fund_name", code)),
                "fund_type": ftype,
                "rate_sensitivity": sens["rate"],
                "estimated_impact_pct": round(shock, 2),
                "estimated_impact_amount": round(loss, 2),
            })

        impact_pct = round(total_impact / max(total_assets, 0.01) * 100, 2)

        return {
            "scenario": f"利率变化 {rate_delta_bps:+d}bp",
            "total_assets_before": round(total_assets, 2),
            "total_assets_after": round(total_assets + total_impact, 2),
            "total_impact_pct": impact_pct,
            "severity": self._severity(impact_pct),
            "holdings_impact": impacts,
            "generated_at": datetime.now().isoformat(),
        }

    # ── 4. 通胀侵蚀 ──────────────────────────────────────────
    def inflation_impact(
        self,
        holdings: List[Dict[str, Any]],
        inflation_rate_pct: float = 3.0,
        years: float = 1.0,
        total_assets: Optional[float] = None,
    ) -> Dict[str, Any]:
        """通胀侵蚀模拟。

        Returns:
            实际购买力变化
        """
        if total_assets is None:
            total_assets = sum(h.get("amount", 0) for h in holdings) or 100000.0

        inflation = inflation_rate_pct / 100.0
        real_value = total_assets / ((1 + inflation) ** years)
        erosion = total_assets - real_value

        # 不同类型基金的抗通胀能力
        type_inflation_hedge = {
            "股票型": 0.30, "偏股混合": 0.25, "QDII": 0.35,
            "债券型": -0.20, "纯债": -0.30, "货币型": -0.40,
            "商品/黄金": 0.60,
        }

        total_weight = sum(h.get("weight", 0) for h in holdings) or 1.0
        hedge_score = 0.0
        for h in holdings:
            ftype = self._get_fund_type(h.get("fund_code", ""))
            w = h.get("weight", 0) / total_weight
            hedge_score += type_inflation_hedge.get(ftype, 0.0) * w

        return {
            "scenario": f"通胀率 {inflation_rate_pct}% 持续 {years} 年",
            "total_assets_nominal": round(total_assets, 2),
            "total_assets_real": round(real_value, 2),
            "purchasing_power_loss": round(erosion, 2),
            "purchasing_power_loss_pct": round(erosion / max(total_assets, 0.01) * 100, 2),
            "inflation_hedge_score": round(hedge_score, 2),
            "hedge_assessment": (
                "🟢 组合有一定抗通胀能力" if hedge_score > 0.2
                else "🟡 组合抗通胀能力一般" if hedge_score > 0
                else "🔴 组合缺乏抗通胀保护"
            ),
            "generated_at": datetime.now().isoformat(),
        }

    # ── 5. 批量情景 ──────────────────────────────────────────
    def run_scenarios(
        self,
        holdings: List[Dict[str, Any]],
        scenarios: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """运行多个预设情景。

        Args:
            scenarios: 情景名称列表（None=全部）

        Returns:
            {"results": [...], "worst_case": ..., "best_case": ...}
        """
        if scenarios is None:
            scenarios = list(SCENARIO_TEMPLATES.keys())

        results = []
        for sc_name in scenarios:
            tmpl = SCENARIO_TEMPLATES.get(sc_name)
            if not tmpl:
                continue
            params = tmpl["params"]
            stype = tmpl.get("type")
            if stype == "equity_shock":
                r = self.market_shock(
                    holdings,
                    equity_shock_pct=params.get("equity_shock", 0) * 100,
                    bond_shock_pct=params.get("bond_shock", 0) * 100,
                )
            elif stype == "rate":
                r = self.rate_change(holdings, rate_delta_bps=params["rate_delta_bps"])
            elif stype == "sector_boom":
                r = self.sector_boom(
                    holdings, sector=params.get("sector", "科技"),
                    sector_return=params.get("sector_return", 0.30),
                    other_return=params.get("other_return", 0.05))
            elif stype == "inflation":
                r = self.inflation_surge(
                    holdings, inflation_delta=params.get("inflation_delta", 0.03),
                    equity_shock=params.get("equity_shock", -0.10),
                    bond_shock=params.get("bond_shock", -0.08))
            elif stype == "currency":
                r = self.currency_devaluation(
                    holdings, fx_depreciation=params.get("fx_depreciation", 0.10),
                    qdii_return=params.get("qdii_return", 0.10),
                    domestic_shock=params.get("domestic_shock", -0.05))
            else:
                continue
            r["scenario"] = tmpl["name"]
            results.append(r)

        worst = min(results, key=lambda r: r.get("total_impact_pct", 0)) if results else {}
        best = max(results, key=lambda r: r.get("total_impact_pct", 0)) if results else {}

        return {
            "scenarios": results,
            "count": len(results),
            "worst_case": worst,
            "best_case": best,
            "generated_at": datetime.now().isoformat(),
        }

    # ── v9.0: 补充情景（sector_boom / inflation_surge / currency_devaluation） ──
    @staticmethod
    def _sector_keywords(sector: str):
        return {
            "科技": ["科技", "电子", "半导体", "计算机", "通信", "软件", "芯片"],
            "消费": ["消费", "食品", "白酒", "家电", "零售"],
            "医药": ["医药", "医疗", "生物", "健康", "疫苗"],
            "金融": ["金融", "银行", "券商", "保险", "地产"],
            "新能源": ["新能源", "光伏", "锂", "电池", "风电"],
            "高端制造": ["制造", "机械", "军工", "汽车", "半导体"],
        }.get(sector, [sector])

    def sector_boom(self, holdings, sector="科技", sector_return=0.30,
                    other_return=0.05) -> Dict[str, Any]:
        """v9.0: 板块领涨 — 命中板块的基金按 sector_return，其余按 other_return。"""
        total_weight = sum(h.get("weight", 0) for h in holdings) or 1.0
        total_assets = sum(h.get("amount", 0) for h in holdings) or 100000.0
        kws = self._sector_keywords(sector)
        impacts = []
        total_loss = 0.0
        for h in holdings:
            name = h.get("name", h.get("fund_name", ""))
            weight = h.get("weight", 0) / total_weight
            amount = h.get("amount", total_assets * weight)
            hit = any(k in str(name) for k in kws)
            ret = sector_return if hit else other_return
            loss = amount * ret
            total_loss += loss
            impacts.append({
                "fund_code": h.get("fund_code", ""),
                "fund_name": name,
                "fund_type": h.get("fund_type", ""),
                "estimated_shock_pct": round(ret * 100, 2),
                "estimated_loss": round(loss, 2),
                "weight_pct": round(weight * 100, 1),
                "in_sector": hit,
            })
        impact_pct = round(total_loss / max(total_assets, 0.01) * 100, 2)
        return {
            "scenario": f"板块「{sector}」领涨 {sector_return * 100:.0f}%",
            "total_assets_before": round(total_assets, 2),
            "total_assets_after": round(total_assets + total_loss, 2),
            "total_impact_amount": round(total_loss, 2),
            "total_impact_pct": impact_pct,
            "severity": self._severity(impact_pct),
            "holdings_impact": impacts,
            "worst_hit": max(impacts, key=lambda x: abs(x["estimated_loss"]), default={}),
            "generated_at": datetime.now().isoformat(),
        }

    def inflation_surge(self, holdings, inflation_delta=0.03,
                        equity_shock=-0.10, bond_shock=-0.08) -> Dict[str, Any]:
        """v9.0: 通胀上升 — 名义冲击 + 购买力侵蚀。"""
        base = self.market_shock(holdings, equity_shock_pct=equity_shock * 100,
                                 bond_shock_pct=bond_shock * 100)
        erosion = inflation_delta
        base["total_impact_pct"] = round(base["total_impact_pct"] - erosion * 100, 2)
        base["scenario"] = f"通胀上升 {inflation_delta * 100:.0f}pp（含购买力侵蚀 {erosion * 100:.1f}%）"
        base["severity"] = self._severity(base["total_impact_pct"])
        base["total_assets_after"] = round(
            base["total_assets_before"] * (1 + base["total_impact_pct"] / 100), 2)
        return base

    def currency_devaluation(self, holdings, fx_depreciation=0.10,
                             qdii_return=0.10, domestic_shock=-0.05) -> Dict[str, Any]:
        """v9.0: 汇率贬值 — QDII 受益，国内资产按 fx 敏感度承压。"""
        total_weight = sum(h.get("weight", 0) for h in holdings) or 1.0
        total_assets = sum(h.get("amount", 0) for h in holdings) or 100000.0
        impacts = []
        total_loss = 0.0
        for h in holdings:
            code = h.get("fund_code", "")
            ftype = self._get_fund_type(code)
            sens = SHOCK_SENSITIVITIES.get(ftype, SHOCK_SENSITIVITIES["default"])
            ret = qdii_return if (ftype == "QDII" or sens.get("fx", 0) >= 0.5) \
                else sens["equity"] * domestic_shock
            weight = h.get("weight", 0) / total_weight
            amount = h.get("amount", total_assets * weight)
            loss = amount * ret
            total_loss += loss
            impacts.append({
                "fund_code": code, "fund_name": h.get("name", h.get("fund_name", code)),
                "fund_type": ftype, "estimated_shock_pct": round(ret * 100, 2),
                "estimated_loss": round(loss, 2), "weight_pct": round(weight * 100, 1),
            })
        impact_pct = round(total_loss / max(total_assets, 0.01) * 100, 2)
        return {
            "scenario": f"人民币贬值 {fx_depreciation * 100:.0f}%（QDII 受益，国内承压）",
            "total_assets_before": round(total_assets, 2),
            "total_assets_after": round(total_assets + total_loss, 2),
            "total_impact_amount": round(total_loss, 2),
            "total_impact_pct": impact_pct,
            "severity": self._severity(impact_pct),
            "holdings_impact": impacts,
            "worst_hit": max(impacts, key=lambda x: abs(x["estimated_loss"]), default={}),
            "generated_at": datetime.now().isoformat(),
        }

    def list_scenarios(self) -> List[Dict[str, Any]]:
        """列出所有可用情景模板。"""
        return [
            {
                "key": k,
                "name": v["name"],
                "description": v["description"],
                "params": v["params"],
            }
            for k, v in SCENARIO_TEMPLATES.items()
        ]

    # ── 工具方法 ─────────────────────────────────────────────
    def _get_fund_type(self, code: str) -> str:
        """获取基金类型。"""
        fund = self.funds_db.get(code, {})
        return fund.get("type", fund.get("fund_type", "default"))

    @staticmethod
    def _severity(impact_pct: float) -> str:
        """影响严重度评级。"""
        abs_pct = abs(impact_pct)
        if abs_pct <= 2:
            return "🟢 轻微"
        elif abs_pct <= 5:
            return "🟡 中等"
        elif abs_pct <= 10:
            return "🟠 严重"
        else:
            return "🔴 重大"


# 模块级单例
_simulator_instance: Optional[ScenarioSimulator] = None


def get_simulator() -> ScenarioSimulator:
    """获取 ScenarioSimulator 单例。"""
    global _simulator_instance
    if _simulator_instance is None:
        _simulator_instance = ScenarioSimulator()
    return _simulator_instance
