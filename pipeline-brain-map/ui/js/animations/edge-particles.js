/**
 * Particle flow along edges between pipeline nodes.
 * Uses Three.js Points geometry.
 */

import * as THREE from 'three';

const DEFAULT_PARTICLE_COUNT = 20;
const DEFAULT_SPEED = 1.0;
const PARTICLE_SIZE = 2.5;
const PARTICLE_OPACITY = 0.8;

/**
 * Create a particle flow system along an edge.
 * @param {THREE.Vector3} startPos
 * @param {THREE.Vector3} endPos
 * @param {THREE.Color | number} color
 * @param {number} speed — multiplier (1.0 = default)
 * @param {number} count — number of particles
 * @returns {ParticleFlow}
 */
export function createParticleFlow(
  startPos,
  endPos,
  color = 0x4fc3f7,
  speed = DEFAULT_SPEED,
  count = DEFAULT_PARTICLE_COUNT
) {
  return new ParticleFlow(startPos, endPos, color, speed, count);
}

class ParticleFlow {
  /**
   * @param {THREE.Vector3} startPos
   * @param {THREE.Vector3} endPos
   * @param {THREE.Color | number} color
   * @param {number} speed
   * @param {number} count
   */
  constructor(startPos, endPos, color, speed, count) {
    this.startPos = startPos.clone();
    this.endPos = endPos.clone();
    this.speed = speed;
    this.count = count;
    this.disposed = false;

    this.offsets = new Float32Array(count);
    this._initOffsets();

    this.geometry = this._buildGeometry();
    this.material = this._buildMaterial(color);
    this.points = new THREE.Points(this.geometry, this.material);
  }

  _initOffsets() {
    for (let i = 0; i < this.count; i++) {
      this.offsets[i] = i / this.count;
    }
  }

  _buildGeometry() {
    const positions = new Float32Array(this.count * 3);
    const geometry = new THREE.BufferGeometry();
    geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    this._updatePositions();
    return geometry;
  }

  _buildMaterial(color) {
    return new THREE.PointsMaterial({
      color: new THREE.Color(color),
      size: PARTICLE_SIZE,
      transparent: true,
      opacity: PARTICLE_OPACITY,
      depthWrite: false,
      blending: THREE.AdditiveBlending,
      sizeAttenuation: true,
    });
  }

  _updatePositions() {
    const posAttr = this.geometry.getAttribute('position');
    const dir = new THREE.Vector3().subVectors(this.endPos, this.startPos);

    for (let i = 0; i < this.count; i++) {
      const t = this.offsets[i];
      const x = this.startPos.x + dir.x * t;
      const y = this.startPos.y + dir.y * t;
      const z = this.startPos.z + dir.z * t;
      posAttr.setXYZ(i, x, y, z);
    }
    posAttr.needsUpdate = true;
  }

  /**
   * Advance particles along the edge.
   * @param {number} deltaTime — seconds
   */
  update(deltaTime) {
    if (this.disposed) return;

    const step = this.speed * deltaTime;
    for (let i = 0; i < this.count; i++) {
      this.offsets[i] = (this.offsets[i] + step) % 1;
    }
    this._updatePositions();
  }

  /**
   * Update the edge endpoints (for moving nodes).
   * @param {THREE.Vector3} start
   * @param {THREE.Vector3} end
   */
  setEndpoints(start, end) {
    this.startPos.copy(start);
    this.endPos.copy(end);
  }

  /**
   * Get the Three.js object to add to the scene.
   * @returns {THREE.Points}
   */
  getObject() {
    return this.points;
  }

  /**
   * Cleanup GPU resources.
   */
  dispose() {
    if (this.disposed) return;
    this.disposed = true;
    this.geometry.dispose();
    this.material.dispose();
  }
}

/**
 * Manage multiple particle flows and update them together.
 */
export class ParticleFlowManager {
  constructor() {
    /** @type {ParticleFlow[]} */
    this.flows = [];
  }

  /**
   * @param {ParticleFlow} flow
   * @param {THREE.Scene} scene
   */
  add(flow, scene) {
    this.flows.push(flow);
    scene.add(flow.getObject());
  }

  /**
   * Update all flows.
   * @param {number} deltaTime — seconds
   */
  update(deltaTime) {
    for (const flow of this.flows) {
      flow.update(deltaTime);
    }
  }

  /**
   * Remove and dispose all flows.
   * @param {THREE.Scene} scene
   */
  disposeAll(scene) {
    for (const flow of this.flows) {
      scene.remove(flow.getObject());
      flow.dispose();
    }
    this.flows.length = 0;
  }
}
