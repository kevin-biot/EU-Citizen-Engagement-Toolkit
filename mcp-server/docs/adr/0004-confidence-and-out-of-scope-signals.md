# ADR-0004: Confidence and out-of-scope signaling in search

## Status

Accepted

## Context

Search systems that always return something can create dangerous false confidence, especially for:

- mixed-intent queries
- vulnerable-user help queries
- clearly out-of-scope queries such as financial advice or medical referral

## Decision

Add explicit search diagnostics and confidence signals to `find_contacts`, including:

- `confidence_band`
- `suggested_action`
- `confidence_reason`
- `scope_message`
- `suppressed_matches`
- ranking and fallback warnings

For out-of-scope queries, suppress weak matches rather than returning plausible-looking garbage.

## Consequences

Positive:

- safer client behavior
- clearer out-of-scope handling
- better user trust when no good answer exists

Negative:

- heuristics must be maintained and tuned
- some borderline queries may be conservatively suppressed

## Follow-on Rule

When adding new ranking logic, consider whether it changes:

- confidence calibration
- out-of-scope detection
- user-safety behavior for ambiguous or high-stakes queries
