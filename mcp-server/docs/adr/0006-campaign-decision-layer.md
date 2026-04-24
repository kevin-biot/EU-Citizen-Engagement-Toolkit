# ADR-0006: Data-Driven Campaign Decision Layer

## Status

Accepted

## Context

The toolkit now has strong routing, contact, template, and campaign-source coverage, especially for GDPR complaints.

What it still lacks is a structured way to answer:

- what stage is this campaign in
- what should happen next
- when should the user escalate
- which template or dataset best fits that stage

Without a decision layer, MCP clients can retrieve many useful files but still force users to guess the next move.

## Decision

Introduce a metadata-driven campaign decision layer backed by CSV datasets and exposed through MCP tools.

The first implementation is scoped to `gdpr_complaints`.

The design has two source datasets:

1. `gdpr-campaign-stages.csv`
Describes the stable campaign stages, their entry signals, goals, preferred routes, and exit conditions.

2. `gdpr-next-step-rules.csv`
Describes stage-aware next-step and escalation rules, including:
- required signals
- excluded signals
- recommended next action
- recommended template
- recommended bundle
- recommended dataset
- escalation level

The MCP server should:

- load these datasets into the main catalog
- expose stable tools for stage assessment and next-step recommendation
- keep the code responsible for signal interpretation, not for hardcoding campaign content

## Consequences

### Positive

- campaign guidance becomes inspectable and reusable
- new campaign packs can adopt the same pattern without rewriting MCP logic
- open-source contributors can improve campaign behavior by editing datasets first
- MCP clients can explain why a next step was chosen using source-backed metadata

### Negative

- the first version uses heuristic boolean signals rather than full case-state modeling
- campaign quality depends on keeping the CSV rules disciplined and non-overlapping
- later campaigns may need richer condition fields than the first GDPR pass

## Rejected Alternatives

### Hardcode campaign logic in MCP handlers

Rejected because it hides the reasoning, makes reuse harder, and breaks the repo-first design.

### Use freeform search over campaign markdown

Rejected because it is too ambiguous for step-by-step operator guidance and would reproduce the same selection problems already solved in the template layer.

## Follow-Up

- add `list_campaign_stages`
- add `assess_campaign_stage`
- add `recommend_next_step`
- add `recommend_escalation`
- extend the pattern to future campaigns only after the GDPR version proves stable
