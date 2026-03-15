/**
 * Smooth position, scale, and color tweens for 3D nodes.
 * Uses requestAnimationFrame for an internal tick system.
 */

const ACTIVE_TWEENS = [];
let animFrameId = null;

function easeOut(t) {
  return 1 - Math.pow(1 - t, 3);
}

function easeInOut(t) {
  return t < 0.5
    ? 4 * t * t * t
    : 1 - Math.pow(-2 * t + 2, 3) / 2;
}

const EASING_FNS = {
  easeOut,
  easeInOut,
  linear: (t) => t,
};

function getEasing(name) {
  return EASING_FNS[name] ?? easeOut;
}

function tick(timestamp) {
  for (let i = ACTIVE_TWEENS.length - 1; i >= 0; i--) {
    const tween = ACTIVE_TWEENS[i];
    if (!tween.startTime) tween.startTime = timestamp;

    const elapsed = timestamp - tween.startTime;
    const rawT = Math.min(elapsed / tween.duration, 1);
    const t = tween.easingFn(rawT);

    tween.update(t);

    if (rawT >= 1) {
      tween.update(1);
      ACTIVE_TWEENS.splice(i, 1);
      if (tween.onComplete) tween.onComplete();
    }
  }

  if (ACTIVE_TWEENS.length > 0) {
    animFrameId = requestAnimationFrame(tick);
  } else {
    animFrameId = null;
  }
}

function scheduleTween(tween) {
  ACTIVE_TWEENS.push(tween);
  if (animFrameId === null) {
    animFrameId = requestAnimationFrame(tick);
  }
}

/**
 * Animate a mesh to a target position.
 * @param {Object} mesh — must have mesh.position.{x,y,z}
 * @param {{ x: number, y: number, z: number }} target
 * @param {number} duration — ms
 * @param {string} easing — 'easeOut' | 'easeInOut' | 'linear'
 * @returns {Promise<void>}
 */
export function animateTo(mesh, target, duration = 400, easing = 'easeOut') {
  const start = { x: mesh.position.x, y: mesh.position.y, z: mesh.position.z };
  const easingFn = getEasing(easing);

  return new Promise((resolve) => {
    scheduleTween({
      duration,
      easingFn,
      startTime: null,
      onComplete: resolve,
      update(t) {
        mesh.position.x = start.x + (target.x - start.x) * t;
        mesh.position.y = start.y + (target.y - start.y) * t;
        mesh.position.z = start.z + (target.z - start.z) * t;
      },
    });
  });
}

/**
 * Animate a mesh's scale uniformly.
 * @param {Object} mesh — must have mesh.scale.{x,y,z}
 * @param {number} targetScale
 * @param {number} duration — ms
 * @returns {Promise<void>}
 */
export function animateScale(mesh, targetScale, duration = 300) {
  const startScale = mesh.scale.x;

  return new Promise((resolve) => {
    scheduleTween({
      duration,
      easingFn: easeOut,
      startTime: null,
      onComplete: resolve,
      update(t) {
        const s = startScale + (targetScale - startScale) * t;
        mesh.scale.set(s, s, s);
      },
    });
  });
}

/**
 * Animate a material's color to a target color.
 * @param {Object} material — must have material.color.{r,g,b}
 * @param {{ r: number, g: number, b: number }} targetColor
 * @param {number} duration — ms
 * @returns {Promise<void>}
 */
export function animateColor(material, targetColor, duration = 300) {
  const startColor = { r: material.color.r, g: material.color.g, b: material.color.b };

  return new Promise((resolve) => {
    scheduleTween({
      duration,
      easingFn: easeOut,
      startTime: null,
      onComplete: resolve,
      update(t) {
        material.color.r = startColor.r + (targetColor.r - startColor.r) * t;
        material.color.g = startColor.g + (targetColor.g - startColor.g) * t;
        material.color.b = startColor.b + (targetColor.b - startColor.b) * t;
      },
    });
  });
}

/**
 * Cancel all active tweens.
 */
export function cancelAll() {
  ACTIVE_TWEENS.length = 0;
  if (animFrameId !== null) {
    cancelAnimationFrame(animFrameId);
    animFrameId = null;
  }
}

/**
 * @returns {number} count of active tweens
 */
export function activeCount() {
  return ACTIVE_TWEENS.length;
}
