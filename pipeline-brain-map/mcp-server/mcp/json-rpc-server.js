/**
 * JSON-RPC 2.0 server for MCP protocol over stdio.
 *
 * Handles capability negotiation (initialize), tool listing,
 * and tool dispatch via the ToolRegistry.
 */

const readline = require('readline');

const SERVER_NAME = 'pipeline-brain-map';
const SERVER_VERSION = '0.1.0';
const PROTOCOL_VERSION = '2024-11-05';

class JsonRpcServer {
  /**
   * @param {import('../tools/tool-registry').ToolRegistry} toolRegistry
   */
  constructor(toolRegistry) {
    this._registry = toolRegistry;
    this._initialized = false;
    this._rl = null;
  }

  /**
   * Start listening on stdin for JSON-RPC messages.
   */
  start() {
    this._rl = readline.createInterface({
      input: process.stdin,
      output: process.stdout,
      terminal: false,
    });

    let buffer = '';

    process.stdin.on('data', (chunk) => {
      buffer += chunk.toString();
      const lines = buffer.split('\n');
      buffer = lines.pop() || '';

      for (const line of lines) {
        const trimmed = line.trim();
        if (trimmed) {
          this._handleMessage(trimmed);
        }
      }
    });

    process.stdin.on('end', () => {
      process.exit(0);
    });
  }

  /**
   * Parse and dispatch a single JSON-RPC message.
   *
   * @param {string} raw — raw JSON string
   */
  async _handleMessage(raw) {
    let parsed;
    try {
      parsed = JSON.parse(raw);
    } catch {
      this._sendError(null, -32700, 'Parse error');
      return;
    }

    const { id, method, params } = parsed;

    try {
      const result = await this._dispatch(method, params || {});
      if (id !== undefined) {
        this._sendResult(id, result);
      }
    } catch (err) {
      if (id !== undefined) {
        this._sendError(id, -32603, err.message);
      }
    }
  }

  /**
   * Dispatch a method call to the appropriate handler.
   *
   * @param {string} method
   * @param {Object} params
   * @returns {Promise<Object>}
   */
  async _dispatch(method, params) {
    switch (method) {
      case 'initialize':
        return this._handleInitialize(params);
      case 'initialized':
        return {};
      case 'tools/list':
        return this._handleToolsList();
      case 'tools/call':
        return this._handleToolsCall(params);
      default:
        throw new Error(`Unknown method: ${method}`);
    }
  }

  /**
   * Handle MCP initialize request.
   *
   * @param {Object} params
   * @returns {Object} server capabilities
   */
  _handleInitialize(params) {
    this._initialized = true;
    return {
      protocolVersion: PROTOCOL_VERSION,
      capabilities: {
        tools: { listChanged: false },
      },
      serverInfo: {
        name: SERVER_NAME,
        version: SERVER_VERSION,
      },
    };
  }

  /**
   * Handle tools/list request.
   *
   * @returns {Object} tool list
   */
  _handleToolsList() {
    return { tools: this._registry.listTools() };
  }

  /**
   * Handle tools/call request.
   *
   * @param {Object} params — { name, arguments }
   * @returns {Promise<Object>} tool result
   */
  async _handleToolsCall(params) {
    const { name, arguments: args } = params;
    const result = await this._registry.dispatch(name, args || {});
    return {
      content: [{
        type: 'text',
        text: JSON.stringify(result, null, 2),
      }],
    };
  }

  /**
   * Send a JSON-RPC success response.
   *
   * @param {number|string} id
   * @param {Object} result
   */
  _sendResult(id, result) {
    const response = JSON.stringify({
      jsonrpc: '2.0',
      id,
      result,
    });
    process.stdout.write(response + '\n');
  }

  /**
   * Send a JSON-RPC error response.
   *
   * @param {number|string|null} id
   * @param {number} code
   * @param {string} message
   */
  _sendError(id, code, message) {
    const response = JSON.stringify({
      jsonrpc: '2.0',
      id,
      error: { code, message },
    });
    process.stdout.write(response + '\n');
  }
}

module.exports = { JsonRpcServer };
