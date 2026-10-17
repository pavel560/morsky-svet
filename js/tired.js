// Mořský svět — the turtle yawns after ~15 minutes (BRIEF §2). Shown at a natural pause, once; never forced.
import { tiredNow } from './session.js';
import { charEl, hasArt } from './assets.js';
import { h, icon, esc, say } from './ui.js';
import { t } from './i18n.js';
import { go } from './router.js';

document.addEventListener('screen:leave', () => document.querySelector('.tired-layer')?.remove());

export function maybeTired() {
  if (!tiredNow()) return false;
  const layer = h(`<div class="tired-layer" role="dialog" aria-modal="true" aria-label="${esc(t('tired.title'))}">
    <div class="tired-card"><div class="tired-turtle"></div>
      <div class="tired-actions">
        <button class="btn round main primary" data-act="home" aria-label="${esc(t('nav.home'))}">${icon('home')}</button>
        <button class="btn round main paper" data-act="stay" aria-label="${esc(t('nav.close'))}">${icon('close')}</button>
      </div></div></div>`);
  if (hasArt('guide-turtle')) layer.querySelector('.tired-turtle').append(charEl('guide-turtle'));
  document.getElementById('overlay').append(layer);
  layer.addEventListener('click', (e) => {
    const b = e.target.closest('[data-act]'); if (!b) return;
    layer.remove(); if (b.dataset.act === 'home') go('home');
  });
  say('ui.tired');
  return true;
}
