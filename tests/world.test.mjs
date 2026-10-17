// node tests/world.test.mjs — dive geometry (built from the designer's real tile metadata), depth, gates, motion.
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { t, done } from './_harness.mjs';
const ROOT = path.join(path.dirname(fileURLToPath(import.meta.url)), '..');
const W = await import(pathToFileURL(path.join(ROOT, 'js/dive/world.js')).href);
const read = (n) => { const p = path.join(ROOT, 'data', `${n}.json`); const j = JSON.parse(fs.readFileSync(fs.existsSync(p) ? p : path.join(ROOT, 'dev/placeholders', `${n}.json`), 'utf8')); return Array.isArray(j) ? j : j[n]; };
const species = read('species');

// tile metadata from art/ponor (when present) must parse and stitch
const meta = {};
for (const n of new Set(W.SEQUENCE)) {
  const f = path.join(ROOT, 'art/ponor', `${n}.svg`);
  if (!fs.existsSync(f)) continue;
  const m = W.parseTileMeta(fs.readFileSync(f, 'utf8'));
  t(`tile ${n} parses`, !!m && m.ys?.length === 17 && m.w === W.TILE_W, JSON.stringify(m)?.slice(0, 120));
  if (m) { meta[n] = m; t(`tile ${n}: first/last sample = data-in/out`, Math.abs(m.ys[0] - m.in) < 4 && Math.abs(m.ys[16] - m.out) < 4); }
}
W.setProfile(W.buildProfile(meta));
const P = W.profile();
t('4 zones in order', P.zones.map((z) => z.id).join() === W.ZONE_IDS.join());
t('zones tile the world without gaps', P.zones.every((z, k) => (k ? z.x0 === P.zones[k - 1].x1 : z.x0 === 0)) && P.zones[3].x1 === P.width);
let cont = true; let prevOut = null;
for (const sg of P.segs) { if (prevOut !== null && Math.abs(sg.top + sg.ys[0] - prevOut) > 4) cont = false; prevOut = sg.top + sg.ys[sg.ys.length - 1]; }
t('floor is continuous across every tile seam (≤ 4 units; data-in = previous data-out)', cont);
let finite = true; let minF = Infinity;
for (let x = 0; x < P.width; x += 37) { const f = W.floorY(x); if (!Number.isFinite(f)) finite = false; minF = Math.min(minF, f); }
t('floorY finite everywhere', finite);
t('seabed always below the surface with room to swim', minF > 400, String(minF));
t('seabed overall gets deeper (end > start)', W.floorY(P.width - 10) > W.floorY(10) + 600);
let monoD = true; let prev = -1;
for (let x = 0; x < P.width; x += 50) { const d = W.floorDepthM(x); if (d < prev) monoD = false; prev = d; }
t('floor depth in metres never decreases along the dive', monoD);
t('depth: reef ≈ 6–20 m, deep end 4000 m', W.floorDepthM(0) >= 5 && W.floorDepthM(P.zones[0].x1) === 20 && Math.round(W.floorDepthM(P.width)) === 4000);
t('depth 0 at the surface', W.depthM(1000, 0) === 0 && W.depthM(1000, -50) === 0);
t('depth grows with y at a fixed x', W.depthM(9000, 300) < W.depthM(9000, 900));
t('gauge fraction monotonic 0…1', [0, 10, 20, 30, 200, 1000, 4000].map(W.gaugeFrac).every((v, i, a) => !i || v > a[i - 1]) && W.gaugeFrac(0) === 0 && W.gaugeFrac(4000) === 1);
t('daylight on the reef, full dark at the end', W.darkness(500) === 0 && W.darkness(P.width - 300) === 1);
t('rays bright on the reef, none in the deep', W.lightRays(500, 100) > 0.8 && W.lightRays(P.width - 300, 1500) === 0);
let reach = true;
for (let x = W.START_X; x < W.endX(); x += 61) { if (W.maxY(x) - W.minY(x) < 120) reach = false; }
t('there is always ≥120 units of water to swim in', reach);
t('in the deep the diver cannot rise to the surface', W.minY(P.width - 500) > 1000);
// gates
const g = W.clampDiver(P.zones[1].x0 + 500, 500, [false, false, false]);
t('closed gate stops the diver before the next zone', g.bumped && g.x < P.zones[1].x0 && W.zoneIndexAt(g.x) === 0);
const g2 = W.clampDiver(P.zones[1].x0 + 500, 500, [true, false, false]);
t('open gate lets her through', !g2.bumped && W.zoneIndexAt(g2.x) === 1);
t('clampDiver keeps her below the surface and above the floor', (() => { const c = W.clampDiver(3000, -500); const d = W.clampDiver(3000, 99999); return c.y >= W.SURFACE_GAP && d.y <= W.floorY(3000) - 79; })());
// zone weights cross-fade
let wsum = true;
for (let x = 0; x < P.width; x += 97) { const s = W.ZONE_IDS.reduce((a, _, k) => a + W.zoneWeight(k, x), 0); if (s < 0.99) wsum = false; }
t('zone weights cover every x (sum ≥ 1, no blank water colour)', wsum);
// species
for (const lvl of [1, 2]) {
  for (const z of W.ZONE_IDS) {
    const list = W.zoneSpecies(species, z, lvl);
    t(`level ${lvl} ${z}: 3–8 creatures, goal ≥ 1`, list.length >= 3 && list.length <= 8 && W.goalFor(list.length) >= 1, String(list.length));
  }
}
t('level 2 shows every species', W.ZONE_IDS.flatMap((z) => W.zoneSpecies(species, z, 2)).length === species.length);
t('goal is 3 or fewer', W.goalFor(6) === 3 && W.goalFor(2) === 2);
t('parseMotion: "swim + jump (u hladiny)" → jump', W.parseMotion('swim + jump (u hladiny)').kind === 'jump');
t('parseMotion: "school/pulse" → school', W.parseMotion('school/pulse (světélkuje)').kind === 'school');
t('parseMotion: crawl-side is not crawl', W.parseMotion('crawl-side').kind === 'crawl-side');
t('groupKey strips diacritics', W.groupKey('Korýš') === 'korys' && W.groupKey('žahavec') === 'zahavec' && W.groupKey('ryba/žahavec') === 'ryba');
// placement + motion for every species
let okPos = true; let okNear = true; let okFloor = true; const bad = [];
W.ZONE_IDS.forEach((z, k) => {
  const list = W.zoneSpecies(species, z, 2).filter((s) => s.id !== 'zelva');
  list.forEach((sp, i) => {
    const c = W.placeCreature(sp, k, i, list.length);
    if (c.x0 < P.zones[k].x0 || c.x0 > P.zones[k].x1) { okNear = false; bad.push(sp.id); }
    for (let tt = 0; tt < 120; tt += 0.7) for (const slow of [false, true]) {
      const m = W.motion(c, tt, slow);
      if (![m.x, m.y, m.rot].every(Number.isFinite) || Math.abs(m.dir) !== 1) { okPos = false; bad.push(sp.id); }
      if (!c.floorAnchored && c.kind !== 'jump' && m.y > W.floorY(m.x) + 10) { okFloor = false; bad.push(`${sp.id}@floor`); }
    }
  });
});
t('every creature is placed inside its zone', okNear, bad.join());
t('motion gives finite positions + dir ±1 for every species, normal and reduced', okPos, bad.join());
t('swimmers never sink below the seabed', okFloor, bad.join());
const dol = species.find((s) => s.id === 'delfin');
if (dol) {
  const c = W.placeCreature(dol, 2, 0, 4); let jumped = false;
  for (let tt = 0; tt < 40; tt += 0.1) if (W.motion(c, tt).y < 0) jumped = true;
  t('the dolphin leaps out of the water (BRIEF §4.2)', c.kind === 'jump' && jumped);
  let still = true; for (let tt = 0; tt < 40; tt += 0.1) if (W.motion(c, tt, true).y < 0) still = false;
  t('reduced motion: no leaping', still);
}
const tr = W.placeTrash(['lahev', 'sacek', 'plechovka', 'sit']);
t('rubbish: 2 on the reef, 1 per other zone', tr.length === 5 && tr.filter((x) => x.k === 0).length === 2);
t('rubbish lies on the seabed or floats above it', tr.every((x) => x.y < W.floorY(x.x) && x.y > 0));
t('nextInteresting picks the nearest item to the right within the limit', W.nextInteresting(100, [{ x: 900 }, { x: 400 }, { x: 300, done: true }, { x: 50 }], 2000).x === 400 && W.nextInteresting(100, [{ x: 5000 }], 2000) === null);
const cam = W.cameraTarget(W.START_X, 150, 1333, 768);
t('camera at the start shows the sky band above the surface', cam.y < 0);
done('world');
