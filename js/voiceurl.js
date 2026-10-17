// Mořský svět — content-addressed voice URLs. A recording's URL carries the first 10 characters of its hash from
// voice/index.json (fetched network-first, so always fresh): a re-recorded line gets a NEW URL, so neither the
// CDN (GitHub Pages caches ~10 min) nor the service worker can ever serve the old bytes for it.
// sw.js repeats this rule (a classic worker cannot import modules): keep both in sync.
export const VOICE_HASH_LEN = 10;

/** 'voice/cs/ui.level.1.mp3?v=0123456789' for an index entry ({ file, sha1 }); no ?v= if the entry has no hash. */
export function voiceUrl(entry, base = 'voice/') {
  if (!entry || typeof entry.file !== 'string') return null;
  const v = typeof entry.sha1 === 'string' && entry.sha1 ? `?v=${encodeURIComponent(entry.sha1.slice(0, VOICE_HASH_LEN))}` : '';
  return `${base}${entry.file}${v}`;
}
