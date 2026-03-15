#!/usr/bin/env node

/**
 * Pipeline Brain-Map MCP server entry point.
 *
 * Creates the composition root, wires all dependencies,
 * and starts the JSON-RPC server on stdio.
 */

const { CompositionRoot } = require('./composition-root');

function main() {
  const config = {
    traceDir: process.env.BRAIN_MAP_TRACE_DIR || undefined,
    sseUrl: process.env.BRAIN_MAP_SSE_URL || undefined,
    mode: process.env.BRAIN_MAP_MODE || 'replay',
  };

  const root = new CompositionRoot(config);
  const server = root.createMcpServer();
  server.start();
}

main();
