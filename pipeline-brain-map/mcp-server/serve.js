#!/usr/bin/env node

/**
 * Standalone visualization server — replays a brain trace and serves the UI.
 *
 * Usage:
 *   node pipeline-brain-map/mcp-server/serve.js [trace-path] [port]
 *
 * Replays the trace into the graph engine, then serves:
 *   - /api/graph   → current graph state
 *   - /api/stats   → graph statistics
 *   - /api/trace   → raw trace events as JSON array
 *   - /api/events  → SSE stream
 *   - /*           → static files from ui/
 */

'use strict';

const path = require('path');
const fs = require('fs');

const { CompositionRoot } = require('./composition-root');
const { HttpServer } = require('./adapters/http-server');
const { applyMutation } = require('./tools/replay-tools');

const DEFAULT_TRACE = path.resolve(__dirname, '..', '..', '.ai-architect', 'brain-trace.jsonl');
const DEFAULT_PORT = 8420;
const UI_DIR = path.resolve(__dirname, '..', 'ui');

function parseArgs() {
  const tracePath = process.argv[2] || DEFAULT_TRACE;
  const port = parseInt(process.argv[3] || DEFAULT_PORT, 10);
  return { tracePath, port };
}

function loadTrace(tracePath) {
  if (!fs.existsSync(tracePath)) {
    console.error(`Trace file not found: ${tracePath}`);
    process.exit(1);
  }
  const content = fs.readFileSync(tracePath, 'utf-8');
  return content.trim().split('\n').filter(l => l.trim());
}

function replayTrace(lines, graph, mapper) {
  let processed = 0;
  let errors = 0;

  for (const line of lines) {
    try {
      const event = JSON.parse(line);
      const mutations = mapper.map(event);
      for (const m of mutations) {
        applyMutation(graph, m);
      }
      processed++;
    } catch {
      errors++;
    }
  }

  return { processed, errors };
}

async function main() {
  const { tracePath, port } = parseArgs();

  console.log(`\n  Pipeline Brain-Map Server`);
  console.log(`  ========================`);
  console.log(`  Trace: ${tracePath}`);

  const lines = loadTrace(tracePath);
  console.log(`  Events: ${lines.length}`);

  const root = new CompositionRoot({ traceDir: path.dirname(tracePath) });
  const graph = root.createGraph();
  const mapper = root.createEventMapper();

  const { processed, errors } = replayTrace(lines, graph, mapper);
  const stats = graph.getStats();
  console.log(`  Replayed: ${processed} events, ${errors} errors`);
  console.log(`  Graph: ${stats.nodeCount} nodes, ${stats.edgeCount} edges`);

  const server = new HttpServer({
    graphPort: graph,
    staticDir: UI_DIR,
    tracePath: tracePath,
  });

  server._port = port;
  await server.serve();

  console.log(`\n  >>> http://localhost:${port}`);
  console.log(`\n  Press Ctrl+C to stop.\n`);
}

main().catch(err => {
  console.error('Fatal:', err.message);
  process.exit(1);
});
