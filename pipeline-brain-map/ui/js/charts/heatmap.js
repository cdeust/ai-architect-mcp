/**
 * Heatmap chart — stages (X) × findings (Y).
 * Pure Canvas2D, zero dependencies.
 */

const HEATMAP_PADDING = { top: 40, right: 20, bottom: 60, left: 120 };
const FONT_SIZE = 12;
const LABEL_FONT = `${FONT_SIZE}px system-ui, monospace`;
const TITLE_FONT = `bold 14px system-ui, monospace`;

function lerpColor(t) {
  const clamped = Math.max(0, Math.min(1, t));
  const r = Math.round(30 + clamped * 225);
  const g = Math.round(80 + (1 - Math.abs(clamped - 0.5) * 2) * 120);
  const b = Math.round(220 - clamped * 200);
  return `rgb(${r},${g},${b})`;
}

export class HeatmapChart {
  /** @param {HTMLCanvasElement} canvas */
  constructor(canvas) {
    this.canvas = canvas;
    this.ctx = canvas.getContext('2d');
    this.hoveredCell = null;
    this.data = null;
    this.cellRects = [];
    canvas.addEventListener('mousemove', (e) => this._onMouseMove(e));
    canvas.addEventListener('mouseleave', () => this._onMouseLeave());
  }

  /**
   * @param {{ stages: string[], findings: string[], values: number[][] }} data
   *   values[findingIdx][stageIdx] — heat intensity 0..1
   */
  render(data) {
    this.data = data;
    this._resize();
    this._draw();
  }

  _resize() {
    const dpr = window.devicePixelRatio || 1;
    const rect = this.canvas.getBoundingClientRect();
    this.canvas.width = rect.width * dpr;
    this.canvas.height = rect.height * dpr;
    this.ctx.scale(dpr, dpr);
    this.width = rect.width;
    this.height = rect.height;
  }

  _draw() {
    const { ctx, data, width, height } = this;
    if (!data) return;

    ctx.clearRect(0, 0, width, height);
    ctx.fillStyle = '#0a0a1a';
    ctx.fillRect(0, 0, width, height);

    const cols = data.stages.length;
    const rows = data.findings.length;
    if (cols === 0 || rows === 0) return;

    const plotW = width - HEATMAP_PADDING.left - HEATMAP_PADDING.right;
    const plotH = height - HEATMAP_PADDING.top - HEATMAP_PADDING.bottom;
    const cellW = plotW / cols;
    const cellH = plotH / rows;

    this.cellRects = [];
    this._drawCells(cols, rows, cellW, cellH);
    this._drawXLabels(cols, cellW);
    this._drawYLabels(rows, cellH);
    this._drawTooltip(cellW, cellH);
  }

  _drawCells(cols, rows, cellW, cellH) {
    const { ctx, data } = this;
    for (let r = 0; r < rows; r++) {
      for (let c = 0; c < cols; c++) {
        const x = HEATMAP_PADDING.left + c * cellW;
        const y = HEATMAP_PADDING.top + r * cellH;
        const val = data.values[r][c];
        ctx.fillStyle = lerpColor(val);
        ctx.fillRect(x + 1, y + 1, cellW - 2, cellH - 2);
        this.cellRects.push({ x, y, w: cellW, h: cellH, row: r, col: c });
      }
    }
  }

  _drawXLabels(cols, cellW) {
    const { ctx, data, height } = this;
    ctx.fillStyle = '#aaa';
    ctx.font = LABEL_FONT;
    ctx.textAlign = 'right';
    for (let c = 0; c < cols; c++) {
      const x = HEATMAP_PADDING.left + c * cellW + cellW / 2;
      const y = height - HEATMAP_PADDING.bottom + 16;
      ctx.save();
      ctx.translate(x, y);
      ctx.rotate(-Math.PI / 4);
      ctx.fillText(data.stages[c], 0, 0);
      ctx.restore();
    }
  }

  _drawYLabels(rows, cellH) {
    const { ctx, data } = this;
    ctx.fillStyle = '#aaa';
    ctx.font = LABEL_FONT;
    ctx.textAlign = 'right';
    ctx.textBaseline = 'middle';
    for (let r = 0; r < rows; r++) {
      const y = HEATMAP_PADDING.top + r * cellH + cellH / 2;
      ctx.fillText(data.findings[r], HEATMAP_PADDING.left - 8, y);
    }
  }

  _drawTooltip(cellW, cellH) {
    if (!this.hoveredCell || !this.data) return;
    const { ctx, data } = this;
    const { row, col, x, y } = this.hoveredCell;
    const val = data.values[row][col];
    const label = `${data.findings[row]} × ${data.stages[col]}: ${val.toFixed(2)}`;
    ctx.font = TITLE_FONT;
    const tw = ctx.measureText(label).width + 16;
    const tx = Math.min(x + cellW, this.width - tw - 4);
    const ty = y - 28;
    ctx.fillStyle = 'rgba(0,0,0,0.85)';
    ctx.roundRect(tx, ty, tw, 24, 4);
    ctx.fill();
    ctx.fillStyle = '#fff';
    ctx.textAlign = 'left';
    ctx.textBaseline = 'middle';
    ctx.fillText(label, tx + 8, ty + 12);
  }

  _onMouseMove(e) {
    const rect = this.canvas.getBoundingClientRect();
    const mx = e.clientX - rect.left;
    const my = e.clientY - rect.top;
    this.hoveredCell = this.cellRects.find(
      (c) => mx >= c.x && mx <= c.x + c.w && my >= c.y && my <= c.y + c.h
    ) || null;
    this._draw();
  }

  _onMouseLeave() {
    this.hoveredCell = null;
    this._draw();
  }
}
