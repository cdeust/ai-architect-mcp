const PANEL_CLASS = "analytics-panel";
const GLASSMORPHISM_CLASS = "glassmorphism";
const VISIBLE_CLASS = "visible";
const CHART_SLOT_COUNT = 6;

const CHART_SLOT_IDS = [
  "chart-stage-timeline",
  "chart-tool-frequency",
  "chart-hor-coverage",
  "chart-confidence-trend",
  "chart-gate-results",
  "chart-error-distribution",
];

const CHART_SLOT_TITLES = [
  "Stage Timeline",
  "Tool Frequency",
  "HOR Coverage",
  "Confidence Trend",
  "Gate Results",
  "Error Distribution",
];

let panelElement = null;
let kpiStripElement = null;
let chartContainers = [];
let visible = false;

function createHeader() {
  const header = document.createElement("div");
  header.className = "analytics-panel-header";

  const title = document.createElement("h3");
  title.className = "analytics-panel-title";
  title.textContent = "Analytics";

  const toggleBtn = document.createElement("button");
  toggleBtn.className = "analytics-panel-toggle";
  toggleBtn.textContent = "\u00D7";
  toggleBtn.addEventListener("click", toggle);

  header.appendChild(title);
  header.appendChild(toggleBtn);
  return header;
}

function createKPIStrip() {
  const strip = document.createElement("div");
  strip.className = "analytics-kpi-strip";
  return strip;
}

function createChartSlot(id, title) {
  const slot = document.createElement("div");
  slot.className = "chart-slot";
  slot.id = id;

  const slotTitle = document.createElement("div");
  slotTitle.className = "chart-slot-title";
  slotTitle.textContent = title;

  const canvas = document.createElement("div");
  canvas.className = "chart-canvas";

  const placeholder = document.createElement("div");
  placeholder.className = "chart-placeholder";
  placeholder.textContent = "Chart placeholder";

  canvas.appendChild(placeholder);
  slot.appendChild(slotTitle);
  slot.appendChild(canvas);

  return slot;
}

function createChartsContainer() {
  const container = document.createElement("div");
  container.className = "charts-container";

  chartContainers = [];
  for (let i = 0; i < CHART_SLOT_COUNT; i++) {
    const slot = createChartSlot(CHART_SLOT_IDS[i], CHART_SLOT_TITLES[i]);
    container.appendChild(slot);
    chartContainers.push(slot);
  }

  return container;
}

function computeStatsFromGraph(graphState) {
  if (!graphState || !graphState.nodes) {
    return {
      active: 0,
      completed: 0,
      blocked: 0,
      avgDuration: 0,
      passRate: 0,
      coverage: 0,
    };
  }
  const nodes = graphState.nodes;

  let active = 0;
  let completed = 0;
  let blocked = 0;
  let totalDuration = 0;
  let durationCount = 0;
  let horPassed = 0;
  let horTotal = 0;

  for (const node of nodes) {
    const status = node.metadata ? node.metadata.status : null;
    if (status === "running" || status === "active") {
      active++;
    }
    if (status === "completed") {
      completed++;
    }
    if (status === "blocked" || status === "failed") {
      blocked++;
    }
    if (node.metadata && node.metadata.duration) {
      totalDuration += node.metadata.duration;
      durationCount++;
    }
    if (node.type === "hor_rule") {
      horTotal++;
      if (node.metadata && node.metadata.passed) {
        horPassed++;
      }
    }
  }

  const avgDuration = durationCount > 0
    ? Math.round(totalDuration / durationCount)
    : 0;
  const passRate = horTotal > 0
    ? Math.round((horPassed / horTotal) * 100)
    : 0;
  const coverage = horTotal > 0
    ? Math.round((horTotal / 64) * 100)
    : 0;

  return { active, completed, blocked, avgDuration, passRate, coverage };
}

function renderKPICards(stats) {
  if (!kpiStripElement) {
    return;
  }

  const kpis = [
    { label: "Active", value: stats.active },
    { label: "Completed", value: stats.completed },
    { label: "Blocked", value: stats.blocked },
    { label: "Avg Duration", value: `${stats.avgDuration}ms` },
    { label: "Pass Rate", value: `${stats.passRate}%` },
    { label: "Coverage", value: `${stats.coverage}%` },
  ];

  kpiStripElement.innerHTML = "";
  for (const kpi of kpis) {
    const card = document.createElement("div");
    card.className = "kpi-card-mini";

    const label = document.createElement("div");
    label.className = "kpi-card-label";
    label.textContent = kpi.label;

    const value = document.createElement("div");
    value.className = "kpi-card-value";
    value.textContent = kpi.value;

    card.appendChild(value);
    card.appendChild(label);
    kpiStripElement.appendChild(card);
  }
}

export function init(container) {
  panelElement = document.createElement("div");
  panelElement.className = `${PANEL_CLASS} ${GLASSMORPHISM_CLASS}`;

  const header = createHeader();
  kpiStripElement = createKPIStrip();
  const charts = createChartsContainer();

  panelElement.appendChild(header);
  panelElement.appendChild(kpiStripElement);
  panelElement.appendChild(charts);
  container.appendChild(panelElement);

  return panelElement;
}

export function toggle() {
  if (!panelElement) {
    return;
  }
  visible = !visible;
  if (visible) {
    panelElement.classList.add(VISIBLE_CLASS);
  } else {
    panelElement.classList.remove(VISIBLE_CLASS);
  }
}

export function show() {
  if (!panelElement) {
    return;
  }
  visible = true;
  panelElement.classList.add(VISIBLE_CLASS);
}

export function hide() {
  if (!panelElement) {
    return;
  }
  visible = false;
  panelElement.classList.remove(VISIBLE_CLASS);
}

export function updateCharts(graphState) {
  const stats = computeStatsFromGraph(graphState);
  renderKPICards(stats);
}

export function getChartContainer(index) {
  if (index < 0 || index >= CHART_SLOT_COUNT) {
    return null;
  }
  return chartContainers[index];
}

export function isVisible() {
  return visible;
}

export { CHART_SLOT_IDS, CHART_SLOT_TITLES };
