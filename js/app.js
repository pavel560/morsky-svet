// Mořský svět — boot: data + art, start tap (sound unlock), routing, rotate prompt, diver colours.
import { loadAll, loadArt, svgEl, charEl, hasArt, species, zones, trash, voiceIndex } from './assets.js';
import { mountScene, toScreen, startDolphin, logoEl, TITLE_ANIM } from './scene.js';
import { buildCatalogue } from './phrases.js';
import { register, go } from './router.js';
import { h, icon, esc, say, mountCaption, cssVar } from './ui.js';
import { t, applyI18n, getLang } from './i18n.js';
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
import { mountLangButton } from './langbtn.js';

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

/** Start screen (DESIGN §10.1): the title scene, the logo, the play bubble in open water, the safety line.
 *  The first tap unlocks sound + speech on the iPad. */
const PLAY_AT = [640, 680];          // scene units: open water left of the fish school, clear of the boat, oar and dolphin arc
function startScreen() {
  const layer = h(`<div class="start-layer">
    <div class="start-scene"></div>
    <div class="logo-wrap start-logo" role="img" data-ta="app.name" aria-label="${esc(t('app.name'))}"></div>
    <button class="play-bubble-btn" data-ta="start.play" aria-label="${esc(t('start.play'))}"></button>
    <p class="start-safety">${icon('parents')}<span data-t="say.safetyDive">${esc(t('say.safetyDive'))}</span></p>
  </div>`);
  document.getElementById('overlay').append(layer);
  const sc = mountScene(layer.querySelector('.start-scene'), 'title', TITLE_ANIM);
  const logo = layer.querySelector('.start-logo');
  const drawLogo = () => logo.replaceChildren(logoEl(getLang()));
  drawLogo();
  const play = layer.querySelector('.play-bubble-btn');
  if (hasArt('play-bubble')) play.append(charEl('play-bubble')); else play.innerHTML = icon('play');
  const place = () => {
    if (!sc) return;
    const p = toScreen(sc, PLAY_AT[0], PLAY_AT[1], innerWidth, innerHeight);
    play.style.left = `${p.x.toFixed(0)}px`; play.style.top = `${p.y.toFixed(0)}px`;
  };
  place(); addEventListener('resize', place);
  const stopDolphin = startDolphin(sc);
  addEventListener('langchange', drawLogo);
  play.addEventListener('click', async () => {
    sound.unlock(); speech.unlockAudio(); speech.prime(true); sound.play('bubble');
    layer.classList.add('leaving');
    setTimeout(() => { layer.remove(); stopDolphin(); removeEventListener('resize', place); removeEventListener('langchange', drawLogo); }, 380);
    await go('home');
    say(['ui.greet', 'ui.safetyDive']);
  });
}

async function boot() {
  try {
    await loadAll();
    await Promise.all(['title', 'home', 'logo-cs', 'logo-en', 'play-bubble', 'door-sea', 'door-quiz', 'door-habitat', 'quiz-bg', 'summary-bg'].map(loadArt));
  } catch (err) {
    document.getElementById('screen').append(h(`<p class="boot-error">${esc(t('common.loading'))} ${esc(err.message)}</p>`));
    throw err;
  }
  speech.setVoice({ catalogue: buildCatalogue(species, { zones, trash }), index: voiceIndex });
  try { document.getElementById('sprite').append(svgEl('ui-icons', { unique: false })); } catch { /* no icons yet */ }
  mountCaption();
  mountLangButton();
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
