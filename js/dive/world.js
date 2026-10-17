// Mořský svět — the dive world as pure functions (no DOM): geometry, depth, zones, gates, creature motion.
// World units = CSS px at a 768 px tall viewport (the view scales by innerHeight / 768).
// x grows to the right (the diver swims left → right), y grows downwards; the water surface is y = 0.
export const VH = 768;
export const TILE_W = 2048;                               // floor + layer tiles (DESIGN §6.4: 2048 wide, layer 768 tall)
export const ZONE_IDS = ['utes', 'chaluhy', 'sire-more', 'hlubiny'];
export const START_X = 300;
export const SURFACE_GAP = 40;                            // the diver stays this far below the surface
export const DEEP_BAND = 560;                             // in the deep she stays within this distance above the seabed
export const DIVER_SIZE_CM = 115;                         // the child, for the size bar on the card
export const TILE_TOP0 = 40;                              // world y of the first floor tile's top edge (surface = 0)

export const clamp = (v, a, b) => Math.max(a, Math.min(b, v));
export const lerp = (a, b, t) => a + (b - a) * t;
export const smooth = (t) => { const u = clamp(t, 0, 1); return u * u * (3 - 2 * u); };

// ------------------------------------------------------------------ the stitched seabed (DESIGN §6.4)
// Floor tiles are a WORLD plane: each tile's data-in y sits at the previous tile's data-out y; data-floor-y holds
// 17 samples (every 128 viewBox units) of the walkable seabed inside the tile. The sequence below is the dive.
export const SEQUENCE = ['utes-floor', 'utes-floor', 'trans-utes-chaluhy', 'chaluhy-floor', 'trans-chaluhy-sire-more',
  'sire-more-floor', 'trans-sire-more-hlubiny', 'hlubiny-floor'];
/** Built-in metadata (same numbers as the art) so the world works — and tests run — before / without the tiles. */
export const DEFAULT_TILES = {
  'utes-floor': { h: 1024, in: 560, out: 680, zone: 'utes' },
  'trans-utes-chaluhy': { h: 1024, in: 560, out: 820, zone: 'chaluhy', trans: true },
  'chaluhy-floor': { h: 1024, in: 560, out: 720, zone: 'chaluhy' },
  'trans-chaluhy-sire-more': { h: 2048, in: 560, out: 980, zone: 'sire-more', trans: true, floorNone: true },
  'sire-more-floor': { h: 1024, in: 560, out: 780, zone: 'sire-more', floorNone: true },
  'trans-sire-more-hlubiny': { h: 1536, in: 560, out: 680, zone: 'hlubiny', trans: true },
  'hlubiny-floor': { h: 1024, in: 560, out: 650, zone: 'hlubiny' },
};
/** Parse a floor tile's root attributes → metadata ({ h, in, out, ys, floorNone, fill }) or null. */
export function parseTileMeta(svgText) {
  const head = /<svg\b[^]*?(?=<defs|<g|<path|<rect|<title)/.exec(svgText)?.[0] || svgText.slice(0, 3000);
  const a = (n) => new RegExp(`\\s${n}="([^"]*)"`).exec(head)?.[1];
  const vb = (a('viewBox') || '').split(/[\s,]+/).map(Number);
  const ys = (a('data-floor-y') || '').split(',').map(Number).filter(Number.isFinite);
  const fin = Number(a('data-in')); const fout = Number(a('data-out'));
  if (!(vb[2] > 0 && vb[3] > 0) || !Number.isFinite(fin) || !Number.isFinite(fout)) return null;
  return { w: vb[2], h: vb[3], in: fin, out: fout, ys: ys.length >= 2 ? ys : null, floorNone: a('data-floor') === 'none',
    fill: a('data-fill') && a('data-fill') !== 'none' ? a('data-fill') : null };
}

/** Lay the sequence out: segments with world x0, tile top, samples; zones with x-ranges. */
export function buildProfile(meta = {}) {
  const segs = []; let x = 0; let floorAt = TILE_TOP0 + (meta[SEQUENCE[0]]?.in ?? DEFAULT_TILES[SEQUENCE[0]].in);
  for (const name of SEQUENCE) {
    const d = DEFAULT_TILES[name]; const m = { ...d, ...(meta[name] || {}) };
    const ys = m.ys || Array.from({ length: 17 }, (_, i) => lerp(m.in, m.out, i / 16));
    const top = floorAt - m.in;
    segs.push({ name, x0: x, w: TILE_W, top, h: m.h, ys, zone: d.zone, trans: !!d.trans, floorNone: !!m.floorNone, fill: m.fill || null });
    x += TILE_W; floorAt = top + m.out;
  }
  const zones = ZONE_IDS.map((id) => {
    const own = segs.filter((sg) => sg.zone === id);
    return { id, x0: own[0].x0, x1: own[own.length - 1].x0 + TILE_W };
  });
  return { segs, zones, width: x };
}
let P = buildProfile();
export function setProfile(p) { P = p; WORLD.W = p.width; }
export const profile = () => P;
export const WORLD = { W: P.width };
export const END_X_PAD = 260;
export const endX = () => P.width - END_X_PAD;

export function zoneIndexAt(x) { for (let k = P.zones.length - 1; k >= 0; k--) if (x >= P.zones[k].x0) return k; return 0; }
export const zoneAt = (x) => ZONE_IDS[zoneIndexAt(x)];
export const zoneStart = (k) => P.zones[k].x0;
export const zoneEnd = (k) => P.zones[k].x1;
/** Gate k (k = 0…2) sits just before zone k+1 begins: closed until zone k's goal is met. */
export const gateX = (k) => P.zones[k + 1].x0 - 140;

export function floorY(x) {
  const xx = clamp(x, 0, P.width - 1);
  const sg = P.segs[Math.min(P.segs.length - 1, Math.floor(xx / TILE_W))];
  const u = ((xx - sg.x0) / sg.w) * (sg.ys.length - 1);
  const i = Math.min(sg.ys.length - 2, Math.floor(u));
  return sg.top + lerp(sg.ys[i], sg.ys[i + 1], u - i);
}
/** Start of the deep: the transition tile into the abyss. */
const deepX0 = () => P.zones[3].x0;
/** Highest point the diver may reach at x: just below the surface; in the deep, a band above the seabed. */
export function minY(x) {
  const d0 = deepX0();
  const f = smooth((x - (d0 - TILE_W * 0.2)) / (TILE_W * 0.9));
  return lerp(SURFACE_GAP, Math.max(SURFACE_GAP, floorY(x) - DEEP_BAND), f);
}
/** Lowest point the diver may reach at x (above the seabed). */
export const maxY = (x) => floorY(x) - 80;

// Depth in metres. The seabed's depth grows along the dive (reef 6 → 20 m … abyss 4000 m) and the diver's depth
// is that times how far down the water column she is. Monotonic in x along the floor; 0 at the surface.
export function floorDepthM(x) {
  const z = P.zones;
  const pts = [[0, 6], [z[0].x1, 20], [z[1].x1, 30], [z[2].x0 + TILE_W, 120], [z[2].x1, 200], [z[3].x0 + TILE_W, 1500], [P.width, 4000]];
  for (let i = 1; i < pts.length; i++) if (x <= pts[i][0]) return lerp(pts[i - 1][1], pts[i][1], clamp((x - pts[i - 1][0]) / (pts[i][0] - pts[i - 1][0]), 0, 1));
  return 4000;
}
export const depthM = (x, y) => (y <= 0 ? 0 : floorDepthM(x) * clamp(y / Math.max(1, floorY(x)), 0, 1));
// Gauge: piecewise scale so the shallow metres are readable (bands match css .gauge-track).
const GAUGE = [[0, 0], [20, 0.26], [30, 0.376], [200, 0.621], [4000, 1]];
export function gaugeFrac(m) {
  for (let i = 1; i < GAUGE.length; i++) if (m <= GAUGE[i][0]) return lerp(GAUGE[i - 1][1], GAUGE[i][1], (m - GAUGE[i - 1][0]) / (GAUGE[i][0] - GAUGE[i - 1][0]));
  return 1;
}
/** Depth marks spoken once per dive when first passed on the way down. */
export const DEPTH_MARKS = [10, 20, 30, 100, 200, 1000, 2000, 3000];
export const GAUGE_LABELS = [0, 10, 20, 30, 200, 1000, 2000, 4000];
/** 0 = daylight … 1 = full dark (headlamp): across the transition into the deep. */
export const darkness = (x) => smooth((x - (deepX0() + 300)) / 1300);
/** Sun rays: bright near the surface of the sunlit zones, gone in the deep. */
export const lightRays = (x, y) => (1 - darkness(x)) * (1 - 0.7 * smooth(y / Math.max(1, floorY(x))));
/** Weight of zone k's look (water colour, layer tiles) at x: cross-fades over the transition tiles. */
export function zoneWeight(k, x) {
  const z = P.zones; const fade = TILE_W * 0.8;
  const inW = k === 0 ? 1 : smooth((x - z[k].x0 + fade * 0.2) / fade);
  const outW = k === z.length - 1 ? 1 : 1 - smooth((x - z[k + 1].x0 + fade * 0.2) / fade);
  return clamp(Math.min(inW, outW), 0, 1);
}

/** Diver position clamped to the reachable water and to closed gates. Returns { x, y, bumped }. */
export function clampDiver(x, y, gatesOpen = [true, true, true]) {
  let bumped = false;
  let xx = clamp(x, START_X - 120, endX());
  for (let k = 0; k < 3; k++) {
    if (!gatesOpen[k] && xx > gateX(k) - 60) { xx = gateX(k) - 60; bumped = true; }
  }
  const lo = minY(xx); const hi = Math.max(lo + 40, maxY(xx));
  return { x: xx, y: clamp(y, lo, hi), bumped };
}

/** Where there is a seabed, the camera puts it at this fraction of the view height (like the comps). */
export const FLOOR_AT = 0.76;
/** The diver always stays between these fractions of the view height (clear of the top bar and bottom HUD). */
export const DIVER_BAND = [0.24, 0.7];
export const segAt = (x) => P.segs[clamp(Math.floor(clamp(x, 0, P.width - 1) / TILE_W), 0, P.segs.length - 1)];
/** Camera (top-left of the view, world units): seabed low in the frame, diver comfortably inside. */
export function cameraTarget(dx, dy, vw, vh, free = false) {
  const cx = clamp(dx - vw * 0.4, -60, P.width - vw + 60);
  const top = -vh * 0.24;
  if (free) return { x: cx, y: Math.max(dy - vh * 0.52, top) };
  const fx = dx + vw * 0.1;
  let cy = segAt(fx).floorNone ? dy - vh * 0.5 : floorY(fx) - FLOOR_AT * vh;
  cy = clamp(cy, dy - vh * DIVER_BAND[1], dy - vh * DIVER_BAND[0]);
  return { x: cx, y: Math.max(cy, top) };
}

// ------------------------------------------------------------------ species placement
const GROUP_KEYS = ['ryba', 'savec', 'plaz', 'korys', 'mekkys', 'ostnokozec', 'zahavec'];
export function groupKey(g) {
  const k = String(g || '').toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, '').split(/[\/|,+ ]/)[0];
  return GROUP_KEYS.includes(k) ? k : 'ryba';
}
const MOTIONS = ['swim', 'school', 'hover', 'crawl-side', 'crawl', 'jet', 'pulse', 'glide', 'surface', 'jump', 'flap', 'sway'];
/** "swim + jump (u hladiny)" → { kind: 'jump', all: ['swim','jump'] } */
export function parseMotion(m) {
  const s = String(m || 'swim').toLowerCase();
  const all = MOTIONS.filter((k) => new RegExp(`(^|[^a-z-])${k}([^a-z-]|$)`).test(s));
  if (!all.length) all.push('swim');
  const kind = all.includes('jump') ? 'jump' : all.includes('surface') ? 'surface' : all[0];
  return { kind, all };
}
/** Art width in world units for a body length in cm (log-ish so a crab and a whale both fit). */
export const displayW = (sizeCm) => clamp(Math.round(92 * Math.pow(Math.max(1, sizeCm || 20) / 20, 0.4)), 96, 540);

/**
 * Species shown in a zone's goal bar (= spawned in the world) at a level.
 * Level 2: all of the zone's species. Level 1: level-1 species, padded with level-2 ones up to 3.
 * The guide turtle (`zelva`) is never spawned separately, but is part of the bar (tap the guide to find it).
 */
export function zoneSpecies(all, zoneId, level) {
  const inZone = all.filter((s) => s.zone === zoneId);
  if (level >= 2) return inZone;
  const l1 = inZone.filter((s) => (s.level || 1) <= 1);
  const pad = inZone.filter((s) => (s.level || 1) > 1).slice(0, Math.max(0, 3 - l1.length));
  return [...l1, ...pad];
}
export const goalFor = (n) => Math.min(3, n);

function hash(str) { let x = 2166136261; for (const c of String(str)) { x ^= c.charCodeAt(0); x = Math.imul(x, 16777619); } return (x >>> 0) / 4294967296; }

/** Creature motion parameters for a species in zone k at slot i of n. Pure + deterministic. */
export function placeCreature(sp, k, i, n) {
  const pm = parseMotion(sp.motion); const { all } = pm;
  // BRIEF §4.2: the dolphin leaps at the surface (data says plain „swim“)
  const kind = sp.id === 'delfin' && pm.kind === 'swim' ? 'jump' : pm.kind;
  const w = displayW(sp.sizeCm);
  const r = hash(sp.id);
  const zx0 = zoneStart(k) + (ZONE_IDS[k] === 'utes' ? 700 : 600); const zx1 = zoneEnd(k) - 520;
  const x0 = zx0 + ((zx1 - zx0) * (i + 0.5)) / Math.max(1, n) + (r - 0.5) * 120;
  const floor = floorY(x0);
  let y0;
  // swimmers live in the lower part of the frame (camera keeps the floor at FLOOR_AT): clear of the top bar
  const midTop = Math.max(170, minY(x0) + 100, floor - 0.55 * VH); const midBot = floor - 190;
  if (['crawl', 'crawl-side', 'sway'].includes(kind)) y0 = floor;            // feet on the seabed (bottom-anchored)
  else if (kind === 'jet') y0 = floor - 60;
  else if (kind === 'surface') y0 = 6;
  else if (kind === 'jump') y0 = 170;
  else y0 = lerp(midTop, Math.max(midTop + 40, midBot), 0.25 + 0.5 * r);
  if (sp.id === 'konik') y0 = floor - 150;
  const speed = { swim: 55, school: 70, glide: 34, crawl: 6, 'crawl-side': 22, jet: 0, pulse: 0, hover: 0, flap: 0, sway: 0, surface: 8, jump: 70 }[kind] ?? 40;
  const range = { swim: 260, school: 380, glide: 700, crawl: 70, 'crawl-side': 150, surface: 90, jump: 520 }[kind] ?? 40;
  return { id: sp.id, kind, all, w, x0, y0, speed, range, phase: r * Math.PI * 2, floorAnchored: ['crawl', 'crawl-side', 'sway'].includes(kind),
    breathes: !!sp.breathesAir && ['swim', 'glide'].includes(kind) };
}

/**
 * Position of a creature at time t (s). Returns { x, y, dir (+1 right / -1 left), rot (deg), state }.
 * slow = prefers-reduced-motion: half speed, no bobbing.
 */
export function motion(c, t, slow = false) {
  const sp = slow ? 0.5 : 1; const bob = slow ? 0 : 1;
  const T = t * sp + c.phase * 10;
  const osc = (range, speed) => {               // back-and-forth with eased turns
    const w = speed / Math.max(1, range);
    return { x: range * Math.sin(T * w), v: Math.cos(T * w) };
  };
  let x = c.x0; let y = c.y0; let dir = 1; let rot = 0; let state = '';
  switch (c.kind) {
    case 'swim': case 'school': case 'glide': {
      const o = osc(c.range, c.speed); x += o.x; dir = o.v >= 0 ? 1 : -1;
      y += bob * (c.kind === 'glide' ? 26 : 16) * Math.sin(T * 0.7);
      if (c.breathes) {                          // air-breathers swim up to the surface now and then
        const b = Math.max(0, Math.sin(T * 0.11));
        const up = smooth((b - 0.75) / 0.25);
        y = lerp(y, 70, up); if (up > 0.05) state = 'breathe';
      }
      rot = bob * 4 * Math.sin(T * 0.7 + 1);
      break;
    }
    case 'crawl': case 'crawl-side': {
      const o = osc(c.range, c.speed); x += o.x;
      dir = c.kind === 'crawl-side' ? 1 : (o.v >= 0 ? 1 : -1);
      state = Math.abs(o.v) > 0.2 ? 'walk' : '';
      break;
    }
    case 'sway': break;
    case 'hover': {
      y += bob * 14 * Math.sin(T * 0.8); x += bob * 6 * Math.sin(T * 0.3);
      dir = Math.sin(T * 0.07) >= -0.2 ? 1 : -1;
      break;
    }
    case 'flap': {
      y += 34 * Math.sin(T * 0.45) * (slow ? 0.5 : 1); x += 50 * Math.sin(T * 0.17);
      dir = Math.cos(T * 0.17) >= 0 ? 1 : -1; state = 'flap';
      break;
    }
    case 'pulse': {
      const ph = (T * 0.5) % 1; const kick = smooth(ph / 0.3) * (1 - smooth((ph - 0.3) / 0.7));
      y += 50 * Math.sin(T * 0.09) - (slow ? 0 : 10 * kick); x += 40 * Math.sin(T * 0.06);
      state = kick > 0.3 ? 'pulse' : '';
      break;
    }
    case 'jet': {
      const P = 9; const ph = ((T % P) + P) % P; const n = Math.floor(T / P);
      const side = n % 2 === 0 ? 1 : -1;
      const u = smooth(Math.min(1, Math.max(0, ph - 6) / 0.9));
      x += side * (-90 + 180 * u); y -= 70 * Math.sin(Math.PI * u);
      dir = ph > 6 ? -side : side; state = ph > 6 && ph < 7 ? 'jet' : ph > 7.2 ? 'hide' : '';
      break;
    }
    case 'surface': {
      x += c.range * Math.sin(T * 0.08); y += bob * 4 * Math.sin(T * 1.1);
      dir = Math.cos(T * 0.08) >= 0 ? 1 : -1; state = 'float';
      break;
    }
    case 'jump': {
      const o = osc(c.range, c.speed); x += o.x; dir = o.v >= 0 ? 1 : -1;
      y += bob * 12 * Math.sin(T * 0.9);
      const P = 11; const ph = ((T % P) + P) % P;
      if (!slow && ph > 9 && ph < 10.6) {         // a jump: up through the surface and back, 1.6 s
        const u = (ph - 9) / 1.6;
        y = lerp(c.y0, -150, Math.sin(Math.PI * u)) ;
        rot = -dir * (60 * Math.cos(Math.PI * u));
        state = 'jump';
      }
      break;
    }
    default: break;
  }
  return { x, y, dir, rot, state };
}

/** Next thing worth swimming to on the right (an unfound creature or untaken trash). */
export function nextInteresting(x, items, maxX) {
  let best = null;
  for (const it of items) {
    if (it.done || it.x <= x + 90 || it.x > maxX) continue;
    if (!best || it.x < best.x) best = it;
  }
  return best;
}

/** Trash spots per zone (ids from data/trash.json, cycled): 2 in the reef, 1 elsewhere. */
export function placeTrash(ids) {
  if (!ids.length) return [];
  const plan = [[0, 0.3], [0, 0.72], [1, 0.62], [2, 0.6], [3, 0.7]];
  return plan.map(([k, f], i) => {
    const x = zoneStart(k) + (zoneEnd(k) - zoneStart(k)) * f;
    const id = ids[i % ids.length];
    const floating = ZONE_IDS[k] === 'sire-more';
    return { id, k, x, y: floating ? Math.min(floorY(x) - 300, 640) : floorY(x) - 30, floating };
  });
}
