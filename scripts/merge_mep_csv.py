#!/usr/bin/env python3
"""
Merge MEP CSV slices into a single deduplicated file.

Usage:
  python scripts/merge_mep_csv.py --output merged.csv base.csv slice1.csv slice2.csv ...

Behavior:
- Preserves header order from the first file.
- Deduplicates by mep_name (case-insensitive); if duplicate, keeps the first occurrence unless --prefer-latest is set.
- Optionally deduplicate by email using --key email.
"""

import argparse
import csv
from pathlib import Path


def parse_args():
    p = argparse.ArgumentParser(description="Merge MEP CSV slices deterministically.")
    p.add_argument("inputs", nargs="+", help="Input CSV files (header + data). Order matters.")
    p.add_argument("--output", required=True, help="Output merged CSV path")
    p.add_argument("--key", default="mep_name", choices=["mep_name", "email"], help="Deduplication key")
    p.add_argument(
        "--prefer-latest",
        action="store_true",
        help="If set, later files override earlier ones on duplicate key. Default keeps first seen.",
    )
    return p.parse_args()


def read_csv(path):
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    return reader.fieldnames, rows


def main():
    args = parse_args()
    key = args.key
    merged_rows = []
    seen = {}
    header = None

    for idx, input_path in enumerate(args.inputs):
        fields, rows = read_csv(input_path)
        if header is None:
            header = fields
        elif fields != header:
            raise SystemExit(f"Header mismatch in {input_path}. Expected {header}, found {fields}")

        for row in rows:
            k = (row.get(key) or "").lower()
            if not k:
                # skip rows without key
                continue
            if k in seen:
                if args.prefer-latest:
                    merged_rows[seen[k]] = row
                # else keep first occurrence
            else:
                seen[k] = len(merged_rows)
                merged_rows.append(row)

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=header)
        writer.writeheader()
        writer.writerows(merged_rows)


if __name__ == "__main__":
    main()
