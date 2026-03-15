const PANEL_CLASS = "detail-panel";
const GLASSMORPHISM_CLASS = "glassmorphism";
const VISIBLE_CLASS = "visible";

let panelElement = null;
let contentElement = null;
let currentNodeId = null;

function createPanelDOM() {
  const panel = document.createElement("div");
  panel.className = `${PANEL_CLASS} ${GLASSMORPHISM_CLASS}`;

  const header = document.createElement("div");
  header.className = "detail-panel-header";

  const title = document.createElement("h3");
  title.className = "detail-panel-title";
  title.textContent = "Details";

  const closeBtn = document.createElement("button");
  closeBtn.className = "detail-panel-close";
  closeBtn.textContent = "\u00D7";
  closeBtn.addEventListener("click", hide);

  header.appendChild(title);
  header.appendChild(closeBtn);

  const content = document.createElement("div");
  content.className = "detail-panel-content";

  panel.appendChild(header);
  panel.appendChild(content);

  return { panel, content, title };
}

function renderStageDetails(data) {
  const { label, metadata } = data;
  let html = `<div class="detail-section">`;
  html += `<div class="detail-label">Stage</div>`;
  html += `<div class="detail-value">${label}</div>`;
  html += `</div>`;

  if (metadata.status) {
    html += `<div class="detail-section">`;
    html += `<div class="detail-label">Status</div>`;
    html += `<div class="detail-value status-${metadata.status}">${metadata.status}</div>`;
    html += `</div>`;
  }

  if (metadata.tools && metadata.tools.length > 0) {
    html += `<div class="detail-section">`;
    html += `<div class="detail-label">Tools Used</div>`;
    html += `<ul class="detail-list">`;
    for (const tool of metadata.tools) {
      html += `<li>${tool}</li>`;
    }
    html += `</ul></div>`;
  }

  if (metadata.artifacts && metadata.artifacts.length > 0) {
    html += `<div class="detail-section">`;
    html += `<div class="detail-label">Artifacts</div>`;
    html += `<ul class="detail-list">`;
    for (const artifact of metadata.artifacts) {
      html += `<li>${artifact}</li>`;
    }
    html += `</ul></div>`;
  }

  return html;
}

function renderToolDetails(data) {
  const { label, metadata } = data;
  let html = `<div class="detail-section">`;
  html += `<div class="detail-label">Tool</div>`;
  html += `<div class="detail-value">${label}</div>`;
  html += `</div>`;

  if (metadata.status) {
    html += `<div class="detail-section">`;
    html += `<div class="detail-label">Status</div>`;
    html += `<div class="detail-value status-${metadata.status}">${metadata.status}</div>`;
    html += `</div>`;
  }

  if (metadata.duration !== undefined) {
    html += `<div class="detail-section">`;
    html += `<div class="detail-label">Duration</div>`;
    html += `<div class="detail-value">${metadata.duration}ms</div>`;
    html += `</div>`;
  }

  if (metadata.args) {
    html += `<div class="detail-section">`;
    html += `<div class="detail-label">Arguments</div>`;
    html += `<pre class="detail-code">${JSON.stringify(metadata.args, null, 2)}</pre>`;
    html += `</div>`;
  }

  return html;
}

function renderHorRuleDetails(data) {
  const { label, metadata } = data;
  let html = `<div class="detail-section">`;
  html += `<div class="detail-label">HOR Rule</div>`;
  html += `<div class="detail-value">${label}</div>`;
  html += `</div>`;

  html += `<div class="detail-section">`;
  html += `<div class="detail-label">Result</div>`;
  html += `<div class="detail-value status-${metadata.passed ? "completed" : "failed"}">`;
  html += metadata.passed ? "PASS" : "FAIL";
  html += `</div></div>`;

  if (metadata.category) {
    html += `<div class="detail-section">`;
    html += `<div class="detail-label">Category</div>`;
    html += `<div class="detail-value">${metadata.category}</div>`;
    html += `</div>`;
  }

  if (metadata.details) {
    html += `<div class="detail-section">`;
    html += `<div class="detail-label">Details</div>`;
    html += `<pre class="detail-code">${metadata.details}</pre>`;
    html += `</div>`;
  }

  return html;
}

function renderGateDetails(data) {
  const { label, metadata } = data;
  let html = `<div class="detail-section">`;
  html += `<div class="detail-label">Gate</div>`;
  html += `<div class="detail-value">${label}</div>`;
  html += `</div>`;

  html += `<div class="detail-section">`;
  html += `<div class="detail-label">Result</div>`;
  html += `<div class="detail-value status-${metadata.passed ? "completed" : "failed"}">`;
  html += metadata.passed ? "PASSED" : "BLOCKED";
  html += `</div></div>`;

  if (metadata.reason) {
    html += `<div class="detail-section">`;
    html += `<div class="detail-label">Reason</div>`;
    html += `<div class="detail-value">${metadata.reason}</div>`;
    html += `</div>`;
  }

  if (metadata.scores) {
    html += `<div class="detail-section">`;
    html += `<div class="detail-label">Scores</div>`;
    html += `<pre class="detail-code">${JSON.stringify(metadata.scores, null, 2)}</pre>`;
    html += `</div>`;
  }

  return html;
}

function renderDefaultDetails(data) {
  const { label, type, metadata } = data;
  let html = `<div class="detail-section">`;
  html += `<div class="detail-label">Type</div>`;
  html += `<div class="detail-value">${type}</div>`;
  html += `</div>`;

  html += `<div class="detail-section">`;
  html += `<div class="detail-label">Label</div>`;
  html += `<div class="detail-value">${label}</div>`;
  html += `</div>`;

  if (metadata && Object.keys(metadata).length > 0) {
    html += `<div class="detail-section">`;
    html += `<div class="detail-label">Metadata</div>`;
    html += `<pre class="detail-code">${JSON.stringify(metadata, null, 2)}</pre>`;
    html += `</div>`;
  }

  return html;
}

const RENDERERS = {
  stage: renderStageDetails,
  tool: renderToolDetails,
  hor_rule: renderHorRuleDetails,
  gate: renderGateDetails,
};

export function init(container) {
  const { panel, content, title } = createPanelDOM();
  panelElement = panel;
  contentElement = content;
  container.appendChild(panel);
  return panel;
}

export function show(nodeData) {
  if (!panelElement || !contentElement) {
    return;
  }
  currentNodeId = nodeData.id;
  const renderer = RENDERERS[nodeData.type] || renderDefaultDetails;
  contentElement.innerHTML = renderer(nodeData);

  const title = panelElement.querySelector(".detail-panel-title");
  if (title) {
    title.textContent = nodeData.label || "Details";
  }

  panelElement.classList.add(VISIBLE_CLASS);
}

export function hide() {
  if (!panelElement) {
    return;
  }
  panelElement.classList.remove(VISIBLE_CLASS);
  currentNodeId = null;
}

export function isVisible() {
  return panelElement ? panelElement.classList.contains(VISIBLE_CLASS) : false;
}

export function getCurrentNodeId() {
  return currentNodeId;
}
