# MEP Extracts: How to Find the Right Door

This folder contains ready-made CSV subsets derived from `complete_mep_database.csv`. Use them to quickly identify the gatekeepers for a given topic.

## Where to start
- **Digital/AI policy**: look first at `committees/IMCO_members.csv`, `ITRE_members.csv`, `LIBE_members.csv`, `JURI_members.csv`, `ECON_members.csv`.
- **Gatekeepers**: `gatekeepers/all_gatekeepers.csv` plus committee-specific files (e.g., `gatekeepers/IMCO_gatekeepers.csv`). These rely on `role_tags` (chairs/vice-chairs/leadership).
- **Group alignment**: `groups/*.csv` for political ideology targeting (EPP, S&D, Renew, Greens/EFA, ECR, PFE, LEFT, ESN, NI).
- **Country relevance**: `countries/*.csv` for national campaigns.
- **Strategic coalitions**: `strategic/AI_Act_Coalition.csv`, `Digital_Rights_Champions.csv`, `EU_AI_Governance_Taskforce.csv`, `Tech_Industry_Contacts.csv`.
- **Lane² focus**: `lane2/*.csv` for compliance, telco/digital transformation, cross-border coordination, and digital single market champions.

## Quick queries
Use the helper to combine filters at once:
```
python3 scripts/query_meps.py --committee IMCO --group EPP --role chair
python3 scripts/query_meps.py --policy "ai act" --committee LIBE --group GREENS_EFA
python3 scripts/query_meps.py --country Germany --committee ITRE --limit 10
```

## Regenerating extracts
```
python3 scripts/build_complete_csv.py    # rebuild canonical CSV from markdown slices
python3 scripts/extract_meps.py          # regenerate all extracts
python3 scripts/validate_extractions.py  # sanity checks (counts/dupes/email format)
```

## Notes
- Counts in extracts are deduped by email (fallback: name).
- `role_tags` currently covers EP President/Vice-Presidents and select chairs/vice-chairs (IMCO, ITRE, LIBE, JURI, ECON, plus some others). Expand as you learn more: edit `ROLE_TAGS` in `scripts/build_complete_csv.py` and rebuild.
- If you need a 720-row master (without merging duplicate entries), we can reintroduce the split records; current master is deduped to 716 unique entries.
