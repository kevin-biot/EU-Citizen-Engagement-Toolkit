#!/usr/bin/env python3
"""
Build a best-effort reference of public press/comms surfaces for European
Commission departments and executive agencies.

Sources:
  - https://commission.europa.eu/about/departments-and-executive-agencies_en
  - individual department / service / executive agency pages linked there

Outputs:
  - data/commission-reference/commission-dg-press-surfaces.csv
  - data/commission-reference/commission-dg-press-surfaces.md
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
from urllib.parse import urljoin
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data" / "commission-reference"
CSV_PATH = DATA_DIR / "commission-dg-press-surfaces.csv"
MD_PATH = DATA_DIR / "commission-dg-press-surfaces.md"
LIST_BASE = "https://commission.europa.eu/about/departments-and-executive-agencies_en"
BASE_URL = "https://commission.europa.eu"
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


def normalize_unit_code(code: str) -> str:
    replacements = {
        "Connect": "CNECT",
    }
    return replacements.get(code, code)


def list_page_urls() -> List[str]:
    return [LIST_BASE, f"{LIST_BASE}?page=1", f"{LIST_BASE}?page=2"]


def parse_directory_entries(page_html: str) -> List[Dict[str, str]]:
    entries: List[Dict[str, str]] = []
    title_pattern = re.compile(
        r'<div class="ecl-content-block__title"><a\s+href="([^"]+)"[^>]*>(.*?)</a></div>',
        re.S,
    )
    meta_pattern = re.compile(r'<li class="ecl-content-block__primary-meta-item">(.*?)</li>', re.S)

    for match in title_pattern.finditer(page_html):
        context_start = max(0, match.start() - 1200)
        context = page_html[context_start : match.start()]
        meta_items = meta_pattern.findall(context)
        if len(meta_items) < 2:
            continue
        entries.append(
            {
                "unit_type": clean_text(meta_items[-2]),
                "unit_code": normalize_unit_code(clean_text(meta_items[-1])),
                "unit_name": clean_text(match.group(2)),
                "department_page_url": urljoin(BASE_URL, html.unescape(match.group(1))),
            }
        )
    return entries


def collect_directory_entries() -> List[Dict[str, str]]:
    entries: List[Dict[str, str]] = []
    seen = set()
    for url in list_page_urls():
        html_text = fetch(url)
        for entry in parse_directory_entries(html_text):
            if entry["department_page_url"] in seen:
                continue
            seen.add(entry["department_page_url"])
            entries.append(entry)
    return entries


def extract_press_contacts_url(page_html: str) -> str:
    match = re.search(r'<a\s+href="([^"]+)"[^>]*>\s*<span\s+class="ecl-link__label">Press contacts</span>', page_html)
    return urljoin(BASE_URL, html.unescape(match.group(1))) if match else ""


def extract_question_url(page_html: str) -> str:
    patterns = [
        r'<a\s+href="([^"]+)"[^>]*>\s*<span\s+class="ecl-link__label">Ask a question</span>',
        r'<a\s+href="([^"]+)"[^>]*>\s*<span\s+class="ecl-link__label">Send a message to this department</span>',
        r'<a\s+href="([^"]+)"[^>]*>\s*<span\s+class="ecl-link__label">Write to us</span>',
    ]
    for pattern in patterns:
        match = re.search(pattern, page_html)
        if match:
            return urljoin(BASE_URL, html.unescape(match.group(1)))
    return ""


def extract_phone(page_html: str) -> str:
    patterns = [
        r"Phone number:\s*([^<\n]+)",
        r'<dt class="ecl-description-list__term">Phone number</dt><dd class="ecl-description-list__definition"><div><div>(.*?)</div></div></dd>',
        r'<dt class="ecl-description-list__term">Phone number</dt><dd class="ecl-description-list__definition"><div>(.*?)</div></dd>',
    ]
    for pattern in patterns:
        match = re.search(pattern, page_html, re.S)
        if match:
            return clean_text(match.group(1))
    return ""


def classify_surface(press_contacts_url: str, question_url: str) -> str:
    if press_contacts_url:
        return "dg_press_contacts_link"
    if question_url:
        return "public_question_route_only"
    return "no_public_press_surface_found"


def note_for_entry(unit_type: str, press_contacts_url: str, question_url: str) -> str:
    notes: List[str] = []
    if unit_type.lower() == "executive agency":
        notes.append("Executive agency rather than DG.")
    elif unit_type.lower() != "directorate-general":
        notes.append(f"{unit_type} rather than DG.")
    if press_contacts_url and "field_job_tags_tid=" in press_contacts_url:
        notes.append("Press contacts link appears to target a filtered Brussels press-contacts listing.")
    elif press_contacts_url:
        notes.append("Press contacts link is public but not visibly filtered on-page.")
    else:
        notes.append("No public press-contacts link found on the department page.")
    if question_url:
        notes.append("Public question or write-to-us route also published.")
    return " ".join(notes)


def extract_contact_section(page_html: str) -> str:
    start_match = re.search(r'<h2 id="contact"[^>]*>.*?</h2>', page_html, re.S)
    if not start_match:
        return page_html
    start = start_match.start()
    end_candidates = []
    for pattern in [r'<h2 id="plans-and-reports"', r'<h2 id="[^"]+"', r'class="ecl-u-type-heading-2 ecl-u-mt-none ecl-u-mb-l">Plans and reports']:
        match = re.search(pattern, page_html[start + 1 :], re.S)
        if match:
            end_candidates.append(start + 1 + match.start())
    end = min(end_candidates) if end_candidates else len(page_html)
    return page_html[start:end]


def build_rows() -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    for entry in collect_directory_entries():
        if not entry["department_page_url"].startswith(BASE_URL):
            rows.append(
                {
                    "unit_code": entry["unit_code"],
                    "unit_name": entry["unit_name"],
                    "unit_type": entry["unit_type"],
                    "department_page_url": entry["department_page_url"],
                    "public_surface_type": "external_directory_entry",
                    "press_contacts_url": "",
                    "public_question_url": "",
                    "public_phone": "",
                    "last_verified": LAST_VERIFIED,
                    "notes": f"{entry['unit_type']} entry in the official directory, but it points to an external site so no department-page press parsing was attempted.",
                }
            )
            continue

        page_html = fetch(entry["department_page_url"])
        contact_html = extract_contact_section(page_html)
        press_contacts_url = extract_press_contacts_url(contact_html)
        question_url = extract_question_url(contact_html)
        phone = extract_phone(contact_html)
        rows.append(
            {
                "unit_code": entry["unit_code"],
                "unit_name": entry["unit_name"],
                "unit_type": entry["unit_type"],
                "department_page_url": entry["department_page_url"],
                "public_surface_type": classify_surface(press_contacts_url, question_url),
                "press_contacts_url": press_contacts_url,
                "public_question_url": question_url,
                "public_phone": phone,
                "last_verified": LAST_VERIFIED,
                "notes": note_for_entry(entry["unit_type"], press_contacts_url, question_url),
            }
        )
    return rows


def write_csv(rows: List[Dict[str, str]]) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with CSV_PATH.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "unit_code",
                "unit_name",
                "unit_type",
                "department_page_url",
                "public_surface_type",
                "press_contacts_url",
                "public_question_url",
                "public_phone",
                "last_verified",
                "notes",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)


def write_markdown(rows: List[Dict[str, str]]) -> None:
    with MD_PATH.open("w", encoding="utf-8") as f:
        f.write("# Commission Department Press Surfaces (Markdown view)\n\n")
        f.write("Source: data/commission-reference/commission-dg-press-surfaces.csv\n\n")
        f.write(
            "This file is a best-effort map of the public press/comms surface published on official department and executive-agency pages. It does not claim that every listed body has a standalone communications unit page; it records what public press-facing route is actually exposed.\n\n"
        )
        f.write("| unit_code | unit_name | unit_type | public_surface_type | press_contacts | public_question | phone |\n")
        f.write("| --- | --- | --- | --- | --- | --- | --- |\n")
        for row in rows:
            press_contacts = f"[press contacts]({row['press_contacts_url']})" if row["press_contacts_url"] else ""
            question = f"[public route]({row['public_question_url']})" if row["public_question_url"] else ""
            f.write(
                f"| {row['unit_code']} | {row['unit_name']} | {row['unit_type']} | {row['public_surface_type']} | {press_contacts} | {question} | {row['public_phone']} |\n"
            )
        f.write("\nNotes:\n\n")
        f.write("- `dg_press_contacts_link` means the department page itself exposes a public `Press contacts` link.\n")
        f.write("- Many of those links point to the central Commission press-contact system with department-specific filtering, rather than to a standalone DG communications site.\n")
        f.write("- `public_question_route_only` means a public contact route is exposed, but no dedicated press-contacts link was found on the department page.\n")
        f.write("- `external_directory_entry` means the official directory points outside the main Commission department-page system, so no like-for-like press parsing was attempted.\n")
        f.write("- Executive agencies and service departments are included because they appear in the official departments-and-executive-agencies directory.\n")


def main() -> None:
    rows = build_rows()
    write_csv(rows)
    write_markdown(rows)
    print(f"Wrote {len(rows)} rows to {CSV_PATH.relative_to(ROOT)}")
    print(f"Wrote Markdown view to {MD_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
