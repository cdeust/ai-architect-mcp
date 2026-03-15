/**
 * Bloom Compositor — post-processing pipeline with UnrealBloomPass.
 *
 * Wraps EffectComposer to provide a single render() call that applies
 * bloom and tone-mapping to the final frame.
 */

import { EffectComposer } from "three/addons/postprocessing/EffectComposer.js";
import { RenderPass } from "three/addons/postprocessing/RenderPass.js";
import { UnrealBloomPass } from "three/addons/postprocessing/UnrealBloomPass.js";
import { Vector2 } from "three";

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const BLOOM_STRENGTH = 1.2;
const BLOOM_RADIUS = 0.5;
const BLOOM_THRESHOLD = 0.15;

// ---------------------------------------------------------------------------
// Class
// ---------------------------------------------------------------------------

export class BloomCompositor {
  /**
   * @param {import("three").WebGLRenderer} renderer
   * @param {import("three").Scene} scene
   * @param {import("three").Camera} camera
   */
  constructor(renderer, scene, camera) {
    const resolution = new Vector2(window.innerWidth, window.innerHeight);

    this._composer = new EffectComposer(renderer);

    const renderPass = new RenderPass(scene, camera);
    this._composer.addPass(renderPass);

    this._bloomPass = new UnrealBloomPass(
      resolution,
      BLOOM_STRENGTH,
      BLOOM_RADIUS,
      BLOOM_THRESHOLD,
    );
    this._composer.addPass(this._bloomPass);
  }

  /**
   * Render one frame through the post-processing pipeline.
   *
   * @param {import("three").Scene} scene
   * @param {import("three").Camera} camera
   */
  render(scene, camera) {
    this._composer.render();
  }

  /**
   * Update internal buffers when the viewport size changes.
   *
   * @param {number} width
   * @param {number} height
   */
  resize(width, height) {
    this._composer.setSize(width, height);
    this._bloomPass.resolution.set(width, height);
  }
}
