# EU Citizen Engagement Toolkit

**Democratic infrastructure for AI-augmented engagement with EU institutions**

## What This Is

This repository provides **templates, guides, datasets, and local tooling** for individuals, community groups, journalists, advocates, and SMEs who need to engage effectively with EU institutions and adjacent national enforcement routes.

It now covers both:

- **process navigation**: consultations, complaints, access-to-documents, Ombudsman routes, public-interest outreach
- **contact and routing infrastructure**: MEPs, Commission leadership and media surfaces, national digital authorities, public-interest organisations, and issue-specific escalation bundles

**Key innovation:** combines existing EU engagement mechanisms with AI-assisted capability so people can act with institutional awareness and procedural discipline without needing a large legal or lobbying budget.

## What You'll Find Here

- **Templates:** ready-to-use filings, complaint skeletons, and administrative correspondence
- **Guides:** practical walkthroughs for EU institutional processes
- **Digital Issue Playbooks:** citizen-facing guides for platform harms, GDPR issues, scams, accessibility failures, AI harms, and cross-border consumer problems
- **Campaign Packs:** extended issue playbooks for multi-target, evidence-heavy, time-sequenced advocacy
- **Outreach Templates:** short emails for MEPs, committee coordinators, journalists, NGOs, and Commission process challenges
- **Template Selector Layer:** registry and use-case selector data for choosing the right template family and fallback
- **Reference Data:** Parliament, Commission, national-authority, and community-contact layers
- **Issue Bundles:** curated contact bundles with `why_this_route` logic
- **Local MCP Server:** a repo-native MCP package for Claude/Codex-style local agents to query playbooks, templates, datasets, contacts, bundles, and routing guidance
- **Scripts:** data builders, extractors, and validation utilities

## Repository Map

- `templates/`: formal drafting templates by escalation level
- `docs/`: narrative guides, digital issue playbooks, and outreach email templates
- `campaigns/`: extended campaign packs with targets, evidence, messaging, timelines, escalation, and missing-data queues
- `data/`: structured reference data and contact layers
- `mcp-server/`: local MCP package exposing the repo as a structured assistant surface
- `scripts/`: builders, extractors, validators, and maintenance scripts

## Data Coverage

Current data layers include:

- **Parliament-side reference**: MEP contact database, topic tags, committee extracts, committee leadership tags
- **Commission reference**: College of Commissioners, cabinet contacts, spokesperson roster, DG press surfaces, Commissioners' Project Groups
- **National authority routing**: Digital Services Coordinators, DPAs, competition authorities, CPC consumer authorities, equality bodies, and web-accessibility bodies
- **Community escalation routes**: digital-rights groups, journalism-support organisations, women’s-rights and equality routes, EWL member-network references, and issue-specific contact bundles
- **Institutional routes**: functional mailboxes, secretariats, and access-to-documents surfaces
- **Template selection data**: registry and selector layers that map use cases to concrete repo templates

## Documentation Coverage

Current docs now include:

- getting-started material
- digital-issue playbooks
- campaign packs
- outreach email templates
- template-family design notes
- citizen digital support roadmap
- MCP install and usage guides

## Quick Start

1. **Identify the issue or route you need**
See `docs/` for playbooks and process guidance.

2. **Choose the right source layer**
Use `data/` for contacts, authorities, Commission/Parliament references, and escalation bundles.

3. **Choose the right campaign layer if the issue needs repeated pressure**
Use `campaigns/` when the issue needs targets, sequencing, escalation, and evidence tracking rather than a one-off filing.

4. **Choose or assemble the right draft**
Use `templates/`, `docs/digital-issues/email-templates/`, or `docs/outreach-email-templates/`.

If you need help choosing between them, use the selector data in `data/template-selector/`.

5. **Use the MCP server if you want AI assistance grounded in the repo**
See `mcp-server/README.md`, `mcp-server/INSTALL.md`, and `mcp-server/USER_GUIDE.md`.

6. **Verify before sending**
This repo helps with routing and drafting, but you still need to check official requirements and current institutional guidance.

## Current Status

**Version:** 1.x (Framework + active data and MCP tooling)  
**Status:** Community development phase  
**Validated:** Framework in use; datasets and MCP server under active iteration  
**Languages:** English (translations welcomed as contributions)

## Contributing

This is **community infrastructure**—your contributions make it better:

- **Test templates** and share what worked/didn't work
- **Submit improvements** via pull requests
- **Share case studies** (anonymized if needed)
- **Translate templates** to other EU languages
- **Report issues** when you find gaps or errors

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## Important Disclaimers

⚠️ **This is not legal advice.** These are informational templates and guides.

⚠️ **This is not medical or financial advice.** The MCP server now explicitly marks those queries as out of scope.

⚠️ **You use these at your own risk.** Always verify against official institutional guidance.

⚠️ **Success not guaranteed.** Institutions have legitimate defenses and procedural requirements.

⚠️ **Time investment required.** Budget 100-300 hours spread over 2-4 years for full engagement.

## License

This work is licensed under [Creative Commons Attribution-ShareAlike 4.0 International](LICENSE).

**You are free to:**
- Use these templates for any purpose
- Adapt them to your needs
- Share them with others

**Under these terms:**
- Attribute this project
- Share improvements under same license

## Acknowledgments

Built on decades of EU institutional experience and AI-augmented development methodologies.

Community contributions welcomed and credited in [CONTRIBUTORS.md](CONTRIBUTORS.md).

## Contact & Support

- **Issues:** Use GitHub Issues for bugs, questions, template improvements
- **Discussions:** Use GitHub Discussions for strategy, case coordination, peer support
- **Updates:** Watch this repo for new templates and framework improvements

**This is infrastructure for democratic participation. Use it. Improve it. Share it.**

## Key Entry Points

- Citizen authorship: `manifesto-human-authorship.md` (root)
- Ombudsman form guide: `docs/ombudsman-form-guide.md`
- Verticalization guide (fork-and-layer by topic): `docs/topic-verticalization.md`
- Citizen digital needs roadmap: `docs/citizen-digital-needs-roadmap.md`
- Digital issue playbooks: `docs/digital-issues/`
- Campaign packs: `campaigns/README.md`
- Outreach email templates: `docs/outreach-email-templates/`
- Template families: `docs/template-families/README.md`
- Data index: `data/README.md`
- Docs index: `docs/README.md`
- Local MCP server: `mcp-server/README.md`
- MCP install guide: `mcp-server/INSTALL.md`
- MCP user guide: `mcp-server/USER_GUIDE.md`

## Positioning vs. Other Participation Tools

- **Citizens' Engagement Platform (European Commission)** — Official front door for public debates/consultations/Citizens' Panels. Complementary: this toolkit helps citizens use it effectively and escalate beyond it.
- **Citizen-Led Action Toolkit (CitiObs, EU-funded)** — Practical guides for community-led environmental monitoring. Parallel: shows demand for actionable toolkits; here the focus is regulatory/legal process navigation.
- **Your Priorities / Active Citizen (CitizensFoundation)** — Open-source platforms for debate/prioritization. Different domain: provides the tech forum; this toolkit provides the strategic “how” for engagement.
- **NetZeroCities Engagement Tools (EU Mission)** — Frameworks for cities to engage stakeholders on climate. Different audience: aimed at city admins designing processes; this toolkit empowers individuals to navigate them.

**Unique value:** Self-advocacy and execution-layer know-how for regulatory/legal engagement (DMA/PSD/FOI/Ombudsman/courts), not just structured participation via official portals.
