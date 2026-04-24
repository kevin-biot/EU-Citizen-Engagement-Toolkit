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
- `list_datasets`
- `list_bundles`

Pattern:

- `ok: true`
- collection payload
- lightweight metadata only

### Get-style tools

Examples:

- `get_playbook`
- `get_template`
- `get_dataset`
- `get_bundle`

Pattern:

- `ok: true`
- a single named payload object
- source path or related metadata when relevant

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
