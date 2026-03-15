/**
 * Creates Three.js lines for 5 edge types.
 * Uses BufferGeometry with LineBasicMaterial or LineDashedMaterial.
 * @module edge-factory
 */

import {
  BufferGeometry,
  Float32BufferAttribute,
  Line,
  LineBasicMaterial,
  LineDashedMaterial,
  Vector3,
  Color,
} from 'three';

const EDGE_STYLES = {
  data_flow: {
    color: '#ffffff',
    opacity: 0.4,
    linewidth: 1,
    dashed: false,
  },
  triggers: {
    color: '#ff9800',
    opacity: 0.8,
    linewidth: 1,
    dashed: true,
    dashSize: 3,
    gapSize: 2,
  },
  contains: {
    color: '#9e9e9e',
    opacity: 0.2,
    linewidth: 1,
    dashed: false,
  },
  depends_on: {
    color: '#ffeb3b',
    opacity: 0.7,
    linewidth: 2,
    dashed: false,
  },
  cross_reference: {
    color: '#00e5ff',
    opacity: 0.5,
    linewidth: 1,
    dashed: true,
    dashSize: 1,
    gapSize: 2,
  },
};

const DEFAULT_STYLE = {
  color: '#ffffff',
  opacity: 0.3,
  linewidth: 1,
  dashed: false,
};

/**
 * Resolve the style configuration for an edge type.
 * @param {string} edgeType — one of the 5 edge types.
 * @returns {{color: string, opacity: number, linewidth: number, dashed: boolean, dashSize?: number, gapSize?: number}}
 */
function resolveStyle(edgeType) {
  return EDGE_STYLES[edgeType] ?? DEFAULT_STYLE;
}

/**
 * Create a material for the given edge style.
 * @param {{color: string, opacity: number, linewidth: number, dashed: boolean, dashSize?: number, gapSize?: number}} style
 * @returns {LineBasicMaterial|LineDashedMaterial}
 */
function buildMaterial(style) {
  const params = {
    color: new Color(style.color),
    transparent: true,
    opacity: style.opacity,
    linewidth: style.linewidth,
  };

  if (style.dashed) {
    return new LineDashedMaterial({
      ...params,
      dashSize: style.dashSize ?? 3,
      gapSize: style.gapSize ?? 2,
    });
  }

  return new LineBasicMaterial(params);
}

/**
 * Create a BufferGeometry from two 3D positions.
 * @param {{x: number, y: number, z: number}} sourcePos
 * @param {{x: number, y: number, z: number}} targetPos
 * @returns {BufferGeometry}
 */
function buildLineGeometry(sourcePos, targetPos) {
  const geometry = new BufferGeometry();
  const positions = new Float32Array([
    sourcePos.x, sourcePos.y, sourcePos.z,
    targetPos.x, targetPos.y, targetPos.z,
  ]);

  geometry.setAttribute('position', new Float32BufferAttribute(positions, 3));
  return geometry;
}

/**
 * Create a Three.js Line representing a graph edge.
 *
 * @param {{id: string, source: string, target: string, type: string, weight?: number, animated?: boolean}} edgeData
 * @param {{x: number, y: number, z: number}} sourcePos — world position of source node.
 * @param {{x: number, y: number, z: number}} targetPos — world position of target node.
 * @returns {Line}
 */
export function createEdge(edgeData, sourcePos, targetPos) {
  const style = resolveStyle(edgeData.type);
  const geometry = buildLineGeometry(sourcePos, targetPos);
  const material = buildMaterial(style);
  const line = new Line(geometry, material);

  line.name = `edge-${edgeData.id}`;
  line.userData = {
    edgeId: edgeData.id,
    edgeType: edgeData.type,
    source: edgeData.source,
    target: edgeData.target,
    animated: edgeData.animated ?? false,
  };

  if (style.dashed) {
    line.computeLineDistances();
  }

  return line;
}

/**
 * Update an existing edge line's geometry to reflect new endpoint positions.
 *
 * @param {Line} line — the Three.js Line to update.
 * @param {{x: number, y: number, z: number}} sourcePos — new source position.
 * @param {{x: number, y: number, z: number}} targetPos — new target position.
 */
export function updateEdge(line, sourcePos, targetPos) {
  const positionAttr = line.geometry.getAttribute('position');
  const positions = positionAttr.array;

  positions[0] = sourcePos.x;
  positions[1] = sourcePos.y;
  positions[2] = sourcePos.z;
  positions[3] = targetPos.x;
  positions[4] = targetPos.y;
  positions[5] = targetPos.z;

  positionAttr.needsUpdate = true;
  line.geometry.computeBoundingSphere();

  if (line.userData.edgeType && resolveStyle(line.userData.edgeType).dashed) {
    line.computeLineDistances();
  }
}

/**
 * Animate a dashed-line edge by shifting the dash offset.
 * Call this each frame for edges with `animated: true`.
 *
 * @param {Line} line — the dashed Line to animate.
 * @param {number} deltaTime — seconds since last frame.
 * @param {number} speed — dash scroll speed (default 5).
 */
export function animateEdgeDash(line, deltaTime, speed = 5) {
  if (!line.material.isLineDashedMaterial) {
    return;
  }

  line.material.dashOffset -= deltaTime * speed;
}
