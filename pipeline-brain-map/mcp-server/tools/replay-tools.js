/**
 * Replay tools — MCP tools for trace replay and comparison.
 *
 * 3 tools: replay_trace, compare_traces, open_visualization.
 */

const fs = require('fs');
const path = require('path');

/**
 * Register replay-related tools with the tool registry.
 *
 * @param {import('./tool-registry').ToolRegistry} registry
 * @param {import('../ports/graph-port').GraphPort} graphPort
 * @param {import('../domain/event-mapper').EventMapper} eventMapper
 */
function registerReplayTools(registry, graphPort, eventMapper) {
  registry.register('replay_trace', {
    type: 'object',
    properties: {
      filePath: {
        type: 'string',
        description: 'Path to brain-trace.jsonl file',
      },
      speed: {
        type: 'number',
        description: 'Playback speed multiplier (0 = instant)',
        default: 0,
      },
    },
    required: ['filePath'],
  }, 'Replay a pipeline trace from a JSONL file', async (args) => {
    const filePath = args.filePath;

    if (!fs.existsSync(filePath)) {
      throw new Error(`Trace file not found: ${filePath}`);
    }

    const content = fs.readFileSync(filePath, 'utf-8');
    const lines = content.trim().split('\n').filter(l => l.trim());
    let eventCount = 0;
    let errorCount = 0;

    for (const line of lines) {
      try {
        const event = JSON.parse(line);
        const mutations = eventMapper.map(event);
        for (const mutation of mutations) {
          applyMutation(graphPort, mutation);
        }
        eventCount++;
      } catch (err) {
        errorCount++;
      }
    }

    return {
      status: 'completed',
      events_processed: eventCount,
      errors: errorCount,
      graph_stats: graphPort.getStats(),
    };
  });

  registry.register('compare_traces', {
    type: 'object',
    properties: {
      traceA: { type: 'string', description: 'Path to first trace' },
      traceB: { type: 'string', description: 'Path to second trace' },
    },
    required: ['traceA', 'traceB'],
  }, 'Compare two pipeline traces side by side', async (args) => {
    const statsA = loadTraceStats(args.traceA);
    const statsB = loadTraceStats(args.traceB);

    return {
      traceA: { path: args.traceA, ...statsA },
      traceB: { path: args.traceB, ...statsB },
      differences: computeDifferences(statsA, statsB),
    };
  });

  registry.register('open_visualization', {
    type: 'object',
    properties: {
      port: {
        type: 'number',
        description: 'HTTP server port for the UI',
      },
    },
  }, 'Get the URL to open the visualization UI', async (args) => {
    const port = args.port || 0;
    const uiPath = path.resolve(__dirname, '..', '..', 'ui', 'index.html');
    const exists = fs.existsSync(uiPath);

    return {
      ui_path: uiPath,
      ui_available: exists,
      message: exists
        ? `Open ${uiPath} in a browser`
        : 'UI not found — run Phase 3 setup first',
    };
  });
}

/**
 * Apply a single graph mutation.
 *
 * @param {import('../ports/graph-port').GraphPort} graphPort
 * @param {Object} mutation
 */
function applyMutation(graphPort, mutation) {
  switch (mutation.type) {
    case 'addNode':
      graphPort.addNode(mutation.node);
      break;
    case 'addEdge':
      graphPort.addEdge(mutation.edge);
      break;
    case 'updateNode': {
      const existing = graphPort.getNode(mutation.nodeId);
      if (existing) {
        Object.assign(existing, mutation.updates);
        graphPort.addNode(existing);
      }
      break;
    }
  }
}

/**
 * Load basic stats from a trace file.
 *
 * @param {string} filePath
 * @returns {Object} event type counts and total
 */
function loadTraceStats(filePath) {
  if (!fs.existsSync(filePath)) {
    return { total: 0, types: {}, error: 'File not found' };
  }

  const content = fs.readFileSync(filePath, 'utf-8');
  const lines = content.trim().split('\n').filter(l => l.trim());
  const types = {};

  for (const line of lines) {
    try {
      const event = JSON.parse(line);
      const t = event.event_type || 'unknown';
      types[t] = (types[t] || 0) + 1;
    } catch { /* skip invalid lines */ }
  }

  return { total: lines.length, types };
}

/**
 * Compute differences between two trace stat sets.
 *
 * @param {Object} a
 * @param {Object} b
 * @returns {Object}
 */
function computeDifferences(a, b) {
  const allTypes = new Set([
    ...Object.keys(a.types || {}),
    ...Object.keys(b.types || {}),
  ]);

  const diffs = {};
  for (const t of allTypes) {
    const countA = (a.types || {})[t] || 0;
    const countB = (b.types || {})[t] || 0;
    if (countA !== countB) {
      diffs[t] = { traceA: countA, traceB: countB, delta: countB - countA };
    }
  }

  return {
    total_delta: (b.total || 0) - (a.total || 0),
    type_differences: diffs,
  };
}

module.exports = { registerReplayTools, applyMutation };
