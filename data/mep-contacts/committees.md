# European Parliament Committees: Codes and Purpose

This file maps committee codes found in the MEP database to their full names, scope, and why they matter for citizen engagement—especially on digital, AI, and regulatory topics.

## Core committees
- **AFET** — Foreign Affairs: External relations, security policy, sanctions, enlargement; critical for cross-border digital cooperation and standards diplomacy.
- **AFCO** — Constitutional Affairs: Institutional rules, treaty questions, subsidiarity; key for governance frameworks and institutional powers.
- **AGRI** — Agriculture and Rural Development: CAP, food systems, agri-tech, rural innovation.
- **ANIT** — Animal Transport (special): Animal welfare in transport; narrow scope, occasional relevance.
- **AIDA** — Artificial Intelligence in the Digital Age (historical special committee): AI impact studies; context for legacy AI work.
- **BUDG** — Budgets: EU budget design, MFF, funding priorities; important for program financing (digital/AI spend).
- **CONT** — Budgetary Control: Oversight and anti-fraud; leverage for compliance and transparency angles.
- **CULT** — Culture and Education: Media freedom, cultural programs, education, disinformation; relevant for digital media policy.
- **DEVE** — Development: External development policy; ties to digital inclusion abroad.
- **DROI** — Human Rights (Subcommittee): Global human rights; relevant for surveillance, digital repression, exports.
- **DMER** — Common Market for Medicines (special): Medicine/health market (rare).
- **EUDS** — European Democracy Shield (special): Safeguarding democracy, disinformation, election integrity—strong digital link.
- **ECON** — Economic and Monetary Affairs: Financial services, fintech, digital euro, taxation, competition; central for digital finance and platform economics.
- **EMPL** — Employment and Social Affairs: Labor rights, platform work, social protections, skills.
- **ENVI** — Environment, Public Health, Food Safety: Climate, environment, health; digital health, green tech, data for environment.
- **FEMM** — Women’s Rights and Gender Equality: Gender impacts, inclusion in digital/AI, online safety.
- **FISC** — Tax Matters (Subcommittee): Tax policy, digital taxation, corporate tax fairness.
- **HOUS** — Housing Crisis (special): Housing policy (contextual; limited digital link unless smart-city/proptech focus).
- **IMCO** — Internal Market and Consumer Protection: Single market, product safety, DSA/DMA/AI Act implementation, consumer rights—primary digital/AI gatekeeper.
- **INTA** — International Trade: Trade agreements, digital trade chapters, data flows, export controls.
- **ITRE** — Industry, Research, Energy: Industrial strategy, R&D, Horizon Europe, energy, AI policy, digital infrastructure—primary digital/AI gatekeeper.
- **JURI** — Legal Affairs: Liability, IP, corporate governance, AI liability, standard-essential patents—primary digital/AI gatekeeper.
- **LIBE** — Civil Liberties, Justice, Home Affairs: Privacy, data protection, surveillance, migration; AI ethics and rights—primary digital/AI gatekeeper.
- **PECH** — Fisheries: Fisheries policy; occasionally tech/traceability angles.
- **PETI** — Petitions: Citizen petitions; procedural channel to raise issues.
- **REGI** — Regional Development: Cohesion funds, regional innovation, smart regions.
- **SANT** — Public Health (Subcommittee): Health systems, digital health, preparedness.
- **SEDE** — Security and Defence: Defence policy, cybersecurity, cyber-defence, hybrid threats.
- **TRAN** — Transport and Tourism: Mobility, infrastructure, logistics; digital/AI in transport.

## Notes on usage
- Prioritize **IMCO**, **ITRE**, **LIBE**, **JURI**, **ECON** for AI/digital governance.
- For leadership targets, combine committee + `role_tags` (chair/vice/coordinator/rapporteur) to find gatekeepers.
- Special/temporary committees (AIDA, ANIT, EUDS, DMER, HOUS) may sunset or change scope; treat as contextual.

## How to extend
Update this file when new special committees appear or scopes change. If you add codes to `KNOWN_COMMITTEES` in `scripts/build_complete_csv.py`, mirror the description here.
