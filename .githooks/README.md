# Local Git Hooks

Optional local hooks for this repository.

These hooks are not enabled automatically.

If you want to use them:

```bash
cd /Users/kevinbrown/EU-Citizen-Engagement-Toolkit
git config core.hooksPath .githooks
chmod +x .githooks/pre-push scripts/check-mcp.sh
```

To stop using them:

```bash
cd /Users/kevinbrown/EU-Citizen-Engagement-Toolkit
git config --unset core.hooksPath
```

## Current Hooks

- `pre-push`: runs the local MCP quality gate before pushes
