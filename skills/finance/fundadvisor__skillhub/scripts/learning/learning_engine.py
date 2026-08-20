#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""自进化学习引擎 (v7.0 新增)

学习闭环：记录建议 → 事后回填 → 统计命中 → 校准参数 → 更新规则库 → 下次建议用新参数

数据文件（数据目录可注入，优先级：构造参数 > 环境变量 FUND_ADVISOR_LEARNING_DIR > DATA_DIR/learning）：
- advice_log.jsonl  每行一条建议记录
- outcomes.jsonl    事后回填的实际表现
- calibration.json  学习得到的阈值参数
- playbook.json     策略规则库（首次运行从 playbook_default.json 拷贝）

纯标准库；所有网络调用 try/except 优雅降级；jsonl 一律 append 写入。
"""
from __future__ import annotations

import sys
import os
import json
import shutil
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional

_SCRIPTS = Path(__file__).resolve().parents[1]
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))
sys.path.insert(0, str(_SCRIPTS / "data_collection"))

from fund_advisor_paths import DATA_DIR  # noqa: E402

# 动作方向分组：决定 hit 判定方向
SELL_ACTIONS = {"减持", "减持止盈", "止盈", "止损", "评估止损", "清仓", "考虑转换", "转换", "替换出", "卖出"}
BUY_ACTIONS = {"增持", "买入", "持有", "加仓", "定投", "新增"}

# 校准参数上下限（保守约束）
PARAM_BOUNDS = {
    "profit_take_threshold": (20.0, 50.0),   # 止盈线 %
    "stop_loss_threshold": (-30.0, -10.0),   # 止损线 %
    "drift_threshold": (3.0, 10.0),          # 漂移阈值 %
    "min_confidence": (0.5, 0.9),            # 建议最低置信度
}

DEFAULT_CALIBRATION = {
    "profit_take_threshold": 30.0,
    "stop_loss_threshold": -20.0,
    "drift_threshold": 5.0,
    "min_confidence": 0.6,
    "rating_weights": {"morningstar": 0.30, "howbuy": 0.25, "jiucaiban": 0.20,
                       "xueqiu": 0.15, "eastmoney": 0.10},
    "updated_at": "",
    "stats": {},
    "adjust_log": [],
}

EVAL_HORIZON_DAYS = 30  # 建议评估窗口（天）


class LearningEngine:
    """自进化学习引擎

    用法:
        le = LearningEngine()                      # 默认数据目录 data/learning
        le = LearningEngine(data_dir="/tmp/x")     # 注入数据目录（测试用）
        aid = le.log_advice("张三", "rebalance", "110022", "减持止盈", ["收益超30%"])
        le.record_outcome(aid, 30, -5.0, 2.0)      # 30天后基金-5%，基准+2%
        le.compute_stats(); le.calibrate(); le.playbook_update()
    """

    def __init__(self, data_dir: Optional[str] = None):
        env = os.environ.get("FUND_ADVISOR_LEARNING_DIR")
        self.data_dir = Path(data_dir or env or (DATA_DIR / "learning"))
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.advice_log_path = self.data_dir / "advice_log.jsonl"
        self.outcomes_path = self.data_dir / "outcomes.jsonl"
        self.calibration_path = self.data_dir / "calibration.json"
        self.playbook_path = self.data_dir / "playbook.json"
        self._ensure_playbook()

    # ─── 文件读写基础 ─────────────────────────────────────
    def _ensure_playbook(self) -> None:
        """首次运行：playbook.json 不存在则从默认模板拷贝"""
        if not self.playbook_path.exists():
            default = Path(__file__).resolve().parent / "playbook_default.json"
            try:
                shutil.copyfile(str(default), str(self.playbook_path))
            except Exception:
                # 模板缺失时写入空骨架，保证后续读不炸
                self._write_json(self.playbook_path, {"version": "7.0", "rules": []})

    @staticmethod
    def _append_jsonl(path: Path, record: Dict) -> None:
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    @staticmethod
    def _read_jsonl(path: Path) -> List[Dict]:
        if not path.exists():
            return []
        out = []
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    out.append(json.loads(line))
                except json.JSONDecodeError:
                    continue  # 跳过坏行
        return out

    @staticmethod
    def _read_json(path: Path, default):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return default

    @staticmethod
    def _write_json(path: Path, data) -> None:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def load_calibration(self) -> Dict:
        """读取当前校准参数（缺失时用默认值补齐）"""
        cal = dict(DEFAULT_CALIBRATION)
        stored = self._read_json(self.calibration_path, {})
        if isinstance(stored, dict):
            cal.update({k: v for k, v in stored.items() if v is not None})
        return cal

    # ─── 1. 记录建议 ──────────────────────────────────────
    def log_advice(self, client_id: str, kind: str, target: str, action: str,
                   reasons: List[str], confidence: float = 0.6,
                   context: Optional[Dict] = None,
                   provider=None) -> str:
        """记录一条投顾建议，返回 advice_id

        advice_id 规则：yyyymmdd-序号(当日第几条，3位)。
        会尝试记录 target 当前净值 nav_at_log（供 auto_evaluate 用），失败则为 None。
        """
        now = datetime.now()
        day = now.strftime("%Y%m%d")
        today_count = sum(1 for a in self._read_jsonl(self.advice_log_path)
                          if str(a.get("advice_id", "")).startswith(day))
        advice_id = f"{day}-{today_count + 1:03d}"
        nav_at_log = None
        if target:
            nav_at_log = self._try_get_nav(target, provider)
        record = {
            "advice_id": advice_id,
            "ts": now.strftime("%Y-%m-%d %H:%M:%S"),
            "client_id": client_id,
            "kind": kind,
            "target": target,
            "action": action,
            "confidence": round(float(confidence), 3),
            "reasons": list(reasons or []),
            "context": context or {},
            "params_used": self._params_snapshot(),
            "nav_at_log": nav_at_log,
        }
        self._append_jsonl(self.advice_log_path, record)
        # 规则使用计数
        self._bump_rule_uses(action)
        return advice_id

    def _params_snapshot(self) -> Dict:
        """记录建议时使用的阈值参数快照（供事后审计）"""
        cal = self.load_calibration()
        return {k: cal.get(k) for k in
                ("profit_take_threshold", "stop_loss_threshold", "drift_threshold", "min_confidence")}

    def _try_get_nav(self, code: str, provider=None) -> Optional[float]:
        """尽力获取基金当前净值（网络调用全部 try/except）"""
        try:
            p = provider
            if p is None:
                from multi_source import get_provider
                p = get_provider()
            r = p.get_fund_nav(code)
            nav = r.get("nav")
            if isinstance(nav, dict):
                nav = nav.get("nav")
            return float(nav) if nav else None
        except Exception:
            return None

    # ─── 2. 事后回填 ──────────────────────────────────────
    @staticmethod
    def _eval_hit(action: str, fund_return: float, benchmark_return: float):
        """hit 判定规则（方向清晰）：

        - 卖出类（减持/止盈/止损/转换出）：horizon 内 fund_return < benchmark_return
          说明"不操作会更差"，建议正确 -> hit=True；
          action_benefit = benchmark_return - fund_return（避免损失的幅度）
        - 买入/持有类：fund_return > benchmark_return -> hit=True；
          action_benefit = fund_return - benchmark_return
        - 其他动作：以 fund_return > benchmark_return 记 hit。
        """
        if action in SELL_ACTIONS:
            hit = fund_return < benchmark_return
            benefit = benchmark_return - fund_return
        else:  # 买入/持有类及其他
            hit = fund_return > benchmark_return
            benefit = fund_return - benchmark_return
        return hit, round(benefit, 4)

    def record_outcome(self, advice_id: str, horizon_days: int,
                       fund_return: float, benchmark_return: float) -> Dict:
        """回填一条建议的实际结果，写入 outcomes.jsonl

        参数收益单位为 %。返回写入的 outcome 记录。
        """
        advice = next((a for a in self._read_jsonl(self.advice_log_path)
                       if a.get("advice_id") == advice_id), None)
        if advice is None:
            return {"error": f"未找到建议记录: {advice_id}"}
        if any(o.get("advice_id") == advice_id for o in self._read_jsonl(self.outcomes_path)):
            return {"error": f"建议 {advice_id} 已回填过，忽略重复"}
        hit, benefit = self._eval_hit(advice.get("action", ""), fund_return, benchmark_return)
        outcome = {
            "advice_id": advice_id,
            "eval_ts": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "horizon_days": int(horizon_days),
            "fund_return": round(float(fund_return), 4),
            "benchmark_return": round(float(benchmark_return), 4),
            "action_benefit": benefit,
            "hit": bool(hit),
        }
        self._append_jsonl(self.outcomes_path, outcome)
        return outcome

    def auto_evaluate_pending(self, provider=None) -> Dict:
        """自动回填超过 30 天未评估的建议

        用多源 provider 拉取 target 当前净值，与 log 时的 nav_at_log 对比得到
        fund_return；基准尽力取沪深300指数同期涨跌，失败则按 0 处理。
        网络失败跳过并计数，不抛异常。
        """
        advices = self._read_jsonl(self.advice_log_path)
        done_ids = {o.get("advice_id") for o in self._read_jsonl(self.outcomes_path)}
        now = datetime.now()
        result = {"evaluated": 0, "skipped_not_due": 0, "skipped_no_nav": 0,
                  "skipped_network": 0, "details": []}
        p = provider
        for a in advices:
            aid = a.get("advice_id")
            if aid in done_ids:
                continue
            try:
                ts = datetime.strptime(a.get("ts", ""), "%Y-%m-%d %H:%M:%S")
            except ValueError:
                result["skipped_no_nav"] += 1
                continue
            days = (now - ts).days
            if days < EVAL_HORIZON_DAYS:
                result["skipped_not_due"] += 1
                continue
            nav0 = a.get("nav_at_log")
            target = a.get("target", "")
            if not nav0 or not target:
                result["skipped_no_nav"] += 1
                continue
            try:
                if p is None:
                    from multi_source import get_provider
                    p = get_provider()
                nav1 = self._try_get_nav(target, p)
                if not nav1:
                    result["skipped_network"] += 1
                    continue
                fund_ret = (nav1 / nav0 - 1.0) * 100.0
                bench_ret = self._try_benchmark_return(days, p)
                oc = self.record_outcome(aid, days, fund_ret, bench_ret)
                if "error" in oc:
                    result["skipped_no_nav"] += 1
                else:
                    result["evaluated"] += 1
                    result["details"].append({"advice_id": aid, "hit": oc["hit"],
                                              "fund_return": oc["fund_return"]})
            except Exception:
                result["skipped_network"] += 1
        return result

    def _try_benchmark_return(self, days: int, provider) -> float:
        """尽力取基准（沪深300）同期收益%，失败返回 0.0"""
        try:
            r = provider.get_fund_nav("000300")  # 部分源支持指数代码
            nav = r.get("nav")
            if isinstance(nav, dict):
                chg = nav.get("change_pct")
                if chg is not None:
                    return float(chg)  # 仅有当日涨跌时的近似
        except Exception:
            pass
        return 0.0

    # ─── 3. 统计命中 ──────────────────────────────────────
    def compute_stats(self) -> Dict:
        """按 kind / action 分组统计命中率与平均 benefit"""
        advices = {a.get("advice_id"): a for a in self._read_jsonl(self.advice_log_path)}
        outcomes = [o for o in self._read_jsonl(self.outcomes_path)
                    if o.get("advice_id") in advices]

        def group_stats(key_fn):
            groups: Dict[str, Dict] = {}
            for o in outcomes:
                a = advices[o["advice_id"]]
                k = key_fn(a)
                g = groups.setdefault(k, {"samples": 0, "hits": 0, "benefits": []})
                g["samples"] += 1
                g["hits"] += 1 if o.get("hit") else 0
                g["benefits"].append(o.get("action_benefit", 0.0))
            for g in groups.values():
                g["win_rate"] = round(g["hits"] / g["samples"] * 100.0, 1) if g["samples"] else None
                g["avg_benefit"] = round(sum(g["benefits"]) / len(g["benefits"]), 3) if g["benefits"] else None
                del g["benefits"]
            return groups

        total = len(outcomes)
        hits = sum(1 for o in outcomes if o.get("hit"))
        return {
            "total_advice": len(advices),
            "evaluated": total,
            "overall_win_rate": round(hits / total * 100.0, 1) if total else None,
            "by_kind": group_stats(lambda a: a.get("kind", "other")),
            "by_action": group_stats(lambda a: a.get("action", "其他")),
            "computed_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }

    # ─── 4. 参数校准 ──────────────────────────────────────
    @staticmethod
    def _clamp(param: str, value: float) -> float:
        lo, hi = PARAM_BOUNDS[param]
        return max(lo, min(hi, value))

    def calibrate(self) -> Dict:
        """根据命中统计校准阈值参数（保守规则，单次调整幅度 <=5）

        规则:
        - 止盈类（减持止盈）命中率 <40% 且样本>=5 -> profit_take_threshold +5
          （止盈太频繁/太早，提高门槛）；>70% -> -5
        - 止损类（评估止损）命中率 <40% 且样本>=5 -> stop_loss_threshold -5
          （放宽止损线，减少误杀）；>70% -> +5（收紧）
        - 再平衡类命中率 <40% 且样本>=5 -> drift_threshold +1；>70% -> -1
        - 整体命中率 <50% 且样本>=10 -> min_confidence +0.05；>70% -> -0.05
        所有参数受 PARAM_BOUNDS 上下限约束。
        """
        stats = self.compute_stats()
        cal = self.load_calibration()
        reasons: List[str] = []

        def adjust(param: str, delta: float, reason: str):
            old = float(cal.get(param, DEFAULT_CALIBRATION[param]))
            new = self._clamp(param, old + delta)
            if abs(new - old) > 1e-9:
                cal[param] = round(new, 4)
                reasons.append(f"{reason}: {param} {old} -> {new}")

        by_action = stats.get("by_action", {})
        take_profit = by_action.get("减持止盈", {})
        if take_profit.get("samples", 0) >= 5:
            wr = take_profit.get("win_rate") or 0
            if wr < 40:
                adjust("profit_take_threshold", 5, f"止盈建议命中率仅{wr}%(<40%)，提高止盈门槛")
            elif wr > 70:
                adjust("profit_take_threshold", -5, f"止盈建议命中率{wr}%(>70%)，可适度降低门槛")
        stop_loss = by_action.get("评估止损", {})
        if stop_loss.get("samples", 0) >= 5:
            wr = stop_loss.get("win_rate") or 0
            if wr < 40:
                adjust("stop_loss_threshold", -5, f"止损建议命中率仅{wr}%(<40%)，放宽止损线减少误杀")
            elif wr > 70:
                adjust("stop_loss_threshold", 5, f"止损建议命中率{wr}%(>70%)，可适度收紧")
        reb = stats.get("by_kind", {}).get("rebalance", {})
        if reb.get("samples", 0) >= 5:
            wr = reb.get("win_rate") or 0
            if wr < 40:
                adjust("drift_threshold", 1, f"再平衡类命中率仅{wr}%(<40%)，提高漂移阈值")
            elif wr > 70:
                adjust("drift_threshold", -1, f"再平衡类命中率{wr}%(>70%)，可更灵敏")
        if stats.get("evaluated", 0) >= 10:
            owr = stats.get("overall_win_rate") or 0
            if owr < 50:
                adjust("min_confidence", 0.05, f"整体命中率{owr}%(<50%)，提高建议置信度门槛")
            elif owr > 70:
                adjust("min_confidence", -0.05, f"整体命中率{owr}%(>70%)，可放宽置信度门槛")

        cal["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cal["stats"] = {"overall_win_rate": stats.get("overall_win_rate"),
                        "evaluated": stats.get("evaluated")}
        log = cal.get("adjust_log") or []
        if reasons:
            log.append({"ts": cal["updated_at"], "reasons": reasons})
        cal["adjust_log"] = log[-20:]  # 只留最近 20 次
        self._write_json(self.calibration_path, cal)
        return {"calibration": cal, "adjustments": reasons,
                "note": "无满足条件的调整规则" if not reasons else f"共 {len(reasons)} 项调整"}

    # ─── 5. 规则库更新 ────────────────────────────────────
    def _bump_rule_uses(self, action: str) -> None:
        """log_advice 时给匹配规则 uses +1"""
        pb = self._read_json(self.playbook_path, {"rules": []})
        changed = False
        for rule in pb.get("rules", []):
            cond = rule.get("condition", {})
            if rule.get("action") == action or cond.get("action") == action:
                rule.setdefault("stats", {}).setdefault("uses", 0)
                rule["stats"]["uses"] += 1
                changed = True
        if changed:
            self._write_json(self.playbook_path, pb)

    def playbook_update(self) -> Dict:
        """按规则命中统计更新 playbook：胜率过低停用，胜率高的强化

        规则 stats 从 advice_log + outcomes 重新聚合（按 action 匹配）：
        - win_rate < 35% 且 evaluated >= 5 -> enabled=false（记录停用原因）
        - win_rate > 70% 且 evaluated >= 5 -> 保持启用并标记"强化"
        """
        stats = self.compute_stats()
        by_action = stats.get("by_action", {})
        pb = self._read_json(self.playbook_path, {"rules": []})
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        changes: List[str] = []
        for rule in pb.get("rules", []):
            key = rule.get("action") or rule.get("condition", {}).get("action", "")
            g = by_action.get(key, {})
            st = rule.setdefault("stats", {})
            st["evaluated"] = g.get("samples", 0)
            st["hits"] = g.get("hits", 0)
            st["win_rate"] = g.get("win_rate")
            st["avg_benefit"] = g.get("avg_benefit")
            st.setdefault("uses", 0)
            if st["evaluated"] >= 5 and st["win_rate"] is not None:
                if st["win_rate"] < 35 and rule.get("enabled", True):
                    rule["enabled"] = False
                    rule["disable_reason"] = f"胜率{st['win_rate']}%<35%(样本{st['evaluated']})，自动停用"
                    changes.append(f"停用 {rule['rule_id']} {rule['name']}: {rule['disable_reason']}")
                elif st["win_rate"] > 70 and rule.get("enabled", True):
                    rule["reinforced"] = True
                    changes.append(f"强化 {rule['rule_id']} {rule['name']}: 胜率{st['win_rate']}%")
            rule["last_updated"] = now
        self._write_json(self.playbook_path, pb)
        enabled = sum(1 for r in pb.get("rules", []) if r.get("enabled"))
        return {"changes": changes, "enabled": enabled,
                "disabled": len(pb.get("rules", [])) - enabled,
                "note": "无变化" if not changes else f"{len(changes)} 项更新"}

    def add_rule(self, name: str, condition: Dict, action: str, enabled: bool = True) -> Dict:
        """手工加入新规则，返回新规则 dict"""
        pb = self._read_json(self.playbook_path, {"rules": []})
        existing = [r.get("rule_id", "") for r in pb.get("rules", [])]
        seq = len(existing) + 1
        rule_id = f"R{seq:03d}"
        while rule_id in existing:
            seq += 1
            rule_id = f"R{seq:03d}"
        rule = {
            "rule_id": rule_id,
            "name": name,
            "condition": condition,
            "action": action,
            "enabled": bool(enabled),
            "stats": {"uses": 0, "evaluated": 0, "hits": 0, "win_rate": None, "avg_benefit": None},
            "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        pb.setdefault("rules", []).append(rule)
        self._write_json(self.playbook_path, pb)
        return rule

    # ─── 6. 学习报告 / 参数应用 ────────────────────────────
    def get_learning_report(self) -> Dict:
        """汇总学习状态：样本量/命中率/分组统计/校准参数/规则库/最近建议"""
        stats = self.compute_stats()
        cal = self.load_calibration()
        pb = self._read_json(self.playbook_path, {"rules": []})
        advices = self._read_jsonl(self.advice_log_path)
        outcomes = {o.get("advice_id"): o for o in self._read_jsonl(self.outcomes_path)}
        recent = []
        for a in advices[-10:]:
            oc = outcomes.get(a.get("advice_id"))
            recent.append({
                "advice_id": a.get("advice_id"), "ts": a.get("ts"),
                "kind": a.get("kind"), "target": a.get("target"),
                "action": a.get("action"), "confidence": a.get("confidence"),
                "evaluated": oc is not None,
                "hit": oc.get("hit") if oc else None,
                "action_benefit": oc.get("action_benefit") if oc else None,
            })
        rules = pb.get("rules", [])
        enabled = [r for r in rules if r.get("enabled")]
        return {
            "样本量": stats["total_advice"],
            "已评估": stats["evaluated"],
            "整体命中率": stats["overall_win_rate"],
            "分组统计": {"by_kind": stats["by_kind"], "by_action": stats["by_action"]},
            "当前校准参数": {k: cal.get(k) for k in
                           ("profit_take_threshold", "stop_loss_threshold",
                            "drift_threshold", "min_confidence", "rating_weights")},
            "calibration_updated_at": cal.get("updated_at"),
            "playbook": {"规则总数": len(rules), "启用": len(enabled),
                         "停用": len(rules) - len(enabled),
                         "rules": [{"rule_id": r.get("rule_id"), "name": r.get("name"),
                                    "enabled": r.get("enabled"),
                                    "win_rate": r.get("stats", {}).get("win_rate")}
                                   for r in rules]},
            "最近建议": recent,
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }

    def apply_calibration(self, params: Dict) -> Dict:
        """用 calibration.json 覆盖传入的默认参数（供 rebalancer 等模块调用）

        只覆盖 calibration 中存在的同名键，其余原样保留。
        """
        cal = self.load_calibration()
        merged = dict(params or {})
        for k in ("profit_take_threshold", "stop_loss_threshold",
                  "drift_threshold", "min_confidence", "rating_weights"):
            if k in cal and cal[k] is not None:
                merged[k] = cal[k]
        return merged


if __name__ == "__main__":
    # 演示（离线安全：在临时目录中跑全链路，不污染真实数据目录）
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        le = LearningEngine(data_dir=td)
        aid1 = le.log_advice("demo_client", "rebalance", "110022", "减持止盈",
                             ["累计收益超30%"], confidence=0.7)
        aid2 = le.log_advice("demo_client", "risk_alert", "510300", "评估止损",
                             ["累计亏损超20%"], confidence=0.8)
        print("记录建议:", aid1, aid2)
        print("回填:", le.record_outcome(aid1, 30, -5.0, 2.0))
        print("回填:", le.record_outcome(aid2, 30, -8.0, 1.0))
        import json as _json
        print(_json.dumps(le.compute_stats(), ensure_ascii=False, indent=2))
        print(_json.dumps(le.get_learning_report()["playbook"], ensure_ascii=False, indent=2)[:600])
        print("演示完成（临时目录已自动清理）")
