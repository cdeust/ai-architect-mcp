/**
 * Camera Controller — PerspectiveCamera with OrbitControls.
 *
 * Manages camera positioning, smooth damping, and convenience methods
 * for focusing on graph nodes or resetting the view.
 */

import * as THREE from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const FOV = 60;
const NEAR = 0.1;
const FAR = 5000;

const INITIAL_POSITION = new THREE.Vector3(0, 150, 500);
const LOOK_AT_TARGET = new THREE.Vector3(0, 0, 0);

const DAMPING_FACTOR = 0.05;
const AUTO_ROTATE_SPEED = 0.15;
const ROTATE_SPEED = 0.4;
const ZOOM_SPEED = 0.8;
const MIN_DISTANCE = 50;
const MAX_DISTANCE = 2000;
const FOCUS_OFFSET = new THREE.Vector3(0, 80, 200);
const FOCUS_LERP_SPEED = 0.05;

// ---------------------------------------------------------------------------
// Class
// ---------------------------------------------------------------------------

export class CameraController {
  /**
   * @param {import("three").WebGLRenderer} renderer
   */
  constructor(renderer) {
    const aspect = window.innerWidth / window.innerHeight;

    this.camera = new THREE.PerspectiveCamera(FOV, aspect, NEAR, FAR);
    this.camera.position.copy(INITIAL_POSITION);
    this.camera.lookAt(LOOK_AT_TARGET);

    this._controls = new OrbitControls(this.camera, renderer.domElement);
    this._controls.enableDamping = true;
    this._controls.dampingFactor = DAMPING_FACTOR;
    this._controls.rotateSpeed = ROTATE_SPEED;
    this._controls.zoomSpeed = ZOOM_SPEED;
    this._controls.minDistance = MIN_DISTANCE;
    this._controls.maxDistance = MAX_DISTANCE;
    this._controls.autoRotate = true;
    this._controls.autoRotateSpeed = AUTO_ROTATE_SPEED;
    this._controls.target.copy(LOOK_AT_TARGET);

    this._focusTarget = null;
  }

  /**
   * Tick the controls. Call once per frame.
   */
  update() {
    if (this._focusTarget) {
      this._animateFocus();
    }
    this._controls.update();
  }

  /**
   * Smoothly move the camera to focus on a world-space position.
   *
   * @param {THREE.Vector3} position — the target position to look at.
   */
  focusOn(position) {
    this._focusTarget = position.clone();
  }

  /**
   * Reset camera to the initial overview position.
   */
  resetView() {
    this._focusTarget = null;
    this.camera.position.copy(INITIAL_POSITION);
    this._controls.target.copy(LOOK_AT_TARGET);
  }

  /**
   * Update camera aspect ratio after a viewport resize.
   *
   * @param {number} width
   * @param {number} height
   */
  resize(width, height) {
    this.camera.aspect = width / height;
    this.camera.updateProjectionMatrix();
  }

  // -----------------------------------------------------------------------
  // Private
  // -----------------------------------------------------------------------

  /**
   * Lerp camera and controls target toward _focusTarget.
   */
  _animateFocus() {
    const destination = this._focusTarget.clone().add(FOCUS_OFFSET);

    this.camera.position.lerp(destination, FOCUS_LERP_SPEED);
    this._controls.target.lerp(this._focusTarget, FOCUS_LERP_SPEED);

    const distance = this.camera.position.distanceTo(destination);
    if (distance < 1.0) {
      this._focusTarget = null;
    }
  }
}
