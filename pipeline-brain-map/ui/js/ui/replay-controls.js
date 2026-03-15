const SPEEDS = [0.5, 1, 2, 4];
const DEFAULT_SPEED_INDEX = 1;
const STEP_FORWARD = 1;
const STEP_BACKWARD = -1;

let containerElement = null;
let scrubberElement = null;
let currentDisplay = null;
let playPauseBtn = null;
let speedBtn = null;

let events = [];
let currentIndex = -1;
let playing = false;
let speedIndex = DEFAULT_SPEED_INDEX;
let playInterval = null;
let eventCallback = null;

function getIntervalMs() {
  const speed = SPEEDS[speedIndex];
  return Math.round(1000 / speed);
}

function updateDisplay() {
  if (!currentDisplay) {
    return;
  }
  const total = events.length;
  const current = currentIndex + 1;
  currentDisplay.textContent = `${current} / ${total}`;
}

function updateScrubber() {
  if (!scrubberElement) {
    return;
  }
  scrubberElement.max = String(Math.max(0, events.length - 1));
  scrubberElement.value = String(Math.max(0, currentIndex));
}

function updatePlayPauseLabel() {
  if (!playPauseBtn) {
    return;
  }
  playPauseBtn.textContent = playing ? "Pause" : "Play";
}

function updateSpeedLabel() {
  if (!speedBtn) {
    return;
  }
  speedBtn.textContent = `${SPEEDS[speedIndex]}x`;
}

function emitEvent() {
  if (!eventCallback || currentIndex < 0 || currentIndex >= events.length) {
    return;
  }
  eventCallback(events[currentIndex], currentIndex);
}

function tick() {
  if (currentIndex >= events.length - 1) {
    pause();
    return;
  }
  currentIndex++;
  updateScrubber();
  updateDisplay();
  emitEvent();
}

function startInterval() {
  stopInterval();
  playInterval = setInterval(tick, getIntervalMs());
}

function stopInterval() {
  if (playInterval) {
    clearInterval(playInterval);
    playInterval = null;
  }
}

function handleScrubberInput() {
  const wasPlaying = playing;
  if (wasPlaying) {
    stopInterval();
  }
  currentIndex = parseInt(scrubberElement.value, 10);
  updateDisplay();
  emitEvent();
  if (wasPlaying) {
    startInterval();
  }
}

function handleSpeedClick() {
  speedIndex = (speedIndex + 1) % SPEEDS.length;
  updateSpeedLabel();
  if (playing) {
    startInterval();
  }
}

function createButton(text, className, handler) {
  const btn = document.createElement("button");
  btn.className = className;
  btn.textContent = text;
  btn.addEventListener("click", handler);
  return btn;
}

export function init(container) {
  containerElement = document.createElement("div");
  containerElement.className = "replay-controls";

  const controls = document.createElement("div");
  controls.className = "replay-buttons";

  const stepBackBtn = createButton("Back", "replay-btn step-back", () => {
    step(STEP_BACKWARD);
  });

  playPauseBtn = createButton("Play", "replay-btn play-pause", () => {
    if (playing) {
      pause();
    } else {
      play();
    }
  });

  const stepFwdBtn = createButton("Next", "replay-btn step-forward", () => {
    step(STEP_FORWARD);
  });

  speedBtn = createButton(
    `${SPEEDS[speedIndex]}x`,
    "replay-btn speed",
    handleSpeedClick
  );

  controls.appendChild(stepBackBtn);
  controls.appendChild(playPauseBtn);
  controls.appendChild(stepFwdBtn);
  controls.appendChild(speedBtn);

  const scrubberWrapper = document.createElement("div");
  scrubberWrapper.className = "replay-scrubber-wrapper";

  scrubberElement = document.createElement("input");
  scrubberElement.type = "range";
  scrubberElement.className = "replay-scrubber";
  scrubberElement.min = "0";
  scrubberElement.max = "0";
  scrubberElement.value = "0";
  scrubberElement.addEventListener("input", handleScrubberInput);

  currentDisplay = document.createElement("span");
  currentDisplay.className = "replay-display";
  currentDisplay.textContent = "0 / 0";

  scrubberWrapper.appendChild(scrubberElement);
  scrubberWrapper.appendChild(currentDisplay);

  containerElement.appendChild(controls);
  containerElement.appendChild(scrubberWrapper);
  container.appendChild(containerElement);

  return containerElement;
}

export function setEvents(newEvents) {
  pause();
  events = newEvents || [];
  currentIndex = events.length > 0 ? 0 : -1;
  updateScrubber();
  updateDisplay();
}

export function play() {
  if (events.length === 0) {
    return;
  }
  if (currentIndex >= events.length - 1) {
    currentIndex = 0;
  }
  playing = true;
  updatePlayPauseLabel();
  startInterval();
}

export function pause() {
  playing = false;
  updatePlayPauseLabel();
  stopInterval();
}

export function step(direction) {
  const wasPlaying = playing;
  if (wasPlaying) {
    pause();
  }
  const next = currentIndex + direction;
  if (next < 0 || next >= events.length) {
    return;
  }
  currentIndex = next;
  updateScrubber();
  updateDisplay();
  emitEvent();
}

export function setSpeed(multiplier) {
  const idx = SPEEDS.indexOf(multiplier);
  if (idx === -1) {
    return;
  }
  speedIndex = idx;
  updateSpeedLabel();
  if (playing) {
    startInterval();
  }
}

export function onEvent(callback) {
  eventCallback = callback;
}

export function isPlaying() {
  return playing;
}

export function getCurrentIndex() {
  return currentIndex;
}
