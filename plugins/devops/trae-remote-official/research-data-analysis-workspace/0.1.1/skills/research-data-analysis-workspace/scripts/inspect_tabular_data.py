#!/usr/bin/env python3
"""Profile CSV/TSV/XLSX research tables without modifying the source files.

The JSON output contains structural metadata and candidate interpretations. Raw
example values are omitted unless --include-examples is explicitly requested.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any

try:
    import pandas as pd
except ImportError:
    print("This script requires pandas and, for XLSX, openpyxl.", file=sys.stderr)
    raise SystemExit(2)


TEXT_MISSING_CANDIDATES = {
    "",
    ".",
    "-",
    "na",
    "n/a",
    "nan",
    "none",
    "null",
    "missing",
    "unknown",
    "未知",
    "缺失",
}
NUMERIC_MISSING_CANDIDATES = {-9999, -999, -99, 99, 999, 9999}


def _json_value(value: Any) -> Any:
    if value is None or pd.isna(value):
        return None
    if hasattr(value, "isoformat"):
        return value.isoformat()
    if isinstance(value, bool):
        return value
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return value if math.isfinite(value) else None
    return str(value)


def _read_delimited(path: Path, max_rows: int | None) -> tuple[pd.DataFrame, str]:
    separator = "\t" if path.suffix.lower() == ".tsv" else None
    read_rows = max_rows + 1 if max_rows is not None else None
    errors: list[str] = []
    for encoding in ("utf-8-sig", "utf-8", "gb18030"):
        try:
            frame = pd.read_csv(
                path,
                encoding=encoding,
                sep=separator,
                engine="python" if separator is None else "c",
                nrows=read_rows,
            )
            return frame, encoding
        except (UnicodeDecodeError, pd.errors.ParserError) as exc:
            errors.append(f"{encoding}:{type(exc).__name__}")
    raise ValueError(f"Unable to read {path}; attempts: {', '.join(errors)}")


def _read_tables(
    path: Path,
    sheet: str | int | None,
    all_sheets: bool,
    max_rows: int | None,
) -> list[tuple[str | None, pd.DataFrame, dict[str, Any]]]:
    suffix = path.suffix.lower()
    if suffix in {".csv", ".tsv", ".txt"}:
        frame, encoding = _read_delimited(path, max_rows)
        return [(None, frame, {"encoding": encoding})]
    if suffix in {".xlsx", ".xls"}:
        workbook = pd.ExcelFile(path)
        read_rows = max_rows + 1 if max_rows is not None else None
        selected: list[str | int]
        if all_sheets:
            selected = list(workbook.sheet_names)
        elif sheet is None:
            selected = [workbook.sheet_names[0]]
        else:
            selected = [sheet]
        tables = []
        for selected_sheet in selected:
            frame = pd.read_excel(path, sheet_name=selected_sheet, nrows=read_rows)
            tables.append(
                (str(selected_sheet), frame, {"available_sheets": workbook.sheet_names})
            )
        return tables
    raise ValueError(f"Unsupported tabular format: {suffix}")


def _parse_ratios(series: pd.Series) -> tuple[float, float]:
    non_null = series.dropna()
    if non_null.empty:
        return 0.0, 0.0
    numeric = pd.to_numeric(non_null, errors="coerce")
    numeric_ratio = float(numeric.notna().mean())
    date_ratio = 0.0
    sample = non_null.astype(str).head(500)
    if numeric_ratio < 0.9 and sample.str.contains(r"[-/:年月日]", regex=True).mean() >= 0.5:
        parsed_dates = pd.to_datetime(sample, errors="coerce")
        date_ratio = float(parsed_dates.notna().mean())
    return numeric_ratio, date_ratio


def _semantic_candidate(
    series: pd.Series,
    non_null_count: int,
    unique_count: int,
    numeric_ratio: float,
    date_ratio: float,
) -> str:
    if non_null_count == 0:
        return "empty"
    if pd.api.types.is_bool_dtype(series):
        return "boolean"
    if pd.api.types.is_datetime64_any_dtype(series):
        return "datetime"
    if pd.api.types.is_numeric_dtype(series):
        return "numeric"
    if unique_count == non_null_count and non_null_count > 1:
        return "identifier_candidate"
    category_limit = min(50, max(2, int(math.sqrt(non_null_count))))
    if unique_count <= category_limit:
        return "categorical_candidate"
    if numeric_ratio >= 0.9:
        return "numeric_text_candidate"
    if date_ratio >= 0.8:
        return "datetime_text_candidate"
    return "text"


def _missing_marker_counts(series: pd.Series) -> dict[str, int]:
    counts: dict[str, int] = {}
    text = series.dropna().astype(str).str.strip().str.casefold()
    for marker in sorted(TEXT_MISSING_CANDIDATES):
        count = int((text == marker.casefold()).sum())
        if count:
            counts[marker or "<blank>"] = count
    numeric = pd.to_numeric(series, errors="coerce")
    for marker in sorted(NUMERIC_MISSING_CANDIDATES):
        count = int((numeric == marker).sum())
        if count:
            counts[str(marker)] = count
    return counts


def _numeric_summary(series: pd.Series, numeric_ratio: float) -> dict[str, Any] | None:
    if not pd.api.types.is_numeric_dtype(series) and numeric_ratio < 0.9:
        return None
    numeric = pd.to_numeric(series, errors="coerce").dropna()
    if numeric.empty:
        return None
    return {
        "min": _json_value(numeric.min()),
        "q1": _json_value(numeric.quantile(0.25)),
        "median": _json_value(numeric.median()),
        "mean": _json_value(numeric.mean()),
        "q3": _json_value(numeric.quantile(0.75)),
        "max": _json_value(numeric.max()),
    }


def profile_frame(
    frame: pd.DataFrame,
    include_examples: bool,
    example_count: int,
    truncated: bool,
) -> dict[str, Any]:
    row_count = int(len(frame))
    columns = []
    key_candidates: list[str] = []
    categorical_candidates: list[str] = []
    duplicate_column_names = [
        str(name) for name in frame.columns[frame.columns.duplicated()].unique()
    ]
    for column_index, raw_name in enumerate(frame.columns):
        name = str(raw_name)
        series = frame.iloc[:, column_index]
        missing = int(series.isna().sum())
        non_null = row_count - missing
        unique = int(series.nunique(dropna=True))
        numeric_ratio, date_ratio = _parse_ratios(series)
        semantic = _semantic_candidate(
            series, non_null, unique, numeric_ratio, date_ratio
        )
        if row_count > 0 and missing == 0 and unique == row_count:
            key_candidates.append(name)
        if semantic == "categorical_candidate":
            categorical_candidates.append(name)
        item: dict[str, Any] = {
            "name": name,
            "position": column_index,
            "storage_dtype": str(series.dtype),
            "semantic_candidate": semantic,
            "non_null": non_null,
            "missing": missing,
            "missing_pct": round(missing / row_count * 100, 2) if row_count else None,
            "unique": unique,
            "unique_pct": round(unique / non_null * 100, 2) if non_null else None,
            "numeric_parse_ratio": round(numeric_ratio, 3),
            "datetime_parse_ratio": round(date_ratio, 3),
            "candidate_missing_markers": _missing_marker_counts(series),
        }
        summary = _numeric_summary(series, numeric_ratio)
        if summary is not None:
            item["numeric_summary"] = summary
        if include_examples:
            item["examples"] = [
                str(value)[:120]
                for value in series.dropna().drop_duplicates().head(example_count)
            ]
        columns.append(item)
    return {
        "rows_profiled": row_count,
        "column_count": int(frame.shape[1]),
        "truncated": truncated,
        "exact_duplicate_rows": int(frame.duplicated().sum()),
        "duplicate_column_names": duplicate_column_names,
        "single_column_key_candidates": key_candidates,
        "categorical_candidates": categorical_candidates,
        "columns": columns,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Profile research tables without modifying the input files."
    )
    parser.add_argument("files", nargs="+", type=Path)
    parser.add_argument("--sheet", help="Excel sheet name; defaults to the first sheet")
    parser.add_argument("--all-sheets", action="store_true")
    parser.add_argument("--max-rows", type=int)
    parser.add_argument("--include-examples", action="store_true")
    parser.add_argument("--example-count", type=int, default=3)
    parser.add_argument("--output", type=Path, default=Path("dataset_profile.json"))
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if args.max_rows is not None and args.max_rows <= 0:
        raise SystemExit("--max-rows must be positive")
    if args.example_count <= 0:
        raise SystemExit("--example-count must be positive")

    profiles = []
    for path in args.files:
        resolved = path.expanduser().resolve()
        if not resolved.is_file():
            raise SystemExit(f"Input does not exist: {resolved}")
        tables = _read_tables(resolved, args.sheet, args.all_sheets, args.max_rows)
        for sheet_name, frame, read_meta in tables:
            truncated = args.max_rows is not None and len(frame) > args.max_rows
            if truncated:
                frame = frame.head(args.max_rows).copy()
            profile = {
                "path": str(resolved),
                "format": resolved.suffix.lower().lstrip("."),
                "file_size_bytes": resolved.stat().st_size,
                "sheet": sheet_name,
                **read_meta,
                **profile_frame(
                    frame,
                    include_examples=args.include_examples,
                    example_count=args.example_count,
                    truncated=truncated,
                ),
            }
            profiles.append(profile)

    payload = {
        "profile_version": 1,
        "examples_included": bool(args.include_examples),
        "datasets": profiles,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"Profiled {len(profiles)} table(s) -> {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
