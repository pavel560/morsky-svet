// Writes voice/phrases.json = every spoken line, per language, keyed by stable phrase id.
// Usage: node dev/export_phrases.mjs     (no dependencies; Node 18+)
import { fileURLToPath, pathToFileURL } from 'node:url';
import path from 'node:path';
import fs from 'node:fs';
const ROOT = path.join(path.dirname(fileURLToPath(import.meta.url)), '..');
const { buildCatalogue } = await import(pathToFileURL(path.join(ROOT, 'js', 'phrases.js')).href);
const read = (name) => {
  for (const p of [path.join(ROOT, 'data', `${name}.json`), path.join(ROOT, 'dev', 'placeholders', `${name}.json`)]) {
    if (fs.existsSync(p)) { const j = JSON.parse(fs.readFileSync(p, 'utf8')); return Array.isArray(j) ? j : (j[name] || []); }
  }
  return [];
};
const cat = buildCatalogue(read('species'), { zones: read('zones'), trash: read('trash') });
const sorted = Object.fromEntries(Object.entries(cat).map(([lang, m]) => [lang, Object.fromEntries(Object.keys(m).sort().map((k) => [k, m[k]]))]));
fs.mkdirSync(path.join(ROOT, 'voice'), { recursive: true });
fs.writeFileSync(path.join(ROOT, 'voice', 'phrases.json'), JSON.stringify(sorted, null, 2) + '\n');
console.log(`voice/phrases.json: ${Object.entries(sorted).map(([l, m]) => `${l} ${Object.keys(m).length}`).join(', ')} phrases`);
