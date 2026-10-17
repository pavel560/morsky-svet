// node tests/backup.test.mjs — parents' backup / restore validation (js/backup.js).
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { t, done } from './_harness.mjs';
const ROOT = path.join(path.dirname(fileURLToPath(import.meta.url)), '..');
const { validateBackup } = await import(pathToFileURL(path.join(ROOT, 'js/backup.js')).href);
const env = JSON.stringify({ app: 'morsky-svet', v: 1, state: { found: { klaun: '2026-10-17T10:00:00Z' }, level: 2 } });
t('accepts the export envelope', validateBackup(env).ok && validateBackup(env).state.found.klaun);
t('accepts a bare state', validateBackup(JSON.stringify({ found: { krab: 'x' } })).ok);
t('rejects empty', validateBackup('').reason === 'empty');
t('rejects non-JSON', validateBackup('hello').reason === 'not-json');
t('rejects another app\'s backup', validateBackup(JSON.stringify({ app: 'houbicky', state: {} })).reason === 'other-app');
t('rejects arrays', validateBackup('[1,2]').reason === 'shape');
t('rejects found as array', validateBackup(JSON.stringify({ found: ['klaun'] })).reason === 'shape');
t('drops unsafe species keys', !('<img>' in validateBackup(JSON.stringify({ found: { '<img>': 'x', klaun: 'y' } })).state.found));
t('rejects huge input', validateBackup('x'.repeat(300000)).reason === 'too-big');
done('backup');
