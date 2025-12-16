#!/usr/bin/env python3
"""
Generate a summary report of the MEP database and extracts.
Output: data/mep-contacts/extracts/SUMMARY.md
"""

from __future__ import annotations

import csv
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data" / "mep-contacts"
MASTER = DATA_DIR / "complete_mep_database.csv"
EXTRACT_DIR = DATA_DIR / "extracts"
SUMMARY = EXTRACT_DIR / "SUMMARY.md"


def load_rows(path: Path):
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def summarize_master(rows):
    group_counts = Counter(r.get("political_group") for r in rows)
    committee_counts = Counter()
    for r in rows:
        cm = (r.get("committee_memberships") or "").split(";")
        committee_counts.update([c.strip() for c in cm if c.strip()])
    role_counts = Counter()
    for r in rows:
        for tag in (r.get("role_tags") or "").split(";"):
            t = tag.strip()
            if t:
                role_counts[t] += 1
    return group_counts, committee_counts, role_counts


def summarize_extracts():
    summary = defaultdict(list)
    for path in EXTRACT_DIR.rglob("*.csv"):
        rows = load_rows(path)
        summary[path.parent.relative_to(EXTRACT_DIR)].append((path.name, len(rows)))
    return summary


def main():
    rows = load_rows(MASTER)
    group_counts, committee_counts, role_counts = summarize_master(rows)
    extracts = summarize_extracts()

    SUMMARY.parent.mkdir(parents=True, exist_ok=True)
    with SUMMARY.open("w", encoding="utf-8") as f:
        f.write("# MEP Database Summary\n\n")
        f.write(f"- Master rows (deduped): {len(rows)}\n")
        f.write(f"- Master source: {MASTER.relative_to(ROOT)}\n\n")

        f.write("## Political group counts\n")
        for g, n in group_counts.most_common():
            f.write(f"- {g}: {n}\n")
        f.write("\n")

        f.write("## Committee mentions (counts of committee strings)\n")
        for c, n in committee_counts.most_common():
            f.write(f"- {c}: {n}\n")
        f.write("\n")

        f.write("## Role tags\n")
        for r, n in role_counts.most_common():
            f.write(f"- {r}: {n}\n")
        f.write("\n")

        f.write("## Extract files\n")
        for folder, files in sorted(extracts.items()):
            f.write(f"### {folder}\n")
            for name, n in sorted(files):
                f.write(f"- {name}: {n} rows\n")
            f.write("\n")

    print(f"Wrote summary to {SUMMARY}")


if __name__ == "__main__":
    main()
