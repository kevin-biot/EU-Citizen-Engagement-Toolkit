# ADR-0002: Structured tools over generic filesystem exposure

## Status

Accepted

## Context

A generic filesystem MCP would make the repo technically accessible, but it would push complexity onto the client model and make routing behavior inconsistent.

## Decision

Expose task-shaped tools such as:

- `find_contacts`
- `route_issue`
- `get_bundle`
- `query_dataset`
- `build_draft_packet`

instead of exposing the repository as a raw browsing interface.

## Consequences

Positive:

- less prompt burden on clients
- safer and more repeatable routing behavior
- easier to encode editorial judgment like `why_this_route`

Negative:

- every major new workflow needs an intentional tool or data-model extension
- tool design becomes part of the project’s public interface

## Follow-on Rule

Add a new MCP tool only when it represents a stable user workflow that would otherwise require fragile inference from raw files.
