// Mořský svět — levels (BRIEF §4.8): 1 „Malá potápěčka“, 2 „Potápěčka“. Automatic step-up after 10 discoveries.
import * as store from './store.js';
export const LEVEL2_AT = 10;
export const effectiveLevel = () => store.getLevel();
/** True exactly once: the child has just earned level 2 (call after a discovery). */
export function checkLevelUp() {
  if (store.getLevel() >= 2 || store.wasSeen('level2') || store.foundCount() < LEVEL2_AT) return false;
  store.setLevel(2); store.markSeen('level2');
  return true;
}
