#!/usr/bin/env python3
"""
Build a first-pass national digital authorities directory for EU Member States.

This builder prioritizes central official or EU-level directory pages so the
dataset stays reproducible without a fragile 27-country scrape.

Sources:
  - https://digital-strategy.ec.europa.eu/en/policies/dsa-dscs
  - https://www.edpb.europa.eu/about-edpb/about-edpb/members_en
  - https://www.berec.europa.eu/en/berec-members
  - https://competition-policy.ec.europa.eu/antitrust-and-cartels/european-competition-network/national-competition-authorities_en
  - https://commission.europa.eu/strategy-and-policy/policies/justice-and-fundamental-rights/gender-equality/who-we-work-gender-equality/national-gender-equality-bodies_en

Outputs:
  - data/national-authorities/national-digital-authorities.csv
  - data/national-authorities/national-digital-authorities.md
"""

from __future__ import annotations

import csv
import html
import re
import time
from datetime import date
from pathlib import Path
from typing import Dict, List, Tuple
from urllib.error import HTTPError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data" / "national-authorities"
CSV_PATH = DATA_DIR / "national-digital-authorities.csv"
MD_PATH = DATA_DIR / "national-digital-authorities.md"

DSC_URL = "https://digital-strategy.ec.europa.eu/en/policies/dsa-dscs"
DPA_URL = "https://www.edpb.europa.eu/about-edpb/about-edpb/members_en"
BEREC_URL = "https://www.berec.europa.eu/en/berec-members"
COMPETITION_URL = (
    "https://competition-policy.ec.europa.eu/antitrust-and-cartels/"
    "european-competition-network/national-competition-authorities_en"
)
EQUALITY_URL = (
    "https://commission.europa.eu/strategy-and-policy/policies/justice-and-fundamental-rights/"
    "gender-equality/who-we-work-gender-equality/national-gender-equality-bodies_en"
)

LAST_VERIFIED = date.today().isoformat()
USER_AGENT = (
    "Mozilla/5.0 (compatible; EUCitizenEngagementToolkit/1.0; "
    "+https://github.com/kevin-biot/EU-Citizen-Engagement-Toolkit)"
)
FETCH_CACHE: Dict[str, str] = {}

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


def fetch(url: str) -> str:
    if url in FETCH_CACHE:
        return FETCH_CACHE[url]

    request = Request(url, headers={"User-Agent": USER_AGENT})
    for attempt in range(5):
        try:
            with urlopen(request, timeout=30) as response:
                body = response.read().decode("utf-8", "ignore")
            time.sleep(1.0)
            FETCH_CACHE[url] = body
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


def canonical_country_name(value: str) -> str:
    value = clean_text(value)
    return COUNTRY_ALIASES.get(value, value)


def parse_dscs(page_html: str) -> Dict[str, Dict[str, str]]:
    body_match = re.search(r"<tbody[^>]*>(.*?)</tbody>", page_html, re.S)
    if not body_match:
        return {}

    rows: Dict[str, Dict[str, str]] = {}
    for block in re.findall(r"<td>(.*?)</td>", body_match.group(1), re.S):
        if "Flag of" not in block:
            continue
        country_match = re.search(r'alt="Flag of (?:the )?[^"]+"[^>]*>\s*([^<]+)</p>', block)
        if not country_match:
            continue
        country_name = canonical_country_name(country_match.group(1))
        hrefs = re.findall(r'<a href="([^"]+)">(.*?)</a>', block, re.S)
        if not hrefs:
            continue
        english_name = ""
        paragraphs = re.findall(r"<p>(.*?)</p>", block, re.S)
        if len(paragraphs) >= 2:
            second = clean_text(paragraphs[1])
            parts = [part.strip() for part in second.split("|") if part.strip()]
            english_name = parts[-1] if parts else ""
        rows[country_name] = {
            "name": english_name or clean_text(hrefs[0][1]),
            "url": html.unescape(hrefs[0][0]),
        }
    return rows


def parse_dpas(page_html: str) -> Dict[str, Dict[str, str]]:
    pattern = re.compile(
        r'<a name="member-([^"]+)"></a>\s*'
        r'<h3[^>]*>\s*<div[^>]*>(.*?)</div>\s*</h3>\s*'
        r'<div class="content mb-4">\s*'
        r'<h4[^>]*>(.*?)</h4>.*?'
        r'<span class="field__label">Website:</span>\s*'
        r"<span class='field__items'>\s*"
        r'<span class="field__item"><a href="([^"]+)"',
        re.S,
    )
    rows: Dict[str, Dict[str, str]] = {}
    allowed_codes = {code.lower() for code, _ in EU27}
    for match in pattern.finditer(page_html):
        code = match.group(1).lower()
        if code not in allowed_codes:
            continue
        country_name = canonical_country_name(match.group(2))
        rows[country_name] = {
            "name": clean_text(match.group(3)),
            "url": html.unescape(match.group(4)),
        }
    return rows


def parse_berec_members(page_html: str) -> Dict[str, Dict[str, str]]:
    pattern = re.compile(
        r'<div class="member-box">\s*'
        r'<a href="([^"]+)"[^>]*>\s*'
        r'<div class="content">\s*'
        r'<div class="title">(.*?)</div>\s*'
        r'<div class="description">(.*?)</div>\s*'
        r'<div class="acronym-wrapper">\s*'
        r'<div class="acronym">(.*?)</div>',
        re.S,
    )
    eu_names = {name for _, name in EU27}
    rows: Dict[str, Dict[str, str]] = {}
    for match in pattern.finditer(page_html):
        country_name = canonical_country_name(match.group(2))
        if country_name not in eu_names:
            continue
        acronym = clean_text(match.group(4))
        description = clean_text(match.group(3))
        rows[country_name] = {
            "name": f"{description} ({acronym})" if acronym and acronym not in description else description,
            "url": html.unescape(match.group(1)),
        }
    return rows


def parse_competition_authorities(page_html: str) -> Dict[str, Dict[str, str]]:
    pattern = re.compile(
        r'<div class="ecl-content-block__title"><a\s+href="([^"]+)"[^>]*>\s*'
        r'<span[^>]*>(.*?)</span>.*?</a></div>'
        r'<div class="ecl-content-block__description"><p>(.*?)</p>',
        re.S,
    )
    rows: Dict[str, Dict[str, str]] = {}
    for match in pattern.finditer(page_html):
        country_name = canonical_country_name(match.group(2))
        rows[country_name] = {
            "name": clean_text(match.group(3)),
            "url": html.unescape(match.group(1)),
        }
    return rows


def parse_equality_bodies(page_html: str) -> Dict[str, Dict[str, str]]:
    rows: Dict[str, Dict[str, str]] = {}
    start_match = re.search(r"<h2>National equality bodies</h2>(.*)", page_html, re.S)
    if not start_match:
        return rows
    section_html = start_match.group(1)
    matches = list(re.finditer(r"<h3>(.*?)</h3>", section_html, re.S))
    allowed_countries = {name for _, name in EU27}
    for index, match in enumerate(matches):
        country_name = canonical_country_name(match.group(1))
        if country_name not in allowed_countries:
            continue
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else section_html.find("</div>", start)
        if end == -1:
            end = len(section_html)
        block = section_html[start:end]
        paragraphs = re.findall(r"<p>(.*?)</p>", block, re.S)
        body_names: List[str] = []
        body_urls: List[str] = []
        for paragraph in paragraphs:
            links = re.findall(r'<a href="([^"]+)"[^>]*>.*?<span class="ecl-link__label">(.*?)</span>', paragraph, re.S)
            if not links:
                continue
            labels = [clean_text(label) for _, label in links if clean_text(label)]
            urls = [html.unescape(url).strip() for url, _ in links if html.unescape(url).strip()]
            if labels:
                body_names.append(" / ".join(labels))
            if urls:
                body_urls.append(urls[0])
        rows[country_name] = {
            "name": "; ".join(body_names),
            "url": " ; ".join(dict.fromkeys(body_urls)),
        }
    return rows


def consumer_hint(
    country_name: str,
    dscs: Dict[str, Dict[str, str]],
    competition: Dict[str, Dict[str, str]],
) -> Dict[str, str]:
    if country_name == "Denmark" and country_name in competition:
        return {
            "name": "Danish Competition and Consumer Authority (DCCA)",
            "url": competition[country_name]["url"],
        }
    if country_name == "Estonia" and country_name in dscs:
        return {
            "name": "Consumer Protection and Technical Regulatory Authority (CPTRA)",
            "url": dscs[country_name]["url"],
        }
    if country_name == "Finland" and country_name in competition:
        return {
            "name": "Finnish Competition and Consumer Authority",
            "url": competition[country_name]["url"],
        }
    if country_name == "Ireland" and country_name in competition:
        return {
            "name": "Competition and Consumer Protection Commission (CCPC)",
            "url": competition[country_name]["url"],
        }
    if country_name == "Latvia" and country_name in dscs:
        return {
            "name": "Consumer Rights Protection Centre",
            "url": dscs[country_name]["url"],
        }
    if country_name == "Netherlands" and country_name in competition:
        return {
            "name": "Authority for Consumers and Markets",
            "url": competition[country_name]["url"],
        }
    if country_name == "Malta" and country_name in competition:
        return {
            "name": "Malta Competition and Consumer Affairs Authority (MCCAA)",
            "url": competition[country_name]["url"],
        }
    if country_name == "Poland" and country_name in competition:
        return {
            "name": "Office of Competition and Consumer Protection",
            "url": competition[country_name]["url"],
        }
    return {"name": "", "url": ""}


def join_notes(parts: List[str]) -> str:
    return " ".join(part for part in parts if part)


def build_rows() -> List[Dict[str, str]]:
    dscs = parse_dscs(fetch(DSC_URL))
    dpas = parse_dpas(fetch(DPA_URL))
    berec = parse_berec_members(fetch(BEREC_URL))
    competition = parse_competition_authorities(fetch(COMPETITION_URL))
    equality = parse_equality_bodies(fetch(EQUALITY_URL))

    rows: List[Dict[str, str]] = []
    for country_code, country_name in EU27:
        dsc = dscs.get(country_name, {"name": "", "url": ""})
        dpa = dpas.get(country_name, {"name": "", "url": ""})
        telecom = berec.get(country_name, {"name": "", "url": ""})
        competition_body = competition.get(country_name, {"name": "", "url": ""})
        equality_body = equality.get(country_name, {"name": "", "url": ""})
        consumer = consumer_hint(country_name, dscs, competition)

        notes: List[str] = []
        if not dsc["name"]:
            notes.append("Commission DSC page did not list a designated coordinator in this snapshot.")
        if dsc["name"] and telecom["name"] and dsc["name"] == telecom["name"]:
            notes.append("Digital Services Coordinator also matches the telecom/media regulator.")
        if dsc["name"] and competition_body["name"] and dsc["name"] == competition_body["name"]:
            notes.append("Digital Services Coordinator also matches the competition authority.")
        if consumer["name"] and competition_body["name"] and consumer["name"] in competition_body["name"]:
            notes.append("Competition authority also carries an explicit consumer-protection remit.")
        if consumer["name"] and dsc["name"] and consumer["name"] in dsc["name"]:
            notes.append("Digital Services Coordinator also carries an explicit consumer-protection remit.")
        if equality_body["name"] and ";" in equality_body["name"]:
            notes.append("More than one equality body is listed in the official source snapshot.")

        rows.append(
            {
                "country_code": country_code,
                "country_name": country_name,
                "digital_services_coordinator_name": dsc["name"],
                "digital_services_coordinator_url": dsc["url"],
                "data_protection_authority_name": dpa["name"],
                "data_protection_authority_url": dpa["url"],
                "consumer_protection_authority_name": consumer["name"],
                "consumer_protection_authority_url": consumer["url"],
                "telecom_or_media_regulator_name": telecom["name"],
                "telecom_or_media_regulator_url": telecom["url"],
                "competition_authority_name": competition_body["name"],
                "competition_authority_url": competition_body["url"],
                "accessibility_or_equality_body_name": equality_body["name"],
                "accessibility_or_equality_body_url": equality_body["url"],
                "last_verified": LAST_VERIFIED,
                "notes": join_notes(notes),
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
                "digital_services_coordinator_name",
                "digital_services_coordinator_url",
                "data_protection_authority_name",
                "data_protection_authority_url",
                "consumer_protection_authority_name",
                "consumer_protection_authority_url",
                "telecom_or_media_regulator_name",
                "telecom_or_media_regulator_url",
                "competition_authority_name",
                "competition_authority_url",
                "accessibility_or_equality_body_name",
                "accessibility_or_equality_body_url",
                "last_verified",
                "notes",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)


def linked(label: str, url: str, blank_label: str) -> str:
    label_parts = [part.strip() for part in label.split(";") if part.strip()]
    url_parts = [part.strip() for part in url.split(" ; ") if part.strip()]
    if len(label_parts) > 1 and len(label_parts) == len(url_parts):
        return "; ".join(f"[{name}]({target})" for name, target in zip(label_parts, url_parts))
    if label and url:
        return f"[{label}]({url_parts[0] if url_parts else url})"
    if label:
        return label
    return blank_label


def write_markdown(rows: List[Dict[str, str]]) -> None:
    dsc_count = sum(1 for row in rows if row["digital_services_coordinator_name"])
    dpa_count = sum(1 for row in rows if row["data_protection_authority_name"])
    consumer_count = sum(1 for row in rows if row["consumer_protection_authority_name"])
    telecom_count = sum(1 for row in rows if row["telecom_or_media_regulator_name"])
    competition_count = sum(1 for row in rows if row["competition_authority_name"])
    accessibility_count = sum(1 for row in rows if row["accessibility_or_equality_body_name"])

    with MD_PATH.open("w", encoding="utf-8") as f:
        f.write("# National Digital Authorities (Markdown view)\n\n")
        f.write("Source: data/national-authorities/national-digital-authorities.csv\n\n")
        f.write(
            "This is a first-pass routing layer for citizens facing digital harms in EU Member States. "
            "It prioritises authority types that can be rebuilt from central EU-level or official directory pages: "
            "Digital Services Coordinators, data protection authorities, telecom or media regulators, and competition authorities.\n\n"
        )
        f.write(
            "Consumer-protection fields in this summary file are only populated where that remit is explicit in the same central source pass. "
            "A fuller CPC layer now lives in `national-cpc-authorities.md`. "
            "Equality bodies are now backfilled from the Commission's official equality-bodies page. "
            "Web-accessibility bodies are still not flattened into this summary file because those structures are often split across multiple roles and levels. "
            "A detailed web-accessibility layer lives in `national-web-accessibility-bodies.md`, and a detailed equality-body layer lives in `national-equality-bodies.md`.\n\n"
        )
        f.write(
            "Use this file as the summary routing layer. For the detailed consumer-protection layer, see "
            "`national-cpc-authorities.md`. For the web-accessibility enforcement layer, see "
            "`national-web-accessibility-bodies.md`. For the equality-body layer, see "
            "`national-equality-bodies.md`.\n\n"
        )
        f.write(
            f"Coverage in this snapshot: {len(rows)} Member States, "
            f"{dsc_count} DSCs, {dpa_count} DPAs, {consumer_count} consumer bodies, "
            f"{telecom_count} telecom/media regulators, {competition_count} competition authorities, "
            f"{accessibility_count} accessibility/equality bodies.\n\n"
        )
        f.write("| country | DSC | DPA | consumer | telecom/media | competition | accessibility/equality | notes |\n")
        f.write("| --- | --- | --- | --- | --- | --- | --- | --- |\n")
        for row in rows:
            f.write(
                "| "
                + row["country_name"]
                + " | "
                + linked(
                    row["digital_services_coordinator_name"],
                    row["digital_services_coordinator_url"],
                    "Not yet listed in source snapshot",
                )
                + " | "
                + linked(
                    row["data_protection_authority_name"],
                    row["data_protection_authority_url"],
                    "No authority parsed",
                )
                + " | "
                + linked(
                    row["consumer_protection_authority_name"],
                    row["consumer_protection_authority_url"],
                    "See national-cpc-authorities.md",
                )
                + " | "
                + linked(
                    row["telecom_or_media_regulator_name"],
                    row["telecom_or_media_regulator_url"],
                    "No authority parsed",
                )
                + " | "
                + linked(
                    row["competition_authority_name"],
                    row["competition_authority_url"],
                    "No authority parsed",
                )
                + " | "
                + linked(
                    row["accessibility_or_equality_body_name"],
                    row["accessibility_or_equality_body_url"],
                    "See national-web-accessibility-bodies.md / national-equality-bodies.md",
                )
                + " | "
                + (row["notes"] or " ")
                + " |\n"
            )

        f.write("\nSources:\n\n")
        f.write(f"- Digital Services Coordinators: <{DSC_URL}>\n")
        f.write(f"- EDPB members / DPAs: <{DPA_URL}>\n")
        f.write(f"- BEREC members / telecom and media regulators: <{BEREC_URL}>\n")
        f.write(f"- ECN national competition authorities: <{COMPETITION_URL}>\n")
        f.write(f"- Commission equality bodies page: <{EQUALITY_URL}>\n")


def main() -> None:
    rows = build_rows()
    write_csv(rows)
    write_markdown(rows)
    print(f"Wrote {len(rows)} rows to {CSV_PATH.relative_to(ROOT)}")
    print(f"Wrote Markdown view to {MD_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
