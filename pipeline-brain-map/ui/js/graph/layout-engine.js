/**
 * Client-side force-directed layout engine.
 * Computes 3D positions for graph nodes using gravity wells,
 * repulsion, and spring forces. Can also apply server-provided positions.
 * @module layout-engine
 */

import { Vector3 } from 'three';

const STAGE_COUNT = 11;
const ARC_RADIUS = 400;
const REPULSION_STRENGTH = 5000;
const SPRING_STRENGTH = 0.005;
const SPRING_REST_LENGTH = 60;
const GRAVITY_STRENGTH = 0.02;
const DAMPING = 0.85;
const MIN_DISTANCE = 1;
const MAX_VELOCITY = 50;
const CONVERGENCE_THRESHOLD = 0.1;

/**
 * Compute the 3D gravity well position for a pipeline stage index.
 * Stages are arranged on a semicircular arc in the XZ plane.
 *
 * @param {number} stageId — stage index (0-10).
 * @returns {Vector3}
 */
function computeGravityWell(stageId) {
  const clampedId = Math.max(0, Math.min(stageId, STAGE_COUNT - 1));
  const angle = (Math.PI * clampedId) / (STAGE_COUNT - 1);

  return new Vector3(
    ARC_RADIUS * Math.cos(angle),
    0,
    ARC_RADIUS * Math.sin(angle),
  );
}

/**
 * Precompute all 11 gravity well positions.
 * @returns {Vector3[]}
 */
function buildGravityWells() {
  const wells = [];
  for (let i = 0; i < STAGE_COUNT; i++) {
    wells.push(computeGravityWell(i));
  }
  return wells;
}

/**
 * Internal node representation for the physics simulation.
 * @typedef {{
 *   id: string,
 *   stageId: number,
 *   position: Vector3,
 *   velocity: Vector3,
 *   force: Vector3,
 * }} LayoutNode
 */

/**
 * Internal edge representation.
 * @typedef {{source: string, target: string}} LayoutEdge
 */

/**
 * Force-directed layout engine operating on Three.js Vector3.
 */
export class LayoutEngine {
  /** @type {Map<string, LayoutNode>} */
  _nodes = new Map();

  /** @type {LayoutEdge[]} */
  _edges = [];

  /** @type {Vector3[]} */
  _gravityWells = buildGravityWells();

  /** @type {boolean} */
  _converged = false;

  /**
   * Add a node to the layout simulation.
   * Initial position is near the gravity well for the node's stage.
   *
   * @param {string} id — unique node id.
   * @param {number} stageId — pipeline stage index (0-10), or -1 for unassigned.
   */
  addNode(id, stageId) {
    const wellIndex = Math.max(0, Math.min(stageId, STAGE_COUNT - 1));
    const well = stageId >= 0
      ? this._gravityWells[wellIndex]
      : new Vector3(0, 0, 0);

    const jitter = new Vector3(
      (Math.random() - 0.5) * 40,
      (Math.random() - 0.5) * 40,
      (Math.random() - 0.5) * 40,
    );

    this._nodes.set(id, {
      id,
      stageId,
      position: well.clone().add(jitter),
      velocity: new Vector3(0, 0, 0),
      force: new Vector3(0, 0, 0),
    });

    this._converged = false;
  }

  /**
   * Remove a node from the simulation.
   * @param {string} id
   */
  removeNode(id) {
    this._nodes.delete(id);
    this._edges = this._edges.filter(
      (e) => e.source !== id && e.target !== id,
    );
    this._converged = false;
  }

  /**
   * Add an edge (spring constraint) between two nodes.
   * @param {string} source — source node id.
   * @param {string} target — target node id.
   */
  addEdge(source, target) {
    this._edges.push({ source, target });
    this._converged = false;
  }

  /**
   * Get the current position of a node.
   * @param {string} id
   * @returns {Vector3|null}
   */
  getPosition(id) {
    const node = this._nodes.get(id);
    return node ? node.position.clone() : null;
  }

  /**
   * Apply server-provided positions, bypassing the simulation.
   * @param {Array<{id: string, x: number, y: number, z: number}>} positions
   */
  applyServerPositions(positions) {
    for (const pos of positions) {
      const node = this._nodes.get(pos.id);
      if (node) {
        node.position.set(pos.x, pos.y, pos.z);
        node.velocity.set(0, 0, 0);
      }
    }
    this._converged = true;
  }

  /**
   * Run one simulation tick.
   * @param {number} deltaTime — seconds since last tick.
   * @returns {boolean} True if the layout has converged.
   */
  tick(deltaTime) {
    if (this._converged) {
      return true;
    }

    this._resetForces();
    this._applyRepulsion();
    this._applySprings();
    this._applyGravity();
    this._integrate(deltaTime);

    return this._checkConvergence();
  }

  /**
   * Zero out all force accumulators.
   */
  _resetForces() {
    for (const node of this._nodes.values()) {
      node.force.set(0, 0, 0);
    }
  }

  /**
   * Apply repulsive forces between all node pairs.
   */
  _applyRepulsion() {
    const nodes = Array.from(this._nodes.values());
    const count = nodes.length;
    const delta = new Vector3();

    for (let i = 0; i < count; i++) {
      for (let j = i + 1; j < count; j++) {
        this._repelPair(nodes[i], nodes[j], delta);
      }
    }
  }

  /**
   * Apply repulsive force between two nodes.
   * @param {LayoutNode} a
   * @param {LayoutNode} b
   * @param {Vector3} delta — reusable scratch vector.
   */
  _repelPair(a, b, delta) {
    delta.subVectors(a.position, b.position);
    const distSq = Math.max(delta.lengthSq(), MIN_DISTANCE);
    const magnitude = REPULSION_STRENGTH / distSq;

    delta.normalize().multiplyScalar(magnitude);
    a.force.add(delta);
    b.force.sub(delta);
  }

  /**
   * Apply spring (attraction) forces along edges.
   */
  _applySprings() {
    const delta = new Vector3();

    for (const edge of this._edges) {
      const source = this._nodes.get(edge.source);
      const target = this._nodes.get(edge.target);
      if (!source || !target) {
        continue;
      }

      delta.subVectors(target.position, source.position);
      const dist = Math.max(delta.length(), MIN_DISTANCE);
      const displacement = dist - SPRING_REST_LENGTH;
      const magnitude = SPRING_STRENGTH * displacement;

      delta.normalize().multiplyScalar(magnitude);
      source.force.add(delta);
      target.force.sub(delta);
    }
  }

  /**
   * Pull nodes toward their assigned gravity wells.
   */
  _applyGravity() {
    const delta = new Vector3();

    for (const node of this._nodes.values()) {
      if (node.stageId < 0 || node.stageId >= STAGE_COUNT) {
        continue;
      }

      const well = this._gravityWells[node.stageId];
      delta.subVectors(well, node.position);
      delta.multiplyScalar(GRAVITY_STRENGTH);
      node.force.add(delta);
    }
  }

  /**
   * Integrate forces into velocities and positions.
   * @param {number} deltaTime
   */
  _integrate(deltaTime) {
    for (const node of this._nodes.values()) {
      node.velocity.add(
        node.force.clone().multiplyScalar(deltaTime),
      );
      node.velocity.multiplyScalar(DAMPING);
      node.velocity.clampLength(0, MAX_VELOCITY);
      node.position.add(
        node.velocity.clone().multiplyScalar(deltaTime),
      );
    }
  }

  /**
   * Check whether all node velocities are below the convergence threshold.
   * @returns {boolean}
   */
  _checkConvergence() {
    for (const node of this._nodes.values()) {
      if (node.velocity.length() > CONVERGENCE_THRESHOLD) {
        return false;
      }
    }

    this._converged = true;
    return true;
  }
}
