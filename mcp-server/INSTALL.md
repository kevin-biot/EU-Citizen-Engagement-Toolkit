# MCP Server Installation Guide

This guide covers local install, build, client setup, and update workflow for the EU Citizen Engagement Toolkit MCP server.

## Prerequisites

- `node` and `npm` installed locally
- a local checkout of the repository
- an MCP client such as Claude Desktop, Codex, or another stdio-compatible MCP client

Check your local runtime:

```bash
node --version
npm --version
```

## Build The Server

From the repository root:

```bash
cd /Users/kevinbrown/EU-Citizen-Engagement-Toolkit/mcp-server
npm install
npm run build
```

This produces the runnable MCP entrypoint at:

`/Users/kevinbrown/EU-Citizen-Engagement-Toolkit/mcp-server/dist/index.js`

## Run A Local Smoke Test

Start the server directly:

```bash
cd /Users/kevinbrown/EU-Citizen-Engagement-Toolkit/mcp-server
npm start
```

This is a stdio server, so the terminal will usually look quiet. That is normal.

Stop it with `Ctrl+C`.

## Claude Desktop Configuration

Add the server to your Claude Desktop MCP config.

Example full entry:

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

Then restart Claude Desktop fully.

## Optional Repository Override

By default the server resolves the repository root relative to the compiled `dist/index.js` file.

If you need to point the server at a different checkout, set:

- `EU_TOOLKIT_ROOT`

Example:

```json
{
  "mcpServers": {
    "eu-citizen-engagement-toolkit": {
      "command": "node",
      "args": [
        "/Users/kevinbrown/EU-Citizen-Engagement-Toolkit/mcp-server/dist/index.js"
      ],
      "env": {
        "EU_TOOLKIT_ROOT": "/Users/kevinbrown/EU-Citizen-Engagement-Toolkit"
      }
    }
  }
}
```

## Upgrade After Pulling Changes

When the repo changes:

```bash
cd /Users/kevinbrown/EU-Citizen-Engagement-Toolkit/mcp-server
npm install
npm run build
```

Then restart the MCP client.

## Troubleshooting

`Server not found`
- Confirm the absolute `dist/index.js` path in your client config.
- Re-run `npm run build`.

`Client starts but tools are missing`
- Restart the MCP client after rebuilding.
- Check that the client is pointing at the right checkout.

`TypeScript build fails`
- Run:

```bash
cd /Users/kevinbrown/EU-Citizen-Engagement-Toolkit/mcp-server
npm run check
```

- Fix the reported type error before retrying `npm run build`.

`The server answers from the wrong repo`
- Set `EU_TOOLKIT_ROOT` explicitly in the MCP client config.

## Basic Verification Prompts

After connecting the server, try:

- `List the available playbooks from eu-citizen-engagement-toolkit`
- `List the current Commission project groups`
- `Get the privacy_data_protection bundle`
- `Find contacts for journalist support and surveillance in Germany`

For practical usage patterns, see the [User Guide](/Users/kevinbrown/EU-Citizen-Engagement-Toolkit/mcp-server/USER_GUIDE.md).
