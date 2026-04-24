#!/usr/bin/env python3
"""
Build scoped committee leadership tags from the official current European Parliament
committee member pages.

Output:
- data/mep-contacts/committee-leadership-tags.csv

The output is used by build_complete_csv.py to add tags such as:
- femm_chair
- femm_vice_chair
- econ_chair
- econ_vice_chair

Only committees with a live members page are included.
"""

from __future__ import annotations

import csv
import html
import re
import unicodedata
from datetime import date
from pathlib import Path
from typing import Dict, Iterable
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data" / "mep-contacts"
INPUT = DATA_DIR / "complete_mep_database_topics.csv"
OUTPUT = DATA_DIR / "committee-leadership-tags.csv"

USER_AGENT = "Mozilla/5.0 (compatible; EU-Citizen-Engagement-Toolkit/1.0)"

EXCLUDED_CODES = {
    "AFET-INT",
    "AIDA",
    "ANIT",
    "D-KS",
    "DMER",
}

CURRENT_ONLY_CODES = {
    "AFCO",
    "AFET",
    "AGRI",
    "BUDG",
    "CONT",
    "CULT",
    "DEVE",
    "DROI",
    "ECON",
    "EMPL",
    "ENVI",
    "EUDS",
    "FEMM",
    "FISC",
    "HOUS",
    "IMCO",
    "INTA",
    "ITRE",
    "JURI",
    "LIBE",
    "PECH",
    "PETI",
    "REGI",
    "SANT",
    "SEDE",
    "TRAN",
}

MEMBER_PATTERN = re.compile(
    r'es_title-h4 t-item">(.*?)</div>.*?<span class="sln-additional-info">(.*?)</span>',
    re.S,
)


def normalize_name(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    ascii_only = "".join(char for char in normalized if not unicodedata.combining(char))
    return re.sub(r"[^a-z0-9]+", " ", ascii_only.lower()).strip()


def read_rows(path: Path) -> list[Dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def infer_committee_codes(rows: Iterable[Dict[str, str]]) -> list[str]:
    codes = set()
    for row in rows:
        for token in (row.get("committee_memberships") or "").split(";"):
            code = token.strip().upper()
            if not code or code in EXCLUDED_CODES:
                continue
            if code in CURRENT_ONLY_CODES:
                codes.add(code)
    return sorted(codes)


def fetch_html(url: str) -> str:
    request = Request(url, headers={"User-Agent": USER_AGENT})
    with urlopen(request, timeout=30) as response:
        return response.read().decode("utf-8", errors="ignore")


def fetch_committee_leaders(code: str) -> list[tuple[str, str]]:
    url = f"https://www.europarl.europa.eu/committees/en/{code.lower()}/home/members"
    try:
        page = fetch_html(url)
    except (HTTPError, URLError, TimeoutError):
        return []

    leaders: list[tuple[str, str]] = []
    for raw_name, raw_label in MEMBER_PATTERN.findall(page):
        name = html.unescape(re.sub(r"<.*?>", "", raw_name)).strip()
        label = html.unescape(raw_label).strip()
        if label not in {"Chair", "Vice-Chair"}:
            continue
        role = "chair" if label == "Chair" else "vice_chair"
        leaders.append((name, role))
    return leaders


def name_index(rows: Iterable[Dict[str, str]]) -> Dict[str, Dict[str, str]]:
    index: Dict[str, Dict[str, str]] = {}
    for row in rows:
        name = (row.get("mep_name") or "").strip()
        if not name:
            continue
        index[normalize_name(name)] = row
    return index


def main() -> None:
    source_rows = read_rows(INPUT)
    by_name = name_index(source_rows)
    committee_codes = infer_committee_codes(source_rows)
    today = date.today().isoformat()

    output_rows: list[Dict[str, str]] = []
    unmatched: list[tuple[str, str, str]] = []

    for code in committee_codes:
        source_url = f"https://www.europarl.europa.eu/committees/en/{code.lower()}/home/members"
        leaders = fetch_committee_leaders(code)
        if not leaders:
            continue

        for leader_name, role in leaders:
            matched = by_name.get(normalize_name(leader_name))
            if not matched:
                unmatched.append((code, role, leader_name))
                continue

            output_rows.append(
                {
                    "committee_code": code,
                    "role": role,
                    "mep_name": matched.get("mep_name", leader_name),
                    "email": matched.get("email", ""),
                    "role_tag": f"{code.lower()}_{role}",
                    "source_url": source_url,
                    "last_verified": today,
                }
            )

    fieldnames = [
        "committee_code",
        "role",
        "mep_name",
        "email",
        "role_tag",
        "source_url",
        "last_verified",
    ]
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(output_rows)

    print(f"Wrote {len(output_rows)} committee leadership tags to {OUTPUT}")
    if unmatched:
        print("Unmatched names:")
        for code, role, leader_name in unmatched:
            print(f"- {code} {role}: {leader_name}")


if __name__ == "__main__":
    main()
