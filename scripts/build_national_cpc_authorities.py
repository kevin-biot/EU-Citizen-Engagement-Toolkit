#!/usr/bin/env python3
"""
Build a detailed country-by-country directory from the European Commission's CPC
competent-authorities page.

The public Commission page embeds a webtools dataset in an iframe. This builder
pulls that official dataset directly, with the required referer header.

Sources:
  - https://commission.europa.eu/live-work-travel-eu/consumer-rights-and-complaints/enforcement-consumer-protection/consumer-protection-cooperation-network/list-cpc-competent-authorities_en
  - https://ec.europa.eu/consumers/cpcn/cpc_ca.html

Outputs:
  - data/national-authorities/national-cpc-authorities.csv
  - data/national-authorities/national-cpc-authorities.md
"""

from __future__ import annotations

import csv
import html
import json
import re
import time
from collections import defaultdict
from datetime import date
from pathlib import Path
from typing import Dict, List, Tuple
from urllib.error import HTTPError
from urllib.parse import quote
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data" / "national-authorities"
CSV_PATH = DATA_DIR / "national-cpc-authorities.csv"
MD_PATH = DATA_DIR / "national-cpc-authorities.md"
SOURCE_PAGE_URL = (
    "https://commission.europa.eu/live-work-travel-eu/consumer-rights-and-complaints/"
    "enforcement-consumer-protection/consumer-protection-cooperation-network/"
    "list-cpc-competent-authorities_en"
)
IFRAME_URL = "https://ec.europa.eu/consumers/cpcn/cpc_ca.html"
DATA_URL_BASE = (
    "https://webtools.europa.eu/rest/wbase/wbql/qyUEbD345O/184/ca"
    '?env=acc&fields=["country_name","region","official_name","informal_title","contact_details","legal_responsability"]'
)
LAST_VERIFIED = date.today().isoformat()
USER_AGENT = (
    "Mozilla/5.0 (compatible; EUCitizenEngagementToolkit/1.0; "
    "+https://github.com/kevin-biot/EU-Citizen-Engagement-Toolkit)"
)

EU27: List[Tuple[str, str]] = [
    ("AT", "Austria"),
    ("BE", "Belgium"),
    ("BG", "Bulgaria"),
    ("HR", "Croatia"),
    ("CY", "Cyprus"),
    ("CZ", "Czechia"),
    ("DK", "Denmark"),
    ("EE", "Estonia"),
    ("FI", "Finland"),
    ("FR", "France"),
    ("DE", "Germany"),
    ("GR", "Greece"),
    ("HU", "Hungary"),
    ("IE", "Ireland"),
    ("IT", "Italy"),
    ("LV", "Latvia"),
    ("LT", "Lithuania"),
    ("LU", "Luxembourg"),
    ("MT", "Malta"),
    ("NL", "Netherlands"),
    ("PL", "Poland"),
    ("PT", "Portugal"),
    ("RO", "Romania"),
    ("SK", "Slovakia"),
    ("SI", "Slovenia"),
    ("ES", "Spain"),
    ("SE", "Sweden"),
]

COUNTRY_CODE_BY_NAME = {name: code for code, name in EU27}


def fetch(url: str) -> str:
    request = Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Referer": IFRAME_URL,
        },
    )
    for attempt in range(5):
        try:
            with urlopen(request, timeout=30) as response:
                body = response.read().decode("utf-8", "ignore")
            time.sleep(1.0)
            return body
        except HTTPError as exc:
            if exc.code == 429 and attempt < 4:
                time.sleep(8 * (attempt + 1))
                continue
            raise


def clean_text(value: str) -> str:
    value = html.unescape(value)
    value = value.replace("\xa0", " ")
    value = re.sub(r"\s+", " ", value)
    return value.strip()


def normalize_url(value: str) -> str:
    value = clean_text(value)
    if not value:
        return ""
    if value.startswith("//"):
        return "https:" + value
    if value.startswith("http:/") and not value.startswith("http://"):
        return value.replace("http:/", "http://", 1)
    if value.startswith("https:/") and not value.startswith("https://"):
        return value.replace("https:/", "https://", 1)
    return value


def split_contact_details(raw: str) -> Dict[str, str]:
    phone = ""
    email = ""
    website = ""
    address_parts: List[str] = []
    extras: List[str] = []

    for line in raw.splitlines():
        line = clean_text(line)
        if not line:
            continue
        lower = line.lower()
        if lower.startswith("telephone:"):
            phone = line.split(":", 1)[1].strip()
        elif lower.startswith("email:"):
            email = line.split(":", 1)[1].strip()
        elif lower.startswith("website:"):
            website = normalize_url(line.split(":", 1)[1].strip())
        elif lower.startswith("adress:") or lower.startswith("address:"):
            address_parts.append(line.split(":", 1)[1].strip())
        elif address_parts:
            address_parts.append(line)
        else:
            extras.append(line)

    return {
        "phone": phone,
        "email": email,
        "website": website,
        "address": "; ".join(part for part in address_parts if part),
        "extra_contact_details": " | ".join(extras),
    }


def build_data_url(limit: int = 500, offset: int = 0) -> str:
    orderby = quote('{"ms":"ASC"}')
    return f"{DATA_URL_BASE}&limit={limit}&offset={offset}&orderby={orderby}"


def build_rows() -> List[Dict[str, str]]:
    payload = json.loads(fetch(build_data_url()))
    rows: List[Dict[str, str]] = []
    for item in payload["data"]:
        country_name = clean_text(item.get("country_name", ""))
        if country_name not in COUNTRY_CODE_BY_NAME:
            continue
        contact_parts = split_contact_details(item.get("contact_details", ""))
        legal_responsibility = clean_text(item.get("legal_responsability", ""))
        notes = []
        if not legal_responsibility:
            notes.append("Official source row does not list a legal responsibility in this snapshot.")
        if item.get("region"):
            notes.append("Source lists this entry with regional or sectoral scope metadata.")
        rows.append(
            {
                "country_code": COUNTRY_CODE_BY_NAME[country_name],
                "country_name": country_name,
                "region": clean_text(item.get("region", "")),
                "official_name": clean_text(item.get("official_name", "")),
                "informal_title": clean_text(item.get("informal_title", "")),
                "legal_responsibility": legal_responsibility,
                "phone": contact_parts["phone"],
                "email": contact_parts["email"],
                "website": contact_parts["website"],
                "address": contact_parts["address"],
                "extra_contact_details": contact_parts["extra_contact_details"],
                "source_page_url": SOURCE_PAGE_URL,
                "source_iframe_url": IFRAME_URL,
                "last_verified": LAST_VERIFIED,
                "notes": " ".join(notes),
            }
        )

    rows.sort(key=lambda row: (row["country_name"], row["region"], row["official_name"]))
    return rows


def write_csv(rows: List[Dict[str, str]]) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with CSV_PATH.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "country_code",
                "country_name",
                "region",
                "official_name",
                "informal_title",
                "legal_responsibility",
                "phone",
                "email",
                "website",
                "address",
                "extra_contact_details",
                "source_page_url",
                "source_iframe_url",
                "last_verified",
                "notes",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)


def write_markdown(rows: List[Dict[str, str]]) -> None:
    grouped: Dict[str, List[Dict[str, str]]] = defaultdict(list)
    explicit_legal = 0
    for row in rows:
        grouped[row["country_name"]].append(row)
        if row["legal_responsibility"]:
            explicit_legal += 1

    with MD_PATH.open("w", encoding="utf-8") as f:
        f.write("# National CPC Authorities (Markdown view)\n\n")
        f.write("Source: data/national-authorities/national-cpc-authorities.csv\n\n")
        f.write(
            "This file captures the detailed consumer-protection cooperation (CPC) entries published through the official Commission page. "
            "It is intentionally more granular than the summary national routing file because the CPC layer is often split by sector, region, or legal instrument.\n\n"
        )
        f.write(
            f"Coverage in this snapshot: {len(rows)} EU Member State entries across {len(grouped)} countries. "
            f"{explicit_legal} rows publish a non-empty legal-responsibility field in the source snapshot.\n\n"
        )
        f.write(
            "Important note: the official source itself is heterogeneous. Some rows list explicit legal responsibilities and some do not. "
            "This Markdown view mirrors that source reality rather than pretending every entry is a single national general-consumer authority.\n\n"
        )

        for country_name in [name for _, name in EU27]:
            country_rows = grouped.get(country_name, [])
            f.write(f"## {country_name}\n\n")
            if not country_rows:
                f.write("No CPC entry appeared in the official source snapshot for this country.\n\n")
                continue
            f.write(
                "| region | official name | informal title | website | email | phone | legal responsibility |\n"
            )
            f.write("| --- | --- | --- | --- | --- | --- | --- |\n")
            for row in country_rows:
                website = f"[link]({row['website']})" if row["website"] else "No website published"
                email = f"[{row['email']}](mailto:{row['email']})" if row["email"] else "No email published"
                phone = row["phone"] or "No phone published"
                legal = row["legal_responsibility"] or "No legal responsibility listed in source snapshot"
                region = row["region"] or "Not specified"
                informal = row["informal_title"] or "No informal title published"
                f.write(
                    f"| {region} | {row['official_name']} | {informal} | {website} | {email} | {phone} | {legal} |\n"
                )
            f.write("\n")

        f.write("Sources:\n\n")
        f.write(f"- Commission wrapper page: <{SOURCE_PAGE_URL}>\n")
        f.write(f"- Embedded CPC table page: <{IFRAME_URL}>\n")


def main() -> None:
    rows = build_rows()
    write_csv(rows)
    write_markdown(rows)
    print(f"Wrote {len(rows)} rows to {CSV_PATH.relative_to(ROOT)}")
    print(f"Wrote Markdown view to {MD_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
