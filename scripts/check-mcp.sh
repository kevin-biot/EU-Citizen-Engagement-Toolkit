#!/usr/bin/env bash

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MCP_DIR="$REPO_ROOT/mcp-server"

echo "[check-mcp] repo: $REPO_ROOT"
echo "[check-mcp] running MCP quality gate"

cd "$MCP_DIR"

echo "[check-mcp] npm run build"
npm run build

echo "[check-mcp] npm run check"
npm run check

echo "[check-mcp] npm run test:corpus"
npm run test:corpus

echo "[check-mcp] all MCP checks passed"
