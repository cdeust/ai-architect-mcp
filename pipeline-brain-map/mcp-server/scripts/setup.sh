#!/usr/bin/env bash
set -euo pipefail

# Pipeline Brain-Map — setup script
# Validates Node.js availability and registers the MCP server.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SERVER_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
PROJECT_ROOT="$(cd "$SERVER_DIR/../.." && pwd)"

echo "Pipeline Brain-Map Setup"
echo "========================"

# Check Node.js
if ! command -v node &> /dev/null; then
    echo "ERROR: Node.js not found. Install Node.js 18+ to use Brain-Map."
    exit 1
fi

NODE_VERSION=$(node --version | sed 's/v//')
echo "Node.js: v${NODE_VERSION}"

# Verify entry point exists
if [ ! -f "$SERVER_DIR/index.js" ]; then
    echo "ERROR: index.js not found in $SERVER_DIR"
    exit 1
fi

# Verify it loads without error
node -e "require('$SERVER_DIR/composition-root')" 2>/dev/null && \
    echo "Module load: OK" || \
    echo "WARNING: Module load failed — check dependencies"

echo ""
echo "Setup complete. To start the MCP server:"
echo "  node $SERVER_DIR/index.js"
echo ""
echo "Or add to .mcp.json:"
echo "  See $SERVER_DIR/.mcp.json for configuration"
