// Tiny test harness (no dependencies): t(name, fn) collects; done(label) prints and sets the exit code.
let pass = 0; const fails = [];
export function t(name, cond, extra = '') { if (cond) pass++; else fails.push(`FAIL ${name}${extra ? ` — ${extra}` : ''}`); }
export function done(label) {
  for (const f of fails) console.log(f);
  console.log(`${label}: ${pass}/${pass + fails.length} passed`);
  process.exit(fails.length ? 1 : 0);
}
