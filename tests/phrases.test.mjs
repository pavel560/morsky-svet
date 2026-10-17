// node tests/phrases.test.mjs — the spoken-line catalogue: complete, both languages, no template leftovers,
// and every phrase id the code asks for exists (static scan of js/).
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { t, done } from './_harness.mjs';
const ROOT = path.join(path.dirname(fileURLToPath(import.meta.url)), '..');
const { buildCatalogue, UI_SAY, TRASH_COUNT_MAX, trashCountKey } = await import(pathToFileURL(path.join(ROOT, 'js/phrases.js')).href);
const { DEPTH_MARKS } = await import(pathToFileURL(path.join(ROOT, 'js/dive/world.js')).href);
const { strings } = await import(pathToFileURL(path.join(ROOT, 'js/i18n.js')).href);
const read = (n) => { const p = path.join(ROOT, 'data', `${n}.json`); const j = JSON.parse(fs.readFileSync(fs.existsSync(p) ? p : path.join(ROOT, 'dev/placeholders', `${n}.json`), 'utf8')); return Array.isArray(j) ? j : j[n]; };
const species = read('species'); const zones = read('zones'); const trash = read('trash');
const cat = buildCatalogue(species, { zones, trash });
const cs = cat.cs; const en = cat.en;
t('same phrase ids in cs and en', Object.keys(cs).sort().join() === Object.keys(en).sort().join(), `${Object.keys(cs).length} vs ${Object.keys(en).length}`);
t('no empty lines', Object.values(cs).concat(Object.values(en)).every((s) => typeof s === 'string' && s.trim().length > 1));
t('no unresolved {placeholders}', !Object.values(cs).concat(Object.values(en)).some((s) => /\{\w+\}/.test(s)));
t('every line ends with punctuation', Object.values(cs).every((s) => /[.!?…]$/.test(s)));
t('no line is longer than 160 characters', Object.values(cs).every((s) => s.length <= 160), Object.entries(cs).filter(([, s]) => s.length > 160).map(([k]) => k).join());
for (const sp of species) {
  for (const s of ['name', 'group', 'where', 'isFishQ', 'isFishA', 'bigger', 'home', 'fact', 'size', 'eats', 'riddle', 'look.0', 'look.1', 'look.2']) {
    t(`sp.${sp.id}.${s} exists`, !!cs[`sp.${sp.id}.${s}`]);
  }
  if (sp.touch && sp.touch !== 'look') t(`sp.${sp.id}.safety exists (touch=${sp.touch})`, !!cs[`sp.${sp.id}.safety`]);
}
for (const z of ['utes', 'chaluhy', 'sire-more', 'hlubiny']) t(`zone ${z}: name + first sentence`, !!cs[`zone.${z}.name`] && !!cs[`zone.${z}.say.0`]);
for (const tr of trash) t(`trash ${tr.id}: turtle sentence`, !!cs[`trash.${tr.id}`]);
for (const m of DEPTH_MARKS) t(`depth ${m} m`, !!cs[`ui.depth.${m}`]);
t('Czech rubbish plural: 1 odpadek / 3 odpadky / 7 odpadků', /jeden odpadek/.test(cs['ui.trashCount.1']) && /3 odpadky/.test(cs['ui.trashCount.3']) && /7 odpadků/.test(cs['ui.trashCount.7']) && trashCountKey(0) === 'say.trashCount0');
t('fish vs not-fish sentences', /je ryba/.test(cs['sp.klaun.group']) && /není ryba, je to savec/.test(cs['sp.delfin.group']) && /Dýchá vzduch/.test(cs['sp.delfin.group']));
if (cs['sp.sardinky.group']) t('plural species speak in plural (Sardinky jsou ryby.)', cs['sp.sardinky.group'] === 'Sardinky jsou ryby.' && /^Jsou /.test(cs['sp.sardinky.isFishQ']));
t('female speakers: feminine past tense (Uklidily, potkaly)', /Uklidily/.test(cs['ui.trashCount.3']) && /potkaly/.test(cs['ui.endFound']));
t('safety lines present (BRIEF §2)', cs['ui.safetyDive'] === 'Pod vodu se potápíme jen s dospělým.' && cs['ui.safetyLook'] === 'Na zvířátka nesaháme, jen se díváme.');
t('the turtle\'s custom name is never part of a spoken line', !Object.values(strings.cs).some((s) => /\{turtle/i.test(s)));
// static scan: literal ids in say([...]) / say('…') across js/
const used = new Set(); const dynamic = [];
const walk = (d) => fs.readdirSync(d, { withFileTypes: true }).flatMap((e) => (e.isDirectory() ? walk(path.join(d, e.name)) : e.name.endsWith('.js') ? [path.join(d, e.name)] : []));
for (const f of walk(path.join(ROOT, 'js'))) {
  const src = fs.readFileSync(f, 'utf8');
  for (const m of src.matchAll(/\bsay\(\s*\[?([^)\]]*)/g)) {
    for (const q of m[1].matchAll(/'((?:ui|sp|zone|trash)\.[^'$]+)'/g)) used.add(q[1]);
    for (const q of m[1].matchAll(/`([^`]+)`/g)) dynamic.push(q[1]);
  }
}
const missing = [...used].filter((id) => !(id in cs));
t(`every literal phrase id used in js/ exists (${used.size} ids)`, !missing.length, missing.join(', '));
const pat = dynamic.map((d) => new RegExp(`^${d.replace(/[.*+?^()|[\]\\]/g, '\\$&').replace(/\$\\\{[^}]+\}/g, '[^]+').replace(/\$\{[^}]+\}/g, '[^]+')}$`));
t(`every templated phrase id pattern matches catalogue ids (${pat.length} patterns)`, pat.every((r) => Object.keys(cs).some((k) => r.test(k))), dynamic.filter((d, i) => !Object.keys(cs).some((k) => pat[i].test(k))).join(' | '));
t('UI_SAY keys all have templates', UI_SAY.every((k) => strings.cs[`say.${k}`] && strings.en[`say.${k}`]));
t('trash count lines up to the max', !!cs[`ui.trashCount.${TRASH_COUNT_MAX}`]);
done('phrases');
