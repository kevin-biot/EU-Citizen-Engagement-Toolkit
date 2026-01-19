#!/usr/bin/env python3
"""
Quick query helper to filter MEPs from the canonical CSV.

Examples:
  python3 scripts/query_meps.py --committee IMCO --group EPP --role chair
  python3 scripts/query_meps.py --policy "ai act"
  python3 scripts/query_meps.py --country Germany --limit 10
"""

from __future__ import annotations

import argparse
import csv
import re
from pathlib import Path
from typing import Dict, Iterable, List

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data" / "mep-contacts"
INPUT_PRIMARY = DATA_DIR / "complete_mep_database.csv"
INPUT_TOPICS = DATA_DIR / "complete_mep_database_topics.csv"


def load_rows() -> List[Dict[str, str]]:
    source = INPUT_TOPICS if INPUT_TOPICS.exists() else INPUT_PRIMARY
    with source.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def matches_regex(value: str, patterns: Iterable[str]) -> bool:
    if not patterns:
        return True
    text = value or ""
    return all(re.search(pat, text, re.IGNORECASE) for pat in patterns)


def norm_group(group: str) -> str:
    g = group.lower()
    if "people's party" in g or g == "epp":
        return "EPP"
    if "socialists" in g or "s&d" in g:
        return "S&D"
    if "renew" in g:
        return "RENEW"
    if "greens" in g or "efa" in g:
        return "GREENS_EFA"
    if "conservatives and reformists" in g or g == "ecr":
        return "ECR"
    if "patriots for europe" in g or g == "pfe":
        return "PFE"
    if "left" in g:
        return "LEFT"
    if "sovereign nations" in g or g == "esn":
        return "ESN"
    if "non-attached" in g or g == "ni":
        return "NI"
    return group or "UNKNOWN"


def main() -> None:
    parser = argparse.ArgumentParser(description="Query MEP database.")
    parser.add_argument("--committee", help="Committee code (e.g., IMCO, ITRE, LIBE, JURI)")
    parser.add_argument("--group", help="Political group code")
    parser.add_argument("--role", help="Role tag or substring (chair, vice, president, coordinator)")
    parser.add_argument("--country", help="Jurisdiction/country")
    parser.add_argument("--policy", help="Substring/regex to match in policy_briefs")
    parser.add_argument("--topic", help="Topic tag to match in topic_tags (e.g., women-rights)")
    parser.add_argument("--limit", type=int, default=0, help="Limit results")
    args = parser.parse_args()

    rows = load_rows()
    results = []
    for r in rows:
        if args.group and norm_group(r.get("political_group", "")) != args.group:
            continue
        if args.country and (r.get("jurisdiction") or "") != args.country:
            continue
        if args.committee and not re.search(args.committee, r.get("committee_memberships", ""), re.IGNORECASE):
            continue
        if args.role and not re.search(args.role, r.get("role_tags", ""), re.IGNORECASE):
            continue
        if args.policy and not re.search(args.policy, r.get("policy_briefs", ""), re.IGNORECASE):
            continue
        if args.topic and not re.search(args.topic, r.get("topic_tags", ""), re.IGNORECASE):
            continue
        results.append(r)

    if args.limit:
        results = results[: args.limit]

    cols = [
        "mep_name",
        "jurisdiction",
        "political_group",
        "email",
        "committee_memberships",
        "role_tags",
        "policy_briefs",
        "topic_tags",
    ]
    for r in results:
        print(" | ".join(r.get(c, "") for c in cols))
    print(f"\nTotal: {len(results)}")


if __name__ == "__main__":
    main()
