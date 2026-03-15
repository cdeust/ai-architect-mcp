import * as THREE from "three";

const STAGE_NAMES = [
  "HealthCheck",
  "Context",
  "Triage",
  "Requirements",
  "Interview",
  "Generation",
  "Review",
  "Verification",
  "Build",
  "Regression",
  "PullRequest",
];

const STAGE_LABELS = [
  "Stage 0: Health",
  "Stage 1: Context",
  "Stage 2: Triage",
  "Stage 3: Requirements",
  "Stage 4: Interview",
  "Stage 5: Generation",
  "Stage 6: Review",
  "Stage 7: Verification",
  "Stage 8: Build",
  "Stage 9: Regression",
  "Stage 10: PR",
];

const ARC_RADIUS = 400;
const SPHERE_RADIUS = 40;
const SPHERE_SEGMENTS = 16;
const DEFAULT_OPACITY = 0.05;
const HIGHLIGHT_OPACITY = 0.25;
const STAGE_COUNT = 11;

const regions = [];

function computeArcPosition(index) {
  const angle = (Math.PI * index) / (STAGE_COUNT - 1);
  const x = ARC_RADIUS * Math.cos(angle);
  const y = 0;
  const z = ARC_RADIUS * Math.sin(angle);
  return new THREE.Vector3(x, y, z);
}

function createTextSprite(text) {
  const canvas = document.createElement("canvas");
  const ctx = canvas.getContext("2d");
  canvas.width = 256;
  canvas.height = 64;

  ctx.fillStyle = "transparent";
  ctx.fillRect(0, 0, canvas.width, canvas.height);

  ctx.font = "bold 24px monospace";
  ctx.fillStyle = "#ffffff";
  ctx.textAlign = "center";
  ctx.textBaseline = "middle";
  ctx.fillText(text, canvas.width / 2, canvas.height / 2);

  const texture = new THREE.CanvasTexture(canvas);
  const material = new THREE.SpriteMaterial({
    map: texture,
    transparent: true,
  });
  const sprite = new THREE.Sprite(material);
  sprite.scale.set(80, 20, 1);
  return sprite;
}

function createRegion(index) {
  const geometry = new THREE.SphereGeometry(
    SPHERE_RADIUS,
    SPHERE_SEGMENTS,
    SPHERE_SEGMENTS
  );
  const material = new THREE.MeshBasicMaterial({
    color: 0x4fc3f7,
    opacity: DEFAULT_OPACITY,
    transparent: true,
    wireframe: true,
  });
  const mesh = new THREE.Mesh(geometry, material);
  const position = computeArcPosition(index);
  mesh.position.copy(position);
  mesh.userData = { stageId: index, stageName: STAGE_NAMES[index] };

  const label = createTextSprite(STAGE_LABELS[index]);
  label.position.copy(position);
  label.position.y += SPHERE_RADIUS + 15;

  return { mesh, label, index };
}

export function create(scene) {
  regions.length = 0;
  for (let i = 0; i < STAGE_COUNT; i++) {
    const region = createRegion(i);
    scene.add(region.mesh);
    scene.add(region.label);
    regions.push(region);
  }
  return regions;
}

export function highlight(stageId) {
  if (stageId < 0 || stageId >= STAGE_COUNT) {
    return;
  }
  const region = regions[stageId];
  if (region) {
    region.mesh.material.opacity = HIGHLIGHT_OPACITY;
    region.mesh.material.color.set(0x00e5ff);
  }
}

export function clearHighlights() {
  for (const region of regions) {
    region.mesh.material.opacity = DEFAULT_OPACITY;
    region.mesh.material.color.set(0x4fc3f7);
  }
}

export function getRegions() {
  return regions;
}

export function getPosition(stageId) {
  if (stageId < 0 || stageId >= STAGE_COUNT) {
    return null;
  }
  return computeArcPosition(stageId);
}

export { STAGE_NAMES, STAGE_LABELS, ARC_RADIUS, STAGE_COUNT };
