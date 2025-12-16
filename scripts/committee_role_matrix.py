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

COMMITTEE_DESCRIPTIONS = {
    "AFET": "Foreign Affairs",
    "AFCO": "Constitutional Affairs",
    "AGRI": "Agriculture and Rural Development",
    "ANIT": "Animal Transport (special)",
    "AIDA": "Artificial Intelligence in the Digital Age (historical)",
    "BUDG": "Budgets",
    "CONT": "Budgetary Control",
    "CULT": "Culture and Education",
    "DEVE": "Development",
    "DROI": "Human Rights (Subcommittee)",
    "DMER": "Common Market for Medicines (special)",
    "EUDS": "European Democracy Shield (special)",
    "ECON": "Economic and Monetary Affairs",
    "EMPL": "Employment and Social Affairs",
    "ENVI": "Environment, Public Health, Food Safety",
    "FEMM": "Women's Rights and Gender Equality",
    "FISC": "Tax Matters (Subcommittee)",
    "HOUS": "Housing Crisis (special)",
    "IMCO": "Internal Market and Consumer Protection",
    "INTA": "International Trade",
    "ITRE": "Industry, Research, Energy",
    "JURI": "Legal Affairs",
    "LIBE": "Civil Liberties, Justice, Home Affairs",
    "PECH": "Fisheries",
    "PETI": "Petitions",
    "REGI": "Regional Development",
    "SANT": "Public Health (Subcommittee)",
    "SEDE": "Security and Defence",
    "TRAN": "Transport and Tourism",
}

ROLE_DESCRIPTIONS = {
    "chair": "Leads the committee; sets agendas and steers files.",
    "vice_chair": "Deputy to the chair; can lead in chair’s absence.",
    "coordinator": "Negotiates for their political group within the committee; key gatekeeper for group positions.",
    "rapporteur": "Primary author/negotiator on a legislative file.",
    "shadow_rapporteur": "Group’s negotiator shadowing the rapporteur on a file.",
    "ep_president": "Presides over Parliament; sets overall agenda.",
    "ep_vice_president": "Deputy to the President; can chair sessions and represent Parliament.",
}


def load_rows(path: Path):
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def main():
    rows = load_rows(MASTER)
    # committee -> role -> group -> list of (name, email)
    matrix = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))

    for r in rows:
        comms = [c.strip() for c in (r.get("committee_memberships") or "").split(";") if c.strip()]
        roles = [t.strip() for t in (r.get("role_tags") or "").split(";") if t.strip()]
        group = r.get("political_group") or ""
        for c in comms:
            for role in roles:
                if role in GATEKEEPER_ROLES:
                    matrix[c][role][group].append((r["mep_name"], r.get("email", "")))

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT.open("w", encoding="utf-8") as f:
        f.write("# Committee × Role × Group Matrix (Gatekeepers)\n\n")
        f.write("Focus on roles: chair, vice_chair, coordinator, rapporteur, shadow_rapporteur, EP leadership.\n\n")
        f.write("## Role definitions\n")
        for role, desc in ROLE_DESCRIPTIONS.items():
            f.write(f"- **{role}**: {desc}\n")
        f.write("\n")

        for c in sorted(matrix.keys(), key=lambda x: (0 if x in CORE_COMMITTEES else 1, x)):
            desc = COMMITTEE_DESCRIPTIONS.get(c, "")
            title = f"{c} — {desc}" if desc else c
            f.write(f"## {title}\n")
            role_map = matrix[c]
            for role, group_map in sorted(role_map.items()):
                f.write(f"- **{role}**\n")
                for g, meps in sorted(group_map.items()):
                    uniq = {(name, email) for name, email in meps}
                    formatted = [f"{name} ({email})" if email else name for name, email in sorted(uniq)]
                    f.write(f"  - {g}: {', '.join(formatted)}\n")
            f.write("\n")

    print(f"Wrote matrix to {OUTPUT}")


if __name__ == "__main__":
    main()
