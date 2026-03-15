'use strict';

const VALID_TYPES = new Set([
  'stage', 'tool', 'artifact', 'hor_rule', 'gate', 'ooda', 'error', 'thinking', 'decision',
]);

const VALID_STATUSES = new Set([
  'active', 'completed', 'failed', 'pending',
]);

class GraphNode {
  /**
   * @param {string} id
   * @param {string} type
   * @param {string} label
   * @param {number|null} stageId
   * @param {{x: number, y: number, z: number}} position
   * @param {string} status
   */
  constructor(id, type, label, stageId = null, position = { x: 0, y: 0, z: 0 }, status = 'pending') {
    if (!id) throw new Error('GraphNode requires a non-empty id');
    if (!VALID_TYPES.has(type)) {
      throw new Error(`Invalid node type '${type}'. Must be one of: ${[...VALID_TYPES].join(', ')}`);
    }
    if (!VALID_STATUSES.has(status)) {
      throw new Error(`Invalid status '${status}'. Must be one of: ${[...VALID_STATUSES].join(', ')}`);
    }

    this.id = id;
    this.type = type;
    this.label = label || id;
    this.stageId = stageId;
    this.position = { x: position.x || 0, y: position.y || 0, z: position.z || 0 };
    this.status = status;
  }

  /**
   * Create a GraphNode from a pipeline event object.
   * @param {object} event
   * @returns {GraphNode}
   */
  static fromEvent(event) {
    const id = event.nodeId || event.id || `${event.type}-${Date.now()}`;
    const nodeType = event.nodeType || 'stage';
    const label = event.label || event.name || id;
    const stageId = event.stageId != null ? event.stageId : null;
    const position = event.position || { x: 0, y: 0, z: 0 };
    const status = event.status || 'pending';

    return new GraphNode(id, nodeType, label, stageId, position, status);
  }

  /**
   * Serialize the node to a plain object.
   * @returns {object}
   */
  toJSON() {
    return {
      id: this.id,
      type: this.type,
      label: this.label,
      stageId: this.stageId,
      position: { ...this.position },
      status: this.status,
    };
  }
}

module.exports = { GraphNode, VALID_TYPES, VALID_STATUSES };
