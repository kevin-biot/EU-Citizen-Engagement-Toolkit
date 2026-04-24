# Template Selector

Source: [template-selector.csv](/Users/kevinbrown/EU-Citizen-Engagement-Toolkit/data/template-selector/template-selector.csv:1)

This file maps recurring use cases to the best current template and a fallback.

It is a selector layer, not a prose guide.

Current coverage in this pass: `18` recurring use cases.

| use case | primary template | fallback | scope | note |
| --- | --- | --- | --- | --- |
| Respond to an EU public consultation | `consultation_response_template` | — | `EU` | Use when the task is a real open consultation submission rather than a complaint. |
| Request EU institution documents | `foi_request_template` | — | `EU` | Use for Regulation 1049/2001 document requests. |
| Complain to the European Ombudsman about maladministration | `ombudsman_complaint_template` | — | `EU` | Use only for EU institutions or bodies after direct contact. |
| Challenge a platform suspension or removal | `platform_account_suspension_email` | `mep_outreach_procedural_concern_email` | `Mixed` | Start with the platform route; move to politics only if the issue becomes systemic. |
| Follow up on illegal content or notice-and-action failure | `illegal_content_and_dsa_email` | `committee_coordinator_procedural_concern_email` | `Mixed` | Preserve the platform chronology first. |
| Complain about dark patterns | `dark_patterns_email` | `ngo_support_request_email` | `Mixed` | Start with the direct complaint; escalate if the pattern looks systemic. |
| Make or repeat a controller-side GDPR rights request | `gdpr_data_rights_email` | `privacy_ngo_support_request_email` | `Mixed` | Start controller-side before external escalation. |
| Follow up after DPA silence on a GDPR complaint | `dpa_follow_up_after_silence_email` | `mep_gdpr_under_enforcement_email` | `National_or_cross_border` | First ask the DPA to move; use oversight pressure if the problem becomes systemic. |
| Ask a privacy NGO to review or amplify a systemic GDPR issue | `privacy_ngo_support_request_email` | `cross_border_complainant_coordination_note` | `Mixed` | Use when the issue is broader than one unresolved personal request. |
| Pitch a journalist on GDPR under-enforcement | `journalist_gdpr_enforcement_pitch_email` | `journalist_issue_pitch_email` | `EU_or_national` | Prefer the GDPR-specific pitch for enforcement stories. |
| Coordinate several complainants before cross-border GDPR escalation | `cross_border_complainant_coordination_note` | `privacy_ngo_support_request_email` | `EU_cross_border` | Use when shared chronology and internal alignment come first. |
| Raise a procedural concern with an MEP on a live policy file | `mep_outreach_procedural_concern_email` | `committee_coordinator_procedural_concern_email` | `EU` | Use the coordinator fallback only when committee leverage matters. |
| Pressure a committee coordinator on process or pace | `committee_coordinator_procedural_concern_email` | `mep_outreach_procedural_concern_email` | `EU` | Use when the recipient's internal committee role is the point of contact. |
| Challenge a Commission consultation process | `commission_consultation_process_email` | `mep_outreach_procedural_concern_email` | `EU` | Use when the process itself is the grievance. |
| Pitch a journalist on a general public-interest issue | `journalist_issue_pitch_email` | `ngo_support_request_email` | `Mixed` | Use when the issue is public-interest but not yet a GDPR under-enforcement story. |
| Ask an NGO or network to review or amplify a concern | `ngo_support_request_email` | `journalist_issue_pitch_email` | `Mixed` | Use when coalition and review matter more than publicity. |
| Report an accessibility failure to the service owner first | `digital_accessibility_failure_email` | `ngo_support_request_email` | `Mixed` | Use for the first remediation ask, not for an ombudsman end-stage filing. |
| Send a first documented complaint on a cross-border consumer dispute | `cross_border_consumer_dispute_email` | `ngo_support_request_email` | `Mixed` | Use the trader or platform complaint first, then escalate externally if needed. |

## Limits

- This is only the first selector pass.
- It does not yet cover national ombudsman templates because those templates do not yet exist.
- It does not yet express language variants or country-specific forks.
- It is intended to support future MCP recommendation tools, but is already usable by contributors and human operators now.
