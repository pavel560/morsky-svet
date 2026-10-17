// Mořský svět — „Loďka“ (home): the surface, the boat, the diver on its edge, the turtle peeking out.
import { charEl, hasArt, loadArt } from './assets.js';
import { h, icon, esc, say, replay } from './ui.js';
import { t } from './i18n.js';
import { go } from './router.js';
import * as sound from './sound.js';

const HOLD_MS = 3000;
let root = null; let holdT = 0;

export async function mount(el) {
  root = el;
  await loadArt('home');
  el.append(h(`<div class="home">
    <div class="home-scene"></div>
    <div class="home-turtle" data-act="turtle"></div>
    <div class="topbar">
      <button class="btn round touch paper parents-btn" data-act="parents" aria-label="${esc(t('home.parents'))}">${icon('parents')}<svg class="hold-ring" viewBox="0 0 40 40" aria-hidden="true"><circle cx="20" cy="20" r="18"/></svg></button>
      <h1 class="title-pill">${esc(t('app.name'))}</h1>
      <button class="btn round main paper" data-act="replay" aria-label="${esc(t('nav.replay'))}">${icon('speaker')}</button>
    </div>
    <div class="home-main">
      <button class="btn hero primary dive-btn" data-act="dive">${icon('down')}<span>${esc(t('home.dive'))}</span></button>
      <div class="doors">
        <button class="btn door paper" data-act="sea">${icon('collection')}<span>${esc(t('home.sea'))}</span></button>
        <button class="btn door paper" data-act="quiz">${icon('quiz')}<span>${esc(t('home.quiz'))}</span></button>
        <button class="btn door paper" data-act="habitat">${icon('who-where')}<span>${esc(t('home.habitat'))}</span></button>
      </div>
    </div>
    <p class="home-safety">${esc(t('say.safetyDive'))}</p>
  </div>`));
  const scene = el.querySelector('.home-scene');
  if (hasArt('home')) { const art = charEl('home'); scene.append(art); scene.classList.add('has-art'); }
  else scene.innerHTML = '<div class="home-sky"><div class="home-sun"></div></div><div class="home-sea"><div class="home-line"></div></div><div class="home-boat"><div class="boat-hull"></div></div>';
  if (hasArt('guide-turtle')) el.querySelector('.home-turtle').append(charEl('guide-turtle'));
  placeTurtle(); addEventListener('resize', placeTurtle);
  el.addEventListener('click', onClick);
  const pb = el.querySelector('.parents-btn');
  pb.addEventListener('pointerdown', (e) => {
    e.preventDefault(); pb.classList.add('holding');
    holdT = setTimeout(() => { pb.classList.remove('holding'); holdT = -1; sound.play('pop'); go('parents'); }, HOLD_MS);
  });
  const cancel = () => { if (holdT > 0) { clearTimeout(holdT); holdT = 0; pb.classList.remove('holding'); say('ui.parentsHold'); } };
  pb.addEventListener('pointerup', cancel); pb.addEventListener('pointerleave', cancel); pb.addEventListener('pointercancel', cancel);
}
export function unmount() { clearTimeout(holdT); holdT = 0; root = null; removeEventListener('resize', placeTurtle); }

/** The guide peeks out where home.svg says (data-turtle, viewBox units; the scene is xMidYMid slice). */
function placeTurtle() {
  const art = root?.querySelector('.home-scene svg'); const tu = root?.querySelector('.home-turtle');
  if (!art || !tu) return;
  const [tx, ty] = (art.getAttribute('data-turtle') || '').split(/\s+/).map(Number);
  if (!Number.isFinite(tx)) return;
  const vb = (art.getAttribute('viewBox') || '0 0 1600 1000').split(/\s+/).map(Number);
  const W = innerWidth; const H = innerHeight; const k = Math.max(W / vb[2], H / vb[3]);
  tu.style.left = `${((tx - vb[0]) * k + (W - vb[2] * k) / 2).toFixed(0)}px`;
  tu.style.top = `${((ty - vb[1]) * k + (H - vb[3] * k) / 2).toFixed(0)}px`;
  tu.classList.add('anchored');
}

function onClick(e) {
  const b = e.target.closest('[data-act]'); if (!b) return;
  const a = b.dataset.act;
  if (a === 'parents') return;                     // hold-only
  if (a === 'replay') { replay(); return; }
  if (a === 'turtle') { sound.play('bubble'); say(['ui.greet']); return; }
  sound.play('tap');
  if (['dive', 'sea', 'quiz', 'habitat'].includes(a)) go(a);
}
