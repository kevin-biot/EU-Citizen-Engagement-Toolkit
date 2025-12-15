#!/usr/bin/env python3
"""
Validation helper for MEP extraction outputs.

Checks:
- Total rows in master database
- Counts per political group extract
- Duplicate emails/names
- Email format sanity
"""

from __future__ import annotations

import csv
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data" / "mep-contacts"
MASTER = DATA_DIR / "complete_mep_database.csv"
EXTRACT_DIR = DATA_DIR / "extracts"


def load_rows(path: Path):
    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return list(reader)


def count_duplicates(rows):
    keys = [(r.get("email") or "").lower().strip() or (r.get("mep_name") or "").lower().strip() for r in rows]
    c = Counter(keys)
    dups = {k: v for k, v in c.items() if v > 1 and k}
    return dups


def invalid_emails(rows):
    bad = []
    pattern = re.compile(r"^[A-Za-z0-9_.+-]+@[A-Za-z0-9.-]+$")
    for r in rows:
        email = r.get("email") or ""
        if email and not pattern.match(email):
            bad.append(email)
    return bad


def main():
    master_rows = load_rows(MASTER)
    print(f"Master rows (incl. header not counted): {len(master_rows)}")

    dups = count_duplicates(master_rows)
    print(f"Duplicate keys in master: {len(dups)}")
    if dups:
        print("  Sample duplicates:", list(dups.items())[:5])

    bad_emails = invalid_emails(master_rows)
    print(f"Invalid email formats: {len(bad_emails)}")

    # Group extracts summary
    group_dir = EXTRACT_DIR / "groups"
    if group_dir.exists():
        for p in sorted(group_dir.glob("*.csv")):
            rows = load_rows(p)
            print(f"{p.name}: {len(rows)} rows")


if __name__ == "__main__":
    main()
