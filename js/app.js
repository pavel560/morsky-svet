// Mořský svět — boot: data + art, start tap (sound unlock), routing, rotate prompt, diver colours.
import { loadAll, svgEl, species, zones, trash, voiceIndex } from './assets.js';
import { buildCatalogue } from './phrases.js';
import { register, go } from './router.js';
import { h, icon, esc, say, mountCaption, cssVar } from './ui.js';
import { t, applyI18n } from './i18n.js';
import * as speech from './speech.js';
import * as sound from './sound.js';
import { registerServiceWorker } from './pwa.js';
import * as home from './home.js';
import * as dive from './dive/game.js';
import * as sea from './sea.js';
import * as quiz from './quiz.js';
import * as habitat from './habitat.js';
import * as parents from './parents.js';
import { openCard, closeCard } from './card.js';
import * as store from './store.js';
import * as session from './session.js';

register('home', home); register('dive', dive); register('sea', sea); register('quiz', quiz); register('habitat', habitat); register('parents', parents);

/** Hair + wetsuit colours: picked from the designer's option lists (tokens), set as --hair / --suit. */
export function applyLook() {
  const root = document.documentElement;
  for (const k of ['hair', 'suit', 'skin']) {
    root.style.removeProperty(`--${k}`);
    const list = cssVar(`--${k}-options`).split(/\s+/).filter(Boolean);
    if (list[store.get(k)]) root.style.setProperty(`--${k}`, list[store.get(k)]);
  }
}

function startScreen() {
  const layer = h(`<div class="start-layer">
    <div class="start-card">
      <h1 class="start-title">${esc(t('app.name'))}</h1>
      <button class="btn round hero primary play" aria-label="${esc(t('start.play'))}">${icon('play')}</button>
      <p class="start-safety">${esc(t('say.safetyDive'))}</p>
    </div></div>`);
  document.getElementById('overlay').append(layer);
  layer.querySelector('.play').addEventListener('click', async () => {
    sound.unlock(); speech.unlockAudio(); speech.prime(true); sound.play('bubble');
    layer.classList.add('leaving');
    setTimeout(() => layer.remove(), 380);
    await go('home');
    say(['ui.greet', 'ui.safetyDive']);
  });
}

async function boot() {
  try { await loadAll(); } catch (err) {
    document.getElementById('screen').append(h(`<p class="boot-error">${esc(t('common.loading'))} ${esc(err.message)}</p>`));
    throw err;
  }
  speech.setVoice({ catalogue: buildCatalogue(species, { zones, trash }), index: voiceIndex });
  try { document.getElementById('sprite').append(svgEl('ui-icons', { unique: false })); } catch { /* no icons yet */ }
  mountCaption();
  applyI18n(); applyLook();
  addEventListener('store:change', (e) => { if (['hair', 'suit', 'skin', '*'].includes(e.detail?.key)) applyLook(); });
  const rot = document.getElementById('rotate');
  const drawRot = () => {
    rot.innerHTML = `<div class="rotate-card"><div class="rotate-ic">${icon('rotate')}</div><p>${esc(t('rotate.title'))}</p></div>`;
  };
  drawRot(); addEventListener('langchange', drawRot);
  document.documentElement.classList.add('ready');
  document.documentElement.dataset.screen = 'start';
  if (new URLSearchParams(location.search).has('autostart')) { await go('home'); } else startScreen();
  registerServiceWorker().then((r) => { window.__morsky.sw = { ok: r.ok, reason: r.reason || null }; });
}

for (const ev of ['gesturestart', 'gesturechange', 'gestureend']) document.addEventListener(ev, (e) => e.preventDefault(), { passive: false });
// test / debugging hook (no secrets here)
window.__morsky = { go, openCard, closeCard, store, session, species };
boot();
