#!/usr/bin/env python3
"""
Build a country-by-country reference of national equality bodies from the
European Commission's official equality-bodies page.

Source:
  - https://commission.europa.eu/strategy-and-policy/policies/justice-and-fundamental-rights/gender-equality/who-we-work-gender-equality/national-gender-equality-bodies_en

Outputs:
  - data/national-authorities/national-equality-bodies.csv
  - data/national-authorities/national-equality-bodies.md
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
CSV_PATH = DATA_DIR / "national-equality-bodies.csv"
MD_PATH = DATA_DIR / "national-equality-bodies.md"
SOURCE_URL = (
    "https://commission.europa.eu/strategy-and-policy/policies/justice-and-fundamental-rights/"
    "gender-equality/who-we-work-gender-equality/national-gender-equality-bodies_en"
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

COUNTRY_ALIASES = {
    "Czech Republic": "Czechia",
    "The Netherlands": "Netherlands",
}
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


def normalize_country_name(value: str) -> str:
    value = clean_text(value)
    return COUNTRY_ALIASES.get(value, value)


def normalize_url(url: str) -> str:
    url = html.unescape(url).strip()
    if url.startswith("//"):
        return "https:" + url
    if url.startswith("http:/") and not url.startswith("http://"):
        return url.replace("http:/", "http://", 1)
    if url.startswith("https:/") and not url.startswith("https://"):
        return url.replace("https:/", "https://", 1)
    return url


def parse_country_blocks(page_html: str) -> Dict[str, str]:
    blocks: Dict[str, str] = {}
    start_match = re.search(r"<h2>National equality bodies</h2>(.*)", page_html, re.S)
    if not start_match:
        return blocks
    section_html = start_match.group(1)
    matches = list(re.finditer(r"<h3>(.*?)</h3>", section_html, re.S))
    for index, match in enumerate(matches):
        country_name = normalize_country_name(match.group(1))
        if country_name not in COUNTRY_CODE_BY_NAME:
            continue
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else section_html.find("</div>", start)
        if end == -1:
            end = len(section_html)
        blocks[country_name] = section_html[start:end]
    return blocks


def parse_body_entries(country_name: str, country_html: str) -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    paragraphs = re.findall(r"<p>(.*?)</p>", country_html, re.S)
    display_order = 0

    for paragraph in paragraphs:
        links = re.findall(r'<a href="([^"]+)"[^>]*>.*?<span class="ecl-link__label">(.*?)</span>', paragraph, re.S)
        if not links:
            continue
        display_order += 1
        labels = [clean_text(label) for _, label in links if clean_text(label)]
        urls = [normalize_url(url) for url, _ in links if normalize_url(url)]
        description_match = re.search(r"\)\s*$", clean_text(paragraph))
        description = ""
        if description_match:
            cleaned = clean_text(paragraph)
            open_index = cleaned.rfind("(")
            if open_index != -1 and cleaned.endswith(")"):
                description = cleaned[open_index + 1 : -1].strip()

        rows.append(
            {
                "country_code": COUNTRY_CODE_BY_NAME[country_name],
                "country_name": country_name,
                "display_order": str(display_order),
                "body_name": " / ".join(labels),
                "body_description": description,
                "website_urls": " ; ".join(urls),
                "source_url": SOURCE_URL,
                "last_verified": LAST_VERIFIED,
                "notes": "Commission equality-bodies page entry.",
            }
        )

    return rows


def build_rows() -> List[Dict[str, str]]:
    page_html = fetch(SOURCE_URL)
    country_blocks = parse_country_blocks(page_html)
    rows: List[Dict[str, str]] = []
    for _, country_name in EU27:
        rows.extend(parse_body_entries(country_name, country_blocks.get(country_name, "")))
    return rows


def write_csv(rows: List[Dict[str, str]]) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with CSV_PATH.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "country_code",
                "country_name",
                "display_order",
                "body_name",
                "body_description",
                "website_urls",
                "source_url",
                "last_verified",
                "notes",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)


def format_urls(urls: str) -> str:
    parts = [part.strip() for part in urls.split(" ; ") if part.strip()]
    if not parts:
        return "No website published"
    return " ; ".join(f"[link]({part})" for part in parts)


def write_markdown(rows: List[Dict[str, str]]) -> None:
    grouped: Dict[str, List[Dict[str, str]]] = defaultdict(list)
    for row in rows:
        grouped[row["country_name"]].append(row)

    with MD_PATH.open("w", encoding="utf-8") as f:
        f.write("# National Equality Bodies (Markdown view)\n\n")
        f.write("Source: data/national-authorities/national-equality-bodies.csv\n\n")
        f.write(
            "This file captures the national equality-body entries listed on the European Commission's official page. "
            "It is a routing aid for discrimination and equal-treatment complaints, not a claim that every body has the same mandate or powers.\n\n"
        )
        f.write(
            f"Coverage in this snapshot: {len(rows)} listed body entries across {len(grouped)} Member States.\n\n"
        )
        f.write(
            "Important note: the source page is framed through the Commission's gender-equality section, but it points to national equality bodies more broadly. "
            "Some countries have one listed body and some have more than one.\n\n"
        )

        for _, country_name in EU27:
            f.write(f"## {country_name}\n\n")
            country_rows = grouped.get(country_name, [])
            if not country_rows:
                f.write("No equality-body entry parsed for this country in this snapshot.\n\n")
                continue
            f.write("| order | body | description | websites |\n")
            f.write("| --- | --- | --- | --- |\n")
            for row in country_rows:
                description = row["body_description"] or "No description published"
                f.write(
                    f"| {row['display_order']} | {row['body_name']} | {description} | {format_urls(row['website_urls'])} |\n"
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
