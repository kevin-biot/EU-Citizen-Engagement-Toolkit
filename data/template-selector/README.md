# Template Selector Data

Structured selection data for choosing the right template by use case.

This layer exists because the repository now has multiple template families with overlapping subject matter but different:

- targets
- escalation stages
- tones
- jurisdiction assumptions
- evidence thresholds

## Files

- `template-registry.csv`: one row per concrete template file
- `template-registry.md`: human-readable view of the template registry
- `template-selector.csv`: recurring use-case mappings to primary and fallback templates
- `template-selector.md`: human-readable view of the use-case selector

## Intended Use

Use this layer when you need to answer:

- which template should I start from
- which template family covers this situation
- when should I use a fallback template instead
- which templates are not suitable for a particular jurisdiction or escalation stage

## Design Rule

This is a selector layer, not a prose layer.

It should stay:

- explicit
- reviewable
- stable enough for MCP tooling to consume

See [ADR-0005](</Users/kevinbrown/EU-Citizen-Engagement-Toolkit/mcp-server/docs/adr/0005-metadata-driven-template-selection.md>) for the design rationale.
