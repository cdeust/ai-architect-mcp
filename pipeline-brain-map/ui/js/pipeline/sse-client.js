const INITIAL_RETRY_MS = 1000;
const MAX_RETRY_MS = 30000;
const BACKOFF_MULTIPLIER = 2;

let eventSource = null;
let retryMs = INITIAL_RETRY_MS;
let retryTimeout = null;
let url = "";
let eventCallback = null;
let connected = false;

function resetBackoff() {
  retryMs = INITIAL_RETRY_MS;
}

function scheduleReconnect() {
  if (retryTimeout) {
    clearTimeout(retryTimeout);
  }
  console.log(`SSE reconnecting in ${retryMs}ms...`);
  retryTimeout = setTimeout(() => {
    connect();
  }, retryMs);
  retryMs = Math.min(retryMs * BACKOFF_MULTIPLIER, MAX_RETRY_MS);
}

function handleOpen() {
  console.log("SSE connection established");
  connected = true;
  resetBackoff();
}

function handleError() {
  console.warn("SSE connection error");
  connected = false;
  if (eventSource) {
    eventSource.close();
    eventSource = null;
  }
  scheduleReconnect();
}

function handleMessage(messageEvent) {
  if (!eventCallback) {
    return;
  }
  try {
    const data = JSON.parse(messageEvent.data);
    eventCallback(data);
  } catch (err) {
    console.error("SSE parse error:", err.message);
  }
}

export function connect(serverUrl) {
  if (serverUrl) {
    url = serverUrl;
  }
  if (!url) {
    console.error("SSE client: no URL provided");
    return;
  }
  disconnect();
  eventSource = new EventSource(url);
  eventSource.onopen = handleOpen;
  eventSource.onerror = handleError;
  eventSource.addEventListener("pipeline", handleMessage);
}

export function disconnect() {
  if (retryTimeout) {
    clearTimeout(retryTimeout);
    retryTimeout = null;
  }
  if (eventSource) {
    eventSource.close();
    eventSource = null;
  }
  connected = false;
}

export function onEvent(callback) {
  eventCallback = callback;
}

export function isConnected() {
  return connected;
}
