// Mořský svět — Kvíz „Kdo jsem?“ (BRIEF §4.5): 5 questions. Level 1: name / riddle → pick 1 of 3.
// Level 2 adds „Je to ryba?“ (yes/no) and „Kdo je větší?“. No score, no „wrong“: 1st miss = gentle hint,
// 2nd miss = the choice narrows (one wrong option leaves), never a lit-up answer.
import { species, byId, charEl } from './assets.js';
import { groupKey } from './dive/world.js';
import { h, icon, esc, say, replay, shuffle, sleep, nameOf, anim, reduced } from './ui.js';
import { t, getLang } from './i18n.js';
import { phraseText } from './speech.js';
import { go } from './router.js';
import { effectiveLevel } from './levels.js';
import * as store from './store.js';
import * as sound from './sound.js';
import { maybeTired } from './tired.js';

export const ROUNDS = 5;
let S = null;

/** Question plan (pure-ish; exported for tests): list of { type, target, options }. */
export function plan(pool, level, rnd = Math.random) {
  const types = level >= 2 ? ['name', 'riddle', 'isFish', 'bigger'] : ['name', 'riddle'];
  const pick = (arr) => arr[Math.floor(rnd() * arr.length)];
  const out = []; const used = new Set();
  for (let i = 0; i < ROUNDS; i++) {
    let type = types[i % types.length];
    const fresh = pool.filter((s) => !used.has(s.id));
    const target = pick(fresh.length ? fresh : pool);
    used.add(target.id);
    if (type === 'bigger') {
      const other = pool.filter((s) => s.id !== target.id && s.sizeCm && target.sizeCm && Math.max(s.sizeCm, target.sizeCm) / Math.min(s.sizeCm, target.sizeCm) >= 2);
      if (!other.length) type = 'name';
      else { const o = pick(other); out.push({ type, target: target.sizeCm > o.sizeCm ? target : o, options: shuffle([target, o]) }); continue; }
    }
    if (type === 'isFish') { out.push({ type, target, options: [] }); continue; }
    const distract = shuffle(pool.filter((s) => s.id !== target.id)).slice(0, 2);
    out.push({ type, target, options: shuffle([target, ...distract]) });
  }
  return out;
}

export function mount(root) {
  const lvl = effectiveLevel();
  const levelPool = species.filter((s) => (s.level || 1) <= lvl);
  const found = species.filter((s) => store.isFound(s.id));
  const pool = found.length >= 4 ? found : levelPool.length >= 3 ? levelPool : species;
  const el = h(`<div class="quiz">
    <div class="topbar">
      <button class="btn round main paper" data-act="home" aria-label="${esc(t('nav.home'))}">${icon('home')}</button>
      <h1 class="title-pill">${esc(t('quiz.title'))}</h1>
      <div class="quiz-progress" aria-hidden="true">${Array.from({ length: ROUNDS }, () => '<i></i>').join('')}</div>
      <button class="btn round main paper" data-act="replay" aria-label="${esc(t('nav.replay'))}">${icon('speaker')}</button>
    </div>
    <div class="quiz-stage"></div></div>`);
  root.append(el);
  S = { el, stage: el.querySelector('.quiz-stage'), qs: plan(pool, lvl), i: 0, misses: 0, busy: false, lvl };
  el.addEventListener('click', onClick);
  window.__morsky.quiz = { current: () => S && { ...S.qs[S.i], target: S.qs[S.i]?.target.id, options: S.qs[S.i]?.options.map((o) => o.id), i: S.i } };
  say(['ui.quizIntro']).then(() => { if (S && S.i === 0) ask(); });
  show();
}
export function unmount() { S = null; if (window.__morsky) delete window.__morsky.quiz; }

function promptIds(q) {
  const id = q.target.id; const lang = getLang();
  if (q.type === 'riddle') return [phraseText(`sp.${id}.riddle`, lang) ? `sp.${id}.riddle` : `sp.${id}.look.0`];
  if (q.type === 'isFish') return [`sp.${id}.isFishQ`];
  if (q.type === 'bigger') return ['ui.quizBigger'];
  return [`sp.${id}.where`];
}
const ask = () => { if (S) say(promptIds(S.qs[S.i])); };

function show() {
  const q = S.qs[S.i]; S.misses = 0; S.busy = false;
  S.el.querySelectorAll('.quiz-progress i').forEach((d, k) => d.classList.toggle('on', k < S.i));
  let html;
  if (q.type === 'isFish') {
    html = `<div class="q-one"><div class="q-art"></div></div>
      <div class="q-yesno"><button class="btn yes-no" data-act="ans" data-v="yes" aria-label="${esc(t('quiz.yes'))}">${icon('grp-ryba')}${icon('check', 'mark')}</button>
      <button class="btn yes-no" data-act="ans" data-v="no" aria-label="${esc(t('quiz.no'))}">${icon('grp-ryba')}${icon('close', 'mark')}</button></div>`;
  } else {
    html = `<div class="q-opts n${q.options.length}">${q.options.map((o) => `<button class="q-opt" data-act="ans" data-v="${esc(o.id)}" aria-label="${esc(nameOf(o))}"></button>`).join('')}</div>`;
  }
  S.stage.innerHTML = `<button class="btn q-prompt" data-act="prompt">${icon('speaker')}<span>${esc(promptText(q))}</span></button>${html}`;
  if (q.type === 'isFish') S.stage.querySelector('.q-art').append(charEl(q.target.id));
  else for (const b of S.stage.querySelectorAll('.q-opt')) b.append(charEl(b.dataset.v));
  if (S.i > 0) ask();
}
function promptText(q) { const lang = getLang(); return phraseText(promptIds(q)[0], lang) || ''; }

async function answer(b) {
  if (S.busy) return;
  const q = S.qs[S.i]; const v = b.dataset.v;
  const right = q.type === 'isFish' ? (v === 'yes') === (groupKey(q.target.group) === 'ryba') : v === q.target.id;
  if (!right) {
    S.misses += 1; sound.play('tryAgain');
    if (!reduced()) anim(b, [{ transform: 'translateX(0)' }, { transform: 'translateX(-10px)' }, { transform: 'translateX(10px)' }, { transform: 'translateX(0)' }], { duration: 320 });
    if (S.misses >= 2) {                                       // narrow the choice: this wrong option leaves
      b.disabled = true; b.classList.add('gone');
      say(['ui.quizShow']);
    } else say(['ui.quizTry', ...promptIds(q)]);
    return;
  }
  S.busy = true; b.classList.add('right'); sound.play('sparkle');
  const praise = `ui.quizRight${S.i % 3}`;
  const tail = q.type === 'isFish' ? [`sp.${q.target.id}.isFishA`] : q.type === 'bigger' ? [`sp.${q.target.id}.bigger`] : [`sp.${q.target.id}.name`];
  await say([praise, ...tail]);
  await sleep(350);
  if (!S) return;
  S.i += 1;
  if (S.i >= ROUNDS) return done();
  show();
}

function done() {
  S.el.querySelectorAll('.quiz-progress i').forEach((d) => d.classList.add('on'));
  S.stage.innerHTML = `<div class="quiz-done"><div class="q-turtle"></div>
    <div class="q-done-actions"><button class="btn hero primary" data-act="again" aria-label="${esc(t('home.quiz'))}">${icon('quiz')}</button>
    <button class="btn round main paper" data-act="home" aria-label="${esc(t('nav.home'))}">${icon('home')}</button></div></div>`;
  try { S.stage.querySelector('.q-turtle').append(charEl('guide-turtle')); } catch { /* no art */ }
  sound.play('success');
  say(['ui.quizDone']).then(() => maybeTired());
}

function onClick(e) {
  const b = e.target.closest('[data-act]'); if (!b || !S) return;
  const a = b.dataset.act;
  if (a === 'ans') return answer(b);
  sound.play('tap');
  if (a === 'home') go('home');
  else if (a === 'replay' || a === 'prompt') { if (S.i < ROUNDS) ask(); else replay(); }
  else if (a === 'again') go('quiz');
}
