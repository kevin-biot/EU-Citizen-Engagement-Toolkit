# MCP Server User Guide

This guide explains what the MCP server is good at, how to ask it useful questions, and how to interpret the results.

## What The Server Is For

The server exposes the toolkit as structured local data for AI agents. It is strongest at:

- finding civic, media, rights, and institutional contact routes
- routing issues to the right playbook or authority layer
- returning country-level authority summaries
- surfacing Commission, Parliament, MEP, and community-contact datasets
- assembling draft context from templates and playbooks

It is not a general web-search engine, a medical directory, or a source of personal financial advice.

## Main Tool Families

### Playbooks and Templates

Use these when you already know you want a guide or a draft starting point.

- `list_playbooks`
- `get_playbook`
- `list_templates`
- `get_template`
- `list_templates_by_use_case`
- `recommend_template`
- `list_campaign_stages`
- `assess_campaign_stage`
- `recommend_next_step`
- `recommend_escalation`
- `list_email_templates`
- `get_email_template`
- `build_draft_packet`

Good prompts:

- `List the digital-issue playbooks`
- `Get the platform-account-suspension playbook`
- `Get the template foi-request-template`
- `List templates for gdpr_rights_request`
- `Recommend a template for DPA silence after a GDPR complaint`
- `Assess the GDPR campaign stage for a filed complaint with regulator silence`
- `Recommend the next GDPR campaign step for a cross-border complaint`
- `Build a draft packet for ombudsman-complaint-template using these facts: ...`

### Contact and Routing Search

Use these when you want to know who to contact or which route is most relevant.

- `find_contacts`
- `route_issue`
- `get_authorities`
- `list_bundles`
- `get_bundle`

Good prompts:

- `Route this issue: my account was suspended with no explanation`
- `Find contacts for AI accountability in Poland`
- `Get authorities for Germany`
- `Get the journalist_safety bundle`

### Structured Data

Use these when you want direct dataset access rather than semantic search.

- `list_datasets`
- `get_dataset`
- `query_dataset`
- `list_commission_project_groups`
- `get_commission_project_group`

Good prompts:

- `List datasets`
- `Query complete_mep_database_topics where jurisdiction equals France and committee_memberships contains IMCO`
- `List Commission project groups related to AI`
- `Get Commission project group Artificial Intelligence`

## Best Query Patterns

The server performs best when your query includes:

- a clear issue or topic
- an audience when relevant, such as `journalists`
- a country when national routing matters
- a route intent, if you know it, such as `support`, `complaint`, `press`, `regulator`, or `committee`

Better:

- `journalist support surveillance Germany`
- `women's rights Czech Republic`
- `platform suspension DSA Poland`
- `climate policy Commissioner`

Worse:

- `help`
- `digital`
- `committee`
- `who should I contact`

## How To Read `find_contacts` Results

The search response now includes confidence and scope signals.

Important fields:

- `confidence_band`
  - `high`: strong result set
  - `medium`: useful but mixed
  - `low`: weak relevance, refine the query
  - `out_of_scope`: the toolkit should not answer this query directly
- `suggested_action`
  - `use_results`
  - `refine_query`
  - `suggest_external_resource`
  - `out_of_scope`
- `scope_message`
  - plain-language explanation when the query is outside the toolkit’s remit
- `ranking_warning`
  - warns when the result set is too clustered or too one-dimensional
- `country_matches_found` and `audience_matches_found`
  - help explain whether the server actually found exact country or audience routes

## Example: Good High-Confidence Query

Prompt:

`Find contacts for journalism support and surveillance in Germany`

Expected pattern:

- operational support routes near the top
- press-freedom and journalist-safety organisations
- digital-security or surveillance-rights support routes
- then, secondarily, relevant MEP or institutional contacts

## Example: Out-Of-Scope Query

Prompt:

`Should I buy these shares?`

Expected pattern:

- `confidence_band: out_of_scope`
- `suggested_action: out_of_scope`
- zero shown matches
- a `scope_message` explaining that the toolkit does not provide financial advice

## When To Use Bundles Instead Of Search

Use `get_bundle` when you want a curated set of contacts with reasons, rather than a mixed ranked list.

Examples:

- `Get the privacy_data_protection bundle`
- `Get the journalist_safety bundle`
- `Get the surveillance_state_power bundle`

Bundles are often the best first stop because they include `why_this_route`, not just contact details.

## When To Use Template Selection Instead Of Guessing

Use `list_templates_by_use_case` when you know the rough action you need, but want the sanctioned template options.

Examples:

- `List templates for eu_document_request`
- `List templates for committee process pressure`
- `List templates for GDPR media story`

Use `recommend_template` when you have a real situation, not just a known use-case key.

Examples:

- `Recommend a template for following up after my DPA ignored a GDPR complaint`
- `Recommend a template for asking a journalist to look at GDPR under-enforcement in Ireland`
- `Recommend a template for raising a procedural concern with an MEP about a live EU file`

The selector layer is driven by two repo datasets:

- [template-registry.csv](/Users/kevinbrown/EU-Citizen-Engagement-Toolkit/data/template-selector/template-registry.csv)
- [template-selector.csv](/Users/kevinbrown/EU-Citizen-Engagement-Toolkit/data/template-selector/template-selector.csv)

The recommendation response includes:

- the matched use case
- the primary template
- any fallback template
- source paths and metadata such as scope, stage, tone, and `not_for`

## Campaign Decision Workflow

Use the campaign decision tools when you need to decide what to do next, not just which file to open.

Examples:

- `List campaign stages for gdpr_complaints`
- `Assess campaign stage for gdpr_complaints with controller_contacted=true and dpa_complaint_filed=true`
- `Recommend next step for gdpr_complaints with controller_contacted=true, dpa_complaint_filed=true, regulator_silent=true`
- `Recommend escalation for gdpr_complaints with regulator_silent=true, need_public_pressure=true, want_media_route=true`

These tools are currently backed by:

- [gdpr-campaign-stages.csv](/Users/kevinbrown/EU-Citizen-Engagement-Toolkit/data/campaign-selector/gdpr-campaign-stages.csv)
- [gdpr-next-step-rules.csv](/Users/kevinbrown/EU-Citizen-Engagement-Toolkit/data/campaign-selector/gdpr-next-step-rules.csv)

The pattern is:

1. assess the stage
2. inspect the recommended next step
3. escalate only when the rule layer says the chronology is ready

## Drafting Workflow

Recommended flow:

1. use `route_issue` or `get_bundle`
2. read the relevant playbook
3. choose a template
4. call `build_draft_packet`
5. let the AI client draft the final text

Important:

- `build_draft_packet` gives context, not a finished filing
- if the packet warns about scope or jurisdiction, treat that seriously

## Known Limits

- The server is scoped to the repository’s civic, institutional, and public-interest data
- it can still surface mixed result sets for broad or ambiguous queries
- some orgs may appear via both direct contacts and bundle rows
- it is not a substitute for legal, medical, or financial professional advice

## Safe Usage Rule

If `confidence_band` is `low` or `out_of_scope`, do not present the result list as a definitive answer. Refine the query, switch to a bundle, or route the user to a clearly external resource class instead.
