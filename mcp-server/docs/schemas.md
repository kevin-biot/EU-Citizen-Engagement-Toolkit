# MCP Schemas

This document explains the main internal data shapes used by the MCP server.

It is not a generated API reference. It is a developer-oriented map of the stable concepts in the code.

## Core Catalog Types

Defined in [src/catalog.ts](/Users/kevinbrown/EU-Citizen-Engagement-Toolkit/mcp-server/src/catalog.ts:1).

### `RepoItem`

Used for markdown-backed repo content such as playbooks, templates, and email templates.

Fields:

- `slug`
- `title`
- `path`
- `category`
- `summary`
- `body`

### `DatasetSummary`

Used for dataset listing and lightweight inspection.

Fields:

- `slug`
- `title`
- `path`
- `rows`
- `columns`
- `sample`

### `IssueRoute`

Backed by `data/national-authorities/issue-router.csv`.

Fields:

- `issue_key`
- `issue_name`
- `first_route_type`
- `possible_eu_layer`
- `possible_national_layer`
- `evidence_priority`
- `notes`

### `AuthorityRow`

Currently a generic `Record<string, string>` loaded from `national-digital-authorities.csv`.

Important common fields:

- `country_name`
- `country_code`
- `digital_services_coordinator_*`
- `data_protection_authority_*`
- `competition_authority_*`
- related summary routing fields

### `BundleRow`

Backed by `data/community-contacts/issue-specific-contact-bundles.csv`.

Important fields:

- `bundle_slug`
- `bundle_label`
- `organization`
- `org_scope`
- `contact_scope`
- `public_contact`
- `source_url`
- `why_this_route`

### `TemplateRegistryRow`

Backed by `data/template-selector/template-registry.csv`.

Important fields:

- `template_slug`
- `title`
- `template_family`
- `template_kind`
- `primary_target`
- `jurisdiction_scope`
- `stage`
- `tone`
- `requires_evidence`
- `best_when`
- `not_for`
- `source_path`

### `TemplateSelectorRow`

Backed by `data/template-selector/template-selector.csv`.

Important fields:

- `use_case_key`
- `use_case_label`
- `primary_template_slug`
- `fallback_template_slug`
- `jurisdiction_scope`
- `selector_note`
- `not_for`

### `CampaignStageRow`

Backed by `data/campaign-selector/gdpr-campaign-stages.csv`.

Important fields:

- `campaign_slug`
- `stage_key`
- `stage_label`
- `description`
- `entry_signals`
- `primary_goal`
- `preferred_templates`
- `preferred_routes`
- `exit_signal`
- `not_for`

### `CampaignRuleRow`

Backed by `data/campaign-selector/gdpr-next-step-rules.csv`.

Important fields:

- `campaign_slug`
- `rule_key`
- `stage_key`
- `required_signals`
- `excluded_signals`
- `recommended_next_step`
- `recommended_template_slug`
- `recommended_bundle_slug`
- `recommended_dataset_slug`
- `recommended_contact_type`
- `recommended_stage_after`
- `escalation_level`
- `note`

### `ContactRow`

`ContactRow` is the shared search surface.

It is built by normalizing many heterogeneous CSVs into a flat cross-source structure.

Common fields that frequently appear:

- `organization`
- `public_contact`
- `public_contact_type`
- `public_page`
- `country`
- `jurisdiction`
- `audience`
- `focus`
- `notes`
- `role_tags`
- `committee_memberships`
- `__source_path`
- `__contact_index`

## Contact Index Values

`__contact_index` is important because ranking logic uses it for source-aware behavior.

Current values include:

- `general`
- `womens_member_network`
- `national_equality_body`
- `issue_bundle`
- `institutional_route`
- `mep_political`
- `commission_college`
- `commission_cabinet`
- `commission_dg_press`
- `commission_spp`

## MCP Tool Response Patterns

### List-style tools

Examples:

- `list_playbooks`
- `list_templates`
- `list_templates_by_use_case`
- `list_datasets`
- `list_bundles`
- `list_campaign_stages`

Pattern:

- `ok: true`
- collection payload
- lightweight metadata only

### Get-style tools

Examples:

- `get_playbook`
- `get_template`
- `recommend_template`
- `get_dataset`
- `get_bundle`
- `assess_campaign_stage`
- `recommend_next_step`
- `recommend_escalation`

Pattern:

- `ok: true`
- a single named payload object
- source path or related metadata when relevant

### Selector-style tools

Examples:

- `list_templates_by_use_case`
- `recommend_template`

Pattern:

- `ok: true`
- query echo when relevant
- resolved template metadata from the registry
- primary template plus optional fallback or alternatives
- local source paths for provenance

### Campaign decision tools

Examples:

- `list_campaign_stages`
- `assess_campaign_stage`
- `recommend_next_step`
- `recommend_escalation`

Pattern:

- `ok: true`
- explicit boolean signal echo
- assessed stage with reasons
- rule-backed recommendations with template, bundle, and dataset references where available

### Search / routing tools

Examples:

- `find_contacts`
- `route_issue`
- `get_authorities`

Pattern:

- `ok: true`
- query echo
- result collection
- diagnostics or confidence metadata

## `find_contacts` Diagnostic Fields

The search layer now returns explicit diagnostics for safer client behavior.

Important fields:

- `country_filter_mode`
- `audience_filter_mode`
- `country_matches_found`
- `country_matches_total`
- `audience_matches_found`
- `audience_matches_total`
- `scoped_committee_role_matches_total`
- `result_index_diversity`
- `fallback_strategy`
- `audience_fallback_strategy`
- `search_warning`
- `ranking_warning`
- `confidence_band`
- `suggested_action`
- `confidence_reason`
- `scope_message`
- `suppressed_matches`

## Confidence Model

`confidence_band` currently uses four levels:

- `high`
- `medium`
- `low`
- `out_of_scope`

These are heuristic outputs from `routing.ts`, not statistical probabilities.

They exist so MCP clients can avoid presenting weak or dangerous matches as authoritative answers.

## Schema Stability Guidance

For reuse and extension:

- prefer adding new optional fields over renaming existing response fields
- keep diagnostic fields explicit rather than burying them in prose
- preserve `__source_path` for provenance
- preserve `__contact_index` for source-aware ranking and downstream filtering
