/**
 * Scene Factory — creates and configures the Three.js scene.
 *
 * Returns { scene, renderer } with lighting, fog, and grid helpers
 * pre-configured for the brain-map dark aesthetic.
 */

import * as THREE from "three";

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const BACKGROUND_COLOR = 0x030508;
const FOG_NEAR = 400;
const FOG_FAR = 2000;

const AMBIENT_COLOR = 0x101520;
const AMBIENT_INTENSITY = 2;

const CYAN_POINT_COLOR = 0x00d2ff;
const CYAN_POINT_INTENSITY = 40;
const CYAN_POINT_RANGE = 1200;
const CYAN_POINT_POSITION = new THREE.Vector3(0, 200, 100);

const MAGENTA_POINT_COLOR = 0xff4081;
const MAGENTA_POINT_INTENSITY = 20;
const MAGENTA_POINT_RANGE = 800;
const MAGENTA_POINT_POSITION = new THREE.Vector3(-200, -100, -200);

const DIR_LIGHT_COLOR = 0x4060a0;
const DIR_LIGHT_INTENSITY = 1;
const DIR_LIGHT_POSITION = new THREE.Vector3(100, 300, 200);

const GRID_SIZE = 2000;
const GRID_DIVISIONS = 40;
const GRID_CENTER_COLOR = 0x1a1a3a;
const GRID_LINE_COLOR = 0x111128;
const GRID_OPACITY = 0.3;

// ---------------------------------------------------------------------------
// Factory
// ---------------------------------------------------------------------------

/**
 * Create a fully configured Three.js scene and WebGL renderer.
 *
 * @param {HTMLCanvasElement} canvas — the target canvas element.
 * @returns {{ scene: THREE.Scene, renderer: THREE.WebGLRenderer }}
 */
export function createScene(canvas) {
  const renderer = buildRenderer(canvas);
  const scene = new THREE.Scene();

  scene.background = new THREE.Color(BACKGROUND_COLOR);
  scene.fog = new THREE.FogExp2(BACKGROUND_COLOR, 0.0006);

  addLighting(scene);
  addGrid(scene);

  return { scene, renderer };
}

// ---------------------------------------------------------------------------
// Renderer
// ---------------------------------------------------------------------------

/**
 * Build and configure the WebGL renderer.
 *
 * @param {HTMLCanvasElement} canvas
 * @returns {THREE.WebGLRenderer}
 */
function buildRenderer(canvas) {
  const renderer = new THREE.WebGLRenderer({
    canvas,
    antialias: true,
    alpha: false,
  });

  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  renderer.setSize(window.innerWidth, window.innerHeight);
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure = 1.2;
  renderer.outputColorSpace = THREE.SRGBColorSpace;

  return renderer;
}

// ---------------------------------------------------------------------------
// Lighting
// ---------------------------------------------------------------------------

/**
 * Add ambient, key, and fill lights to the scene.
 *
 * @param {THREE.Scene} scene
 */
function addLighting(scene) {
  const ambient = new THREE.AmbientLight(AMBIENT_COLOR, AMBIENT_INTENSITY);
  scene.add(ambient);

  const cyanPoint = new THREE.PointLight(CYAN_POINT_COLOR, CYAN_POINT_INTENSITY, CYAN_POINT_RANGE);
  cyanPoint.position.copy(CYAN_POINT_POSITION);
  scene.add(cyanPoint);

  const magentaPoint = new THREE.PointLight(MAGENTA_POINT_COLOR, MAGENTA_POINT_INTENSITY, MAGENTA_POINT_RANGE);
  magentaPoint.position.copy(MAGENTA_POINT_POSITION);
  scene.add(magentaPoint);

  const dirLight = new THREE.DirectionalLight(DIR_LIGHT_COLOR, DIR_LIGHT_INTENSITY);
  dirLight.position.copy(DIR_LIGHT_POSITION);
  scene.add(dirLight);
}

// ---------------------------------------------------------------------------
// Grid
// ---------------------------------------------------------------------------

/**
 * Add a subtle transparent grid on the XZ plane.
 *
 * @param {THREE.Scene} scene
 */
function addGrid(scene) {
  const grid = new THREE.GridHelper(
    GRID_SIZE,
    GRID_DIVISIONS,
    GRID_CENTER_COLOR,
    GRID_LINE_COLOR,
  );

  grid.material.transparent = true;
  grid.material.opacity = GRID_OPACITY;
  grid.material.depthWrite = false;
  grid.position.y = -50;

  scene.add(grid);
}
