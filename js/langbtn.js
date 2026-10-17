// Mořský svět — the visible language switch (like Houbičky): one 64 px round flag button, top-right under the
// speaker, on start / Loďka / Ponor / Můj kousek moře / Kvíz. It shows the flag of the OTHER language (tap the
// flag you want) with a small swap badge. Tap = switch at once, persist, the turtle says one line in the new language.
// Texts marked data-t / data-ta (aria-label) are re-translated in place on 'langchange' — nothing is remounted.
import { h, icon, esc, say } from './ui.js';
import { t, getLang, setLang } from './i18n.js';
import * as sound from './sound.js';

const OTHER = { cs: 'en', en: 'cs' };
/** Designer may add dedicated button flags (i-flag-cz-btn / i-flag-en-btn); fall back to the plain flags. */
function flagIcon(lang) {
  const btn = lang === 'cs' ? 'flag-cz-btn' : 'flag-en-btn';
  return document.getElementById(`i-${btn}`) ? btn : `flag-${lang}`;
}
let el = null;
function draw() {
  const to = OTHER[getLang()];
  el.innerHTML = `${icon(flagIcon(to), 'flag')}<span class="lang-swap" aria-hidden="true">${icon('flip')}</span>`;
  el.setAttribute('aria-label', t(`lang.${to}`));
  el.dataset.to = to;
}
export function mountLangButton() {
  el = h('<button id="lang-btn" class="btn round touch paper" type="button"></button>');
  document.body.append(el);
  draw();
  el.addEventListener('click', () => {
    sound.play('tap');
    setLang(el.dataset.to);
    say(['ui.langHello']);
  });
  addEventListener('langchange', () => { draw(); retranslate(); });
}
export function retranslate(root = document) {
  for (const n of root.querySelectorAll('[data-t]')) n.textContent = t(n.dataset.t);
  for (const n of root.querySelectorAll('[data-ta]')) n.setAttribute('aria-label', t(n.dataset.ta));
}
export const _esc = esc;
