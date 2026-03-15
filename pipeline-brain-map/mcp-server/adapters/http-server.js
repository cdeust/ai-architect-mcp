'use strict';

const http = require('node:http');
const fs = require('node:fs');
const nodePath = require('node:path');
const { HttpPort } = require('../ports/http-port');

const CORS_HEADERS = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Methods': 'GET, OPTIONS',
  'Access-Control-Allow-Headers': 'Content-Type',
};

const CONTENT_TYPES = {
  '.html': 'text/html',
  '.css': 'text/css',
  '.js': 'application/javascript',
  '.json': 'application/json',
  '.png': 'image/png',
  '.svg': 'image/svg+xml',
};

const DEFAULT_INDEX = '/index.html';
const API_PREFIX = '/api/';

/**
 * Node.js http-based HttpPort implementation.
 *
 * Serves graph API endpoints and proxies SSE events to
 * connected browser clients. All dependencies injected
 * via constructor.
 */
class HttpServer extends HttpPort {
  /**
   * @param {{ graphPort: import('../ports/graph-port').GraphPort,
   *           eventSourcePort?: import('../ports/event-source-port').EventSourcePort,
   *           staticDir?: string,
   *           tracePath?: string }} deps
   */
  constructor({ graphPort, eventSourcePort, staticDir, tracePath }) {
    super();
    if (!graphPort) {
      throw new Error('HttpServer requires a graphPort');
    }
    this._graphPort = graphPort;
    this._eventSourcePort = eventSourcePort || null;
    this._staticDir = staticDir || null;
    this._tracePath = tracePath || null;
    this._server = null;
    this._port = 0;
    /** @type {Set<import('http').ServerResponse>} */
    this._sseClients = new Set();
    this._eventSubscribed = false;
  }

  /**
   * Start the HTTP server on the specified or ephemeral port.
   *
   * @param {function(Object, Object): void} _handler — unused, routing is internal
   * @returns {Promise<number>} assigned port number
   */
  async serve(_handler) {
    this._server = http.createServer((req, res) => {
      this._route(req, res);
    });

    return new Promise((resolve, reject) => {
      this._server.listen(this._port, () => {
        this._port = this._server.address().port;
        if (this._eventSourcePort) {
          this._subscribeToEvents();
        }
        resolve(this._port);
      });
      this._server.on('error', reject);
    });
  }

  /**
   * Get the port the server is listening on.
   * @returns {number}
   */
  getPort() {
    return this._port;
  }

  /**
   * Route incoming HTTP requests to the appropriate handler.
   * @param {import('http').IncomingMessage} req
   * @param {import('http').ServerResponse} res
   * @private
   */
  _route(req, res) {
    if (req.method === 'OPTIONS') {
      this._sendCors(res);
      return;
    }

    const url = new URL(req.url, `http://localhost:${this._port}`);
    const path = url.pathname;

    if (req.method !== 'GET') {
      this._sendJson(res, 405, { error: 'Method not allowed' });
      return;
    }

    switch (path) {
      case '/api/graph':
        this._handleGraph(res);
        break;
      case '/api/stats':
        this._handleStats(res);
        break;
      case '/api/events':
        this._handleSseClient(res);
        break;
      case '/api/trace':
        this._handleTrace(res);
        break;
      case '/health':
        this._handleHealth(res);
        break;
      default:
        if (this._staticDir && !path.startsWith(API_PREFIX)) {
          this._handleStatic(req, res, path);
        } else {
          this._sendJson(res, 404, { error: `Route not found: ${path}` });
        }
    }
  }

  /** @private Handle GET /api/graph — return the full graph as JSON. */
  _handleGraph(res) {
    this._sendJson(res, 200, this._graphPort.toJSON());
  }

  /** @private Handle GET /api/stats — return graph statistics. */
  _handleStats(res) {
    this._sendJson(res, 200, this._graphPort.getStats());
  }

  /** @private Handle GET /health — return health check response. */
  _handleHealth(res) {
    this._sendJson(res, 200, { status: 'ok' });
  }

  /**
   * Handle GET /api/events — register an SSE client.
   * @param {import('http').ServerResponse} res
   * @private
   */
  _handleSseClient(res) {
    res.writeHead(200, {
      ...CORS_HEADERS,
      'Content-Type': 'text/event-stream',
      'Cache-Control': 'no-cache',
      'Connection': 'keep-alive',
    });

    this._sseClients.add(res);

    res.on('close', () => {
      this._sseClients.delete(res);
    });
  }

  /** @private Handle GET /api/trace — return brain-trace.jsonl as JSON array. */
  _handleTrace(res) {
    if (!this._tracePath) {
      this._sendJson(res, 200, []);
      return;
    }

    let raw;
    try {
      raw = fs.readFileSync(this._tracePath, 'utf-8');
    } catch (_err) {
      this._sendJson(res, 200, []);
      return;
    }

    const entries = raw
      .split('\n')
      .filter((line) => line.trim().length > 0)
      .map((line) => JSON.parse(line));

    this._sendJson(res, 200, entries);
  }

  /** @private Serve a static file from the configured staticDir. */
  _handleStatic(_req, res, urlPath) {
    const servePath = urlPath === '/' ? DEFAULT_INDEX : urlPath;
    const resolved = nodePath.resolve(this._staticDir, `.${servePath}`);
    const normalizedBase = nodePath.resolve(this._staticDir);

    if (!resolved.startsWith(normalizedBase + nodePath.sep) && resolved !== normalizedBase) {
      this._sendJson(res, 403, { error: 'Forbidden — path traversal detected' });
      return;
    }

    let data;
    try {
      data = fs.readFileSync(resolved);
    } catch (_err) {
      this._sendJson(res, 404, { error: `File not found: ${servePath}` });
      return;
    }

    const ext = nodePath.extname(resolved).toLowerCase();
    const contentType = CONTENT_TYPES[ext] || 'application/octet-stream';

    res.writeHead(200, { ...CORS_HEADERS, 'Content-Type': contentType });
    res.end(data);
  }

  /** @private Subscribe to the event source and broadcast to SSE clients. */
  _subscribeToEvents() {
    if (this._eventSubscribed) return;
    this._eventSubscribed = true;

    this._eventSourcePort.subscribe((event) => {
      this._broadcastEvent(event);
    });
  }

  /** @private Send an event to all connected SSE clients. */
  _broadcastEvent(event) {
    const data = `data: ${JSON.stringify(event)}\n\n`;

    for (const client of this._sseClients) {
      if (!client.writableEnded) {
        client.write(data);
      }
    }
  }

  /** @private Send a CORS-only response for preflight requests. */
  _sendCors(res) {
    res.writeHead(204, CORS_HEADERS);
    res.end();
  }

  /** @private Send a JSON response with CORS headers. */
  _sendJson(res, statusCode, body) {
    res.writeHead(statusCode, {
      ...CORS_HEADERS,
      'Content-Type': 'application/json',
    });
    res.end(JSON.stringify(body));
  }

  /** Close the server, disconnect all SSE clients, and release resources. */
  async close() {
    for (const client of this._sseClients) {
      if (!client.writableEnded) {
        client.end();
      }
    }
    this._sseClients.clear();

    if (this._server) {
      return new Promise((resolve) => {
        this._server.close(() => resolve());
      });
    }
  }
}

module.exports = { HttpServer };
