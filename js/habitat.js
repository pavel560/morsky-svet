// Mořský svět — „Kdo kde bydlí?“ (BRIEF §4.6): a vertical cut through the sea (4 floors); the child moves
// 6 animals to their floor (drag, or tap + tap). A miss is corrected kindly; a 2nd miss on the same animal
// dims one wrong floor (the choice narrows), it never lights the answer.
import { species, charEl, hasArt, loadArt } from './assets.js';
import { ZONE_IDS } from './dive/world.js';
import { h, icon, esc, say, replay, shuffle, nameOf, anim, reduced } from './ui.js';
import { t } from './i18n.js';
import { go } from './router.js';
import { pressDrag, inside } from './drag.js';
import { effectiveLevel } from './levels.js';
import * as store from './store.js';
import * as sound from './sound.js';
import { maybeTired } from './tired.js';

let S = null;

/** 6 animals, at least one per floor when possible (exported for tests). */
export function pickSix(list, rnd = Math.random) {
  const byZone = ZONE_IDS.map((z) => shuffle(list.filter((s) => s.zone === z)));
  const out = [];
  for (const zl of byZone) if (zl.length) out.push(zl.shift());
  const rest = shuffle(byZone.flat());
  while (out.length < 6 && rest.length) out.push(rest.shift());
  return shuffle(out).slice(0, 6);
}

export async function mount(root) {
  await loadArt('cross-section');
  const lvl = effectiveLevel();
  const pool = species.filter((s) => (s.level || 1) <= lvl);
  const six = pickSix(pool.length >= 6 ? pool : species);
  const el = h(`<div class="habitat">
    <div class="topbar">
      <button class="btn round main paper" data-act="home" aria-label="${esc(t('nav.home'))}">${icon('home')}</button>
      <h1 class="title-pill">${esc(t('habitat.title'))}</h1>
      <button class="btn round main paper" data-act="replay" aria-label="${esc(t('nav.replay'))}">${icon('speaker')}</button>
    </div>
    <div class="hab-body">
      <div class="hab-tray">${six.map((sp) => `<button class="hab-cr" data-id="${esc(sp.id)}" aria-label="${esc(nameOf(sp))}"></button>`).join('')}</div>
      <div class="hab-cut">${ZONE_IDS.map((z) => `<button class="hab-floor" data-zone="${z}" aria-label="${esc(t(`zone.${z}`))}">${icon(`zone-${z}`)}<span class="hab-label">${esc(t(`zone.${z}`))}</span><span class="hab-slot"></span></button>`).join('')}</div>
    </div></div>`);
  root.append(el);
  if (hasArt('cross-section')) {        // the designer's cut through the sea; band rows follow its data-y0/y1
    const art = charEl('cross-section'); const cut = el.querySelector('.hab-cut');
    art.setAttribute('preserveAspectRatio', 'none');            // bands must line up with the drop rows exactly
    const bands = [...art.querySelectorAll('.band[data-y0]')].map((b) => [+b.dataset.y0, +b.dataset.y1]);
    const H = Number((art.getAttribute('viewBox') || '0 0 1 1000').split(/\s+/)[3]) || 1000;
    if (bands.length === 4) cut.style.gridTemplateRows = `${bands[0][0] / H}fr ${bands.map(([a, b]) => `${(b - a) / H}fr`).join(' ')}`;
    cut.classList.add('has-art'); cut.prepend(h('<div class="hab-sky"></div>')); cut.append(art);
  }
  S = { el, six, selected: null, misses: {}, placed: 0 };
  for (const b of el.querySelectorAll('.hab-cr')) {
    b.append(charEl(b.dataset.id));
    b.addEventListener('pointerdown', (e) => {
      if (b.classList.contains('home')) return;
      pressDrag(e, b, {
        ghost: () => { const g = h('<div class="ghost"></div>'); g.append(charEl(b.dataset.id)); return g; },
        onTap: () => select(b),
        onDrop: (x, y) => { const f = [...el.querySelectorAll('.hab-floor')].find((fl) => inside(fl, x, y)); if (f) drop(b, f); },
      });
    });
  }
  el.addEventListener('click', onClick);
  window.__morsky.habitat = { six: () => S?.six.map((s) => ({ id: s.id, zone: s.zone })), drop: (id, zone) => drop(el.querySelector(`.hab-cr[data-id="${id}"]`), el.querySelector(`.hab-floor[data-zone="${zone}"]`)) };
  say(['ui.habitatIntro']);
}
export function unmount() { S = null; if (window.__morsky) delete window.__morsky.habitat; }

function select(b) {
  S.selected = S.selected === b.dataset.id ? null : b.dataset.id;
  S.el.querySelectorAll('.hab-cr').forEach((x) => x.classList.toggle('selected', x.dataset.id === S.selected));
  sound.play('tap');
  if (S.selected) say([`sp.${S.selected}.name`]);
}

function drop(b, floor) {
  if (!b || !floor || b.classList.contains('home') || floor.classList.contains('dim-' + b.dataset.id)) return;
  const id = b.dataset.id; const sp = S.six.find((s) => s.id === id);
  S.selected = null; S.el.querySelectorAll('.hab-cr').forEach((x) => x.classList.remove('selected'));
  if (floor.dataset.zone !== sp.zone) {
    S.misses[id] = (S.misses[id] || 0) + 1; sound.play('tryAgain');
    if (!reduced()) anim(b, [{ transform: 'translateX(0)' }, { transform: 'translateX(-10px)' }, { transform: 'translateX(10px)' }, { transform: 'translateX(0)' }], { duration: 320 });
    if (S.misses[id] >= 2) {                                    // narrow: the floor just tried is dimmed for this animal
      floor.classList.add(`dim-${id}`, 'dimmed');
      setTimeout(() => floor.classList.remove('dimmed'), 2600);
    }
    say(['ui.habitatWrong']);
    return;
  }
  b.classList.add('home'); b.disabled = true;
  floor.querySelector('.hab-slot').append(b);
  sound.play('bubble'); S.placed += 1;
  if (S.placed >= S.six.length) { sound.play('success'); say([`sp.${id}.home`, 'ui.habitatDone']).then(() => maybeTired()); }
  else say([`sp.${id}.home`]);
}

function onClick(e) {
  const b = e.target.closest('[data-act], .hab-floor'); if (!b || !S) return;
  if (b.classList.contains('hab-floor')) {
    if (S.selected) drop(S.el.querySelector(`.hab-cr[data-id="${S.selected}"]`), b);
    return;
  }
  sound.play('tap');
  if (b.dataset.act === 'home') go('home'); else if (b.dataset.act === 'replay') replay();
}
