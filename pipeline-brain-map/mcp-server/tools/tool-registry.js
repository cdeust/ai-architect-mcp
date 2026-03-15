/**
 * Tool registry — registers and dispatches MCP tools.
 *
 * Central registry for all 8 graph engine tools. Dispatches tool
 * calls by name and provides capability listing for MCP negotiation.
 */

const TOOL_PREFIX = 'brain_map_';

class ToolRegistry {
  /**
   * @param {Object} deps — injected dependencies
   * @param {import('../ports/graph-port').GraphPort} deps.graphPort
   * @param {import('../ports/event-source-port').EventSourcePort} deps.eventSourcePort
   */
  constructor(deps) {
    this._tools = new Map();
    this._deps = deps;
  }

  /**
   * Register a tool with its handler.
   *
   * @param {string} name — tool name (without prefix)
   * @param {Object} schema — JSON Schema for input parameters
   * @param {string} description — human-readable description
   * @param {function(Object): Promise<Object>} handler — async handler function
   */
  register(name, schema, description, handler) {
    this._tools.set(TOOL_PREFIX + name, {
      name: TOOL_PREFIX + name,
      description,
      inputSchema: schema,
      handler,
    });
  }

  /**
   * Dispatch a tool call by name.
   *
   * @param {string} toolName — full tool name with prefix
   * @param {Object} args — tool arguments
   * @returns {Promise<Object>} tool result
   * @throws {Error} if tool not found
   */
  async dispatch(toolName, args) {
    const tool = this._tools.get(toolName);
    if (!tool) {
      const available = Array.from(this._tools.keys()).join(', ');
      throw new Error(
        `Tool '${toolName}' not found — available: ${available}`
      );
    }
    return tool.handler(args);
  }

  /**
   * List all registered tools for MCP capability negotiation.
   *
   * @returns {Array<{ name: string, description: string, inputSchema: Object }>}
   */
  listTools() {
    const tools = [];
    for (const tool of this._tools.values()) {
      tools.push({
        name: tool.name,
        description: tool.description,
        inputSchema: tool.inputSchema,
      });
    }
    return tools;
  }

  /**
   * Check if a tool is registered.
   *
   * @param {string} toolName
   * @returns {boolean}
   */
  hasTool(toolName) {
    return this._tools.has(toolName);
  }

  /**
   * Get the number of registered tools.
   * @returns {number}
   */
  get size() {
    return this._tools.size;
  }
}

module.exports = { ToolRegistry, TOOL_PREFIX };
