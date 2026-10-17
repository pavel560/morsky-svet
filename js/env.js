// Mořský svět — where this copy runs (derived from the module URL; no build step).
/** App root path, e.g. '/morsky-svet/' */
export const BASE_PATH = new URL('../', import.meta.url).pathname;
/** localStorage key for progress (BRIEF §8). */
export const STORE_KEY = 'morsky-svet.v1';
/** Cache-name prefix shared with sw.js. */
export const CACHE_PREFIX = 'morsky-svet-';
