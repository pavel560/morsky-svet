// node tests/sw_stale.test.mjs [path/to/sw.js] — the service worker never caches a stale CDN copy.
// Simulates GitHub Pages' CDN right after a deploy: a plain URL returns the PREVIOUS file (the CDN's cached copy),
// a URL with a query the CDN has never seen returns the fresh file from the origin. sw.js runs in a vm sandbox with
// fake caches; after install every precached file, a cache-first hit and a network-first JSON must be the fresh copy.
import fs from 'node:fs';
import path from 'node:path';
import vm from 'node:vm';
import { fileURLToPath } from 'node:url';
import { t, done } from './_harness.mjs';
const ROOT = path.join(path.dirname(fileURLToPath(import.meta.url)), '..');
const SW = process.argv[2] || path.join(ROOT, 'sw.js');
const SCOPE = 'https://example.test/morsky-svet/';
const src = fs.readFileSync(SW, 'utf8');
const core = [...src.match(/const CORE = \[([\s\S]*?)\];/)[1].matchAll(/'\.\/([^']*)'/g)].map((m) => m[1]);

const fetched = [];
const body = (url, fresh) => (url.pathname.endsWith('species.json') ? JSON.stringify(fresh ? [{ id: 'klaun' }] : [{ id: 'old' }])
  : url.pathname.endsWith('.json') ? JSON.stringify({ fresh }) : `/* ${fresh ? 'FRESH' : 'STALE'} ${url.pathname} */`);
async function cdnFetch(input) {
  const url = new URL(typeof input === 'string' ? input : input.url, SCOPE);
  fetched.push(url.href);
  const fresh = url.search !== '';                         // a query string = a new CDN key → the origin answers
  return new Response(body(url, fresh), { status: 200, headers: { 'content-type': url.pathname.endsWith('.json') ? 'application/json' : 'text/plain' } });
}
class FakeCache {
  constructor() { this.m = new Map(); }
  k(r) { return new URL(typeof r === 'string' ? r : r.url, SCOPE).href; }
  async match(r, o = {}) {
    const k = this.k(r); if (this.m.has(k)) return this.m.get(k).clone();
    if (o.ignoreSearch) { const b = k.split('?')[0]; for (const [kk, v] of this.m) if (kk.split('?')[0] === b) return v.clone(); }
    return undefined;
  }
  async put(r, res) { this.m.set(this.k(r), res.clone()); }
  async add(r) { await this.put(r, await cdnFetch(r)); }
  async addAll(list) { for (const r of list) await this.add(r); }
  async keys() { return [...this.m.keys()].map((url) => ({ url })); }
  async delete(r) { return this.m.delete(this.k(r)); }
}
const stores = new Map();
const caches = { async open(n) { if (!stores.has(n)) stores.set(n, new FakeCache()); return stores.get(n); }, async keys() { return [...stores.keys()]; }, async delete(n) { return stores.delete(n); } };
const handlers = {};
class SwRequest extends Request { constructor(u, init) { super(typeof u === 'string' ? new URL(u, SCOPE).href : u, init); } }
const self = { registration: { scope: SCOPE }, location: new URL('sw.js', SCOPE), addEventListener: (ty, f) => { handlers[ty] = f; },
  skipWaiting: async () => {}, clients: { claim: async () => {} } };
const ctx = vm.createContext({ self, caches, fetch: cdnFetch, Request: SwRequest, Response, Headers, URL, URLSearchParams, Blob, console, setTimeout, clearTimeout, Promise, encodeURIComponent });
vm.runInContext(src, ctx);

const waits = [];
const ev = (extra = {}) => ({ waitUntil: (p) => waits.push(p), ...extra });
const settle = async () => { while (waits.length) await waits.shift(); };
handlers.install(ev()); await settle();
const cache = [...stores.values()][0];
const text = async (u) => (await cache.match(new URL(u, SCOPE).href))?.text();
let stale = [];
for (const u of core) { const b = await text(u); if (b === undefined || /STALE|"old"|"fresh":false/.test(b)) stale.push(u || './'); }
t(`install: every precached CORE file (${core.length}) is the fresh copy, none from the CDN's stale cache`, stale.length === 0, stale.slice(0, 5).join(', '));
t('install: cache keys are plain URLs (no cache-busting query stored)', !(await cache.keys()).some((r) => /__v=/.test(r.url)));

async function request(rel, init = {}) {
  let resp = null;
  const req = init.navigate ? { url: new URL(rel, SCOPE).href, method: 'GET', mode: 'navigate', headers: new Headers() } : new Request(new URL(rel, SCOPE).href);
  handlers.fetch(ev({ request: req, respondWith: (p) => { resp = p; } }));
  const r = await resp; await settle(); return r;
}
const app = await (await request('js/app.js')).text();
t('cache-first: js/app.js is served fresh', /FRESH/.test(app), app.slice(0, 60));
t('cache-first: no background refresh overwrites it with the stale CDN copy', /FRESH/.test(await text('js/app.js')));
const nav = await (await request('?autostart', { navigate: true })).text();
t('navigation (with ?autostart) gets the fresh index.html', /FRESH/.test(nav), nav.slice(0, 60));
const sp = await (await request('data/species.json')).json();
t('network-first JSON (data, voice index) is fresh even while the CDN is stale', sp[0]?.id === 'klaun', JSON.stringify(sp));
t('…and the cache keeps it under the plain key', JSON.parse(await text('data/species.json'))[0].id === 'klaun');
t('every network fetch for app files used a cache-busting query', fetched.filter((u) => !u.includes('/voice/')).every((u) => new URL(u).search !== ''),
  fetched.filter((u) => new URL(u).search === '').slice(0, 3).join(', '));
done('sw-stale-cdn');
