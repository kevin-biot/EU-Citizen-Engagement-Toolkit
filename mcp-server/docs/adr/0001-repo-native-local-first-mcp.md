# ADR-0001: Repo-native, local-first MCP server

## Status

Accepted

## Context

The repository contains useful civic materials, but users and AI clients need structured access to playbooks, templates, contacts, and datasets without exposing the full repository as a raw file browser.

## Decision

Build the MCP server as a repo-native, local-first package that resolves content from the local checkout and returns local provenance paths.

## Consequences

Positive:

- grounded answers from local curated material
- predictable provenance
- privacy-friendly local usage
- easier reuse across MCP clients

Negative:

- the server is tightly coupled to the repository structure
- source moves require catalog updates

## Follow-on Rule

New features should keep local curated content as the primary source of truth unless there is a very strong reason to introduce a remote dependency.
