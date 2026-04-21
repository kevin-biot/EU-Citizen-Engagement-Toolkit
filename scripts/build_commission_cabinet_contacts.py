#!/usr/bin/env python3
"""
Build a citizen-facing reference of European Commission cabinet contacts.

Sources:
  - Current College profile pages on commission.europa.eu
  - Individual cabinet/team pages linked from those profiles

Outputs:
  - data/commission-reference/commission-cabinet-contacts.csv
  - data/commission-reference/commission-cabinet-contacts.md

The script uses only the Python standard library so it can run in this repo
without extra dependencies.
"""

from __future__ import annotations

import csv
import html
import re
import time
import unicodedata
from datetime import date
from pathlib import Path
from typing import Dict, Iterable, List, Optional
from urllib.error import HTTPError
from urllib.parse import urljoin
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data" / "commission-reference"
COLLEGE_CSV = DATA_DIR / "commission-college.csv"
CABINET_CSV = DATA_DIR / "commission-cabinet-contacts.csv"
CABINET_MD = DATA_DIR / "commission-cabinet-contacts.md"
BASE_URL = "https://commission.europa.eu"
LAST_VERIFIED = date.today().isoformat()
USER_AGENT = "Mozilla/5.0 (compatible; EUCitizenEngagementToolkit/1.0; +https://github.com/kevin-biot/EU-Citizen-Engagement-Toolkit)"


def fetch(url: str) -> str:
    request = Request(url, headers={"User-Agent": USER_AGENT})
    delay = 1.2
    for attempt in range(5):
        try:
            with urlopen(request, timeout=30) as response:
                body = response.read().decode("utf-8", "ignore")
            time.sleep(delay)
            return body
        except HTTPError as exc:
            if exc.code == 429 and attempt < 4:
                time.sleep(8 * (attempt + 1))
                continue
            raise
    raise RuntimeError(f"Failed to fetch {url}")


def load_college_rows() -> List[Dict[str, str]]:
    with COLLEGE_CSV.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def slugify_name(name: str) -> str:
    replacements = {
        "ø": "o",
        "Ø": "O",
        "æ": "ae",
        "Æ": "Ae",
        "œ": "oe",
        "Œ": "Oe",
        "ß": "ss",
    }
    for source, target in replacements.items():
        name = name.replace(source, target)
    normalized = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-z0-9]+", "-", normalized.lower()).strip("-")
    return slug


def commissioner_profile_url(member_name: str) -> str:
    if member_name == "Ursula von der Leyen":
        return f"{BASE_URL}/about/organisation/president/about-president_en"
    return f"{BASE_URL}/about/organisation/college-commissioners/{slugify_name(member_name)}_en"


def clean_text(value: str) -> str:
    value = re.sub(r"<br\s*/?>", "\n", value, flags=re.IGNORECASE)
    value = re.sub(r"<[^>]+>", "", value)
    value = html.unescape(value)
    value = value.replace("\xa0", " ")
    value = re.sub(r"\s+", " ", value)
    return value.strip()


def normalize_email_piece(value: str) -> str:
    cleaned = clean_text(value)
    cleaned = cleaned.replace("[dot]", ".")
    cleaned = cleaned.replace(" [dot] ", ".")
    cleaned = cleaned.replace(" [dot]", ".")
    cleaned = cleaned.replace("[dot] ", ".")
    cleaned = cleaned.replace(" ", "")
    return cleaned


def normalize_obfuscated_email(value: str) -> str:
    cleaned = clean_text(value)
    cleaned = cleaned.replace("[dot]", ".")
    cleaned = cleaned.replace("[at]", "@")
    cleaned = cleaned.replace(" ", "")
    return cleaned


def extract_email(block: str) -> str:
    href_email = re.search(r'href="([^"?]+@[^"?]+)', block)
    if href_email:
        return href_email.group(1).strip()

    parenthetical = re.search(r"\(([^()]+?\[at\][^()]+)\)", block)
    if parenthetical:
        return normalize_obfuscated_email(parenthetical.group(1))

    user_domain = re.search(
        r'<span class="u">(.*?)</span>\s*<img class="spamspan-image"[^>]*>\s*<span class="d">(.*)</span>\s*</span>',
        block,
        re.S,
    )
    if user_domain:
        user = normalize_email_piece(user_domain.group(1))
        domain = normalize_email_piece(user_domain.group(2))
        if user and domain:
            return f"{user}@{domain}"

    return ""


def extract_phone(block: str) -> str:
    match = re.search(r"Phone number:\s*</strong>\s*<a [^>]*>([^<]+)</a>", block, re.S)
    return clean_text(match.group(1)) if match else ""


def extract_team_url(profile_html: str, profile_url: str) -> str:
    match = re.search(r'href="([^"]+team_en)"', profile_html)
    if match:
        return urljoin(BASE_URL, match.group(1))
    if "/about/organisation/president/" in profile_url:
        return f"{BASE_URL}/about/organisation/president/president-von-der-leyens-team_en"
    raise ValueError(f"No team page found for {profile_url}")


def extract_office_contact(team_html: str) -> tuple[str, str]:
    office_email = re.search(
        r'<dt class="ecl-description-list__term">Email</dt><dd class="ecl-description-list__definition"><div>(.*?)</div></dd>',
        team_html,
        re.S,
    )
    if office_email:
        return ("cabinet_email", extract_email(office_email.group(1)))

    president_contact = re.search(r'href="([^"]+/contact-president_en)"[^>]*>Contact the President<', team_html)
    if president_contact:
        return ("contact_page", urljoin(BASE_URL, president_contact.group(1)))

    return ("", "")


def extract_people(team_html: str) -> List[Dict[str, str]]:
    heading_pattern = re.compile(r"<h2 class=['\"]ecl-u-type-heading-2['\"]>(.*?)</h2>", re.S)
    headings = list(heading_pattern.finditer(team_html))
    people: List[Dict[str, str]] = []

    for index, heading in enumerate(headings):
        start = heading.start()
        end = headings[index + 1].start() if index + 1 < len(headings) else len(team_html)
        block = team_html[start:end]
        role_match = re.search(r'ecl-featured-item__title"[^>]*>(.*?)</div>', block, re.S)
        if not role_match:
            continue
        people.append(
            {
                "name": clean_text(heading.group(1)),
                "role": clean_text(role_match.group(1)).upper(),
                "email": extract_email(block),
                "phone": extract_phone(block),
            }
        )

    return people


def select_person(people: Iterable[Dict[str, str]], role_patterns: List[str]) -> Dict[str, str]:
    for pattern in role_patterns:
        for person in people:
            if pattern in person["role"]:
                return person
    return {"name": "", "role": "", "email": "", "phone": ""}


def build_notes(office_contact_kind: str, assistant: Dict[str, str]) -> str:
    notes: List[str] = []
    if not office_contact_kind:
        notes.append("No generic office inbox published on the team page.")
    elif office_contact_kind == "contact_page":
        notes.append("President page links to a contact page instead of publishing a generic office inbox.")
    if not assistant["name"]:
        notes.append("No clearly designated assistant-to-principal role found on the team page.")
    return " ".join(notes)


def markdown_contact(kind: str, value: str) -> str:
    if not value:
        return ""
    if kind == "contact_page":
        return f"[Contact page]({value})"
    return value


def markdown_staff(name: str, email: str) -> str:
    if not name:
        return ""
    if email:
        return f"{name} ({email})"
    return name


def write_csv(path: Path, rows: List[Dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "member_name",
                "member_role",
                "office_contact_kind",
                "office_contact",
                "head_of_cabinet_name",
                "head_of_cabinet_email",
                "head_of_cabinet_phone",
                "deputy_head_of_cabinet_name",
                "deputy_head_of_cabinet_email",
                "deputy_head_of_cabinet_phone",
                "principal_assistant_name",
                "principal_assistant_role",
                "principal_assistant_email",
                "principal_assistant_phone",
                "team_page_url",
                "last_verified",
                "notes",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)


def write_markdown(path: Path, rows: List[Dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        f.write("# Commission Cabinet Contacts (Markdown view)\n\n")
        f.write("Source: data/commission-reference/commission-cabinet-contacts.csv\n\n")
        f.write(
            "This file focuses on public office-side contacts: the generic cabinet inbox where published, the Head of Cabinet, and the most direct assistant role visible on the official team page.\n\n"
        )
        f.write("| member_name | office_contact | head_of_cabinet | principal_assistant | team_page | notes |\n")
        f.write("| --- | --- | --- | --- | --- | --- |\n")
        for row in rows:
            f.write(
                "| "
                + row["member_name"]
                + " | "
                + markdown_contact(row["office_contact_kind"], row["office_contact"])
                + " | "
                + markdown_staff(row["head_of_cabinet_name"], row["head_of_cabinet_email"])
                + " | "
                + markdown_staff(row["principal_assistant_name"], row["principal_assistant_email"])
                + " | "
                + f"[team page]({row['team_page_url']})"
                + " | "
                + row["notes"]
                + " |\n"
            )

        f.write("\nOfficial sources:\n\n")
        f.write("- Current College of Commissioners: <https://commission.europa.eu/about/organisation/college-commissioners_en>\n")
        f.write("- Commission contact page: <https://commission.europa.eu/about/contact_en>\n")
        f.write("- Each row links to the specific official team page used for extraction.\n")


def main() -> None:
    rows_out: List[Dict[str, str]] = []
    for college_row in load_college_rows():
        member_name = college_row["member_name"]
        member_role = college_row["member_role"]
        profile_url = commissioner_profile_url(member_name)
        try:
            profile_html = fetch(profile_url)
            team_url = extract_team_url(profile_html, profile_url)
            team_html = fetch(team_url)
        except Exception as exc:
            raise RuntimeError(f"Failed to build cabinet contact row for {member_name} ({profile_url})") from exc

        office_contact_kind, office_contact = extract_office_contact(team_html)
        people = extract_people(team_html)

        head = select_person(people, ["HEAD OF CABINET"])
        deputy = select_person(people, ["DEPUTY HEAD OF CABINET"])
        assistant = select_person(
            people,
            [
                "ASSISTANT TO THE EXECUTIVE VICE-PRESIDENT",
                "ASSISTANT TO THE HIGH REPRESENTATIVE",
                "ASSISTANT TO THE COMMISSIONER",
                "ASSISTANT TO THE PRESIDENT",
                "PERSONAL ASSISTANT/MEMBER",
            ],
        )

        rows_out.append(
            {
                "member_name": member_name,
                "member_role": member_role,
                "office_contact_kind": office_contact_kind,
                "office_contact": office_contact,
                "head_of_cabinet_name": head["name"],
                "head_of_cabinet_email": head["email"],
                "head_of_cabinet_phone": head["phone"],
                "deputy_head_of_cabinet_name": deputy["name"],
                "deputy_head_of_cabinet_email": deputy["email"],
                "deputy_head_of_cabinet_phone": deputy["phone"],
                "principal_assistant_name": assistant["name"],
                "principal_assistant_role": assistant["role"],
                "principal_assistant_email": assistant["email"],
                "principal_assistant_phone": assistant["phone"],
                "team_page_url": team_url,
                "last_verified": LAST_VERIFIED,
                "notes": build_notes(office_contact_kind, assistant),
            }
        )

    write_csv(CABINET_CSV, rows_out)
    write_markdown(CABINET_MD, rows_out)
    print(f"Wrote {len(rows_out)} rows to {CABINET_CSV.relative_to(ROOT)}")
    print(f"Wrote Markdown view to {CABINET_MD.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
