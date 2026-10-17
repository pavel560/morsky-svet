// Renders icons/*.png from art/app-icon.svg (designer) with headless Chromium.
//   PLAYWRIGHT=<.../playwright/index.mjs> CHROME=<chrome> node dev/make_icons.mjs
import { fileURLToPath } from 'node:url';
import path from 'node:path';
import fs from 'node:fs';
const { chromium } = await import(process.env.PLAYWRIGHT || 'playwright');
const ROOT = path.join(path.dirname(fileURLToPath(import.meta.url)), '..');
const svg = fs.readFileSync(path.join(ROOT, 'art', 'app-icon.svg'), 'utf8');
const b = await chromium.launch({ executablePath: process.env.CHROME || undefined });
for (const [name, size, pad] of [['icon-192.png', 192, 0], ['icon-512.png', 512, 0], ['icon-maskable-512.png', 512, 0.1], ['apple-touch-icon.png', 180, 0]]) {
  const p = await b.newPage({ viewport: { width: size, height: size } });
  await p.setContent(`<body style="margin:0;width:${size}px;height:${size}px;overflow:hidden;background:#3a9fd6"><div style="position:absolute;inset:${pad * size}px">${svg.replace('<svg', '<svg width="100%" height="100%"')}</div></body>`);
  await p.screenshot({ path: path.join(ROOT, 'icons', name), omitBackground: false });
  await p.close();
}
await b.close();
console.log('icons written');
