// Mořský svět — full-screen illustrated scenes (title, home, quiz, summary) drawn as TWO layers for iPad speed:
//   1. a static <img> of the scene with the animated groups hidden (rasterised once, never repainted);
//   2. an inline copy where only the animated groups are visible, so a frame repaints just those groups.
// Reduced motion: only the static image, with everything shown (e.g. the dolphin frozen mid-leap, DESIGN §10.3).
import { artText, charEl } from './assets.js';
import { h, reduced } from './ui.js';

const urls = new Map();
function staticUrl(name, hide) {
  const key = `${name}|${hide.join(',')}`;
  if (urls.has(key)) return urls.get(key);
  const doc = new DOMParser().parseFromString(artText(name), 'image/svg+xml');
  for (const sel of hide) for (const el of doc.querySelectorAll(sel)) el.setAttribute('visibility', 'hidden');
  const url = URL.createObjectURL(new Blob([new XMLSerializer().serializeToString(doc)], { type: 'image/svg+xml' }));
  urls.set(key, url);
  return url;
}

/** Mount scene `name` into `host`. `animated` = selectors of groups that move (DESIGN §10.3). */
export function mountScene(host, name, animated = []) {
  if (!artText(name)) return null;
  const anim = !reduced() && animated.length > 0;
  const svg0 = new DOMParser().parseFromString(artText(name), 'image/svg+xml').documentElement;
  const par = svg0.getAttribute('preserveAspectRatio') || 'xMidYMid slice';
  host.classList.add('scene-host');
  const img = h(`<img class="scene-static" alt="" decoding="async" src="${staticUrl(name, anim ? animated : [])}">`);
  img.style.objectPosition = /YMax/.test(par) ? '50% 100%' : '50% 50%';
  host.append(img);
  let live = null;
  if (anim) {
    live = charEl(name);
    live.classList.add('scene-live');
    live.setAttribute('visibility', 'hidden');
    for (const sel of animated) for (const el of live.querySelectorAll(sel)) el.setAttribute('visibility', 'visible');
    host.append(live);
  }
  const vb = (svg0.getAttribute('viewBox') || '0 0 1600 1000').split(/[\s,]+/).map(Number);
  return { img, live, vb, ymax: /YMax/.test(par), root: svg0 };
}

/** Scene (viewBox) point → screen px inside a host of size W×H (slice mapping). */
export function toScreen(sc, x, y, W, H) {
  const [vx, vy, vw, vh] = sc.vb; const k = Math.max(W / vw, H / vh);
  const ox = (W - vw * k) / 2; const oy = sc.ymax ? H - vh * k : (H - vh * k) / 2;
  return { x: (x - vx) * k + ox, y: (y - vy) * k + oy, k };
}

/** The title dolphin leaps along data-arc="x0 y0 x1 y1 h" about every 8 s (1.6 s jump), splash at entry and exit. */
export function startDolphin(sc) {
  if (!sc?.live) return () => {};
  const d = sc.live.querySelector('.dolphin'); const sp = sc.live.querySelector('.splash');
  const arc = (sc.root.getAttribute('data-arc') || '').split(/\s+/).map(Number);
  if (!d || arc.length !== 5) return () => {};
  const [x0, y0, x1, y1, hh] = arc;
  const [px, py] = (d.getAttribute('data-pivot') || '640 410').split(/\s+/).map(Number);
  d.removeAttribute('transform');
  d.style.opacity = '0';
  const frames = [];
  for (let i = 0; i <= 24; i++) {
    const u = i / 24; const x = x0 + (x1 - x0) * u; const y = y0 + (y1 - y0) * u - hh * 4 * u * (1 - u);
    const dx = x1 - x0; const dy = (y1 - y0) - hh * 4 * (1 - 2 * u);
    frames.push({ transform: `translate(${(x - px).toFixed(1)}px, ${(y - py).toFixed(1)}px) rotate(${(Math.atan2(dy, dx) * 180 / Math.PI).toFixed(1)}deg)`, opacity: i === 0 || i === 24 ? 0 : 1 });
  }
  const [sx, sy] = (sp?.getAttribute('data-pivot') || `${x0} ${y0}`).split(/\s+/).map(Number);
  const splash = (x) => sp?.animate([{ transform: `translate(${x - sx}px, 0) scale(0)`, opacity: 0 }, { transform: `translate(${x - sx}px, 0) scale(1)`, opacity: 1, offset: 0.4 }, { transform: `translate(${x - sx}px, 0) scale(0)`, opacity: 0 }], { duration: 700, easing: 'ease-out' });
  if (sp) sp.style.opacity = '0';
  const jump = () => {
    if (!d.isConnected) return;
    d.animate(frames, { duration: 1600, easing: 'linear' });
    splash(x0); setTimeout(() => splash(x1), 1450);
  };
  const t0 = setTimeout(jump, 1800); const iv = setInterval(jump, 8000);
  return () => { clearTimeout(t0); clearInterval(iv); };
}

/** The logo for the current language (inline: letters bob + bubbles rise). */
export function logoEl(lang) {
  const name = `logo-${lang === 'en' ? 'en' : 'cs'}`;
  return artText(name) ? charEl(name) : h('<span></span>');
}
export const TITLE_ANIM = ['.sun-rays', '.sun-glow', '.cloud', '.gull', '.boat', '.waves-front', '.refraction', '.uw-rays', '.school', '.jelly', '.whale-far', '.kelp', '.sway', '.bubbles', '.dolphin', '.splash', '.turtle'];
export const HOME_ANIM = ['.sun-rays', '.sun-glow', '.cloud', '.gull', '.boat', '.waves-front', '.refraction', '.uw-rays', '.school', '.kelp', '.sway', '.bubbles', '.peek'];
export const BG_ANIM = ['.uw-rays', '.bubbles', '.sway', '.kelp'];
