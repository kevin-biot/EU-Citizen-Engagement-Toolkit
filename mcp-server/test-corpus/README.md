# MCP Test Corpus

Canonical test cases for the repo-native MCP server.

This corpus exists because informal prompting was surfacing real regressions, but those regressions were living only in chat history.

The goal is to preserve:

- important query shapes
- known failure modes
- expected safety behavior
- expected source-class behavior

## Design

The corpus is intentionally assertion-based, not snapshot-based.

It should capture:

- the tool being exercised
- a `family` label for grouped reporting
- a `priority` level
- a `risk_level` classification such as `correctness` or `safety`
- the input payload
- the key expectations that should hold
- the reason the case exists

It should not require:

- exact full output matching
- frozen ranking for every lower-ranked row
- brittle comparisons against all response fields

## Current Files

- [canonical-tool-queries.json](/Users/kevinbrown/EU-Citizen-Engagement-Toolkit/mcp-server/test-corpus/canonical-tool-queries.json:1)

## Case Families

Current starter cases cover:

- Commissioner-by-portfolio discovery
- committee leadership lookup
- country-aware rights routing
- conflicting-intent contact search
- out-of-scope and low-confidence search safety
- curated bundle access
- GDPR campaign-stage assessment
- GDPR next-step and escalation recommendations
- template selector behavior

## Intended Use

Short term:

- manual MCP regression replay
- contributor orientation
- bug reproduction with stable case IDs

Next step:

- add a lightweight runner that can read this corpus and check response assertions automatically

That runner now exists:

```bash
cd /Users/kevinbrown/EU-Citizen-Engagement-Toolkit/mcp-server
npm run test:corpus
```

To run only selected cases, pass case IDs after the script:

```bash
cd /Users/kevinbrown/EU-Citizen-Engagement-Toolkit/mcp-server
npx tsx test-corpus/run-corpus.ts find-contacts-commission-climate campaign-stage-gdpr-regulator-delay
```

The runner now reports:

- total pass/fail
- pass/fail by tool
- pass/fail by family
- failed case ids

## Maintenance Rule

When a real bug is found through user testing, add:

1. a new corpus case
2. the expected safe behavior
3. a short note explaining the regression class

That keeps the test surface tied to real failures rather than imagined ones.
