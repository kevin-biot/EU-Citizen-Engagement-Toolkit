#!/usr/bin/env python3
"""
Build a canonical CSV of all MEPs by extracting CSV code blocks from the markdown slices.

Source files:
- data/mep-contacts/mep-database.md
- data/mep-contacts/mep-database-step-2.md
- data/mep-contacts/mep-database-step-3.md
- data/mep-contacts/mep-database-step-4.md

Output:
- data/mep-contacts/complete_mep_database.csv

Deduplication:
- Primary key: email (lowercased)
- Fallback: mep_name (lowercased) if email is missing
"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Iterable, List, Dict

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data" / "mep-contacts"
OUTPUT = DATA_DIR / "complete_mep_database.csv"

SOURCE_FILES = [
    DATA_DIR / "mep-database.md",
    DATA_DIR / "mep-database-step-2.md",
    DATA_DIR / "mep-database-step-3.md",
    DATA_DIR / "mep-database-step-4.md",
]


def extract_blocks(md_text: str) -> Iterable[List[str]]:
    """Yield each CSV code block as a list of lines (including header row)."""
    in_code = False
    current: List[str] = []
    for line in md_text.splitlines():
        stripped = line.strip()
        if stripped.startswith("```"):
            if in_code and current:
                yield current
                current = []
            in_code = not in_code
            continue
        if not in_code or not stripped:
            continue
        current.append(stripped)
    if in_code and current:
        yield current


def parse_csv_block(lines: List[str]) -> Iterable[Dict[str, str]]:
    header = lines[0].split(",")
    reader = csv.DictReader(lines[1:], fieldnames=header)
    for row in reader:
        yield header, row


def main() -> None:
    all_rows: Dict[str, Dict[str, str]] = {}
    master_header: List[str] | None = None

    for path in SOURCE_FILES:
        text = path.read_text(encoding="utf-8")
        for block in extract_blocks(text):
            if not block:
                continue
            header = block[0].split(",")
            if master_header is None:
                master_header = header
            elif master_header != header:
                raise SystemExit(f"Header mismatch in {path.name}: {header} != {master_header}")
            for _, row in parse_csv_block(block):
                key = (row.get("email") or "").lower().strip() or (row.get("mep_name") or "").lower().strip()
                if not key:
                    continue
                all_rows.setdefault(key, row)

    if not master_header:
        raise SystemExit("No data extracted; check source files.")

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=master_header)
        writer.writeheader()
        writer.writerows(all_rows.values())

    print(f"Wrote {len(all_rows)} rows to {OUTPUT}")


if __name__ == "__main__":
    main()
