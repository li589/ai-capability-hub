#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""预测追踪器 (v4.0.0 新增)

记录每次预测输出 (维度/周期/方向/幅度)，在周期结束后解析实际结果，
计算命中率 (方向匹配 + 幅度误差)，按模型/周期/窗口分维度统计。
持久化: data/evolution/predictions.jsonl (追加JSONL)
"""
from __future__ import annotations
import sys, json, time
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, field
import uuid

SKILL_DIR = Path(__file__).resolve().parents[3]
EVO_DIR = SKILL_DIR / "data" / "evolution"
EVO_DIR.mkdir(parents=True, exist_ok=True)

# K线获取（用于解析实际结果）
sys.path.insert(0, str(SKILL_DIR / "scripts"))


@dataclass
class PredictionRecord:
    pred_id: str
    target_type: str       # stock/sector
    code: str
    horizon: str           # 1d/3d/5d/1M/1Q
    source_model: str      # "multi_horizon_forecaster" / "ml_1d" etc
    predicted_direction: str
    predicted_pct: float
    confidence: float
    timestamp: str
    status: str = "pending"       # pending/resolved
    actual_pct: Optional[float] = None
    hit: Optional[bool] = None    # None=unresolved True/False
    direction_match: Optional[bool] = None
    resolved_at: Optional[str] = None


class PredictionTracker:
    def __init__(self):
        self._file = EVO_DIR / "predictions.jsonl"

    def log(self, record: PredictionRecord):
        with open(self._file, "a", encoding="utf-8") as f:
            f.write(json.dumps(record.__dict__, ensure_ascii=False, default=str) + "\n")

    def new_record(
        self, target_type: str, code: str, horizon: str,
        source_model: str, direction: str, predicted_pct: float, confidence: float
    ) -> PredictionRecord:
        r = PredictionRecord(
            pred_id=str(uuid.uuid4())[:12],
            target_type=target_type, code=code, horizon=horizon,
            source_model=source_model, predicted_direction=direction,
            predicted_pct=predicted_pct, confidence=confidence,
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        )
        self.log(r)
        return r

    def resolve_pending(self) -> int:
        """解析所有pending预测：读取实际价格 → 判定命中"""
        resolved = 0
        records = self._read_all()
        now = datetime.now()

        for rec in records:
            if rec.status != "pending":
                continue
            # 判断周期是否已过期
            horizon_days = {"1d": 1, "3d": 3, "5d": 5, "1M": 22, "1Q": 66}
            days = horizon_days.get(rec.horizon, 5)
            ts = None
            try:
                ts = datetime.strptime(rec.timestamp[:10], "%Y-%m-%d")
            except Exception:
                continue
            if (now - ts).days < days:
                continue  # 尚未到期

            # 获取实际涨跌幅
            actual = self._fetch_actual(rec.code, ts, days)
            if actual is None:
                continue

            rec.actual_pct = round(actual, 3)
            rec.status = "resolved"
            rec.resolved_at = now.strftime("%Y-%m-%d %H:%M:%S")

            # 方向命中的宽松定义
            want_up = rec.predicted_direction in ("看多", "分歧偏多", "增持")
            want_down = rec.predicted_direction in ("看空", "分歧偏空", "减持")
            if want_up and actual > 0:
                rec.direction_match = True; rec.hit = True
            elif want_down and actual < 0:
                rec.direction_match = True; rec.hit = True
            elif abs(actual) < 0.5 and abs(rec.predicted_pct) < 1:
                rec.direction_match = True; rec.hit = True  # 震荡命中
            else:
                rec.direction_match = False; rec.hit = False
            resolved += 1

        if resolved > 0:
            self._write_all(records)
        return resolved

    def accuracy_report(self, model: str = None, horizon: str = None,
                         window_days: int = 90) -> Dict:
        """准确率报告"""
        records = self._read_all()
        cutoff = datetime.now() - timedelta(days=window_days)

        filtered = []
        for r in records:
            if r.status != "resolved" or r.hit is None:
                continue
            try:
                ts = datetime.strptime(r.timestamp[:10], "%Y-%m-%d")
            except Exception:
                continue
            if ts < cutoff:
                continue
            if model and model not in r.source_model:
                continue
            if horizon and r.horizon != horizon:
                continue
            filtered.append(r)

        total = len(filtered)
        hits = sum(1 for r in filtered if r.hit)
        hit_rate = round(hits / total * 100, 1) if total > 0 else 0

        # 按周期/模型细分
        by_horizon = {}
        by_model = {}
        for r in filtered:
            by_horizon.setdefault(r.horizon, {"total": 0, "hits": 0})
            by_horizon[r.horizon]["total"] += 1
            if r.hit:
                by_horizon[r.horizon]["hits"] += 1
            by_model.setdefault(r.source_model, {"total": 0, "hits": 0})
            by_model[r.source_model]["total"] += 1
            if r.hit:
                by_model[r.source_model]["hits"] += 1

        hor_rates = {h: round(v["hits"] / v["total"] * 100, 1) if v["total"] else 0
                     for h, v in by_horizon.items()}
        mod_rates = {m: round(v["hits"] / v["total"] * 100, 1) if v["total"] else 0
                     for m, v in by_model.items()}

        return {
            "window_days": window_days, "total_predictions": total,
            "hits": hits, "hit_rate_pct": hit_rate,
            "by_horizon": hor_rates, "by_model": mod_rates,
        }

    def _fetch_actual(self, code: str, pred_date: datetime, days: int) -> Optional[float]:
        """获取预测日后 N 天的实际涨跌幅"""
        try:
            from stock_researcher.data.market import MarketData
            kline = MarketData().fetch_history(code, days=days + 30)
            closes = kline.get("closes", [])
            if len(closes) < days + 2:
                return None
            pred_close = closes[-(days + 1)]
            actual_close = closes[-1]
            if pred_close <= 0:
                return None
            return (actual_close - pred_close) / pred_close * 100
        except Exception:
            return None

    def _read_all(self) -> List[PredictionRecord]:
        records = []
        if not self._file.exists():
            return records
        with open(self._file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    d = json.loads(line)
                    records.append(PredictionRecord(**d))
                except Exception:
                    continue
        return records

    def _write_all(self, records: List[PredictionRecord]):
        with open(self._file, "w", encoding="utf-8") as f:
            for r in records:
                f.write(json.dumps(r.__dict__, ensure_ascii=False, default=str) + "\n")
