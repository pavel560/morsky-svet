// Mořský svět — gentle 15-minute end (BRIEF §2): counts visible play time; the turtle yawns at the next pause
// (after the activity in progress finishes), once per session. Never forces anything.
export const TIRED_AFTER_MS = 15 * 60 * 1000;
let played = 0; let last = performance.now(); let shown = false;
function tick() {
  const now = performance.now();
  if (!document.hidden) played += Math.min(5000, now - last);
  last = now;
}
setInterval(tick, 1000);
document.addEventListener('visibilitychange', () => { last = performance.now(); });
export const playedMs = () => { tick(); return played; };
/** For tests and the parents' corner. */
export function _setPlayed(ms) { played = ms; shown = false; }
/** Call at a natural pause; true when it is time to suggest a break (once). */
export function tiredNow() {
  if (shown || playedMs() < TIRED_AFTER_MS) return false;
  shown = true; return true;
}
