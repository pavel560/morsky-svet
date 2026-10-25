// Mořský svět — Koutek pro rodiče (BRIEF §4.7), behind a 3 s hold on the home screen.
import { species, credits, manifest, photoCredit, hiddenPhotos } from './assets.js';
import { h, icon, esc, say, cssVar, nameOf } from './ui.js';
import { t, getLang, setLang } from './i18n.js';
import * as store from './store.js';
import * as sound from './sound.js';
import { go } from './router.js';

let root = null; let pollT = 0;
const sw = (on, act) => `<button class="switch" role="switch" aria-checked="${on}" data-act="${act}"><span class="knob"></span><span class="sw-label">${esc(on ? t('parents.on') : t('parents.off'))}</span></button>`;
const seg = (act, opts, cur) => `<div class="seg" role="group">${opts.map(([v, label]) => `<button class="seg-btn${String(v) === String(cur) ? ' on' : ''}" aria-pressed="${String(v) === String(cur)}" data-act="${act}" data-v="${v}">${esc(label)}</button>`).join('')}</div>`;
const swatches = (act, list, cur, labelKey) => `<div class="swatches" role="group">${list.map((c, i) =>
  `<button class="swatch${i === cur ? ' on' : ''}" data-act="${act}" data-v="${i}" aria-pressed="${i === cur}" aria-label="${esc(t(`${labelKey}.${i}`))}" style="--sw:${esc(c)}"></button>`).join('')}</div>`;

function credRows() {
  return species.map((sp) => {
    const has = !!credits[sp.id]; const c = photoCredit(sp.id);
    const right = has || manifest[sp.id]
      ? `${esc(c.author)} · ${c.licenseUrl ? `<a href="${esc(c.licenseUrl)}" target="_blank" rel="noopener">${esc(c.license)}</a>` : esc(c.license)}${c.sourcePage ? ` · <a href="${esc(c.sourcePage)}" target="_blank" rel="noopener">Wikimedia Commons</a>` : ''}${has ? '' : ` <span class="muted">(${esc(t('parents.creditsEmpty'))})</span>`}`
      : `<span class="muted">${esc(t('parents.creditsEmpty'))}</span>`;
    return `<li><b>${esc(nameOf(sp))}</b> <i>${esc(sp.latin || '')}</i>${hiddenPhotos.has(sp.id) ? ` <span class="muted">(${esc(t('parents.photoHidden'))})</span>` : ''}<br>${right}</li>`;
  }).join('');
}

// The free games link to the paid series only here, behind the parents' hold — never from the child's screens, never
// as a purchase button. Empty until the series has its name and web address; the section is then hidden.
const SERIES = { name: '', url: '' };

function aboutSection() {
  const more = SERIES.url
    ? `<section class="more-games"><h2>${esc(t('parents.moreGames'))}</h2><p>${t('parents.moreGamesText', {
      name: `<a href="${esc(SERIES.url)}" target="_blank" rel="noopener">${esc(SERIES.name || SERIES.url)}</a>` })}</p></section>`
    : '';
  return `<section class="about"><h2>${esc(t('parents.about'))}</h2>
      <p>${esc(t('parents.aboutMade'))}</p><p class="muted">${esc(t('parents.aboutVoices'))}<br>${esc(t('parents.aboutFonts'))}</p>
      <p>${esc(t('parents.aboutPrivacy'))}</p></section>${more}`;
}

function render() {
  const hair = cssVar('--hair-options').split(/\s+/).filter(Boolean);
  const suit = cssVar('--suit-options').split(/\s+/).filter(Boolean);
  const skin = cssVar('--skin-options').split(/\s+/).filter(Boolean);
  const st = store.get();
  root.replaceChildren(h(`<div class="parents-screen">
    <div class="topbar">
      <button class="btn round main paper" data-act="home" aria-label="${esc(t('nav.home'))}">${icon('home')}</button>
      <h1 class="title-pill">${esc(t('parents.title'))}</h1>
    </div>
    <article class="sheet">
      <section class="safety-box">${icon('parents', 'big')}<div><p><b>${esc(t('say.safetyDive'))}</b></p><p>${esc(t('say.safetyLook'))}</p></div></section>
      <section><p class="muted progress-line">${esc(t('parents.found', { n: store.foundCount(), total: species.length, d: st.dives, t: st.trash }))}</p></section>
      <section class="offline"><h2>${esc(t('parents.offline'))}</h2>
        <p class="offline-ready" role="status">${esc(t('parents.offlineChecking'))}</p><p class="muted">${esc(t('parents.offlineHint'))}</p></section>
      <section class="row-set">
        <div class="row"><h2>${esc(t('parents.level'))}</h2>${seg('level', [[1, `1 · ${t('level.1')}`], [2, `2 · ${t('level.2')}`]], st.level)}</div>
        <p class="muted">${esc(t('parents.levelHint'))}</p>
        <div class="row"><h2>${esc(t('parents.lang'))}</h2>${seg('lang', [['cs', t('lang.cs')], ['en', t('lang.en')]], getLang())}</div>
        <div class="row"><h2>${esc(t('parents.rate'))}</h2>${seg('rate', [['slow', t('parents.rateSlow')], ['normal', t('parents.rateNormal')]], st.rate)}</div>
        <div class="row"><h2>${esc(t('parents.sound'))}</h2>${sw(!st.mute, 'sound')}</div>
        <div class="row"><h2>${esc(t('parents.turtle'))}</h2><input class="text-in turtle-name" maxlength="24" value="${esc(st.turtleName)}" placeholder="${esc(t('turtle.default'))}" autocomplete="off"></div>
        <p class="muted">${esc(t('parents.turtleHint'))}</p>
        <div class="row"><h2>${esc(t('parents.hair'))}</h2>${swatches('hair', hair, st.hair, 'hair')}</div>
        <div class="row"><h2>${esc(t('parents.suit'))}</h2>${swatches('suit', suit, st.suit, 'suit')}</div>
        ${skin.length ? `<div class="row"><h2>${esc(t('parents.skin'))}</h2>${swatches('skin', skin, st.skin, 'skin')}</div>` : ''}
      </section>
      <section class="backup"><h2>${esc(t('parents.backup'))}</h2>
        <div class="btn-row"><button class="btn text-btn" data-act="export">${esc(t('parents.export'))}</button>
        <button class="btn text-btn" data-act="copy">${esc(t('parents.copy'))}</button>
        <button class="btn text-btn" data-act="import">${esc(t('parents.import'))}</button></div>
        <div class="import-box" hidden><textarea class="text-in import-text" rows="3" placeholder="${esc(t('parents.importPaste'))}"></textarea>
          <div class="btn-row"><label class="btn text-btn file-btn">${esc(t('parents.import'))}…<input type="file" accept="application/json,.json,.txt" hidden></label>
          <button class="btn text-btn" data-act="import-go">${esc(t('parents.ok'))}</button></div></div>
        <p class="backup-msg muted" role="status"></p></section>
      <section><h2>${esc(t('parents.credits'))}</h2><p class="muted">${esc(t('parents.photosNote'))}</p><ul class="credits">${credRows()}</ul></section>
      <section><p><a href="data/RESEARCH_NOTES.md" target="_blank" rel="noopener">${esc(t('parents.notes'))}</a></p></section>
      ${aboutSection()}
      <section class="reset"><h2>${esc(t('parents.reset'))}</h2><div class="reset-row"><button class="btn text-btn" data-act="reset">${esc(t('parents.reset'))}</button></div></section>
      ${store.persistent ? '' : `<p class="muted">${esc(t('parents.noStorage'))}</p>`}
    </article></div>`));
  const tn = root.querySelector('.turtle-name');
  tn.addEventListener('change', () => store.set('turtleName', tn.value.trim()));
  root.querySelector('input[type=file]').addEventListener('change', async (e) => {
    const f = e.target.files?.[0]; if (!f) return;
    root.querySelector('.import-text').value = await f.text();
  });
  askStatus();
}

function onSwMessage(e) {
  if (e.data?.type !== 'status' || !root) return;
  const el = root.querySelector('.offline-ready'); if (!el) return;
  const p = e.data.total ? Math.floor((100 * e.data.have) / e.data.total) : 0;
  el.classList.toggle('done', p >= 100);
  el.innerHTML = `<span>${esc(t('parents.offlineReady', { p }))}</span><span class="bar" aria-hidden="true"><i style="--p:${p}%"></i></span>`;
  clearTimeout(pollT);
  if (p < 100) pollT = setTimeout(askStatus, 1500);
}
async function askStatus() {
  const el = root?.querySelector('.offline-ready'); if (!el) return;
  const reg = 'serviceWorker' in navigator && window.isSecureContext ? await navigator.serviceWorker.getRegistration('./').catch(() => null) : null;
  const w = reg?.active || reg?.waiting || reg?.installing;
  if (!w) { el.textContent = t('parents.offlineNoSw'); return; }
  w.postMessage({ type: 'status' });
}

export function mount(el) { root = el; render(); el.addEventListener('click', onClick); navigator.serviceWorker?.addEventListener('message', onSwMessage); }
export function unmount() { clearTimeout(pollT); navigator.serviceWorker?.removeEventListener('message', onSwMessage); root = null; }

function msg(text) { const m = root.querySelector('.backup-msg'); if (m) m.textContent = text; }

async function onClick(e) {
  const b = e.target.closest('[data-act]'); if (!b) return;
  const a = b.dataset.act;
  if (a === 'home') { go('home'); return; }
  sound.play('tap');
  const keepScroll = () => { const y = root.querySelector('.sheet')?.scrollTop || 0; render(); const sh = root.querySelector('.sheet'); if (sh) sh.scrollTop = y; };
  if (a === 'level') { store.setLevel(Number(b.dataset.v)); store.markSeen('level2'); keepScroll(); }
  else if (a === 'lang') { setLang(b.dataset.v); keepScroll(); say('ui.safetyDive'); }
  else if (a === 'rate') { store.set('rate', b.dataset.v); keepScroll(); say('ui.safetyLook'); }
  else if (a === 'sound') { sound.setMuted(!store.isMuted()); keepScroll(); }
  else if (a === 'hair' || a === 'suit' || a === 'skin') { store.set(a, Number(b.dataset.v)); keepScroll(); }
  else if (a === 'export') {
    const blob = new Blob([store.exportText()], { type: 'application/json' });
    const url = URL.createObjectURL(blob); const link = document.createElement('a');
    link.href = url; link.download = `morsky-svet-zaloha-${new Date().toISOString().slice(0, 10)}.json`;
    document.body.append(link); link.click(); link.remove(); setTimeout(() => URL.revokeObjectURL(url), 2000);
  } else if (a === 'copy') {
    try { await navigator.clipboard.writeText(store.exportText()); msg(t('parents.copied')); } catch { root.querySelector('.import-box').hidden = false; root.querySelector('.import-text').value = store.exportText(); }
  } else if (a === 'import') { root.querySelector('.import-box').hidden = false; }
  else if (a === 'import-go') {
    const r = store.importText(root.querySelector('.import-text').value);
    if (r.ok) { keepScroll(); msg(t('parents.importOk')); } else msg(t('parents.importBad'));
  } else if (a === 'reset') {
    b.closest('.reset-row').innerHTML = `<span>${esc(t('parents.resetConfirm'))}</span><button class="btn text-btn danger" data-act="reset-yes">${esc(t('parents.yes'))}</button><button class="btn text-btn" data-act="reset-no">${esc(t('parents.no'))}</button>`;
  } else if (a === 'reset-yes') { store.reset(); render(); root.querySelector('.reset-row').innerHTML = `<span>${esc(t('parents.resetDone'))}</span>`; }
  else if (a === 'reset-no') keepScroll();
}
