# Contributing Guidelines

Thank you for helping build the EU Citizen Engagement Toolkit. Contributions of templates, documentation, data improvements, and automation are welcome.

## How to contribute
1. **Discuss first**: Open an issue to propose new templates, data additions, or process changes.
2. **Fork or branch**: Create a branch for your change.
3. **Match structure**: Place new content in the appropriate `templates/`, `data/`, `docs/`, or `examples/` folder. Include a README in new directories to explain intent and usage.
4. **Document decisions**: Add context on assumptions, intended audiences, and any required tools.
5. **Submit a pull request**: Reference related issues and describe testing or validation you performed.

## Style expectations
- Keep templates clear, versioned, and reusable; prefer Markdown.
- For datasets, include source and freshness notes; avoid personal data unless explicitly allowed.
- Keep automation scripts small, documented, and idempotent.
- Follow the Code of Conduct in all interactions.

## MCP changes

If your change touches `mcp-server/` or the MCP-facing selector and corpus data, run the local MCP quality gate before pushing:

```bash
cd /Users/kevinbrown/EU-Citizen-Engagement-Toolkit
./scripts/check-mcp.sh
```

This avoids relying on hosted CI and keeps the local MCP server, the corpus runner, and the documented tool surface in sync.

Optional local git-hook setup is documented in [/.githooks/README.md](/Users/kevinbrown/EU-Citizen-Engagement-Toolkit/.githooks/README.md).

## Review process
Maintainers review for clarity, completeness, licensing alignment, and fit with the framework levels. Expect feedback; collaborative iteration is encouraged.
