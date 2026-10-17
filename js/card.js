// Mořský svět — Kartička (BRIEF §4.3): pins on 3 features, group badge, where I live, what I eat,
// size vs the diver (115 cm), „Víš, že…?“, look-only mark, flip to the real photo with credit.
import { byId, zoneById, charEl, hasArt, hasPhoto, photoUrl, photoCredit, spanFrac, hiddenPhotos } from './assets.js';
import { cardIntroIds } from './phrases.js';
import { groupKey, DIVER_SIZE_CM } from './dive/world.js';
import { $, h, icon, esc, say, hush, nameOf, anim, reduced } from './ui.js';
import { t, getLang } from './i18n.js';
import * as store from './store.js';
import * as sound from './sound.js';

let layer = null; let current = null; let opening = false; let resolveClose = null;
export const cardOpen = () => !!layer || opening;
document.addEventListener('screen:leave', () => closeCard());

const depthText = (sp) => {
  const d = Array.isArray(sp.depthM) ? sp.depthM : null;
  return d ? `${d[0]}–${d[1]} m` : '';
};
const lookText = (lf, lang) => (lf && typeof lf === 'object' ? lf[lang] ?? lf.cs : lf) || '';

function frontHtml(sp) {
  const lang = getLang(); const other = lang === 'cs' ? 'en' : 'cs';
  const g = groupKey(sp.group);
  const looks = (sp.lookFor || []).map((lf, i) =>
    `<li><button class="look" data-act="look" data-look="${i}"><span class="num">${i + 1}</span><span class="look-text">${esc(lookText(lf, lang))}</span></button></li>`).join('');
  const zone = zoneById.get(sp.zone);
  const zname = (zone?.name && (zone.name[lang] ?? zone.name.cs)) || t(`zone.${sp.zone}`);
  const touch = sp.touch && sp.touch !== 'look' ? sp.touch : null;
  return `
    <div class="card-face card-front">
      <div class="card-art" data-zone="${esc(sp.zone)}"><div class="art-box"></div><div class="pins"></div>
        <button class="size-bar" data-act="size" aria-label="${esc(t('card.size'))}"><span class="sz-track"><span class="sz-diver"></span><span class="sz-animal"></span></span></button>
        ${touch ? `<button class="look-only" data-act="safety">${icon('look-only')}<span>${esc(t(`touch.${touch}`))} · ${esc(t('card.safetyLook'))}</span></button>` : ''}
      </div>
      <div class="card-info">
        <h2 class="sp-name" id="card-title">${esc(nameOf(sp, lang))}</h2>
        <p class="sp-alt">${icon(`flag-${other}`, 'flag')}<span class="alt-name">${esc(nameOf(sp, other))}</span><span class="latin">${esc(sp.latin || '')}</span></p>
        <div class="card-rows">
          <button class="badge grp" data-group="${g}" data-act="group">${icon(`grp-${g}`)}<span>${esc(t(`group.${g}`))}</span></button>
          <button class="row-btn" data-act="home" data-zone="${esc(sp.zone)}">${icon(`zone-${sp.zone}`)}<span><b>${esc(zname)}</b> ${esc(depthText(sp))}</span></button>
          <button class="row-btn" data-act="eats">${icon(`eats-${sp.eats || 'mixed'}`)}<span>${esc(t(`eats.${sp.eats || 'mixed'}`))}</span></button>
        </div>
        <ol class="looks" aria-label="${esc(t('card.lookFor'))}">${looks}</ol>
        <button class="wow" data-act="fact">${icon('turtle')}<span class="wow-q">${esc(t('card.fact'))}</span><span class="wow-text">${esc(lookText(sp.fact, lang))}</span></button>
      </div>
    </div>`;
}
function backHtml(sp) {
  if (hasPhoto(sp.id)) {
    const c = photoCredit(sp.id);
    return `<div class="card-face card-back" inert aria-hidden="true">
      <figure class="photo-frame"><img class="photo" alt="${esc(nameOf(sp))}" src="${photoUrl(sp.id)}" decoding="async">
        <figcaption class="credit">${esc(t('card.photoCredit', { author: c.author, license: c.license }))}</figcaption></figure></div>`;
  }
  return `<div class="card-face card-back missing" inert aria-hidden="true">${missingInner(sp.id)}</div>`;
}

const missingInner = (id) => `<div class="missing-frame"><div class="missing-art"></div><span class="missing-ic">${icon('photo')}</span></div>
  <p class="missing-text">${esc(t('card.photoMissing'))}</p>${hiddenPhotos.has(id) ? '' : `<p class="missing-hint">${esc(t('card.photoMissingHint'))}</p>`}`;

/** Size bar: diver (115 cm) and animal on ONE scale; the smaller shrinks to a dot (min 3 %). */
function fillSizeBar(card, sp) {
  const L = Math.max(DIVER_SIZE_CM, sp.sizeCm || 1);
  const fd = Math.max(0.03, DIVER_SIZE_CM / L); const fa = Math.max(0.03, (sp.sizeCm || 1) / L);
  const dv = $('.sz-diver', card); const an = $('.sz-animal', card);
  dv.style.setProperty('--f', fd.toFixed(4)); an.style.setProperty('--f', fa.toFixed(4));
  if (hasArt('diver')) dv.append(charEl('diver'));
  const a = charEl(sp.id); const { f0, f1 } = spanFrac(a);
  a.style.setProperty('--span', (f1 - f0).toFixed(4)); a.style.setProperty('--f0', f0.toFixed(4));
  an.append(a);
  card.dataset.bigger = fa > fd ? 'animal' : 'diver';
}

function placePins(card) {
  const art = $('.card-art', card); const svg = $('.art-box svg', card); const pins = $('.pins', card);
  if (!art || !svg) return;
  const base = art.getBoundingClientRect(); const pts = [];
  pins.replaceChildren();
  for (const a of [...svg.querySelectorAll('circle.anchor[data-look]')].sort((x, y) => x.dataset.look - y.dataset.look)) {
    const r = a.getBoundingClientRect();
    let x = r.x + r.width / 2 - base.x; let y = r.y + r.height / 2 - base.y;
    for (const [px, py] of pts) {
      const d = Math.hypot(x - px, y - py);
      if (d < 72) { const vx = (x - px) / (d || 1); const vy = (y - py) / (d || 1) || 1; x += vx * (72 - d); y += vy * (72 - d); }
    }
    pts.push([x, y]);
    const i = +a.dataset.look;
    pins.append(h(`<button class="pin" data-act="look" data-look="${i}" style="left:${x.toFixed(0)}px;top:${y.toFixed(0)}px" aria-label="${esc(t('card.pin', { n: i + 1 }))}"><span>${i + 1}</span></button>`));
  }
}
function pulse(i) {
  const pin = $(`.pin[data-look="${i}"]`, layer); const chip = $(`.look[data-look="${i}"]`, layer);
  for (const el of [pin, chip]) { if (!el) continue; el.classList.remove('lit'); void el.offsetWidth; el.classList.add('lit'); }
}

/** Open the card; resolves when it is closed. skipName: the creature already said its name on the tap. */
export function openCard(id, { skipName = false } = {}) {
  if (layer || opening) return Promise.resolve(false);
  const sp = byId.get(id); if (!sp) return Promise.resolve(false);
  opening = true; current = sp;
  store.addFound(id);
  layer = h(`<div class="card-layer" data-id="${esc(id)}">
    <div class="card-scrim" data-act="close"></div>
    <section class="card" role="dialog" aria-modal="true" aria-labelledby="card-title" data-group="${groupKey(sp.group)}" data-zone="${esc(sp.zone)}">
      <div class="card-flip">${frontHtml(sp)}${backHtml(sp)}</div>
      <div class="card-actions">
        <button class="btn round main primary" data-act="speak" aria-label="${esc(t('card.listen'))}">${icon('speaker')}</button>
        <button class="btn round main paper" data-act="flip" aria-label="${esc(t('card.flip'))}">${icon('photo')}</button>
        <button class="btn round touch paper" data-act="close" aria-label="${esc(t('nav.close'))}">${icon('close')}</button>
      </div>
    </section></div>`);
  $('.art-box', layer).append(charEl(id));
  const miss = $('.missing-art', layer); if (miss) miss.append(charEl(id));
  fillSizeBar(layer, sp);
  $('img.photo', layer)?.addEventListener('error', () => {
    const back = $('.card-back', layer); if (!back) return;
    back.classList.add('missing'); back.innerHTML = missingInner(id);
    $('.missing-art', back).append(charEl(id));
  }, { once: true });
  document.getElementById('overlay').append(layer);
  layer.addEventListener('click', onClick);
  document.addEventListener('keydown', onKey);
  requestAnimationFrame(() => { if (layer) placePins(layer); });
  addEventListener('resize', onResize);
  sound.play('whoosh');
  if (!reduced()) anim($('.card', layer), [{ transform: 'translateY(24px) scale(.96)', opacity: 0 }, { transform: 'none', opacity: 1 }], { duration: 320, easing: 'cubic-bezier(.22,1,.36,1)' });
  say(cardIntroIds(sp, { skipName }));
  opening = false;
  return new Promise((r) => { resolveClose = r; });
}
const onResize = () => { if (layer) placePins(layer); };
const onKey = (e) => { if (e.key === 'Escape') closeCard(); };

export function closeCard() {
  if (!layer) return;
  hush();
  layer.remove(); layer = null;
  removeEventListener('resize', onResize); document.removeEventListener('keydown', onKey);
  const sp = current; current = null;
  window.dispatchEvent(new CustomEvent('card:close', { detail: { id: sp?.id } }));
  const r = resolveClose; resolveClose = null; r?.(true);
}

function flip() {
  const f = $('.card-flip', layer); const on = !f.classList.contains('flipped');
  f.classList.toggle('flipped', on);
  const front = $('.card-front', layer); const back = $('.card-back', layer);
  for (const [el, show] of [[front, !on], [back, on]]) { el.inert = !show; el.setAttribute('aria-hidden', String(!show)); }
  $('[data-act="flip"]', layer).setAttribute('aria-label', t(on ? 'card.drawing' : 'card.flip'));
  if (on && back.classList.contains('missing')) say('ui.photoMissing');
}

function onClick(e) {
  const b = e.target.closest('[data-act]'); if (!b || !current) return;
  const id = current.id; const a = b.dataset.act;
  if (a === 'close') { sound.play('tap'); closeCard(); return; }
  sound.play('tap');
  if (a === 'speak') say(cardIntroIds(current));
  else if (a === 'flip') flip();
  else if (a === 'look') { const i = +b.dataset.look; pulse(i); say(`sp.${id}.look.${i}`); }
  else if (a === 'group') say(`sp.${id}.group`);
  else if (a === 'home') say(`sp.${id}.home`);
  else if (a === 'eats') say(`sp.${id}.eats`);
  else if (a === 'size') say(`sp.${id}.size`);
  else if (a === 'fact') { b.classList.add('open'); say(`sp.${id}.fact`); }
  else if (a === 'safety') say([`sp.${id}.safety`, 'ui.safetyLook']);
}
