// Mořský svět — Ponor (BRIEF §4.2): side view, the diver swims left → right while the seabed slopes down
// through four zones. DOM/SVG for characters (CSS transforms only), canvas 2D for particles, one rAF loop.
// Layers (back → front): water gradient · sky + surface band · far/mid parallax · world (seabed, patches, trash,
// creatures, turtle, diver) · particles canvas · darkness with the headlamp hole · deep glow copies · near layer · HUD.
import { species, byId, zoneById, trash as trashData, charEl, svgEl, hasArt, loadArt, artText, viewBox, spanFrac, floorFrac, anchorFrac } from '../assets.js';
import * as W from './world.js';
import { Particles } from './particles.js';
import { openCard, cardOpen } from '../card.js';
import { h, icon, esc, say, hush, replay, reduced, sleep, cssVar, num, measure, parseColor, rgba, mix, nameOf, anim } from '../ui.js';
import { t } from '../i18n.js';
import * as store from '../store.js';
import * as sound from '../sound.js';
import { go } from '../router.js';
import { effectiveLevel, checkLevelUp } from '../levels.js';
import { maybeTired } from '../tired.js';
import { celebrate } from '../confetti.js';
import { mountScene, BG_ANIM } from '../scene.js';
import { phraseText } from '../speech.js';
import { getLang } from '../i18n.js';

let S = null;

const LAYERS = ['far', 'mid', 'near'];
const PATCH_ZONES = ['utes', 'chaluhy', 'hlubiny'];      // DESIGN §0.11: the open sea has no patch (a school arrives)

// ------------------------------------------------------------------ water colour (tokens → interpolated)
// Each zone has top / mid / low stops (tokens); the colour at a point follows how far down the water column it is,
// and zones cross-fade over the transition tiles (W.zoneWeight).
function waterStops() {
  const c = (n) => parseColor(cssVar(n));
  return W.ZONE_IDS.map((z) => { const p = z === 'sire-more' ? 'sire' : z; return [c(`--${p}-top`), c(`--${p}-mid`), c(`--${p}-low`)]; });
}
function waterColor(stops, x, y) {
  const f = W.clamp(y / Math.max(1, W.floorY(x)), 0, 1);
  let acc = [0, 0, 0, 0]; let sum = 0;
  for (let k = 0; k < stops.length; k++) {
    const w = W.zoneWeight(k, x); if (w <= 0) continue;
    const st = stops[k]; const col = f < 0.5 ? mix(st[0], st[1], f / 0.5) : mix(st[1], st[2], (f - 0.5) / 0.5);
    acc = acc.map((v, i) => v + col[i] * w); sum += w;
  }
  return acc.map((v) => v / (sum || 1));
}

// ------------------------------------------------------------------ build
/** Fallback seabed for a segment whose tile art is missing: a filled path along the profile. */
function seabedFallback(sg) {
  const x0 = sg.x0 - 2; const x1 = sg.x0 + sg.w + 2;
  const pts = []; for (let x = x0; x <= x1; x += 32) pts.push([x, W.floorY(x)]);
  const top = Math.min(...pts.map((q) => q[1])) - 10; const bot = Math.max(...pts.map((q) => q[1])) + 1400;
  const d = `M${pts.map(([x, y]) => `${(x - x0).toFixed(0)} ${(y - top).toFixed(1)}`).join(' L')} L${x1 - x0} ${bot - top} L0 ${bot - top} Z`;
  return `<svg class="seabed z-${sg.zone}${sg.floorNone ? ' none' : ''}" style="left:${x0}px;top:${top}px;width:${x1 - x0}px;height:${bot - top}px" viewBox="0 0 ${x1 - x0} ${bot - top}" preserveAspectRatio="none" aria-hidden="true"><path class="bed" d="${d}"/></svg>`;
}
/** Floor tiles (world plane, DESIGN §6.4) + the solid ground below each (data-fill), or the fallback path. */
function buildFloor(world) {
  for (const sg of W.profile().segs) {
    const name = `ponor/${sg.name}`;
    if (hasArt(name)) {
      if (sg.fill) world.append(h(`<div class="ground" style="left:${sg.x0 - 1}px;top:${sg.top + sg.h - 2}px;width:${sg.w + 2}px;height:1600px;background:${esc(sg.fill)}"></div>`));
      const img = h(`<img class="floor-tile" alt="" decoding="async" src="art/${name}.svg" style="left:${sg.x0}px;top:${sg.top}px;width:${sg.w}px;height:${sg.h}px">`);
      world.append(img);
    } else if (!sg.floorNone) world.insertAdjacentHTML('beforeend', seabedFallback(sg));
    // caustics: faint light on the sunlit seabed only (reef + kelp), never over the open water column
    if (!sg.floorNone && ['utes', 'chaluhy'].includes(sg.zone)) {
      const ys = sg.ys.map((y) => sg.top + y); const lo = Math.min(...ys); const hi = Math.max(...ys);
      world.append(h(`<div class="caustic-strip" style="left:${sg.x0}px;top:${(lo - 170).toFixed(0)}px;width:${sg.w}px;height:${(hi - lo + 260).toFixed(0)}px"><i></i></div>`));
    }
  }
}
/** Kelp props in the kelp forest (nested sway groups `.kelp-seg`, pivots applied by charEl). */
function buildKelp(world) {
  const kinds = ['kelp-1', 'kelp-2', 'kelp-3'].filter((k) => hasArt(`ponor/${k}`));
  if (!kinds.length) return;
  const z = W.profile().zones[1];
  for (let x = z.x0 + 900, i = 0; x < z.x1 - 300; x += 300 + ((i * 97) % 160), i++) {
    const el = charEl(`ponor/${kinds[i % kinds.length]}`); const vb = viewBox(el);
    const hh = 520 + ((i * 53) % 180); const ww = hh * vb.w / vb.h;
    const wrap = h(`<div class="kelp-prop" style="left:${(x - ww / 2).toFixed(0)}px;top:${(W.floorY(x) - hh * 0.985).toFixed(0)}px;width:${ww.toFixed(0)}px;height:${hh}px;--i:${i}"></div>`);
    wrap.append(el); world.append(wrap);
  }
}
async function loadProfile() {
  const names = [...new Set(W.SEQUENCE)];
  await Promise.all([...names.map((n) => loadArt(`ponor/${n}`)), ...['kelp-1', 'kelp-2', 'kelp-3'].map((n) => loadArt(`ponor/${n}`))]);
  const meta = {};
  for (const n of names) { const txt = artText(`ponor/${n}`); const m = txt && W.parseTileMeta(txt); if (m) meta[n] = m; }
  W.setProfile(W.buildProfile(meta));
}

function makeCreature(sp, k, i, n) {
  const c = W.placeCreature(sp, k, i, n);
  const svg = charEl(sp.id);
  const vb = viewBox(svg); const span = spanFrac(svg); const ff = floorFrac(svg);
  const elW = c.w / Math.max(0.25, span.f1 - span.f0); const elH = elW * vb.h / vb.w;
  const ax = elW / 2; const ay = c.floorAnchored ? (ff ?? 0.94) * elH : elH / 2;
  const zone = W.ZONE_IDS[k];
  const deep = zone === 'hlubiny';
  const pad = Math.max(0, (110 - Math.min(elW, elH)) / 2);
  const el = h(`<div class="cr m-${c.kind}" data-id="${esc(sp.id)}" data-zone="${zone}" style="width:${elW.toFixed(0)}px;height:${elH.toFixed(0)}px;--pad:${pad.toFixed(0)}px"><div class="cr-in"></div></div>`);
  el.firstChild.append(svg);
  let glow = null;
  if (deep && svg.querySelector('.glow')) {             // glowing copy above the darkness (only the light shows)
    glow = h(`<div class="cr cr-glow m-${c.kind}" data-id="${esc(sp.id)}" style="width:${elW.toFixed(0)}px;height:${elH.toFixed(0)}px;--pad:${pad.toFixed(0)}px"><div class="cr-in"></div></div>`);
    glow.firstChild.append(charEl(sp.id));
  }
  return { sp, c, el, glow, inner: el.firstChild, ginner: glow?.firstChild, elW, elH, ax, ay, x: c.x0, y: c.y0, dir: 1, rot: 0,
    k, zone, deep, vis: null, state: '', faceUntil: 0, faceDir: 1, tf: '', itf: '' };
}

function buildWorld(root) {
  const lvl = effectiveLevel();
  const bars = W.ZONE_IDS.map((z) => W.zoneSpecies(species, z, lvl));
  const creatures = [];
  bars.forEach((list, k) => {
    const spawn = list.filter((s) => s.id !== 'zelva');
    spawn.forEach((sp, i) => creatures.push(makeCreature(sp, k, i, spawn.length)));
  });
  const trashSpots = W.placeTrash(trashData.map((x) => x.id)).map((tr, i) => ({ ...tr, idx: i, done: false }));
  return { bars, creatures, trashSpots };
}

// ------------------------------------------------------------------ mount
export async function mount(root) {
  await Promise.all([loadProfile(), ...PATCH_ZONES.map((z) => loadArt(`ponor/patch-${z}`)), ...W.ZONE_IDS.map((z) => loadArt(`ponor/${z}-near`))]);
  const rm = reduced();
  const view = h(`<div class="dive" data-zone="utes">
    <div class="dv-view" aria-label="${esc(t('home.dive'))}">
      <div class="dv-water"></div>
      <div class="dv-sky"><div class="dv-sun"></div></div>
      <div class="dv-par far"></div><div class="dv-par mid"></div>
      <div class="dv-rays"><img alt="" src="art/ponor/rays.svg" decoding="async"></div>
      <div class="dv-surface"></div>
      <div class="dv-world"></div>
      <canvas class="dv-particles" aria-hidden="true"></canvas>
      <div class="dv-world dv-glow"></div>
      <div class="dv-par near"></div>
    </div>
    <div class="dv-hud">
      <button class="btn round main paper hud-home" data-act="surface" data-ta="dive.surface" aria-label="${esc(t('dive.surface'))}">${icon('up')}</button>
      <div class="goal-bar" role="group" data-ta="dive.goal" aria-label="${esc(t('dive.goal'))}"><span class="goal-zone" data-zone="utes">${icon('zone-utes')}</span><div class="goal-chips"></div><div class="goal-dots"></div></div>
      <button class="btn round main paper hud-replay" data-act="replay" data-ta="nav.replay" aria-label="${esc(t('nav.replay'))}">${icon('speaker')}</button>
      <div class="gauge" aria-label="${esc(t('dive.depth'))}"><div class="gauge-track"></div><div class="gauge-diver"><span class="gauge-mask">${icon('depth')}</span><span class="gauge-m"></span></div></div>
      <button class="btn round touch paper hud-back" data-act="back" data-ta="dive.back" aria-label="${esc(t('dive.back'))}">${icon('back')}</button>
      <button class="btn round touch paper hud-net" data-act="net" data-ta="dive.trash" aria-label="${esc(t('dive.trash'))}">${icon('net')}<span class="net-n">0</span></button>
      <span class="hud-fwd-label" data-t="dive.forward" aria-hidden="true">${esc(t('dive.forward'))}</span>
      <button class="btn round hero primary hud-fwd" data-act="fwd" data-ta="dive.forward" aria-label="${esc(t('dive.forward'))}">${icon('swim-on')}</button>
      <button class="btn round hero primary hud-up" data-act="up" data-ta="dive.surface" aria-label="${esc(t('dive.surface'))}" hidden>${icon('up')}</button>
    </div>
  </div>`);
  root.append(view);
  const $ = (s) => view.querySelector(s);
  const world = $('.dv-world:not(.dv-glow)'); const glowLayer = $('.dv-glow');
  const { bars, creatures, trashSpots } = buildWorld(root);

  // seabed + kelp + gates + patches + trash
  buildFloor(world);
  buildKelp(world);
  view.querySelector('.dv-rays img').addEventListener('error', (e) => { e.target.remove(); }, { once: true });
  for (let k = 0; k < 3; k++) {
    world.append(h(`<div class="gate" data-k="${k}" style="left:${W.gateX(k) - 40}px;top:${W.minY(W.gateX(k)) - 40}px;height:${W.maxY(W.gateX(k)) - W.minY(W.gateX(k)) + 120}px"><i></i><i></i><i></i></div>`));
    world.append(h(`<div class="gate-arrow" data-k="${k}" style="left:${W.gateX(k) + 40}px;top:${(W.minY(W.gateX(k)) + W.maxY(W.gateX(k))) / 2}px" hidden>${icon(k === 2 ? 'down' : 'swim-on')}</div>`));
  }
  for (const tr of trashSpots) {
    const z = W.ZONE_IDS[tr.k];
    if (!tr.floating && PATCH_ZONES.includes(z) && hasArt(`ponor/patch-${z}`)) {
      const p = charEl(`ponor/patch-${z}`); const vb = viewBox(p); const ff = floorFrac(p) ?? 0.93;
      const pw = 400; const ph = pw * vb.h / vb.w;
      tr.patch = h(`<div class="patch" style="left:${tr.x - pw / 2}px;top:${W.floorY(tr.x) - ph * ff}px;width:${pw}px;height:${ph}px"></div>`);
      tr.patch.append(p); world.append(tr.patch);
    }
    tr.el = h(`<div class="trash-spot" data-trash="${tr.idx}" style="transform:translate3d(${tr.x - 45}px,${tr.y - 45}px,0)"></div>`);
    if (hasArt(`trash-${tr.id}`)) tr.el.append(charEl(`trash-${tr.id}`)); else tr.el.classList.add('no-art');
    world.append(tr.el);
  }
  for (const cr of creatures) { world.append(cr.el); if (cr.glow) glowLayer.append(cr.glow); }

  // guide turtle + diver
  const turtle = { x: W.START_X - 200, y: 150, dir: 1, el: h('<div class="guide-wrap" data-guide="1"><div class="cr-in"></div></div>'), talkUntil: 0 };
  if (hasArt('guide-turtle')) turtle.el.firstChild.append(charEl('guide-turtle'));
  const diverSvg = hasArt('diver') ? charEl('diver') : null;
  const diver = { x: W.START_X, y: 240, vx: 0, vy: 0, tx: W.START_X + 60, ty: 250, dir: 1, el: h('<div class="diver-wrap"><div class="cr-in"></div></div>'), svg: diverSvg };
  if (diverSvg) diver.el.firstChild.append(diverSvg);
  world.append(turtle.el, diver.el);

  // parallax layers (DESIGN §6.4): <zone>-far/-mid/-near.svg, 2048×768, seamless, screen-anchored vertically;
  // one group per zone, cross-faded by zone weight; tiles laid out in layout() once the view width is known
  const par = {};
  for (const L of LAYERS) {
    par[L] = $(`.dv-par.${L}`);
    for (const [k, z] of W.ZONE_IDS.entries()) {
      if (!(await tileExists(`art/ponor/${z}-${L}.svg`))) continue;
      par[L].append(h(`<div class="zl" data-k="${k}" data-src="art/ponor/${z}-${L}.svg"${L === 'near' && hasArt(`ponor/${z}-near`) ? ` data-inline="ponor/${z}-near"` : ''}></div>`));
    }
  }

  S = {
    root, view, $, world, glowLayer, creatures, trashSpots, bars, turtle, diver, par,
    parts: new Particles($('.dv-particles')), raf: 0, last: performance.now(), t: 0, rm,
    cam: { x: 0, y: -120 }, s: 1, vw: 1024, vh: 768, hold: 0, holdStart: 0, steer: null,
    found: new Set(), newFound: [], trashTaken: 0, goalMet: [false, false, false, false], zoneIdx: -1,
    depthSaid: 0, lastSpeech: 0, bumpSaid: -Infinity, pending: false, ending: false, free: false, stopped: false,
    stops: waterStops(), waterKey: '', gaugeY: -1, lampOn: false, fwdPulse: false,
    parF: { far: num('--parallax-far', 0.25), mid: num('--parallax-mid', 0.55), near: num('--parallax-near', 1.25) },
    deepDim: cssVar('--deep-dim'), fps: { n: 0, t0: performance.now(), last: 0 },
  };
  diver.ty = 250;
  layout();
  seedSchools();
  S.$('.gauge-track').insertAdjacentHTML('beforeend', W.GAUGE_LABELS.map((m) =>
    `<span class="tick" style="--at:${(W.gaugeFrac(m) * 100).toFixed(2)}"><b>${m}</b></span>`).join(''));
  layout();                                        // again: the tick list for the pill-overlap rule needs the ticks
  renderGoal(0);
  bindInput();
  addEventListener('resize', layout);
  addEventListener('speech:say', onSpeech);
  addEventListener('langchange', onDiveLang);
  addEventListener('keydown', onKey); addEventListener('keyup', onKeyUp);
  S.raf = requestAnimationFrame(frame);
  setTimeout(() => { if (S && !S.ending) say(['ui.diveIntro']); }, 400);
  exposeHooks();
}

export function unmount() {
  if (!S) return;
  cancelAnimationFrame(S.raf); S.stopped = true;
  removeEventListener('resize', layout); removeEventListener('speech:say', onSpeech); removeEventListener('langchange', onDiveLang);
  removeEventListener('keydown', onKey); removeEventListener('keyup', onKeyUp);
  document.querySelector('.dive-summary')?.remove();
  S = null;
  if (window.__morsky) delete window.__morsky.dive;
}

function onDiveLang() {        // chip names + gauge label follow the language; the dive itself goes on
  if (!S) return;
  for (const b of S.$('.goal-chips').children) b.setAttribute('aria-label', nameOf(byId.get(b.dataset.id)));
  S.gaugeLabel = null; S.gaugeY = -1;
}

function onSpeech(e) {
  if (!S) return;
  S.lastSpeech = performance.now();
  S.turtle.talkUntil = S.t + Math.min(6, 0.6 + (e.detail?.text?.length || 20) * 0.06);
}

const tileOk = new Map();
async function tileExists(url) {
  if (!tileOk.has(url)) tileOk.set(url, fetch(url, { method: 'HEAD' }).then((r) => r.ok && /svg/.test(r.headers.get('content-type') || '')).catch(() => false));
  return tileOk.get(url);
}

function layout() {
  if (!S) return;
  const vwPx = innerWidth; const vhPx = innerHeight;
  S.s = vhPx / W.VH; S.vw = vwPx / S.s; S.vh = W.VH;
  const dpr = Math.min(2, devicePixelRatio || 1);
  S.parts.resize(vwPx, vhPx, S.s, dpr);
  S.view.style.setProperty('--s', S.s.toFixed(4));
  // characters sized from tokens (--diver-h, --turtle-h are screen px → world units)
  const dh = measure('height', 'var(--diver-h)') / S.s || 180; const th = measure('height', 'var(--turtle-h)') / S.s || 110;
  for (const [o, hh] of [[S.diver, dh], [S.turtle, th]]) {
    const svg = o.el.querySelector('svg'); const vb = svg ? viewBox(svg) : { w: 2, h: 1 };
    o.w = hh * vb.w / vb.h; o.h = hh;
    o.el.style.width = `${o.w.toFixed(0)}px`; o.el.style.height = `${o.h.toFixed(0)}px`;
  }
  const bub = S.diver.svg ? anchorFrac(S.diver.svg, '.anchor-bubbles') : null;
  const lamp = S.diver.svg ? anchorFrac(S.diver.svg, '.anchor-lamp') : null;
  const net = S.diver.svg ? anchorFrac(S.diver.svg, '.anchor-net') : null;
  S.diver.anch = { bub: bub || { fx: 0.8, fy: 0.5 }, lamp: lamp || { fx: 0.78, fy: 0.3 }, net: net || { fx: 0.45, fy: 0.7 } };
  S.lampR = measure('width', 'var(--lamp-radius)') || 300;
  const gTrack = S.$('.gauge-track'); S.gaugeH = gTrack.clientHeight || 400; S.gaugeY = -1;
  S.ticks = [...gTrack.querySelectorAll('.tick')].map((el) => ({ el, y: (parseFloat(el.style.getPropertyValue('--at')) / 100) * S.gaugeH, off: false }));
  const gr = S.$('.gauge').getBoundingClientRect(); S.safeLeft = gr.right + 8;
  S.safeTop = S.$('.goal-bar').getBoundingClientRect().bottom + 6;
  // parallax tiles: for zone k, layer factor f, cover layer-space [x0·f − vw, x1·f + vw] with 2048-wide copies
  for (const L of LAYERS) {
    const f = S.parF[L];
    for (const g of S.par[L].querySelectorAll('.zl')) {
      const z = W.profile().zones[+g.dataset.k];
      const n0 = Math.floor((z.x0 * f - S.vw) / W.TILE_W); const n1 = Math.ceil((z.x1 * f + S.vw) / W.TILE_W);
      const want = []; for (let n = n0; n <= n1; n++) want.push(n);
      if (g.dataset.n !== want.join(',')) {
        g.dataset.n = want.join(',');
        // near tiles are inlined (DESIGN §0.10: g.near-item fades while it covers the diver or a target)
        g.replaceChildren(...want.map((n) => {
          if (!g.dataset.inline) return h(`<img class="tile" alt="" decoding="async" src="${g.dataset.src}" style="left:${n * W.TILE_W}px">`);
          const el = svgEl(g.dataset.inline); el.classList.add('tile'); el.style.left = `${n * W.TILE_W}px`; el.dataset.n = n; el.setAttribute('aria-hidden', 'true'); return el;
        }));
      }
    }
  }
  S.nearItems = [];
  for (const svg of S.par.near.querySelectorAll('svg.tile')) {
    const n = +svg.dataset.n; const k = +svg.parentElement.dataset.k;
    for (const it of svg.querySelectorAll('.near-item')) {
      let bb; try { bb = it.getBBox(); } catch { continue; }
      if (bb.width > 0) S.nearItems.push({ el: it, k, x: n * W.TILE_W + bb.x, y: bb.y, w: bb.width, h: bb.height, faded: false });
    }
  }
  S.waterKey = '';
}

function seedSchools() {
  const reef = ['--coral-orange', '--coral-yellow', '--coral-pink', '--coral-violet'].map((n) => cssVar(n));
  const silver = [cssVar('--surface-line'), cssVar('--sky-mid')];
  const P = S.parts;
  const z0 = W.profile().zones;
  P.addSchool({ x: 1100, y: 380, n: 11, range: 260, colors: reef });
  P.addSchool({ x: 2900, y: 480, n: 9, range: 220, colors: reef.slice(1) });
  P.addSchool({ x: z0[1].x0 + 2600, y: 650, n: 10, range: 300, colors: [cssVar('--kelp-light'), cssVar('--coral-yellow')] });
  const img = new Image(); img.src = 'art/ponor/school-fish.svg';
  const zs = W.profile().zones; const sx = zs[2].x0 + W.TILE_W * 1.2;
  P.addSchool({ x: sx, y: 520, n: 22, range: 520, colors: silver, speed: 80, img });
  P.addSchool({ x: sx + 1300, y: Math.min(1200, W.floorY(sx + 1300) - 400), n: 16, range: 420, colors: silver, speed: 70, img });
}

// ------------------------------------------------------------------ input
function worldPoint(clientX, clientY) { return { x: S.cam.x + clientX / S.s, y: S.cam.y + clientY / S.s }; }
function setTarget(x, y) { const c = W.clampDiver(x, y, gatesOpen()); S.diver.tx = c.x; S.diver.ty = c.y; S.wantX = x; }
const gatesOpen = () => [S.goalMet[0], S.goalMet[1], S.goalMet[2]];

function bindInput() {
  const v = S.$('.dv-view');
  let down = null;
  v.addEventListener('pointerdown', (e) => {
    if (S.ending || S.pending || cardOpen()) return;
    down = { x: e.clientX, y: e.clientY, t: performance.now(), id: e.pointerId, target: e.target };
    const hit = e.target.closest('.cr, .trash-spot, [data-guide]');
    if (!hit) { const p = worldPoint(e.clientX, e.clientY); setTarget(p.x, p.y); S.steer = e.pointerId; v.setPointerCapture?.(e.pointerId); }
  });
  v.addEventListener('pointermove', (e) => {
    if (S.steer !== e.pointerId) return;
    const p = worldPoint(e.clientX, e.clientY); setTarget(p.x, p.y);
  });
  const up = (e) => {
    if (S.steer === e.pointerId) S.steer = null;
    if (!down || down.id !== e.pointerId) return;
    const moved = Math.hypot(e.clientX - down.x, e.clientY - down.y) > 14;
    const target = down.target; down = null;
    if (moved || S.ending || S.pending || cardOpen()) return;
    const hit = target.closest?.('.cr, .trash-spot, [data-guide]');
    if (!hit) return;
    if (hit.dataset.guide) tapGuide();
    else if (hit.classList.contains('trash-spot')) tapTrash(S.trashSpots[+hit.dataset.trash]);
    else { const cr = S.creatures.find((c) => c.el === hit || c.glow === hit); if (cr) tapCreature(cr); }
  };
  v.addEventListener('pointerup', up); v.addEventListener('pointercancel', (e) => { if (S.steer === e.pointerId) S.steer = null; down = null; });

  const hud = S.$('.dv-hud');
  const fwd = S.$('.hud-fwd'); const back = S.$('.hud-back');
  for (const [btn, dir] of [[fwd, 1], [back, -1]]) {
    btn.addEventListener('pointerdown', (e) => { e.preventDefault(); if (S.ending || cardOpen()) return; S.hold = dir; S.holdStart = performance.now(); btn.setPointerCapture?.(e.pointerId); });
    const end = () => {
      if (S.hold !== dir) return;
      const quick = performance.now() - S.holdStart < 280; S.hold = 0;
      if (quick) { sound.play('tap'); tapArrow(dir); }
      else setTarget(S.diver.x + dir * 30, S.diver.y);
    };
    btn.addEventListener('pointerup', end); btn.addEventListener('pointercancel', end); btn.addEventListener('lostpointercapture', end);
  }
  hud.addEventListener('click', (e) => {
    const b = e.target.closest('[data-act]'); if (!b) return;
    const a = b.dataset.act;
    if (a === 'replay') replay();
    else if (a === 'surface' || a === 'up') { sound.play('tap'); surface(); }
    else if (a === 'net') { sound.play('tap'); say([`ui.trashCount.${Math.min(10, S.trashTaken)}`]); }
    else if (a === 'chip') {
      const id = b.dataset.id; sound.play('tap');
      say(S.found.has(id) ? [`sp.${id}.name`] : [`sp.${id}.where`]);
      // a gentle „show me“: the diver turns and swims part of the way toward an animal of this zone
      const cr = S.creatures.find((c) => c.sp.id === id);
      if (cr && !S.found.has(id) && !S.pending && W.zoneIndexAt(cr.x) === S.zoneIdx) setTarget(S.diver.x + (cr.x - S.diver.x) * 0.6, S.diver.y + (cr.y - S.diver.y) * 0.6);
    }
  });
}
const KEYS = { ArrowRight: [1, 0], ArrowLeft: [-1, 0], ArrowUp: [0, -1], ArrowDown: [0, 1] };
function onKey(e) {
  if (!S || S.ending || cardOpen() || !KEYS[e.key]) return;
  e.preventDefault(); S.keys = KEYS[e.key];
}
function onKeyUp(e) { if (S && KEYS[e.key]) S.keys = null; }

function tapArrow(dir) {
  const d = S.diver;
  if (dir < 0) { setTarget(d.x - 420, d.y); return; }
  const items = [...S.creatures.map((c) => ({ x: c.x, y: c.y, done: S.found.has(c.sp.id) })), ...S.trashSpots.map((tr) => ({ x: tr.x, y: tr.y - 60, done: tr.done }))];
  const lim = gatesOpen().reduce((m, open, k) => (m === null && !open ? W.gateX(k) - 60 : m), null) ?? W.endX();
  const n = W.nextInteresting(d.x, items, lim);
  if (n) setTarget(n.x - 180, n.y - 40); else setTarget(d.x + 520, d.y);
}

async function tapCreature(cr) {
  if (S.pending) return;
  S.pending = true;
  const id = cr.sp.id;
  react(cr);
  say([`sp.${id}.name`]);
  // the diver swims close (never touches): stop ~1.2 diver-widths away, on her side
  const side = S.diver.x < cr.x ? -1 : 1;
  setTarget(cr.x + side * (cr.c.w * 0.5 + S.diver.w * 0.55), cr.y - 10);
  const t0 = performance.now();
  while (S && !S.stopped && performance.now() - t0 < 1300 && Math.hypot(S.diver.x - S.diver.tx, S.diver.y - S.diver.ty) > 40) await sleep(60);
  if (!S || S.stopped) return;
  await discover(id, cr.el);
}
async function tapGuide() {
  if (S.pending || !byId.has('zelva')) { say(['ui.greet']); return; }
  S.pending = true;
  sound.play('bubble');
  S.turtle.el.classList.remove('react'); void S.turtle.el.offsetWidth; S.turtle.el.classList.add('react');
  say(['sp.zelva.name']);
  await sleep(500);
  if (S) await discover('zelva');
}
async function discover(id) {
  const isNew = store.addFound(id);
  S.found.add(id);
  if (isNew && !S.newFound.includes(id)) S.newFound.push(id);
  await openCard(id, { skipName: true });
  if (!S) return;
  S.pending = false;
  renderGoal(S.zoneIdx);
  checkGoal();
  if (checkLevelUp()) { sound.play('success'); setTimeout(() => say('ui.level2'), 300); }
  else maybeTired();
}

function react(cr) {
  cr.faceUntil = S.t + 1.4; cr.faceDir = S.diver.x < cr.x ? -1 : 1;
  sound.play('bubble');
  S.parts.emit(cr.x + cr.faceDir * cr.c.w * 0.35, cr.y - cr.elH * 0.2, 6, 14);
  cr.el.classList.remove('react'); void cr.el.offsetWidth; cr.el.classList.add('react');
  setTimeout(() => cr.el?.classList.remove('react'), 700);
}

async function tapTrash(tr) {
  if (!tr || tr.done || S.pending) return;
  S.pending = true;
  setTarget(tr.x - S.diver.w * 0.3, tr.y - S.diver.h * 0.35);
  const t0 = performance.now();
  while (S && !S.stopped && performance.now() - t0 < 2500 && Math.hypot(S.diver.x - tr.x, S.diver.y - tr.y) > 220) await sleep(60);
  if (!S || S.stopped) return;
  tr.done = true; S.trashTaken += 1;
  { const n = S.$('.net-n'); n.textContent = String(S.trashTaken); n.classList.remove('bump'); void n.offsetWidth; n.classList.add('bump'); }
  sound.play('pop');
  // fly into the net (anchor-net), then the place comes alive
  const d = S.diver; const nx = d.x - d.w / 2 + (d.dir > 0 ? d.anch.net.fx : 1 - d.anch.net.fx) * d.w; const ny = d.y - d.h / 2 + d.anch.net.fy * d.h;
  await anim(tr.el, [{ transform: `translate3d(${tr.x - 45}px,${tr.y - 45}px,0) scale(1)` }, { transform: `translate3d(${nx - 45}px,${ny - 45}px,0) scale(.25)`, opacity: 0.2 }],
    { duration: reduced() ? 1 : 420, easing: 'cubic-bezier(.55,0,1,.45)', fill: 'forwards' });
  tr.el.remove();
  S.diver.el.classList.add('net-full');
  if (tr.patch) tr.patch.classList.add('clean');
  sound.play('sparkle');
  S.parts.addSchool({ x: tr.x, y: Math.min(tr.y - 160, W.maxY(tr.x) - 60), n: 8, range: 120, colors: ['--coral-yellow', '--coral-pink', '--coral-orange'].map((n) => cssVar(n)) });
  S.parts.emit(tr.x, tr.y - 20, 10, 40);
  say(phraseText(`trash.${tr.id}`, getLang()) ? [`trash.${tr.id}`] : ['ui.trashTake']);
  S.pending = false;
}

// ------------------------------------------------------------------ goal bar + gates
function renderGoal(k) {
  if (!S) return;
  const list = S.bars[k] || [];
  const chips = S.$('.goal-chips');
  if (chips.dataset.k !== String(k) || chips.childElementCount !== list.length) {
    chips.dataset.k = String(k);
    chips.replaceChildren(...list.map((sp) => {
      const b = h(`<button class="chip" data-act="chip" data-id="${esc(sp.id)}" aria-label="${esc(nameOf(sp))}"></button>`);
      if (hasArt(sp.id)) b.append(charEl(sp.id));
      return b;
    }));
  }
  for (const b of chips.children) {
    const was = b.classList.contains('found'); const now = S.found.has(b.dataset.id);
    b.classList.toggle('found', now);
    if (now && !was && !reduced()) anim(b, [{ transform: 'scale(1)' }, { transform: 'scale(1.18)' }, { transform: 'scale(1)' }], { duration: 360 });
  }
  const goal = W.goalFor(list.length);
  const got = list.filter((sp) => S.found.has(sp.id)).length;
  S.$('.goal-dots').innerHTML = Array.from({ length: goal }, (_, i) => `<i class="${i < got ? 'on' : ''}"></i>`).join('');
}
function checkGoal() {
  W.ZONE_IDS.forEach((_, k) => {
    if (S.goalMet[k]) return;
    const list = S.bars[k];
    const got = list.filter((sp) => S.found.has(sp.id)).length;
    if (got < W.goalFor(list.length) || !list.length) return;
    S.goalMet[k] = true;
    if (k < 3) {
      S.world.querySelector(`.gate[data-k="${k}"]`)?.classList.add('open');
      const ar = S.world.querySelector(`.gate-arrow[data-k="${k}"]`); if (ar) ar.hidden = false;
      S.$('.hud-fwd').classList.add('pulse');
      if (k === S.zoneIdx) { sound.play('sparkle'); say(['ui.deeper']); }
    } else {
      S.$('.hud-up').hidden = false; sound.play('chime'); say(['ui.deepDone']);
    }
  });
}

// ------------------------------------------------------------------ loop
function frame(now) {
  if (!S || S.stopped) return;
  const dt = Math.min(0.05, (now - S.last) / 1000); S.last = now; S.t += dt;
  S.fps.n++; if (now - S.fps.t0 > 1000) { S.fps.last = Math.round((S.fps.n * 1000) / (now - S.fps.t0)); S.fps.n = 0; S.fps.t0 = now; }
  step(dt);
  S.raf = requestAnimationFrame(frame);
}

function step(dt) {
  const d = S.diver; const rm = S.rm;
  if (!S.ending) {
    if (S.hold) setTarget(d.x + S.hold * 260, d.ty);
    if (S.keys) setTarget(d.x + S.keys[0] * 220, d.y + S.keys[1] * 160);
  }
  // diver kinematics: ease toward the target, capped speed
  const maxV = rm ? 170 : 270;
  const dx = d.tx - d.x; const dy = d.ty - d.y; const dist = Math.hypot(dx, dy);
  const want = Math.min(maxV, dist * 2.4);
  const tvx = dist > 1 ? (dx / dist) * want : 0; const tvy = dist > 1 ? (dy / dist) * want : 0;
  const k = 1 - Math.exp(-dt * 5);
  d.vx += (tvx - d.vx) * k; d.vy += (tvy - d.vy) * k;
  d.x += d.vx * dt; d.y += d.vy * dt;
  if (!S.free) {
    const c = W.clampDiver(d.x, d.y, gatesOpen());
    if (c.bumped && (S.hold > 0 || (S.keys && S.keys[0] > 0) || S.wantX > c.x + 40)) bump();
    d.x = c.x; d.y = c.y;
  }
  if (Math.abs(d.vx) > 14) d.dir = d.vx > 0 ? 1 : -1;
  const speed = Math.hypot(d.vx, d.vy);
  const swimming = speed > 28;
  if (swimming !== d.swimming) { d.swimming = swimming; d.el.classList.toggle('swimming', swimming); }
  const dtf = `translate3d(${(d.x - d.w / 2).toFixed(1)}px,${(d.y - d.h / 2).toFixed(1)}px,0)`;
  if (dtf !== d.tf) { d.el.style.transform = dtf; d.tf = dtf; }
  const tilt = rm ? 0 : Math.max(-14, Math.min(14, (d.vy / maxV) * 16)) * d.dir;
  const itf = `scaleX(${d.dir}) rotate(${tilt.toFixed(1)}deg)`;
  if (itf !== d.itf) { d.el.firstChild.style.transform = itf; d.itf = itf; }
  // bubbles from the snorkel
  d.bubT = (d.bubT ?? 1) - dt;
  if (d.bubT <= 0) {
    d.bubT = swimming ? 1.1 + Math.random() * 0.6 : 1.8 + Math.random();
    const bx = d.x - d.w / 2 + (d.dir > 0 ? d.anch.bub.fx : 1 - d.anch.bub.fx) * d.w; const by = d.y - d.h / 2 + d.anch.bub.fy * d.h;
    S.parts.emit(bx, by, 2 + Math.floor(Math.random() * 3), 4);
  }

  // camera
  const ct = W.cameraTarget(d.x, d.y, S.vw, S.vh, S.free);
  const ck = 1 - Math.exp(-dt * (S.ending ? 3 : 3.2));
  S.cam.x += (ct.x - S.cam.x) * ck; S.cam.y += (ct.y - S.cam.y) * ck;
  const cx = S.cam.x; const cy = S.cam.y; const s = S.s;
  const wtf = `translate3d(${(-cx * s).toFixed(1)}px,${(-cy * s).toFixed(1)}px,0) scale(${s.toFixed(4)})`;
  S.world.style.transform = wtf; S.glowLayer.style.transform = wtf;
  const midX0 = cx + S.vw / 2;
  for (const L of LAYERS) {
    const f = S.parF[L];
    S.par[L].style.transform = `translate3d(${(-cx * f * s).toFixed(1)}px,0,0) scale(${s.toFixed(4)})`;
    for (const g of S.par[L].children) {
      const w = W.zoneWeight(+g.dataset.k, midX0);
      const q = w.toFixed(2);
      if (g.dataset.w !== q) { g.dataset.w = q; g.style.opacity = q; g.style.visibility = w > 0.01 ? 'visible' : 'hidden'; }
    }
  }
  // sky + surface band follow the camera vertically only
  const skyY = (-cy) * s;
  S.$('.dv-sky').style.transform = `translate3d(0,${(skyY - S.vh * 0.6 * s).toFixed(1)}px,0)`;
  S.$('.dv-surface').style.transform = `translate3d(${(-((cx * s) % (W.TILE_W * s))).toFixed(1)}px,${skyY.toFixed(1)}px,0)`;

  // creatures
  const midX = cx + S.vw / 2;
  for (const cr of S.creatures) {
    const near = Math.abs(cr.c.x0 - midX) < S.vw * 0.75 + cr.c.range + cr.elW;
    if (near !== cr.vis) { cr.vis = near; cr.el.classList.toggle('off', !near); cr.glow?.classList.toggle('off', !near); }
    if (!near) continue;
    const m = W.motion(cr.c, S.t, rm);
    if (cr.c.floorAnchored) m.y = W.floorY(m.x);
    else if (cr.c.kind === 'jet') m.y = Math.min(m.y, W.floorY(m.x) - cr.elH * 0.35);
    if (S.t < cr.faceUntil && cr.c.kind !== 'crawl-side') m.dir = cr.faceDir;
    cr.x = m.x; cr.y = m.y;
    const tf = `translate3d(${(m.x - cr.ax).toFixed(1)}px,${(m.y - cr.ay).toFixed(1)}px,0)`;
    if (tf !== cr.tf) { cr.el.style.transform = tf; if (cr.glow) cr.glow.style.transform = tf; cr.tf = tf; }
    const itf2 = `scaleX(${m.dir})${m.rot ? ` rotate(${m.rot.toFixed(1)}deg)` : ''}`;
    if (itf2 !== cr.itf) { cr.inner.style.transform = itf2; if (cr.ginner) cr.ginner.style.transform = itf2; cr.itf = itf2; }
    if (m.state !== cr.state) { cr.state = m.state; cr.el.dataset.state = m.state; if (cr.glow) cr.glow.dataset.state = m.state; if (m.state === 'jump') { sound.play('splash'); } }
  }

  // turtle guide: a little behind and above the diver
  const tu = S.turtle;
  const gx = d.x - d.dir * (d.w * 0.62); const gy = Math.max(W.minY(d.x) + 10, d.y - d.h * 0.55);
  const tk = 1 - Math.exp(-dt * 1.8);
  const ox = tu.x; tu.x += (gx - tu.x) * tk; tu.y += (gy - tu.y) * tk + (rm ? 0 : Math.sin(S.t * 1.3) * 6 * dt);
  if (Math.abs(tu.x - ox) > 0.4) tu.dir = tu.x > ox ? 1 : -1;
  // keep her clear of the depth gauge (left) and the goal bar (top)
  const rx = Math.max(tu.x, cx + (S.safeLeft || 0) / s + tu.w / 2); const ry = Math.max(tu.y, cy + (S.safeTop || 0) / s + tu.h / 2);
  tu.el.style.transform = `translate3d(${(rx - tu.w / 2).toFixed(1)}px,${(ry - tu.h / 2).toFixed(1)}px,0)`;
  tu.el.firstChild.style.transform = `scaleX(${tu.dir})`;
  const talking = S.t < tu.talkUntil && Math.floor(S.t * 4.4) % 2 === 0;
  if (talking !== tu.talking) { tu.talking = talking; tu.el.classList.toggle('talking', talking); }

  // zone change
  const zk = W.zoneIndexAt(d.x);
  if (zk !== S.zoneIdx) enterZone(zk);

  // depth: gauge, spoken marks, darkness, rays, water colour
  const m = W.depthM(d.x, d.y);
  const gy2 = W.gaugeFrac(m);
  if (Math.abs(gy2 - S.gaugeY) > 0.0015) {
    S.gaugeY = gy2;
    S.$('.gauge-diver').style.transform = `translate3d(0,calc(${(gy2 * 100).toFixed(2)} * var(--gauge-h) / 100),0)`;
    const mm = m < 10 ? Math.round(m) : m < 200 ? Math.round(m / 5) * 5 : Math.round(m / 50) * 50;
    const py = gy2 * S.gaugeH;                       // labels under the moving pill fade out (DESIGN: never overlap)
    for (const tk of S.ticks || []) { const off = Math.abs(tk.y - py) < 22; if (off !== tk.off) { tk.off = off; tk.el.classList.toggle('under-pill', off); } }
    const label = t('dive.m', { m: mm });
    if (label !== S.gaugeLabel) { S.gaugeLabel = label; S.$('.gauge-m').textContent = label; }
  }
  if (!S.ending) {
    for (const mark of W.DEPTH_MARKS) {
      if (m >= mark && mark > S.depthSaid) {
        S.depthSaid = mark;
        if (performance.now() - S.lastSpeech > 6000 && !S.pending) say([`ui.depth.${mark}`]);
      }
    }
  }
  const dark = rm ? (W.darkness(midX) > 0.5 ? 1 : 0) : W.darkness(midX);
  S.dark = dark;
  // headlamp: a little ahead of the mask, so the lit circle shows where she is going
  const lampX = (d.x - d.w / 2 + (d.dir > 0 ? d.anch.lamp.fx : 1 - d.anch.lamp.fx) * d.w + d.dir * S.lampR / s * 0.35 - cx) * s;
  const lampY = (d.y - d.h / 2 + d.anch.lamp.fy * d.h - cy) * s;
  const lampOn = dark > 0.35;
  if (lampOn !== S.lampOn) {
    S.lampOn = lampOn; d.el.classList.toggle('lamp-on', lampOn);
    if (lampOn && !S.ending) { sound.play('chime'); }
  }
  const rq = (W.lightRays(midX, cy + S.vh * 0.3) * 0.9).toFixed(2);
  if (rq !== S.raysQ) { S.raysQ = rq; S.$('.dv-rays').style.opacity = rq; }

  const top = waterColor(S.stops, midX, cy); const bot = waterColor(S.stops, midX, cy + S.vh);
  const key = `${rgba(top)}|${rgba(bot)}`;
  if (key !== S.waterKey) {
    S.waterKey = key;
    const wEl = S.$('.dv-water'); wEl.style.setProperty('--w-top', rgba(top)); wEl.style.setProperty('--w-bot', rgba(bot));
  }

  // near items fade while they cover the diver or something tappable (every 3rd frame, arithmetic only)
  if (S.nearItems?.length && (S.fps.n % 3 === 0)) fadeNear(cx, cy, s);

  // particles
  S.parts.update(dt, S.cam, S.vw, S.vh, d, rm);
  S.parts.draw(S.cam, S.vw, S.vh, dark, { x: lampX, y: lampY, r: S.lampR });
}

function fadeNear(cx, cy, s) {
  const f = S.parF.near; const d = S.diver;
  const boxes = [[d.x - d.w / 2, d.y - d.h / 2, d.w, d.h]];
  for (const c of S.creatures) if (c.vis) boxes.push([c.x - c.ax, c.y - c.ay, c.elW, c.elH]);
  for (const tr of S.trashSpots) if (!tr.done) boxes.push([tr.x - 45, tr.y - 45, 90, 90]);
  const scr = boxes.map(([x, y, w, hh]) => [(x - cx) * s, (y - cy) * s, w * s, hh * s]);
  for (const it of S.nearItems) {
    const ix = (it.x - cx * f) * s; const iy = it.y * s; const iw = it.w * s; const ih = it.h * s;
    const hit = ix < innerWidth && ix + iw > 0 && scr.some(([x, y, w, hh]) => x < ix + iw && x + w > ix && y < iy + ih && y + hh > iy);
    if (hit !== it.faded) { it.faded = hit; it.el.classList.toggle('faded', hit); }
  }
}

function bump() {
  const now = performance.now();
  if (now - S.bumpSaid < 9000) return;
  S.bumpSaid = now;
  S.$('.goal-bar').classList.remove('nudge'); void S.$('.goal-bar').offsetWidth; S.$('.goal-bar').classList.add('nudge');
  say(['ui.findMore']);
}

function enterZone(k) {
  const first = S.zoneIdx < k && !S.announced?.[k];
  S.zoneIdx = k; S.announced = { ...(S.announced || {}), [k]: true };
  S.view.dataset.zone = W.ZONE_IDS[k];
  { const gz = S.$('.goal-zone'); gz.dataset.zone = W.ZONE_IDS[k]; gz.innerHTML = icon(`zone-${W.ZONE_IDS[k]}`); }
  renderGoal(k);
  S.$('.hud-fwd').classList.remove('pulse');
  if (!first || S.ending || k === 0) return;
  const z = W.ZONE_IDS[k];
  const ids = [`zone.${z}.name`];
  if (phraseText(`zone.${z}.say.0`, getLang())) ids.push(`zone.${z}.say.0`);
  if (k === 2) ids.push('ui.darker');
  if (k === 3) ids.push('ui.lamp');
  setTimeout(() => { if (S && !S.pending) say(ids); }, 300);
}

// ------------------------------------------------------------------ end of the dive
async function surface() {
  if (!S || S.ending) return;
  S.ending = true; S.free = true; S.hold = 0; S.steer = null;
  S.$('.dv-hud').classList.add('leaving');
  hush(); say(['ui.surface']);
  sound.play('whoosh');
  const d = S.diver; const dur = reduced() ? 900 : 3200; const y0 = d.y; const t0 = performance.now();
  const bubbler = setInterval(() => { if (S) S.parts.emit(d.x + (Math.random() - 0.5) * 300, d.y + 100, 4, 30, 1.4); }, 120);
  await new Promise((resolve) => {
    const tick = () => {
      if (!S) return resolve();
      const u = Math.min(1, (performance.now() - t0) / dur);
      d.tx = d.x; d.ty = W.lerp(y0, 90, W.smooth(u)); d.y = d.ty;
      if (u < 1) requestAnimationFrame(tick); else resolve();
    };
    requestAnimationFrame(tick);
  });
  clearInterval(bubbler);
  if (S) summary();
}

async function summary() {
  const ids = [...S.found];
  store.recordDive({ trash: S.trashTaken });
  const fresh = S.newFound.slice();
  const layer = h(`<div class="dive-summary" role="dialog" aria-modal="true" aria-label="${esc(t('dive.summary'))}">
    <div class="sum-bg"></div>
    <div class="sum-card">
      <h2 class="sum-title">${esc(t('dive.summary'))}</h2>
      <ul class="sum-found">${ids.map((id) => `<li class="sum-cr${fresh.includes(id) ? ' new' : ''}" data-id="${esc(id)}"><div class="sum-art"></div><span>${esc(nameOf(byId.get(id)))}</span></li>`).join('')}</ul>
      <p class="sum-trash">${icon('net')}<span>${esc(t('dive.trash'))}: <b>${S.trashTaken}</b></span></p>
      <p class="sum-safety">${icon('parents')}<span>${esc(t('say.safetyDive'))}</span></p>
      <div class="sum-actions">
        ${fresh.length ? `<button class="btn hero primary" data-act="release">${icon('collection')}<span>${esc(t('dive.release'))}</span></button>` : ''}
        <button class="btn round main paper" data-act="home" aria-label="${esc(t('nav.home'))}">${icon('home')}</button>
      </div>
    </div></div>`);
  mountScene(layer.querySelector('.sum-bg'), 'summary-bg', BG_ANIM);
  for (const li of layer.querySelectorAll('.sum-cr')) if (hasArt(li.dataset.id)) li.querySelector('.sum-art').append(charEl(li.dataset.id));
  document.getElementById('overlay').append(layer);
  layer.addEventListener('click', (e) => {
    const b = e.target.closest('[data-act]'); if (!b) return;
    sound.play('tap'); hush(); layer.remove();
    if (b.dataset.act === 'release') go('sea', { fresh }); else go('home');
  });
  sound.play('success');
  celebrate({ duration: 850 });
  const seq = async () => {
    if (!ids.length) { await say(['ui.endNone', `ui.trashCount.${Math.min(10, S?.trashTaken || 0)}`, 'ui.safetyDive']); return; }
    if (!(await say(['ui.endFound']))) return;
    for (const id of ids) {
      if (!layer.isConnected) return;
      const li = layer.querySelector(`.sum-cr[data-id="${id}"]`); li?.classList.add('speaking');
      const ok = await say([`sp.${id}.name`]); li?.classList.remove('speaking');
      if (!ok) return;
    }
    if (!layer.isConnected) return;
    const lines = [`ui.trashCount.${Math.min(10, S?.trashTaken ?? 0)}`, 'ui.safetyDive'];
    if (fresh.length) lines.push('ui.release');
    await say(lines);
    maybeTired();
  };
  seq();
}

// ------------------------------------------------------------------ test hooks (e2e)
function exposeHooks() {
  window.__morsky = window.__morsky || {};
  window.__morsky.dive = {
    state: () => S && ({ x: S.diver.x, y: S.diver.y, cam: { ...S.cam }, zone: S.zoneIdx, found: [...S.found], goalMet: [...S.goalMet],
      trash: S.trashTaken, fps: S.fps.last, depth: W.depthM(S.diver.x, S.diver.y), dark: S.dark || 0, lampOn: S.lampOn, ending: S.ending,
      floorScreen: (W.floorY(S.diver.x + S.vw * 0.1) - S.cam.y) / S.vh, diverScreen: (S.diver.y - S.cam.y) / S.vh, s: S.s,
      width: W.profile().width, nearItems: S.nearItems?.length || 0, nearFaded: S.nearItems?.filter((i) => i.faded).length || 0, zones: W.profile().zones, tiles: S.world.querySelectorAll('img.floor-tile').length,
      creatures: S.creatures.map((c) => ({ id: c.sp.id, x: c.x, y: c.y, zone: c.zone, vis: c.vis })), bars: S.bars.map((b) => b.map((s) => s.id)),
      trashSpots: S.trashSpots.map((tr) => ({ id: tr.id, x: tr.x, y: tr.y, done: tr.done })), particles: S.parts.count }),
    pending: () => S.pending,
    teleport: (x, y) => { const c = W.clampDiver(x, y, gatesOpen()); Object.assign(S.diver, { x: c.x, y: c.y, tx: c.x, ty: c.y, vx: 0, vy: 0 }); const ct = W.cameraTarget(c.x, c.y, S.vw, S.vh); S.cam.x = ct.x; S.cam.y = ct.y; },
    find: (id) => { S.found.add(id); store.addFound(id); renderGoal(S.zoneIdx); checkGoal(); },
    screenOf: (id) => { const c = S.creatures.find((x) => x.sp.id === id); if (!c) return null; return { x: (c.x - S.cam.x) * S.s, y: (c.y - (c.c.floorAnchored ? c.elH * 0.4 : 0) - S.cam.y) * S.s }; },
    trashScreen: (i) => { const tr = S.trashSpots[i]; return { x: (tr.x - S.cam.x) * S.s, y: (tr.y - S.cam.y) * S.s }; },
    surface: () => surface(),
    openGates: () => { S.goalMet = [true, true, true, S.goalMet[3]]; S.world.querySelectorAll('.gate').forEach((g) => g.classList.add('open')); },
  };
}
