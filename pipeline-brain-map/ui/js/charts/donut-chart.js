/**
 * Donut chart for HOR rule category distribution.
 * Pure Canvas2D, zero dependencies.
 */

const DONUT_PADDING = 20;
const INNER_RATIO = 0.55;
const LEGEND_LINE_HEIGHT = 22;
const LEGEND_SWATCH = 14;
const FONT = '12px system-ui, monospace';
const CENTER_FONT = 'bold 22px system-ui, monospace';
const CENTER_SUB_FONT = '12px system-ui, monospace';
const LABEL_COLOR = '#ccc';

export class DonutChart {
  /** @param {HTMLCanvasElement} canvas */
  constructor(canvas) {
    this.canvas = canvas;
    this.ctx = canvas.getContext('2d');
  }

  /**
   * @param {{ segments: { label: string, value: number, color: string }[] }} data
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

    const segments = data.segments;
    if (segments.length === 0) return;

    const total = segments.reduce((sum, s) => sum + s.value, 0);
    const legendH = segments.length * LEGEND_LINE_HEIGHT + DONUT_PADDING;
    const availH = height - legendH;
    const radius = Math.min(width / 2, availH / 2) - DONUT_PADDING;
    const cx = width / 2;
    const cy = availH / 2;
    const innerR = radius * INNER_RATIO;

    this._drawArcs(segments, total, cx, cy, radius, innerR);
    this._drawCenterText(total, cx, cy);
    this._drawLegend(segments, total, availH);
  }

  _drawArcs(segments, total, cx, cy, radius, innerR) {
    const { ctx } = this;
    let startAngle = -Math.PI / 2;

    for (const seg of segments) {
      const sweep = (seg.value / total) * Math.PI * 2;
      ctx.beginPath();
      ctx.arc(cx, cy, radius, startAngle, startAngle + sweep);
      ctx.arc(cx, cy, innerR, startAngle + sweep, startAngle, true);
      ctx.closePath();
      ctx.fillStyle = seg.color;
      ctx.fill();
      startAngle += sweep;
    }
  }

  _drawCenterText(total, cx, cy) {
    const { ctx } = this;
    ctx.fillStyle = '#fff';
    ctx.font = CENTER_FONT;
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText(total.toString(), cx, cy - 8);
    ctx.fillStyle = LABEL_COLOR;
    ctx.font = CENTER_SUB_FONT;
    ctx.fillText('total', cx, cy + 14);
  }

  _drawLegend(segments, total, startY) {
    const { ctx, width } = this;
    const lx = DONUT_PADDING;
    let ly = startY + DONUT_PADDING / 2;

    for (const seg of segments) {
      ctx.fillStyle = seg.color;
      ctx.fillRect(lx, ly, LEGEND_SWATCH, LEGEND_SWATCH);
      ctx.fillStyle = LABEL_COLOR;
      ctx.font = FONT;
      ctx.textAlign = 'left';
      ctx.textBaseline = 'middle';
      const pct = ((seg.value / total) * 100).toFixed(1);
      ctx.fillText(`${seg.label} (${pct}%)`, lx + LEGEND_SWATCH + 8, ly + LEGEND_SWATCH / 2);
      ly += LEGEND_LINE_HEIGHT;
    }
  }
}
