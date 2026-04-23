#!/usr/bin/env python3
"""
Build a country-by-country reference of public web-accessibility monitoring,
reporting, and enforcement bodies from the official Commission page.

Source:
  - https://digital-strategy.ec.europa.eu/en/policies/web-accessibility-monitoring

Outputs:
  - data/national-authorities/national-web-accessibility-bodies.csv
  - data/national-authorities/national-web-accessibility-bodies.md
"""

from __future__ import annotations

import csv
import html
import re
import time
from collections import defaultdict
from datetime import date
from pathlib import Path
from typing import Dict, List, Tuple
from urllib.error import HTTPError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data" / "national-authorities"
CSV_PATH = DATA_DIR / "national-web-accessibility-bodies.csv"
MD_PATH = DATA_DIR / "national-web-accessibility-bodies.md"
SOURCE_URL = "https://digital-strategy.ec.europa.eu/en/policies/web-accessibility-monitoring"
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


def normalize_url(url: str) -> str:
    url = html.unescape(url).strip()
    if not url:
        return ""
    if url.startswith("//"):
        return "https:" + url
    if url.startswith("http:/") and not url.startswith("http://"):
        url = url.replace("http:/", "http://", 1)
    if url.startswith("https:/") and not url.startswith("https://"):
        url = url.replace("https:/", "https://", 1)
    if "urldefense.com" in url:
        match = re.search(r"__(https?[:/].*?)__", url)
        if match:
            url = match.group(1)
            if url.startswith("http:/") and not url.startswith("http://"):
                url = url.replace("http:/", "http://", 1)
            if url.startswith("https:/") and not url.startswith("https://"):
                url = url.replace("https:/", "https://", 1)
    return url


def split_country_blocks(page_html: str) -> Dict[str, str]:
    blocks: Dict[str, str] = {}
    matches = list(re.finditer(r'<h2 id="[^"]+">(.*?)</h2>', page_html, re.S))
    for index, match in enumerate(matches):
        country_name = clean_text(match.group(1))
        if country_name not in COUNTRY_CODE_BY_NAME:
            continue
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(page_html)
        blocks[country_name] = page_html[start:end]
    return blocks


def split_section_blocks(country_html: str) -> List[Tuple[str, str]]:
    sections: List[Tuple[str, str]] = []
    matches = list(re.finditer(r'<h3(?: id="[^"]+")?>(.*?)</h3>', country_html, re.S))
    if not matches:
        return [("National", country_html)]

    prefix = country_html[: matches[0].start()]
    if re.search(r"(Monitoring|Reporting|Enforcement|Responsible body)", prefix, re.I):
        sections.append(("National", prefix))

    for index, match in enumerate(matches):
        section_name = clean_text(match.group(1))
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(country_html)
        sections.append((section_name, country_html[start:end]))
    return sections


def extract_role_prefix(text: str) -> Tuple[List[str], str]:
    normalized = text.strip()
    checks = [
        ("Responsible body for monitoring, enforcement and reporting is", ["monitoring", "reporting", "enforcement"]),
        ("Monitoring, reporting and enforcement:", ["monitoring", "reporting", "enforcement"]),
        ("Monitoring and reporting:", ["monitoring", "reporting"]),
        ("Reporting and enforcement:", ["reporting", "enforcement"]),
        ("Monitoring and enforcement:", ["monitoring", "enforcement"]),
        ("Monitoring:", ["monitoring"]),
        ("Reporting:", ["reporting"]),
        ("Enforcement:", ["enforcement"]),
    ]
    for prefix, roles in checks:
        if normalized.lower().startswith(prefix.lower()):
            return roles, normalized[len(prefix) :].strip(" .:-")
    return [], normalized


def collect_role_items(section_html: str) -> Dict[str, Dict[str, List[str]]]:
    role_data: Dict[str, Dict[str, List[str]]] = {
        "monitoring": {"summaries": [], "urls": []},
        "reporting": {"summaries": [], "urls": []},
        "enforcement": {"summaries": [], "urls": []},
    }

    snippets = re.findall(r"<li>(.*?)</li>", section_html, re.S)
    snippets.extend(
        snippet
        for snippet in re.findall(r"<p>(.*?)</p>", section_html, re.S)
        if re.search(r"(Monitoring|Reporting|Enforcement|Responsible body)", clean_text(snippet), re.I)
    )

    for snippet in snippets:
        text = clean_text(snippet)
        roles, summary = extract_role_prefix(text)
        if not roles:
            continue
        urls = [normalize_url(url) for url in re.findall(r'href="([^"]+)"', snippet)]
        urls = [url for url in urls if url]
        for role in roles:
            if summary and summary not in role_data[role]["summaries"]:
                role_data[role]["summaries"].append(summary)
            for url in urls:
                if url not in role_data[role]["urls"]:
                    role_data[role]["urls"].append(url)

    return role_data


def build_rows() -> List[Dict[str, str]]:
    page_html = fetch(SOURCE_URL)
    country_blocks = split_country_blocks(page_html)
    rows: List[Dict[str, str]] = []

    for country_name in [name for _, name in EU27]:
        country_html = country_blocks.get(country_name, "")
        if not country_html:
            rows.append(
                {
                    "country_code": COUNTRY_CODE_BY_NAME[country_name],
                    "country_name": country_name,
                    "section_name": "National",
                    "monitoring_summary": "",
                    "monitoring_urls": "",
                    "reporting_summary": "",
                    "reporting_urls": "",
                    "enforcement_summary": "",
                    "enforcement_urls": "",
                    "last_verified": LAST_VERIFIED,
                    "notes": "No section found on the official source page in this snapshot.",
                }
            )
            continue

        for section_name, section_html in split_section_blocks(country_html):
            role_items = collect_role_items(section_html)
            notes: List[str] = []
            if section_name != "National":
                notes.append("Subsection on the official Commission page, not a single country-wide row.")
            rows.append(
                {
                    "country_code": COUNTRY_CODE_BY_NAME[country_name],
                    "country_name": country_name,
                    "section_name": section_name,
                    "monitoring_summary": " | ".join(role_items["monitoring"]["summaries"]),
                    "monitoring_urls": " ; ".join(role_items["monitoring"]["urls"]),
                    "reporting_summary": " | ".join(role_items["reporting"]["summaries"]),
                    "reporting_urls": " ; ".join(role_items["reporting"]["urls"]),
                    "enforcement_summary": " | ".join(role_items["enforcement"]["summaries"]),
                    "enforcement_urls": " ; ".join(role_items["enforcement"]["urls"]),
                    "last_verified": LAST_VERIFIED,
                    "notes": " ".join(notes),
                }
            )

    return rows


def write_csv(rows: List[Dict[str, str]]) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with CSV_PATH.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "country_code",
                "country_name",
                "section_name",
                "monitoring_summary",
                "monitoring_urls",
                "reporting_summary",
                "reporting_urls",
                "enforcement_summary",
                "enforcement_urls",
                "last_verified",
                "notes",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)


def format_links(urls: str) -> str:
    if not urls:
        return "No link published"
    parts = [part.strip() for part in urls.split(" ; ") if part.strip()]
    return " ; ".join(f"[link]({part})" for part in parts)


def write_markdown(rows: List[Dict[str, str]]) -> None:
    grouped: Dict[str, List[Dict[str, str]]] = defaultdict(list)
    for row in rows:
        grouped[row["country_name"]].append(row)

    with MD_PATH.open("w", encoding="utf-8") as f:
        f.write("# National Web Accessibility Bodies (Markdown view)\n\n")
        f.write("Source: data/national-authorities/national-web-accessibility-bodies.csv\n\n")
        f.write(
            "This file maps the official bodies that EU countries notified to the Commission for web-accessibility monitoring, reporting, and enforcement. "
            "It mirrors the structure of the Commission page, which means some countries have a single national row while federal or devolved systems have multiple subsections.\n\n"
        )
        f.write(
            f"Coverage in this snapshot: {len(rows)} rows across {len(grouped)} Member States.\n\n"
        )

        for country_name in [name for _, name in EU27]:
            f.write(f"## {country_name}\n\n")
            country_rows = grouped.get(country_name, [])
            if not country_rows:
                f.write("No official body row parsed for this country in this snapshot.\n\n")
                continue
            f.write("| section | monitoring | reporting | enforcement | notes |\n")
            f.write("| --- | --- | --- | --- | --- |\n")
            for row in country_rows:
                monitoring = row["monitoring_summary"] or "No monitoring body parsed"
                if row["monitoring_urls"]:
                    monitoring += f" ({format_links(row['monitoring_urls'])})"
                reporting = row["reporting_summary"] or "No reporting body parsed"
                if row["reporting_urls"]:
                    reporting += f" ({format_links(row['reporting_urls'])})"
                enforcement = row["enforcement_summary"] or "No enforcement body parsed"
                if row["enforcement_urls"]:
                    enforcement += f" ({format_links(row['enforcement_urls'])})"
                f.write(
                    f"| {row['section_name']} | {monitoring} | {reporting} | {enforcement} | {row['notes'] or ' '} |\n"
                )
            f.write("\n")

        f.write("Source:\n\n")
        f.write(f"- Official Commission page: <{SOURCE_URL}>\n")


def main() -> None:
    rows = build_rows()
    write_csv(rows)
    write_markdown(rows)
    print(f"Wrote {len(rows)} rows to {CSV_PATH.relative_to(ROOT)}")
    print(f"Wrote Markdown view to {MD_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
