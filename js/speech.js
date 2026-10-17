// Mořský svět — Web Speech wrapper: speak(text, 'cs' | 'en'), best-voice selection, iOS gesture unlock.
//
// iOS/iPadOS: the first speak() must happen inside a user gesture. This module primes speech on the
// first pointerup/touchend/click/keydown automatically; after that, speak() works from timers too.
import { voiceUrl } from './voiceurl.js';

const LANG_TAG = { cs: 'cs-CZ', en: 'en-GB' };

// Preferred voices, best first (substring match on voice.name, case-insensitive).
const PREFERRED = {
  'cs-CZ': ['zuzana', 'iveta', 'vlasta', 'antonín', 'antonin', 'jakub', 'google čeština', 'google cestina'],
  'en-GB': ['serena', 'daniel', 'kate', 'stephanie', 'martha', 'arthur', 'oliver', 'libby', 'sonia', 'ryan', 'maisie', 'hazel', 'susan', 'george', 'google uk english female', 'google uk english male'],
};
// Novelty / robotic macOS voices we never want for a child.
const NOVELTY = /\b(albert|bad news|bahh|bells|boing|bubbles|cellos|good news|jester|organ|superstar|trinoids|whisper|wobble|zarvox|junior|ralph|fred|kathy|grandma|grandpa|rocko|shelley|eddy|flo|reed|sandy)\b/i;

const DEFAULT_RATE = 0.85;   // a little slower for a 5-year-old
const DEFAULT_PITCH = 1.05;

const synth = typeof window !== 'undefined' ? window.speechSynthesis : undefined;
let voices = [];
const chosen = new Map();     // 'cs-CZ' → SpeechSynthesisVoice | null
const live = new Set();       // keep utterances referenced (Chrome GC bug drops onend)
let primed = false;
let fallbackHandler = defaultFallback;

const norm = (s) => String(s || '').replace('_', '-').toLowerCase();
const tagFor = (lang) => LANG_TAG[lang] || lang || 'cs-CZ';

/** true when the browser has a Web Speech implementation at all */
export const isSupported = () => !!synth && typeof window.SpeechSynthesisUtterance === 'function';

function refreshVoices() {
  if (!isSupported()) return [];
  const list = synth.getVoices() || [];
  if (list.length) { voices = list; chosen.clear(); }
  return voices;
}

/** Resolves once the voice list is known (or after ~3 s with whatever we have — Safari may never fire voiceschanged). */
export const voicesReady = new Promise((resolve) => {
  if (!isSupported()) return resolve([]);
  if (refreshVoices().length) return resolve(voices);
  let done = false;
  const finish = () => { if (!done) { done = true; resolve(refreshVoices()); } };
  synth.addEventListener?.('voiceschanged', () => { refreshVoices(); if (voices.length) finish(); });
  let tries = 0;
  const poll = setInterval(() => {
    if (refreshVoices().length || ++tries > 12) { clearInterval(poll); finish(); }
  }, 250);
});
if (isSupported()) synth.addEventListener?.('voiceschanged', refreshVoices);

function score(v, tag) {
  const lang = norm(v.lang);
  const name = norm(v.name);
  const uri = norm(v.voiceURI);
  let s = 0;
  if (lang === norm(tag)) s += 100;
  else if (lang.startsWith(tag.slice(0, 2).toLowerCase())) s += (tag === 'en-GB' && /en-(ie|au|nz)/.test(lang)) ? 60 : 40;
  else return -1;
  if (NOVELTY.test(v.name)) return -1;
  const pref = PREFERRED[tag] || [];
  const i = pref.findIndex((p) => name.includes(p));
  if (i >= 0) s += 50 - i;
  if (/premium|enhanced|neural|natural|siri/.test(name + ' ' + uri)) s += 30;
  if (/compact|eloquence/.test(uri)) s -= 15;
  if (v.localService) s += 5;          // works offline
  if (v.default) s += 1;
  return s;
}

/** Best voice for 'cs' | 'en' (or a BCP-47 tag), or null if none. Czech never falls back to a foreign voice. */
export function getVoice(lang) {
  const tag = tagFor(lang);
  if (chosen.has(tag)) return chosen.get(tag);
  refreshVoices();
  let best = null; let bestScore = -1;
  for (const v of voices) {
    const sc = score(v, tag);
    if (sc > bestScore) { best = v; bestScore = sc; }
  }
  if (voices.length) chosen.set(tag, best);
  return best;
}

export const hasVoice = (lang) => !!getVoice(lang);
export const listVoices = (lang) => refreshVoices().filter((v) => !lang || norm(v.lang).startsWith(tagFor(lang).slice(0, 2).toLowerCase()));

/** Stop whatever is being said. */
export function cancel() {
  if (!isSupported()) return;
  try { synth.cancel(); } catch { /* ignore */ }
}

/** Unlock speech on iOS: call inside a user gesture (done automatically on the first tap). */
export function prime(force = false) {
  if ((primed && !force) || !isSupported()) return;
  try {
    const u = new SpeechSynthesisUtterance(' ');
    u.volume = 0;
    // primed only once the engine actually started/finished it (iOS may silently block it outside a gesture)
    u.onstart = () => { primed = true; };
    u.onend = () => { primed = true; };
    synth.speak(u);
  } catch { /* ignore */ }
}

/**
 * Say text aloud. Cancels the previous utterance.
 * @param {string} text
 * @param {'cs'|'en'|string} [lang='cs']
 * @param {{rate?:number, pitch?:number, volume?:number, onstart?:Function, onend?:Function, fallback?:boolean}} [opts]
 * @returns {Promise<boolean>} resolves true when finished speaking, false if it could not speak
 */
export function speak(text, lang = 'cs', opts = {}) {
  const tag = tagFor(lang);
  if (!text) return Promise.resolve(false);
  if (!isSupported()) { notifyUnavailable(text, tag, 'unsupported', opts); return Promise.resolve(false); }
  const voice = getVoice(tag);
  if (!voice && voices.length) { notifyUnavailable(text, tag, 'no-voice', opts); return Promise.resolve(false); }

  cancel();
  primed = true;
  return new Promise((resolve) => {
    const u = new SpeechSynthesisUtterance(text);
    u.lang = voice?.lang || tag;   // voice list may still be empty on very first call; the browser picks by lang
    if (voice) u.voice = voice;
    u.rate = opts.rate ?? DEFAULT_RATE;
    u.pitch = opts.pitch ?? DEFAULT_PITCH;
    u.volume = opts.volume ?? 1;
    let settled = false;
    const done = (ok) => {
      if (settled) return;
      settled = true; live.delete(u); clearTimeout(watchdog);
      window.dispatchEvent(new CustomEvent('speech:end', { detail: { text, lang: tag, ok } }));
      opts.onend?.(ok);
      resolve(ok);
    };
    u.onstart = () => {
      window.dispatchEvent(new CustomEvent('speech:start', { detail: { text, lang: tag } }));
      opts.onstart?.();
    };
    u.onend = () => done(true);
    u.onerror = (e) => {
      // 'interrupted'/'canceled' = we cancelled it for the next phrase: not a failure worth showing.
      if (e.error !== 'interrupted' && e.error !== 'canceled') notifyUnavailable(text, tag, e.error || 'error', opts);
      done(false);
    };
    // Some engines never fire onend; never leave a caller hanging.
    const watchdog = setTimeout(() => done(true), 2000 + text.length * 150);
    live.add(u);
    try {
      if (synth.paused) synth.resume();
      synth.speak(u);
    } catch (err) {
      notifyUnavailable(text, tag, 'error', opts);
      done(false);
    }
  });
}

export const isSpeaking = () => !!(isSupported() && (synth.speaking || synth.pending));

/**
 * Replace the visible fallback (default: small bubble with the text). Phase B can route it into the UI.
 * handler({text, lang, reason})
 */
export function setFallbackHandler(fn) { fallbackHandler = typeof fn === 'function' ? fn : () => {}; }

function notifyUnavailable(text, lang, reason, opts) {
  const detail = { text, lang, reason };
  window.dispatchEvent(new CustomEvent('speech:unavailable', { detail }));
  if (opts.fallback !== false) {
    try { fallbackHandler(detail); } catch { /* ignore */ }
  }
}

function defaultFallback({ text }) {
  if (typeof document === 'undefined' || !document.body) return;
  let el = document.getElementById('speech-fallback');
  if (!el) {
    el = document.createElement('div');
    el.id = 'speech-fallback';
    el.setAttribute('role', 'status');
    el.setAttribute('aria-live', 'polite');
    Object.assign(el.style, {
      position: 'fixed', left: '50%', bottom: '24px', transform: 'translateX(-50%)', zIndex: '9998',
      maxWidth: 'min(90vw, 640px)', padding: '14px 22px', borderRadius: '24px',
      background: 'rgba(255,255,255,.96)', color: '#2b2118', boxShadow: '0 6px 24px rgba(0,0,0,.18)',
      font: '600 clamp(18px, 2.4vw, 28px)/1.3 "Nunito", system-ui, sans-serif', textAlign: 'center',
      transition: 'opacity .3s', pointerEvents: 'none',
    });
    document.body.append(el);
  }
  el.textContent = '\u{1F508} ' + text;
  el.style.opacity = '1';
  clearTimeout(el._t);
  el._t = setTimeout(() => { el.style.opacity = '0'; }, 2500 + text.length * 60);
}

// Auto-prime on the first real user activation (pointerdown does not count for touch on iOS).
if (typeof window !== 'undefined' && isSupported()) {
  const events = ['pointerup', 'touchend', 'click', 'keydown'];
  const onGesture = () => { prime(); if (primed) events.forEach((ev) => window.removeEventListener(ev, onGesture, true)); };
  events.forEach((ev) => window.addEventListener(ev, onGesture, { capture: true, passive: true }));
  // Chrome stops queued speech when a tab is hidden; never resume stale phrases.
  document.addEventListener('visibilitychange', () => { if (document.hidden) cancel(); });
}


// ======================================================================= pre-recorded voice
// Every line the game says is a catalogue phrase (js/phrases.js). If voice/<lang>/<id>.mp3 exists for the
// CURRENT text (voice/index.json, written by make_voice.py), it plays through one reused <audio>; otherwise
// the same text goes to Web Speech above. Events: 'speech:say' {ids, lang, text} once per call,
// 'speech:file' {id, lang, ok, rate} per recording played.
let catalogue = {}; let voiceIndex = {};
let audio = null; let playToken = 0; let endCurrent = null; let silent = null;

export function setVoice({ catalogue: c, index } = {}) { catalogue = c || {}; voiceIndex = index || {}; }
export const phraseText = (id, lang) => catalogue[lang]?.[id] ?? null;
export function hasRecording(id, lang) {
  const e = voiceIndex[lang]?.[id];
  return !!(e && typeof e.file === 'string' && e.text === phraseText(id, lang));
}
function audioEl() {
  if (!audio && typeof Audio !== 'undefined') { audio = new Audio(); audio.preload = 'auto'; }
  return audio;
}
function silentWav() {      // 0.1 s of silence, built in memory (no file needed)
  if (silent) return silent;
  const n = 800; const b = new Uint8Array(44 + n); const v = new DataView(b.buffer);
  const w = (o, str) => { for (let i = 0; i < str.length; i++) b[o + i] = str.charCodeAt(i); };
  w(0, 'RIFF'); v.setUint32(4, 36 + n, true); w(8, 'WAVE'); w(12, 'fmt '); v.setUint32(16, 16, true); v.setUint16(20, 1, true); v.setUint16(22, 1, true);
  v.setUint32(24, 8000, true); v.setUint32(28, 8000, true); v.setUint16(32, 1, true); v.setUint16(34, 8, true); w(36, 'data'); v.setUint32(40, n, true); b.fill(128, 44);
  let bin = ''; b.forEach((x) => { bin += String.fromCharCode(x); });
  silent = `data:audio/wav;base64,${btoa(bin)}`;
  return silent;
}
/** Call inside the Play tap: iOS lets an <audio> element play later only if it first played in a gesture. */
export function unlockAudio() {
  const a = audioEl(); if (!a) return;
  try { a.src = silentWav(); const p = a.play(); if (p) p.catch(() => {}); } catch { /* ignore */ }
}
function playFile(url, rate) {
  const a = audioEl();
  if (!a) return Promise.resolve(null);
  return new Promise((resolve) => {
    let settled = false;
    const fin = (ok) => { if (settled) return; settled = true; clearTimeout(wd); a.onended = null; a.onerror = null; endCurrent = null; resolve(ok); };
    const wd = setTimeout(() => fin(true), 20000);
    endCurrent = () => fin(false);
    a.onended = () => fin(true);
    a.onerror = () => fin(null);                       // null = could not play → Web Speech fallback
    try {
      a.src = url;
      a.defaultPlaybackRate = rate; a.playbackRate = rate;
      a.preservesPitch = true; a.webkitPreservesPitch = true;   // slower, not deeper
      const p = a.play();
      if (p) p.catch(() => fin(null));
    } catch { fin(null); }
  });
}
/** Stop the current line (recording or Web Speech). */
export function stopAll() {
  playToken++;
  try { audio?.pause(); } catch { /* ignore */ }
  endCurrent?.();
  cancel();
}
/**
 * Say catalogue phrases in sequence; a new call cancels the previous one.
 * @param {string|string[]} ids  phrase ids (unknown ids are skipped)
 * @param {'cs'|'en'} lang
 * @param {{rate?: number, ttsRate?: number}} opts  rate = playbackRate for recordings, ttsRate for Web Speech
 * @returns {Promise<boolean>} true when everything was said
 */
export async function sayAll(ids, lang = 'cs', { rate = 1, ttsRate } = {}) {
  const list = [].concat(ids).filter((id) => phraseText(id, lang));
  stopAll();
  const my = playToken;
  if (!list.length) return false;
  if (typeof window !== 'undefined') window.dispatchEvent(new CustomEvent('speech:say', { detail: { ids: list, lang, text: list.map((id) => phraseText(id, lang)).join(' ') } }));
  for (const id of list) {
    if (my !== playToken) return false;
    let ok = null;
    if (hasRecording(id, lang)) {
      ok = await playFile(voiceUrl(voiceIndex[lang][id]), rate);
      if (typeof window !== 'undefined') window.dispatchEvent(new CustomEvent('speech:file', { detail: { id, lang, ok, rate } }));
    }
    if (my !== playToken) return false;
    if (ok === null) ok = await speak(phraseText(id, lang), lang, ttsRate ? { rate: ttsRate } : {});
    if (!ok || my !== playToken) return false;
  }
  return true;
}
export const say = (id, lang, opts) => sayAll([id], lang, opts);
