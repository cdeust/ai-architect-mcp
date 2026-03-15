/**
 * Pipeline Brain-Map — Main entry point.
 * Bootstraps the 3D visualization by fetching trace data from the
 * server API, wiring components via DI, and starting the render loop.
 */
import { createScene } from './scene/scene-factory.js';
import { BloomCompositor } from './scene/bloom-compositor.js';
import { CameraController } from './scene/camera-controller.js';
import { GraphState } from './graph/graph-state.js';
import { createNode, updateNodeStatus } from './graph/node-factory.js';
import { createEdge, updateEdge } from './graph/edge-factory.js';
import { LayoutEngine } from './graph/layout-engine.js';
import * as StageRegions from './pipeline/stage-regions.js';
import * as EventProcessor from './pipeline/event-processor.js';
import * as KPIStrip from './ui/kpi-strip.js';
import * as ReplayControls from './ui/replay-controls.js';
import * as DetailPanel from './ui/detail-panel.js';
import * as SearchBar from './ui/search-bar.js';
import { Raycaster, Vector2 } from 'three';

const TRACE_ENDPOINT = '/api/trace';
const DELTA_TIME = 1 / 60;

// ---------------------------------------------------------------------------
// Bootstrap
// ---------------------------------------------------------------------------

/** Main entry — creates components, fetches data, starts render loop. */
async function boot() {
  const canvas = document.getElementById('viewport');
  const uiRoot = document.getElementById('ui-root');
  const { scene, renderer } = createScene(canvas);
  const camera = new CameraController(renderer);
  const bloom = new BloomCompositor(renderer, scene, camera.camera);
  const graphState = new GraphState();
  const layout = new LayoutEngine();

  StageRegions.create(scene);
  KPIStrip.init(uiRoot);
  ReplayControls.init(uiRoot);
  DetailPanel.init(uiRoot);
  SearchBar.init(uiRoot);

  const processEvent = wireEventProcessor(graphState, scene, layout);
  const events = await fetchTraceData();

  ReplayControls.setEvents(events);
  ReplayControls.onEvent((event) => processEvent(event));

  attachResizeHandler(renderer, camera, bloom);
  attachRaycastHandler(renderer, camera.camera, scene, graphState);
  createRenderLoop(bloom, camera, scene, layout, graphState)();
}

// ---------------------------------------------------------------------------
// Data fetching
// ---------------------------------------------------------------------------

/** @returns {Promise<Array<object>>} Parsed event array from server. */
async function fetchTraceData() {
  const res = await fetch(TRACE_ENDPOINT);
  if (!res.ok) {
    console.error(`Trace fetch failed: ${res.status} ${res.statusText}`);
    return [];
  }
  return res.json();
}

// ---------------------------------------------------------------------------
// Render loop
// ---------------------------------------------------------------------------

/** Returns a self-scheduling render tick function. */
function createRenderLoop(compositor, camera, scene, layout, graphState) {
  return function tick() {
    requestAnimationFrame(tick);
    camera.update();
    layout.tick(DELTA_TIME);
    syncNodePositions(graphState, layout);
    syncEdgePositions(graphState);
    compositor.render(scene, camera.camera);
  };
}

/** Copy layout-computed positions onto Three.js node meshes. */
function syncNodePositions(graphState, layout) {
  for (const node of graphState.getAllNodes()) {
    const pos = layout.getPosition(node.id);
    if (pos && node.mesh) {
      node.mesh.position.copy(pos);
      node.position = { x: pos.x, y: pos.y, z: pos.z };
    }
  }
}

/** Update edge line geometries to track their endpoint nodes. */
function syncEdgePositions(graphState) {
  for (const edge of graphState.getAllEdges()) {
    if (!edge.line) {
      continue;
    }
    const src = graphState.getNode(edge.source);
    const tgt = graphState.getNode(edge.target);
    if (src && tgt) {
      updateEdge(edge.line, src.position, tgt.position);
    }
  }
}

// ---------------------------------------------------------------------------
// Event processing wiring
// ---------------------------------------------------------------------------

/**
 * Wire EventProcessor callbacks to mutate graph, scene, and layout.
 * @returns {function} A function that accepts a raw event and processes it.
 */
function wireEventProcessor(graphState, scene, layout) {
  EventProcessor.on('onNodeCreated', (data) => {
    handleNodeCreated(data, graphState, scene, layout);
  });
  EventProcessor.on('onNodeUpdated', (data) => {
    handleNodeUpdated(data, graphState);
  });
  EventProcessor.on('onEdgeCreated', (data) => {
    handleEdgeCreated(data, graphState, scene, layout);
  });
  return (event) => EventProcessor.processEvent(event);
}

/** Create a Three.js mesh for a new node and register in layout. */
function handleNodeCreated(data, graphState, scene, layout) {
  const node = graphState.addNode(data);
  const mesh = createNode(data);
  node.mesh = mesh;
  scene.add(mesh);
  layout.addNode(node.id, node.stageId);
}

/** Apply status updates to the graph model and mesh material. */
function handleNodeUpdated(data, graphState) {
  const node = graphState.updateNode(data.id, data.updates);
  if (node && node.mesh && data.updates.status) {
    updateNodeStatus(node.mesh, data.updates.status);
  }
}

/** Create a Three.js line for a new edge and register in layout. */
function handleEdgeCreated(data, graphState, scene, layout) {
  const edgeId = `${data.source}-${data.target}`;
  const edgeRecord = graphState.addEdge({ id: edgeId, ...data });
  const srcNode = graphState.getNode(data.source);
  const tgtNode = graphState.getNode(data.target);
  const srcPos = srcNode ? srcNode.position : { x: 0, y: 0, z: 0 };
  const tgtPos = tgtNode ? tgtNode.position : { x: 0, y: 0, z: 0 };
  const line = createEdge({ id: edgeId, ...data }, srcPos, tgtPos);
  edgeRecord.line = line;
  scene.add(line);
  layout.addEdge(data.source, data.target);
}

// ---------------------------------------------------------------------------
// Resize handling
// ---------------------------------------------------------------------------

/** Attach a window resize handler for renderer, camera, and bloom. */
function attachResizeHandler(renderer, camera, bloom) {
  function onResize() {
    const w = window.innerWidth;
    const h = window.innerHeight;
    renderer.setSize(w, h);
    camera.resize(w, h);
    bloom.resize(w, h);
  }
  window.addEventListener('resize', onResize);
  onResize();
}

// ---------------------------------------------------------------------------
// Raycasting — click/hover for node selection
// ---------------------------------------------------------------------------

/** Attach mouse handlers for click-to-select and hover cursor. */
function attachRaycastHandler(renderer, camera, scene, graphState) {
  const raycaster = new Raycaster();
  const pointer = new Vector2();
  const dom = renderer.domElement;

  dom.addEventListener('click', (event) => {
    updatePointer(event, pointer, dom);
    const node = raycastNode(raycaster, pointer, camera, scene, graphState);
    if (node) {
      DetailPanel.show(node);
    }
  });

  dom.addEventListener('pointermove', (event) => {
    updatePointer(event, pointer, dom);
    const hit = raycastNode(raycaster, pointer, camera, scene, graphState);
    dom.style.cursor = hit ? 'pointer' : 'default';
  });
}

/** Convert a mouse event to normalized device coordinates. */
function updatePointer(event, pointer, domElement) {
  const rect = domElement.getBoundingClientRect();
  pointer.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
  pointer.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;
}

/** Raycast into the scene, return the first intersected node's data. */
function raycastNode(raycaster, pointer, camera, scene, graphState) {
  raycaster.setFromCamera(pointer, camera);
  const intersects = raycaster.intersectObjects(scene.children, true);
  for (const hit of intersects) {
    const group = findNodeGroup(hit.object);
    if (group) {
      return graphState.getNode(group.userData.nodeId) ?? null;
    }
  }
  return null;
}

/** Walk up the object hierarchy to find the parent Group tagged as a node. */
function findNodeGroup(object) {
  let current = object;
  while (current) {
    if (current.userData && current.userData.nodeId) {
      return current;
    }
    current = current.parent;
  }
  return null;
}

// ---------------------------------------------------------------------------
// Start
// ---------------------------------------------------------------------------

boot();
