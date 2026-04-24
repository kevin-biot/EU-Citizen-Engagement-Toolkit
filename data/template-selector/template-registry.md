# Template Registry

Source: [template-registry.csv](/Users/kevinbrown/EU-Citizen-Engagement-Toolkit/data/template-selector/template-registry.csv:1)

This is the first metadata registry for concrete templates in the repo.

Current coverage in this pass: `21` concrete templates across:

- `formal_filing`
- `citizen_issue_email`
- `outreach_email`
- `campaign_email`

## By Family

### Formal Filing

| slug | title | target | scope | stage |
| --- | --- | --- | --- | --- |
| `consultation_response_template` | Consultation Response Template | Commission consultation or Have Your Say portal | `EU` | `pre_filing` |
| `foi_request_template` | Freedom of Information (FOI) Request Template | EU institution document-access office | `EU` | `initial_administrative` |
| `ombudsman_complaint_template` | European Ombudsman Complaint Template | European Ombudsman | `EU` | `oversight_escalation` |

### Citizen Issue Email

| slug | title | target | scope | stage |
| --- | --- | --- | --- | --- |
| `platform_account_suspension_email` | Platform Account Suspension Or Removal | Platform support or complaint team | `Mixed` | `initial_contact` |
| `illegal_content_and_dsa_email` | Illegal Content Or Notice-And-Action Problem | Platform notice-and-action or trust-and-safety team | `Mixed` | `initial_contact` |
| `dark_patterns_email` | Dark Patterns And Manipulative Design | Platform or trader compliance or support contact | `Mixed` | `initial_contact` |
| `gdpr_data_rights_email` | Data Access, Deletion, Or Profiling Problem | Controller or privacy office | `Mixed` | `initial_contact` |
| `ai_decision_harm_email` | AI Decision Harm Or Opaque Automated Output | Service provider or controller | `Mixed` | `initial_contact` |
| `online_scam_and_marketplace_harm_email` | Online Scam, Fake Seller, Or Marketplace Failure | Marketplace or payment-platform support or complaints team | `Mixed` | `initial_contact` |
| `digital_accessibility_failure_email` | Inaccessible Digital Service Or App | Service owner or accessibility contact | `Mixed` | `initial_contact` |
| `cross_border_consumer_dispute_email` | Cross-Border Online Consumer Dispute | Trader or platform complaints contact | `Mixed` | `initial_contact` |

### Outreach Email

| slug | title | target | scope | stage |
| --- | --- | --- | --- | --- |
| `mep_outreach_procedural_concern_email` | MEP Outreach On A Policy File Or Procedural Concern | MEP office | `EU` | `political_outreach` |
| `committee_coordinator_procedural_concern_email` | Committee Coordinator Pressure Email | Committee coordinator office | `EU` | `political_outreach` |
| `commission_consultation_process_email` | Commission Consultation Process Challenge | Commission service, cabinet, or Secretariat-General contact | `EU` | `process_challenge` |
| `journalist_issue_pitch_email` | Journalist Issue Pitch | Journalist or newsroom | `Mixed` | `media_outreach` |
| `ngo_support_request_email` | NGO Support Or Amplification Request | NGO or advocacy network | `Mixed` | `coalition_outreach` |

### Campaign Email

| slug | title | target | scope | stage |
| --- | --- | --- | --- | --- |
| `dpa_follow_up_after_silence_email` | DPA Follow-Up After Silence | National DPA | `National_or_cross_border` | `regulator_follow_up` |
| `privacy_ngo_support_request_email` | Privacy NGO Support Or Amplification Request | Privacy NGO or public-interest watchdog | `Mixed` | `coalition_outreach` |
| `journalist_gdpr_enforcement_pitch_email` | Journalist Pitch On GDPR Under-Enforcement | Journalist or newsroom | `EU_or_national` | `media_outreach` |
| `mep_gdpr_under_enforcement_email` | MEP Oversight Pressure On GDPR Under-Enforcement | MEP office | `EU` | `political_outreach` |
| `cross_border_complainant_coordination_note` | Cross-Border GDPR Complaint Coordination | Partner complainants or allied organisations | `EU_cross_border` | `coordination` |

## Why This Exists

This file makes template choice inspectable.

It helps answer:

- which templates are formal filings and which are emails
- which templates are EU-only
- which templates assume a campaign stage rather than an initial complaint
- which templates are visibly bad fits for a given jurisdiction or escalation step

See [ADR-0005](</Users/kevinbrown/EU-Citizen-Engagement-Toolkit/mcp-server/docs/adr/0005-metadata-driven-template-selection.md>) for the design decision.
