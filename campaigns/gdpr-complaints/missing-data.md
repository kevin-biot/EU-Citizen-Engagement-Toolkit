# GDPR Campaign Missing Data

Use this as the working queue for slow harvest runs.

## Priority Queue

### High

- country-by-country DPA complaint portals, complaint instructions, and follow-up norms
Why it matters:
- campaign execution depends on knowing the real authority intake routes and expected steps
Status:
- all `27` Member States now mapped in `dpa-complaint-routes.{csv,md}`, but `Belgium`, `Cyprus`, `Finland`, and `Hungary` still need a cleaner or more stable complaint-entry pass

- stronger GDPR-specific journalist and newsroom routes
Why it matters:
- privacy and enforcement stories need specialist handling
Status:
- integrated through `gdpr-privacy-enforcement-support-routes.{csv,md}` and the `GDPR Enforcement Pressure` bundle, but still partial for country-specific specialist privacy desks

- regulator-delay and under-enforcement templates
Why it matters:
- current repo is stronger on first complaint than on stalled-case pressure
Status:
- integrated for core English campaign use through `campaigns/gdpr-complaints/emails/`, but still partial for country-specific or ombudsman-adjacent variants

### Medium

- cross-border one-stop-shop references and lead-authority mapping notes
Why it matters:
- large-platform GDPR campaigns often become cross-border quickly
Status:
- integrated through `campaigns/gdpr-complaints/one-stop-shop.md` and `data/national-authorities/gdpr-cross-border-reference.{csv,md}`, but still partial for controller-specific establishment mapping

- more national privacy-rights organisation coverage beyond current bundle countries
Why it matters:
- the bundle layer is useful but still sparse
Status:
- partial

### Lower

- example anonymized case chronologies
Why it matters:
- useful for training and repeatable campaign practice
Status:
- missing

## Slow Harvest Plan

### Pass 1

Harvest one country family at a time for DPA intake and escalation details.

Current state:
- first family integrated: `France`, `Germany`, `Ireland`, `Italy`, `Netherlands`, `Spain`, `Poland`
- second family mostly integrated: `Austria`, `Belgium`, `Denmark`, `Sweden`
- third family integrated or partially integrated: `Finland`, `Luxembourg`, `Portugal`, `Czechia`, `Slovakia`
- fourth family integrated: `Croatia`, `Estonia`, `Latvia`, `Lithuania`, `Romania`
- fifth family integrated: `Bulgaria`, `Cyprus`, `Greece`, `Hungary`, `Malta`, `Slovenia`

Next family:
- `Belgium` portal re-check after `May 8, 2026`
- cleanup pass for `Cyprus`, `Finland`, and `Hungary`
- build a lightweight script or schema note for future DPA-route refreshes

### Pass 2

Harvest NGO and journalist routes specifically for privacy, adtech, profiling, and enforcement-failure stories.

### Pass 3

Harvest regulator-delay patterns and build dedicated templates from real complaint timelines.

## Status Legend

- `missing`
- `partial`
- `mapped`
- `integrated`
