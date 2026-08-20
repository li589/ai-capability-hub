#!/usr/bin/env python3
"""Apply explicit, configuration-driven transformations to one research table.

The source file is never overwritten. The script does not infer scientific
semantics, choose statistical methods, validate reports, or render outputs.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

try:
    import pandas as pd
except ImportError:
    print("This script requires pandas and, for XLSX, openpyxl.", file=sys.stderr)
    raise SystemExit(2)


READ_OPTION_KEYS = {"dtype", "header", "skiprows", "usecols", "keep_default_na"}
SUPPORTED_TYPES = {"string", "numeric", "integer", "date", "datetime", "boolean", "category"}


def _resolve(base: Path, value: str | Path) -> Path:
    path = Path(value).expanduser()
    return path.resolve() if path.is_absolute() else (base / path).resolve()


def _read_table(path: Path, sheet: str | int | None, options: dict[str, Any]) -> pd.DataFrame:
    unknown = sorted(set(options) - READ_OPTION_KEYS)
    if unknown:
        raise ValueError(f"Unsupported read_options: {unknown}")
    suffix = path.suffix.lower()
    if suffix in {".xlsx", ".xls"}:
        return pd.read_excel(path, sheet_name=sheet if sheet is not None else 0, **options)
    if suffix in {".csv", ".tsv", ".txt"}:
        separator = "\t" if suffix == ".tsv" else None
        errors = []
        for encoding in ("utf-8-sig", "utf-8", "gb18030"):
            try:
                return pd.read_csv(
                    path,
                    encoding=encoding,
                    sep=separator,
                    engine="python" if separator is None else "c",
                    **options,
                )
            except (UnicodeDecodeError, pd.errors.ParserError) as exc:
                errors.append(f"{encoding}:{type(exc).__name__}")
        raise ValueError(f"Unable to read {path}; attempts: {', '.join(errors)}")
    raise ValueError(f"Unsupported input format: {suffix}")


def _write_table(frame: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    suffix = path.suffix.lower()
    if suffix == ".xlsx":
        frame.to_excel(path, index=False, engine="openpyxl")
    elif suffix == ".csv":
        frame.to_csv(path, index=False, encoding="utf-8-sig")
    elif suffix == ".tsv":
        frame.to_csv(path, index=False, encoding="utf-8", sep="\t")
    else:
        raise ValueError("Output must end in .csv, .tsv, or .xlsx")


def _require_columns(frame: pd.DataFrame, columns: list[str], context: str) -> None:
    missing = [column for column in columns if column not in frame.columns]
    if missing:
        raise ValueError(f"Missing columns for {context}: {missing}")


def _replace_missing(frame: pd.DataFrame, rules: dict[str, list[Any]]) -> list[dict[str, Any]]:
    actions: list[dict[str, Any]] = []
    global_markers = rules.get("*", [])
    for column in frame.columns:
        markers = [*global_markers, *rules.get(str(column), [])]
        if not markers:
            continue
        before = int(frame[column].isna().sum())
        frame[column] = frame[column].replace(markers, pd.NA)
        after = int(frame[column].isna().sum())
        if after > before:
            actions.append(
                {
                    "action": "replace_missing",
                    "column": str(column),
                    "new_missing": after - before,
                }
            )
    unknown_columns = sorted(set(rules) - {"*"} - {str(c) for c in frame.columns})
    if unknown_columns:
        raise ValueError(f"missing_values refers to absent columns: {unknown_columns}")
    return actions


def _boolean_series(series: pd.Series, spec: dict[str, Any], errors: str) -> pd.Series:
    true_values = spec.get("true_values", [True, 1, "1", "true", "yes", "y"])
    false_values = spec.get("false_values", [False, 0, "0", "false", "no", "n"])
    true_set = {str(value).strip().casefold() for value in true_values}
    false_set = {str(value).strip().casefold() for value in false_values}

    def convert(value: Any) -> Any:
        if pd.isna(value):
            return pd.NA
        normalized = str(value).strip().casefold()
        if normalized in true_set:
            return True
        if normalized in false_set:
            return False
        if errors == "coerce":
            return pd.NA
        raise ValueError(f"Cannot parse boolean value: {value!r}")

    return series.map(convert).astype("boolean")


def _convert_column(series: pd.Series, spec: str | dict[str, Any]) -> tuple[pd.Series, dict[str, Any]]:
    cfg = {"type": spec} if isinstance(spec, str) else dict(spec)
    target = cfg.get("type")
    errors = cfg.get("errors", "raise")
    if target not in SUPPORTED_TYPES:
        raise ValueError(f"Unsupported target type: {target}")
    if errors not in {"raise", "coerce"}:
        raise ValueError("type conversion errors must be 'raise' or 'coerce'")

    before_non_null = series.notna()
    if target == "string":
        converted = series.astype("string")
    elif target == "numeric":
        converted = pd.to_numeric(series, errors=errors)
    elif target == "integer":
        numeric = pd.to_numeric(series, errors=errors)
        fractional = numeric.dropna().mod(1).ne(0)
        if fractional.any():
            if errors == "raise":
                raise ValueError("Non-integer values found during integer conversion")
            numeric.loc[fractional[fractional].index] = pd.NA
        converted = numeric.astype("Int64")
    elif target in {"date", "datetime"}:
        converted = pd.to_datetime(
            series,
            errors=errors,
            format=cfg.get("format"),
            dayfirst=bool(cfg.get("dayfirst", False)),
            utc=bool(cfg.get("utc", False)),
        )
        if target == "date":
            converted = converted.dt.date
    elif target == "boolean":
        converted = _boolean_series(series, cfg, errors)
    else:
        converted = series.astype("category")

    failed = int((before_non_null & pd.isna(converted)).sum())
    return converted, {"target_type": target, "coerced_to_missing": failed}


def _reshape(frame: pd.DataFrame, spec: dict[str, Any]) -> tuple[pd.DataFrame, dict[str, Any]]:
    mode = spec.get("mode")
    if mode != "wide_to_long":
        raise ValueError("Only reshape.mode='wide_to_long' is supported")
    id_columns = list(spec.get("id_columns", []))
    value_columns = list(spec.get("value_columns", []))
    if not value_columns:
        raise ValueError("reshape.value_columns must be explicit")
    _require_columns(frame, [*id_columns, *value_columns], "reshape")
    variable_name = spec.get("variable_name", "variable")
    value_name = spec.get("value_name", "value")
    before_rows = len(frame)
    reshaped = frame.melt(
        id_vars=id_columns,
        value_vars=value_columns,
        var_name=variable_name,
        value_name=value_name,
    )
    return reshaped, {
        "action": "wide_to_long",
        "rows_before": before_rows,
        "rows_after": len(reshaped),
        "value_columns": value_columns,
    }


def normalize(config: dict[str, Any], config_dir: Path) -> dict[str, Any]:
    input_spec = config.get("input", {})
    output_spec = config.get("output", {})
    if "path" not in input_spec or "path" not in output_spec:
        raise ValueError("config requires input.path and output.path")

    input_path = _resolve(config_dir, input_spec["path"])
    output_path = _resolve(config_dir, output_spec["path"])
    if not input_path.is_file():
        raise ValueError(f"Input does not exist: {input_path}")
    if input_path == output_path:
        raise ValueError("Output path must differ from input path")

    frame = _read_table(
        input_path,
        input_spec.get("sheet"),
        dict(input_spec.get("read_options", {})),
    )
    summary: dict[str, Any] = {
        "normalization_version": 1,
        "input": str(input_path),
        "output": str(output_path),
        "rows_before": int(len(frame)),
        "columns_before": [str(column) for column in frame.columns],
        "actions": [],
    }

    rename = dict(config.get("rename", {}))
    if rename:
        _require_columns(frame, list(rename), "rename")
        if len(set(rename.values())) != len(rename.values()):
            raise ValueError("rename contains duplicate target names")
        frame = frame.rename(columns=rename)
        if frame.columns.duplicated().any():
            duplicates = sorted({str(c) for c in frame.columns[frame.columns.duplicated()]})
            raise ValueError(f"rename creates duplicate columns: {duplicates}")
        summary["actions"].append({"action": "rename", "mapping": rename})

    if config.get("trim_strings", False):
        changed = 0
        for column in frame.columns:
            if pd.api.types.is_object_dtype(frame[column]) or pd.api.types.is_string_dtype(frame[column]):
                original = frame[column]
                trimmed = original.map(lambda value: value.strip() if isinstance(value, str) else value)
                changed += int((original.fillna("<NA>") != trimmed.fillna("<NA>")).sum())
                frame[column] = trimmed
        summary["actions"].append({"action": "trim_strings", "changed_cells": changed})

    missing_rules = dict(config.get("missing_values", {}))
    if missing_rules:
        summary["actions"].extend(_replace_missing(frame, missing_rules))

    type_rules = dict(config.get("types", {}))
    if type_rules:
        _require_columns(frame, list(type_rules), "types")
        for column, spec in type_rules.items():
            frame[column], detail = _convert_column(frame[column], spec)
            summary["actions"].append(
                {"action": "convert_type", "column": column, **detail}
            )

    reshape_spec = config.get("reshape")
    if reshape_spec:
        frame, detail = _reshape(frame, dict(reshape_spec))
        summary["actions"].append(detail)

    if config.get("drop_exact_duplicates", False):
        before = len(frame)
        frame = frame.drop_duplicates().copy()
        summary["actions"].append(
            {"action": "drop_exact_duplicates", "removed_rows": before - len(frame)}
        )

    sort_by = list(config.get("sort_by", []))
    if sort_by:
        _require_columns(frame, sort_by, "sort_by")
        frame = frame.sort_values(sort_by, kind="stable")
        summary["actions"].append({"action": "sort", "columns": sort_by})

    _write_table(frame, output_path)
    summary["rows_after"] = int(len(frame))
    summary["columns_after"] = [str(column) for column in frame.columns]

    summary_path_value = output_spec.get("summary")
    if summary_path_value:
        summary_path = _resolve(config_dir, summary_path_value)
        summary_path.parent.mkdir(parents=True, exist_ok=True)
        summary_path.write_text(
            json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        summary["summary_path"] = str(summary_path)
    return summary


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Apply explicit transformations to a derived research table."
    )
    parser.add_argument("--config", required=True, type=Path)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    config_path = args.config.expanduser().resolve()
    if not config_path.is_file():
        raise SystemExit(f"Config does not exist: {config_path}")
    config = json.loads(config_path.read_text(encoding="utf-8"))
    summary = normalize(config, config_path.parent)
    print(
        f"Normalized {summary['rows_before']} -> {summary['rows_after']} rows: "
        f"{summary['output']}"
    )
    if summary.get("summary_path"):
        print(f"Summary: {summary['summary_path']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
