// Mořský svět — Můj kousek moře (BRIEF §4.4): found creatures are released from the drawer into the child's
// own scene, where they swim by their kind. Drag, or tap + tap. Day / night (deep creatures glow at night).
// Tap a creature = it says its name; hold = its card. Placement is saved.
import { species, byId, charEl, hasArt, loadArt, viewBox, floorFrac } from './assets.js';
import { motion, parseMotion, displayW } from './dive/world.js';
import { h, icon, esc, say, replay, reduced, nameOf, anim } from './ui.js';
import { t } from './i18n.js';
import { go } from './router.js';
import { openCard, cardOpen } from './card.js';
import { pressDrag, inside } from './drag.js';
import * as store from './store.js';
import * as sound from './sound.js';
import { maybeTired } from './tired.js';

let S = null;
const FLOOR_DEFAULT = 0.86; const SURF = 0.07;

export async function mount(root, params = {}) {
  await Promise.all([loadArt('my-sea-day'), loadArt('my-sea-night')]);
  const sc = store.getScene();
  const el = h(`<div class="sea${sc.night ? ' night' : ''}">
    <div class="sea-scene"><div class="sea-bg day"></div><div class="sea-bg night"></div><div class="sea-life"></div></div>
    <div class="topbar">
      <button class="btn round main paper" data-act="home" aria-label="${esc(t('nav.home'))}">${icon('home')}</button>
      <h1 class="title-pill">${esc(t('sea.title'))}</h1>
      <button class="btn round main paper daynight" data-act="night" aria-pressed="${sc.night}" aria-label="${esc(t(sc.night ? 'sea.day' : 'sea.night'))}">${icon(sc.night ? 'day' : 'night')}</button>
      <button class="btn round main paper" data-act="replay" aria-label="${esc(t('nav.replay'))}">${icon('speaker')}</button>
    </div>
    <div class="drawer" role="list" aria-label="${esc(t('sea.drawer'))}"></div>
  </div>`);
  root.append(el);
  for (const k of ['day', 'night']) if (hasArt(`my-sea-${k}`)) el.querySelector(`.sea-bg.${k}`).append(charEl(`my-sea-${k}`));
  const fy = Number(el.querySelector('.sea-bg.day svg')?.getAttribute('data-floor-y'));
  S = { el, root, scene: el.querySelector('.sea-scene'), life: el.querySelector('.sea-life'), drawer: el.querySelector('.drawer'),
    placed: [], selected: null, floorY: Number.isFinite(fy) && fy > 0 ? fy : null, raf: 0, t: 0, last: performance.now(), fresh: params.fresh || [] };
  for (const p of sc.placed) if (byId.has(p.id) && store.isFound(p.id)) addCreature(p.id, p.x, p.y);
  renderDrawer();
  el.addEventListener('click', onClick);
  S.scene.addEventListener('pointerup', onSceneTap);
  S.raf = requestAnimationFrame(frame);
  const found = store.foundCount();
  say(found ? ['ui.seaIntro'] : ['ui.seaEmpty']);
  window.__morsky.sea = { placed: () => S?.placed.map((p) => ({ id: p.id, x: p.nx, y: p.ny })), place: (id, nx, ny) => { place(id, nx, ny); } };
}
export function unmount() { if (!S) return; cancelAnimationFrame(S.raf); S = null; if (window.__morsky) delete window.__morsky.sea; }

function renderDrawer() {
  const placedIds = new Set(S.placed.map((p) => p.id));
  S.drawer.replaceChildren(...species.map((sp) => {
    const found = store.isFound(sp.id);
    const b = h(`<button class="drawer-item${found ? '' : ' unknown'}${placedIds.has(sp.id) ? ' placed' : ''}${S.fresh.includes(sp.id) && !placedIds.has(sp.id) ? ' fresh' : ''}${S.selected === sp.id ? ' selected' : ''}"
      role="listitem" data-id="${esc(sp.id)}" aria-label="${esc(found ? nameOf(sp) : '?')}"></button>`);
    b.append(charEl(sp.id));
    b.addEventListener('pointerdown', (e) => {
      if (!found) return;
      pressDrag(e, b, {
        ghost: () => { const g = h('<div class="ghost"></div>'); g.append(charEl(sp.id)); return g; },
        onDrop: (x, y) => { if (inside(S.scene, x, y)) { const r = S.scene.getBoundingClientRect(); place(sp.id, (x - r.left) / r.width, (y - r.top) / r.height); } },
      });
    });
    return b;
  }));
}

function place(id, nx, ny) {
  const ex = S.placed.find((p) => p.id === id);
  if (ex) { ex.el.remove(); S.placed.splice(S.placed.indexOf(ex), 1); }
  addCreature(id, nx, ny, true);
  S.selected = null; S.fresh = S.fresh.filter((x) => x !== id);
  save(); renderDrawer();
  sound.play('bubble'); say([`sp.${id}.name`]);
}

function addCreature(id, nx, ny, splash = false) {
  const sp = byId.get(id); const { kind } = parseMotion(sp.motion);
  const svg = charEl(id); const vb = viewBox(svg); const ff = floorFrac(svg);
  const w = displayW(sp.sizeCm) * 0.62; const hh = w * vb.h / vb.w;
  const el = h(`<div class="cr sea-cr m-${kind}" data-id="${esc(id)}" style="width:${w.toFixed(0)}px;height:${hh.toFixed(0)}px"><div class="cr-in"></div></div>`);
  el.firstChild.append(svg);
  const floorKind = ['crawl', 'crawl-side', 'sway'].includes(kind);
  const p = { id, sp, el, kind, nx, ny, w, h: hh, floorKind, ay: floorKind ? (ff ?? 0.94) * hh : hh / 2, tf: '' };
  el.addEventListener('pointerdown', (e) => {
    e.stopPropagation();
    pressDrag(e, el, {
      ghost: () => { const g = h('<div class="ghost"></div>'); g.append(charEl(id)); return g; },
      onTap: () => { sound.play('bubble'); el.classList.remove('react'); void el.offsetWidth; el.classList.add('react'); say([`sp.${id}.name`]); },
      onLong: () => { if (!cardOpen()) { sound.play('tap'); openCard(id).then(() => maybeTired()); } },
      onDrop: (x, y) => {
        if (inside(S.drawer, x, y)) { el.remove(); S.placed.splice(S.placed.indexOf(p), 1); save(); renderDrawer(); sound.play('pop'); return; }
        if (inside(S.scene, x, y)) { const r = S.scene.getBoundingClientRect(); p.nx = (x - r.left) / r.width; p.ny = (y - r.top) / r.height; save(); }
      },
    });
  });
  S.life.append(el); S.placed.push(p);
  if (splash && !reduced()) anim(el.firstChild, [{ transform: 'scale(.3)', opacity: 0 }, { transform: 'scale(1)', opacity: 1 }], { duration: 420, easing: 'cubic-bezier(.22,1,.36,1)' });
}

function save() { store.setScene({ night: S.el.classList.contains('night'), placed: S.placed.map((p) => ({ id: p.id, x: p.nx, y: p.ny })) }); }

function onSceneTap(e) {
  if (!S.selected || e.target.closest('.sea-cr')) return;
  const r = S.scene.getBoundingClientRect();
  place(S.selected, (e.clientX - r.left) / r.width, (e.clientY - r.top) / r.height);
}

function onClick(e) {
  const b = e.target.closest('[data-act], .drawer-item'); if (!b) return;
  if (b.classList.contains('drawer-item')) {
    const id = b.dataset.id;
    if (!store.isFound(id)) { sound.play('tap'); say(['ui.seaUnknown']); return; }
    S.selected = S.selected === id ? null : id; sound.play('tap'); renderDrawer();
    if (S.selected) say([`sp.${id}.name`]);
    return;
  }
  const a = b.dataset.act; sound.play('tap');
  if (a === 'home') go('home');
  else if (a === 'replay') replay();
  else if (a === 'night') {
    const night = !S.el.classList.contains('night');
    S.el.classList.toggle('night', night);
    b.setAttribute('aria-pressed', String(night)); b.setAttribute('aria-label', t(night ? 'sea.day' : 'sea.night'));
    b.innerHTML = icon(night ? 'day' : 'night');
    save(); say([night ? 'ui.seaNight' : 'ui.seaDay']);
  }
}

function frame(now) {
  if (!S) return;
  const dt = Math.min(0.05, (now - S.last) / 1000); S.last = now; S.t += dt;
  const W = S.scene.clientWidth; const H = S.scene.clientHeight; const rm = reduced();
  const FLOOR = S.floorY ? (H - (1000 - S.floorY) * Math.max(W / 1600, H / 1000)) / H : FLOOR_DEFAULT;
  for (const p of S.placed) {
    let x0 = p.nx * W; let y0 = p.ny * H;
    if (p.floorKind) y0 = FLOOR * H; else if (p.kind === 'surface') y0 = SURF * H + p.h * 0.2;
    x0 = Math.min(W - p.w / 2, Math.max(p.w / 2, x0));
    if (!p.floorKind && p.kind !== 'surface') y0 = Math.min(FLOOR * H - p.h / 2, Math.max(SURF * H + p.h / 2, y0));
    const range = Math.min(W * 0.18, 160);
    const c = { kind: p.kind === 'jump' ? 'swim' : p.kind === 'jet' ? 'hover' : p.kind, x0, y0, range, speed: p.kind === 'glide' ? 24 : p.floorKind ? 10 : 34,
      phase: (p.id.length * 1.7) % 6.28, floorAnchored: p.floorKind };
    const m = motion(c, S.t, rm);
    const x = Math.min(W - p.w / 2, Math.max(p.w / 2, m.x));
    const tf = `translate3d(${(x - p.w / 2).toFixed(1)}px,${(m.y - p.ay).toFixed(1)}px,0)`;
    if (tf !== p.tf) { p.el.style.transform = tf; p.tf = tf; }
    const itf = `scaleX(${m.dir})`;
    if (itf !== p.itf) { p.el.firstChild.style.transform = itf; p.itf = itf; }
  }
  S.raf = requestAnimationFrame(frame);
}
