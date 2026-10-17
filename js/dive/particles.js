// Mořský svět — canvas 2D for everything small and numerous: bubbles, plankton, marine snow, glowing motes,
// and the reef/open-ocean fish schools (simple flocking around a moving centre, shy of the diver).
// One full-screen canvas, cleared and redrawn each frame; counts are capped for the iPad.
import { cssVar, parseColor, rgba } from '../ui.js';

const rnd = (a, b) => a + Math.random() * (b - a);
const MAX_BUBBLES = 180;

function fishSprite(color, ink, dpr) {
  const w = 30; const hgt = 16; const c = document.createElement('canvas');
  c.width = Math.ceil(w * dpr); c.height = Math.ceil(hgt * dpr);
  const g = c.getContext('2d'); g.scale(dpr, dpr);
  g.fillStyle = color; g.beginPath(); g.ellipse(17, 8, 11, 5.6, 0, 0, Math.PI * 2); g.fill();
  g.beginPath(); g.moveTo(7, 8); g.lineTo(0, 2.5); g.lineTo(1.5, 8); g.lineTo(0, 13.5); g.closePath(); g.fill();
  g.fillStyle = ink; g.beginPath(); g.arc(23.5, 6.8, 1.4, 0, Math.PI * 2); g.fill();
  return { c, w, h: hgt };
}

export class Particles {
  constructor(canvas) {
    this.c = canvas; this.g = canvas.getContext('2d');
    this.bubbles = []; this.schools = []; this.t = 0;
    const col = (n) => parseColor(cssVar(n));
    this.col = { bubble: cssVar('--bubble'), rim: cssVar('--bubble-rim'), snow: col('--snow'), sand: col('--surface-line'),
      glow: ['--glow-cyan', '--glow-violet', '--glow-green'].map((n) => cssVar(n)), ink: cssVar('--ink'), deep: cssVar('--deep-dim') };
    this.col.deepClear = rgba([...parseColor(this.col.deep).slice(0, 3), 0]);
    this.snow = Array.from({ length: 70 }, () => ({ x: rnd(0, 2000), y: rnd(0, 1200), z: rnd(0.5, 1.2), r: rnd(0.8, 2.2), v: rnd(6, 16) }));
    this.plankton = Array.from({ length: 40 }, () => ({ x: rnd(0, 2000), y: rnd(0, 1200), z: rnd(0.4, 1), r: rnd(0.8, 1.6), ph: rnd(0, 6) }));
    this.motes = Array.from({ length: 28 }, (_, i) => ({ x: rnd(0, 2000), y: rnd(0, 1200), z: rnd(0.6, 1.1), r: rnd(1.5, 3.2), ph: rnd(0, 6), c: i % 3 }));
  }
  resize(vwPx, vhPx, s, dpr) {
    this.vwPx = vwPx; this.vhPx = vhPx; this.s = s; this.dpr = dpr;
    this.c.width = Math.round(vwPx * dpr); this.c.height = Math.round(vhPx * dpr);
    this.c.style.width = `${vwPx}px`; this.c.style.height = `${vhPx}px`;
    this.sprites = new Map();
  }
  sprite(color) {
    if (!this.sprites.has(color)) this.sprites.set(color, fishSprite(color, this.col.ink, this.dpr * this.s));
    return this.sprites.get(color);
  }
  /** Bubbles at a world point (n of them, scattered by spread). */
  emit(x, y, n = 3, spread = 10, big = 1) {
    for (let i = 0; i < n && this.bubbles.length < MAX_BUBBLES; i++) {
      this.bubbles.push({ x: x + rnd(-spread, spread), y: y + rnd(-spread, spread), vy: -rnd(55, 105), r: rnd(2.2, 5.5) * big, life: 0, max: rnd(3, 5.5), ph: rnd(0, 6) });
    }
  }
  /** A school of n small fish swimming around (x0, y0) over ±range. colors = CSS colour strings. */
  addSchool({ x, y, n = 12, range = 300, colors = [], speed = 50, img = null, imgW = 34 }) {
    const fish = Array.from({ length: n }, (_, i) => {
      const a = (i / n) * Math.PI * 2; const rr = 18 + (i % 4) * 14;
      return { ox: Math.cos(a) * rr * 1.6, oy: Math.sin(a) * rr * 0.7, x: x + rnd(-60, 60), y: y + rnd(-30, 30), vx: 0, vy: 0, dir: 1,
        col: colors[i % Math.max(1, colors.length)] || this.col.bubble, sc: rnd(0.8, 1.15) };
    });
    const sc = { x0: x, y0: y, range, speed, ph: rnd(0, 6), fish, cx: x, cy: y, img, imgW, imgH: img && img.naturalWidth ? imgW * img.naturalHeight / img.naturalWidth : imgW * 0.45 };
    this.schools.push(sc); return sc;
  }
  update(dt, cam, vw, vh, diver, slow) {
    this.t += dt;
    for (const b of this.bubbles) {
      b.life += dt; b.y += b.vy * dt * (slow ? 0.6 : 1); b.x += Math.sin(this.t * 3 + b.ph) * 12 * dt;
      if (b.y < 2) b.life = b.max;                       // pops at the surface
    }
    this.bubbles = this.bubbles.filter((b) => b.life < b.max);
    for (const s of this.schools) {
      if (Math.abs(s.x0 - (cam.x + vw / 2)) > vw * 1.6) continue;   // far away: frozen
      const w = s.speed / s.range; const T = this.t * (slow ? 0.5 : 1);
      s.cx = s.x0 + s.range * Math.sin(T * w + s.ph); s.cy = s.y0 + 30 * Math.sin(T * 0.4 + s.ph);
      const dirC = Math.cos(T * w + s.ph) >= 0 ? 1 : -1;
      for (const f of s.fish) {
        const tx = s.cx + f.ox * dirC + Math.sin(T * 1.3 + f.ox) * 10; const ty = s.cy + f.oy + Math.cos(T * 1.1 + f.oy) * 8;
        let ax = (tx - f.x) * 2.2; let ay = (ty - f.y) * 2.2;
        const dx = f.x - diver.x; const dy = f.y - diver.y; const d = Math.hypot(dx, dy);
        if (d < 190 && d > 1) { ax += (dx / d) * 900 * (1 - d / 190); ay += (dy / d) * 900 * (1 - d / 190); }
        f.vx = (f.vx + ax * dt) * (1 - 2.2 * dt); f.vy = (f.vy + ay * dt) * (1 - 2.2 * dt);
        f.x += f.vx * dt; f.y = Math.max(20, f.y + f.vy * dt);
        if (Math.abs(f.vx) > 6) f.dir = f.vx > 0 ? 1 : -1;
      }
    }
  }
  /**
   * dark = 0…1 (marine snow + glowing motes fade in; plankton fades out).
   * lamp = { x, y, r } in CSS px: the headlamp hole in the darkness (the darkness is painted here, on the canvas
   * that is redrawn anyway, instead of a huge DOM gradient layer — iPad memory).
   */
  draw(cam, vw, vh, dark, lamp = null) {
    const { g, dpr, s } = this; const k = dpr * s;
    g.setTransform(1, 0, 0, 1, 0, 0); g.clearRect(0, 0, this.c.width, this.c.height);
    // view-space drift particles (parallax by z)
    g.setTransform(k, 0, 0, k, 0, 0);
    const wrap = (v, m) => ((v % m) + m) % m;
    if (dark < 0.95) {
      g.fillStyle = rgba([...this.col.sand.slice(0, 3), 0.55 * (1 - dark)]);
      for (const p of this.plankton) {
        const x = wrap(p.x - cam.x * p.z, vw + 40) - 20; const y = wrap(p.y - cam.y * p.z + Math.sin(this.t * 0.6 + p.ph) * 8, vh + 40) - 20;
        g.beginPath(); g.arc(x, y, p.r, 0, Math.PI * 2); g.fill();
      }
    }
    if (dark > 0.05) {
      g.fillStyle = rgba([...this.col.snow.slice(0, 3), this.col.snow[3] * dark]);
      for (const p of this.snow) {
        const x = wrap(p.x - cam.x * p.z, vw + 40) - 20; const y = wrap(p.y - cam.y * p.z + this.t * p.v, vh + 40) - 20;
        g.beginPath(); g.arc(x, y, p.r, 0, Math.PI * 2); g.fill();
      }
    }
    // world-space: schools, bubbles
    g.setTransform(k, 0, 0, k, -cam.x * k, -cam.y * k);
    const inView = (x, y, m = 60) => x > cam.x - m && x < cam.x + vw + m && y > cam.y - m && y < cam.y + vh + m;
    for (const sc of this.schools) {
      if (!inView(sc.cx, sc.cy, 400)) continue;
      for (const f of sc.fish) {
        if (!inView(f.x, f.y)) continue;
        g.save(); g.translate(f.x, f.y); g.scale(f.dir * f.sc, f.sc);
        if (sc.img?.complete && sc.img.naturalWidth) g.drawImage(sc.img, -sc.imgW / 2, -sc.imgH / 2, sc.imgW, sc.imgH);
        else { const sp = this.sprite(f.col); g.drawImage(sp.c, -sp.w / 2, -sp.h / 2, sp.w, sp.h); }
        g.restore();
      }
    }
    g.lineWidth = 1.4;
    for (const b of this.bubbles) {
      if (!inView(b.x, b.y)) continue;
      const a = Math.min(1, (b.max - b.life) * 2);
      g.globalAlpha = a; g.strokeStyle = this.col.rim; g.fillStyle = this.col.bubble;
      g.beginPath(); g.arc(b.x, b.y, b.r, 0, Math.PI * 2); g.stroke();
      g.beginPath(); g.arc(b.x - b.r * 0.35, b.y - b.r * 0.35, b.r * 0.3, 0, Math.PI * 2); g.fill();
    }
    g.globalAlpha = 1;
    if (dark > 0.01) {
      g.setTransform(dpr, 0, 0, dpr, 0, 0);
      const W = this.vwPx; const H = this.vhPx;
      const lx = lamp?.x ?? W / 2; const ly = lamp?.y ?? H / 2; const r = lamp?.r ?? 300;
      const grad = g.createRadialGradient(lx, ly, r * 0.5, lx, ly, r);
      grad.addColorStop(0, this.col.deepClear); grad.addColorStop(1, this.col.deep);
      g.globalAlpha = dark; g.fillStyle = grad; g.fillRect(0, 0, W, H); g.globalAlpha = 1;
      g.setTransform(k, 0, 0, k, 0, 0);
      for (const p of this.motes) {                    // slow breathing glow above the dark, period ≈ 8 s (never flashes)
        const a = dark * (0.35 + 0.35 * Math.sin(this.t * 0.8 + p.ph));
        const x = wrap(p.x - cam.x * p.z, vw + 40) - 20; const y = wrap(p.y - cam.y * p.z - this.t * 4, vh + 40) - 20;
        g.globalAlpha = Math.max(0, a); g.fillStyle = this.col.glow[p.c];
        g.beginPath(); g.arc(x, y, p.r, 0, Math.PI * 2); g.fill();
      }
      g.globalAlpha = 1;
    }
  }
  get count() { return this.bubbles.length + this.schools.reduce((n, s) => n + s.fish.length, 0); }
}
