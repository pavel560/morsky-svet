// node tests/voiceurl.test.mjs — content-addressed voice URLs (js/voiceurl.js) and the same rule in sw.js.
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
const ROOT = path.join(path.dirname(fileURLToPath(import.meta.url)), '..');
const { voiceUrl } = await import(pathToFileURL(path.join(ROOT, 'js/voiceurl.js')).href);
let fail = 0; const ok = (n, c, x = '') => { if (!c) { fail++; console.log('FAIL', n, x); } };
const a = { file: 'cs/ui.level.1.mp3', sha1: '0123456789abcdef' };
ok('url carries the first 10 hash chars', voiceUrl(a) === 'voice/cs/ui.level.1.mp3?v=0123456789', voiceUrl(a));
ok('a re-recorded line (new sha1) gets a new URL', voiceUrl({ ...a, sha1: 'fedcba9876543210' }) !== voiceUrl(a));
ok('same take → same URL (stays cacheable)', voiceUrl({ ...a }) === voiceUrl(a));
ok('no sha1 → plain path', voiceUrl({ file: 'cs/x.mp3' }) === 'voice/cs/x.mp3');
ok('bad entry → null', voiceUrl(null) === null && voiceUrl({}) === null);
const sw = fs.readFileSync(path.join(ROOT, 'sw.js'), 'utf8');
ok('sw.js builds the same ?v= (10 chars)', /sha1\.slice\(0, 10\)/.test(sw) && /\?v=\$\{encodeURIComponent/.test(sw));
ok('sw.js matches voices exactly (no ignoreSearch for them)', /cache\.match\(url\.href\)/.test(sw) && /function handleVoice/.test(sw));
console.log(fail ? `${fail} failed` : '7/7 voice-url checks passed');
process.exit(fail ? 1 : 0);
