/**
 * Client-side graph model that mirrors the server state.
 * Dispatches events on mutation for reactive UI updates.
 * @module graph-state
 */

const NODE_EVENTS = {
  ADDED: 'node-added',
  UPDATED: 'node-updated',
  REMOVED: 'node-removed',
};

const EDGE_EVENTS = {
  ADDED: 'edge-added',
};

/**
 * Reactive graph state container.
 * Stores nodes and edges, dispatches DOM-style events on changes.
 */
export class GraphState extends EventTarget {
  /** @type {Map<string, {id: string, type: string, label: string, stageId: number, position: {x: number, y: number, z: number}, status: string, mesh: object|null}>} */
  _nodes = new Map();

  /** @type {Map<string, {id: string, source: string, target: string, type: string, weight: number, animated: boolean, line: object|null}>} */
  _edges = new Map();

  /**
   * Add a node to the graph.
   * @param {{id: string, type: string, label: string, stageId?: number, position?: {x: number, y: number, z: number}, status?: string}} data
   * @returns {{id: string, type: string, label: string, stageId: number, position: {x: number, y: number, z: number}, status: string, mesh: object|null}}
   */
  addNode(data) {
    const node = {
      id: data.id,
      type: data.type,
      label: data.label,
      stageId: data.stageId ?? -1,
      position: data.position ?? { x: 0, y: 0, z: 0 },
      status: data.status ?? 'idle',
      mesh: null,
    };

    this._nodes.set(node.id, node);
    this._dispatch(NODE_EVENTS.ADDED, { node });
    return node;
  }

  /**
   * Remove a node by id.
   * @param {string} id
   * @returns {boolean} True if the node existed and was removed.
   */
  removeNode(id) {
    const node = this._nodes.get(id);
    if (!node) {
      return false;
    }

    this._nodes.delete(id);
    this._removeEdgesForNode(id);
    this._dispatch(NODE_EVENTS.REMOVED, { node });
    return true;
  }

  /**
   * Partially update a node's properties.
   * @param {string} id
   * @param {object} updates — key/value pairs to merge into the node.
   * @returns {{id: string, type: string, label: string, stageId: number, position: {x: number, y: number, z: number}, status: string, mesh: object|null}|null}
   */
  updateNode(id, updates) {
    const node = this._nodes.get(id);
    if (!node) {
      return null;
    }

    Object.assign(node, updates);
    this._dispatch(NODE_EVENTS.UPDATED, { node, updates });
    return node;
  }

  /**
   * Add an edge to the graph.
   * @param {{id: string, source: string, target: string, type: string, weight?: number, animated?: boolean}} data
   * @returns {{id: string, source: string, target: string, type: string, weight: number, animated: boolean, line: object|null}}
   */
  addEdge(data) {
    const edge = {
      id: data.id,
      source: data.source,
      target: data.target,
      type: data.type,
      weight: data.weight ?? 1.0,
      animated: data.animated ?? false,
      line: null,
    };

    this._edges.set(edge.id, edge);
    this._dispatch(EDGE_EVENTS.ADDED, { edge });
    return edge;
  }

  /**
   * Retrieve a node by id.
   * @param {string} id
   * @returns {object|undefined}
   */
  getNode(id) {
    return this._nodes.get(id);
  }

  /**
   * Retrieve an edge by id.
   * @param {string} id
   * @returns {object|undefined}
   */
  getEdge(id) {
    return this._edges.get(id);
  }

  /**
   * Query nodes matching a filter predicate.
   * @param {function} filterFn — receives a node, returns boolean.
   * @returns {Array<object>}
   */
  queryNodes(filterFn) {
    const results = [];
    for (const node of this._nodes.values()) {
      if (filterFn(node)) {
        results.push(node);
      }
    }
    return results;
  }

  /**
   * Return all nodes as an array.
   * @returns {Array<object>}
   */
  getAllNodes() {
    return Array.from(this._nodes.values());
  }

  /**
   * Return all edges as an array.
   * @returns {Array<object>}
   */
  getAllEdges() {
    return Array.from(this._edges.values());
  }

  /**
   * Remove all nodes and edges, resetting to empty state.
   */
  clear() {
    this._nodes.clear();
    this._edges.clear();
  }

  /**
   * Dispatch a typed CustomEvent.
   * @param {string} eventName
   * @param {object} detail
   */
  _dispatch(eventName, detail) {
    this.dispatchEvent(new CustomEvent(eventName, { detail }));
  }

  /**
   * Remove all edges connected to a given node id.
   * @param {string} nodeId
   */
  _removeEdgesForNode(nodeId) {
    for (const [edgeId, edge] of this._edges) {
      if (edge.source === nodeId || edge.target === nodeId) {
        this._edges.delete(edgeId);
      }
    }
  }
}
