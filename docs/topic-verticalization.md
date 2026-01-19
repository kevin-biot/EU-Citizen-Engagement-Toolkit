# How to Verticalize This Toolkit for a Specific Domain

This repo is designed to be forked and layered with domain-specific targets (e.g., women’s rights, climate, digital safety). The lightest way to do that is to add `topic_tags`, regenerate extracts, and use the query helper to find the right gatekeepers.

## Quick Start (example: women’s rights)

1) Add/extend an overlay  
   Edit `data/mep-contacts/overlays/women-rights.csv` (or add a new file) with `mep_name,topic_tags,notes`. Keep `mep_name` identical to the master CSV.

2) Generate topic-tagged master CSV  
   ```bash
   python3 scripts/add_topic_tags.py \
     --overlay data/mep-contacts/overlays/women-rights.csv \
     --out data/mep-contacts/complete_mep_database_topics.csv
   ```

3) Query by topic  
   ```bash
   python3 scripts/query_meps.py --topic women-rights --committee FEMM --limit 10
   ```
   The query helper will automatically prefer `complete_mep_database_topics.csv` when it exists.

4) Share the fork  
   Update the README to explain the vertical focus and link to your overlay and any topic-specific templates or playbooks.

## Tips for Creating Topic Overlays

- Use commas to stack multiple tags (e.g., `women-rights, gender-equality, GBV`).
- Anchor tags to real power centers: FEMM/LIBE/IMCO/ITRE/JURI; add group lenses if needed.
- Keep notes short and action-oriented (e.g., “DSA rapporteur; safety/gender angles”).
- If you need more tags, just add them to the overlay; the script will merge them.

## Suggested Extras for a Vertical Fork

- A “starter runbook” page: committees, key rapporteurs/shadows, standard asks, timelines, evidence requirements, and follow-up cadence.
- Topic-specific template variants (consultations, FOI, Ombudsman, confirmatory applications).
- An institutional contact shortlist relevant to your domain (DG secretariats, EP committee secretariats).
- Prebuilt extracts for your tags (e.g., run `query_meps.py --topic women-rights` and save to `data/mep-contacts/extracts/women-rights.csv`).

## File Map

- Overlays: `data/mep-contacts/overlays/`
- Topic-tagged master: `data/mep-contacts/complete_mep_database_topics.csv`
- Query helper: `scripts/query_meps.py` (`--topic` flag)
- Tagging script: `scripts/add_topic_tags.py`

This lets anyone fork the repo, add their own overlay, and immediately target the right committees, roles, and groups for their domain.***
