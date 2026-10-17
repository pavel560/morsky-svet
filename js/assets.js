// Mořský svět — loads data + art once; hands out inline SVG instances (ids made unique per instance).
// Data falls back to dev/placeholders/ while the researcher's files are not there yet (dev only: dev/ is never deployed).
import * as store from './store.js';

export const species = [];
export const byId = new Map();
export const zones = [];
export const zoneById = new Map();
export const trash = [];
export const trashById = new Map();
export let credits = {};
export let manifest = {};
export let voiceIndex = {};
export let hiddenPhotos = new Set();   // photos/hidden.json: photos never shown (e.g. a model with visible teeth)
export const source = { species: null, zones: null, trash: null };   // 'data' | 'placeholder' | null
export const artSource = new Map();                                     // name → 'art' | 'placeholder'
const svgText = new Map();

async function get(url, type = 'text') {
  // JSON (data, voice/index.json) must bypass the HTTP cache: GitHub Pages lets browsers keep it ~10 min.
  const r = await fetch(url, type === 'json' ? { cache: 'no-cache' } : undefined);
  if (!r.ok) throw new Error(`${url}: HTTP ${r.status}`);
  return type === 'json' ? r.json() : r.text();
}
async function getData(name) {
  try { const j = await get(`data/${name}.json`, 'json'); return { j, from: 'data' }; } catch { /* not yet */ }
  try { const j = await get(`dev/placeholders/${name}.json`, 'json'); return { j, from: 'placeholder' }; } catch { return { j: null, from: null }; }
}
const listOf = (j, key) => (Array.isArray(j) ? j : Array.isArray(j?.[key]) ? j[key] : []);

/** Load art/<name>.svg, else dev/placeholders/<name>.svg. Resolves to true when one of them exists. */
export async function loadArt(name) {
  if (svgText.has(name)) return true;
  for (const [base, from] of [['art/', 'art'], ['dev/placeholders/', 'placeholder']]) {
    try {
      const txt = await get(`${base}${name}.svg`);
      if (!/<svg[\s>]/.test(txt)) continue;            // an SPA fallback page is not art
      svgText.set(name, txt); artSource.set(name, from); return true;
    } catch { /* try the next */ }
  }
  return false;
}
export const hasArt = (name) => svgText.has(name);
export const artText = (name) => svgText.get(name) || null;

export async function loadAll() {
  const [sp, zn, tr] = await Promise.all([getData('species'), getData('zones'), getData('trash')]);
  if (!sp.j) throw new Error('data/species.json');
  source.species = sp.from; source.zones = zn.from; source.trash = tr.from;
  for (const s of listOf(sp.j, 'species')) if (s && /^[a-z0-9-]+$/.test(s.id || '')) { species.push(s); byId.set(s.id, s); }
  for (const z of listOf(zn.j, 'zones')) if (z?.id) { zones.push(z); zoneById.set(z.id, z); }
  for (const x of listOf(tr.j, 'trash')) if (x?.id) { trash.push(x); trashById.set(x.id, x); }
  const [cr, mf, vi] = await Promise.all([
    get('photos/credits.json', 'json').catch(() => ({})),
    get('photos/manifest.json', 'json').catch(() => ({ photos: [] })),
    get('voice/index.json', 'json').catch(() => ({})),
    get('photos/hidden.json', 'json').catch(() => []),
  ]).then((r) => { hiddenPhotos = new Set(Array.isArray(r[3]) ? r[3] : (r[3]?.hidden || [])); return r; });
  credits = cr && typeof cr === 'object' ? cr : {};
  manifest = Object.fromEntries((Array.isArray(mf?.photos) ? mf.photos : []).map((p) => [p.id, p]));
  voiceIndex = vi && typeof vi === 'object' ? vi : {};
  await Promise.all(['ui-icons', 'diver', 'guide-turtle', ...trash.map((x) => `trash-${x.id}`)].map(loadArt));
  const missing = [];
  await Promise.all(species.map(async (s) => { if (!(await loadArt(s.id))) missing.push(s.id); }));
  if (missing.length) {          // data ahead of art: leave the creature out rather than break the game
    console.info('Mořský svět: no art yet for', missing.join(', '));
    for (const id of missing) { byId.delete(id); species.splice(species.findIndex((s) => s.id === id), 1); }
  }
}

const reEsc = (s) => s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
let seq = 0;
/** Parse loaded art into a fresh element (ids rewritten so the same art can appear many times). */
export function svgEl(name, { unique = true } = {}) {
  let s = svgText.get(name);
  if (!s) throw new Error(`art not loaded: ${name}`);
  if (unique) {
    const n = ++seq;
    for (const id of [...new Set([...s.matchAll(/\sid="([^"]+)"/g)].map((m) => m[1]))]) {
      const nid = `${id}__${n}`;
      s = s.replace(new RegExp(`(\\s)id="${reEsc(id)}"`, 'g'), `$1id="${nid}"`)
        .replace(new RegExp(`#${reEsc(id)}(?=["')\\s])`, 'g'), `#${nid}`);
    }
  }
  const tp = document.createElement('template');
  tp.innerHTML = s.trim();
  return tp.content.firstElementChild;
}
export function viewBox(svg) {
  const v = (svg.getAttribute('viewBox') || '0 0 100 100').split(/[\s,]+/).map(Number);
  return { x: v[0] || 0, y: v[1] || 0, w: v[2] || 100, h: v[3] || 100 };
}
/** Pivots (DESIGN §0.1): every g[data-pivot] rotates/scales around its own point, in viewBox units. */
export function applyPivots(svg) {
  for (const g of svg.querySelectorAll('[data-pivot]')) {
    if (g === svg) continue;
    const [x, y] = g.dataset.pivot.split(/[\s,]+/).map(Number);
    if (Number.isFinite(x) && Number.isFinite(y)) { g.style.transformBox = 'view-box'; g.style.transformOrigin = `${x}px ${y}px`; }
  }
  return svg;
}
/** A creature / diver / turtle instance ready to animate. */
export function charEl(name) {
  const el = applyPivots(svgEl(name));
  el.querySelector('title')?.remove();
  el.setAttribute('focusable', 'false'); el.setAttribute('aria-hidden', 'true');
  return el;
}
/** Anchor centre as a fraction of the viewBox: { fx, fy } (0…1), or null. */
export function anchorFrac(svg, selector) {
  const a = svg.querySelector(selector); if (!a) return null;
  const vb = viewBox(svg);
  return { fx: (Number(a.getAttribute('cx')) - vb.x) / vb.w, fy: (Number(a.getAttribute('cy')) - vb.y) / vb.h };
}
/** data-span="x0 x1" (DESIGN §0.4) as a fraction of the viewBox width; whole width when absent. */
export function spanFrac(svg) {
  const vb = viewBox(svg);
  const sp = (svg.getAttribute('data-span') || '').split(/[\s,]+/).map(Number);
  if (sp.length === 2 && sp.every(Number.isFinite) && sp[1] > sp[0]) return { f0: (sp[0] - vb.x) / vb.w, f1: (sp[1] - vb.x) / vb.w };
  return { f0: 0, f1: 1 };
}
/** data-floor="y" → fraction of the viewBox height (bottom-dwellers); null otherwise. */
export function floorFrac(svg) {
  const f = Number(svg.getAttribute('data-floor'));
  if (!svg.hasAttribute('data-floor') || !Number.isFinite(f)) return null;
  const vb = viewBox(svg); return (f - vb.y) / vb.h;
}

// ---- photos (fetch_photos.py writes photos/<id>.jpg + photos/credits.json in CI)
export const hasPhoto = (id) => !!credits[id] && !hiddenPhotos.has(id);
export const photoUrl = (id) => `photos/${id}.jpg`;
export function photoCredit(id) {
  const c = credits[id] || {}; const m = manifest[id] || {};
  return { author: c.author || m.author || '?', license: c.license || m.license || '', licenseUrl: c.licenseUrl || m.licenseUrl || '', sourcePage: c.sourcePage || m.sourcePage || '' };
}
export const _store = store;
