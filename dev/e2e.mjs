// Mořský svět — end-to-end walk of the whole game + screenshot matrix (Playwright, Chromium).
// Self-contained: copies the site into a temp dir under /morsky-svet/ (like GitHub Pages), adds FAKE photos and silent
// voice mp3s there (never in the repo), serves it with serve.py and drives Chromium. Screens → dev/screens/.
//   PLAYWRIGHT=<.../playwright/index.mjs> CHROME=<chrome or headless shell> node dev/e2e.mjs
import { fileURLToPath } from 'node:url';
import path from 'node:path';
import fs from 'node:fs';
import os from 'node:os';
import { spawn } from 'node:child_process';
const { chromium } = await import(process.env.PLAYWRIGHT || 'playwright');
const HERE = path.dirname(fileURLToPath(import.meta.url));
const SRC = path.join(HERE, '..');
const OUT = path.join(HERE, 'screens');
fs.mkdirSync(OUT, { recursive: true });
const TMP = fs.mkdtempSync(path.join(os.tmpdir(), 'morsky-e2e-'));
const SITE = path.join(TMP, 'morsky-svet');
fs.cpSync(SRC, SITE, { recursive: true, filter: (f) => !/[\\/](dev[\\/]screens|__pycache__|\.git|node_modules)([\\/]|$)/.test(f) });
const read = (n) => { const j = JSON.parse(fs.readFileSync(path.join(SRC, 'data', `${n}.json`), 'utf8')); return Array.isArray(j) ? j : j[n]; };
const species = read('species');
const { buildCatalogue } = await import(new URL('../js/phrases.js', import.meta.url).href);
const CATALOGUE = buildCatalogue(species, { zones: read('zones'), trash: read('trash') });
const frame = Buffer.alloc(417); frame.set([0xFF, 0xFB, 0x90, 0x64]);          // MPEG-1 L3 frame, silent
const SILENT_MP3 = Buffer.concat(Array(8).fill(frame));
const vindex = {};
for (const [lang, m] of Object.entries(CATALOGUE)) {
  fs.mkdirSync(path.join(SITE, 'voice', lang), { recursive: true }); vindex[lang] = {};
  for (const [id, text] of Object.entries(m)) { fs.writeFileSync(path.join(SITE, 'voice', lang, `${id}.mp3`), SILENT_MP3); vindex[lang][id] = { text, file: `${lang}/${id}.mp3`, sha1: 'e2etest', bytes: SILENT_MP3.length }; }
}
fs.writeFileSync(path.join(SITE, 'voice', 'index.json'), JSON.stringify(vindex));
const PORT = 8760 + Math.floor(Math.random() * 40);
const server = spawn('python3', [path.join(SRC, 'serve.py'), '--dir', TMP, '--port', String(PORT), '--host', '127.0.0.1', '--quiet'], { stdio: 'ignore' });
process.on('exit', () => { server.kill(); fs.rmSync(TMP, { recursive: true, force: true }); });
const BASE = `http://localhost:${PORT}/morsky-svet`;
for (let i = 0; i < 60; i++) { try { if ((await fetch(`${BASE}/index.html`)).ok) break; } catch { /* starting */ } await new Promise((r) => setTimeout(r, 100)); }

const browser = await chromium.launch({ executablePath: process.env.CHROME || undefined });
// a fake "photo": the clownfish drawing on a sea-blue field, written into the temp site only
{
  const mk = await browser.newPage({ viewport: { width: 900, height: 600 } });
  await mk.goto(`${BASE}/art/klaun.svg`);
  const jpg = await mk.screenshot({ type: 'jpeg', quality: 70 });
  await mk.close();
  for (const id of ['klaun', 'krab', 'das']) fs.writeFileSync(path.join(SITE, 'photos', `${id}.jpg`), jpg);
  fs.writeFileSync(path.join(SITE, 'photos', 'credits.json'), JSON.stringify(Object.fromEntries(['klaun', 'krab', 'das'].map((id) => [id, { author: 'Test Author', license: 'CC BY-SA 4.0', licenseUrl: 'https://creativecommons.org/licenses/by-sa/4.0/', sourcePage: 'https://commons.wikimedia.org/wiki/File:Test.jpg', via: 'commonsFile' }]))));
}

const results = []; const errors = []; const notFound = new Set();
process.on('uncaughtException', (e) => { console.log(results.join('\n')); console.log('ABORTED:', e.message.split('\n')[0], '| errors:', errors.slice(0, 5).join(' | ')); process.exit(2); });
const check = (name, ok, extra = '') => { results.push(`${ok ? 'PASS' : 'FAIL'}  ${name}${extra && !ok ? `  — ${extra}` : ''}`); return ok; };
const FAKE_SPEECH = () => {
  const V = [{ name: 'Zuzana (Enhanced)', lang: 'cs-CZ', voiceURI: 'cs', localService: true }, { name: 'Serena (Enhanced)', lang: 'en-GB', voiceURI: 'en', localService: true }];
  window.__spoken = []; window.__langs = []; window.__ids = []; window.__tts = []; window.__files = []; let cur = null;
  addEventListener('speech:say', (e) => { window.__spoken.push(e.detail.text); window.__langs.push(e.detail.lang); window.__ids.push(...e.detail.ids); });
  addEventListener('speech:file', (e) => window.__files.push(e.detail));
  const synth = new EventTarget();
  Object.assign(synth, { speaking: false, pending: false, paused: false, getVoices: () => V,
    cancel() { if (cur) { const u = cur; cur = null; u.onerror && u.onerror({ error: 'interrupted' }); } }, resume() {},
    speak(u) { if (u.text.trim()) window.__tts.push(u.text); cur = u; setTimeout(() => { if (cur === u) { cur = null; u.onend && u.onend(); } }, 60); } });
  Object.defineProperty(window, 'speechSynthesis', { value: synth, configurable: true });
  window.SpeechSynthesisUtterance = class { constructor(t) { this.text = t; } };
};
async function session(vp, { reducedMotion = 'no-preference', sw = 'block', seed = null } = {}) {
  const ctx = await browser.newContext({ viewport: vp, serviceWorkers: sw, reducedMotion, hasTouch: false });
  await ctx.addInitScript(FAKE_SPEECH);
  if (seed) await ctx.addInitScript((s) => { if (!localStorage.getItem('morsky-svet.v1')) localStorage.setItem('morsky-svet.v1', JSON.stringify(s)); }, seed);
  const page = await ctx.newPage();
  page.on('pageerror', (e) => errors.push(`${vp.width}: ${e.message}`));
  page.on('response', (r) => { if (r.status() === 404) notFound.add(new URL(r.url()).pathname); });
  page.on('console', (m) => { if (m.type() === 'error' && !/404|Failed to load resource/.test(m.text())) errors.push(`${vp.width}: ${m.text()}`); });
  return { ctx, page };
}
const shot = (page, name) => page.screenshot({ path: path.join(OUT, `${name}.png`) });
const ids = (page) => page.evaluate(() => window.__ids.slice());
const wait = (page, ms) => page.waitForTimeout(ms);
const dive = (page, expr, arg) => page.evaluate(([e, a]) => new Function('D', 'a', `return (${e})`)(window.__morsky.dive, a), [expr, arg]);
async function tapCreature(page, id) {
  for (let i = 0; i < 4; i++) {
    const p = await dive(page, 'D.screenOf(a)', id);
    if (p && p.x > 70 && p.y > 110 && p.x < page.viewportSize().width - 10) {
      await page.mouse.click(p.x, p.y);
      try { await page.waitForSelector('.card-layer', { timeout: 2500 }); return true; } catch { /* moved away; retry */ }
    } else await dive(page, 'D.teleport(D.state().creatures.find(c => c.id === a).x - 300, D.state().creatures.find(c => c.id === a).y)', id);
    await wait(page, 300);
  }
  return false;
}
async function minTarget(page, sel) {
  return page.evaluate((s) => Math.min(...[...document.querySelectorAll(s)].filter((e) => e.offsetParent || e.getClientRects().length)
    .map((e) => { const r = e.getBoundingClientRect(); return Math.min(r.width, r.height); }).filter((v) => v > 0)), sel);
}


const rect = (page, sel) => page.evaluate((q) => { const e = document.querySelector(q); if (!e || !e.getClientRects().length) return null; const r = e.getBoundingClientRect(); return { l: r.left, t: r.top, r: r.right, b: r.bottom }; }, sel);
const overlap = (a, b) => a && b && a.l < b.r && a.r > b.l && a.t < b.b && a.b > b.t;
/** Visible creatures whose centre sits under a HUD control (top bar, back, Plav dál, caption). */
async function hudOffenders(page) {
  return page.evaluate(() => {
    const huds = ['.goal-bar', '.hud-home', '.hud-replay', '.hud-back', '.hud-net', '.hud-fwd', '.hud-fwd-label', '#caption.show'].map((q) => document.querySelector(q)).filter((e) => e && e.getClientRects().length)
      .map((e) => e.getBoundingClientRect());
    const out = [];
    for (const c of document.querySelectorAll('.dv-world:not(.dv-glow) .cr:not(.off)')) {
      const r = c.getBoundingClientRect(); const x = (r.left + r.right) / 2; const y = (r.top + r.bottom) / 2;
      if (x < 0 || x > innerWidth || y < 0 || y > innerHeight) continue;
      if (huds.some((h) => x > h.left && x < h.right && y > h.top && y < h.bottom)) out.push(c.dataset.id);
    }
    return out;
  });
}
async function cardFits(page, id) {
  await page.evaluate((i) => { window.__morsky.closeCard(); window.__morsky.openCard(i); }, id);
  await page.waitForSelector('.card-layer'); await wait(page, 450);
  const r = await page.evaluate(() => { const i = document.querySelector('.card-info'); const c = document.querySelector('.card').getBoundingClientRect();
    const last = [...document.querySelectorAll('.card .look, .card .wow')].map((e) => e.getBoundingClientRect().bottom);
    return { sh: i.scrollHeight, ch: i.clientHeight, inside: last.every((b) => b <= c.bottom + 1) }; });
  await page.evaluate(() => window.__morsky.closeCard());
  return r;
}

// ============================================================ A. full walk at two iPad sizes
for (const vp of [{ width: 1024, height: 768 }, { width: 1180, height: 820 }]) {
  const tag = `${vp.width}x${vp.height}`;
  const { ctx, page } = await session(vp);
  await page.goto(`${BASE}/`);
  await page.waitForSelector('.start-layer .play-bubble-btn');
  check(`${tag} start: safety line on the start screen`, (await page.textContent('.start-safety')).includes('jen s dospělým'));
  check(`${tag} start v2: title scene, logo, play bubble`, (await page.locator('.start-layer .scene-static').count()) === 1 && (await page.locator('.start-logo svg[data-lang="cs"]').count()) === 1 && (await minTarget(page, '.play-bubble-btn')) >= 120);
  check(`${tag} start: play bubble clear of the boat, logo and safety line`, await page.evaluate(() => {
    const p = document.querySelector('.play-bubble-btn').getBoundingClientRect(); const ov = (q) => { const r = q.getBoundingClientRect(); return p.left < r.right && p.right > r.left && p.top < r.bottom && p.bottom > r.top; };
    const boat = document.querySelector('.start-layer .scene-live .boat');
    return !ov(document.querySelector('.start-logo')) && !ov(document.querySelector('.start-safety')) && !(boat && ov(boat)); }));
  await shot(page, `${tag}-0-start`);
  await page.click('.start-layer .play-bubble-btn');
  await page.waitForSelector('.home .dive-btn'); await wait(page, 500);
  check(`${tag} home: greeting + safety spoken`, (await ids(page)).includes('ui.greet') && (await ids(page)).includes('ui.safetyDive'));
  check(`${tag} home: recordings used (voice/ files), no TTS fallback`, await page.waitForFunction(() => window.__files.length > 0, null, { timeout: 5000 }).then(() => true, () => false));
  check(`${tag} home: hero button ≥ 88 px, doors ≥ 88 px, every button ≥ 64 px`, (await minTarget(page, '.home .dive-btn')) >= 88 && (await minTarget(page, '.home .door')) >= 88 && (await minTarget(page, '.home .btn')) >= 64, `${await minTarget(page, '.home .door')} / ${await minTarget(page, '.home .btn')}`);
  check(`${tag} home v2: scene (static + live layer), logo, three illustrated doors`, (await page.locator('.home .scene-static').count()) === 1 && (await page.locator('.home .scene-live').count()) === 1 && (await page.locator('.home-logo svg').count()) === 1 && (await page.locator('.home .door .door-obj > svg').count()) === 3);
  check(`${tag} home: icons rendered from the sprite`, await page.evaluate(() => !!document.querySelector('#sprite symbol#i-home')));
  await shot(page, `${tag}-1-home`);
  check(`${tag} home: the turtle's caption covers no door or button`, await page.evaluate(() => { const c = document.getElementById('caption').getBoundingClientRect();
    return ![...document.querySelectorAll('.home .btn, .home .door, .home-safety')].some((b) => { const r = b.getBoundingClientRect(); return c.left < r.right && c.right > r.left && c.top < r.bottom && c.bottom > r.top; }); }));

  // parents gate: a short tap only says "for grown-ups"
  await page.click('.parents-btn'); await wait(page, 300);
  check(`${tag} parents gate: short tap does not open`, (await page.evaluate(() => document.documentElement.dataset.screen)) === 'home' && (await ids(page)).includes('ui.parentsHold'));

  // ---- Ponor
  await page.click('.dive-btn'); await page.waitForFunction(() => window.__morsky.dive?.state());
  await wait(page, 1200);
  let st = await dive(page, 'D.state()');
  check(`${tag} dive: world from designer tiles (8 floor tiles, 4 zones)`, st.tiles === 8 && st.zones.length === 4, `${st.tiles}`);
  check(`${tag} dive: creatures spawned for every zone`, new Set(st.creatures.map((c) => c.zone)).size === 4 && st.creatures.length >= 12, String(st.creatures.length));
  check(`${tag} dive: HUD targets ≥ 64 px, „Plav dál“ ≥ 88 px`, (await minTarget(page, '.dv-hud .btn')) >= 64 && (await minTarget(page, '.hud-fwd')) >= 88);
  check(`${tag} dive: intro line spoken`, (await ids(page)).includes('ui.diveIntro'));
  await wait(page, 3500);                                   // settle: first rasterisation of the big tiles is a one-off
  const fps2 = () => page.evaluate(() => new Promise((res) => { let n = 0; const t0 = performance.now(); const f = () => { n++; if (performance.now() - t0 < 2000) requestAnimationFrame(f); else res(Math.round(n / 2)); }; requestAnimationFrame(f); }));
  const samples = [await fps2(), await fps2(), await fps2()].sort((x, y) => x - y); const steady = samples[1];
  const need = vp.width === 1024 ? 50 : 45;     // headless software rendering; real iPad still to be checked by hand
  check(`${tag} dive: steady fps headless, median of 3 ≥ ${need} (samples ${samples.join('/')})`, steady >= need, String(samples));
  await shot(page, `${tag}-2-dive-utes`);
  st = await dive(page, 'D.state()');
  check(`${tag} framing at start: seabed at ${Math.round(st.floorScreen * 100)} % of the view (70–80 %)`, st.floorScreen >= 0.68 && st.floorScreen <= 0.82);
  { const off = await hudOffenders(page); check(`${tag} framing at start: no visible creature under the HUD`, !off.length, off.join(',')); }
  { const cs = await page.evaluate(() => [...document.querySelectorAll('.caustic-strip')].map((e) => e.getBoundingClientRect()).filter((r) => r.bottom > 0 && r.top < innerHeight).map((r) => r.top / innerHeight));
    check(`${tag} caustics: only on the seabed (strips start below ${Math.round(Math.min(...cs) * 100)} % of the view)`, cs.length > 0 && Math.min(...cs) > 0.4 && !(await page.$('.dv-caustics')), cs.map((v) => v.toFixed(2)).join()); }
  { const fbb = await page.locator('.hud-fwd').boundingBox(); await page.mouse.click(fbb.x + fbb.width / 2, fbb.y + fbb.height / 2); await wait(page, 2600);
    const s2 = await dive(page, 'D.state()');
    check(`${tag} framing after one „Plav dál“ tap: seabed at ${Math.round(s2.floorScreen * 100)} %`, s2.floorScreen >= 0.68 && s2.floorScreen <= 0.82);
    const off = await hudOffenders(page); check(`${tag} framing after the tap: no visible creature under the HUD`, !off.length, off.join(','));
    await shot(page, `${tag}-2b-after-tap`); }
  // tap the water: she swims there
  const x0 = st.x;
  await page.mouse.click(vp.width * 0.8, vp.height * 0.5); await wait(page, 1500);
  st = await dive(page, 'D.state()');
  check(`${tag} dive: tap in the water → the diver swims there`, st.x > x0 + 150, `${x0} → ${st.x}`);
  // hold „Plav dál“
  const x1 = st.x; const fb = await page.locator('.hud-fwd').boundingBox();
  await page.mouse.move(fb.x + fb.width / 2, fb.y + fb.height / 2); await page.mouse.down(); await wait(page, 1300); await page.mouse.up(); await wait(page, 300);
  st = await dive(page, 'D.state()');
  check(`${tag} dive: hold „Plav dál“ → swims on`, st.x > x1 + 200, `${x1} → ${st.x}`);
  if (vp.width === 1024 || vp.width === 1180) {
    await dive(page, 'D.openGates()'); await dive(page, 'D.teleport(D.state().zones[1].x0 - 900, 450)'); await wait(page, 1500);
    const fbx = await page.locator('.hud-fwd').boundingBox(); await page.mouse.move(fbx.x + fbx.width / 2, fbx.y + fbx.height / 2); await page.mouse.down();
    const cross = await page.evaluate(() => new Promise((res) => { let n = 0; const t0 = performance.now(); const f = () => { n++; if (performance.now() - t0 < 4000) requestAnimationFrame(f); else res(Math.round(n / 4)); }; requestAnimationFrame(f); }));
    await page.mouse.up();
    check(`${tag} dive: swimming across the reef→kelp boundary ≥ 30 fps headless (measured ${cross})`, cross >= 30, String(cross));
    await page.reload(); await page.waitForSelector('.start-layer .play-bubble-btn'); await page.click('.start-layer .play-bubble-btn');
    await page.waitForSelector('.home .dive-btn'); await page.click('.dive-btn'); await page.waitForFunction(() => window.__morsky.dive?.state()); await wait(page, 1200);
  }
  // the closed gate stops her and the turtle asks to find more
  await dive(page, 'D.teleport(D.state().zones[1].x0 - 400, 400)');
  await page.mouse.move(fb.x + fb.width / 2, fb.y + fb.height / 2); await page.mouse.down();
  const said = await page.waitForFunction(() => window.__ids.includes('ui.findMore'), null, { timeout: 5000 }).then(() => true, () => false);
  await page.mouse.up();
  st = await dive(page, 'D.state()');
  check(`${tag} dive: closed gate holds her in the reef + „najdi ještě někoho“`, st.zone === 0 && said, `zone ${st.zone} x ${Math.round(st.x)} said ${said}`);
  // find 3 reef creatures by tapping them
  await dive(page, 'D.teleport(900, 400)'); await wait(page, 600);
  const reef = st.bars[0];
  let opened = 0; let firstCard = true;
  for (const id of reef) {
    if (opened >= 3) break;
    if (!(await tapCreature(page, id))) continue;
    opened++;
    const pins = await page.locator('.card .pin').count();
    if (firstCard) {
      firstCard = false;
      check(`${tag} card: name spoken on tap, then group sentence`, (await ids(page)).includes(`sp.${id}.name`) && (await page.evaluate(() => window.__ids.slice(-3))).some((x) => /\.group$/.test(x)));
      check(`${tag} card: 3 numbered pins on the drawing`, pins === 3, String(pins));
      check(`${tag} card: group badge, zone, eats, size bar, fact`, await page.evaluate(() => ['.badge.grp', '[data-act="home"]', '[data-act="eats"]', '.size-bar .sz-diver svg', '.size-bar .sz-animal svg', '.wow'].every((s) => document.querySelector(`.card ${s}`))));
      await wait(page, 450);
      { const a = await minTarget(page, '.card-actions .btn'); const b = await minTarget(page, '.card-actions [data-act="speak"]');
        check(`${tag} card: buttons ≥ 64 px, speaker 88 px`, a >= 64 && b >= 88, `${a} / ${b}`); }
      check(`${tag} card: the turtle's caption is hidden while the card is open (it said the line)`, await page.evaluate(() => getComputedStyle(document.getElementById('caption')).display === 'none'));
      await page.click('.card .look[data-look="1"]'); await wait(page, 150);
      check(`${tag} card: tapping feature 2 says it`, (await ids(page)).includes(`sp.${id}.look.1`));
      await page.click('.card .wow'); await wait(page, 150);
      check(`${tag} card: „Víš, že…?“ says the fact`, (await ids(page)).includes(`sp.${id}.fact`));
      await shot(page, `${tag}-3-card`);
      await page.click('.card [data-act="flip"]'); await wait(page, 900);
      const back = await page.evaluate(() => ({ photo: !!document.querySelector('.card-flip.flipped .card-back img.photo'), credit: document.querySelector('.card .credit')?.textContent || '', missing: !!document.querySelector('.card-flip.flipped .card-back.missing') }));
      check(`${tag} card: flip shows the photo + credit, or „Fotku zatím nemáme“`, (back.photo && /Test Author/.test(back.credit)) || back.missing, JSON.stringify(back));
      await shot(page, `${tag}-3b-card-back`);
    }
    await page.click('.card [data-act="close"]'); await page.waitForSelector('.card-layer', { state: 'detached' }); await wait(page, 250);
  }
  st = await dive(page, 'D.state()');
  check(`${tag} dive: 3 creatures found by tapping → goal met, gate open`, opened >= 3 && st.goalMet[0], `opened ${opened}`);
  check(`${tag} dive: turtle „Poplaveme hlouběji?“`, (await ids(page)).includes('ui.deeper'));
  check(`${tag} dive: silhouettes coloured in the goal bar`, (await page.locator('.goal-chips .chip.found').count()) >= 3);
  // a creature with a sting/spines shows the look-only mark
  const stinger = species.find((s) => s.touch && s.touch !== 'look');
  if (stinger) {
    await page.evaluate((id) => { window.__morsky.openCard(id); }, stinger.id); await wait(page, 450); await page.waitForSelector('.card-layer');
    check(`${tag} card: „${stinger.touch}“ species shows „jen se díváme“ and says the safety line`, (await page.locator('.card .look-only').count()) === 1 && (await ids(page)).includes(`sp.${stinger.id}.safety`));
    await shot(page, `${tag}-3c-card-sting`);
    await page.evaluate(() => window.__morsky.closeCard());
  }
  for (const id of ['papousek', 'kapustnak', 'chobotnice', 'keporkak', stinger?.id].filter((x) => x && species.some((s) => s.id === x))) {
    const r = await cardFits(page, id);
    check(`${tag} card ${id}: everything fits without scrolling (${r.sh} ≤ ${r.ch})`, r.sh <= r.ch + 1 && r.inside);
  }
  for (const [id, why] of [['hvezdice', 'no photo downloaded'], ['das', 'photo hidden (photos/hidden.json)']]) {
    await page.evaluate((i) => { window.__morsky.openCard(i); }, id); await page.waitForSelector('.card-layer'); await wait(page, 400);
    await page.click('.card [data-act="flip"]'); await wait(page, 850);
    const b = await page.evaluate(() => ({ missing: !!document.querySelector('.card-flip.flipped .card-back.missing .missing-text'), photo: !!document.querySelector('.card-flip.flipped img.photo'), hint: document.querySelector('.missing-hint')?.textContent || '' }));
    check(`${tag} card back, ${why}: designed „Fotku zatím nemáme“ page, no photo`, b.missing && !b.photo && (id === 'das' ? b.hint === '' : b.hint.length > 5), JSON.stringify(b));
    await shot(page, `${tag}-3d-card-nophoto-${id}`);
    await page.evaluate(() => window.__morsky.closeCard());
  }
  // rubbish
  const tr0 = st.trashSpots[0];
  await dive(page, 'D.teleport(a.x - 350, a.y - 150)', tr0); await wait(page, 700);
  const ts = await dive(page, 'D.trashScreen(0)');
  const under = await page.evaluate(([x, y]) => { const e = document.elementFromPoint(x, y); return e?.closest('.trash') ? 'trash' : `${e?.tagName}.${e?.className?.baseVal ?? e?.className}`; }, [ts.x, ts.y]);
  await page.mouse.click(ts.x, ts.y); await wait(page, 3200);
  st = await dive(page, 'D.state()');
  check(`${tag} trash: tap → into the net, place brightens, turtle thanks`, st.trash === 1 && st.trashSpots[0].done && (await page.locator('.patch.clean').count()) >= 1 && (await ids(page)).includes(`trash.${tr0.id}`), `trash ${st.trash}, under the tap: ${under}, at ${Math.round(ts.x)},${Math.round(ts.y)}`);
  check(`${tag} trash: the net counter shows 1`, (await page.textContent('.hud-net .net-n')) === '1');
  await shot(page, `${tag}-4-trash-clean`);
  // other zones
  await dive(page, 'D.openGates()');
  for (const [k, name] of [[1, 'chaluhy'], [2, 'sire-more'], [3, 'hlubiny']]) {
    await dive(page, `D.teleport(D.state().zones[${k}].x0 + 2500, ${k === 3 ? 99999 : 500})`); await wait(page, 1600);
    st = await dive(page, 'D.state()');
    check(`${tag} zone ${name}: entered, goal bar shows its creatures`, st.zone === k && (await page.locator('.goal-chips .chip').count()) === st.bars[k].length);
    { const pill = await rect(page, '.gauge-m');
      const hit = await page.evaluate((p) => [...document.querySelectorAll('.gauge .tick:not(.under-pill)')].filter((e) => { const r = e.getBoundingClientRect(); return r.left < p.r && r.right > p.l && r.top < p.b && r.bottom > p.t; }).map((e) => e.textContent), pill);
      check(`${tag} gauge in ${name}: no tick label under the depth pill`, !hit.length, hit.join(',')); }
    if (k === 2) {
      const bb = await page.locator('.hud-back').boundingBox(); await page.mouse.move(bb.x + bb.width / 2, bb.y + bb.height / 2); await page.mouse.down();
      let bad = 0; for (let i = 0; i < 8; i++) { await wait(page, 250); if (overlap(await rect(page, '.guide-wrap'), await rect(page, '.gauge'))) bad++; }
      await page.mouse.up(); await wait(page, 800);
      for (let i = 0; i < 4; i++) { await wait(page, 250); if (overlap(await rect(page, '.guide-wrap'), await rect(page, '.gauge'))) bad++; }
      check(`${tag} open sea: the turtle never sits behind the depth gauge (swimming back and turning)`, bad === 0, `${bad} overlaps`);
    }
    if (k === 3) {
      check(`${tag} deep: dark (${st.dark.toFixed(2)}), headlamp on, depth > 1000 m (${Math.round(st.depth)})`, st.dark > 0.95 && st.lampOn && st.depth > 1000);
      check(`${tag} deep: glowing creatures above the dark`, (await page.locator('.dv-glow .cr-glow').count()) >= 1);
      check(`${tag} deep: the lamp line spoken`, (await ids(page)).includes('ui.lamp'));
    }
    await shot(page, `${tag}-5-${name}`);
  }
  // finish the deep goal → swim-up button
  for (const id of st.bars[3]) await dive(page, 'D.find(a)', id);
  await wait(page, 300);
  check(`${tag} deep goal → „Vynořit se“ arrow appears`, await page.isVisible('.hud-up'));
  // the 15-minute yawn appears at the next pause, not mid-action
  await dive(page, 'D.surface()');
  await page.waitForSelector('.dive-summary', { timeout: 8000 }); await wait(page, 600);
  { const n = await page.locator('.sum-cr').count(); const tr = await page.textContent('.sum-trash');
    check(`${tag} end: summary lists who we met + rubbish + safety line`, n >= 5 && (await page.textContent('.sum-safety')).includes('jen s dospělým') && /1/.test(tr), `${n} found, „${tr}“`); }
  await shot(page, `${tag}-6-summary`);
  const read = await page.waitForFunction(() => window.__ids.includes('ui.endFound') && window.__ids.some((i) => /^ui\.trashCount\./.test(i)), null, { timeout: 12000 }).then(() => true, () => false);
  check(`${tag} end: turtle reads the found names, rubbish count, safety`, read, (await ids(page)).slice(-8).join(','));
  // release into my sea
  await page.click('.dive-summary [data-act="release"]');
  await page.waitForSelector('.sea .drawer-item'); await wait(page, 500);
  const drawer = await page.locator('.drawer-item').count(); const known = await page.locator('.drawer-item:not(.unknown)').count();
  check(`${tag} sea: drawer has every species, found ones in colour, others silhouettes`, drawer === species.length && known >= 5 && known < drawer, `${known}/${drawer}`);
  check(`${tag} sea: new friends highlighted`, (await page.locator('.drawer-item.fresh').count()) >= 1);
  // drag one in
  const it = page.locator('.drawer-item:not(.unknown)').first(); const ib = await it.boundingBox();
  await page.mouse.move(ib.x + ib.width / 2, ib.y + ib.height / 2); await page.mouse.down();
  await page.mouse.move(vp.width * 0.4, vp.height * 0.4, { steps: 8 }); await page.mouse.up(); await wait(page, 400);
  // tap-tap another
  await page.locator('.drawer-item:not(.unknown):not(.placed)').first().click(); await wait(page, 150);
  await page.mouse.click(vp.width * 0.65, vp.height * 0.3); await wait(page, 500);
  let placed = await page.evaluate(() => window.__morsky.sea.placed().length);
  check(`${tag} sea: drag and tap+tap both release a creature`, placed === 2, String(placed));
  await page.locator('.daynight').click(); await wait(page, 600);
  check(`${tag} sea: night mode`, await page.evaluate(() => document.querySelector('.sea').classList.contains('night')) && (await ids(page)).includes('ui.seaNight'));
  await shot(page, `${tag}-7-sea-night`);
  await page.reload(); await page.waitForSelector('.start-layer .play-bubble-btn'); await page.click('.start-layer .play-bubble-btn');
  await page.evaluate(() => window.__morsky.go('sea')); await page.waitForSelector('.sea .drawer-item'); await wait(page, 500);
  placed = await page.evaluate(() => window.__morsky.sea.placed().length);
  check(`${tag} sea: placement + night survive a reload`, placed === 2 && await page.evaluate(() => document.querySelector('.sea').classList.contains('night')));
  await page.locator('.daynight').click(); await wait(page, 500);
  await shot(page, `${tag}-7-sea-day`);
  await page.evaluate(() => window.__morsky.session._setPlayed(16 * 60 * 1000));     // a reload restarts the session clock
  // ---- quiz
  await page.evaluate(() => window.__morsky.go('quiz')); await page.waitForSelector('.quiz-stage .q-prompt'); await wait(page, 400);
  for (let q = 0; q < 5; q++) {
    const cur = await page.evaluate(() => window.__morsky.quiz.current());
    if (q === 0 && cur.options?.length === 3) {
      const wrong = cur.options.find((o) => o !== cur.target);
      await page.click(`.q-opt[data-v="${wrong}"]`); await wait(page, 200);
      check(`${tag} quiz: 1st miss → gentle „zkus to ještě jednou“, no „špatně“`, (await ids(page)).includes('ui.quizTry'));
      await page.click(`.q-opt[data-v="${wrong}"]`); await wait(page, 200);
      check(`${tag} quiz: 2nd miss → the choice narrows (one option leaves), answer not lit`, (await page.locator('.q-opt.gone').count()) === 1 && (await page.locator('.q-opt.right').count()) === 0);
      await shot(page, `${tag}-8-quiz`);
    }
    if (cur.type === 'isFish') {
      const fish = await page.evaluate((id) => window.__morsky.species.find((s) => s.id === id).group, cur.target);
      await page.click(`.yes-no[data-v="${/^ryba/.test(fish) ? 'yes' : 'no'}"]`);
    } else await page.click(`.q-opt[data-v="${cur.target}"]`);
    await page.waitForFunction((i) => !window.__morsky.quiz?.current() || window.__morsky.quiz.current().i > i || document.querySelector('.quiz-done'), q, { timeout: 15000 });
  }
  await page.waitForSelector('.quiz-done', { timeout: 15000 });
  check(`${tag} quiz: 5 questions → kind ending`, (await ids(page)).includes('ui.quizDone'));
  const yawn = await page.waitForSelector('.tired-layer', { timeout: 8000 }).then(() => true, () => false);
  check(`${tag} 15 minutes: the turtle yawns at the next pause (after the quiz), once`, yawn && (await ids(page)).includes('ui.tired'));
  if (yawn) { await shot(page, `${tag}-8b-tired`); await page.click('.tired-layer [data-act="stay"]'); }
  // ---- habitat
  await page.evaluate(() => window.__morsky.go('habitat')); await page.waitForSelector('.hab-cr'); await wait(page, 400);
  await shot(page, `${tag}-9-habitat`);
  const six = await page.evaluate(() => window.__morsky.habitat.six());
  const wrongZone = ['utes', 'chaluhy', 'sire-more', 'hlubiny'].find((z) => z !== six[0].zone);
  await page.evaluate(([id, z]) => window.__morsky.habitat.drop(id, z), [six[0].id, wrongZone]); await wait(page, 150);
  check(`${tag} habitat: wrong floor → kind correction, animal stays in the tray`, (await ids(page)).includes('ui.habitatWrong') && (await page.locator('.hab-tray .hab-cr').count()) === 6);
  // drag one for real
  const b0 = await page.locator(`.hab-cr[data-id="${six[0].id}"]`).boundingBox(); const fl = await page.locator(`.hab-floor[data-zone="${six[0].zone}"]`).boundingBox();
  await page.mouse.move(b0.x + b0.width / 2, b0.y + b0.height / 2); await page.mouse.down();
  await page.mouse.move(fl.x + fl.width * 0.4, fl.y + fl.height / 2, { steps: 8 }); await page.mouse.up(); await wait(page, 200);
  for (const s of six.slice(1)) await page.evaluate(([id, z]) => window.__morsky.habitat.drop(id, z), [s.id, s.zone]);
  await wait(page, 300);
  check(`${tag} habitat: all 6 home (drag + drop) → „Všichni jsou doma!“`, (await page.locator('.hab-cr.home').count()) === 6 && (await ids(page)).includes('ui.habitatDone'));
  await shot(page, `${tag}-9b-habitat-done`);
  // ---- parents
  await page.evaluate(() => window.__morsky.go('home')); await page.waitForSelector('.parents-btn');
  const pb = await page.locator('.parents-btn').boundingBox();
  await page.mouse.move(pb.x + pb.width / 2, pb.y + pb.height / 2); await page.mouse.down(); await wait(page, 3300); await page.mouse.up();
  await page.waitForSelector('.parents-screen', { timeout: 3000 });
  check(`${tag} parents: opens after a 3 s hold`, true);
  check(`${tag} parents: safety sentences, credits, offline status`, (await page.textContent('.safety-box')).includes('jen s dospělým') && (await page.locator('.credits li').count()) === species.length && (await page.textContent('.offline-ready')).length > 3);
  await shot(page, `${tag}-10-parents`);
  const hair0 = await page.evaluate(() => getComputedStyle(document.documentElement).getPropertyValue('--hair').trim());
  await page.click('.swatch[data-act="hair"][data-v="3"]'); await wait(page, 150);
  const hair1 = await page.evaluate(() => getComputedStyle(document.documentElement).getPropertyValue('--hair').trim());
  check(`${tag} parents: hair colour changes the diver (--hair ${hair0} → ${hair1})`, hair1 && hair1 !== hair0);
  await page.fill('.turtle-name', 'Bublinka'); await page.press('.turtle-name', 'Tab'); await wait(page, 100);
  await page.click('.seg-btn[data-act="rate"][data-v="slow"]'); await wait(page, 300);
  check(`${tag} parents: turtle name shown in the caption, never spoken`, (await page.textContent('#caption .cap-who')) === 'Bublinka' && !(await page.evaluate(() => window.__spoken.join(' '))).includes('Bublinka'));
  const backup = await page.evaluate(() => window.__morsky.store.exportText());
  await page.click('.seg-btn[data-act="lang"][data-v="en"]'); await wait(page, 200);
  check(`${tag} parents: English switches the labels`, (await page.textContent('.parents-screen .title-pill')).includes('Grown-ups'));
  await page.click('.seg-btn[data-act="lang"][data-v="cs"]'); await wait(page, 200);
  await page.click('.reset-row [data-act="reset"]'); await page.click('[data-act="reset-yes"]'); await wait(page, 200);
  check(`${tag} parents: reset (with confirmation) clears discoveries, keeps the look`, (await page.evaluate(() => window.__morsky.store.foundCount())) === 0 && (await page.evaluate(() => window.__morsky.store.get('hair'))) === 3);
  await page.click('[data-act="import"]'); await page.fill('.import-text', backup); await page.click('[data-act="import-go"]'); await wait(page, 200);
  check(`${tag} parents: restore from backup brings the discoveries back`, (await page.evaluate(() => window.__morsky.store.foundCount())) >= 5);
  await page.click('[data-act="import"]'); await page.fill('.import-text', '{"app":"houbicky"}'); await page.click('[data-act="import-go"]'); await wait(page, 100);
  check(`${tag} parents: a bad backup is refused`, (await page.textContent('.backup-msg')).length > 3 && (await page.evaluate(() => window.__morsky.store.foundCount())) >= 5);
  await ctx.close();
}

// ============================================================ B. portrait iPad
{
  const { ctx, page } = await session({ width: 768, height: 1024 });
  await page.goto(`${BASE}/`); await page.waitForSelector('.start-layer .play-bubble-btn');
  check('portrait: „Otoč iPad na šířku“ covers the game', await page.evaluate(() => getComputedStyle(document.getElementById('rotate')).display !== 'none' && document.getElementById('rotate').textContent.includes('Otoč iPad')));
  await shot(page, '768x1024-portrait');
  await ctx.close();
}
// ============================================================ C. reduced motion
{
  const { ctx, page } = await session({ width: 1024, height: 768 }, { reducedMotion: 'reduce' });
  await page.goto(`${BASE}/?autostart`); await page.waitForSelector('.home .dive-btn');
  await page.click('.dive-btn'); await page.waitForFunction(() => window.__morsky.dive?.state()); await wait(page, 1200);
  check('reduced motion: kelp/rays/tails do not animate', await page.evaluate(() => ['.dv-rays', '.cr .tail'].every((s) => { const e = document.querySelector(s); return !e || getComputedStyle(e).animationName === 'none'; })));
  check('reduced motion: parallax layers do not move (factor 0)', await page.evaluate(() => getComputedStyle(document.documentElement).getPropertyValue('--parallax-far').trim() === '0'));
  await shot(page, '1024x768-reduced-motion');
  await ctx.close();
}
// ============================================================ D. level 2 after 10 discoveries
{
  const found = Object.fromEntries(species.filter((s) => s.level === 1).slice(0, 9).map((s) => [s.id, '2026-10-17T10:00:00Z']));
  const { ctx, page } = await session({ width: 1024, height: 768 }, { seed: { found } });
  await page.goto(`${BASE}/?autostart`); await page.waitForSelector('.home .dive-btn');
  await page.click('.dive-btn'); await page.waitForFunction(() => window.__morsky.dive?.state()); await wait(page, 800);
  const st = await dive(page, 'D.state()');
  const tenth = st.creatures.find((c) => !found[c.id] && c.zone === 'utes') || st.creatures.find((c) => !found[c.id]);
  await dive(page, 'D.teleport(a.x - 300, a.y)', tenth); await wait(page, 600);
  await tapCreature(page, tenth.id);
  await page.click('.card [data-act="close"]'); await wait(page, 900);
  check('level 2: unlocked by the 10th discovery, turtle celebrates', (await page.evaluate(() => window.__morsky.store.get('level'))) === 2 && (await ids(page)).includes('ui.level2'));
  await ctx.close();
}
// ============================================================ E. offline (service worker) — needs a secure context: localhost
{
  const { ctx, page } = await session({ width: 1024, height: 768 }, { sw: 'allow' });
  await page.goto(`${BASE}/?autostart`); await page.waitForSelector('.home .dive-btn');
  const ok = await page.waitForFunction(() => navigator.serviceWorker.controller || window.__morsky.sw?.ok, null, { timeout: 15000 }).then(() => true, () => false);
  await page.evaluate(() => window.__morsky.go('parents'));
  const full = await page.waitForFunction(() => /100\s*%/.test(document.querySelector('.offline-ready')?.textContent || ''), null, { timeout: 45000 }).then(() => true, () => false);
  check('offline: service worker installs and reports „Připraveno na cestu: 100 %“', ok && full, await page.textContent('.offline-ready').catch(() => ''));
  await ctx.setOffline(true);
  await page.goto(`${BASE}/?autostart`).catch(() => {});
  const booted = await page.waitForSelector('.home .dive-btn', { timeout: 10000 }).then(() => true, () => false);
  let diveOk = false;
  if (booted) { await page.click('.dive-btn'); diveOk = await page.waitForFunction(() => window.__morsky.dive?.state()?.creatures.length > 0, null, { timeout: 10000 }).then(() => true, () => false); }
  check('offline: the game boots and dives with the network off', booted && diveOk);
  await ctx.close();
}


// ============================================================ F. language switch (flag button) at both iPad sizes
async function flagClear(page) {
  return page.evaluate(() => {
    const f = document.getElementById('lang-btn'); if (!f || !f.getClientRects().length) return { visible: false };
    const r = f.getBoundingClientRect();
    const hits = [...document.querySelectorAll('.btn, .door, .daynight-seg, .hud-fwd-label, .goal-bar, .title-pill:not(.sr-only), .gauge, .q-prompt, .q-opt, .drawer, .home-safety, .start-logo, .home-logo, .play-bubble-btn, .start-safety, .quiz-progress')]
      .filter((e) => e !== f && !f.contains(e) && e.getClientRects().length && getComputedStyle(e).visibility !== 'hidden')
      .filter((e) => { const q = e.getBoundingClientRect(); return q.width && r.left < q.right && r.right > q.left && r.top < q.bottom && r.bottom > q.top; })
      .map((e) => e.className.baseVal ?? e.className);
    return { visible: true, size: Math.min(r.width, r.height), hits };
  });
}
for (const vp of [{ width: 1024, height: 768 }, { width: 1180, height: 820 }]) {
  const tag = `${vp.width}x${vp.height} lang`;
  const { ctx, page } = await session(vp);
  await page.goto(`${BASE}/`); await page.waitForSelector('.start-layer .play-bubble-btn');
  let fc = await flagClear(page);
  check(`${tag}: flag button on the start screen, ≥ 64 px, collides with nothing`, fc.visible && fc.size >= 64 && !fc.hits.length, JSON.stringify(fc));
  await page.click('#lang-btn'); await wait(page, 300);
  check(`${tag}: start screen switches to English at once (logo + labels)`, (await page.getAttribute('.start-logo', 'aria-label')) === 'Ocean World' && (await page.locator('.start-logo svg[data-lang="en"]').count()) === 1 && (await page.evaluate(() => document.documentElement.lang)) === 'en');
  await page.click('#lang-btn'); await wait(page, 200);
  await page.click('.start-layer .play-bubble-btn'); await page.waitForSelector('.home .dive-btn'); await wait(page, 500);
  fc = await flagClear(page);
  check(`${tag}: flag on Loďka collides with nothing`, fc.visible && !fc.hits.length, JSON.stringify(fc));
  check(`${tag}: it shows the OTHER language's flag (English while Czech), designer's i-flag-en-btn`, (await page.getAttribute('#lang-btn', 'aria-label')) === 'English' && (await page.innerHTML('#lang-btn')).includes('#i-flag-en-btn'));
  await page.click('#lang-btn'); await wait(page, 600);
  const last = await page.evaluate(() => ({ id: window.__ids.at(-1), lang: window.__langs.at(-1), text: window.__spoken.at(-1) }));
  check(`${tag}: tap → the turtle says one line in English`, last.id === 'ui.langHello' && last.lang === 'en' && /English/.test(last.text), JSON.stringify(last));
  check(`${tag}: home texts switch (logo, pill, doors, safety)`, (await page.locator('.home-logo svg[data-lang="en"]').count()) === 1 && (await page.textContent('.dive-btn [data-t]')) === 'Dive in!' && (await page.textContent('.door[data-act="quiz"] .door-label')) === 'Quiz' && (await page.textContent('.home-safety')).includes('grown-up'));
  check(`${tag}: stored + parents' corner in sync`, (await page.evaluate(() => window.__morsky.store.get('lang'))) === 'en');
  await shot(page, `${vp.width}x${vp.height}-11-home-en`);
  // dive in English: card + summary
  await page.click('.dive-btn'); await page.waitForFunction(() => window.__morsky.dive?.state()); await wait(page, 900);
  fc = await flagClear(page);
  check(`${tag}: flag in the dive HUD collides with nothing`, fc.visible && !fc.hits.length, JSON.stringify(fc));
  await page.evaluate(() => { window.__morsky.openCard('klaun'); }); await page.waitForSelector('.card-layer'); await wait(page, 400);
  const en = species.find((x) => x.id === 'klaun').name.en;
  check(`${tag}: card in English (name + spoken group line)`, (await page.textContent('.sp-name')) === en && /fish/i.test(await page.evaluate(() => window.__spoken.at(-1))));
  await shot(page, `${vp.width}x${vp.height}-11-card-en`);
  await page.evaluate(() => window.__morsky.closeCard());
  await dive(page, 'D.find("klaun")'); await dive(page, 'D.surface()'); await page.waitForSelector('.dive-summary', { timeout: 8000 });
  check(`${tag}: end-of-dive summary in English`, (await page.textContent('.sum-title')) === 'Who we met' && (await page.textContent('.sum-safety')).includes('grown-up'));
  await page.click('.dive-summary [data-act="home"]'); await page.waitForSelector('.home .dive-btn');
  // sea + quiz
  await page.evaluate(() => window.__morsky.go('sea')); await page.waitForSelector('.sea .drawer-item'); await wait(page, 300);
  fc = await flagClear(page);
  check(`${tag}: Můj kousek moře in English, flag collides with nothing`, (await page.textContent('.sea .title-pill')) === 'My piece of sea' && fc.visible && !fc.hits.length, JSON.stringify(fc));
  await page.evaluate(() => window.__morsky.go('quiz')); await page.waitForSelector('.q-prompt'); await wait(page, 500);
  fc = await flagClear(page);
  const qp = await page.textContent('.q-prompt span');
  check(`${tag}: quiz in English (title + prompt), flag collides with nothing`, (await page.textContent('.quiz .title-pill')) === 'Who am I?' && /^(Where|Is|Who|I |My |.*Who am I\?)/.test(qp) && fc.visible && !fc.hits.length, `${qp} ${JSON.stringify(fc)}`);
  await shot(page, `${vp.width}x${vp.height}-11-quiz-en`);
  await page.click('#lang-btn'); await wait(page, 400);
  check(`${tag}: switching back mid-quiz → Czech title + prompt, same question`, (await page.textContent('.quiz .title-pill')) === 'Kdo jsem?' && (await page.textContent('.q-prompt span')) !== qp);
  await page.click('#lang-btn'); await wait(page, 200);
  await page.reload(); await page.waitForSelector('.start-layer .play-bubble-btn');
  check(`${tag}: the choice survives a reload`, (await page.getAttribute('.start-logo', 'aria-label')) === 'Ocean World');
  await page.click('.start-layer .play-bubble-btn'); await page.evaluate(() => window.__morsky.go('parents')); await page.waitForSelector('.parents-screen');
  check(`${tag}: parents' corner shows English selected; flag hidden there`, (await page.getAttribute('.seg-btn[data-act="lang"][data-v="en"]', 'aria-pressed')) === 'true' && !(await page.isVisible('#lang-btn')));
  await page.click('.seg-btn[data-act="lang"][data-v="cs"]'); await page.click('[data-act="home"]'); await page.waitForSelector('.home .dive-btn');
  check(`${tag}: changing it in the parents' corner updates the flag`, (await page.getAttribute('#lang-btn', 'aria-label')) === 'English');
  await ctx.close();
}

// ============================================================ G. iPhone landscape (design/phone.css), simulated safe areas
const PHONES = [{ width: 667, height: 375, safe: [0, 0, 0], tag: 'SE' }, { width: 844, height: 390, safe: [47, 47, 21], tag: '14' }, { width: 932, height: 430, safe: [59, 59, 21], tag: 'ProMax' }];
for (const ph of PHONES) {
  const vp = { width: ph.width, height: ph.height }; const tag = `phone ${ph.width}x${ph.height}`; const pre = `phone-${ph.width}x${ph.height}`;
  const { ctx, page } = await session(vp);
  await ctx.addInitScript(([l, r, b]) => { addEventListener('DOMContentLoaded', () => { const st = document.createElement('style'); st.textContent = `:root{--sim-safe-l:${l}px;--sim-safe-r:${r}px;--sim-safe-b:${b}px}`; document.head.append(st); }); }, ph.safe);
  const [sl, sr, sb] = ph.safe;
  const insideSafe = (sel) => page.evaluate(([q, l, r, b]) => [...document.querySelectorAll(q)].filter((e) => e.getClientRects().length && getComputedStyle(e).visibility !== 'hidden')
    .filter((e) => { const x = e.getBoundingClientRect(); return x.left < l - 1 || x.right > innerWidth - r + 1 || x.bottom > innerHeight - b + 1 || x.top < -1; }).map((e) => e.className.baseVal ?? e.className), [sel, sl, sr, sb]);
  await page.goto(`${BASE}/`); await page.waitForSelector('.start-layer .play-bubble-btn'); await wait(page, 600);
  check(`${tag} start: phone layout active (touch-min 44 px)`, await page.evaluate(() => getComputedStyle(document.documentElement).getPropertyValue('--touch-min').trim() === '44px'));
  check(`${tag} start: play bubble ≥ 72 px, clear of the logo, safety line and boat`, (await minTarget(page, '.play-bubble-btn')) >= 72 && await page.evaluate(() => {
    const p = document.querySelector('.play-bubble-btn').getBoundingClientRect(); const ov = (q) => { if (!q) return false; const r = q.getBoundingClientRect(); return p.left < r.right && p.right > r.left && p.top < r.bottom && p.bottom > r.top; };
    return !ov(document.querySelector('.start-logo')) && !ov(document.querySelector('.start-safety')) && !ov(document.querySelector('.start-layer .scene-live .boat')); }));
  { const fc = await flagClear(page); check(`${tag} start: language button collides with nothing`, fc.visible && !fc.hits.length, JSON.stringify(fc)); }
  await shot(page, `${pre}-0-start`);
  await page.click('.start-layer .play-bubble-btn'); await page.waitForSelector('.home .dive-btn'); await wait(page, 700);
  check(`${tag} home: every control inside the safe area`, !(await insideSafe('.home .btn, .home .door, #lang-btn')).length, (await insideSafe('.home .btn, .home .door, #lang-btn')).join(','));
  check(`${tag} home: touch targets ≥ 44 px`, (await minTarget(page, '.home .btn, .home .door, #lang-btn')) >= 44);
  { const fc = await flagClear(page); check(`${tag} home: language button collides with nothing`, fc.visible && !fc.hits.length, JSON.stringify(fc)); }
  check(`${tag} home: the caption covers no door or button`, await page.evaluate(() => { const c = document.getElementById('caption'); if (!c.classList.contains('show')) return true; const k = c.getBoundingClientRect();
    return ![...document.querySelectorAll('.home .btn, .home .door, .home-safety, #lang-btn')].some((b) => { const r = b.getBoundingClientRect(); return k.left < r.right && k.right > r.left && k.top < r.bottom && k.bottom > r.top; }); }));
  await shot(page, `${pre}-1-home`);
  // dive
  await page.click('.dive-btn'); await page.waitForFunction(() => window.__morsky.dive?.state()); await wait(page, 2200);
  let st = await dive(page, 'D.state()');
  check(`${tag} dive: seabed framed at ${Math.round(st.floorScreen * 100)} % (60–80 %)`, st.floorScreen >= 0.6 && st.floorScreen <= 0.8);
  { const off = await hudOffenders(page); check(`${tag} dive: no visible creature under the HUD`, !off.length, off.join(',')); }
  check(`${tag} dive: HUD inside the safe area`, !(await insideSafe('.dv-hud .btn, .goal-bar, .gauge, #lang-btn')).length, (await insideSafe('.dv-hud .btn, .goal-bar, .gauge, #lang-btn')).join(','));
  check(`${tag} dive: HUD targets ≥ 44 px`, (await minTarget(page, '.dv-hud .btn:not([hidden])')) >= 44);
  await shot(page, `${pre}-2-dive`);
  const fbp = await page.locator('.hud-fwd').boundingBox(); await page.mouse.click(fbp.x + fbp.width / 2, fbp.y + fbp.height / 2); await wait(page, 2400);
  st = await dive(page, 'D.state()');
  { const off = await hudOffenders(page); check(`${tag} dive after „Plav dál“: seabed ${Math.round(st.floorScreen * 100)} %, no creature under the HUD`, st.floorScreen >= 0.6 && st.floorScreen <= 0.8 && !off.length, off.join(',')); }
  // cards: a normal one, the sting variant, the longest names
  for (const id of ['klaun', 'meduza', 'papousek', 'kapustnak', 'chobotnice'].filter((x) => species.some((s) => s.id === x))) {
    const r = await cardFits(page, id);
    check(`${tag} card ${id}: fits without scrolling (${r.sh} ≤ ${r.ch})`, r.sh <= r.ch + 1 && r.inside);
  }
  await page.evaluate(() => { window.__morsky.openCard('meduza'); }); await page.waitForSelector('.card-layer'); await wait(page, 500);
  check(`${tag} card: 3 pins, look-only mark, caption hidden, inside the safe area`, (await page.locator('.card .pin').count()) === 3 && (await page.locator('.card .look-only').count()) === 1
    && await page.evaluate(() => getComputedStyle(document.getElementById('caption')).display === 'none') && !(await insideSafe('.card')).length);
  await shot(page, `${pre}-3-card-sting`);
  await page.evaluate(() => window.__morsky.closeCard());
  // summary
  await dive(page, 'D.find("klaun")'); await dive(page, 'D.find("konik")'); await dive(page, 'D.surface()'); await page.waitForSelector('.dive-summary', { timeout: 9000 }); await wait(page, 500);
  check(`${tag} summary: fits without scrolling, buttons inside the safe area`, await page.evaluate(() => { const c = document.querySelector('.sum-card'); return c.scrollHeight <= c.clientHeight + 1; }) && !(await insideSafe('.sum-actions .btn')).length);
  await shot(page, `${pre}-4-summary`);
  await page.click('.dive-summary [data-act="home"]'); await page.waitForSelector('.home .dive-btn');
  await page.evaluate(() => window.__morsky.go('sea')); await page.waitForSelector('.sea .drawer-item'); await wait(page, 500);
  await page.locator('.drawer-item:not(.unknown)').first().click(); await wait(page, 150); await page.mouse.click(vp.width * 0.5, vp.height * 0.45); await wait(page, 500);
  const drawerPad = await page.evaluate(() => { const d = document.querySelector('.drawer'); const cs = getComputedStyle(d); const first = d.querySelector('.drawer-item').getBoundingClientRect();
    return { first: first.left, padR: parseFloat(cs.paddingRight), bottom: d.getBoundingClientRect().bottom - first.bottom }; });
  check(`${tag} sea: tap + tap releases a creature; toggles inside the safe area; drawer content clear of the notch + home indicator`, (await page.evaluate(() => window.__morsky.sea.placed().length)) >= 1
    && !(await insideSafe('.dn-btn, .sea .topbar .btn')).length && drawerPad.first >= sl && drawerPad.padR >= sr - 1 && drawerPad.bottom >= sb - 1, JSON.stringify(drawerPad));
  await shot(page, `${pre}-5-sea`);
  await page.evaluate(() => window.__morsky.go('quiz')); await page.waitForSelector('.q-prompt'); await wait(page, 600);
  check(`${tag} quiz: prompt + 3 options visible, nothing overlaps`, await page.evaluate(() => {
    const els = [document.querySelector('.q-prompt'), ...document.querySelectorAll('.q-opt')]; const rs = els.map((e) => e.getBoundingClientRect());
    if (rs.length !== 4 || rs.some((r) => r.bottom > innerHeight || r.top < 0)) return false;
    for (let i = 0; i < rs.length; i++) for (let j = i + 1; j < rs.length; j++) { const a = rs[i]; const b = rs[j]; if (a.left < b.right && a.right > b.left && a.top < b.bottom && a.bottom > b.top) return false; }
    return true; }) && (await minTarget(page, '.q-opt')) >= 88);
  await shot(page, `${pre}-6-quiz`);
  await page.evaluate(() => window.__morsky.go('habitat')); await page.waitForSelector('.hab-cr'); await wait(page, 400);
  for (const s of await page.evaluate(() => window.__morsky.habitat.six())) await page.evaluate(([i, z]) => window.__morsky.habitat.drop(i, z), [s.id, s.zone]);
  await wait(page, 300);
  check(`${tag} habitat: all six home; floors + tray on screen`, (await page.locator('.hab-cr.home').count()) === 6 && !(await insideSafe('.hab-cut, .hab-tray')).length);
  await shot(page, `${pre}-7-habitat`);
  await page.evaluate(() => window.__morsky.go('parents')); await page.waitForSelector('.parents-screen'); await wait(page, 300);
  check(`${tag} parents: sheet sides + buttons inside the safe area (the sheet scrolls under the home indicator)`, !(await insideSafe('.parents-screen .topbar .btn')).length
    && await page.evaluate(([l, r]) => { const x = document.querySelector('.sheet').getBoundingClientRect(); return x.left >= l - 1 && x.right <= innerWidth - r + 1; }, [sl, sr]));
  check(`${tag} parents: no caption left over from the previous screen`, !(await page.evaluate(() => document.getElementById('caption').classList.contains('show'))));
  await shot(page, `${pre}-8-parents`);
  await ctx.close();
}
{
  const { ctx, page } = await session({ width: 390, height: 844 });
  await page.goto(`${BASE}/`); await page.waitForSelector('.start-layer .play-bubble-btn');
  check('phone portrait: „Otoč telefon na šířku“ covers the game', await page.evaluate(() => getComputedStyle(document.getElementById('rotate')).display !== 'none' && document.getElementById('rotate').textContent.includes('Otoč telefon')));
  await shot(page, 'phone-390x844-portrait');
  await ctx.close();
}

check(`no page errors (${errors.length})`, errors.length === 0, errors.slice(0, 5).join(' | '));
check(`no 404 requests (${notFound.size})`, notFound.size === 0, [...notFound].join(', '));
// gauge at 3 m: the „10“ label must not collide with the pill

await browser.close();
const fails = results.filter((r) => r.startsWith('FAIL'));
console.log(results.join('\n'));
console.log(`\ne2e: ${results.length - fails.length}/${results.length} passed · screens in dev/screens/`);
process.exit(fails.length ? 1 : 0);
