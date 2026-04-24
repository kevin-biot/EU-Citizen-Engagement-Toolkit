# ADR-0005: Metadata-Driven Template Selection

## Status

Accepted

## Context

The repository now has several distinct template surfaces:

- formal filing templates under `templates/`
- issue-linked citizen email templates under `docs/digital-issues/email-templates/`
- outreach templates under `docs/outreach-email-templates/`
- campaign-specific templates under `campaigns/*/emails/`

This is useful coverage, but it creates a new problem for both humans and MCP clients:

- the right template is harder to choose than it used to be
- filename conventions alone are no longer enough to drive recommendation
- similar templates differ by target, stage, tone, jurisdiction, and evidence threshold
- the current MCP surface can list templates, but it cannot yet explain which one fits a use case best

If this repo is meant to be reused in open-source settings, template selection needs a documented and inspectable structure rather than ad hoc path heuristics.

## Decision

We will use a metadata-driven template-selection layer with two explicit datasets:

1. `template-registry`
- one row per concrete template file
- records stable metadata about the template's family, target, scope, stage, tone, and known limits

2. `template-selector`
- one row per recurring use case
- maps a use case to a primary template and optional fallback template
- explains when to use that mapping and when not to

This layer is data-first.

That means:

- the first implementation lives in repo datasets and Markdown docs
- MCP tooling can consume those datasets later
- contributors can review and extend the selection logic without reading TypeScript first

## Consequences

### Positive

- template recommendation becomes auditable and reusable
- humans and MCP clients can share the same selection logic
- new template families can be added without inventing new hardcoded rules each time
- developers can see schema expectations before implementing recommendation tools

### Negative

- registry maintenance becomes a real part of template work
- adding a new template is no longer complete until its metadata row exists
- some template-selection judgement will still remain editorial rather than automatic

## Rejected Alternatives

### Rely only on path naming

Rejected because path naming does not encode enough:

- `who` the template is for
- `when` in the escalation ladder it fits
- `what` evidence threshold it expects
- `where` it should not be used

### Hardcode recommendation rules only in the MCP server

Rejected because that would make the most important selection logic opaque to repo reusers and non-MCP consumers.

### Generate metadata implicitly from Markdown headings

Rejected for now because the current template files are not yet normalized enough for safe inference.

## Implementation Notes

The first pass should:

- inventory all existing templates into the registry
- define a small but useful selector dataset for recurring use cases
- document the family model in repo docs

Later MCP work can add:

- `list_template_families`
- `recommend_template`
- `list_templates_by_use_case`

Those tools should read the registry and selector datasets rather than duplicating selection logic in code.
