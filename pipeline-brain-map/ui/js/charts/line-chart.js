/**
 * Line chart for finding throughput over time.
 * Pure Canvas2D, zero dependencies.
 */

const LINE_PADDING = { top: 30, right: 30, bottom: 50, left: 60 };
const LINE_COLOR = '#4fc3f7';
const FILL_COLOR = 'rgba(79,195,247,0.15)';
const GRID_COLOR = 'rgba(255,255,255,0.08)';
const LABEL_COLOR = '#aaa';
const DOT_RADIUS = 3;
const AXIS_TICKS = 5;
const FONT = '12px system-ui, monospace';
const AXIS_FONT = 'bold 12px system-ui, monospace';

export class LineChart {
  /** @param {HTMLCanvasElement} canvas */
  constructor(canvas) {
    this.canvas = canvas;
    this.ctx = canvas.getContext('2d');
  }

  /**
   * @param {{ points: { x: number, y: number }[], xLabel: string, yLabel: string }} data
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

    const pts = data.points;
    if (pts.length === 0) return;

    const plotW = width - LINE_PADDING.left - LINE_PADDING.right;
    const plotH = height - LINE_PADDING.top - LINE_PADDING.bottom;
    const bounds = this._bounds(pts);

    this._drawGrid(plotW, plotH, bounds);
    this._drawAreaFill(pts, plotW, plotH, bounds);
    this._drawLine(pts, plotW, plotH, bounds);
    this._drawDots(pts, plotW, plotH, bounds);
    this._drawAxisLabels(data, plotW, plotH);
  }

  _bounds(pts) {
    const xs = pts.map((p) => p.x);
    const ys = pts.map((p) => p.y);
    return {
      minX: Math.min(...xs), maxX: Math.max(...xs),
      minY: Math.min(0, Math.min(...ys)), maxY: Math.max(...ys) * 1.1,
    };
  }

  _toScreen(px, py, plotW, plotH, bounds) {
    const x = LINE_PADDING.left + ((px - bounds.minX) / (bounds.maxX - bounds.minX || 1)) * plotW;
    const y = LINE_PADDING.top + plotH - ((py - bounds.minY) / (bounds.maxY - bounds.minY || 1)) * plotH;
    return { x, y };
  }

  _drawGrid(plotW, plotH, bounds) {
    const { ctx } = this;
    ctx.strokeStyle = GRID_COLOR;
    ctx.fillStyle = LABEL_COLOR;
    ctx.font = FONT;
    ctx.textAlign = 'right';
    ctx.textBaseline = 'middle';

    for (let i = 0; i <= AXIS_TICKS; i++) {
      const val = bounds.minY + ((bounds.maxY - bounds.minY) / AXIS_TICKS) * i;
      const y = LINE_PADDING.top + plotH - (plotH * i) / AXIS_TICKS;
      ctx.beginPath();
      ctx.moveTo(LINE_PADDING.left, y);
      ctx.lineTo(LINE_PADDING.left + plotW, y);
      ctx.stroke();
      ctx.fillText(val.toFixed(1), LINE_PADDING.left - 8, y);
    }
  }

  _drawAreaFill(pts, plotW, plotH, bounds) {
    const { ctx } = this;
    const baseY = LINE_PADDING.top + plotH;
    ctx.beginPath();
    const first = this._toScreen(pts[0].x, pts[0].y, plotW, plotH, bounds);
    ctx.moveTo(first.x, baseY);
    ctx.lineTo(first.x, first.y);
    for (let i = 1; i < pts.length; i++) {
      const p = this._toScreen(pts[i].x, pts[i].y, plotW, plotH, bounds);
      ctx.lineTo(p.x, p.y);
    }
    const last = this._toScreen(pts[pts.length - 1].x, pts[pts.length - 1].y, plotW, plotH, bounds);
    ctx.lineTo(last.x, baseY);
    ctx.closePath();
    ctx.fillStyle = FILL_COLOR;
    ctx.fill();
  }

  _drawLine(pts, plotW, plotH, bounds) {
    const { ctx } = this;
    ctx.strokeStyle = LINE_COLOR;
    ctx.lineWidth = 2;
    ctx.lineJoin = 'round';
    ctx.beginPath();
    for (let i = 0; i < pts.length; i++) {
      const p = this._toScreen(pts[i].x, pts[i].y, plotW, plotH, bounds);
      if (i === 0) ctx.moveTo(p.x, p.y);
      else ctx.lineTo(p.x, p.y);
    }
    ctx.stroke();
  }

  _drawDots(pts, plotW, plotH, bounds) {
    const { ctx } = this;
    ctx.fillStyle = LINE_COLOR;
    for (const pt of pts) {
      const p = this._toScreen(pt.x, pt.y, plotW, plotH, bounds);
      ctx.beginPath();
      ctx.arc(p.x, p.y, DOT_RADIUS, 0, Math.PI * 2);
      ctx.fill();
    }
  }

  _drawAxisLabels(data, plotW, plotH) {
    const { ctx, width, height } = this;
    ctx.fillStyle = LABEL_COLOR;
    ctx.font = AXIS_FONT;
    ctx.textAlign = 'center';
    ctx.textBaseline = 'top';
    ctx.fillText(data.xLabel, LINE_PADDING.left + plotW / 2, height - 16);
    ctx.save();
    ctx.translate(14, LINE_PADDING.top + plotH / 2);
    ctx.rotate(-Math.PI / 2);
    ctx.textBaseline = 'bottom';
    ctx.fillText(data.yLabel, 0, 0);
    ctx.restore();
  }
}
