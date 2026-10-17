// Mořský svět — service worker registration. Works on https:// and http://localhost only;
// on the iPad over http://<Mac-IP>:8642 the game runs, just without offline caching. ?nosw unregisters + clears caches.
const OWN_CACHE = /^morsky-svet-v\d+$/;
export async function registerServiceWorker(url = './sw.js') {
  if (!('serviceWorker' in navigator) || !window.isSecureContext) return { ok: false, reason: 'insecure-or-unsupported' };
  try {
    if (new URLSearchParams(location.search).has('nosw')) {
      const scope = new URL('./', location.href).href;
      for (const r of await navigator.serviceWorker.getRegistrations()) if (r.scope === scope) await r.unregister();
      for (const k of await caches.keys()) if (OWN_CACHE.test(k)) await caches.delete(k);
      return { ok: false, reason: 'disabled-by-nosw' };
    }
    const reg = await navigator.serviceWorker.register(url, { scope: './' });
    return { ok: true, registration: reg };
  } catch (err) { return { ok: false, reason: String(err) }; }
}
