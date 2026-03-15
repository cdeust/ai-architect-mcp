/**
 * Graph tools — MCP tools for querying and analyzing the pipeline graph.
 *
 * 5 tools: get_graph, get_stats, search_events, get_stage_detail,
 * export_analytics. All read-only.
 */

/**
 * Register graph query tools with the tool registry.
 *
 * @param {import('./tool-registry').ToolRegistry} registry
 * @param {import('../ports/graph-port').GraphPort} graphPort
 */
function registerGraphTools(registry, graphPort) {
  registry.register('get_graph', {
    type: 'object',
    properties: {
      stageId: { type: 'number', description: 'Filter by stage (0-10)' },
      nodeType: { type: 'string', description: 'Filter by node type' },
    },
  }, 'Get the full pipeline graph or filtered subset', async (args) => {
    if (args.stageId !== undefined || args.nodeType !== undefined) {
      const filter = {};
      if (args.stageId !== undefined) filter.stageId = args.stageId;
      if (args.nodeType !== undefined) filter.type = args.nodeType;
      const nodes = graphPort.queryNodes(filter);
      const nodeIds = new Set(nodes.map(n => n.id));
      const edges = [];
      for (const node of nodes) {
        const nodeEdges = graphPort.getEdgesForNode(node.id);
        for (const edge of nodeEdges) {
          if (nodeIds.has(edge.source) && nodeIds.has(edge.target)) {
            edges.push(edge.toJSON());
          }
        }
      }
      return { nodes: nodes.map(n => n.toJSON()), edges };
    }
    return graphPort.toJSON();
  });

  registry.register('get_stats', {
    type: 'object',
    properties: {},
  }, 'Get graph statistics and breakdown by stage/type/status', async () => {
    return graphPort.getStats();
  });

  registry.register('search_events', {
    type: 'object',
    properties: {
      query: { type: 'string', description: 'Search text' },
      type: { type: 'string', description: 'Filter by node type' },
      stageId: { type: 'number', description: 'Filter by stage' },
      status: { type: 'string', description: 'Filter by status' },
    },
    required: ['query'],
  }, 'Search graph nodes by label, type, stage, or status', async (args) => {
    const filter = {};
    if (args.type) filter.type = args.type;
    if (args.stageId !== undefined) filter.stageId = args.stageId;
    if (args.status) filter.status = args.status;

    let nodes = graphPort.queryNodes(filter);

    if (args.query) {
      const q = args.query.toLowerCase();
      nodes = nodes.filter(n =>
        n.label.toLowerCase().includes(q) ||
        n.id.toLowerCase().includes(q)
      );
    }

    return {
      results: nodes.map(n => n.toJSON()),
      count: nodes.length,
    };
  });

  registry.register('get_stage_detail', {
    type: 'object',
    properties: {
      stageId: { type: 'number', description: 'Stage number (0-10)' },
    },
    required: ['stageId'],
  }, 'Get detailed view of a pipeline stage', async (args) => {
    const stageNodes = graphPort.queryNodes({ stageId: args.stageId });
    const stageNode = stageNodes.find(n => n.type === 'stage');
    const tools = stageNodes.filter(n => n.type === 'tool');
    const artifacts = stageNodes.filter(n => n.type === 'artifact');
    const rules = stageNodes.filter(n => n.type === 'hor_rule');
    const gates = stageNodes.filter(n => n.type === 'gate');

    return {
      stage: stageNode ? stageNode.toJSON() : null,
      tools: tools.map(n => n.toJSON()),
      artifacts: artifacts.map(n => n.toJSON()),
      hor_rules: rules.map(n => n.toJSON()),
      gates: gates.map(n => n.toJSON()),
      total_nodes: stageNodes.length,
    };
  });

  registry.register('export_analytics', {
    type: 'object',
    properties: {
      format: {
        type: 'string',
        enum: ['summary', 'detailed'],
        description: 'Export format',
      },
    },
  }, 'Export pipeline analytics data', async (args) => {
    const stats = graphPort.getStats();
    const format = args.format || 'summary';

    if (format === 'summary') {
      return {
        format: 'summary',
        ...stats,
      };
    }

    const graph = graphPort.toJSON();
    return {
      format: 'detailed',
      stats,
      graph,
    };
  });
}

module.exports = { registerGraphTools };
