/**
 * Creates Three.js meshes for 7 node types.
 * Each node is a Group containing a geometry mesh and a label sprite.
 * @module node-factory
 */

import {
  Group,
  Mesh,
  MeshStandardMaterial,
  IcosahedronGeometry,
  BoxGeometry,
  OctahedronGeometry,
  TetrahedronGeometry,
  CylinderGeometry,
  TorusGeometry,
  SphereGeometry,
  SpriteMaterial,
  Sprite,
  CanvasTexture,
  Color,
} from 'three';

const NODE_COLORS = {
  stage: '#00d2ff',
  tool: '#ff6b35',
  artifact: '#a55eea',
  hor_rule: '#dfe6e9',
  gate: '#26de81',
  ooda: '#00cec9',
  error: '#ff4757',
  thinking: '#aed581',
  decision: '#ff4081',
};

const STATUS_EMISSIVE = {
  active: 2.5,
  completed: 1.8,
  failed: 2.8,
  pending: 1.0,
};

const DEFAULT_EMISSIVE = 2.2;
const HALO_SCALE = 5;
const HALO_OPACITY = 0.25;

/**
 * Build a Three.js geometry for the given node type.
 * @param {string} type — one of the 7 node types.
 * @returns {import('three').BufferGeometry}
 */
function buildGeometry(type) {
  switch (type) {
    case 'stage':
      return new IcosahedronGeometry(8);
    case 'tool':
      return new BoxGeometry(4, 4, 4);
    case 'artifact':
      return new OctahedronGeometry(5);
    case 'hor_rule':
      return new TetrahedronGeometry(4);
    case 'gate':
      return new CylinderGeometry(6, 6, 2, 32);
    case 'ooda':
      return new TorusGeometry(5, 1.5, 16, 32);
    case 'error':
      return new SphereGeometry(5, 32, 32);
    case 'thinking':
      return new IcosahedronGeometry(4);
    case 'decision':
      return new TorusGeometry(4, 1, 16, 32);
    default:
      return new SphereGeometry(4, 16, 16);
  }
}

/**
 * Build a MeshStandardMaterial for the given node type and status.
 * @param {string} type — node type key.
 * @param {string} status — current status string.
 * @returns {MeshStandardMaterial}
 */
function buildMaterial(type, status) {
  const hex = NODE_COLORS[type] ?? NODE_COLORS.error;
  const color = new Color(hex);
  const emissiveIntensity = STATUS_EMISSIVE[status] ?? DEFAULT_EMISSIVE;

  return new MeshStandardMaterial({
    color: color.clone().multiplyScalar(0.15),
    emissive: color,
    emissiveIntensity,
    metalness: 0.3,
    roughness: 0.4,
    transparent: true,
    opacity: 0.9,
  });
}

/**
 * Create a glow halo sprite for additive bloom effect.
 * @param {string} type — node type for color lookup.
 * @param {number} scale — node mesh scale.
 * @returns {Sprite}
 */
function createHaloSprite(type, scale) {
  const canvas = document.createElement('canvas');
  canvas.width = 128;
  canvas.height = 128;
  const ctx = canvas.getContext('2d');

  const gradient = ctx.createRadialGradient(64, 64, 0, 64, 64, 64);
  gradient.addColorStop(0, 'rgba(255,255,255,1.0)');
  gradient.addColorStop(0.15, 'rgba(255,255,255,0.6)');
  gradient.addColorStop(0.4, 'rgba(255,255,255,0.15)');
  gradient.addColorStop(0.7, 'rgba(255,255,255,0.03)');
  gradient.addColorStop(1, 'rgba(255,255,255,0.0)');
  ctx.fillStyle = gradient;
  ctx.fillRect(0, 0, 128, 128);

  const texture = new CanvasTexture(canvas);
  const hex = NODE_COLORS[type] ?? NODE_COLORS.error;

  const material = new SpriteMaterial({
    map: texture,
    color: new Color(hex),
    transparent: true,
    opacity: HALO_OPACITY,
    depthWrite: false,
  });

  const sprite = new Sprite(material);
  sprite.scale.setScalar(scale * HALO_SCALE);
  return sprite;
}

/**
 * Create a 2D canvas with the label text rendered on it.
 * @param {string} text — label string to render.
 * @returns {HTMLCanvasElement}
 */
function createLabelCanvas(text) {
  const canvas = document.createElement('canvas');
  const ctx = canvas.getContext('2d');
  const fontSize = 48;
  const padding = 16;

  ctx.font = `${fontSize}px sans-serif`;
  const metrics = ctx.measureText(text);
  const textWidth = metrics.width;

  canvas.width = textWidth + padding * 2;
  canvas.height = fontSize + padding * 2;

  ctx.clearRect(0, 0, canvas.width, canvas.height);
  ctx.font = `${fontSize}px sans-serif`;
  ctx.fillStyle = '#ffffff';
  ctx.textAlign = 'center';
  ctx.textBaseline = 'middle';
  ctx.fillText(text, canvas.width / 2, canvas.height / 2);

  return canvas;
}

/**
 * Create a sprite with a text label.
 * @param {string} label — display text.
 * @returns {Sprite}
 */
function createLabelSprite(label) {
  const canvas = createLabelCanvas(label);
  const texture = new CanvasTexture(canvas);
  const material = new SpriteMaterial({
    map: texture,
    transparent: true,
    depthTest: false,
  });

  const sprite = new Sprite(material);
  const aspect = canvas.width / canvas.height;
  const spriteHeight = 4;
  sprite.scale.set(spriteHeight * aspect, spriteHeight, 1);
  sprite.position.y = 12;

  return sprite;
}

/**
 * Apply position from node data to a Group.
 * @param {Group} group — the Three.js group to position.
 * @param {{x: number, y: number, z: number}} position — target position.
 */
function applyPosition(group, position) {
  group.position.set(
    position.x ?? 0,
    position.y ?? 0,
    position.z ?? 0,
  );
}

/**
 * Create a Three.js Group representing a graph node.
 * The group contains a typed geometry mesh and a floating label sprite.
 *
 * @param {{id: string, type: string, label: string, status?: string, position?: {x: number, y: number, z: number}}} nodeData
 * @returns {Group}
 */
export function createNode(nodeData) {
  const type = nodeData.type ?? 'error';
  const status = nodeData.status ?? 'idle';
  const label = nodeData.label ?? nodeData.id;

  const group = new Group();
  group.name = `node-${nodeData.id}`;
  group.userData = { nodeId: nodeData.id, nodeType: type };

  const geometry = buildGeometry(type);
  const material = buildMaterial(type, status);
  const mesh = new Mesh(geometry, material);
  group.add(mesh);

  const halo = createHaloSprite(type, 3);
  group.add(halo);

  const labelSprite = createLabelSprite(label);
  group.add(labelSprite);

  if (nodeData.position) {
    applyPosition(group, nodeData.position);
  }

  return group;
}

/**
 * Update the material of an existing node mesh to reflect a new status.
 * @param {Group} group — the node's Three.js Group.
 * @param {string} status — the new status.
 */
export function updateNodeStatus(group, status) {
  const mesh = group.children.find((child) => child.isMesh);
  if (!mesh) {
    return;
  }

  const type = group.userData.nodeType ?? 'error';
  const emissiveIntensity = STATUS_EMISSIVE[status] ?? DEFAULT_EMISSIVE;
  const baseColor = NODE_COLORS[type] ?? NODE_COLORS.error;

  mesh.material.emissive.set(baseColor);
  mesh.material.emissiveIntensity = emissiveIntensity;
  mesh.material.needsUpdate = true;
}
