/**
 * Radar / spider chart for verification coverage across HOR categories.
 * Pure Canvas2D, zero dependencies.
 */

const RADAR_PADDING = 50;
const GRID_LEVELS = [0.25, 0.5, 0.75, 1.0];
const FILL_ALPHA = 0.3;
const STROKE_COLOR = '#4fc3f7';
const FILL_COLOR = 'rgba(79,195,247,0.3)';
const GRID_COLOR = 'rgba(255,255,255,0.12)';
const AXIS_COLOR = 'rgba(255,255,255,0.2)';
const LABEL_COLOR = '#ccc';
const DOT_RADIUS = 4;
const FONT = '12px system-ui, monospace';

export class RadarChart {
  /** @param {HTMLCanvasElement} canvas */
  constructor(canvas) {
    this.canvas = canvas;
    this.ctx = canvas.getContext('2d');
  }

  /**
   * @param {{ axes: string[], values: number[] }} data
   *   values are 0..1 per axis
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

    const n = data.axes.length;
    if (n < 3) return;

    const cx = width / 2;
    const cy = height / 2;
    const radius = Math.min(cx, cy) - RADAR_PADDING;

    this._drawGridLines(n, cx, cy, radius);
    this._drawAxes(n, cx, cy, radius);
    this._drawDataPolygon(data, n, cx, cy, radius);
    this._drawLabels(data, n, cx, cy, radius);
  }

  _angleFor(i, n) {
    return (Math.PI * 2 * i) / n - Math.PI / 2;
  }

  _drawGridLines(n, cx, cy, radius) {
    const { ctx } = this;
    ctx.strokeStyle = GRID_COLOR;
    ctx.lineWidth = 1;

    for (const level of GRID_LEVELS) {
      const r = radius * level;
      ctx.beginPath();
      for (let i = 0; i <= n; i++) {
        const angle = this._angleFor(i % n, n);
        const x = cx + Math.cos(angle) * r;
        const y = cy + Math.sin(angle) * r;
        if (i === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
      }
      ctx.closePath();
      ctx.stroke();
    }
  }

  _drawAxes(n, cx, cy, radius) {
    const { ctx } = this;
    ctx.strokeStyle = AXIS_COLOR;
    ctx.lineWidth = 1;

    for (let i = 0; i < n; i++) {
      const angle = this._angleFor(i, n);
      ctx.beginPath();
      ctx.moveTo(cx, cy);
      ctx.lineTo(cx + Math.cos(angle) * radius, cy + Math.sin(angle) * radius);
      ctx.stroke();
    }
  }

  _drawDataPolygon(data, n, cx, cy, radius) {
    const { ctx } = this;

    ctx.beginPath();
    for (let i = 0; i <= n; i++) {
      const idx = i % n;
      const angle = this._angleFor(idx, n);
      const val = Math.max(0, Math.min(1, data.values[idx]));
      const x = cx + Math.cos(angle) * radius * val;
      const y = cy + Math.sin(angle) * radius * val;
      if (i === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    }
    ctx.closePath();
    ctx.fillStyle = FILL_COLOR;
    ctx.fill();
    ctx.strokeStyle = STROKE_COLOR;
    ctx.lineWidth = 2;
    ctx.stroke();

    this._drawDots(data, n, cx, cy, radius);
  }

  _drawDots(data, n, cx, cy, radius) {
    const { ctx } = this;
    ctx.fillStyle = STROKE_COLOR;
    for (let i = 0; i < n; i++) {
      const angle = this._angleFor(i, n);
      const val = Math.max(0, Math.min(1, data.values[i]));
      const x = cx + Math.cos(angle) * radius * val;
      const y = cy + Math.sin(angle) * radius * val;
      ctx.beginPath();
      ctx.arc(x, y, DOT_RADIUS, 0, Math.PI * 2);
      ctx.fill();
    }
  }

  _drawLabels(data, n, cx, cy, radius) {
    const { ctx } = this;
    ctx.fillStyle = LABEL_COLOR;
    ctx.font = FONT;
    ctx.textBaseline = 'middle';

    for (let i = 0; i < n; i++) {
      const angle = this._angleFor(i, n);
      const labelR = radius + 18;
      const x = cx + Math.cos(angle) * labelR;
      const y = cy + Math.sin(angle) * labelR;
      ctx.textAlign = Math.abs(Math.cos(angle)) < 0.1 ? 'center'
        : Math.cos(angle) > 0 ? 'left' : 'right';
      ctx.fillText(data.axes[i], x, y);
    }
  }
}
