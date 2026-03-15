/**
 * Composition root — factory wiring for the graph engine.
 *
 * The ONE place where concrete types are instantiated. All other
 * code depends only on port interfaces, never on concrete adapters.
 */

const path = require('path');

const { MemoryGraph } = require('./adapters/memory-graph');
const { JsonlEventSource } = require('./adapters/jsonl-event-source');
const { SseEventSource } = require('./adapters/sse-event-source');
const { HttpServer } = require('./adapters/http-server');

const { EventMapper } = require('./domain/event-mapper');
const { LayoutEngine } = require('./domain/layout-engine');

const { ToolRegistry } = require('./tools/tool-registry');
const { registerGraphTools } = require('./tools/graph-tools');
const { registerReplayTools } = require('./tools/replay-tools');

const { JsonRpcServer } = require('./mcp/json-rpc-server');

const DEFAULT_TRACE_DIR = path.resolve(__dirname, '..', '..', '.ai-architect');
const DEFAULT_TRACE_FILE = 'brain-trace.jsonl';

class CompositionRoot {
  /**
   * @param {Object} config
   * @param {string} [config.traceDir] — directory for trace files
   * @param {string} [config.sseUrl] — SSE endpoint for live mode
   * @param {string} [config.mode] — 'live' or 'replay'
   */
  constructor(config = {}) {
    this._config = config;
    this._traceDir = config.traceDir || DEFAULT_TRACE_DIR;
    this._mode = config.mode || 'replay';
    this._sseUrl = config.sseUrl || null;
  }

  /**
   * Create the in-memory graph store.
   * @returns {MemoryGraph}
   */
  createGraph() {
    return new MemoryGraph();
  }

  /**
   * Create the event source based on mode.
   * @returns {import('./ports/event-source-port').EventSourcePort}
   */
  createEventSource() {
    if (this._mode === 'live' && this._sseUrl) {
      return new SseEventSource({ url: this._sseUrl });
    }
    const filePath = path.join(this._traceDir, DEFAULT_TRACE_FILE);
    return new JsonlEventSource({ filePath });
  }

  /**
   * Create the event mapper.
   * @returns {EventMapper}
   */
  createEventMapper() {
    return new EventMapper();
  }

  /**
   * Create the layout engine.
   * @returns {LayoutEngine}
   */
  createLayoutEngine() {
    return new LayoutEngine();
  }

  /**
   * Create the HTTP server.
   * @param {import('./ports/graph-port').GraphPort} graphPort
   * @returns {HttpServer}
   */
  createHttpServer(graphPort) {
    return new HttpServer({ graphPort });
  }

  /**
   * Wire everything and return the tool registry.
   * @returns {{ registry: ToolRegistry, graph: MemoryGraph, mapper: EventMapper }}
   */
  wireAll() {
    const graph = this.createGraph();
    const eventMapper = this.createEventMapper();
    const eventSource = this.createEventSource();

    const registry = new ToolRegistry({
      graphPort: graph,
      eventSourcePort: eventSource,
    });

    registerGraphTools(registry, graph);
    registerReplayTools(registry, graph, eventMapper);

    return { registry, graph, mapper: eventMapper, eventSource };
  }

  /**
   * Create the full MCP server, ready to start.
   * @returns {JsonRpcServer}
   */
  createMcpServer() {
    const { registry } = this.wireAll();
    return new JsonRpcServer(registry);
  }
}

module.exports = { CompositionRoot };
