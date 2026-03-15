'use strict';

const { GraphNode } = require('./graph-node.js');
const { GraphEdge } = require('./graph-edge.js');

/**
 * Event type constants matching Python's EventType enum values.
 * Python serializes as lowercase snake_case strings.
 */
const EventType = Object.freeze({
  STAGE_STARTED: 'stage_started',
  STAGE_COMPLETED: 'stage_completed',
  STAGE_FAILED: 'stage_failed',
  TOOL_CALLED: 'tool_called',
  TOOL_COMPLETED: 'tool_completed',
  TOOL_FAILED: 'tool_failed',
  ARTIFACT_SAVED: 'artifact_saved',
  HOR_RULE_EVALUATED: 'hor_rule_evaluated',
  GATE_EVALUATED: 'gate_evaluated',
  OODA_CHECKPOINT: 'ooda_checkpoint',
  CONTEXT_LOADED: 'context_loaded',
  PIPELINE_ERROR: 'pipeline_error',
  THINKING_STEP: 'thinking_step',
  DECISION_MADE: 'decision_made',
});

/** @param {GraphNode} node */
function addNodeMutation(node) {
  return { type: 'addNode', node };
}

/** @param {GraphEdge} edge */
function addEdgeMutation(edge) {
  return { type: 'addEdge', edge };
}

/** @param {string} nodeId @param {object} updates */
function updateNodeMutation(nodeId, updates) {
  return { type: 'updateNode', nodeId, updates };
}

/** @param {string} source @param {string} target @param {string} t */
function eid(source, target, t) {
  return `${source}--${t}--${target}`;
}

/**
 * Maps Python PipelineEvent objects to graph mutations.
 *
 * Events arrive as JSON with snake_case fields matching Python's
 * PipelineEvent model: event_id, event_type, stage_id, tool_name,
 * message, duration_ms, metadata.
 */
class EventMapper {
  constructor() {
    this._handlers = new Map();
    this._registerHandlers();
  }

  _registerHandlers() {
    this._handlers.set(EventType.STAGE_STARTED, (e) => this._onStageStarted(e));
    this._handlers.set(EventType.STAGE_COMPLETED, (e) => this._onStageCompleted(e));
    this._handlers.set(EventType.STAGE_FAILED, (e) => this._onStageFailed(e));
    this._handlers.set(EventType.TOOL_CALLED, (e) => this._onToolCalled(e));
    this._handlers.set(EventType.TOOL_COMPLETED, (e) => this._onToolCompleted(e));
    this._handlers.set(EventType.TOOL_FAILED, (e) => this._onToolFailed(e));
    this._handlers.set(EventType.ARTIFACT_SAVED, (e) => this._onArtifactSaved(e));
    this._handlers.set(EventType.HOR_RULE_EVALUATED, (e) => this._onHorRuleEvaluated(e));
    this._handlers.set(EventType.GATE_EVALUATED, (e) => this._onGateEvaluated(e));
    this._handlers.set(EventType.OODA_CHECKPOINT, (e) => this._onOodaCheckpoint(e));
    this._handlers.set(EventType.CONTEXT_LOADED, (e) => this._onContextLoaded(e));
    this._handlers.set(EventType.PIPELINE_ERROR, (e) => this._onPipelineError(e));
    this._handlers.set(EventType.THINKING_STEP, (e) => this._onThinkingStep(e));
    this._handlers.set(EventType.DECISION_MADE, (e) => this._onDecisionMade(e));
  }

  /**
   * Map a pipeline event to graph mutations.
   *
   * @param {object} event — Python PipelineEvent with snake_case fields
   * @returns {object[]} Array of { type, node/edge/nodeId/updates }
   */
  map(event) {
    if (!event || !event.event_type) {
      throw new Error(
        'Event must have an event_type field — received: ' +
        JSON.stringify(event).slice(0, 100)
      );
    }
    const handler = this._handlers.get(event.event_type);
    if (!handler) {
      throw new Error(`Unknown event type '${event.event_type}'`);
    }
    return handler(event);
  }

  _onStageStarted(event) {
    const nodeId = `stage-${event.stage_id}`;
    const label = event.message || `Stage ${event.stage_id}`;
    const node = new GraphNode(nodeId, 'stage', label, event.stage_id, undefined, 'active');
    const mutations = [addNodeMutation(node)];

    if (event.stage_id > 0) {
      const prevId = `stage-${event.stage_id - 1}`;
      const edge = new GraphEdge(eid(prevId, nodeId, 'data_flow'), prevId, nodeId, 'data_flow', 1.0, true);
      mutations.push(addEdgeMutation(edge));
    }
    return mutations;
  }

  _onStageCompleted(event) {
    return [updateNodeMutation(`stage-${event.stage_id}`, { status: 'completed' })];
  }

  _onStageFailed(event) {
    return [updateNodeMutation(`stage-${event.stage_id}`, { status: 'failed' })];
  }

  _onToolCalled(event) {
    const toolName = event.tool_name || event.event_id;
    const nodeId = `tool-${toolName}`;
    const stageNode = `stage-${event.stage_id}`;
    const node = new GraphNode(nodeId, 'tool', toolName, event.stage_id, undefined, 'active');
    const edge = new GraphEdge(eid(stageNode, nodeId, 'contains'), stageNode, nodeId, 'contains');
    return [addNodeMutation(node), addEdgeMutation(edge)];
  }

  _onToolCompleted(event) {
    const toolName = event.tool_name || event.event_id;
    const updates = { status: 'completed' };
    if (event.duration_ms != null) updates.duration_ms = event.duration_ms;
    return [updateNodeMutation(`tool-${toolName}`, updates)];
  }

  _onToolFailed(event) {
    const toolName = event.tool_name || event.event_id;
    return [updateNodeMutation(`tool-${toolName}`, { status: 'failed' })];
  }

  _onArtifactSaved(event) {
    const findingId = (event.metadata || {}).finding_id || event.event_id;
    const nodeId = `artifact-${findingId}`;
    const stageNode = `stage-${event.stage_id}`;
    const label = event.message || `Artifact ${findingId}`;
    const node = new GraphNode(nodeId, 'artifact', label, event.stage_id, undefined, 'completed');
    const edge = new GraphEdge(eid(stageNode, nodeId, 'triggers'), stageNode, nodeId, 'triggers');
    return [addNodeMutation(node), addEdgeMutation(edge)];
  }

  _onHorRuleEvaluated(event) {
    const meta = event.metadata || {};
    const ruleId = meta.rule_id || event.event_id;
    const ruleName = meta.rule_name || ruleId;
    const passed = meta.passed === 'True';
    const nodeId = `hor-${ruleId}`;
    const stageNode = `stage-${event.stage_id}`;
    const status = passed ? 'completed' : 'failed';
    const node = new GraphNode(nodeId, 'hor_rule', ruleName, event.stage_id, undefined, status);
    const edge = new GraphEdge(eid(stageNode, nodeId, 'contains'), stageNode, nodeId, 'contains');
    return [addNodeMutation(node), addEdgeMutation(edge)];
  }

  _onGateEvaluated(event) {
    const meta = event.metadata || {};
    const gateName = event.tool_name || event.event_id;
    const passed = meta.passed === 'True';
    const nodeId = `gate-${gateName}`;
    const stageNode = `stage-${event.stage_id}`;
    const status = passed ? 'completed' : 'failed';
    const node = new GraphNode(nodeId, 'gate', gateName, event.stage_id, undefined, status);
    const edge = new GraphEdge(eid(stageNode, nodeId, 'triggers'), stageNode, nodeId, 'triggers');
    return [addNodeMutation(node), addEdgeMutation(edge)];
  }

  _onOodaCheckpoint(event) {
    const meta = event.metadata || {};
    const phase = meta.phase || 'unknown';
    const nodeId = `ooda-${event.event_id}`;
    const stageNode = `stage-${event.stage_id}`;
    const label = event.message || `OODA ${phase}`;
    const node = new GraphNode(nodeId, 'ooda', label, event.stage_id, undefined, 'completed');
    const edge = new GraphEdge(eid(stageNode, nodeId, 'contains'), stageNode, nodeId, 'contains');
    return [addNodeMutation(node), addEdgeMutation(edge)];
  }

  _onContextLoaded(event) {
    const sourceStage = (event.metadata || {}).source_stage_id || 0;
    const sourceNode = `stage-${sourceStage}`;
    const currentNode = `stage-${event.stage_id}`;
    const edge = new GraphEdge(eid(sourceNode, currentNode, 'depends_on'), sourceNode, currentNode, 'depends_on');
    return [addEdgeMutation(edge)];
  }

  _onPipelineError(event) {
    const nodeId = `error-${event.event_id}`;
    const stageNode = `stage-${event.stage_id}`;
    const label = event.message || 'Pipeline Error';
    const node = new GraphNode(nodeId, 'error', label, event.stage_id, undefined, 'failed');
    const edge = new GraphEdge(eid(stageNode, nodeId, 'triggers'), stageNode, nodeId, 'triggers');
    return [addNodeMutation(node), addEdgeMutation(edge)];
  }

  _onThinkingStep(event) {
    const meta = event.metadata || {};
    const title = meta.title || 'Thinking';
    const nodeId = `think-${event.event_id}`;
    const stageNode = `stage-${event.stage_id}`;
    const label = event.message || `Thinking: ${title}`;
    const node = new GraphNode(nodeId, 'thinking', label, event.stage_id, undefined, 'completed');
    const edge = new GraphEdge(eid(stageNode, nodeId, 'contains'), stageNode, nodeId, 'contains');
    return [addNodeMutation(node), addEdgeMutation(edge)];
  }

  _onDecisionMade(event) {
    const meta = event.metadata || {};
    const title = meta.title || 'Decision';
    const chosen = meta.chosen || '';
    const nodeId = `decision-${event.event_id}`;
    const stageNode = `stage-${event.stage_id}`;
    const label = event.message || `Decision: ${title} → ${chosen}`;
    const node = new GraphNode(nodeId, 'decision', label, event.stage_id, undefined, 'completed');
    const edge = new GraphEdge(eid(stageNode, nodeId, 'triggers'), stageNode, nodeId, 'triggers');
    return [addNodeMutation(node), addEdgeMutation(edge)];
  }
}

module.exports = { EventMapper, EventType };
