#!/usr/bin/env python3
"""
Produce a committee x role x group matrix to highlight gatekeepers.

Output:
  data/mep-contacts/extracts/committee_role_matrix.md
"""

from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data" / "mep-contacts"
MASTER = DATA_DIR / "complete_mep_database.csv"
OUTPUT = DATA_DIR / "extracts" / "committee_role_matrix.md"

GATEKEEPER_ROLES = {"chair", "vice_chair", "coordinator", "rapporteur", "shadow_rapporteur", "ep_president", "ep_vice_president"}
CORE_COMMITTEES = ["IMCO", "ITRE", "LIBE", "JURI", "ECON", "AFET", "ENVI", "INTA", "AFCO", "BUDG", "CONT"]


def load_rows(path: Path):
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def main():
    rows = load_rows(MASTER)
    # committee -> role -> group -> list of meps
    matrix = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))

    for r in rows:
        comms = [c.strip() for c in (r.get("committee_memberships") or "").split(";") if c.strip()]
        roles = [t.strip() for t in (r.get("role_tags") or "").split(";") if t.strip()]
        group = r.get("political_group") or ""
        for c in comms:
            for role in roles:
                if role in GATEKEEPER_ROLES:
                    matrix[c][role][group].append(r["mep_name"])

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT.open("w", encoding="utf-8") as f:
        f.write("# Committee × Role × Group Matrix (Gatekeepers)\n\n")
        f.write("Focus on roles: chair, vice_chair, coordinator, rapporteur, shadow_rapporteur, EP leadership.\n\n")
        for c in sorted(matrix.keys(), key=lambda x: (0 if x in CORE_COMMITTEES else 1, x)):
            f.write(f"## {c}\n")
            role_map = matrix[c]
            for role, group_map in sorted(role_map.items()):
                f.write(f"- **{role}**\n")
                for g, meps in sorted(group_map.items()):
                    f.write(f"  - {g}: {', '.join(sorted(set(meps)))}\n")
            f.write("\n")

    print(f"Wrote matrix to {OUTPUT}")


if __name__ == "__main__":
    main()
