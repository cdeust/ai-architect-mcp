const EVENT_TYPES = {
  STAGE_START: "stage_start",
  STAGE_COMPLETE: "stage_complete",
  TOOL_CALL: "tool_call",
  TOOL_RESULT: "tool_result",
  NODE_CREATED: "node_created",
  NODE_UPDATED: "node_updated",
  EDGE_CREATED: "edge_created",
  GATE_CHECK: "gate_check",
  GATE_RESULT: "gate_result",
  HOR_RULE: "hor_rule",
  OODA_CHECKPOINT: "ooda_checkpoint",
  ERROR: "error",
  ARTIFACT_PRODUCED: "artifact_produced",
  CONFIDENCE_UPDATE: "confidence_update",
};

const eventHistory = [];
const callbacks = {
  onNodeCreated: [],
  onNodeUpdated: [],
  onStageTransition: [],
  onGateResult: [],
  onEdgeCreated: [],
  onError: [],
};

function emit(callbackName, data) {
  const listeners = callbacks[callbackName];
  if (!listeners) {
    return;
  }
  for (const listener of listeners) {
    listener(data);
  }
}

function handleStageStart(event) {
  const { stage_id, stage_name, timestamp } = event.data;
  emit("onStageTransition", {
    stageId: stage_id,
    stageName: stage_name,
    status: "started",
    timestamp,
  });
  return {
    mutation: "stage_activate",
    stageId: stage_id,
    stageName: stage_name,
  };
}

function handleStageComplete(event) {
  const { stage_id, stage_name, result, timestamp } = event.data;
  emit("onStageTransition", {
    stageId: stage_id,
    stageName: stage_name,
    status: "completed",
    result,
    timestamp,
  });
  return {
    mutation: "stage_complete",
    stageId: stage_id,
    result,
  };
}

function handleNodeCreated(event) {
  const { node_id, node_type, stage_id, label, metadata } = event.data;
  const nodeData = {
    id: node_id,
    type: node_type,
    stageId: stage_id,
    label,
    metadata: metadata || {},
  };
  emit("onNodeCreated", nodeData);
  return { mutation: "add_node", node: nodeData };
}

function handleNodeUpdated(event) {
  const { node_id, updates } = event.data;
  const updateData = { id: node_id, updates };
  emit("onNodeUpdated", updateData);
  return { mutation: "update_node", nodeId: node_id, updates };
}

function handleEdgeCreated(event) {
  const { source_id, target_id, edge_type, label } = event.data;
  const edgeData = {
    source: source_id,
    target: target_id,
    type: edge_type,
    label,
  };
  emit("onEdgeCreated", edgeData);
  return { mutation: "add_edge", edge: edgeData };
}

function handleToolCall(event) {
  const { tool_name, stage_id, args, timestamp } = event.data;
  const nodeData = {
    id: `tool_${tool_name}_${timestamp}`,
    type: "tool",
    stageId: stage_id,
    label: tool_name,
    metadata: { args, status: "running", startTime: timestamp },
  };
  emit("onNodeCreated", nodeData);
  return { mutation: "add_node", node: nodeData };
}

function handleToolResult(event) {
  const { tool_name, stage_id, result, duration, timestamp } = event.data;
  const updates = {
    status: result.success ? "completed" : "failed",
    duration,
    result,
    endTime: timestamp,
  };
  emit("onNodeUpdated", {
    id: `tool_${tool_name}_${event.data.start_timestamp}`,
    updates,
  });
  return {
    mutation: "update_node",
    nodeId: `tool_${tool_name}_${event.data.start_timestamp}`,
    updates,
  };
}

function handleGateResult(event) {
  const { gate_name, stage_id, passed, reason, scores } = event.data;
  const gateData = {
    gateName: gate_name,
    stageId: stage_id,
    passed,
    reason,
    scores,
  };
  emit("onGateResult", gateData);
  return { mutation: "gate_result", gate: gateData };
}

function handleHorRule(event) {
  const { rule_id, rule_name, passed, category, details } = event.data;
  return {
    mutation: "add_node",
    node: {
      id: `hor_${rule_id}`,
      type: "hor_rule",
      label: rule_name,
      metadata: { passed, category, details },
    },
  };
}

function handleError(event) {
  const { error_type, message, stage_id, recoverable } = event.data;
  const errorData = {
    id: `error_${Date.now()}`,
    type: "error",
    stageId: stage_id,
    label: error_type,
    metadata: { message, recoverable },
  };
  emit("onError", errorData);
  return { mutation: "add_node", node: errorData };
}

function handleArtifact(event) {
  const { artifact_id, artifact_type, stage_id, label } = event.data;
  return {
    mutation: "add_node",
    node: {
      id: artifact_id,
      type: "artifact",
      stageId: stage_id,
      label: label || artifact_type,
      metadata: { artifactType: artifact_type },
    },
  };
}

const DISPATCH_MAP = {
  [EVENT_TYPES.STAGE_START]: handleStageStart,
  [EVENT_TYPES.STAGE_COMPLETE]: handleStageComplete,
  [EVENT_TYPES.NODE_CREATED]: handleNodeCreated,
  [EVENT_TYPES.NODE_UPDATED]: handleNodeUpdated,
  [EVENT_TYPES.EDGE_CREATED]: handleEdgeCreated,
  [EVENT_TYPES.TOOL_CALL]: handleToolCall,
  [EVENT_TYPES.TOOL_RESULT]: handleToolResult,
  [EVENT_TYPES.GATE_CHECK]: handleGateResult,
  [EVENT_TYPES.GATE_RESULT]: handleGateResult,
  [EVENT_TYPES.HOR_RULE]: handleHorRule,
  [EVENT_TYPES.ERROR]: handleError,
  [EVENT_TYPES.ARTIFACT_PRODUCED]: handleArtifact,
};

export function processEvent(event) {
  const handler = DISPATCH_MAP[event.event_type];
  if (!handler) {
    console.warn(`Unknown event type: ${event.event_type}`);
    return null;
  }
  eventHistory.push({ ...event, receivedAt: Date.now() });
  return handler(event);
}

export function on(callbackName, listener) {
  if (!callbacks[callbackName]) {
    callbacks[callbackName] = [];
  }
  callbacks[callbackName].push(listener);
}

export function off(callbackName, listener) {
  const listeners = callbacks[callbackName];
  if (!listeners) {
    return;
  }
  const index = listeners.indexOf(listener);
  if (index !== -1) {
    listeners.splice(index, 1);
  }
}

export function getHistory() {
  return [...eventHistory];
}

export function clearHistory() {
  eventHistory.length = 0;
}

export { EVENT_TYPES };
