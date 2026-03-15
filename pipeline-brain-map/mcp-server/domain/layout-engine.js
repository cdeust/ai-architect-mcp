'use strict';

const ARC_RADIUS = 500;
const STAGE_COUNT = 11;
const REPULSION_STRENGTH = 100;
const ATTRACTION_STRENGTH = 0.01;
const GRAVITY_STRENGTH = 0.05;
const DAMPING = 0.95;

class LayoutEngine {
  /**
   * @param {object} [config]
   * @param {number} [config.arcRadius]
   * @param {number} [config.repulsionStrength]
   * @param {number} [config.attractionStrength]
   * @param {number} [config.gravityStrength]
   * @param {number} [config.damping]
   */
  constructor(config = {}) {
    this._arcRadius = config.arcRadius || ARC_RADIUS;
    this._repulsion = config.repulsionStrength || REPULSION_STRENGTH;
    this._attraction = config.attractionStrength || ATTRACTION_STRENGTH;
    this._gravity = config.gravityStrength || GRAVITY_STRENGTH;
    this._damping = config.damping || DAMPING;

    /** @type {Map<string, {x: number, y: number, z: number}>} */
    this._positions = new Map();
    /** @type {Map<string, {x: number, y: number, z: number}>} */
    this._velocities = new Map();
    /** @type {Map<string, number|null>} */
    this._nodeStages = new Map();
    /** @type {{source: string, target: string}[]} */
    this._edges = [];
    /** @type {{x: number, y: number, z: number}[]} */
    this._gravityWells = [];

    this.setGravityWells();
  }

  /**
   * Create 11 gravity points on a semicircular arc in 3D space.
   * Stages are evenly distributed from -PI/2 to PI/2 on the XZ plane,
   * with a slight Y offset per stage for visual separation.
   */
  setGravityWells() {
    this._gravityWells = [];
    for (let i = 0; i < STAGE_COUNT; i++) {
      const angle = (-Math.PI / 2) + (Math.PI * i) / (STAGE_COUNT - 1);
      const x = this._arcRadius * Math.cos(angle);
      const z = this._arcRadius * Math.sin(angle);
      const y = (i - (STAGE_COUNT - 1) / 2) * 20;
      this._gravityWells.push({ x, y, z });
    }
  }

  /**
   * Add a node to the simulation. Initial position is jittered near
   * its stage gravity well, or at the origin if no stageId.
   * @param {object} node - Must have id, stageId.
   */
  addNode(node) {
    if (this._positions.has(node.id)) return;

    const well = this._wellForStage(node.stageId);
    const jitter = () => (Math.random() - 0.5) * 40;
    this._positions.set(node.id, {
      x: well.x + jitter(),
      y: well.y + jitter(),
      z: well.z + jitter(),
    });
    this._velocities.set(node.id, { x: 0, y: 0, z: 0 });
    this._nodeStages.set(node.id, node.stageId);
  }

  /**
   * Remove a node from the simulation.
   * @param {string} nodeId
   */
  removeNode(nodeId) {
    this._positions.delete(nodeId);
    this._velocities.delete(nodeId);
    this._nodeStages.delete(nodeId);
    this._edges = this._edges.filter(
      (e) => e.source !== nodeId && e.target !== nodeId
    );
  }

  /**
   * Register an edge for attraction forces.
   * @param {string} source
   * @param {string} target
   */
  addEdge(source, target) {
    this._edges.push({ source, target });
  }

  /**
   * Run one simulation step.
   * @param {number} deltaTime - Time step in seconds.
   */
  tick(deltaTime) {
    this._applyGravity(deltaTime);
    this._applyRepulsion(deltaTime);
    this._applyAttraction(deltaTime);
    this._integrate(deltaTime);
  }

  /**
   * Return current positions for all nodes.
   * @returns {Map<string, {x: number, y: number, z: number}>}
   */
  getPositions() {
    const result = new Map();
    for (const [id, pos] of this._positions) {
      result.set(id, { x: pos.x, y: pos.y, z: pos.z });
    }
    return result;
  }

  /**
   * Get the gravity well for a given stage id.
   * @param {number|null} stageId
   * @returns {{x: number, y: number, z: number}}
   */
  _wellForStage(stageId) {
    if (stageId != null && stageId >= 0 && stageId < STAGE_COUNT) {
      return this._gravityWells[stageId];
    }
    return { x: 0, y: 0, z: 0 };
  }

  /**
   * Pull each node toward its stage gravity well.
   * @param {number} dt
   */
  _applyGravity(dt) {
    for (const [id, pos] of this._positions) {
      const well = this._wellForStage(this._nodeStages.get(id));
      const vel = this._velocities.get(id);
      vel.x += (well.x - pos.x) * this._gravity * dt;
      vel.y += (well.y - pos.y) * this._gravity * dt;
      vel.z += (well.z - pos.z) * this._gravity * dt;
    }
  }

  /**
   * Push nodes apart to prevent overlap.
   * @param {number} dt
   */
  _applyRepulsion(dt) {
    const ids = [...this._positions.keys()];
    for (let i = 0; i < ids.length; i++) {
      for (let j = i + 1; j < ids.length; j++) {
        this._repelPair(ids[i], ids[j], dt);
      }
    }
  }

  /**
   * Apply repulsion between two nodes.
   * @param {string} idA
   * @param {string} idB
   * @param {number} dt
   */
  _repelPair(idA, idB, dt) {
    const posA = this._positions.get(idA);
    const posB = this._positions.get(idB);
    const dx = posA.x - posB.x;
    const dy = posA.y - posB.y;
    const dz = posA.z - posB.z;
    const distSq = dx * dx + dy * dy + dz * dz + 0.01;
    const dist = Math.sqrt(distSq);
    const force = (this._repulsion * dt) / distSq;
    const fx = (dx / dist) * force;
    const fy = (dy / dist) * force;
    const fz = (dz / dist) * force;

    const velA = this._velocities.get(idA);
    const velB = this._velocities.get(idB);
    velA.x += fx;
    velA.y += fy;
    velA.z += fz;
    velB.x -= fx;
    velB.y -= fy;
    velB.z -= fz;
  }

  /**
   * Pull connected nodes together along edges.
   * @param {number} dt
   */
  _applyAttraction(dt) {
    for (const edge of this._edges) {
      this._attractPair(edge.source, edge.target, dt);
    }
  }

  /**
   * Apply attraction between two connected nodes.
   * @param {string} srcId
   * @param {string} tgtId
   * @param {number} dt
   */
  _attractPair(srcId, tgtId, dt) {
    const posA = this._positions.get(srcId);
    const posB = this._positions.get(tgtId);
    if (!posA || !posB) return;

    const dx = posB.x - posA.x;
    const dy = posB.y - posA.y;
    const dz = posB.z - posA.z;
    const fx = dx * this._attraction * dt;
    const fy = dy * this._attraction * dt;
    const fz = dz * this._attraction * dt;

    const velA = this._velocities.get(srcId);
    const velB = this._velocities.get(tgtId);
    velA.x += fx;
    velA.y += fy;
    velA.z += fz;
    velB.x -= fx;
    velB.y -= fy;
    velB.z -= fz;
  }

  /**
   * Update positions from velocities and apply damping.
   * @param {number} dt
   */
  _integrate(dt) {
    for (const [id, pos] of this._positions) {
      const vel = this._velocities.get(id);
      pos.x += vel.x * dt;
      pos.y += vel.y * dt;
      pos.z += vel.z * dt;
      vel.x *= this._damping;
      vel.y *= this._damping;
      vel.z *= this._damping;
    }
  }
}

module.exports = {
  LayoutEngine,
  ARC_RADIUS,
  STAGE_COUNT,
  REPULSION_STRENGTH,
  ATTRACTION_STRENGTH,
  GRAVITY_STRENGTH,
  DAMPING,
};
