#!/usr/bin/env python3
"""
Build a structured reference of the European Commission Spokespersons' Service
contacts from the official SPP roster page.

Source:
  - https://commission.europa.eu/about/contact/press-services/press-contacts/commissions-spokespersons-service_en

Outputs:
  - data/commission-reference/commission-spp-contacts.csv
  - data/commission-reference/commission-spp-contacts.md
"""

from __future__ import annotations

import csv
import html
import re
import time
from datetime import date
from pathlib import Path
from typing import Dict, List
from urllib.error import HTTPError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data" / "commission-reference"
CSV_PATH = DATA_DIR / "commission-spp-contacts.csv"
MD_PATH = DATA_DIR / "commission-spp-contacts.md"
SOURCE_URL = "https://commission.europa.eu/about/contact/press-services/press-contacts/commissions-spokespersons-service_en"
LAST_VERIFIED = date.today().isoformat()
USER_AGENT = "Mozilla/5.0 (compatible; EUCitizenEngagementToolkit/1.0; +https://github.com/kevin-biot/EU-Citizen-Engagement-Toolkit)"


def fetch(url: str) -> str:
    request = Request(url, headers={"User-Agent": USER_AGENT})
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
    value = re.sub(r"<br\s*/?>", "\n", value, flags=re.IGNORECASE)
    value = re.sub(r"<[^>]+>", "", value)
    value = html.unescape(value)
    value = value.replace("\xa0", " ")
    value = re.sub(r"\s+", " ", value)
    return value.strip()


def normalize_email(value: str) -> str:
    value = html.unescape(value)
    value = re.sub(r"\s+", "", value)
    value = re.sub(r"(?i)\[(?:at)\]|\((?:at)\)|\{(?:at)\}", "@", value)
    value = re.sub(r"(?i)\[(?:dot)\]|\((?:dot)\)|\{(?:dot)\}", ".", value)
    value = value.strip(".,;:()[]<>")
    return value.lower()


def extract_email(block: str) -> str:
    parenthetical = re.search(r'class="t">\s*\(([^)]+)\)', block, re.I)
    if parenthetical:
        return normalize_email(parenthetical.group(1))

    mailto = re.search(r"mailto:([^\"'?&#]+)", block, re.I)
    if mailto:
        return normalize_email(mailto.group(1))

    return ""


def extract_phone(block: str, label: str) -> str:
    tel_match = re.search(rf"{re.escape(label)}.*?href=\"tel:[^\"]+\">(.*?)</a>", block, re.I | re.S)
    if tel_match:
        return clean_text(tel_match.group(1))

    text_match = re.search(rf"{re.escape(label)}.*?(\+\d[\d\s]{6,})", block, re.I | re.S)
    if text_match:
        return clean_text(text_match.group(1))

    return ""


def extract_responsibilities(block: str) -> str:
    match = re.search(r"<strong>Responsibilities:</strong>\s*</p>\s*<ul>(.*?)</ul>", block, re.I | re.S)
    if not match:
        return ""
    items = re.findall(r"<li>(.*?)</li>", match.group(1), re.I | re.S)
    cleaned = [clean_text(item) for item in items if clean_text(item)]
    return "; ".join(cleaned)


def parse_section_markers(page_html: str) -> List[Dict[str, int | str]]:
    markers: List[Dict[str, int | str]] = []
    pattern = re.compile(r'<a id="paragraph_\d+"></a>\s*<div>\s*<div class="ecl"><h2>(.*?)</h2></div>', re.S)
    for match in pattern.finditer(page_html):
        markers.append({"section_name": clean_text(match.group(1)), "start": match.start()})
    return markers


def section_for_offset(markers: List[Dict[str, int | str]], offset: int) -> str:
    current = ""
    for marker in markers:
        if int(marker["start"]) > offset:
            break
        current = str(marker["section_name"])
    return current


def parse_contacts(page_html: str) -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    section_markers = parse_section_markers(page_html)
    section_order: Dict[str, int] = {}
    person_pattern = re.compile(
        r"<h2 class='ecl-u-type-heading-2'>(.*?)</h2>\s*</div>\s*<article\s+class=\"ecl-featured-item\"(.*?)</article>",
        re.S,
    )

    for match in person_pattern.finditer(page_html):
        section_name = section_for_offset(section_markers, match.start())
        section_order[section_name] = section_order.get(section_name, 0) + 1
        name = clean_text(match.group(1))
        article_html = match.group(2)
        role_match = re.search(r'ecl-featured-item__title"[^>]*>(.*?)</div>', article_html, re.S)
        rows.append(
            {
                "section_name": section_name,
                "display_order": str(section_order[section_name]),
                "name": name,
                "role": clean_text(role_match.group(1)) if role_match else "",
                "email": extract_email(article_html),
                "phone": extract_phone(article_html, "Phone number"),
                "mobile": extract_phone(article_html, "Mobile number"),
                "responsibilities": extract_responsibilities(article_html),
                "source_url": SOURCE_URL,
                "last_verified": LAST_VERIFIED,
            }
        )
    return rows


def build_rows() -> List[Dict[str, str]]:
    html_text = fetch(SOURCE_URL)
    return parse_contacts(html_text)


def write_csv(rows: List[Dict[str, str]]) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with CSV_PATH.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "section_name",
                "display_order",
                "name",
                "role",
                "email",
                "phone",
                "mobile",
                "responsibilities",
                "source_url",
                "last_verified",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)


def write_markdown(rows: List[Dict[str, str]]) -> None:
    section_counts: Dict[str, int] = {}
    for row in rows:
        section_counts[row["section_name"]] = section_counts.get(row["section_name"], 0) + 1

    with MD_PATH.open("w", encoding="utf-8") as f:
        f.write("# Commission Spokespersons' Service Contacts (Markdown view)\n\n")
        f.write("Source: data/commission-reference/commission-spp-contacts.csv\n\n")
        f.write(
            "This file captures the official Commission Spokespersons' Service roster page as a structured reference. It preserves the named public contacts, their published role, email, phone, mobile number, and responsibility scope where listed.\n\n"
        )
        summary = ", ".join(f"{section}: {count}" for section, count in section_counts.items())
        f.write(f"Coverage in this snapshot: {len(rows)} published contacts across {len(section_counts)} sections ({summary}).\n\n")
        f.write("| section | name | role | email | phone | mobile | responsibilities |\n")
        f.write("| --- | --- | --- | --- | --- | --- | --- |\n")
        for row in rows:
            email = f"[{row['email']}](mailto:{row['email']})" if row["email"] else "No public email published"
            phone = row["phone"] or "No public phone published"
            mobile = row["mobile"] or "No public mobile published"
            responsibilities = row["responsibilities"] or "No responsibilities listed"
            f.write(
                f"| {row['section_name']} | {row['name']} | {row['role']} | {email} | {phone} | {mobile} | {responsibilities} |\n"
            )

        f.write("\nNotes:\n\n")
        f.write("- This dataset is a structured copy of the official public Spokespersons' Service roster, not a separate inference layer.\n")
        f.write("- Responsibility scopes are copied from the page and can cut across multiple DGs or portfolios.\n")
        f.write("- Some entries publish phone but not mobile, or publish no responsibilities list.\n")
        f.write(f"- Official source page: <{SOURCE_URL}>\n")


def main() -> None:
    rows = build_rows()
    write_csv(rows)
    write_markdown(rows)
    print(f"Wrote {len(rows)} rows to {CSV_PATH.relative_to(ROOT)}")
    print(f"Wrote Markdown view to {MD_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
