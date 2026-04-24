# EU Citizen Engagement Toolkit MCP Server

Repo-native MCP server for local AI agents such as Claude Desktop, Codex, and other Model Context Protocol clients.

This server is intentionally opinionated. It does not expose a generic filesystem browser. It exposes the toolkit as a structured local knowledge layer:

- digital-issue playbooks
- correspondence and filing templates
- email templates
- contact directories
- authority routing
- issue routing based on the repo's own datasets

## Why This Exists

The toolkit is useful as a repository, but communities still need help finding the right file, the right route, and the right next step.

This MCP server turns the repo into a local assistant surface that can:

- list and retrieve playbooks
- list and retrieve templates
- find relevant contact routes
- return country-level authority data
- suggest likely issue routes from a short problem description
- assemble a drafting packet from a chosen template and user facts

## Current Tools

- `list_playbooks`
- `get_playbook`
- `list_templates`
- `get_template`
- `list_email_templates`
- `get_email_template`
- `list_datasets`
- `get_dataset`
- `query_dataset`
- `list_bundles`
- `get_bundle`
- `list_commission_project_groups`
- `get_commission_project_group`
- `find_contacts`
- `get_authorities`
- `route_issue`
- `build_draft_packet`

`find_contacts` searches across:
- community contact routes
- issue-specific contact bundles
- institutional and Commission-facing contacts
- the topic-tagged MEP contact database

`list_commission_project_groups` exposes the current Commissioners' Project Groups directly, so MCP clients do not have to infer them from dataset samples.

`get_bundle` exposes the curated issue-bundle layer directly, including the `why_this_route` rationale that explains when each contact is the right escalation path.

## Install

```bash
cd mcp-server
npm install
npm run build
```

## Run

```bash
cd mcp-server
npm start
```

## Claude Desktop Example

Adjust the absolute path to match your local checkout.

```json
{
  "mcpServers": {
    "eu-citizen-engagement-toolkit": {
      "command": "node",
      "args": [
        "/Users/kevinbrown/EU-Citizen-Engagement-Toolkit/mcp-server/dist/index.js"
      ]
    }
  }
}
```

## Environment

- `EU_TOOLKIT_ROOT`: optional absolute path override for the repository root. By default the server resolves the repo root relative to the compiled server file.

## Notes

- The server is local-first and read-heavy.
- The drafting helper returns context packets and starter structure. The MCP client model should do the actual prose drafting.
- All returned items include local file paths so users can inspect the original source material directly.
