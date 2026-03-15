/**
 * Comparison view — split viewport for side-by-side trace comparison.
 *
 * Phase 4: enables visual diff between two pipeline traces by rendering
 * both graphs simultaneously in a split viewport.
 */

const SPLIT_GAP = 4;

export class ComparisonView {
  /**
   * @param {HTMLElement} container — parent element for the split view
   */
  constructor(container) {
    this._container = container;
    this._leftPanel = null;
    this._rightPanel = null;
    this._active = false;
    this._splitRatio = 0.5;
  }

  /** @returns {boolean} */
  get isActive() {
    return this._active;
  }

  /**
   * Enable comparison mode with split viewport.
   *
   * @param {string} leftLabel — label for left trace
   * @param {string} rightLabel — label for right trace
   */
  enable(leftLabel = 'Trace A', rightLabel = 'Trace B') {
    if (this._active) return;
    this._active = true;

    this._overlay = document.createElement('div');
    this._overlay.className = 'comparison-overlay';
    this._overlay.innerHTML = `
      <div class="comparison-left glass-panel" id="compare-left">
        <div class="comparison-header">${leftLabel}</div>
        <canvas class="comparison-canvas" id="canvas-left"></canvas>
      </div>
      <div class="comparison-divider" id="compare-divider"></div>
      <div class="comparison-right glass-panel" id="compare-right">
        <div class="comparison-header">${rightLabel}</div>
        <canvas class="comparison-canvas" id="canvas-right"></canvas>
      </div>
    `;

    this._container.appendChild(this._overlay);
    this._leftPanel = this._overlay.querySelector('#compare-left');
    this._rightPanel = this._overlay.querySelector('#compare-right');
    this._applyLayout();
    this._setupDividerDrag();
  }

  /** Disable comparison mode and restore single viewport. */
  disable() {
    if (!this._active) return;
    this._active = false;

    if (this._overlay && this._overlay.parentNode) {
      this._overlay.parentNode.removeChild(this._overlay);
    }
    this._overlay = null;
    this._leftPanel = null;
    this._rightPanel = null;
  }

  /** Toggle comparison mode on/off. */
  toggle() {
    if (this._active) {
      this.disable();
    } else {
      this.enable();
    }
  }

  /**
   * Get the canvas elements for both viewports.
   *
   * @returns {{ left: HTMLCanvasElement|null, right: HTMLCanvasElement|null }}
   */
  getCanvases() {
    if (!this._active) return { left: null, right: null };
    return {
      left: this._overlay.querySelector('#canvas-left'),
      right: this._overlay.querySelector('#canvas-right'),
    };
  }

  /**
   * Update the diff highlights between two graph states.
   *
   * @param {Map} leftNodes — node map from trace A
   * @param {Map} rightNodes — node map from trace B
   * @returns {{ added: string[], removed: string[], changed: string[] }}
   */
  computeDiff(leftNodes, rightNodes) {
    const added = [];
    const removed = [];
    const changed = [];

    for (const [id, node] of rightNodes) {
      if (!leftNodes.has(id)) {
        added.push(id);
      } else {
        const leftNode = leftNodes.get(id);
        if (leftNode.status !== node.status) {
          changed.push(id);
        }
      }
    }

    for (const id of leftNodes.keys()) {
      if (!rightNodes.has(id)) {
        removed.push(id);
      }
    }

    return { added, removed, changed };
  }

  /**
   * Apply the current split ratio to panel widths.
   * @private
   */
  _applyLayout() {
    if (!this._leftPanel || !this._rightPanel) return;
    const leftPercent = this._splitRatio * 100;
    const rightPercent = (1 - this._splitRatio) * 100;

    this._leftPanel.style.width = `calc(${leftPercent}% - ${SPLIT_GAP}px)`;
    this._rightPanel.style.width = `calc(${rightPercent}% - ${SPLIT_GAP}px)`;
  }

  /**
   * Set up drag-to-resize on the divider.
   * @private
   */
  _setupDividerDrag() {
    const divider = this._overlay.querySelector('#compare-divider');
    if (!divider) return;

    let dragging = false;

    divider.addEventListener('mousedown', (e) => {
      dragging = true;
      e.preventDefault();
    });

    document.addEventListener('mousemove', (e) => {
      if (!dragging) return;
      const rect = this._overlay.getBoundingClientRect();
      const ratio = (e.clientX - rect.left) / rect.width;
      this._splitRatio = Math.max(0.2, Math.min(0.8, ratio));
      this._applyLayout();
    });

    document.addEventListener('mouseup', () => {
      dragging = false;
    });
  }

  /**
   * Resize handler — called on window resize.
   *
   * @param {number} width — container width
   * @param {number} height — container height
   */
  resize(width, height) {
    if (!this._active) return;
    this._overlay.style.width = `${width}px`;
    this._overlay.style.height = `${height}px`;
    this._applyLayout();
  }
}
