// Mořský svět — tiny Web Audio synth for UI sounds (no audio files).
// play('pop' | 'boing' | 'success' | 'tryAgain' | 'sparkle' | 'tap' | 'whoosh')
// The AudioContext is created on the first user gesture (avoids autoplay warnings; unlocks iOS).
import * as store from './store.js';

let ctx = null;
let master = null;
let noiseBuf = null;

const Ctx = typeof window !== 'undefined' ? (window.AudioContext || window.webkitAudioContext) : null;
export const isSupported = () => !!Ctx;

function ensure() {
  if (ctx || !Ctx) return ctx;
  try {
    ctx = new Ctx({ latencyHint: 'interactive' });
    const comp = ctx.createDynamicsCompressor();
    comp.threshold.value = -14; comp.ratio.value = 4;
    master = ctx.createGain();
    master.gain.value = 0.55;
    master.connect(comp).connect(ctx.destination);
  } catch { ctx = null; }
  return ctx;
}

/** Create/resume the audio context. Must run inside a user gesture the first time (done automatically). */
export function unlock() {
  const c = ensure();
  if (c && c.state !== 'running') c.resume().catch(() => {});
  return c;
}

export const isMuted = () => store.isMuted();
export function setMuted(m) {
  store.setMuted(!!m);
  window.dispatchEvent(new CustomEvent('sound:mute', { detail: { muted: !!m } }));
}
export function toggleMute() { setMuted(!isMuted()); return isMuted(); }

// ---------------------------------------------------------------- building blocks
function env(gainNode, t, peak, attack, decay) {
  const g = gainNode.gain;
  g.cancelScheduledValues(t);
  g.setValueAtTime(0.0001, t);
  g.exponentialRampToValueAtTime(peak, t + attack);
  g.exponentialRampToValueAtTime(0.0001, t + attack + decay);
}

function tone({ type = 'sine', freq, to, glide = 0.1, t, peak = 0.5, attack = 0.005, decay = 0.2, pan = 0, dest = master }) {
  const o = ctx.createOscillator();
  const g = ctx.createGain();
  o.type = type;
  o.frequency.setValueAtTime(freq, t);
  if (to) o.frequency.exponentialRampToValueAtTime(to, t + glide);
  env(g, t, peak, attack, decay);
  let node = o.connect(g);
  if (pan && ctx.createStereoPanner) { const p = ctx.createStereoPanner(); p.pan.value = pan; node = node.connect(p); }
  node.connect(dest);
  o.start(t);
  o.stop(t + attack + decay + 0.05);
  return o;
}

function noise() {
  if (noiseBuf) return noiseBuf;
  noiseBuf = ctx.createBuffer(1, ctx.sampleRate * 0.5, ctx.sampleRate);
  const d = noiseBuf.getChannelData(0);
  for (let i = 0; i < d.length; i++) d[i] = Math.random() * 2 - 1;
  return noiseBuf;
}

// ---------------------------------------------------------------- the sounds
const SOUNDS = {
  pop(t) {
    tone({ freq: 880, to: 220, glide: 0.07, t, peak: 0.6, decay: 0.09 });
    tone({ type: 'triangle', freq: 1760, to: 600, glide: 0.04, t, peak: 0.15, decay: 0.05 });
  },
  tap(t) {
    tone({ type: 'triangle', freq: 660, to: 520, glide: 0.03, t, peak: 0.25, decay: 0.05 });
  },
  boing(t) {
    const o = ctx.createOscillator();
    const g = ctx.createGain();
    const lfo = ctx.createOscillator();
    const depth = ctx.createGain();
    o.type = 'triangle';
    o.frequency.setValueAtTime(160, t);
    o.frequency.exponentialRampToValueAtTime(420, t + 0.12);
    o.frequency.exponentialRampToValueAtTime(260, t + 0.5);
    lfo.frequency.setValueAtTime(18, t);
    lfo.frequency.linearRampToValueAtTime(7, t + 0.5);
    depth.gain.setValueAtTime(60, t);
    depth.gain.exponentialRampToValueAtTime(2, t + 0.55);
    lfo.connect(depth).connect(o.frequency);
    env(g, t, 0.5, 0.01, 0.55);
    o.connect(g).connect(master);
    o.start(t); lfo.start(t);
    o.stop(t + 0.62); lfo.stop(t + 0.62);
  },
  success(t) {
    // C major arpeggio, bell-like (sine + quiet octave triangle)
    [523.25, 659.25, 783.99, 1046.5].forEach((f, i) => {
      const at = t + i * 0.09;
      const last = i === 3;
      tone({ freq: f, t: at, peak: 0.42, attack: 0.008, decay: last ? 0.9 : 0.45 });
      tone({ type: 'triangle', freq: f * 2, t: at, peak: 0.08, attack: 0.008, decay: last ? 0.6 : 0.3 });
    });
  },
  tryAgain(t) {
    // gentle "hmm-mm": two soft descending notes with a slight wobble — never harsh
    [[392, 0], [329.63, 0.22]].forEach(([f, dt]) => {
      const o = ctx.createOscillator();
      const g = ctx.createGain();
      const lfo = ctx.createOscillator();
      const depth = ctx.createGain();
      o.type = 'sine';
      o.frequency.setValueAtTime(f, t + dt);
      o.frequency.linearRampToValueAtTime(f * 0.97, t + dt + 0.3);
      lfo.frequency.value = 7; depth.gain.value = 6;
      lfo.connect(depth).connect(o.frequency);
      env(g, t + dt, 0.3, 0.04, 0.32);
      o.connect(g).connect(master);
      o.start(t + dt); lfo.start(t + dt);
      o.stop(t + dt + 0.42); lfo.stop(t + dt + 0.42);
    });
  },
  sparkle(t) {
    const notes = [1567.98, 2093, 2349.32, 2637.02, 3135.96, 2793.83];
    for (let i = 0; i < 7; i++) {
      const f = notes[Math.floor(Math.random() * notes.length)];
      tone({ freq: f, t: t + i * 0.055 + Math.random() * 0.02, peak: 0.16, attack: 0.003, decay: 0.22, pan: Math.random() * 1.4 - 0.7 });
    }
  },
  bell(t) {
    // low, soft, slow bell — a calm "listen carefully", never an alarm
    [[196, 0.34, 1.6], [392, 0.10, 1.1], [588, 0.05, 0.8]].forEach(([f, peak, decay]) =>
      tone({ freq: f, t, peak, attack: 0.01, decay }));
  },
  hop(t) {
    // soft little footsteps of an animal running across the trail
    [0, 0.11, 0.22].forEach((dt, i) => tone({ type: 'triangle', freq: 330 - i * 30, to: 220, glide: 0.05, t: t + dt, peak: 0.14, attack: 0.004, decay: 0.07 }));
  },
  bubble(t) {
    // two soft rising bloops — a creature answering, a bubble popping
    [[340, 0], [520, 0.07]].forEach(([f, dt]) => tone({ freq: f, to: f * 1.9, glide: 0.09, t: t + dt, peak: 0.22, attack: 0.004, decay: 0.11 }));
  },
  splash(t) {
    const src = ctx.createBufferSource();
    src.buffer = noise();
    const lp = ctx.createBiquadFilter();
    lp.type = 'lowpass';
    lp.frequency.setValueAtTime(2600, t);
    lp.frequency.exponentialRampToValueAtTime(300, t + 0.5);
    const g = ctx.createGain();
    env(g, t, 0.3, 0.02, 0.5);
    src.connect(lp).connect(g).connect(master);
    src.start(t); src.stop(t + 0.55);
  },
  chime(t) {
    // the deep: one low, slow, glassy note — magical, not scary
    [[523.25, 0.18, 1.8], [784, 0.07, 1.4]].forEach(([f, peak, decay]) => tone({ freq: f, t, peak, attack: 0.05, decay }));
  },
  whoosh(t) {
    const src = ctx.createBufferSource();
    src.buffer = noise();
    const bp = ctx.createBiquadFilter();
    bp.type = 'bandpass'; bp.Q.value = 1.2;
    bp.frequency.setValueAtTime(400, t);
    bp.frequency.exponentialRampToValueAtTime(2400, t + 0.25);
    const g = ctx.createGain();
    env(g, t, 0.35, 0.06, 0.22);
    src.connect(bp).connect(g).connect(master);
    src.start(t); src.stop(t + 0.32);
  },
};

export const SOUND_NAMES = Object.keys(SOUNDS);

/** Play a named UI sound. Silently does nothing if muted, unsupported, or before the first gesture. */
export function play(name) {
  if (isMuted() || !SOUNDS[name]) return false;
  const c = ensure();
  if (!c) return false;
  if (c.state !== 'running') c.resume().catch(() => {});
  try { SOUNDS[name](c.currentTime + 0.01); return true; } catch { return false; }
}

export const pop = () => play('pop');
export const tap = () => play('tap');
export const boing = () => play('boing');
export const success = () => play('success');
export const tryAgain = () => play('tryAgain');
export const sparkle = () => play('sparkle');
export const whoosh = () => play('whoosh');
export const bell = () => play('bell');
export const hop = () => play('hop');
export const bubble = () => play('bubble');

// Unlock on user activations; keep listening because iOS suspends ("interrupted") after backgrounding.
if (typeof window !== 'undefined' && Ctx) {
  const onGesture = () => { if (!ctx || ctx.state !== 'running') unlock(); };
  ['pointerup', 'touchend', 'click', 'keydown'].forEach((ev) => window.addEventListener(ev, onGesture, { capture: true, passive: true }));
}
