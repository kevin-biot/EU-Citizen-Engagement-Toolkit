#!/usr/bin/env python3
"""
Generate filtered CSV subsets from the canonical MEP database.

Input:
  data/mep-contacts/complete_mep_database.csv

Outputs:
  data/mep-contacts/extracts/... (group, committee, policy, country, strategic subsets)

Filtering is done in Python (no shell grep), with deduplication by email (fallback to mep_name).
"""

from __future__ import annotations

import csv
import re
from collections import defaultdict
from pathlib import Path
from typing import Callable, Dict, Iterable, List

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data" / "mep-contacts"
INPUT = DATA_DIR / "complete_mep_database.csv"
OUT_BASE = DATA_DIR / "extracts"
COMMITTEES = ["IMCO", "ITRE", "LIBE", "JURI", "ECON"]
TOP_COUNTRIES = ["Germany", "France", "Italy", "Spain", "Poland", "Romania", "Netherlands", "Belgium", "Greece", "Czechia"]
GATEKEEPER_COMMITTEES = ["IMCO", "ITRE", "LIBE", "JURI", "ECON"]


def load_rows() -> List[Dict[str, str]]:
    with INPUT.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    # Deduplicate by email, fallback to name
    seen = set()
    unique = []
    for row in rows:
        key = (row.get("email") or "").lower().strip() or (row.get("mep_name") or "").lower().strip()
        if not key or key in seen:
            continue
        seen.add(key)
        unique.append(row)
    return unique


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def write_csv(path: Path, header: List[str], rows: Iterable[Dict[str, str]]) -> int:
    ensure_dir(path.parent)
    rows_list = list(rows)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=header)
        writer.writeheader()
        writer.writerows(rows_list)
    return len(rows_list)


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


def filter_contains(field: str, patterns: List[str]) -> Callable[[Dict[str, str]], bool]:
    regex = re.compile("|".join(patterns), re.IGNORECASE)
    return lambda row: bool(regex.search(row.get(field, "")))


def filter_committees(patterns: List[str]) -> Callable[[Dict[str, str]], bool]:
    regex = re.compile("|".join(patterns), re.IGNORECASE)
    return lambda row: bool(regex.search(row.get("committee_memberships", "")))


def main() -> None:
    rows = load_rows()
    header = list(rows[0].keys()) if rows else []

    # Phase 1: Political groups
    group_targets = ["EPP", "S&D", "RENEW", "GREENS_EFA", "ECR", "PFE", "LEFT", "ESN", "NI"]
    group_rows = defaultdict(list)
    for row in rows:
        code = norm_group(row.get("political_group", ""))
        group_rows[code].append(row)
    for code in group_targets:
        write_csv(OUT_BASE / "groups" / f"{code}_meps.csv", header, group_rows.get(code, []))

    # Phase 2: Policy focus
    policy_filters = {
        "AI_Act_experts.csv": filter_contains("policy_briefs", ["ai act", "ai governance", "artificial intelligence"]),
        "Digital_Services_experts.csv": filter_contains(
            "policy_briefs", ["digital services", r"\bDSA\b", "digital markets act", r"\bDMA\b"]
        ),
        "Cybersecurity_experts.csv": filter_contains(
            "policy_briefs", ["cybersecurity", r"\bcyber\b", "NIS2", "network security"]
        ),
        "Data_Protection_experts.csv": filter_contains(
            "policy_briefs", ["data protection", "GDPR", "privacy", "data governance"]
        ),
        "Digital_Infrastructure_experts.csv": filter_contains(
            "policy_briefs", ["digital infrastructure", "telecommunications", r"\b5g\b", "connectivity"]
        ),
        "Research_Innovation_experts.csv": filter_contains(
            "policy_briefs", ["horizon europe", "research funding", "innovation", "R&D", "research and development"]
        ),
        "Digital_Economy_experts.csv": filter_contains(
            "policy_briefs", ["digital economy", "fintech", "digital euro", "digital taxation"]
        ),
        "Industrial_Digital_Transformation.csv": filter_contains(
            "policy_briefs", ["industry"] + ["digital", "ai", "automation"]
        ),
    }
    for name, predicate in policy_filters.items():
        write_csv(OUT_BASE / "policy" / name, header, filter(predicate, rows))

    # Phase 3: Committees
    for c in COMMITTEES:
        write_csv(
            OUT_BASE / "committees" / f"{c}_members.csv",
            header,
            filter(filter_committees([rf"\b{re.escape(c)}\b"]), rows),
        )

    # Phase 4: Leadership and power
    leadership_pred = filter_contains("policy_briefs", ["president", "vice-president", "chair"])
    write_csv(OUT_BASE / "leadership" / "EP_Leadership.csv", header, filter(leadership_pred, rows))

    digital_leadership_pred = lambda row: (
        filter_committees(["IMCO", "ITRE", "LIBE", "JURI"])(row)
        and filter_contains("committee_memberships", ["Chair", "Vice-Chair"])(row)
    )
    write_csv(
        OUT_BASE / "leadership" / "Digital_Committee_Leadership.csv",
        header,
        filter(digital_leadership_pred, rows),
    )

    coordinators_pred = lambda row: (
        filter_contains("policy_briefs", ["coordinator"])(row)
        and filter_committees(["IMCO", "ITRE", "LIBE", "JURI"])(row)
    )
    write_csv(
        OUT_BASE / "leadership" / "Digital_Committee_Coordinators.csv",
        header,
        filter(coordinators_pred, rows),
    )

    rapporteur_pred = lambda row: (
        filter_contains("policy_briefs", ["rapporteur"])(row)
        and filter_contains(
            "policy_briefs",
            ["ai act", "digital services", "data act", "digital markets", "nis2", "cybersecurity"],
        )(row)
    )
    write_csv(
        OUT_BASE / "leadership" / "Digital_Rapporteurs.csv",
        header,
        filter(rapporteur_pred, rows),
    )

    # Phase 5: Countries (top 10 by count)
    for country in TOP_COUNTRIES:
        write_csv(
            OUT_BASE / "countries" / f"{country}_meps.csv",
            header,
            filter(lambda r, c=country: r.get("jurisdiction") == c, rows),
        )

    # Phase 6: Strategic subsets
    def load_csv(path: Path) -> List[Dict[str, str]]:
        with path.open(newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            return list(reader)

    def dedupe_by_email(items: Iterable[Dict[str, str]]) -> List[Dict[str, str]]:
        seen = set()
        out = []
        for r in items:
            key = (r.get("email") or "").lower().strip() or (r.get("mep_name") or "").lower().strip()
            if not key or key in seen:
                continue
            seen.add(key)
            out.append(r)
        return out

    # AI Act Coalition: AI experts + IMCO + LIBE + ITRE
    coalition_rows = dedupe_by_email(
        load_csv(OUT_BASE / "policy" / "AI_Act_experts.csv")
        + load_csv(OUT_BASE / "committees" / "IMCO_members.csv")
        + load_csv(OUT_BASE / "committees" / "LIBE_members.csv")
        + load_csv(OUT_BASE / "committees" / "ITRE_members.csv")
    )
    write_csv(OUT_BASE / "strategic" / "AI_Act_Coalition.csv", header, coalition_rows)

    digital_rights_pred = filter_contains(
        "policy_briefs", ["digital rights", "privacy", "data protection", "algorithmic accountability"]
    )
    write_csv(
        OUT_BASE / "strategic" / "Digital_Rights_Champions.csv",
        header,
        filter(digital_rights_pred, rows),
    )

    tech_industry_pred = filter_contains(
        "policy_briefs", ["digital economy", "innovation", "competitiveness", "industrial"]
    )
    write_csv(OUT_BASE / "strategic" / "Tech_Industry_Contacts.csv", header, filter(tech_industry_pred, rows))

    # EU AI Governance Taskforce: leadership + AI + data protection
    taskforce_rows = dedupe_by_email(
        load_csv(OUT_BASE / "leadership" / "Digital_Committee_Leadership.csv")
        + load_csv(OUT_BASE / "policy" / "AI_Act_experts.csv")
        + load_csv(OUT_BASE / "policy" / "Data_Protection_experts.csv")
    )
    write_csv(OUT_BASE / "strategic" / "EU_AI_Governance_Taskforce.csv", header, taskforce_rows)

    # Lane² specific
    compliance_pred = lambda r: (
        filter_contains("policy_briefs", ["compliance", "enforcement", "oversight"])(r)
        and filter_committees(["IMCO", "LIBE"])(r)
    )
    write_csv(
        OUT_BASE / "lane2" / "AI_Compliance_Infrastructure_Targets.csv",
        header,
        filter(compliance_pred, rows),
    )

    telco_pred = filter_contains("policy_briefs", ["telecommunications", "5g", "connectivity", "digital infrastructure"])
    write_csv(
        OUT_BASE / "lane2" / "Telecommunications_Digital_Transformation.csv",
        header,
        filter(telco_pred, rows),
    )

    coord_pred = filter_contains("policy_briefs", ["coordination", "harmonization", "interoperability"])
    write_csv(
        OUT_BASE / "lane2" / "Cross_Border_AI_Coordination.csv",
        header,
        filter(coord_pred, rows),
    )

    single_market_pred = lambda r: filter_committees(["IMCO"])(r) and filter_contains(
        "policy_briefs", ["digital single market"]
    )(r)
    write_csv(
        OUT_BASE / "lane2" / "Digital_Single_Market_Champions.csv",
        header,
        filter(single_market_pred, rows),
    )

    # Gatekeepers: role_tags present and committee matches
    role_regex = re.compile(r"(chair|vice)", re.IGNORECASE)
    gatekeepers = [
        r
        for r in rows
        if (r.get("role_tags") or "") and role_regex.search(r.get("role_tags", ""))
        and filter_committees(GATEKEEPER_COMMITTEES)(r)
    ]
    write_csv(OUT_BASE / "gatekeepers" / "all_gatekeepers.csv", header, gatekeepers)
    for c in GATEKEEPER_COMMITTEES:
        write_csv(
            OUT_BASE / "gatekeepers" / f"{c}_gatekeepers.csv",
            header,
            filter(lambda r, c=c: filter_committees([c])(r) and (r.get("role_tags") or ""), gatekeepers),
        )


if __name__ == "__main__":
    main()
