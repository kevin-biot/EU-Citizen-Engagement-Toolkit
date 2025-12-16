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

ROLE_TAGS = {
    "roberta.metsola@europarl.europa.eu": ["ep_president"],
    "sophie.wilmes@europarl.europa.eu": ["ep_vice_president"],
    "victor.negrescu@europarl.europa.eu": ["ep_vice_president"],
    "jan-christoph.oetjen@europarl.europa.eu": ["ep_vice_president"],
    "younous.omarjee@europarl.europa.eu": ["ep_vice_president"],
    "roberts.zile@europarl.europa.eu": ["ep_vice_president"],
    "david.mcallister@europarl.europa.eu": ["afet_chair"],
    "bernd.lange@europarl.europa.eu": ["inta_chair"],
    "ilhan.kyuchyuk@europarl.europa.eu": ["juri_chair"],
    "monika.hohlmeier@europarl.europa.eu": ["cont_chair"],
    "adam.jarubas@europarl.europa.eu": ["sant_chair"],
    "dolors.montserrat@europarl.europa.eu": ["peti_chair"],
    "borys.budka@europarl.europa.eu": ["itre_chair"],
    "anna.cavazzini@europarl.europa.eu": ["imco_chair"],
    "tomas.tobe@europarl.europa.eu": ["deve_chair"],
    "johan.vanovertveldt@europarl.europa.eu": ["budg_chair"],
    "veronika.vrecionova@europarl.europa.eu": ["agri_chair"],
    "tsvetelina.penkova@europarl.europa.eu": ["itre_vice_chair"],
    "elena.donazzan@europarl.europa.eu": ["itre_vice_chair"],
    "emil.radev@europarl.europa.eu": ["juri_vice_chair"],
    "riho.terras@europarl.europa.eu": ["sede_vice_chair"],
    # Rapporteurs / key files (digital)
    "andreas.schwab@europarl.europa.eu": ["dma_rapporteur"],
    "christel.schaldemose@europarl.europa.eu": ["dsa_rapporteur"],
    "brando.benifei@europarl.europa.eu": ["ai_act_co_rapporteur"],
    "axel.voss@europarl.europa.eu": ["ai_act_architect"],
}


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

    # Ensure role_tags column exists
    if "role_tags" not in master_header:
        master_header.append("role_tags")

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=master_header)
        writer.writeheader()
        for row in all_rows.values():
            email_key = (row.get("email") or "").lower().strip()
            tags = set(ROLE_TAGS.get(email_key, []))
            pb = (row.get("policy_briefs") or "").lower()
            cm = (row.get("committee_memberships") or "").lower()
            if "coordinator" in pb or "coordinator" in cm:
                tags.add("coordinator")
            if "rapporteur" in pb:
                tags.add("rapporteur")
            if "shadow" in pb:
                tags.add("shadow_rapporteur")
            row["role_tags"] = "; ".join(tags)
            writer.writerow(row)

    print(f"Wrote {len(all_rows)} rows to {OUTPUT}")


if __name__ == "__main__":
    main()
