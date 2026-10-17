// Mořský svět — tiny screen router. Screens: { mount(root, params), unmount?() }.
import { hush, viewTransition } from './ui.js';

const screens = {};
let current = null;
let currentName = null;
export const register = (name, mod) => { screens[name] = mod; };
export const screenName = () => currentName;

export async function go(name, params = {}) {
  const root = document.getElementById('screen');
  hush();
  document.dispatchEvent(new CustomEvent('screen:leave', { detail: { from: currentName, to: name } }));
  document.documentElement.setAttribute('data-vt', '');
  await viewTransition(() => {
    current?.unmount?.();
    // A fresh host per screen: listeners a screen attaches die with it (no stacked handlers on #screen).
    const host = document.createElement('div');
    host.className = 'screen-host';
    root.replaceChildren(host);
    document.documentElement.dataset.screen = name;
    current = screens[name];
    currentName = name;
    current.mount(host, params);
  });
  document.documentElement.removeAttribute('data-vt');
}
