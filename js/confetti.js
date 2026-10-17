// Mořský svět — the one celebration (end of a dive only, BRIEF §2): bubbles and little stars, 600–900 ms.
// Colours come from design tokens (read at run time), never from literals.
import { cssVar, reduced } from './ui.js';

let running = null;
export function celebrate({ duration = 850, tokens = ['--ms-cele-1', '--ms-cele-2', '--ms-cele-3', '--ms-cele-4'] } = {}) {
  stop();
  if (reduced()) return Promise.resolve();
  const colors = tokens.map((n) => cssVar(n)).filter(Boolean);
  const c = document.createElement('canvas');
  c.className = 'celebrate'; c.setAttribute('aria-hidden', 'true');
  const dpr = Math.min(2, devicePixelRatio || 1); const W = innerWidth; const H = innerHeight;
  c.width = W * dpr; c.height = H * dpr;
  document.body.append(c);
  const g = c.getContext('2d'); g.scale(dpr, dpr);
  const parts = Array.from({ length: 70 }, (_, i) => ({
    x: W * (0.15 + 0.7 * Math.random()), y: H * (0.55 + 0.4 * Math.random()),
    vx: (Math.random() - 0.5) * 220, vy: -(260 + Math.random() * 420), r: 4 + Math.random() * 9,
    star: i % 3 === 0, col: colors[i % Math.max(1, colors.length)] || 'white', rot: Math.random() * 6,
  }));
  const t0 = performance.now();
  return new Promise((resolve) => {
    let raf = 0;
    const frame = (now) => {
      const t = (now - t0) / 1000; const life = t / (duration / 1000);
      g.clearRect(0, 0, W, H);
      g.globalAlpha = Math.max(0, 1 - Math.max(0, life - 0.6) / 0.4);
      for (const p of parts) {
        const x = p.x + p.vx * t; const y = p.y + p.vy * t + 300 * t * t;
        if (p.star) {
          g.save(); g.translate(x, y); g.rotate(p.rot + t * 3); g.fillStyle = p.col; g.beginPath();
          for (let k = 0; k < 10; k++) { const rr = k % 2 ? p.r * 0.45 : p.r; const a = (k * Math.PI) / 5; g.lineTo(Math.cos(a) * rr, Math.sin(a) * rr); }
          g.closePath(); g.fill(); g.restore();
        } else {
          g.strokeStyle = p.col; g.lineWidth = 2; g.beginPath(); g.arc(x, y, p.r, 0, Math.PI * 2); g.stroke();
        }
      }
      if (life < 1) raf = requestAnimationFrame(frame); else { c.remove(); running = null; resolve(); }
    };
    running = { stop: () => { cancelAnimationFrame(raf); c.remove(); running = null; resolve(); } };
    raf = requestAnimationFrame(frame);
  });
}
export function stop() { running?.stop(); }
