// Mořský svět — pointer drag with a floating ghost; a short press without movement counts as a tap.
// Every drag target also works as „ťukni na předmět, pak na cíl“ (BRIEF §2) — callers implement the tap path.
export function pressDrag(e, el, { ghost, onTap, onDrop, onLong, longMs = 600, threshold = 12 } = {}) {
  const x0 = e.clientX; const y0 = e.clientY; const id = e.pointerId;
  let g = null; let longT = 0; let done = false;
  if (onLong) longT = setTimeout(() => { if (!g && !done) { done = true; cleanup(); onLong(); } }, longMs);
  const move = (ev) => {
    if (ev.pointerId !== id || done) return;
    if (!g && Math.hypot(ev.clientX - x0, ev.clientY - y0) > threshold) {
      clearTimeout(longT);
      g = ghost();
      g.classList.add('drag-ghost'); document.body.append(g);
      el.classList.add('dragging');
    }
    if (g) g.style.transform = `translate3d(${ev.clientX}px,${ev.clientY}px,0) translate(-50%,-50%)`;
  };
  const up = (ev) => {
    if (ev.pointerId !== id || done) return;
    done = true; cleanup();
    if (g) { g.remove(); el.classList.remove('dragging'); onDrop?.(ev.clientX, ev.clientY); } else if (ev.type === 'pointerup') onTap?.();
  };
  function cleanup() {
    clearTimeout(longT);
    removeEventListener('pointermove', move); removeEventListener('pointerup', up); removeEventListener('pointercancel', up);
  }
  addEventListener('pointermove', move); addEventListener('pointerup', up); addEventListener('pointercancel', up);
}
export const inside = (el, x, y) => { const r = el.getBoundingClientRect(); return x >= r.left && x <= r.right && y >= r.top && y <= r.bottom; };
