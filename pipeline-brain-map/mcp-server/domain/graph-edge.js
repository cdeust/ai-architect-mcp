'use strict';

const VALID_EDGE_TYPES = new Set([
  'data_flow', 'triggers', 'contains', 'depends_on', 'cross_reference',
]);

class GraphEdge {
  /**
   * @param {string} id
   * @param {string} source - Source node id
   * @param {string} target - Target node id
   * @param {string} type
   * @param {number} weight
   * @param {boolean} animated
   */
  constructor(id, source, target, type = 'data_flow', weight = 1.0, animated = false) {
    if (!id) throw new Error('GraphEdge requires a non-empty id');
    if (!source) throw new Error('GraphEdge requires a non-empty source');
    if (!target) throw new Error('GraphEdge requires a non-empty target');
    if (!VALID_EDGE_TYPES.has(type)) {
      throw new Error(`Invalid edge type '${type}'. Must be one of: ${[...VALID_EDGE_TYPES].join(', ')}`);
    }

    this.id = id;
    this.source = source;
    this.target = target;
    this.type = type;
    this.weight = weight;
    this.animated = animated;
  }

  /**
   * Serialize the edge to a plain object.
   * @returns {object}
   */
  toJSON() {
    return {
      id: this.id,
      source: this.source,
      target: this.target,
      type: this.type,
      weight: this.weight,
      animated: this.animated,
    };
  }
}

module.exports = { GraphEdge, VALID_EDGE_TYPES };
