#!/usr/bin/env python3
"""Persist recurring market-radar runs and classify signal newness.

This utility performs deterministic state bookkeeping only. It does not fetch sources,
score intelligence, or make business decisions.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sqlite3
import sys
import unicodedata
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit


SCHEMA = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS meta (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS runs (
    run_id TEXT PRIMARY KEY,
    watch_id TEXT NOT NULL,
    started_at TEXT NOT NULL,
    finished_at TEXT,
    status TEXT NOT NULL CHECK(status IN ('active', 'success', 'partial', 'failed')),
    prior_successful_run TEXT,
    note TEXT
);

CREATE TABLE IF NOT EXISTS signals (
    signal_id TEXT PRIMARY KEY,
    fingerprint TEXT NOT NULL UNIQUE,
    entity TEXT NOT NULL,
    change_type TEXT NOT NULL,
    title TEXT NOT NULL,
    delta TEXT,
    summary TEXT,
    event_at TEXT,
    effective_at TEXT,
    first_seen_at TEXT NOT NULL,
    last_seen_at TEXT NOT NULL,
    first_run_id TEXT NOT NULL,
    last_run_id TEXT NOT NULL,
    priority TEXT,
    rise_json TEXT,
    content_hash TEXT NOT NULL,
    revision_count INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS evidence (
    evidence_id INTEGER PRIMARY KEY AUTOINCREMENT,
    signal_id TEXT NOT NULL REFERENCES signals(signal_id) ON DELETE CASCADE,
    source_url TEXT NOT NULL,
    source_title TEXT,
    source_tier TEXT,
    published_at TEXT,
    observed_at TEXT,
    role TEXT NOT NULL DEFAULT 'confirmation',
    UNIQUE(signal_id, source_url, role)
);

CREATE TABLE IF NOT EXISTS run_signals (
    run_id TEXT NOT NULL REFERENCES runs(run_id) ON DELETE CASCADE,
    signal_id TEXT NOT NULL REFERENCES signals(signal_id) ON DELETE CASCADE,
    state TEXT NOT NULL CHECK(state IN ('NEW', 'EVIDENCE', 'REVISION', 'CONTINUATION')),
    previous_content_hash TEXT,
    PRIMARY KEY(run_id, signal_id)
);

CREATE INDEX IF NOT EXISTS idx_runs_watch_status
ON runs(watch_id, status, started_at);

CREATE INDEX IF NOT EXISTS idx_signals_last_seen
ON signals(last_seen_at);
"""

TRACKING_QUERY_KEYS = {
    "fbclid",
    "gclid",
    "mc_cid",
    "mc_eid",
    "ref",
    "ref_src",
    "source",
}


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def state_dir(workspace: str) -> Path:
    return Path(workspace).expanduser().resolve() / ".market-radar"


def db_path(workspace: str) -> Path:
    return state_dir(workspace) / "radar.db"


def connect(workspace: str, create: bool = False) -> sqlite3.Connection:
    directory = state_dir(workspace)
    database = db_path(workspace)
    if create:
        directory.mkdir(parents=True, exist_ok=True)
    elif not database.exists():
        raise SystemExit(f"Radar state not initialized: {database}")
    connection = sqlite3.connect(database)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def normalize_text(value: Any) -> str:
    text = unicodedata.normalize("NFKC", str(value or "")).lower().strip()
    return re.sub(r"[\W_]+", " ", text, flags=re.UNICODE).strip()


def canonical_url(raw_url: str) -> str:
    if not raw_url:
        return ""
    parts = urlsplit(raw_url.strip())
    query = []
    for key, value in parse_qsl(parts.query, keep_blank_values=True):
        lower_key = key.lower()
        if lower_key.startswith("utm_") or lower_key in TRACKING_QUERY_KEYS:
            continue
        query.append((key, value))
    query.sort()
    path = re.sub(r"/+$", "", parts.path) or "/"
    return urlunsplit(
        (parts.scheme.lower(), parts.netloc.lower(), path, urlencode(query), "")
    )


def stable_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def signal_fingerprint(signal: dict[str, Any]) -> str:
    explicit = normalize_text(signal.get("change_key"))
    if explicit:
        basis = ["explicit", explicit]
    else:
        date_basis = (
            signal.get("effective_at")
            or signal.get("event_at")
            or signal.get("published_at")
            or ""
        )
        basis = [
            normalize_text(signal.get("entity")),
            normalize_text(signal.get("change_type")),
            normalize_text(signal.get("title")),
            normalize_text(date_basis)[:10],
        ]
    return digest("|".join(basis))


def signal_content_hash(signal: dict[str, Any]) -> str:
    material = {
        "delta": signal.get("delta") or "",
        "summary": signal.get("summary") or "",
        "effective_at": signal.get("effective_at") or "",
        "priority": signal.get("priority") or "",
        "rise": signal.get("rise") or {},
    }
    return digest(stable_json(material))


def read_records(path: str) -> list[dict[str, Any]]:
    raw = sys.stdin.read() if path == "-" else Path(path).read_text(encoding="utf-8")
    raw = raw.strip()
    if not raw:
        return []
    if raw.startswith("["):
        value = json.loads(raw)
        if not isinstance(value, list):
            raise SystemExit("JSON input must be an array or JSONL records")
        records = value
    else:
        records = [json.loads(line) for line in raw.splitlines() if line.strip()]
    if not all(isinstance(record, dict) for record in records):
        raise SystemExit("Each signal record must be a JSON object")
    return records


def validate_signal(signal: dict[str, Any]) -> None:
    missing = [
        field
        for field in ("entity", "change_type", "title")
        if not str(signal.get(field) or "").strip()
    ]
    if missing:
        raise ValueError(f"Missing required signal fields: {', '.join(missing)}")
    priority = signal.get("priority")
    if priority and priority not in {"P0", "P1", "P2", "P3"}:
        raise ValueError(f"Invalid priority: {priority}")
    evidence = signal.get("evidence", [])
    if evidence is not None and not isinstance(evidence, list):
        raise ValueError("evidence must be a list")


def evidence_records(signal: dict[str, Any], observed_at: str) -> list[dict[str, Any]]:
    records = list(signal.get("evidence") or [])
    if signal.get("source_url"):
        records.append(
            {
                "source_url": signal["source_url"],
                "source_title": signal.get("source_title"),
                "source_tier": signal.get("source_tier"),
                "published_at": signal.get("published_at"),
                "observed_at": signal.get("observed_at"),
                "role": signal.get("evidence_role", "origin"),
            }
        )
    result = []
    for record in records:
        url = canonical_url(str(record.get("source_url") or ""))
        if not url:
            continue
        result.append(
            {
                "source_url": url,
                "source_title": record.get("source_title"),
                "source_tier": record.get("source_tier"),
                "published_at": record.get("published_at"),
                "observed_at": record.get("observed_at") or observed_at,
                "role": record.get("role") or "confirmation",
            }
        )
    return result


def cmd_init(args: argparse.Namespace) -> None:
    with connect(args.workspace, create=True) as connection:
        connection.executescript(SCHEMA)
        connection.execute(
            "INSERT INTO meta(key, value) VALUES('watch_id', ?) "
            "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
            (args.watch_id,),
        )
        connection.execute(
            "INSERT INTO meta(key, value) VALUES('schema_version', '1') "
            "ON CONFLICT(key) DO NOTHING"
        )
    print(
        stable_json(
            {
                "status": "initialized",
                "watch_id": args.watch_id,
                "database": str(db_path(args.workspace)),
            }
        )
    )


def watch_id_for(connection: sqlite3.Connection, override: str | None) -> str:
    if override:
        return override
    row = connection.execute("SELECT value FROM meta WHERE key = 'watch_id'").fetchone()
    if not row:
        raise SystemExit("No watch_id configured; rerun init with --watch-id")
    return str(row["value"])


def cmd_start_run(args: argparse.Namespace) -> None:
    with connect(args.workspace) as connection:
        watch_id = watch_id_for(connection, args.watch_id)
        prior = connection.execute(
            "SELECT run_id FROM runs WHERE watch_id = ? AND status = 'success' "
            "ORDER BY finished_at DESC LIMIT 1",
            (watch_id,),
        ).fetchone()
        run_id = args.run_id or f"run_{uuid.uuid4().hex[:16]}"
        connection.execute(
            "INSERT INTO runs(run_id, watch_id, started_at, status, prior_successful_run) "
            "VALUES(?, ?, ?, 'active', ?)",
            (run_id, watch_id, now_utc(), prior["run_id"] if prior else None),
        )
    print(
        stable_json(
            {
                "run_id": run_id,
                "watch_id": watch_id,
                "prior_successful_run": prior["run_id"] if prior else None,
            }
        )
    )


def assert_active_run(connection: sqlite3.Connection, run_id: str) -> sqlite3.Row:
    run = connection.execute(
        "SELECT * FROM runs WHERE run_id = ?", (run_id,)
    ).fetchone()
    if not run:
        raise SystemExit(f"Unknown run_id: {run_id}")
    if run["status"] != "active":
        raise SystemExit(f"Run is not active: {run_id} ({run['status']})")
    return run


def insert_evidence(
    connection: sqlite3.Connection,
    signal_id: str,
    records: Iterable[dict[str, Any]],
) -> int:
    added = 0
    for record in records:
        cursor = connection.execute(
            """
            INSERT OR IGNORE INTO evidence(
                signal_id, source_url, source_title, source_tier,
                published_at, observed_at, role
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                signal_id,
                record["source_url"],
                record.get("source_title"),
                record.get("source_tier"),
                record.get("published_at"),
                record.get("observed_at"),
                record.get("role") or "confirmation",
            ),
        )
        added += cursor.rowcount
    return added


def upsert_signal(
    connection: sqlite3.Connection,
    run_id: str,
    signal: dict[str, Any],
) -> tuple[str, str]:
    validate_signal(signal)
    observed_at = signal.get("observed_at") or now_utc()
    fingerprint = signal_fingerprint(signal)
    content_hash = signal_content_hash(signal)
    current = connection.execute(
        "SELECT * FROM signals WHERE fingerprint = ?", (fingerprint,)
    ).fetchone()

    if current is None:
        signal_id = f"sig_{fingerprint[:16]}"
        connection.execute(
            """
            INSERT INTO signals(
                signal_id, fingerprint, entity, change_type, title, delta, summary,
                event_at, effective_at, first_seen_at, last_seen_at, first_run_id,
                last_run_id, priority, rise_json, content_hash
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                signal_id,
                fingerprint,
                signal["entity"],
                signal["change_type"],
                signal["title"],
                signal.get("delta"),
                signal.get("summary"),
                signal.get("event_at"),
                signal.get("effective_at"),
                observed_at,
                observed_at,
                run_id,
                run_id,
                signal.get("priority"),
                stable_json(signal.get("rise") or {}),
                content_hash,
            ),
        )
        insert_evidence(connection, signal_id, evidence_records(signal, observed_at))
        state = "NEW"
        previous_hash = None
    else:
        signal_id = str(current["signal_id"])
        added_evidence = insert_evidence(
            connection, signal_id, evidence_records(signal, observed_at)
        )
        if current["content_hash"] != content_hash:
            state = "REVISION"
            connection.execute(
                """
                UPDATE signals SET
                    entity = ?, change_type = ?, title = ?, delta = ?, summary = ?,
                    event_at = ?, effective_at = ?, last_seen_at = ?, last_run_id = ?,
                    priority = ?, rise_json = ?, content_hash = ?,
                    revision_count = revision_count + 1
                WHERE signal_id = ?
                """,
                (
                    signal["entity"],
                    signal["change_type"],
                    signal["title"],
                    signal.get("delta"),
                    signal.get("summary"),
                    signal.get("event_at"),
                    signal.get("effective_at"),
                    observed_at,
                    run_id,
                    signal.get("priority"),
                    stable_json(signal.get("rise") or {}),
                    content_hash,
                    signal_id,
                ),
            )
        else:
            state = "EVIDENCE" if added_evidence else "CONTINUATION"
            connection.execute(
                "UPDATE signals SET last_seen_at = ?, last_run_id = ? WHERE signal_id = ?",
                (observed_at, run_id, signal_id),
            )
        previous_hash = str(current["content_hash"])

    prior_in_run = connection.execute(
        "SELECT state FROM run_signals WHERE run_id = ? AND signal_id = ?",
        (run_id, signal_id),
    ).fetchone()
    precedence = {"CONTINUATION": 0, "EVIDENCE": 1, "REVISION": 2, "NEW": 3}
    if prior_in_run and precedence[prior_in_run["state"]] > precedence[state]:
        state = str(prior_in_run["state"])
    connection.execute(
        """
        INSERT INTO run_signals(run_id, signal_id, state, previous_content_hash)
        VALUES(?, ?, ?, ?)
        ON CONFLICT(run_id, signal_id) DO UPDATE SET
            state = excluded.state,
            previous_content_hash = COALESCE(run_signals.previous_content_hash,
                                             excluded.previous_content_hash)
        """,
        (run_id, signal_id, state, previous_hash),
    )
    return signal_id, state


def cmd_ingest(args: argparse.Namespace) -> None:
    records = read_records(args.input)
    counts = {"NEW": 0, "EVIDENCE": 0, "REVISION": 0, "CONTINUATION": 0}
    results = []
    with connect(args.workspace) as connection:
        assert_active_run(connection, args.run_id)
        for index, signal in enumerate(records, start=1):
            try:
                signal_id, state = upsert_signal(
                    connection, args.run_id, signal
                )
            except (ValueError, json.JSONDecodeError) as exc:
                raise SystemExit(f"Invalid signal at record {index}: {exc}") from exc
            counts[state] += 1
            results.append({"signal_id": signal_id, "state": state})
    print(stable_json({"run_id": args.run_id, "counts": counts, "signals": results}))


def cmd_finish_run(args: argparse.Namespace) -> None:
    with connect(args.workspace) as connection:
        assert_active_run(connection, args.run_id)
        connection.execute(
            "UPDATE runs SET status = ?, finished_at = ?, note = ? WHERE run_id = ?",
            (args.status, now_utc(), args.note, args.run_id),
        )
    print(stable_json({"run_id": args.run_id, "status": args.status}))


def signal_dict(
    connection: sqlite3.Connection, row: sqlite3.Row
) -> dict[str, Any]:
    evidence = connection.execute(
        """
        SELECT source_url, source_title, source_tier, published_at, observed_at, role
        FROM evidence WHERE signal_id = ?
        ORDER BY observed_at, evidence_id
        """,
        (row["signal_id"],),
    ).fetchall()
    return {
        "signal_id": row["signal_id"],
        "state": row["state"],
        "entity": row["entity"],
        "change_type": row["change_type"],
        "title": row["title"],
        "delta": row["delta"],
        "summary": row["summary"],
        "event_at": row["event_at"],
        "effective_at": row["effective_at"],
        "priority": row["priority"],
        "rise": json.loads(row["rise_json"] or "{}"),
        "revision_count": row["revision_count"],
        "first_seen_at": row["first_seen_at"],
        "last_seen_at": row["last_seen_at"],
        "evidence": [dict(item) for item in evidence],
    }


def cmd_export(args: argparse.Namespace) -> None:
    with connect(args.workspace) as connection:
        rows = connection.execute(
            """
            SELECT rs.state, s.*
            FROM run_signals rs
            JOIN signals s ON s.signal_id = rs.signal_id
            WHERE rs.run_id = ?
              AND (? IS NULL OR rs.state = ?)
              AND (? IS NULL OR s.priority = ?)
            ORDER BY
              CASE s.priority WHEN 'P0' THEN 0 WHEN 'P1' THEN 1
                              WHEN 'P2' THEN 2 WHEN 'P3' THEN 3 ELSE 4 END,
              s.last_seen_at DESC
            """,
            (args.run_id, args.state, args.state, args.priority, args.priority),
        ).fetchall()
        payload = [signal_dict(connection, row) for row in rows]
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))


def cmd_stats(args: argparse.Namespace) -> None:
    with connect(args.workspace) as connection:
        runs = connection.execute(
            "SELECT status, COUNT(*) AS count FROM runs GROUP BY status"
        ).fetchall()
        signals = connection.execute(
            "SELECT priority, COUNT(*) AS count FROM signals GROUP BY priority"
        ).fetchall()
    print(
        json.dumps(
            {
                "database": str(db_path(args.workspace)),
                "runs": {row["status"]: row["count"] for row in runs},
                "signals": {
                    (row["priority"] or "unscored"): row["count"] for row in signals
                },
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Maintain deterministic state for recurring market intelligence runs."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("init", help="Initialize a watch database.")
    init_parser.add_argument("--workspace", required=True)
    init_parser.add_argument("--watch-id", required=True)
    init_parser.set_defaults(func=cmd_init)

    start_parser = subparsers.add_parser("start-run", help="Start a monitoring run.")
    start_parser.add_argument("--workspace", required=True)
    start_parser.add_argument("--watch-id")
    start_parser.add_argument("--run-id")
    start_parser.set_defaults(func=cmd_start_run)

    ingest_parser = subparsers.add_parser(
        "ingest", help="Ingest a JSON array or JSONL file of normalized signals."
    )
    ingest_parser.add_argument("--workspace", required=True)
    ingest_parser.add_argument("--run-id", required=True)
    ingest_parser.add_argument("--input", required=True, help="Path or - for stdin.")
    ingest_parser.set_defaults(func=cmd_ingest)

    finish_parser = subparsers.add_parser("finish-run", help="Close an active run.")
    finish_parser.add_argument("--workspace", required=True)
    finish_parser.add_argument("--run-id", required=True)
    finish_parser.add_argument(
        "--status", choices=("success", "partial", "failed"), required=True
    )
    finish_parser.add_argument("--note")
    finish_parser.set_defaults(func=cmd_finish_run)

    export_parser = subparsers.add_parser(
        "export", help="Export signals observed in one run."
    )
    export_parser.add_argument("--workspace", required=True)
    export_parser.add_argument("--run-id", required=True)
    export_parser.add_argument(
        "--state", choices=("NEW", "EVIDENCE", "REVISION", "CONTINUATION")
    )
    export_parser.add_argument("--priority", choices=("P0", "P1", "P2", "P3"))
    export_parser.set_defaults(func=cmd_export)

    stats_parser = subparsers.add_parser("stats", help="Summarize the state database.")
    stats_parser.add_argument("--workspace", required=True)
    stats_parser.set_defaults(func=cmd_stats)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
