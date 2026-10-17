// node tests/games.test.mjs — quiz plan + habitat pick (pure parts of js/quiz.js and js/habitat.js), with a tiny DOM shim.
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { t, done } from './_harness.mjs';
globalThis.window = globalThis; globalThis.addEventListener = () => {}; globalThis.dispatchEvent = () => {};
globalThis.document = { addEventListener() {}, hidden: false, documentElement: {} };
globalThis.CustomEvent = class { constructor(n, o) { this.type = n; this.detail = o?.detail; } };
const ROOT = path.join(path.dirname(fileURLToPath(import.meta.url)), '..');
const { plan, ROUNDS } = await import(pathToFileURL(path.join(ROOT, 'js/quiz.js')).href);
const { pickSix } = await import(pathToFileURL(path.join(ROOT, 'js/habitat.js')).href);
const p = path.join(ROOT, 'data/species.json'); const j = JSON.parse(fs.readFileSync(fs.existsSync(p) ? p : path.join(ROOT, 'dev/placeholders/species.json'), 'utf8'));
const species = Array.isArray(j) ? j : j.species;
for (let run = 0; run < 50; run++) {
  for (const lvl of [1, 2]) {
    const q = plan(species.filter((s) => s.level <= lvl), lvl);
    if (q.length !== ROUNDS) { t('5 questions', false); break; }
    for (const x of q) {
      if (['name', 'riddle'].includes(x.type) && (x.options.length !== 3 || !x.options.some((o) => o.id === x.target.id) || new Set(x.options.map((o) => o.id)).size !== 3)) t(`${x.type}: 3 distinct options incl. the answer`, false);
      if (x.type === 'bigger' && !(x.options.length === 2 && x.options.every((o) => o.sizeCm <= x.target.sizeCm) && x.options.some((o) => o.id === x.target.id))) t('bigger: target is the bigger of 2', false);
      if (lvl === 1 && ['isFish', 'bigger'].includes(x.type)) t('level 1 has no isFish/bigger', false);
    }
  }
}
t('quiz plans: 100 random plans valid', true);
const types2 = new Set(Array.from({ length: 20 }, () => plan(species, 2).map((x) => x.type)).flat());
t('level 2 uses all four question types', ['name', 'riddle', 'isFish', 'bigger'].every((k) => types2.has(k)), [...types2].join());
for (let run = 0; run < 30; run++) {
  const six = pickSix(species);
  if (six.length !== 6 || new Set(six.map((s) => s.id)).size !== 6 || new Set(six.map((s) => s.zone)).size !== 4) { t('habitat: 6 distinct animals covering all 4 floors', false, six.map((s) => s.id).join()); break; }
}
t('habitat picks: 30 random picks valid', true);
done('games');
