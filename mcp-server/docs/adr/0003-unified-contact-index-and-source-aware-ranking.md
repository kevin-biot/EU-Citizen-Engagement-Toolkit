# ADR-0003: Unified contact index and source-aware ranking

## Status

Accepted

## Context

The repo contains heterogeneous contact datasets:

- NGOs and media routes
- issue-specific bundles
- institutional routes
- MEP contacts
- Commission contacts

Searching each source separately would make the MCP surface fragmented, but flattening them without provenance would produce unsafe results.

## Decision

Normalize those sources into a shared `ContactRow` index while preserving:

- `__contact_index`
- `__source_path`

Then apply source-aware ranking in `routing.ts`.

## Consequences

Positive:

- one search surface for clients
- still possible to treat MEP, Commission, bundle, and support routes differently
- easier to layer diagnostics and confidence signals

Negative:

- normalization logic is non-trivial
- weak ranking changes can affect many source families at once

## Follow-on Rule

When adding a new contact dataset, document its normalization assumptions and assign a meaningful `__contact_index` value.
