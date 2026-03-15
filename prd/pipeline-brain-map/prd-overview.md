# Pipeline Brain-Map — Product Requirements Document

**Version:** 0.1
**Author:** Clément Deust
**Date:** 2026-03-15
**Status:** Draft
**Epic:** Pipeline Observability

---

## 1. Vision

Pipeline Brain-Map is a real-time neural-network visualization that renders AI Architect's 11-stage pipeline as an interactive 3D graph. Every file processed, every decision made, every gate passed or failed appears as a living node in a force-directed network — allowing users to watch the pipeline think, identify processing patterns, and replay past runs for debugging and optimization.

The system inherits the visual language and cyberpunk aesthetic of Memory Monitor (Three.js, bloom shaders, Divergent-inspired circuit traces) and extends it with pipeline-specific semantics: stage regions, finding threads, gate indicators, verification pulses, and temporal flow.

## 2. Problem Statement

AI Architect's pipeline processes findings through 11 stages autonomously. Today, observability is limited to log output and HandoffDocuments — text-heavy, sequential, and impossible to scan for patterns across parallel findings. Users cannot answer questions like:

- Which stage is bottlenecking my current run?
- How do findings from the same source relate to each other as they diverge through the pipeline?
- What verification rules triggered most often, and on which finding types?
- When a gate blocks, what upstream signals contributed?
- How does the current run compare structurally to past successful runs?

Pipeline Brain-Map makes these patterns visible by mapping pipeline execution to a spatial, interactive graph where structure and flow reveal what text logs hide.

## 3. Target Users

**Primary:** The pipeline operator — the person running AI Architect on a codebase. They need to understand what the pipeline is doing now, why it made specific decisions, and where to intervene when things go wrong.

**Secondary:** The pipeline developer — someone working on AI Architect itself. They need to see how stage changes affect execution patterns, identify bottleneck shifts, and validate that new stages integrate correctly with the graph topology.

## 4. Core Concepts

### 4.1 Node Taxonomy

Every entity in the pipeline becomes a graph node. Seven node types, each with a distinct visual identity:

| Node Type | Source | Visual | Color | Shape |
|-----------|--------|--------|-------|-------|
| **Finding** | Stage 1 Discovery | Primary entity, largest radius | Cyan `#00d2ff` | Sphere |
| **Stage Gate** | Stages 0–10 | Checkpoint markers | Green `#26de81` (pass) / Red `#ff4757` (fail) / Amber `#ffa502` (retry) | Octahedron |
| **Artifact** | StageContext saves | Data products of each stage | Purple `#a55eea` | Icosahedron |
| **Tool Call** | MCP tool invocations | Operational actions | Orange `#ff6b35` | Cube |
| **Verification Rule** | Stage 7 HOR rules | Deterministic checks | White `#dfe6e9` | Tetrahedron |
| **Decision Point** | OODA checkpoints | Claude's judgment moments | Magenta `#ff4081` | Torus |
| **Source Signal** | Stage 1 inputs | Raw inputs (files, issues, etc.) | Teal `#00cec9` | Diamond |

### 4.2 Edge Taxonomy

Edges represent relationships and data flow between nodes. Five edge types:

| Edge Type | Meaning | Visual | Weight Factors |
|-----------|---------|--------|----------------|
| **Stage Flow** | Finding progresses through a stage | Solid cyan line, animated particles | Always 1.0 (structural) |
| **Data Dependency** | Artifact consumed by downstream stage | Dashed purple line | Inverse distance in stages |
| **Tool Invocation** | Stage calls an MCP tool | Thin orange pulse | Duration of tool call |
| **Verification Link** | HOR rule evaluates an artifact | White flash on pass, red flash on fail | Rule weight from HOR engine |
| **Causal Chain** | Decision at checkpoint X caused action Y | Magenta dotted line | Confidence score from OODA |

### 4.3 Spatial Layout

The graph uses a **stage-gravity** force-directed layout: 11 gravitational wells (one per stage) pull nodes toward their stage's region while inter-node forces prevent overlap. This creates organic clusters that respect pipeline structure without imposing rigid grid placement.

Stage regions are arranged in a gentle arc (not a straight line) to use 3D depth — early stages (0–3) curve from bottom-left, mid stages (4–7) occupy the center-top, and late stages (8–10) descend to the right. This arc maps to how users scan: left-to-right for progression, up for complexity peaks (PRD + Implementation), down for resolution.

Parallel findings occupy parallel planes within each stage region, creating visible "lanes" that show concurrent execution without Z-fighting.

## 5. Functional Requirements

### 5.1 Live Mode

**FR-1:** The system connects to a running AI Architect MCP server instance and subscribes to pipeline events via a new `ai_architect_pipeline_events` SSE (Server-Sent Events) stream.

**FR-2:** When a new finding enters Stage 1, a Finding node materializes at the Discovery region with a spawn animation (scale from 0 → 1 with bloom flash).

**FR-3:** As the finding progresses through stages, an animated particle trail connects its current position to its previous stage, and the node translates smoothly to the new stage region (400ms ease-out).

**FR-4:** Tool calls appear as ephemeral cube nodes that spawn at the calling stage, pulse during execution, and fade after completion (1s decay). High-duration tool calls persist longer.

**FR-5:** Gate pass/fail events trigger a visual gate indicator: a brief octahedral flash (green/red/amber) at the stage boundary. Failed gates emit a shockwave ring that highlights the blocking condition in the detail panel.

**FR-6:** Verification in Stage 7 renders as a rapid-fire sequence of tetrahedra appearing along the finding's verification chain, each flashing white (pass) or red (fail) as HOR rules evaluate.

**FR-7:** OODA decision points appear as magenta torus nodes. When Claude makes a judgment call (retry vs. proceed vs. escalate), the torus pulses and a causal-chain edge connects to the resulting action.

**FR-8:** Multiple findings running in parallel are visible simultaneously, each with its own color variation (hue-shifted from the base Finding cyan) to distinguish threads.

### 5.2 Replay Mode

**FR-9:** After a pipeline run completes, the full execution trace is serialized to a `brain-trace.jsonl` file in the run's output directory. Each line is a timestamped event.

**FR-10:** Replay mode loads a `brain-trace.jsonl` and renders the execution step-by-step with controllable playback: play, pause, step-forward, step-back, speed (0.5x / 1x / 2x / 5x / 10x).

**FR-11:** A timeline scrubber at the bottom shows the full run duration with stage-colored segments. Clicking anywhere jumps to that point in time.

**FR-12:** Replay mode supports side-by-side comparison: load two traces and render them in split viewports. Structural differences (extra nodes, missing edges, divergent paths) are highlighted with a diff overlay.

**FR-13:** Replay mode generates a summary heatmap: which stages consumed the most time, which HOR rules fired most, which tool calls were most frequent. This surfaces bottleneck patterns without requiring manual inspection.

### 5.3 Interaction

**FR-14:** Click any node to open a detail panel (right slide-out, matching Memory Monitor's glassmorphism style). Contents depend on node type:
- **Finding:** Name, source, current stage, all accumulated artifacts (progressive disclosure)
- **Stage Gate:** Pass/fail status, blocking conditions, retry count
- **Artifact:** Full content with syntax highlighting (PRDs in markdown, code in language-appropriate highlighting)
- **Tool Call:** Tool name, input parameters, output, duration, error (if any)
- **Verification Rule:** Rule ID, category (architecture/quality/security/etc.), pass/fail, evidence
- **Decision Point:** OODA phase, options considered, chosen action, confidence

**FR-15:** Hover any node to show a tooltip with name, type, stage, and timestamp.

**FR-16:** Search/filter bar in the header supports: text search across node names/content, filter by node type, filter by stage, filter by finding ID, filter by pass/fail status.

**FR-17:** Keyboard shortcuts: `T` toggle timeline/cluster layout, `A` analytics dashboard, `Space` play/pause (replay), `←/→` step (replay), `1-9,0` jump to stage, `F` fullscreen, `R` reset camera.

### 5.4 Analytics Dashboard

**FR-18:** `A` key opens a left slide-out analytics panel with six charts (mirroring Memory Monitor's analytics pattern):

1. **Stage Duration Heatmap** — 11 columns (stages) × N rows (findings), cell color = time spent
2. **Gate Success Rate** — bar chart per stage showing pass/fail/retry ratios
3. **HOR Rule Distribution** — donut chart of rule categories (architecture, quality, security, observability, resilience, structural, engine)
4. **Tool Call Frequency** — bar chart of most-called tools
5. **Finding Throughput Timeline** — line chart of findings entering/exiting the pipeline over time
6. **Verification Coverage** — radar chart showing coverage across the 7 HOR categories

**FR-19:** KPI strip at the top of analytics: Active Findings, Completed, Blocked, Avg Stage Duration, Gate Pass Rate, HOR Coverage %.

## 6. Data Model

### 6.1 Pipeline Event Schema

Every pipeline event that feeds the visualization:

```
PipelineEvent {
  eventId:      string    // UUID
  timestamp:    ISO-8601  // When the event occurred
  runId:        string    // Pipeline run identifier
  findingId:    string    // Finding being processed
  eventType:    enum      // FINDING_CREATED | STAGE_ENTERED | STAGE_EXITED |
                          // GATE_EVALUATED | TOOL_CALLED | TOOL_COMPLETED |
                          // HOR_RULE_EVALUATED | OODA_CHECKPOINT | ARTIFACT_SAVED |
                          // FINDING_COMPLETED | FINDING_BLOCKED | ERROR
  stageId:      int       // 0–10
  payload:      object    // Event-specific data (tool name, rule ID, gate result, etc.)
}
```

### 6.2 Graph Node Schema

```
GraphNode {
  id:           string    // Derived from eventId or composite key
  type:         enum      // FINDING | STAGE_GATE | ARTIFACT | TOOL_CALL |
                          // VERIFICATION_RULE | DECISION_POINT | SOURCE_SIGNAL
  label:        string    // Display name
  stageId:      int       // Stage affinity for layout gravity
  findingId:    string    // Parent finding thread
  timestamp:    ISO-8601  // Creation time
  status:       enum      // ACTIVE | COMPLETED | FAILED | EPHEMERAL
  metadata:     object    // Type-specific fields
  position:     vec3      // Computed by force-directed layout
  size:         float     // Based on connection count + importance
  glow:         float     // Bloom intensity (0.0–1.0)
}
```

### 6.3 Graph Edge Schema

```
GraphEdge {
  id:           string
  source:       string    // Source node ID
  target:       string    // Target node ID
  type:         enum      // STAGE_FLOW | DATA_DEPENDENCY | TOOL_INVOCATION |
                          // VERIFICATION_LINK | CAUSAL_CHAIN
  weight:       float     // 0.0–1.0, affects visual thickness and opacity
  animated:     boolean   // Whether particles flow along this edge
  timestamp:    ISO-8601
}
```

### 6.4 Brain Trace Format

Persistent format for replay. Each line in `brain-trace.jsonl`:

```
{ "v": 1, "event": <PipelineEvent>, "graphOps": [<AddNode|RemoveNode|AddEdge|UpdateNode>] }
```

The `graphOps` array contains the exact graph mutations this event produces, enabling deterministic replay without re-computing layout decisions.

## 7. Technical Architecture

### 7.1 System Boundary

Pipeline Brain-Map has three components, following AI Architect's own layer separation:

1. **Event Emitter** (Python, inside AI Architect MCP server) — Instruments the pipeline to emit `PipelineEvent` objects at every significant moment. Lives in `mcp/ai_architect_mcp/_observability/`. Emits via SSE endpoint and writes to `brain-trace.jsonl`.

2. **Graph Engine** (Node.js MCP server, separate process) — Receives events, maintains the graph state, computes force-directed layout, serves the UI. Follows Memory Monitor's zero-dependency pattern. Exposes MCP tools for programmatic access.

3. **Visualization UI** (Single HTML file, Three.js) — Renders the 3D scene. Inherits Memory Monitor's visual stack (Three.js 0.137.0, OrbitControls, UnrealBloomPass, custom shaders). Connected to the Graph Engine via injected data + API endpoints.

### 7.2 Event Emitter Integration

The Event Emitter hooks into AI Architect at five instrumentation points:

1. **StageContext.save()** — After every artifact save, emit `ARTIFACT_SAVED` with stage_id, finding_id, and artifact summary.
2. **Tool dispatch** — Before/after every MCP tool call, emit `TOOL_CALLED` and `TOOL_COMPLETED` with tool name, duration, and result summary.
3. **HOR Rule Engine** — After every rule evaluation in Stage 7, emit `HOR_RULE_EVALUATED` with rule ID, category, and pass/fail.
4. **Gate evaluation** — At every stage boundary, emit `GATE_EVALUATED` with stage_id, finding_id, result, and blocking conditions.
5. **OODA checkpoints** — At every OODA checkpoint in every skill, emit `OODA_CHECKPOINT` with phase, options, chosen action.

The emitter is a Protocol-based port (`ObservabilityPort`) with two adapters: `SSEObservabilityAdapter` (live streaming) and `FileObservabilityAdapter` (brain-trace.jsonl persistence). Both run simultaneously.

### 7.3 Graph Engine

The Graph Engine is a standalone Node.js process that:

- Subscribes to the Event Emitter's SSE stream (live mode)
- Loads `brain-trace.jsonl` files (replay mode)
- Maintains an in-memory graph (nodes + edges)
- Runs a simplified force-directed simulation with stage-gravity wells
- Serves the UI on a dynamic port with data injection
- Exposes MCP tools: `get_pipeline_graph`, `get_pipeline_stats`, `open_pipeline_visualization`, `search_pipeline_events`, `replay_trace`

The engine reuses Memory Monitor's architecture: zero-dependency Node.js, stdio JSON-RPC 2.0, lazy caching, auto-close on idle.

### 7.4 Visualization UI

Single `index.html` file inheriting Memory Monitor's entire visual stack:

- **Scene:** Dark cyberpunk (`#030508`), dual point lights (cyan + magenta), bloom compositor
- **Nodes:** Geometry per type (sphere, octahedron, cube, etc.), size by connection count, glow by importance
- **Edges:** Color by type, opacity by weight, animated particles on high-weight edges
- **Layout:** Stage-gravity force-directed with arc arrangement
- **Panels:** Header (search + filters + stats), detail panel (right slide-out), analytics (left slide-out)
- **Replay controls:** Timeline scrubber, playback speed, step controls

New visual elements beyond Memory Monitor:

- **Stage regions:** Translucent bounding volumes (convex hulls) with stage labels, colored by stage identity
- **Finding threads:** Color-coded trails that persist as a finding moves through stages, creating visible paths
- **Gate pulses:** Shockwave rings at stage boundaries on pass/fail
- **Verification cascade:** Rapid-fire tetrahedra sequence in Stage 7
- **Particle streams:** Data flow particles along Stage Flow edges, speed proportional to processing rate

### 7.5 Connection to Memory Monitor

Pipeline Brain-Map and Memory Monitor occupy adjacent conceptual spaces: Memory Monitor shows what Claude remembers across sessions; Pipeline Brain-Map shows what Claude is doing within a pipeline run. A future integration point: cross-reference edges between Memory Monitor's memory nodes and Pipeline Brain-Map's finding nodes when a pipeline run references or creates memories.

## 8. Integration Points

### 8.1 AI Architect MCP Server

New module: `mcp/ai_architect_mcp/_observability/`

| File | Purpose |
|------|---------|
| `observability_port.py` | Protocol defining the `ObservabilityPort` interface |
| `sse_adapter.py` | SSE streaming adapter (live mode) |
| `file_adapter.py` | JSONL file writer adapter (replay persistence) |
| `event_types.py` | Pydantic models for all `PipelineEvent` types |
| `instrumentation.py` | Decorator/mixin that instruments StageContext, tool dispatch, HOR engine, and gates |

Registration: The `ObservabilityPort` is added to `ports.py` and injected via `composition_root.py`, following the existing hexagonal pattern.

### 8.2 Pipeline Brain-Map MCP Server

New project: `pipeline-brain-map/` (sibling to `memory-monitor/`)

| File | Purpose |
|------|---------|
| `mcp-server/index.js` | Graph engine + MCP server |
| `ui/index.html` | 3D visualization |
| `.mcp.json` | MCP configuration |
| `scripts/setup.sh` | Installation |
| `skills/pipeline-brain-map/SKILL.md` | Skill definition |

MCP Tools (8 tools):

| Tool | Purpose |
|------|---------|
| `get_pipeline_graph` | Current graph state (nodes + edges), optionally filtered |
| `get_pipeline_stats` | Summary: findings by stage, gate rates, tool frequency |
| `open_pipeline_visualization` | Launch browser UI with current/replay data |
| `search_pipeline_events` | Full-text search across events with filters |
| `replay_trace` | Load a brain-trace.jsonl and open in replay mode |
| `compare_traces` | Side-by-side diff of two brain traces |
| `get_stage_detail` | Deep dive on a specific stage for a specific finding |
| `export_analytics` | Export analytics data as JSON for external tools |

### 8.3 Shared Visual Library

Memory Monitor and Pipeline Brain-Map share the same visual DNA. Extract shared utilities into a `shared/` module:

- `scene-setup.js` — Three.js scene, lights, bloom, grid shader
- `glassmorphism.css` — Panel styles, animations, transitions
- `chart-renderer.js` — Analytics chart drawing (heatmap, donut, bar, radar)
- `force-layout.js` — Force-directed graph simulation
- `node-geometry.js` — Mesh generation for all node shapes

This prevents divergence between the two visualizations while allowing each to extend with domain-specific rendering.

## 9. Non-Functional Requirements

| Requirement | Target | Measurement |
|-------------|--------|-------------|
| **Render FPS** | ≥ 30 fps with 500 nodes, 2000 edges | Chrome DevTools FPS meter |
| **Event latency** | < 200ms from pipeline event → visual update | Timestamp diff (event.timestamp vs render.timestamp) |
| **Replay load time** | < 3s for 10,000 event trace | Performance.now() around trace load |
| **Memory ceiling** | < 512MB for graph engine process | Node.js process.memoryUsage() |
| **File size** | UI < 5,000 lines, Server < 3,000 lines | wc -l |
| **Zero dependencies** | Node.js standard library only (server) | package.json has no dependencies |
| **Browser support** | Chrome 100+, Safari 16+, Firefox 100+ | WebGL2 required |
| **Idle shutdown** | Auto-close after 5 min idle | Timer from last interaction |

## 10. Acceptance Criteria

### 10.1 Live Mode

- [ ] Connect to running AI Architect and see findings appear as they enter Stage 1
- [ ] Watch a finding traverse all 11 stages with smooth animations
- [ ] See parallel findings running simultaneously with distinct visual threads
- [ ] Click any node and see contextually appropriate detail
- [ ] See gate pass/fail indicators at stage boundaries in real-time
- [ ] See Stage 7 verification cascade render as HOR rules evaluate

### 10.2 Replay Mode

- [ ] Load a brain-trace.jsonl and see the full run reconstruct
- [ ] Control playback (play, pause, step, speed) with keyboard and UI
- [ ] Scrub the timeline to jump to any point in the run
- [ ] Compare two traces side-by-side with diff highlighting
- [ ] Generate analytics summary from completed trace

### 10.3 Analytics

- [ ] Open analytics dashboard with 6 charts populated from current data
- [ ] KPI strip shows accurate real-time metrics
- [ ] Charts update live during live mode
- [ ] Export analytics data as JSON

### 10.4 Integration

- [ ] AI Architect pipeline runs unaffected by observability instrumentation (< 5% overhead)
- [ ] Brain-trace.jsonl files are valid JSONL and replayable
- [ ] MCP tools are discoverable and documented
- [ ] Setup script registers the server in Claude's MCP config

## 11. Phased Delivery

### Phase 1 — Event Infrastructure (Week 1–2)

Instrument AI Architect's pipeline to emit events. Build the `_observability` module with both adapters. Write brain-trace.jsonl for a real pipeline run. Validate event completeness.

Deliverables: `ObservabilityPort`, `SSEObservabilityAdapter`, `FileObservabilityAdapter`, event Pydantic models, integration tests.

### Phase 2 — Graph Engine + Replay (Week 3–4)

Build the Node.js graph engine. Implement JSONL loading, graph construction, force-directed layout with stage gravity, and MCP tool exposure. Replay mode first (simpler: no streaming).

Deliverables: `mcp-server/index.js`, 8 MCP tools, brain-trace replay logic, layout algorithm.

### Phase 3 — Visualization UI (Week 5–7)

Build the Three.js visualization. Start from Memory Monitor's visual foundation. Add stage regions, finding threads, gate pulses, verification cascade, replay controls, analytics dashboard.

Deliverables: `ui/index.html`, shared visual library extraction, all 7 node geometries, 5 edge types, analytics charts.

### Phase 4 — Live Mode + Polish (Week 8–9)

Connect the UI to the SSE stream for live updates. Implement real-time graph mutation, smooth animation transitions, and live analytics. Performance optimization pass. Side-by-side trace comparison.

Deliverables: SSE client, live graph updates, comparison mode, performance profiling.

### Phase 5 — Memory Monitor Cross-Reference (Week 10)

Connect Pipeline Brain-Map findings to Memory Monitor memories. When a pipeline run creates or references a memory, show cross-reference edges between the two visualizations. Unified search across both graphs.

Deliverables: Cross-reference protocol, unified search, shared index format.

## 12. Open Questions

1. **Event granularity:** Should every individual HOR rule evaluation be an event, or should Stage 7 emit a single summary event? Individual rules give more visual detail but produce ~64 events per finding per run.

2. **Graph persistence:** Should the graph state (node positions, layout) be persisted between sessions, or recomputed on every load? Persistence gives consistent spatial memory; recomputation adapts to new data.

3. **SwiftUI client:** Should the Mac app get a native Pipeline Brain-Map view (SceneKit), or should it embed the web visualization in a WKWebView? Native is smoother but doubles the rendering codebase.

4. **Event buffer:** In live mode, should the graph engine buffer events and batch-render (smoother but delayed), or render each event immediately (responsive but potentially janky)?

5. **Privacy:** Pipeline events may contain source code snippets in artifact summaries. Should the brain-trace.jsonl be encrypted at rest? Should sensitive content be redacted in the visualization?

---

*This PRD follows the AI Architect 6-point documentation framework. Each phase deliverable will receive its own decision document with OBSERVATION, PROBLEM, SOLUTION, JUSTIFICATION, REPRODUCIBILITY, and VERIFICATION DATA sections.*
