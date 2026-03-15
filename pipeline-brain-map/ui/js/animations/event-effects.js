/**
 * Visual effects for pipeline events.
 * Each effect self-cleans after animation completes.
 */

import * as THREE from 'three';

const SHOCKWAVE_DURATION = 800;
const SHOCKWAVE_MAX_SCALE = 6;
const SHOCKWAVE_SEGMENTS = 64;

const CASCADE_DELAY = 80;
const CASCADE_DURATION = 400;

const OODA_DURATION = 1200;
const OODA_SEGMENTS = 32;

const GLOW_DURATION = 600;

/**
 * Expanding ring effect for gate pass/fail.
 * @param {THREE.Scene} scene
 * @param {THREE.Vector3} position
 * @param {boolean} passed — green if true, red if false
 * @returns {{ update: (dt: number) => boolean }}
 */
export function gateShockwave(scene, position, passed) {
  const color = passed ? 0x4caf50 : 0xf44336;
  const geometry = new THREE.RingGeometry(0.5, 0.7, SHOCKWAVE_SEGMENTS);
  const material = new THREE.MeshBasicMaterial({
    color,
    transparent: true,
    opacity: 1,
    side: THREE.DoubleSide,
    depthWrite: false,
  });
  const mesh = new THREE.Mesh(geometry, material);
  mesh.position.copy(position);
  scene.add(mesh);

  let elapsed = 0;

  return {
    update(dt) {
      elapsed += dt * 1000;
      const t = Math.min(elapsed / SHOCKWAVE_DURATION, 1);
      const scale = 1 + t * SHOCKWAVE_MAX_SCALE;
      mesh.scale.set(scale, scale, scale);
      material.opacity = 1 - t;
      if (t >= 1) {
        scene.remove(mesh);
        geometry.dispose();
        material.dispose();
        return false;
      }
      return true;
    },
  };
}

/**
 * Sequential pulse through HOR rule node positions.
 * @param {THREE.Scene} scene
 * @param {THREE.Vector3[]} positions
 * @returns {{ update: (dt: number) => boolean }}
 */
export function horCascade(scene, positions) {
  const spheres = positions.map((pos) => {
    const geo = new THREE.SphereGeometry(0.3, 16, 16);
    const mat = new THREE.MeshBasicMaterial({
      color: 0xffab40,
      transparent: true,
      opacity: 0,
      depthWrite: false,
    });
    const mesh = new THREE.Mesh(geo, mat);
    mesh.position.copy(pos);
    scene.add(mesh);
    return { mesh, geo, mat };
  });

  let elapsed = 0;
  const totalDuration = CASCADE_DELAY * positions.length + CASCADE_DURATION;

  return {
    update(dt) {
      elapsed += dt * 1000;
      updateCascadeSpheres(spheres, elapsed);
      if (elapsed >= totalDuration) {
        disposeCascade(scene, spheres);
        return false;
      }
      return true;
    },
  };
}

function updateCascadeSpheres(spheres, elapsed) {
  for (let i = 0; i < spheres.length; i++) {
    const start = i * CASCADE_DELAY;
    const localT = Math.max(0, Math.min((elapsed - start) / CASCADE_DURATION, 1));
    const { mesh, mat } = spheres[i];
    const scale = 1 + localT * 1.5;
    mesh.scale.set(scale, scale, scale);
    mat.opacity = localT < 0.5 ? localT * 2 : 2 * (1 - localT);
  }
}

function disposeCascade(scene, spheres) {
  for (const { mesh, geo, mat } of spheres) {
    scene.remove(mesh);
    geo.dispose();
    mat.dispose();
  }
}

/**
 * Torus spin effect for OODA checkpoints.
 * @param {THREE.Scene} scene
 * @param {THREE.Vector3} position
 * @returns {{ update: (dt: number) => boolean }}
 */
export function oodaPulse(scene, position) {
  const geometry = new THREE.TorusGeometry(0.8, 0.1, 16, OODA_SEGMENTS);
  const material = new THREE.MeshBasicMaterial({
    color: 0x7c4dff,
    transparent: true,
    opacity: 0.9,
    depthWrite: false,
  });
  const mesh = new THREE.Mesh(geometry, material);
  mesh.position.copy(position);
  scene.add(mesh);

  let elapsed = 0;

  return {
    update(dt) {
      elapsed += dt * 1000;
      const t = Math.min(elapsed / OODA_DURATION, 1);
      mesh.rotation.x += dt * 4;
      mesh.rotation.y += dt * 2;
      const scale = 1 + Math.sin(t * Math.PI) * 0.5;
      mesh.scale.set(scale, scale, scale);
      material.opacity = 0.9 * (1 - t * 0.7);
      if (t >= 1) {
        scene.remove(mesh);
        geometry.dispose();
        material.dispose();
        return false;
      }
      return true;
    },
  };
}

/**
 * Temporary emissive boost on a mesh.
 * @param {THREE.Mesh} mesh — must have material with emissive property
 * @param {THREE.Color | number} color
 * @param {number} duration — ms (default 600)
 * @returns {{ update: (dt: number) => boolean }}
 */
export function stageGlow(mesh, color, duration = GLOW_DURATION) {
  const targetColor = new THREE.Color(color);
  const originalEmissive = mesh.material.emissive
    ? mesh.material.emissive.clone()
    : new THREE.Color(0x000000);
  const hasEmissive = 'emissive' in mesh.material;
  if (!hasEmissive) return { update: () => false };

  const originalIntensity = mesh.material.emissiveIntensity ?? 1;
  let elapsed = 0;

  return {
    update(dt) {
      elapsed += dt * 1000;
      const t = Math.min(elapsed / duration, 1);
      const intensity = t < 0.3 ? t / 0.3 : 1 - (t - 0.3) / 0.7;
      mesh.material.emissive.lerpColors(originalEmissive, targetColor, intensity);
      mesh.material.emissiveIntensity = originalIntensity + intensity * 2;
      if (t >= 1) {
        mesh.material.emissive.copy(originalEmissive);
        mesh.material.emissiveIntensity = originalIntensity;
        return false;
      }
      return true;
    },
  };
}

/**
 * Manages active effects and updates them each frame.
 */
export class EffectManager {
  constructor() {
    /** @type {Array<{ update: (dt: number) => boolean }>} */
    this.effects = [];
  }

  /** @param {{ update: (dt: number) => boolean }} effect */
  add(effect) {
    this.effects.push(effect);
  }

  /** @param {number} deltaTime — seconds */
  update(deltaTime) {
    for (let i = this.effects.length - 1; i >= 0; i--) {
      const alive = this.effects[i].update(deltaTime);
      if (!alive) {
        this.effects.splice(i, 1);
      }
    }
  }

  /** @returns {number} */
  get activeCount() {
    return this.effects.length;
  }
}
