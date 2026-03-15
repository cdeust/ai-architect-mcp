/**
 * Vertical bar chart for gate success rates / tool call frequency.
 * Pure Canvas2D, zero dependencies.
 */

const BAR_PADDING = { top: 30, right: 20, bottom: 70, left: 60 };
const BAR_RADIUS = 4;
const DEFAULT_COLOR = '#4fc3f7';
const GRID_COLOR = 'rgba(255,255,255,0.08)';
const LABEL_COLOR = '#aaa';
const FONT = '12px system-ui, monospace';

export class BarChart {
  /** @param {HTMLCanvasElement} canvas */
  constructor(canvas) {
    this.canvas = canvas;
    this.ctx = canvas.getContext('2d');
  }

  /**
   * @param {{ labels: string[], values: number[], colors?: string[] }} data
   */
  render(data) {
    this._resize();
    this._draw(data);
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

  _draw(data) {
    const { ctx, width, height } = this;
    ctx.clearRect(0, 0, width, height);
    ctx.fillStyle = '#0a0a1a';
    ctx.fillRect(0, 0, width, height);

    const count = data.labels.length;
    if (count === 0) return;

    const plotW = width - BAR_PADDING.left - BAR_PADDING.right;
    const plotH = height - BAR_PADDING.top - BAR_PADDING.bottom;
    const maxVal = Math.max(...data.values, 1);
    const barW = (plotW / count) * 0.7;
    const gap = (plotW / count) * 0.3;

    this._drawGrid(plotW, plotH, maxVal);
    this._drawBars(data, count, plotH, barW, gap, maxVal);
    this._drawXLabels(data, count, barW, gap, plotH);
  }

  _drawGrid(plotW, plotH, maxVal) {
    const { ctx } = this;
    const ticks = 5;
    ctx.strokeStyle = GRID_COLOR;
    ctx.fillStyle = LABEL_COLOR;
    ctx.font = FONT;
    ctx.textAlign = 'right';
    ctx.textBaseline = 'middle';

    for (let i = 0; i <= ticks; i++) {
      const val = (maxVal / ticks) * i;
      const y = BAR_PADDING.top + plotH - (plotH * i) / ticks;
      ctx.beginPath();
      ctx.moveTo(BAR_PADDING.left, y);
      ctx.lineTo(BAR_PADDING.left + plotW, y);
      ctx.stroke();
      ctx.fillText(val.toFixed(0), BAR_PADDING.left - 8, y);
    }
  }

  _drawBars(data, count, plotH, barW, gap, maxVal) {
    const { ctx } = this;
    for (let i = 0; i < count; i++) {
      const x = BAR_PADDING.left + i * (barW + gap) + gap / 2;
      const barH = (data.values[i] / maxVal) * plotH;
      const y = BAR_PADDING.top + plotH - barH;
      const color = data.colors?.[i] ?? DEFAULT_COLOR;
      ctx.fillStyle = color;
      this._roundedRect(x, y, barW, barH, BAR_RADIUS);
    }
  }

  _roundedRect(x, y, w, h, r) {
    const { ctx } = this;
    const radius = Math.min(r, h / 2, w / 2);
    ctx.beginPath();
    ctx.moveTo(x + radius, y);
    ctx.lineTo(x + w - radius, y);
    ctx.quadraticCurveTo(x + w, y, x + w, y + radius);
    ctx.lineTo(x + w, y + h);
    ctx.lineTo(x, y + h);
    ctx.lineTo(x, y + radius);
    ctx.quadraticCurveTo(x, y, x + radius, y);
    ctx.closePath();
    ctx.fill();
  }

  _drawXLabels(data, count, barW, gap, plotH) {
    const { ctx, height } = this;
    ctx.fillStyle = LABEL_COLOR;
    ctx.font = FONT;
    ctx.textAlign = 'right';
    for (let i = 0; i < count; i++) {
      const x = BAR_PADDING.left + i * (barW + gap) + gap / 2 + barW / 2;
      const y = BAR_PADDING.top + plotH + 16;
      ctx.save();
      ctx.translate(x, y);
      ctx.rotate(-Math.PI / 4);
      ctx.fillText(data.labels[i], 0, 0);
      ctx.restore();
    }
  }
}
