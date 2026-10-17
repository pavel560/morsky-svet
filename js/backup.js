// Mořský svět — backup file validation (pure; unit-tested in tests/backup.test.mjs).
const MAX = 200000;
/** Parse a backup text. Accepts the export envelope { app, v, state } or a bare state object. */
export function validateBackup(text) {
  if (typeof text !== 'string' || !text.trim()) return { ok: false, reason: 'empty' };
  if (text.length > MAX) return { ok: false, reason: 'too-big' };
  let j;
  try { j = JSON.parse(text); } catch { return { ok: false, reason: 'not-json' }; }
  if (!j || typeof j !== 'object' || Array.isArray(j)) return { ok: false, reason: 'shape' };
  if (j.app !== undefined && j.app !== 'morsky-svet') return { ok: false, reason: 'other-app' };
  const st = j.state && typeof j.state === 'object' ? j.state : j;
  if (st.found !== undefined && (typeof st.found !== 'object' || Array.isArray(st.found))) return { ok: false, reason: 'shape' };
  const found = {};
  for (const [k, v] of Object.entries(st.found || {})) if (/^[a-z0-9-]{1,40}$/.test(k)) found[k] = typeof v === 'string' ? v.slice(0, 40) : new Date().toISOString();
  return { ok: true, state: { ...st, found } };
}
