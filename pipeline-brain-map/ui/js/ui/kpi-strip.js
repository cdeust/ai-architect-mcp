const KPI_DEFINITIONS = [
  { key: "active", label: "Active", format: "number" },
  { key: "completed", label: "Completed", format: "number" },
  { key: "blocked", label: "Blocked", format: "number" },
  { key: "avgDuration", label: "Avg Duration", format: "ms" },
  { key: "passRate", label: "Pass Rate", format: "percent" },
  { key: "coverage", label: "Coverage", format: "percent" },
];

const TREND_UP = "up";
const TREND_DOWN = "down";
const TREND_FLAT = "flat";

const TREND_SYMBOLS = {
  [TREND_UP]: "\u25B2",
  [TREND_DOWN]: "\u25BC",
  [TREND_FLAT]: "\u25C6",
};

let stripElement = null;
let previousValues = {};

function formatValue(value, format) {
  if (format === "ms") {
    return `${value}ms`;
  }
  if (format === "percent") {
    return `${value}%`;
  }
  return String(value);
}

function computeTrend(key, currentValue) {
  const prev = previousValues[key];
  if (prev === undefined || prev === currentValue) {
    return TREND_FLAT;
  }
  return currentValue > prev ? TREND_UP : TREND_DOWN;
}

function createCard(definition, value, trend) {
  const card = document.createElement("div");
  card.className = "kpi-card";
  card.dataset.key = definition.key;

  const valueEl = document.createElement("div");
  valueEl.className = "kpi-value";
  valueEl.textContent = formatValue(value, definition.format);

  const labelEl = document.createElement("div");
  labelEl.className = "kpi-label";
  labelEl.textContent = definition.label;

  const trendEl = document.createElement("span");
  trendEl.className = `kpi-trend kpi-trend-${trend}`;
  trendEl.textContent = TREND_SYMBOLS[trend];

  valueEl.appendChild(trendEl);
  card.appendChild(valueEl);
  card.appendChild(labelEl);

  return card;
}

export function init(container) {
  stripElement = document.createElement("div");
  stripElement.className = "kpi-strip";

  const defaultStats = {
    active: 0,
    completed: 0,
    blocked: 0,
    avgDuration: 0,
    passRate: 0,
    coverage: 0,
  };

  for (const def of KPI_DEFINITIONS) {
    const card = createCard(def, defaultStats[def.key], TREND_FLAT);
    stripElement.appendChild(card);
  }

  container.appendChild(stripElement);
  return stripElement;
}

export function update(stats) {
  if (!stripElement || !stats) {
    return;
  }

  stripElement.innerHTML = "";

  for (const def of KPI_DEFINITIONS) {
    const value = stats[def.key] !== undefined ? stats[def.key] : 0;
    const trend = computeTrend(def.key, value);
    const card = createCard(def, value, trend);
    stripElement.appendChild(card);
  }

  for (const def of KPI_DEFINITIONS) {
    previousValues[def.key] = stats[def.key] !== undefined
      ? stats[def.key]
      : 0;
  }
}

export function reset() {
  previousValues = {};
  if (stripElement) {
    update({
      active: 0,
      completed: 0,
      blocked: 0,
      avgDuration: 0,
      passRate: 0,
      coverage: 0,
    });
  }
}
