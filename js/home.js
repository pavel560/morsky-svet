// Mořský svět — „Loďka“ (home, DESIGN §10.2): the boat scene, a small logo, „Ponořit se!“ on the right at the waterline,
// three doors as objects on the seabed (bowl = Můj kousek moře, clam with a „?“ pearl = Kvíz, sea map = Kdo kde bydlí?),
// parents (hold 3 s) + language top-left, speaker top-right, the turtle peeking out at data-turtle.
import { charEl, hasArt } from './assets.js';
import { h, icon, esc, say, replay } from './ui.js';
import { t, getLang } from './i18n.js';
import { go } from './router.js';
import { mountScene, toScreen, logoEl, HOME_ANIM } from './scene.js';
import * as sound from './sound.js';

const HOLD_MS = 3000;
let root = null; let holdT = 0; let sc = null;
const DOORS = [['sea', 'home.sea'], ['quiz', 'home.quiz'], ['habitat', 'home.habitat']];

export function mount(el) {
  root = el;
  el.append(h(`<div class="home">
    <div class="home-scene"></div>
    <div class="home-turtle" data-act="turtle"></div>
    <div class="topbar">
      <button class="btn round touch paper parents-btn" data-act="parents" data-ta="home.parents" aria-label="${esc(t('home.parents'))}">${icon('parents')}<svg class="hold-ring" viewBox="0 0 40 40" aria-hidden="true"><circle cx="20" cy="20" r="18"/></svg></button>
      <h1 class="sr-only" data-t="app.name">${esc(t('app.name'))}</h1>
      <div class="logo-wrap home-logo" aria-hidden="true"></div>
      <button class="btn round main primary" data-act="replay" data-ta="nav.replay" aria-label="${esc(t('nav.replay'))}">${icon('speaker')}</button>
    </div>
    <button class="btn dive-btn primary" data-act="dive"><span class="dive-ic">${icon('down')}</span><span data-t="home.dive">${esc(t('home.dive'))}</span></button>
    <div class="doors">${DOORS.map(([a, k]) => `<button class="door" data-act="${a}" data-ta="${k}" aria-label="${esc(t(k))}">
      <span class="door-obj"></span><span class="door-label" data-t="${k}">${esc(t(k))}</span></button>`).join('')}</div>
    <p class="home-safety">${icon('parents')}<span data-t="say.safetyDive">${esc(t('say.safetyDive'))}</span></p>
  </div>`));
  sc = mountScene(el.querySelector('.home-scene'), 'home', HOME_ANIM);
  if (!sc) el.querySelector('.home-scene').classList.add('fallback');
  for (const [a] of DOORS) { const art = `door-${a === 'sea' ? 'sea' : a === 'quiz' ? 'quiz' : 'habitat'}`; if (hasArt(art)) el.querySelector(`.door[data-act="${a}"] .door-obj`).append(charEl(art)); }
  drawLogo();
  if (hasArt('guide-turtle')) el.querySelector('.home-turtle').append(charEl('guide-turtle'));
  placeTurtle(); addEventListener('resize', placeTurtle); addEventListener('langchange', drawLogo);
  el.addEventListener('click', onClick);
  const pb = el.querySelector('.parents-btn');
  pb.addEventListener('pointerdown', (e) => {
    e.preventDefault(); pb.classList.add('holding');
    holdT = setTimeout(() => { pb.classList.remove('holding'); holdT = -1; sound.play('pop'); go('parents'); }, HOLD_MS);
  });
  const cancel = () => { if (holdT > 0) { clearTimeout(holdT); holdT = 0; pb.classList.remove('holding'); say('ui.parentsHold'); } };
  pb.addEventListener('pointerup', cancel); pb.addEventListener('pointerleave', cancel); pb.addEventListener('pointercancel', cancel);
}
export function unmount() { clearTimeout(holdT); holdT = 0; root = null; sc = null; removeEventListener('resize', placeTurtle); removeEventListener('langchange', drawLogo); }

function drawLogo() { root?.querySelector('.home-logo')?.replaceChildren(logoEl(getLang())); }
/** The guide peeks out where home.svg says (data-turtle, viewBox units, slice mapping). */
function placeTurtle() {
  const tu = root?.querySelector('.home-turtle'); if (!tu || !sc) return;
  const [tx, ty] = (sc.root.getAttribute('data-turtle') || '').split(/\s+/).map(Number);
  if (!Number.isFinite(tx)) return;
  const p = toScreen(sc, tx, ty, innerWidth, innerHeight);
  tu.style.left = `${p.x.toFixed(0)}px`; tu.style.top = `${p.y.toFixed(0)}px`;
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
