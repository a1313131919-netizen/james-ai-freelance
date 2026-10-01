#!/usr/bin/env python3
"""Small CSV cleanup utility used as a self-initiated portfolio demo.

Features:
- normalizes column names to snake_case
- trims surrounding whitespace in string cells
- removes fully duplicate rows
- writes a cleaned CSV
- writes a JSON summary for auditability

Usage:
    python csv_cleaner.py input.csv cleaned.csv --summary summary.json
"""
from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path


def normalize_header(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9]+", "_", value)
    value = re.sub(r"_+", "_", value).strip("_")
    return value or "column"


def unique_headers(headers: list[str]) -> list[str]:
    counts: dict[str, int] = {}
    result: list[str] = []
    for header in headers:
        base = normalize_header(header)
        counts[base] = counts.get(base, 0) + 1
        suffix = "" if counts[base] == 1 else f"_{counts[base]}"
        result.append(base + suffix)
    return result


def clean_csv(input_path: Path, output_path: Path, summary_path: Path) -> dict:
    with input_path.open("r", encoding="utf-8-sig", newline="") as src:
        reader = csv.reader(src)
        rows = list(reader)

    if not rows:
        raise ValueError("Input CSV is empty.")

    headers = unique_headers(rows[0])
    cleaned_rows: list[list[str]] = []
    seen: set[tuple[str, ...]] = set()
    duplicate_count = 0

    for raw_row in rows[1:]:
        padded = raw_row + [""] * max(0, len(headers) - len(raw_row))
        trimmed = [cell.strip() for cell in padded[: len(headers)]]
        key = tuple(trimmed)
        if key in seen:
            duplicate_count += 1
            continue
        seen.add(key)
        cleaned_rows.append(trimmed)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as dst:
        writer = csv.writer(dst)
        writer.writerow(headers)
        writer.writerows(cleaned_rows)

    summary = {
        "input_file": str(input_path),
        "output_file": str(output_path),
        "input_rows_excluding_header": max(0, len(rows) - 1),
        "output_rows_excluding_header": len(cleaned_rows),
        "duplicates_removed": duplicate_count,
        "columns": headers,
    }
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Clean a CSV and produce an audit summary.")
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--summary", type=Path, default=Path("summary.json"))
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    summary = clean_csv(args.input, args.output, args.summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
