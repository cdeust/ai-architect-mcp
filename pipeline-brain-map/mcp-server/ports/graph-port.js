/**
 * Port interface for graph storage operations.
 *
 * Implementations store nodes and edges in memory, database, or
 * external service. The domain layer uses this port to build and
 * query the pipeline visualization graph.
 *
 * @interface GraphPort
 */

class GraphPort {
  /**
   * Add or update a node in the graph.
   * @param {import('../domain/graph-node')} node
   */
  addNode(node) {
    throw new Error('GraphPort.addNode() must be implemented');
  }

  /**
   * Remove a node and its connected edges.
   * @param {string} nodeId
   * @returns {boolean} true if the node existed
   */
  removeNode(nodeId) {
    throw new Error('GraphPort.removeNode() must be implemented');
  }

  /**
   * Add or update an edge in the graph.
   * @param {import('../domain/graph-edge')} edge
   */
  addEdge(edge) {
    throw new Error('GraphPort.addEdge() must be implemented');
  }

  /**
   * Get a node by ID.
   * @param {string} nodeId
   * @returns {import('../domain/graph-node')|null}
   */
  getNode(nodeId) {
    throw new Error('GraphPort.getNode() must be implemented');
  }

  /**
   * Get an edge by ID.
   * @param {string} edgeId
   * @returns {import('../domain/graph-edge')|null}
   */
  getEdge(edgeId) {
    throw new Error('GraphPort.getEdge() must be implemented');
  }

  /**
   * Query nodes by type, stage, or status.
   * @param {Object} filter
   * @param {string} [filter.type]
   * @param {number} [filter.stageId]
   * @param {string} [filter.status]
   * @returns {Array<import('../domain/graph-node')>}
   */
  queryNodes(filter) {
    throw new Error('GraphPort.queryNodes() must be implemented');
  }

  /**
   * Get all edges connected to a node.
   * @param {string} nodeId
   * @returns {Array<import('../domain/graph-edge')>}
   */
  getEdgesForNode(nodeId) {
    throw new Error('GraphPort.getEdgesForNode() must be implemented');
  }

  /**
   * Get the full graph as a serializable object.
   * @returns {{ nodes: Array, edges: Array }}
   */
  toJSON() {
    throw new Error('GraphPort.toJSON() must be implemented');
  }

  /**
   * Get graph statistics.
   * @returns {{ nodeCount: number, edgeCount: number, stageBreakdown: Object }}
   */
  getStats() {
    throw new Error('GraphPort.getStats() must be implemented');
  }
}

module.exports = { GraphPort };
