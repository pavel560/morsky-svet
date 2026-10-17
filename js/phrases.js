// Mořský svět — the finite catalogue of EVERY spoken line (BRIEF §2). Ids are stable; texts come from the
// templates in i18n.js and the data files, composed here ONCE (never while playing), so every line can be recorded.
// Used by the app (speech.sayAll) and by dev/export_phrases.mjs → voice/phrases.json → make_voice.py → voice/<lang>/<id>.mp3
import { strings } from './i18n.js';
import { groupKey, DEPTH_MARKS } from './dive/world.js';

export const SPOKEN_LANGS = ['cs', 'en'];
export const TRASH_COUNT_MAX = 10;
// UI lines spoken as-is: phrase id `ui.<suffix>` ← template key `say.<suffix>`
export const UI_SAY = ['greet', 'safetyDive', 'safetyLook', 'diveIntro', 'deeper', 'findMore', 'darker', 'lamp', 'deepDone', 'surface',
  'endFound', 'endNone', 'release', 'trashTake', 'seaIntro', 'seaEmpty', 'seaUnknown', 'seaNight', 'seaDay', 'quizIntro', 'quizTry',
  'quizShow', 'quizRight0', 'quizRight1', 'quizRight2', 'quizBigger', 'quizDone', 'habitatIntro', 'habitatWrong', 'habitatDone',
  'level2', 'tired', 'parentsHold', 'photoMissing', 'no', 'langHello', 'rotatePhone', 'rotateTablet'];

/** Species named in the plural (a school): their sentences take plural grammar. `plural: true` in data also works. */
export const PLURAL_IDS = new Set(['sardinky']);
const isPlural = (sp) => sp.plural === true || PLURAL_IDS.has(sp.id);
const PL = {
  cs: { ryba: '{N} jsou ryby.', where: 'Kde jsou {n}?', isFishQ: 'Jsou {n} ryby?', isFishYes: 'Ano! {N} jsou ryby.', bigger: '{N} jsou větší.', home: '{N} bydlí {zin}.' },
  en: { ryba: 'The {n} are fish.', where: 'Where are the {n}?', isFishQ: 'Are the {n} fish?', isFishYes: 'Yes! The {n} are fish.', bigger: 'The {n} are bigger.', home: 'The {n} live {zin}.' },
};
const fill = (s, vars) => s.replace(/\{(\w+)\}/g, (m, k) => (k in vars ? String(vars[k]) : m));
const cap = (s) => (s ? s.charAt(0).toLocaleUpperCase() + s.slice(1) : s);
const text = (v, lang) => (v && typeof v === 'object' ? (v[lang] ?? '') : (typeof v === 'string' && lang === 'cs' ? v : ''));
/** In-sentence short name: species.short, else the full name with a lower-case first letter. */
export function shortName(sp, lang) {
  const s = text(sp.short, lang) || text(sp.name, lang) || sp.id;
  return lang === 'en' ? s.toLowerCase() : s.charAt(0).toLocaleLowerCase('cs') + s.slice(1);
}
/** Czech plural for the rubbish count. */
export function trashCountKey(n) { return n === 0 ? 'say.trashCount0' : n === 1 ? 'say.trashCount1' : n <= 4 ? 'say.trashCountFew' : 'say.trashCountMany'; }
/** Two zone sentences from data/zones.json, whatever the field is called (say / sentences / light+temp …). */
export function zoneSentences(z, lang) {
  if (!z) return [];
  for (const k of ['say', 'sentences', 'lines', 'facts']) if (Array.isArray(z[k])) return z[k].map((v) => text(v, lang)).filter(Boolean);
  const out = [];
  for (const [k, v] of Object.entries(z)) {
    if (['id', 'name', 'short', 'sources', 'depthM', 'depth', 'range'].includes(k)) continue;
    const s = text(v, lang); if (s) out.push(s);
  }
  return out;
}
/** The turtle's sentence for a rubbish item (field name tolerant). */
export function trashSentence(tr, lang) {
  for (const k of ['turtle', 'say', 'sentence', 'line', 'fact', 'text']) { const s = text(tr?.[k], lang); if (s) return s; }
  return '';
}
const sentence = (s) => { const x = String(s || '').trim(); return !x ? '' : /[.!?…]$/.test(x) ? x : `${x}.`; };

/** { cs: { phraseId: text }, en: {...} } */
export function buildCatalogue(species, { zones = [], trash = [] } = {}) {
  const cat = {};
  for (const lang of SPOKEN_LANGS) {
    const S = strings[lang]; const c = (cat[lang] = {});
    for (const k of UI_SAY) c[`ui.${k}`] = S[`say.${k}`];
    for (const m of DEPTH_MARKS) c[`ui.depth.${m}`] = fill(S['say.depth'], { m });
    for (let n = 0; n <= TRASH_COUNT_MAX; n++) c[`ui.trashCount.${n}`] = fill(S[trashCountKey(n)], { n });
    for (const z of ['utes', 'chaluhy', 'sire-more', 'hlubiny']) {
      const zd = zones.find((x) => x.id === z);
      c[`zone.${z}.name`] = sentence(text(zd?.name, lang) || S[`zone.${z}`]);
      zoneSentences(zd, lang).slice(0, 2).forEach((s, i) => { c[`zone.${z}.say.${i}`] = sentence(s); });
    }
    for (const tr of trash) {
      const s = trashSentence(tr, lang); if (s) c[`trash.${tr.id}`] = sentence(s);
      const nm = text(tr.name, lang); if (nm) c[`trash.${tr.id}.name`] = sentence(cap(nm));
    }
    for (const sp of species) {
      const p = `sp.${sp.id}.`; const n = shortName(sp, lang); const N = cap(n);
      const g = groupKey(sp.group);
      c[`${p}name`] = sentence(cap(text(sp.name, lang) || sp.id));
      const pl = isPlural(sp) ? PL[lang] : null;
      c[`${p}group`] = fill(pl && g === 'ryba' ? pl.ryba : S[`group.say.${g}`], { n, N });
      if (text(sp.sizeSay, lang)) c[`${p}size`] = sentence(text(sp.sizeSay, lang));
      if (text(sp.eatsSay, lang)) c[`${p}eats`] = sentence(text(sp.eatsSay, lang));
      if (text(sp.fact, lang)) c[`${p}fact`] = sentence(text(sp.fact, lang));
      if (sp.touch && sp.touch !== 'look' && text(sp.safety, lang)) c[`${p}safety`] = sentence(text(sp.safety, lang));
      if (text(sp.riddle, lang)) c[`${p}riddle`] = sentence(text(sp.riddle, lang));
      (sp.lookFor || []).forEach((lf, i) => { const s = text(lf, lang); if (s) c[`${p}look.${i}`] = sentence(cap(s)); });
      const T = (k) => (pl ? pl[k] : S[`say.sp.${k}`]);
      c[`${p}where`] = fill(T('where'), { n, N });
      c[`${p}isFishQ`] = fill(T('isFishQ'), { n, N });
      c[`${p}isFishA`] = g === 'ryba' ? fill(T('isFishYes'), { n, N }) : `${S['say.no']} ${c[`${p}group`]}`;
      c[`${p}bigger`] = fill(T('bigger'), { n, N });
      if (sp.zone) c[`${p}home`] = fill(T('home'), { n, N, zin: S[`zoneIn.${sp.zone}`] || '' });
    }
  }
  return cat;
}

/** Lines spoken when a card opens (the name was already said on the tap when skipName). */
export function cardIntroIds(sp, { skipName = false } = {}) {
  const ids = skipName ? [] : [`sp.${sp.id}.name`];
  ids.push(`sp.${sp.id}.group`);
  if (sp.touch && sp.touch !== 'look') ids.push(`sp.${sp.id}.safety`);
  return ids;
}
