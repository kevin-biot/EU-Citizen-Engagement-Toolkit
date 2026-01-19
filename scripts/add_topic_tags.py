#!/usr/bin/env python3
"""
Apply topic overlays (e.g., women-rights) to the master MEP CSV.

Usage:
  python3 scripts/add_topic_tags.py \
    --base data/mep-contacts/complete_mep_database.csv \
    --overlay data/mep-contacts/overlays/women-rights.csv \
    --out data/mep-contacts/complete_mep_database_topics.csv
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import Dict, List

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_BASE = ROOT / "data" / "mep-contacts" / "complete_mep_database.csv"
DEFAULT_OUT = ROOT / "data" / "mep-contacts" / "complete_mep_database_topics.csv"


def read_csv(path: Path) -> List[Dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def load_overlays(paths: List[Path]) -> Dict[str, List[str]]:
    tags_by_name: Dict[str, List[str]] = {}
    for p in paths:
        for row in read_csv(p):
            name = row.get("mep_name", "").strip()
            if not name:
                continue
            tags = [t.strip() for t in (row.get("topic_tags", "") or "").split(",") if t.strip()]
            if not tags:
                continue
            if name not in tags_by_name:
                tags_by_name[name] = []
            for t in tags:
                if t not in tags_by_name[name]:
                    tags_by_name[name].append(t)
    return tags_by_name


def main() -> None:
    parser = argparse.ArgumentParser(description="Add topic_tags to MEP CSV using overlay files.")
    parser.add_argument("--base", type=Path, default=DEFAULT_BASE, help="Base CSV (canonical MEP list)")
    parser.add_argument(
        "--overlay",
        type=Path,
        action="append",
        required=True,
        help="Overlay CSV with mep_name,topic_tags",
    )
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT, help="Output CSV with topic_tags column")
    args = parser.parse_args()

    base_rows = read_csv(args.base)
    overlays = load_overlays(args.overlay)

    # Ensure topic_tags column exists
    fieldnames = list(base_rows[0].keys())
    if "topic_tags" not in fieldnames:
        fieldnames.append("topic_tags")

    for row in base_rows:
        name = row.get("mep_name", "").strip()
        existing = [t.strip() for t in (row.get("topic_tags", "") or "").split(",") if t.strip()]
        merged = existing[:]
        for t in overlays.get(name, []):
            if t not in merged:
                merged.append(t)
        row["topic_tags"] = ", ".join(merged)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(base_rows)

    print(f"Wrote {len(base_rows)} rows with topic tags to {args.out}")


if __name__ == "__main__":
    main()
