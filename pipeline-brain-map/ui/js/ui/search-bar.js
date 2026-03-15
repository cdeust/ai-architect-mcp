const TYPE_OPTIONS = [
  { value: "all", label: "All Types" },
  { value: "stage", label: "Stage" },
  { value: "tool", label: "Tool" },
  { value: "artifact", label: "Artifact" },
  { value: "hor_rule", label: "HOR Rule" },
  { value: "gate", label: "Gate" },
  { value: "ooda", label: "OODA" },
  { value: "error", label: "Error" },
];

const STATUS_OPTIONS = [
  { value: "all", label: "All Status" },
  { value: "active", label: "Active" },
  { value: "completed", label: "Completed" },
  { value: "failed", label: "Failed" },
  { value: "pending", label: "Pending" },
];

const MAX_RESULTS = 10;
const STAGE_COUNT = 11;

let containerElement = null;
let inputElement = null;
let resultsElement = null;
let searchCallback = null;

function createSelect(options, className) {
  const select = document.createElement("select");
  select.className = className;
  for (const opt of options) {
    const option = document.createElement("option");
    option.value = opt.value;
    option.textContent = opt.label;
    select.appendChild(option);
  }
  return select;
}

function createStageSelect() {
  const options = [{ value: "all", label: "All Stages" }];
  for (let i = 0; i < STAGE_COUNT; i++) {
    options.push({ value: String(i), label: `Stage ${i}` });
  }
  return createSelect(options, "search-filter-stage");
}

function buildSearchParams() {
  const query = inputElement ? inputElement.value.trim() : "";
  const typeSelect = containerElement.querySelector(".search-filter-type");
  const stageSelect = containerElement.querySelector(".search-filter-stage");
  const statusSelect = containerElement.querySelector(".search-filter-status");

  return {
    query,
    type: typeSelect ? typeSelect.value : "all",
    stageId: stageSelect ? stageSelect.value : "all",
    status: statusSelect ? statusSelect.value : "all",
  };
}

function handleSearch() {
  if (!searchCallback) {
    return;
  }
  const params = buildSearchParams();
  searchCallback(params);
}

function handleKeydown(event) {
  if (event.key === "Enter") {
    handleSearch();
  }
  if (event.key === "Escape") {
    clearSearch();
  }
}

function clearSearch() {
  if (inputElement) {
    inputElement.value = "";
  }
  if (resultsElement) {
    resultsElement.innerHTML = "";
    resultsElement.classList.remove("visible");
  }
}

export function init(container) {
  containerElement = document.createElement("div");
  containerElement.className = "search-bar";

  const inputWrapper = document.createElement("div");
  inputWrapper.className = "search-input-wrapper";

  inputElement = document.createElement("input");
  inputElement.type = "text";
  inputElement.className = "search-input";
  inputElement.placeholder = "Search nodes...";
  inputElement.addEventListener("keydown", handleKeydown);

  const searchBtn = document.createElement("button");
  searchBtn.className = "search-btn";
  searchBtn.textContent = "Search";
  searchBtn.addEventListener("click", handleSearch);

  inputWrapper.appendChild(inputElement);
  inputWrapper.appendChild(searchBtn);

  const filters = document.createElement("div");
  filters.className = "search-filters";

  const typeSelect = createSelect(TYPE_OPTIONS, "search-filter-type");
  const stageSelect = createStageSelect();
  const statusSelect = createSelect(STATUS_OPTIONS, "search-filter-status");

  filters.appendChild(typeSelect);
  filters.appendChild(stageSelect);
  filters.appendChild(statusSelect);

  resultsElement = document.createElement("div");
  resultsElement.className = "search-results";

  containerElement.appendChild(inputWrapper);
  containerElement.appendChild(filters);
  containerElement.appendChild(resultsElement);
  container.appendChild(containerElement);

  return containerElement;
}

export function onSearch(callback) {
  searchCallback = callback;
}

export function showResults(results) {
  if (!resultsElement) {
    return;
  }
  resultsElement.innerHTML = "";
  const limited = results.slice(0, MAX_RESULTS);

  for (const result of limited) {
    const item = document.createElement("div");
    item.className = "search-result-item";
    item.dataset.nodeId = result.id;

    const label = document.createElement("span");
    label.className = "search-result-label";
    label.textContent = result.label;

    const type = document.createElement("span");
    type.className = "search-result-type";
    type.textContent = result.type;

    item.appendChild(label);
    item.appendChild(type);
    resultsElement.appendChild(item);
  }

  resultsElement.classList.toggle("visible", limited.length > 0);
}

export function clear() {
  clearSearch();
}
