#!/usr/bin/env python3
"""Persist and drive a multi-round invalidity-evidence search goal.

The controller intentionally does not call PatSeek itself. It makes each search
action, returned PID set, evidence gain, and next hypothesis durable so an
agent can resume after a pause without repeating a fixed number of rounds.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


STATE_NAME = "goal_state.json"
EVENTS_NAME = "goal_events.jsonl"
VALID_LANES = {
    "qx",
    "qy_base",
    "qy_comp",
    "semantic",
    "world",
    "family_citation",
    "detail",
    "source_gap",
}
VALID_ACTION_STATES = {"pending", "running", "completed", "failed", "skipped"}
DEFAULT_REQUIRED_LANES = ["qx", "qy_base", "world", "semantic", "detail"]
GAIN_FIELDS = (
    "new_candidates",
    "new_high_coverage",
    "new_decisive_evidence",
    "new_pivots",
    "new_ipcs",
    "new_family_citation",
)


def _now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValueError(f"missing file: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid JSON: {path}: {exc}") from exc


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "w", encoding="utf-8", dir=path.parent, delete=False
    ) as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
        temp_path = Path(handle.name)
    temp_path.replace(path)


def _state_path(case_dir: Path) -> Path:
    return case_dir / STATE_NAME


def _load_state(case_dir: Path) -> dict[str, Any]:
    state = _read_json(_state_path(case_dir))
    if not isinstance(state, dict) or state.get("schema_version") not in {"1.0", "1.1"}:
        raise ValueError("unsupported or malformed goal_state.json")
    _backfill_state(state)
    return state


def _backfill_state(state: dict[str, Any]) -> None:
    """Ensure fields introduced in schema 1.1 exist on states created under 1.0."""
    state.setdefault("feature_coverage", {})
    sat = state.setdefault("saturation", {"zero_gain_cycles": 0, "recommendation": "continue"})
    sat.setdefault("zero_gain_cycles", 0)
    sat.setdefault("zero_decisive_cycles", 0)
    sat.setdefault("recommendation", "continue")
    state.setdefault("cost", {"credits_spent": 0, "credits_remaining": None})


def _save_state(case_dir: Path, state: dict[str, Any]) -> None:
    state["updated_at"] = _now()
    _write_json(_state_path(case_dir), state)


def _append_event(case_dir: Path, event_type: str, **payload: Any) -> None:
    event = {"at": _now(), "type": event_type, **payload}
    with (case_dir / EVENTS_NAME).open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, ensure_ascii=False, sort_keys=True))
        handle.write("\n")


def _normalise_action(raw: Any) -> dict[str, Any]:
    if not isinstance(raw, dict):
        raise ValueError("action must be a JSON object")
    lane = str(raw.get("lane") or "").strip()
    action_type = str(raw.get("action_type") or "").strip()
    hypothesis = str(raw.get("hypothesis") or "").strip()
    if lane not in VALID_LANES:
        raise ValueError(f"lane must be one of: {', '.join(sorted(VALID_LANES))}")
    if not action_type:
        raise ValueError("action_type is required")
    if not hypothesis:
        raise ValueError("hypothesis is required")
    priority = int(raw.get("priority", 50))
    if not 0 <= priority <= 100:
        raise ValueError("priority must be between 0 and 100")
    parent_ids = [str(item) for item in raw.get("parent_ids") or []]
    features = [str(item).strip() for item in raw.get("features") or [] if str(item).strip()]
    return {
        "lane": lane,
        "action_type": action_type,
        "hypothesis": hypothesis,
        "query": str(raw.get("query") or "").strip(),
        "market": str(raw.get("market") or "").strip(),
        "priority": priority,
        "parent_ids": parent_ids,
        "features": features,
        "expected_gain": str(raw.get("expected_gain") or "").strip(),
        "required": bool(raw.get("required", False)),
        "notes": str(raw.get("notes") or "").strip(),
    }


def _action_fingerprint(action: dict[str, Any]) -> str:
    key = {
        name: action.get(name)
        for name in ("lane", "action_type", "hypothesis", "query", "market", "parent_ids")
    }
    text = json.dumps(key, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def _enqueue(state: dict[str, Any], raw: Any) -> tuple[dict[str, Any], bool]:
    action = _normalise_action(raw)
    action["fingerprint"] = _action_fingerprint(action)
    for existing in state["frontier"]:
        if existing["fingerprint"] == action["fingerprint"]:
            return existing, False
    action["id"] = f"A{state['next_action_number']:04d}"
    state["next_action_number"] += 1
    action.update({"status": "pending", "created_at": _now(), "result": None})
    state["frontier"].append(action)
    return action, True


def _find_action(state: dict[str, Any], action_id: str) -> dict[str, Any]:
    for action in state["frontier"]:
        if action["id"] == action_id:
            return action
    raise ValueError(f"unknown action id: {action_id}")


def _pid_list(value: Any, field: str) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, list):
        raise ValueError(f"{field} must be a list")
    result: list[str] = []
    for item in value:
        pid = str(item.get("pid") if isinstance(item, dict) else item).strip()
        if pid and pid not in result:
            result.append(pid)
    return result


def _optional_int(value: Any) -> int | None:
    if value is None or value == "":
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _normalise_feature_gaps(value: Any) -> list[dict[str, str]]:
    if not isinstance(value, list):
        return []
    gaps: list[dict[str, str]] = []
    for item in value:
        if not isinstance(item, dict):
            continue
        fid = str(item.get("feature_id") or item.get("id") or "").strip()
        if not fid:
            continue
        gaps.append({
            "feature_id": fid,
            "reason": str(item.get("reason") or "").strip(),
        })
    return gaps


def _normalise_result(raw: Any) -> dict[str, Any]:
    if not isinstance(raw, dict):
        raise ValueError("result must be a JSON object")
    status = str(raw.get("status", "completed"))
    if status not in {"completed", "failed", "skipped"}:
        raise ValueError("result.status must be completed, failed, or skipped")
    result: dict[str, Any] = {
        "status": status,
        "raw_response_path": str(raw.get("raw_response_path") or "").strip(),
        "pid_list_path": str(raw.get("pid_list_path") or "").strip(),
        "top50_path": str(raw.get("top50_path") or "").strip(),
        "total": raw.get("total"),
        "truncated": bool(raw.get("truncated", False)),
        "summary": str(raw.get("summary") or "").strip(),
        "new_candidates": _pid_list(raw.get("new_candidates"), "new_candidates"),
        "new_high_coverage": _pid_list(raw.get("new_high_coverage"), "new_high_coverage"),
        "new_decisive_evidence": _pid_list(
            raw.get("new_decisive_evidence"), "new_decisive_evidence"
        ),
        "new_pivots": [str(item) for item in raw.get("new_pivots") or [] if str(item).strip()],
        "new_ipcs": [str(item) for item in raw.get("new_ipcs") or [] if str(item).strip()],
        "new_family_citation": [
            str(item) for item in raw.get("new_family_citation") or [] if str(item).strip()
        ],
        "feature_coverage_delta": float(raw.get("feature_coverage_delta", 0)),
        "covered_features": [
            str(item).strip() for item in raw.get("covered_features") or [] if str(item).strip()
        ],
        "feature_gaps": _normalise_feature_gaps(raw.get("feature_gaps")),
        "credits_charged": _optional_int(raw.get("credits_charged")),
        "credits_remaining": _optional_int(raw.get("credits_remaining")),
        "followups": raw.get("followups") or [],
    }
    if not isinstance(result["followups"], list):
        raise ValueError("followups must be a list")
    return result


def _state_summary(state: dict[str, Any]) -> dict[str, Any]:
    actions = state["frontier"]
    by_status = {name: sum(item["status"] == name for item in actions) for name in VALID_ACTION_STATES}
    completed_lanes = sorted(
        {item["lane"] for item in actions if item["status"] == "completed"}
    )
    coverage = state.get("feature_coverage", {})
    covered = sum(1 for cov in coverage.values() if cov.get("covered_by"))
    gapped = sum(1 for cov in coverage.values() if cov.get("gap_recorded") and not cov.get("covered_by"))
    unresolved = len(coverage) - covered - gapped
    sat = state.get("saturation", {})
    cost = state.get("cost", {})
    return {
        "case_id": state["case_id"],
        "target_patent": state["target_patent"],
        "status": state["status"],
        "cycle": state["cycle"],
        "actions": by_status,
        "completed_lanes": completed_lanes,
        "required_lanes_missing": sorted(set(state["required_lanes"]) - set(completed_lanes)),
        "unique_candidates": len(state["candidates"]),
        "feature_coverage": {
            "total": len(coverage),
            "covered": covered,
            "gapped": gapped,
            "unresolved": unresolved,
            "all_resolved": unresolved == 0 and bool(coverage),
        },
        "zero_gain_cycles": sat.get("zero_gain_cycles", 0),
        "zero_decisive_cycles": sat.get("zero_decisive_cycles", 0),
        "last_recommendation": sat.get("recommendation", "continue"),
        "credits_spent": cost.get("credits_spent", 0),
        "credits_remaining": cost.get("credits_remaining"),
    }


def cmd_init(args: argparse.Namespace) -> int:
    case_dir = Path(args.case_dir).resolve()
    if _state_path(case_dir).exists():
        raise ValueError(f"goal already exists: {_state_path(case_dir)}")
    features = _read_json(Path(args.features))
    if isinstance(features, dict):
        features = features.get("features")
    if not isinstance(features, list) or not features:
        raise ValueError("features JSON must be a non-empty list or contain a non-empty features list")
    required_lanes = [item.strip() for item in args.required_lanes.split(",") if item.strip()]
    invalid_lanes = sorted(set(required_lanes) - VALID_LANES)
    if invalid_lanes:
        raise ValueError(f"invalid required lanes: {', '.join(invalid_lanes)}")
    case_dir.mkdir(parents=True, exist_ok=True)
    for name in ("rounds", "raw", "pid_lists", "details", "actions", "results"):
        (case_dir / name).mkdir(exist_ok=True)
    feature_coverage: dict[str, Any] = {}
    for feat in features:
        if isinstance(feat, dict):
            fid = str(feat.get("id") or "").strip()
            if fid and fid not in feature_coverage:
                feature_coverage[fid] = {"covered_by": [], "gap_recorded": False}
    state = {
        "schema_version": "1.1",
        "case_id": args.case_id,
        "target_patent": args.target_patent,
        "critical_date": args.critical_date,
        "objective": args.objective,
        "status": "active",
        "completion_reason": "",
        "created_at": _now(),
        "updated_at": _now(),
        "cycle": 0,
        "features": features,
        "required_lanes": required_lanes,
        "feature_coverage": feature_coverage,
        "frontier": [],
        "next_action_number": 1,
        "candidates": {},
        "checkpointed_action_ids": [],
        "saturation": {
            "zero_gain_cycles": 0,
            "zero_decisive_cycles": 0,
            "recommendation": "continue",
        },
        "cost": {"credits_spent": 0, "credits_remaining": None},
    }
    _save_state(case_dir, state)
    _append_event(case_dir, "init", case_id=args.case_id, target_patent=args.target_patent)
    print(json.dumps(_state_summary(state), ensure_ascii=False, indent=2))
    return 0


def cmd_enqueue(args: argparse.Namespace) -> int:
    case_dir = Path(args.case_dir).resolve()
    state = _load_state(case_dir)
    raw = _read_json(Path(args.action))
    action, created = _enqueue(state, raw)
    _save_state(case_dir, state)
    _append_event(case_dir, "enqueue", action_id=action["id"], created=created)
    print(json.dumps({"created": created, "action": action}, ensure_ascii=False, indent=2))
    return 0


def cmd_next(args: argparse.Namespace) -> int:
    case_dir = Path(args.case_dir).resolve()
    state = _load_state(case_dir)
    if state["status"] != "active":
        raise ValueError(f"goal is {state['status']}; resume it before claiming actions")
    actions = [item for item in state["frontier"] if item["status"] == "pending"]
    actions.sort(key=lambda item: (-item["priority"], item["id"]))
    selected = actions[: args.limit]
    if args.claim:
        for item in selected:
            item["status"] = "running"
            item["started_at"] = _now()
        _save_state(case_dir, state)
        _append_event(case_dir, "claim", action_ids=[item["id"] for item in selected])
    print(json.dumps({"summary": _state_summary(state), "actions": selected}, ensure_ascii=False, indent=2))
    return 0


def cmd_record(args: argparse.Namespace) -> int:
    case_dir = Path(args.case_dir).resolve()
    state = _load_state(case_dir)
    action = _find_action(state, args.action_id)
    if action["status"] not in {"pending", "running"}:
        raise ValueError(f"action {args.action_id} is already {action['status']}")
    result = _normalise_result(_read_json(Path(args.result)))
    action["status"] = result["status"]
    action["completed_at"] = _now()
    action["result"] = result
    coverage = state.setdefault("feature_coverage", {})
    for pid in result["new_candidates"]:
        state["candidates"].setdefault(
            pid, {"first_action": action["id"], "signals": [], "covered_features": []}
        )
        state["candidates"][pid]["signals"].append("candidate")
    for pid in result["new_high_coverage"]:
        state["candidates"].setdefault(
            pid, {"first_action": action["id"], "signals": [], "covered_features": []}
        )
        state["candidates"][pid]["signals"].append("high_coverage")
    for pid in result["new_decisive_evidence"]:
        state["candidates"].setdefault(
            pid, {"first_action": action["id"], "signals": [], "covered_features": []}
        )
        state["candidates"][pid]["signals"].append("decisive_evidence")
    # Structured feature coverage: map newly confirmed features to the PID(s)
    # that disclosed them, and record explicitly logged search gaps.
    for fid in result["covered_features"]:
        entry = coverage.setdefault(fid, {"covered_by": [], "gap_recorded": False})
        if action["id"] not in entry["covered_by"]:
            entry["covered_by"].append(action["id"])
    for gap in result["feature_gaps"]:
        fid = gap["feature_id"]
        entry = coverage.setdefault(fid, {"covered_by": [], "gap_recorded": False})
        entry["gap_recorded"] = True
    # Cost tracking from API-reported credits.
    cost = state.setdefault("cost", {"credits_spent": 0, "credits_remaining": None})
    if result["credits_charged"] is not None:
        cost["credits_spent"] = cost.get("credits_spent", 0) + result["credits_charged"]
    if result["credits_remaining"] is not None:
        cost["credits_remaining"] = result["credits_remaining"]
    added_followups = []
    for followup in result["followups"]:
        if isinstance(followup, dict):
            followup.setdefault("parent_ids", [action["id"]])
            added, created = _enqueue(state, followup)
            if created:
                added_followups.append(added["id"])
    # Detect capped searches and surface a narrowing suggestion (not auto-enqueued;
    # the agent decides whether to enqueue it).
    narrowing_suggestions = _narrowing_suggestions(action, result)
    _save_state(case_dir, state)
    _append_event(
        case_dir,
        "record",
        action_id=action["id"],
        status=result["status"],
        followups=added_followups,
        narrowing_suggestions=narrowing_suggestions,
    )
    print(json.dumps(
        {"action": action["id"], "followups": added_followups, "narrowing_suggestions": narrowing_suggestions},
        ensure_ascii=False,
        indent=2,
    ))
    return 0


def _narrowing_suggestions(action: dict[str, Any], result: dict[str, Any]) -> list[dict[str, Any]]:
    """When a Bool/world search hits the 10000 cap, suggest concrete narrowing."""
    total = result.get("total")
    try:
        capped = result.get("truncated") or (total is not None and int(total) >= 10000)
    except (TypeError, ValueError):
        capped = False
    if not capped:
        return []
    return [{
        "lane": action["lane"],
        "action_type": "narrowing_suggestion",
        "hypothesis": f"收窄动作 {action['id']} 的封顶检索（按 IPC/日期/CC 限定）",
        "parent_ids": [action["id"]],
        "features": action.get("features") or [],
        "priority": 55,
        "expected_gain": "降低噪声、暴露封顶路径下的正向候选",
        "notes": f"原检索 total={total}，已达上限；请基于已返回 Top 50 的 IPC/申请人/前缀分布收窄",
    }]


def cmd_checkpoint(args: argparse.Namespace) -> int:
    case_dir = Path(args.case_dir).resolve()
    state = _load_state(case_dir)
    completed = [item for item in state["frontier"] if item["status"] == "completed"]
    terminal = [
        item
        for item in state["frontier"]
        if item["status"] in {"completed", "failed", "skipped"}
    ]
    checkpointed = set(state.get("checkpointed_action_ids") or [])
    # A failed or skipped action is still search budget and evidence about a
    # route's viability.  Count it once in the checkpoint so a permanently
    # unresolvable PID cannot remain invisible to the saturation logic.
    since = [item for item in terminal if item["id"] not in checkpointed]
    if not since:
        raise ValueError("no completed actions since the previous checkpoint")
    gain = {field: 0 for field in GAIN_FIELDS}
    feature_delta = 0.0
    new_covered_features: set[str] = set()
    for action in since:
        result = action.get("result") or {}
        for field in GAIN_FIELDS:
            gain[field] += len(result.get(field) or [])
        feature_delta += float(result.get("feature_coverage_delta", 0))
        for fid in result.get("covered_features") or []:
            cov = state.setdefault("feature_coverage", {}).setdefault(
                fid, {"covered_by": [], "gap_recorded": False}
            )
            if not cov["covered_by"]:
                new_covered_features.add(fid)
            if action["id"] not in cov["covered_by"]:
                cov["covered_by"].append(action["id"])
    # Real coverage delta = newly-first-covered features / total tracked features.
    coverage = state.get("feature_coverage", {})
    total_features = max(len(coverage), 1)
    real_coverage_delta = round(len(new_covered_features) / total_features, 4)
    any_gain = any(gain.values()) or feature_delta > 0
    decisive_gain = (
        gain["new_high_coverage"] > 0
        or gain["new_decisive_evidence"] > 0
        or real_coverage_delta > 0
    )
    saturation = state["saturation"]
    saturation["zero_gain_cycles"] = 0 if any_gain else saturation.get("zero_gain_cycles", 0) + 1
    saturation["zero_decisive_cycles"] = (
        0 if decisive_gain else saturation.get("zero_decisive_cycles", 0) + 1
    )
    state["checkpointed_action_ids"] = sorted(checkpointed | {item["id"] for item in since})
    state["cycle"] += 1
    completed_lanes = {item["lane"] for item in completed}
    missing_lanes = sorted(set(state["required_lanes"]) - completed_lanes)
    pending = [item for item in state["frontier"] if item["status"] in {"pending", "running"}]
    high_pending = [item for item in pending if item["priority"] >= 60]
    all_features_covered_or_gapped = bool(coverage) and all(
        bool(cov.get("covered_by")) or cov.get("gap_recorded") for cov in coverage.values()
    )
    if missing_lanes:
        recommendation = "continue_required_lanes"
    elif high_pending:
        recommendation = "continue_high_value_frontier"
    elif (
        saturation.get("zero_decisive_cycles", 0) >= 3 and all_features_covered_or_gapped
    ):
        recommendation = "saturation_review"
    elif pending:
        recommendation = "continue_frontier"
    else:
        recommendation = "plan_new_diverse_actions"
    saturation["recommendation"] = recommendation
    record = {
        "cycle": state["cycle"],
        "actions": [item["id"] for item in since],
        "gain": gain,
        "feature_coverage_delta": round(feature_delta, 4),
        "real_coverage_delta": real_coverage_delta,
        "newly_covered_features": sorted(new_covered_features),
        "all_features_covered_or_gapped": all_features_covered_or_gapped,
        "zero_decisive_cycles": saturation.get("zero_decisive_cycles", 0),
        "missing_required_lanes": missing_lanes,
        "high_pending_actions": [item["id"] for item in high_pending],
        "recommendation": recommendation,
        "note": args.note or "",
    }
    round_dir = case_dir / "rounds" / f"R{state['cycle']:03d}"
    _write_json(round_dir / "checkpoint.json", record)
    _save_state(case_dir, state)
    _append_event(case_dir, "checkpoint", **record)
    print(json.dumps({"checkpoint": record, "summary": _state_summary(state)}, ensure_ascii=False, indent=2))
    return 0


def cmd_status(args: argparse.Namespace) -> int:
    state = _load_state(Path(args.case_dir).resolve())
    print(json.dumps(_state_summary(state), ensure_ascii=False, indent=2))
    return 0


def cmd_pause_resume(args: argparse.Namespace) -> int:
    case_dir = Path(args.case_dir).resolve()
    state = _load_state(case_dir)
    desired = "paused" if args.command == "pause" else "active"
    state["status"] = desired
    _save_state(case_dir, state)
    _append_event(case_dir, args.command, note=args.note or "")
    print(json.dumps(_state_summary(state), ensure_ascii=False, indent=2))
    return 0


def cmd_complete(args: argparse.Namespace) -> int:
    case_dir = Path(args.case_dir).resolve()
    state = _load_state(case_dir)
    if args.reason not in {"evidence_ready", "saturated", "user_ended"}:
        raise ValueError("reason must be evidence_ready, saturated, or user_ended")
    override_gate = False
    if args.reason == "evidence_ready":
        audit = _completion_audit(state)
        # If the gate is not recommending saturation review, the agent is
        # overriding the loop's own judgement.  Require an explicit note and
        # leave an auditable override_gate marker.
        if audit["gate_recommendation"] != "saturation_review":
            if not (args.note or "").strip():
                raise ValueError(
                    "evidence_ready while gate recommends "
                    f"'{audit['gate_recommendation']}': --note is required to "
                    "explain the override"
                )
            override_gate = True
        print(json.dumps({"completion_audit": audit}, ensure_ascii=False, indent=2))
    state["status"] = "complete"
    state["completion_reason"] = args.reason
    _save_state(case_dir, state)
    _append_event(
        case_dir,
        "complete",
        reason=args.reason,
        override_gate=override_gate,
        note=args.note or "",
    )
    print(json.dumps(_state_summary(state), ensure_ascii=False, indent=2))
    return 0


def _completion_audit(state: dict[str, Any]) -> dict[str, Any]:
    """Pre-completion audit printed before an evidence_ready seal."""
    completed = [item for item in state["frontier"] if item["status"] == "completed"]
    completed_lanes = {item["lane"] for item in completed}
    required = set(state.get("required_lanes", []))
    coverage = state.get("feature_coverage", {})
    all_resolved = bool(coverage) and all(
        bool(cov.get("covered_by")) or cov.get("gap_recorded") for cov in coverage.values()
    )
    decisive_pids = {
        pid
        for item in completed
        for pid in (item.get("result") or {}).get("new_decisive_evidence", [])
    }
    high_pids = {
        pid
        for item in completed
        for pid in (item.get("result") or {}).get("new_high_coverage", [])
    }
    return {
        "required_lanes_all_executed": required.issubset(completed_lanes),
        "missing_required_lanes": sorted(required - completed_lanes),
        "all_features_covered_or_gapped": all_resolved,
        "decisive_candidate_count": len(decisive_pids),
        "high_coverage_candidate_count": len(high_pids),
        "gate_recommendation": state.get("saturation", {}).get("recommendation", "continue"),
        "zero_decisive_cycles": state.get("saturation", {}).get("zero_decisive_cycles", 0),
    }


def cmd_suggest_diversity(args: argparse.Namespace) -> int:
    case_dir = Path(args.case_dir).resolve()
    state = _load_state(case_dir)
    coverage = state.get("feature_coverage", {})
    # Uncovered = no decisive PID and no logged gap yet.
    uncovered = [
        fid for fid, cov in coverage.items()
        if not cov.get("covered_by") and not cov.get("gap_recorded")
    ]
    suggestions: list[dict[str, Any]] = []
    bool_lanes = {"qx", "qy_base", "qy_comp", "world"}
    for fid in uncovered:
        tried_channels: set[str] = set()
        for action in state["frontier"]:
            if action["status"] != "completed":
                continue
            if action["lane"] not in bool_lanes:
                continue
            if fid not in (action.get("features") or []):
                continue
            tried_channels.add(f"{action['lane']}/{action.get('market') or 'cn'}")
        if len(tried_channels) >= args.threshold:
            suggestions.append({
                "feature_id": fid,
                "bool_channels_tried": sorted(tried_channels),
                "suggested_actions": [
                    {
                        "lane": "semantic",
                        "action_type": "semantic_B",
                        "hypothesis": f"去对象化关系视角检索覆盖特征 {fid} 的跨域方案（去掉产品名与目标部件名，仅写部件拓扑/步骤关系+作用机制）",
                        "features": [fid],
                        "priority": 65,
                        "expected_gain": "跨术语体系的同构方案召回（Bool 词面零重叠场景）",
                        "notes": "触发依据：该特征经 ≥2 个 Bool 通道仍零决定性证据",
                    },
                    {
                        "lane": "semantic",
                        "action_type": "semantic_C",
                        "hypothesis": f"问题/机制视角检索覆盖特征 {fid} 的跨域方案（技术问题+实现机制，不写对象名）",
                        "features": [fid],
                        "priority": 60,
                        "expected_gain": "相邻领域可迁移表达召回",
                        "notes": "前置：需至少 1 篇 Y-Base 已完成详情核验并形成真实残余特征",
                    },
                ],
            })
    _append_event(
        case_dir,
        "suggest_diversity",
        uncovered_features=uncovered,
        suggestions_count=len(suggestions),
    )
    print(json.dumps(
        {"uncovered_features": uncovered, "suggestions": suggestions},
        ensure_ascii=False,
        indent=2,
    ))
    return 0


def cmd_export(args: argparse.Namespace) -> int:
    case_dir = Path(args.case_dir).resolve()
    state = _load_state(case_dir)
    search_lanes = {"qx", "qy_base", "qy_comp", "world", "semantic"}
    searches = []
    details = []
    for action in state["frontier"]:
        if action["status"] != "completed":
            continue
        result = action.get("result") or {}
        entry = {
            "action_id": action["id"],
            "lane": action["lane"],
            "action_type": action.get("action_type", ""),
            "hypothesis": action.get("hypothesis", ""),
            "query": action.get("query", ""),
            "market": action.get("market", ""),
            "features": action.get("features") or [],
            "total": result.get("total"),
            "truncated": result.get("truncated", False),
            "raw_response_path": result.get("raw_response_path", ""),
            "pid_list_path": result.get("pid_list_path", ""),
            "summary": result.get("summary", ""),
        }
        if action["lane"] == "detail":
            details.append(entry)
        elif action["lane"] in search_lanes:
            searches.append(entry)
    coverage = state.get("feature_coverage", {})
    completed_lanes = {
        item["lane"] for item in state["frontier"] if item["status"] == "completed"
    }
    required = set(state.get("required_lanes", []))
    evidence = {
        "title": f"无效证据检索骨架 — {state.get('target_patent', '')}",
        "role": "invalidity",
        "decision": "",
        "task_type": "invalidity",
        "as_of": _now()[:10],
        "scope": {
            "target_patent": state.get("target_patent", ""),
            "critical_date": state.get("critical_date", ""),
            "case_id": state.get("case_id", ""),
        },
        "features": [
            {
                "id": fid,
                "covered": bool(cov.get("covered_by")),
                "gap_recorded": cov.get("gap_recorded", False),
                "covered_by": cov.get("covered_by", []),
            }
            for fid, cov in coverage.items()
        ],
        "searches": searches,
        "details": details,
        "gate": {
            "status": "",
            "required_lanes_all_executed": required.issubset(completed_lanes),
            "lanes": sorted(completed_lanes),
            "feature_coverage": {
                fid: ("covered" if cov.get("covered_by")
                      else "gapped" if cov.get("gap_recorded") else "unresolved")
                for fid, cov in coverage.items()
            },
        },
        "limitations": [],
        "conclusion": "",
        "_export_note": "由 invalidity_goal.py export 自动生成骨架；gate.status/limitations/conclusion 需人工填写",
    }
    out_path = Path(args.output) if args.output else case_dir / "evidence_skeleton.json"
    _write_json(out_path, evidence)
    _append_event(case_dir, "export", output=str(out_path))
    print(json.dumps(
        {"output": str(out_path), "searches": len(searches), "details": len(details)},
        ensure_ascii=False,
        indent=2,
    ))
    return 0


def cmd_self_test(_: argparse.Namespace) -> int:
    with tempfile.TemporaryDirectory(prefix="invalidity-goal-") as directory:
        case_dir = Path(directory) / "case"
        feature_file = Path(directory) / "features.json"
        action_file = Path(directory) / "action.json"
        result_file = Path(directory) / "result.json"
        _write_json(feature_file, [
            {"id": "F1", "required": True},
            {"id": "F2", "required": True},
        ])
        init_args = argparse.Namespace(
            case_dir=str(case_dir),
            case_id="SELFTEST",
            target_patent="CN000000000U",
            critical_date="20200101",
            objective="self test",
            features=str(feature_file),
            required_lanes="qx",
        )
        cmd_init(init_args)
        # Action now carries a features list so suggest-diversity can route.
        _write_json(action_file, {
            "lane": "qx", "action_type": "bool", "hypothesis": "test",
            "priority": 80, "features": ["F1"],
        })
        cmd_enqueue(argparse.Namespace(case_dir=str(case_dir), action=str(action_file)))
        cmd_next(argparse.Namespace(case_dir=str(case_dir), limit=1, claim=True))
        # Result now carries covered_features, credits and a feature gap.
        _write_json(result_file, {
            "new_candidates": ["CN100000000A"],
            "feature_coverage_delta": 0.2,
            "covered_features": ["F1"],
            "feature_gaps": [{"feature_id": "F2", "reason": "no bool channel covered F2"}],
            "credits_charged": 1,
            "credits_remaining": 99,
        })
        cmd_record(argparse.Namespace(case_dir=str(case_dir), action_id="A0001", result=str(result_file)))
        cmd_checkpoint(argparse.Namespace(case_dir=str(case_dir), note="self test"))
        state = _load_state(case_dir)
        if state["cycle"] != 1 or "CN100000000A" not in state["candidates"]:
            raise AssertionError("self test state mismatch")
        if state["feature_coverage"]["F1"]["covered_by"] != ["A0001"]:
            raise AssertionError("covered_features not recorded")
        if not state["feature_coverage"]["F2"]["gap_recorded"]:
            raise AssertionError("feature_gaps not recorded")
        if state["cost"]["credits_spent"] != 1 or state["cost"]["credits_remaining"] != 99:
            raise AssertionError("cost not accumulated")
        # suggest-diversity should find F2 unresolved but below threshold (only
        # one bool channel tried), so no suggestions.
        import io, contextlib
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            cmd_suggest_diversity(argparse.Namespace(
                case_dir=str(case_dir), threshold=2
            ))
        sug = json.loads(buf.getvalue())
        if sug["suggestions"]:
            raise AssertionError("suggest-diversity should be empty with 1 channel")
        # export should produce a skeleton with 1 search, 0 details.
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            cmd_export(argparse.Namespace(
                case_dir=str(case_dir), output=None
            ))
        exp = json.loads(buf.getvalue())
        if exp["searches"] != 1 or exp["details"] != 0:
            raise AssertionError("export counts mismatch")
        # evidence_ready without --note should fail because gate does not
        # recommend saturation_review.
        try:
            cmd_complete(argparse.Namespace(
                case_dir=str(case_dir), reason="evidence_ready", note=None
            ))
            raise AssertionError("evidence_ready should require --note on override")
        except ValueError:
            pass  # expected
        # evidence_ready with --note should succeed and mark override_gate.
        cmd_complete(argparse.Namespace(
            case_dir=str(case_dir), reason="evidence_ready",
            note="agent judgement: F1 covered, F2 gapped",
        ))
        state = _load_state(case_dir)
        if state["status"] != "complete":
            raise AssertionError("goal not completed")
    print("invalidity_goal self-test passed")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="管理可恢复的无效检索 Goal Loop")
    subparsers = parser.add_subparsers(dest="command", required=True)

    init = subparsers.add_parser("init", help="创建案例状态与目录")
    init.add_argument("case_dir")
    init.add_argument("--case-id", required=True)
    init.add_argument("--target-patent", required=True)
    init.add_argument("--critical-date", required=True)
    init.add_argument("--objective", default="持续发现并核验高质量无效证据候选")
    init.add_argument("--features", required=True)
    init.add_argument("--required-lanes", default=",".join(DEFAULT_REQUIRED_LANES))
    init.set_defaults(func=cmd_init)

    enqueue = subparsers.add_parser("enqueue", help="将一个可审计检索假设加入前沿")
    enqueue.add_argument("case_dir")
    enqueue.add_argument("action", help="动作 JSON 文件")
    enqueue.set_defaults(func=cmd_enqueue)

    next_action = subparsers.add_parser("next", help="查看或认领当前最高价值动作")
    next_action.add_argument("case_dir")
    next_action.add_argument("--limit", type=int, default=3)
    next_action.add_argument("--claim", action="store_true")
    next_action.set_defaults(func=cmd_next)

    record = subparsers.add_parser("record", help="写入动作结果并生成后续前沿")
    record.add_argument("case_dir")
    record.add_argument("action_id")
    record.add_argument("result", help="结果 JSON 文件")
    record.set_defaults(func=cmd_record)

    checkpoint = subparsers.add_parser("checkpoint", help="计算本循环的证据增益与下一状态")
    checkpoint.add_argument("case_dir")
    checkpoint.add_argument("--note")
    checkpoint.set_defaults(func=cmd_checkpoint)

    status = subparsers.add_parser("status", help="查看状态摘要")
    status.add_argument("case_dir")
    status.set_defaults(func=cmd_status)

    suggest = subparsers.add_parser(
        "suggest-diversity", help="对未覆盖特征建议语义 B/C 多样性动作骨架"
    )
    suggest.add_argument("case_dir")
    suggest.add_argument("--threshold", type=int, default=2,
                         help="触发建议所需的最小 Bool 通道数（默认 2）")
    suggest.set_defaults(func=cmd_suggest_diversity)

    export = subparsers.add_parser(
        "export", help="从 goal_state 导出 evidence.json 骨架供 report_guard 消费"
    )
    export.add_argument("case_dir")
    export.add_argument("--output", help="输出文件路径（默认 <case_dir>/evidence_skeleton.json）")
    export.set_defaults(func=cmd_export)

    for command in ("pause", "resume"):
        lifecycle = subparsers.add_parser(command, help=f"{command} goal")
        lifecycle.add_argument("case_dir")
        lifecycle.add_argument("--note")
        lifecycle.set_defaults(func=cmd_pause_resume)

    complete = subparsers.add_parser("complete", help="在满足完成门后封存 goal")
    complete.add_argument("case_dir")
    complete.add_argument("--reason", required=True)
    complete.add_argument("--note")
    complete.set_defaults(func=cmd_complete)

    self_test = subparsers.add_parser("self-test", help="运行控制器自检")
    self_test.set_defaults(func=cmd_self_test)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        return args.func(args)
    except (ValueError, OSError, AssertionError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
