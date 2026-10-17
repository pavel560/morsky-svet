// Mořský svět — shared helpers: DOM, icons, tokens, speech sequencing + caption, names.
import * as speech from './speech.js';
import * as store from './store.js';
import { getLang, t } from './i18n.js';
import { shortName } from './phrases.js';

export const $ = (s, r = document) => r.querySelector(s);
export const $$ = (s, r = document) => [...r.querySelectorAll(s)];
export function h(html) { const tp = document.createElement('template'); tp.innerHTML = html.trim(); return tp.content.firstElementChild; }
export const esc = (s) => String(s ?? '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
/** Sprite icon from art/ui-icons.svg (symbol id `i-<name>`). */
export const icon = (n, cls = '') => `<svg class="icon ${cls}" aria-hidden="true" focusable="false"><use href="#i-${n}"/></svg>`;
export const reduced = () => matchMedia('(prefers-reduced-motion: reduce)').matches;
export const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
export const cssVar = (token, el = document.documentElement) => getComputedStyle(el).getPropertyValue(token).trim();
/** A duration token in ms ('320ms' | '1.2s'). */
export function ms(token, fallback = 300) {
  const v = cssVar(token); const n = parseFloat(v);
  if (Number.isNaN(n)) return fallback;
  return v.endsWith('ms') ? n : v.endsWith('s') ? n * 1000 : n;
}
export const num = (token, fallback = 0) => { const n = parseFloat(cssVar(token)); return Number.isNaN(n) ? fallback : n; };
/** Resolve any CSS length expression (e.g. var(--diver-h)) to px by measuring a probe. */
export function measure(prop, value) {
  const p = document.createElement('div');
  p.style.cssText = `position:absolute;visibility:hidden;${prop}:${value}`;
  document.body.append(p); const v = prop === 'width' ? p.offsetWidth : p.offsetHeight; p.remove(); return v;
}
/** '#rrggbb' or 'rgb(r g b / a)' → [r, g, b, a] */
export function parseColor(c) {
  const s = String(c || '').trim();
  let m = /^#([0-9a-f]{6})$/i.exec(s);
  if (m) { const n = parseInt(m[1], 16); return [(n >> 16) & 255, (n >> 8) & 255, n & 255, 1]; }
  m = /^rgba?\(\s*([\d.]+)[\s,]+([\d.]+)[\s,]+([\d.]+)(?:\s*[/,]\s*([\d.]+%?))?\s*\)$/i.exec(s);
  if (m) { let a = m[4] === undefined ? 1 : parseFloat(m[4]); if (String(m[4]).endsWith('%')) a /= 100; return [+m[1], +m[2], +m[3], a]; }
  return [0, 0, 0, 1];
}
export const rgba = ([r, g, b, a = 1]) => `rgb(${r | 0} ${g | 0} ${b | 0} / ${(+a).toFixed(3)})`;
export const mix = (a, b, f) => a.map((v, i) => v + (b[i] - v) * f);

export function shuffle(a) { const r = [...a]; for (let i = r.length - 1; i > 0; i--) { const j = Math.floor(Math.random() * (i + 1)); [r[i], r[j]] = [r[j], r[i]]; } return r; }
export function anim(el, keyframes, opts) {
  if (!el?.animate) return Promise.resolve();
  const a = el.animate(keyframes, opts);
  return a.finished.then(() => a, () => a);
}
export async function viewTransition(update) {
  if (!document.startViewTransition || reduced()) { await update(); return; }
  const tr = document.startViewTransition(update);
  tr.ready.catch(() => {});
  await tr.finished.catch(() => {});
}

// ---- names
export function nameOf(sp, lang = getLang()) { return sp?.name?.[lang] ?? sp?.name?.cs ?? sp?.id ?? ''; }
export const shortOf = (sp, lang = getLang()) => shortName(sp, lang);
export const turtleName = () => store.get('turtleName') || t('turtle.default');

// ---- speech: catalogue phrase ids only; one line at a time; a new say() cancels the previous one
const REC_RATE = { cs: { normal: 0.9, slow: 0.78 }, en: { normal: 1, slow: 0.85 } };
const slow = () => store.get('rate') === 'slow';
export const recRate = (lang) => (REC_RATE[lang] ?? REC_RATE.en)[slow() ? 'slow' : 'normal'];
let lastIds = null;
export function say(ids, lang = getLang()) {
  lastIds = [].concat(ids).filter(Boolean);
  return speech.sayAll(lastIds, lang, { rate: recRate(lang), ttsRate: slow() ? 0.72 : 0.85 });
}
/** The permanent „zopakuj“ button. */
export function replay() { if (lastIds?.length) return say(lastIds); return Promise.resolve(false); }
export function hush() { speech.stopAll(); }
export const phraseText = (id, lang = getLang()) => speech.phraseText(id, lang);

/** Visible caption for every spoken line (BRIEF §2: voice + short visible label), bottom-centre, never over the task. */
export function mountCaption() {
  const el = h(`<div id="caption" role="status" aria-live="polite"><span class="cap-who"></span><span class="cap-text"></span></div>`);
  document.body.append(el);
  let tm = 0;
  addEventListener('speech:say', (e) => {
    el.querySelector('.cap-who').textContent = turtleName();
    el.querySelector('.cap-text').textContent = e.detail.text;
    el.classList.add('show');
    clearTimeout(tm);
    tm = setTimeout(() => el.classList.remove('show'), 2400 + e.detail.text.length * 65);
  });
  return el;
}
