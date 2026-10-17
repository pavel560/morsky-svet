// node tests/sw.test.mjs — sw.js precache list matches the tree: every CORE file exists; every app module, scene/ponor
// art file and font is precached (species art comes from data/species.json at run time, so it is not listed).
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { t, done } from './_harness.mjs';
const ROOT = path.join(path.dirname(fileURLToPath(import.meta.url)), '..');
const sw = fs.readFileSync(path.join(ROOT, 'sw.js'), 'utf8');
const core = [...sw.match(/const CORE = \[([\s\S]*?)\];/)[1].matchAll(/'\.\/([^']*)'/g)].map((m) => m[1]).filter(Boolean);
const missing = core.filter((p) => !fs.existsSync(path.join(ROOT, p)));
t('every CORE file exists', !missing.length, missing.join(', '));
const sp = JSON.parse(fs.readFileSync(path.join(ROOT, 'data/species.json'), 'utf8'));
const ids = new Set((Array.isArray(sp) ? sp : sp.species).map((s) => s.id));
const list = (d, re) => fs.readdirSync(path.join(ROOT, d)).filter((f) => re.test(f)).map((f) => `${d}/${f}`);
const want = [...list('js', /\.js$/), ...list('js/dive', /\.js$/), ...list('art', /\.svg$/).filter((f) => !ids.has(path.basename(f, '.svg'))),
  ...list('art/ponor', /\.svg$/), ...[...fs.readFileSync(path.join(ROOT, 'css/fonts.css'), 'utf8').matchAll(/fonts\/[\w.-]+\.woff2/g)].map((m) => m[0])];
const notCached = [...new Set(want)].filter((p) => !core.includes(p));
t(`every module, scene/ponor art and font is precached (${want.length})`, !notCached.length, notCached.join(', '));
t('species art fetched from data at run time', /art\/\$\{id\}\.svg/.test(sw));
t('VERSION is set', /const VERSION = 'v\d+'/.test(sw));
done('sw');
