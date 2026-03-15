# Pipeline Brain-Map — Technical Specification

**Version:** 0.1
**Date:** 2026-03-15

---

## 1. Event Emitter — Instrumentation Layer

### 1.1 ObservabilityPort Protocol

New port in `mcp/ai_architect_mcp/_adapters/ports.py`:

```python
from __future__ import annotations
from typing import Protocol
from ai_architect_mcp._observability.event_types import PipelineEvent

class ObservabilityPort(Protocol):
    """Port for pipeline observability instrumentation."""

    async def emit(self, event: PipelineEvent) -> None:
        """Emit a pipeline event to all registered observers."""
        ...

    async def flush(self) -> None:
        """Flush any buffered events to their destinations."""
        ...

    async def close(self) -> None:
        """Clean up resources."""
        ...
```

### 1.2 Event Type Hierarchy

All events share a base schema and specialize via the `payload` field:

```python
class PipelineEvent(BaseModel):
    event_id: str = Field(default_factory=lambda: str(uuid4()))
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    run_id: str = Field(description="Pipeline run identifier")
    finding_id: str = Field(description="Finding being processed")
    event_type: EventType
    stage_id: int = Field(ge=0, le=10)
    payload: dict[str, Any] = Field(default_factory=dict)

class EventType(str, Enum):
    FINDING_CREATED = "finding_created"
    STAGE_ENTERED = "stage_entered"
    STAGE_EXITED = "stage_exited"
    GATE_EVALUATED = "gate_evaluated"
    TOOL_CALLED = "tool_called"
    TOOL_COMPLETED = "tool_completed"
    HOR_RULE_EVALUATED = "hor_rule_evaluated"
    OODA_CHECKPOINT = "ooda_checkpoint"
    ARTIFACT_SAVED = "artifact_saved"
    FINDING_COMPLETED = "finding_completed"
    FINDING_BLOCKED = "finding_blocked"
    ERROR = "error"
```

### 1.3 Instrumentation Points

Five hooks into the existing codebase, each using the port pattern (no direct coupling):

**Hook 1: StageContext.save()**
```python
# In _context/stage_context.py, after successful store
await self._observability.emit(PipelineEvent(
    run_id=run_id,
    finding_id=finding_id,
    event_type=EventType.ARTIFACT_SAVED,
    stage_id=stage_id,
    payload={"artifact_keys": list(content.keys()), "size_bytes": len(json.dumps(content))}
))
```

**Hook 2: Tool dispatch wrapper**
```python
# Decorator on MCP tool functions
@observe_tool_call(observability_port)
async def ai_architect_some_tool(...):
    ...
# Emits TOOL_CALLED before, TOOL_COMPLETED after, with duration_ms
```

**Hook 3: HOR Rule Engine**
```python
# After each rule evaluation in _verification/hor_rules/engine.py
await observability.emit(PipelineEvent(
    event_type=EventType.HOR_RULE_EVALUATED,
    payload={"rule_id": rule.id, "category": rule.category, "passed": result.passed, "evidence": result.evidence[:200]}
))
```

**Hook 4: Gate evaluation**
```python
# At stage boundaries (orchestrator coordination)
await observability.emit(PipelineEvent(
    event_type=EventType.GATE_EVALUATED,
    payload={"gate_name": gate.name, "result": "pass"|"fail"|"retry", "blocking_conditions": [...], "retry_count": n}
))
```

**Hook 5: OODA checkpoints**
```python
# At every OODA checkpoint in skill execution
await observability.emit(PipelineEvent(
    event_type=EventType.OODA_CHECKPOINT,
    payload={"phase": "observe"|"orient"|"decide"|"act", "options": [...], "chosen": "...", "confidence": 0.85}
))
```

### 1.4 SSE Adapter

```python
class SSEObservabilityAdapter:
    """Streams PipelineEvents as Server-Sent Events over HTTP."""

    def __init__(self, host: str = "127.0.0.1", port: int = 0) -> None:
        self._clients: list[asyncio.StreamWriter] = []
        self._server: asyncio.Server | None = None

    async def emit(self, event: PipelineEvent) -> None:
        data = event.model_dump_json()
        message = f"event: pipeline\ndata: {data}\n\n"
        for client in self._clients:
            client.write(message.encode())
            await client.drain()
```

### 1.5 File Adapter

```python
class FileObservabilityAdapter:
    """Appends PipelineEvents as JSONL for replay."""

    def __init__(self, trace_dir: Path) -> None:
        self._path = trace_dir / "brain-trace.jsonl"
        self._file: IO | None = None

    async def emit(self, event: PipelineEvent) -> None:
        line = json.dumps({"v": 1, "event": event.model_dump()})
        self._file.write(line + "\n")

    async def flush(self) -> None:
        self._file.flush()
```

### 1.6 Composition Root Registration

In `_adapters/composition_root.py`:

```python
observability = CompositeObservabilityAdapter([
    SSEObservabilityAdapter(port=0),
    FileObservabilityAdapter(trace_dir=run_output_dir),
])
container.register(ObservabilityPort, observability)
```

---

## 2. Graph Engine — Node.js MCP Server

### 2.1 Architecture

Follows Memory Monitor's exact architecture: single-file Node.js, zero dependencies, stdio JSON-RPC 2.0.

```
pipeline-brain-map/
├── mcp-server/
│   └── index.js           # Graph engine + MCP server (~2500 lines)
├── ui/
│   └── index.html         # 3D visualization (~3000 lines)
├── shared/                # Extracted from Memory Monitor
│   ├── scene-setup.js     # Three.js boilerplate
│   ├── glassmorphism.css  # Panel styles
│   └── chart-renderer.js  # Analytics charts
├── .mcp.json
├── scripts/setup.sh
└── skills/pipeline-brain-map/SKILL.md
```

### 2.2 Graph State Machine

The engine maintains an in-memory graph that mutates in response to events:

```javascript
const graph = {
  nodes: new Map(),  // nodeId → GraphNode
  edges: new Map(),  // edgeId → GraphEdge
  stageWells: [],    // 11 vec3 positions (arc layout)
  findings: new Map(), // findingId → { color, currentStage, nodeIds }
  runId: null,
  startTime: null,
  eventCount: 0,
};
```

### 2.3 Event → Graph Mutation Mapping

Each `EventType` produces specific graph operations:

| EventType | Graph Ops |
|-----------|-----------|
| `FINDING_CREATED` | AddNode(FINDING), AddNode(SOURCE_SIGNAL), AddEdge(SOURCE→FINDING) |
| `STAGE_ENTERED` | UpdateNode(finding, stageId), AddEdge(STAGE_FLOW, prev→current) |
| `STAGE_EXITED` | AddNode(STAGE_GATE), AddEdge(finding→gate) |
| `GATE_EVALUATED` | UpdateNode(gate, status=pass/fail/retry) |
| `TOOL_CALLED` | AddNode(TOOL_CALL, status=ACTIVE) |
| `TOOL_COMPLETED` | UpdateNode(tool, status=COMPLETED/FAILED), AddEdge(stage→tool) |
| `HOR_RULE_EVALUATED` | AddNode(VERIFICATION_RULE), AddEdge(finding→rule) |
| `OODA_CHECKPOINT` | AddNode(DECISION_POINT), AddEdge(causal chain) |
| `ARTIFACT_SAVED` | AddNode(ARTIFACT), AddEdge(DATA_DEPENDENCY) |
| `FINDING_COMPLETED` | UpdateNode(finding, status=COMPLETED) |
| `FINDING_BLOCKED` | UpdateNode(finding, status=FAILED), highlight blocking path |

### 2.4 Force-Directed Layout with Stage Gravity

The layout algorithm extends a basic Fruchterman-Reingold with gravitational wells:

```javascript
function layoutStep(graph, dt) {
  for (const [id, node] of graph.nodes) {
    // 1. Repulsion from all other nodes (inverse-square)
    let fx = 0, fy = 0, fz = 0;
    for (const [otherId, other] of graph.nodes) {
      if (id === otherId) continue;
      const dx = node.x - other.x, dy = node.y - other.y, dz = node.z - other.z;
      const dist = Math.max(Math.sqrt(dx*dx + dy*dy + dz*dz), 0.1);
      const repulsion = REPULSION_K / (dist * dist);
      fx += (dx / dist) * repulsion;
      fy += (dy / dist) * repulsion;
      fz += (dz / dist) * repulsion;
    }

    // 2. Attraction along edges (Hooke's law)
    for (const edge of getEdges(graph, id)) {
      const other = edge.source === id ? graph.nodes.get(edge.target) : graph.nodes.get(edge.source);
      const dx = other.x - node.x, dy = other.y - node.y, dz = other.z - node.z;
      const dist = Math.sqrt(dx*dx + dy*dy + dz*dz);
      fx += dx * ATTRACTION_K * edge.weight;
      fy += dy * ATTRACTION_K * edge.weight;
      fz += dz * ATTRACTION_K * edge.weight;
    }

    // 3. Stage gravity — pull toward stage well
    const well = graph.stageWells[node.stageId];
    const gdx = well.x - node.x, gdy = well.y - node.y, gdz = well.z - node.z;
    fx += gdx * GRAVITY_K;
    fy += gdy * GRAVITY_K;
    fz += gdz * GRAVITY_K;

    // 4. Apply forces with damping
    node.vx = (node.vx + fx * dt) * DAMPING;
    node.vy = (node.vy + fy * dt) * DAMPING;
    node.vz = (node.vz + fz * dt) * DAMPING;
    node.x += node.vx * dt;
    node.y += node.vy * dt;
    node.z += node.vz * dt;
  }
}
```

Stage wells are arranged on a 3D arc:

```javascript
function computeStageWells() {
  const wells = [];
  for (let i = 0; i <= 10; i++) {
    const t = i / 10;                          // 0.0 → 1.0
    const angle = Math.PI * 0.8 * (t - 0.5);  // -72° → +72°
    const x = Math.sin(angle) * ARC_RADIUS;    // horizontal spread
    const y = Math.cos(angle) * ARC_HEIGHT;    // vertical arc (high in middle)
    const z = (t - 0.5) * DEPTH_SPREAD;        // depth for parallel findings
    wells.push({ x, y, z, stageId: i });
  }
  return wells;
}
```

### 2.5 MCP Tool Definitions

Eight tools, all prefixed `pipeline_brain_map_`:

```javascript
const TOOLS = [
  {
    name: "pipeline_brain_map_get_graph",
    description: "Returns current graph state (nodes + edges). Supports filtering by stage, finding, node type, and time range.",
    inputSchema: {
      type: "object",
      properties: {
        stageId: { type: "integer", minimum: 0, maximum: 10 },
        findingId: { type: "string" },
        nodeType: { type: "string", enum: ["FINDING","STAGE_GATE","ARTIFACT","TOOL_CALL","VERIFICATION_RULE","DECISION_POINT","SOURCE_SIGNAL"] },
        since: { type: "string", description: "ISO-8601 timestamp" },
      }
    }
  },
  // ... (7 more tools as specified in the PRD)
];
```

### 2.6 UI Server

Same pattern as Memory Monitor: HTTP server on port 0, injects graph data as `window.__GRAPH_DATA__`, lazy API endpoints for heavy payloads, 5-minute idle timeout.

New endpoints beyond Memory Monitor:

| Endpoint | Purpose |
|----------|---------|
| `/api/events` | SSE proxy — relays pipeline events to UI |
| `/api/detail/:nodeId` | Full node payload (lazy-loaded on click) |
| `/api/analytics` | Aggregated metrics for dashboard |
| `/api/replay` | Load and serve brain-trace.jsonl |

---

## 3. Visualization — Three.js Rendering

### 3.1 Scene Inheritance from Memory Monitor

Directly reuse:
- Background color (`#030508`), fog settings
- Dual point lights (cyan + magenta)
- Directional light for depth
- UnrealBloomPass with same parameters (strength: 1.5, radius: 0.4, threshold: 0.0)
- JetBrains Mono font, glassmorphism panel CSS
- OrbitControls configuration

### 3.2 New Geometries

Seven node types need distinct Three.js geometries:

```javascript
const GEOMETRIES = {
  FINDING:           new THREE.SphereGeometry(1, 32, 32),
  STAGE_GATE:        new THREE.OctahedronGeometry(0.8),
  ARTIFACT:          new THREE.IcosahedronGeometry(0.6),
  TOOL_CALL:         new THREE.BoxGeometry(0.7, 0.7, 0.7),
  VERIFICATION_RULE: new THREE.TetrahedronGeometry(0.5),
  DECISION_POINT:    new THREE.TorusGeometry(0.5, 0.15, 16, 32),
  SOURCE_SIGNAL:     new THREE.OctahedronGeometry(0.4),  // Diamond = rotated octahedron
};
```

### 3.3 Stage Region Volumes

Each stage has a translucent bounding volume showing its region:

```javascript
function createStageRegion(well, stageId) {
  const geometry = new THREE.SphereGeometry(REGION_RADIUS, 16, 16);
  const material = new THREE.MeshBasicMaterial({
    color: STAGE_COLORS[stageId],
    transparent: true,
    opacity: 0.03,
    wireframe: false,
    depthWrite: false,
  });
  const mesh = new THREE.Mesh(geometry, material);
  mesh.position.set(well.x, well.y, well.z);

  // Stage label (sprite)
  const label = createTextSprite(STAGE_NAMES[stageId], STAGE_COLORS[stageId]);
  label.position.set(well.x, well.y + REGION_RADIUS + 1, well.z);

  return { mesh, label };
}

const STAGE_NAMES = [
  "0: Health", "1: Discovery", "2: Impact", "3: Integration",
  "4: PRD", "5: Review", "6: Implementation", "7: Verification",
  "8: Benchmark", "9: Deployment", "10: Pull Request"
];

const STAGE_COLORS = [
  0x636e72, 0x00d2ff, 0x0984e3, 0x6c5ce7,
  0xa55eea, 0xfd79a8, 0xff6b35, 0xdfe6e9,
  0xffa502, 0x26de81, 0x00cec9
];
```

### 3.4 Animation System

Three animation layers running concurrently:

**Layer 1: Node transitions** — When a finding moves between stages, TWEEN its position from current → new well over 400ms with ease-out.

**Layer 2: Edge particles** — On STAGE_FLOW edges, animate small spheres along the edge path. Particle speed = constant for structural edges, proportional to processing rate for tool invocation edges.

**Layer 3: Event effects** — Ephemeral visual effects triggered by specific events:
- Gate pass: green ripple expanding from gate node (800ms)
- Gate fail: red shockwave ring (1200ms)
- HOR rule pass: white flash on tetrahedron (200ms)
- HOR rule fail: red pulse with lingering glow (600ms)
- Tool call: orange cube scale 0→1→0.8 (spawn), then fade on completion
- OODA decision: magenta torus rotation speed increase (300ms)

### 3.5 Replay Controls

Timeline scrubber at the bottom of the viewport:

```javascript
function createTimelineScrubber(trace) {
  // Canvas-based scrubber
  // X-axis: time (trace start → end)
  // Colored segments per stage (stacked for parallel findings)
  // Playhead: vertical line at current position
  // Click: jump to time
  // Drag: scrub
  // Keyboard: ←/→ = step, Space = play/pause, +/- = speed
}
```

### 3.6 Analytics Charts

Six charts in the left panel, implemented with Canvas 2D (no chart library, matching Memory Monitor):

1. **Stage Duration Heatmap:** `drawHeatmap(stages × findings, durationMs, colorScale)`
2. **Gate Success Rate:** `drawBarChart(stages, {pass, fail, retry}, stackedColors)`
3. **HOR Rule Distribution:** `drawDonutChart(categories, counts, categoryColors)`
4. **Tool Call Frequency:** `drawHorizontalBarChart(toolNames, counts, orange)`
5. **Finding Throughput:** `drawLineChart(timeAxis, {entered, exited}, colors)`
6. **Verification Coverage:** `drawRadarChart(horCategories, coveragePercent)`

---

## 4. File Structure Summary

### New files in AI Architect:

```
mcp/ai_architect_mcp/_observability/
├── __init__.py
├── observability_port.py      # Protocol interface
├── sse_adapter.py             # SSE streaming adapter
├── file_adapter.py            # JSONL file writer
├── event_types.py             # Pydantic event models
├── composite_adapter.py       # Multiplexes to multiple adapters
└── instrumentation.py         # Decorators for instrumenting existing code
```

Plus modifications to:
- `_adapters/ports.py` — Add `ObservabilityPort`
- `_adapters/composition_root.py` — Register observability adapters
- `_context/stage_context.py` — Add emit calls after save
- `_verification/hor_rules/engine.py` — Add emit calls after rule evaluation
- `_tools/*.py` — Wrap tool functions with observability decorator

### New project:

```
pipeline-brain-map/
├── mcp-server/index.js
├── ui/index.html
├── shared/
│   ├── scene-setup.js
│   ├── glassmorphism.css
│   └── chart-renderer.js
├── .mcp.json
├── .claude-plugin/plugin.json
├── scripts/setup.sh
├── skills/pipeline-brain-map/SKILL.md
└── commands/pipeline-brain-map.md
```

---

## 5. Testing Strategy

### Event Emitter Tests

- **Unit:** Each event type produces valid Pydantic models with all required fields
- **Integration:** Pipeline run with instrumentation generates complete brain-trace.jsonl
- **Performance:** Instrumentation adds < 5% overhead (measured via Stage 8 benchmark comparison)
- **Deterministic:** Given the same pipeline inputs, brain-trace.jsonl event sequence is identical (excluding timestamps)

### Graph Engine Tests

- **Unit:** Each event type produces correct graph mutations
- **Layout:** Stage wells compute correct arc positions, force-directed converges within 100 iterations
- **Replay:** Loading a brain-trace.jsonl produces bit-for-bit identical graph state as live ingestion
- **MCP tools:** All 8 tools return valid schemas, handle edge cases (empty graph, single finding, 50 parallel findings)

### Visualization Tests

- **Visual regression:** Screenshot comparison of known graph states
- **Performance:** FPS > 30 with 500 nodes in Chrome
- **Interaction:** Click, hover, search, filter, keyboard shortcuts all functional
- **Replay controls:** Play, pause, step, scrub, speed change all produce correct graph state

---

*This technical specification follows AI Architect's zero-tolerance code standards. All implementations must pass the existing CI pipeline, HOR rules, and security checks before merge.*
