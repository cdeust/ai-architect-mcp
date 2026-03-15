'use strict';

const { GraphPort } = require('../ports/graph-port');
const { GraphNode } = require('../domain/graph-node');
const { GraphEdge } = require('../domain/graph-edge');

/**
 * In-memory Map-based GraphPort implementation.
 *
 * Stores nodes and edges in Maps with an adjacency index
 * (nodeId -> Set of edgeIds) for fast edge lookups.
 */
class MemoryGraph extends GraphPort {
  constructor() {
    super();
    /** @type {Map<string, GraphNode>} */
    this._nodes = new Map();
    /** @type {Map<string, GraphEdge>} */
    this._edges = new Map();
    /** @type {Map<string, Set<string>>} */
    this._nodeEdges = new Map();
  }

  /**
   * Add or update a node in the graph.
   * @param {GraphNode} node
   */
  addNode(node) {
    if (!node || !node.id) {
      throw new Error('addNode requires a node with a non-empty id');
    }
    this._nodes.set(node.id, node);
    if (!this._nodeEdges.has(node.id)) {
      this._nodeEdges.set(node.id, new Set());
    }
  }

  /**
   * Remove a node and all edges connected to it.
   * @param {string} nodeId
   * @returns {boolean} true if the node existed
   */
  removeNode(nodeId) {
    if (!this._nodes.has(nodeId)) return false;

    const edgeIds = this._nodeEdges.get(nodeId);
    if (edgeIds) {
      for (const edgeId of edgeIds) {
        this._removeEdgeFromIndex(edgeId, nodeId);
        this._edges.delete(edgeId);
      }
    }
    this._nodeEdges.delete(nodeId);
    this._nodes.delete(nodeId);
    return true;
  }

  /**
   * Remove an edge from the adjacency index of the opposite node.
   * @param {string} edgeId
   * @param {string} excludeNodeId — the node being removed
   * @private
   */
  _removeEdgeFromIndex(edgeId, excludeNodeId) {
    const edge = this._edges.get(edgeId);
    if (!edge) return;

    const otherNodeId = edge.source === excludeNodeId
      ? edge.target
      : edge.source;

    const otherEdges = this._nodeEdges.get(otherNodeId);
    if (otherEdges) {
      otherEdges.delete(edgeId);
    }
  }

  /**
   * Add or update an edge in the graph.
   * @param {GraphEdge} edge
   */
  addEdge(edge) {
    if (!edge || !edge.id) {
      throw new Error('addEdge requires an edge with a non-empty id');
    }
    this._edges.set(edge.id, edge);
    this._indexEdge(edge);
  }

  /**
   * Add edge to the adjacency index for both endpoints.
   * @param {GraphEdge} edge
   * @private
   */
  _indexEdge(edge) {
    if (!this._nodeEdges.has(edge.source)) {
      this._nodeEdges.set(edge.source, new Set());
    }
    this._nodeEdges.get(edge.source).add(edge.id);

    if (!this._nodeEdges.has(edge.target)) {
      this._nodeEdges.set(edge.target, new Set());
    }
    this._nodeEdges.get(edge.target).add(edge.id);
  }

  /**
   * Get a node by ID.
   * @param {string} nodeId
   * @returns {GraphNode|null}
   */
  getNode(nodeId) {
    return this._nodes.get(nodeId) || null;
  }

  /**
   * Get an edge by ID.
   * @param {string} edgeId
   * @returns {GraphEdge|null}
   */
  getEdge(edgeId) {
    return this._edges.get(edgeId) || null;
  }

  /**
   * Query nodes by type, stageId, or status.
   * @param {{ type?: string, stageId?: number, status?: string }} filter
   * @returns {Array<GraphNode>}
   */
  queryNodes(filter) {
    const results = [];
    for (const node of this._nodes.values()) {
      if (this._matchesFilter(node, filter)) {
        results.push(node);
      }
    }
    return results;
  }

  /**
   * Check if a node matches the given filter criteria.
   * @param {GraphNode} node
   * @param {{ type?: string, stageId?: number, status?: string }} filter
   * @returns {boolean}
   * @private
   */
  _matchesFilter(node, filter) {
    if (filter.type !== undefined && node.type !== filter.type) return false;
    if (filter.stageId !== undefined && node.stageId !== filter.stageId) return false;
    if (filter.status !== undefined && node.status !== filter.status) return false;
    return true;
  }

  /**
   * Get all edges connected to a node.
   * @param {string} nodeId
   * @returns {Array<GraphEdge>}
   */
  getEdgesForNode(nodeId) {
    const edgeIds = this._nodeEdges.get(nodeId);
    if (!edgeIds) return [];

    const edges = [];
    for (const edgeId of edgeIds) {
      const edge = this._edges.get(edgeId);
      if (edge) edges.push(edge);
    }
    return edges;
  }

  /**
   * Serialize the full graph to a plain object.
   * @returns {{ nodes: Array<Object>, edges: Array<Object> }}
   */
  toJSON() {
    const nodes = [];
    for (const node of this._nodes.values()) {
      nodes.push(node.toJSON());
    }

    const edges = [];
    for (const edge of this._edges.values()) {
      edges.push(edge.toJSON());
    }

    return { nodes, edges };
  }

  /**
   * Compute graph statistics with breakdowns.
   * @returns {{
   *   nodeCount: number,
   *   edgeCount: number,
   *   stageBreakdown: Object<string, number>,
   *   typeBreakdown: Object<string, number>,
   *   statusBreakdown: Object<string, number>
   * }}
   */
  getStats() {
    const stageBreakdown = {};
    const typeBreakdown = {};
    const statusBreakdown = {};

    for (const node of this._nodes.values()) {
      this._incrementCount(typeBreakdown, node.type);
      this._incrementCount(statusBreakdown, node.status);

      const stageKey = node.stageId != null ? String(node.stageId) : 'none';
      this._incrementCount(stageBreakdown, stageKey);
    }

    return {
      nodeCount: this._nodes.size,
      edgeCount: this._edges.size,
      stageBreakdown,
      typeBreakdown,
      statusBreakdown,
    };
  }

  /**
   * Increment a count in a breakdown object.
   * @param {Object<string, number>} breakdown
   * @param {string} key
   * @private
   */
  _incrementCount(breakdown, key) {
    breakdown[key] = (breakdown[key] || 0) + 1;
  }
}

module.exports = { MemoryGraph };
