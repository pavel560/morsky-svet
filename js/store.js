// Mořský svět — persistent progress (localStorage 'morsky-svet.v1', in-memory fallback). Never throws.
import { STORE_KEY } from './env.js';
import { validateBackup } from './backup.js';

const KEY = STORE_KEY;
const LANGS = ['cs', 'en'];

export const defaults = () => ({
  version: 1,
  lang: 'cs',
  mute: false,            // UI sound effects; speech is separate
  rate: 'normal',         // voice speed: 'normal' | 'slow'
  turtleName: '',         // the child names the guide (written by a parent); empty = „želvička“
  hair: 0,               // index into the --hair-options token list (0 = default brown)
  suit: 0,               // index into the --suit-options token list (0 = default coral)
  skin: 0,               // index into the --skin-options token list (0 = default)
  level: 1,               // 1 „Malá potápěčka“ | 2 „Potápěčka“
  found: {},              // { [speciesId]: ISO date first found }
  trash: 0,               // pieces of rubbish collected, all dives
  dives: 0,
  scene: { night: false, placed: [] },   // Můj kousek moře: placed = [{ id, x, y }] with x, y in 0…1
  seen: {},               // one-off moments: { level2: true, lamp: true }
  firstSeen: null,
  lastSeen: null,
});

let storage = null;
try {
  const probe = '__morsky_probe__';
  window.localStorage.setItem(probe, '1');
  window.localStorage.removeItem(probe);
  storage = window.localStorage;
} catch { storage = null; }
export const persistent = storage !== null;

let state = load();

export function normalize(saved) {
  const s = { ...defaults(), ...(saved && typeof saved === 'object' ? saved : {}) };
  if (!LANGS.includes(s.lang)) s.lang = 'cs';
  s.mute = !!s.mute;
  if (s.rate !== 'slow') s.rate = 'normal';
  s.turtleName = typeof s.turtleName === 'string' ? s.turtleName.slice(0, 24) : '';
  s.hair = Number.isInteger(s.hair) && s.hair >= 0 && s.hair < 12 ? s.hair : 0;
  s.suit = Number.isInteger(s.suit) && s.suit >= 0 && s.suit < 12 ? s.suit : 0;
  s.skin = Number.isInteger(s.skin) && s.skin >= 0 && s.skin < 12 ? s.skin : 0;
  s.level = Number(s.level) === 2 ? 2 : 1;
  if (!s.found || typeof s.found !== 'object' || Array.isArray(s.found)) s.found = {};
  s.trash = Math.max(0, Math.floor(Number(s.trash) || 0));
  s.dives = Math.max(0, Math.floor(Number(s.dives) || 0));
  if (!s.scene || typeof s.scene !== 'object') s.scene = { night: false, placed: [] };
  s.scene = { night: !!s.scene.night, placed: Array.isArray(s.scene.placed) ? s.scene.placed
    .filter((p) => p && typeof p.id === 'string' && Number.isFinite(p.x) && Number.isFinite(p.y))
    .map((p) => ({ id: p.id, x: Math.min(1, Math.max(0, p.x)), y: Math.min(1, Math.max(0, p.y)) })) : [] };
  if (!s.seen || typeof s.seen !== 'object') s.seen = {};
  return s;
}

function load() {
  let saved = null;
  try { saved = storage ? JSON.parse(storage.getItem(KEY) || 'null') : null; } catch { saved = null; }
  const s = normalize(saved);
  const now = new Date().toISOString();
  s.firstSeen ||= now; s.lastSeen = now;
  return s;
}

function save(changedKey) {
  try { storage?.setItem(KEY, JSON.stringify(state)); } catch { /* quota / private mode: keep in memory */ }
  try { window.dispatchEvent(new CustomEvent('store:change', { detail: { key: changedKey } })); } catch { /* ignore */ }
}
const snapshot = () => structuredClone(state);
export function get(key) { return key === undefined ? snapshot() : structuredClone(state[key]); }
export function set(key, value) { state[key] = value; state = normalize(state); save(key); }
export function update(fn) { const d = snapshot(); fn(d); state = normalize(d); save('*'); }

// ---- discoveries
/** @returns {boolean} true when this creature is new */
export function addFound(id) {
  if (state.found[id]) return false;
  state.found[id] = new Date().toISOString(); save('found'); return true;
}
export const isFound = (id) => !!state.found[id];
export const foundIds = () => Object.keys(state.found);
export const foundCount = () => Object.keys(state.found).length;
export function recordDive({ trash = 0 } = {}) { state.dives += 1; state.trash += trash; save('dives'); }

// ---- settings
export const getLang = () => state.lang;
export const setLang = (l) => { if (LANGS.includes(l)) set('lang', l); };
export const isMuted = () => state.mute;
export const setMuted = (m) => set('mute', !!m);
export const getLevel = () => state.level;
export const setLevel = (n) => set('level', n === 2 ? 2 : 1);
export const wasSeen = (k) => !!state.seen[k];
export function markSeen(k) { state.seen = { ...state.seen, [k]: true }; save('seen'); }
export const getScene = () => structuredClone(state.scene);
export function setScene(sc) { state.scene = sc; state = normalize(state); save('scene'); }

// ---- backup / restore (parents' corner)
export function exportText() { return JSON.stringify({ app: 'morsky-svet', v: 1, at: new Date().toISOString(), state: snapshot() }); }
/** @returns {{ok: boolean, reason?: string}} */
export function importText(text) {
  const r = validateBackup(text);
  if (!r.ok) return r;
  state = normalize(r.state); state.lastSeen = new Date().toISOString(); save('*');
  return { ok: true };
}

/** Wipe progress; keep language, voice, sound, look of the diver and the turtle's name. */
export function reset() {
  const keep = { lang: state.lang, mute: state.mute, rate: state.rate, hair: state.hair, suit: state.suit, skin: state.skin, turtleName: state.turtleName };
  state = normalize({ ...defaults(), ...keep, firstSeen: new Date().toISOString(), lastSeen: new Date().toISOString() });
  save('*');
}
