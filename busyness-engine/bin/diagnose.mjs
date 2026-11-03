#!/usr/bin/env node
// Diagnostics: run the engine on structure files and write SVG charts of the model's state to one HTML file.
//   node busyness-engine/bin/diagnose.mjs [structure files...] [--out data/diagnostics.html]
// With no files, it uses the four test domains (tests/fixtures/busyness/domains/). Open the file in a browser and hover
// for values.
import { readFileSync, readdirSync, writeFileSync, mkdirSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { run } from "../src/index.js";

const ROOT = join(dirname(fileURLToPath(import.meta.url)), "..", "..");
const args = process.argv.slice(2);
const outAt = args.indexOf("--out");
const out = outAt >= 0 ? args.splice(outAt, 2)[1] : join(ROOT, "data", "diagnostics.html");
const fixtures = join(ROOT, "tests", "fixtures", "busyness", "domains");
const files = args.length ? args : readdirSync(fixtures).filter((f) => f.endsWith(".json")).map((f) => join(fixtures, f));
const P = JSON.parse(readFileSync(new URL("../src/params.json", import.meta.url), "utf8"));

const VIEWS = [["day", "Day"], ["morning", "Morning"], ["evening", "Evening"]];
const BANDS = ["under 50%", "50–100%", "queue under 5 min", "queue 5 min+"];
const PURPLE = ["#8a6ad8", "#6a44c8", "#4a24a0", "#2a0d66"]; // the overlay's lift ramp (index.html)
const SERIES = { day: "#2a78d6", morning: "#eb6834", evening: "#1baf7a" }; // first three categorical slots
const esc = (s) => String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;");
const key = (items) => `<div>${items.map(([t, c]) => `<span class="key"><i style="background:${c}"></i>${esc(t)}</span>`).join("")}</div>`;

const domains = files.map((f) => {
  const s = JSON.parse(readFileSync(f, "utf8"));
  const t = performance.now();
  const r = run(s, P);
  const ms = performance.now() - t;
  const lifts = Object.entries(r.lifts).filter(([, l]) => !l.nursery)
    .map(([k, l]) => ({ name: l.name, wait: l.wait, band: r.bands.lifts[k] }));
  const runs = [];
  s.links.forEach((l, i) => {
    if (l.k === "run") runs.push({ z: (s.z[l.a] + s.z[l.b]) / 2, len: l.len, ...Object.fromEntries(VIEWS.map(([v]) => [v, r.links[v][i]])) });
  });
  console.log(`${s.domain.name}: ${Math.round(ms)} ms, ${r.passes} passes`);
  return { label: s.domain.name, lifts, runs, ms, passes: r.passes };
});

/** Lift bands by view: how many lifts fall in each overlay band. */
function bandsChart() {
  const W = 900, L = 200, bh = 18, gap = 4;
  let y = 6;
  const g = [];
  for (const d of domains) {
    g.push(`<text class="t" x="0" y="${y + 12}">${esc(d.label)}</text>`);
    y += 18;
    for (const [view, label] of VIEWS) {
      const counts = [0, 0, 0, 0];
      for (const l of d.lifts) if (l.band[view] != null) counts[l.band[view]]++;
      const n = counts.reduce((a, b) => a + b, 0);
      g.push(`<text x="${L - 8}" y="${y + 13}" text-anchor="end">${label} (${n} lifts)</text>`);
      let x = L;
      counts.forEach((c, b) => {
        const w = ((W - L) * c) / n;
        if (w > 0) {
          g.push(`<rect x="${x.toFixed(1)}" y="${y}" width="${Math.max(w - 2, 0.5).toFixed(1)}" height="${bh}" rx="3" fill="${PURPLE[b]}"><title>${esc(d.label)}, ${label}: ${BANDS[b]}: ${c} lifts</title></rect>`);
          if (w > 30) g.push(`<text x="${(x + 5).toFixed(1)}" y="${y + 13}" style="fill:#fff">${c}</text>`);
        }
        x += w;
      });
      y += bh + gap;
    }
    y += 14;
  }
  return key(BANDS.map((b, i) => [b, PURPLE[i]])) + `<svg width="${W}" height="${y}">${g.join("")}</svg>`;
}

/** Day waits at queued lifts, on a log scale, with the observed 20-minute reference. */
function waitsChart() {
  const W = 900, L = 170, R = 20, rowh = 72, top = 28;
  const lo = 0, hi = Math.log10(3000);
  const sx = (m) => L + ((Math.log10(Math.max(m, 1)) - lo) / (hi - lo)) * (W - L - R);
  const H = top + rowh * domains.length;
  const g = [];
  for (const t of [1, 3, 10, 30, 100, 300, 1000, 3000]) {
    g.push(`<line x1="${sx(t)}" x2="${sx(t)}" y1="${top}" y2="${H}" stroke="#e4e3df"/><text x="${sx(t)}" y="${H + 16}" text-anchor="middle">${t}</text>`);
  }
  g.push(`<line x1="${sx(20)}" x2="${sx(20)}" y1="${top - 6}" y2="${H}" stroke="#eb6834" stroke-width="2" stroke-dasharray="4 3"/>`);
  g.push(`<text x="${sx(20) + 6}" y="${top - 10}" style="fill:#0b0b0b">20 min: the longest queue the owner has seen at Cucumelle</text>`);
  domains.forEach((d, k) => {
    const y = top + k * rowh + rowh / 2 + 6;
    const queued = d.lifts.filter((l) => l.wait.day >= 30).sort((a, b) => b.wait.day - a.wait.day);
    g.push(`<text class="lab" x="${L - 10}" y="${y}" text-anchor="end">${esc(d.label)}</text><text x="${L - 10}" y="${y + 14}" text-anchor="end">${queued.length} of ${d.lifts.length} queued</text>`);
    queued.forEach((l, j) => {
      const m = l.wait.day / 60;
      g.push(`<circle cx="${sx(m).toFixed(1)}" cy="${(y + ((j % 5) - 2) * 5).toFixed(1)}" r="4" fill="#2a78d6" fill-opacity=".55" stroke="#fcfcfb"><title>${esc(l.name)}: ${Math.round(m)} min by day</title></circle>`);
    });
    queued.slice(0, 2).forEach((l, j) => {
      g.push(`<text x="${sx(l.wait.day / 60).toFixed(1)}" y="${y - 16 - 12 * j}" text-anchor="end">${esc(l.name)} ${Math.round(l.wait.day / 60)}</text>`);
    });
  });
  g.push(`<text x="${(W + L) / 2}" y="${H + 34}" text-anchor="middle">modelled day wait beyond loading, minutes (log scale)</text>`);
  return `<svg width="${W}" height="${H + 42}">${g.join("")}</svg>`;
}

/** Share of each view's run traffic (skier-metres an hour) in each 100 m altitude band, one panel per domain. */
function altitudeChart() {
  const PW = 430, PH = 230, ml = 46, mb = 34, mt = 24;
  const panels = domains.map((d) => {
    const bins = new Map();
    for (const r of d.runs) {
      const b = Math.floor(r.z / 100) * 100;
      const cur = bins.get(b) || { day: 0, morning: 0, evening: 0 };
      for (const [v] of VIEWS) cur[v] += r[v] * r.len;
      bins.set(b, cur);
    }
    const zs = [...bins.keys()].sort((a, b) => a - b);
    const share = Object.fromEntries(VIEWS.map(([v]) => {
      const tot = zs.reduce((a, z) => a + bins.get(z)[v], 0);
      return [v, zs.map((z) => (100 * bins.get(z)[v]) / tot)];
    }));
    const ymax = Math.ceil(Math.max(...Object.values(share).flat()) / 5) * 5;
    const x0 = zs[0], x1 = zs[zs.length - 1] + 100;
    const sx = (z) => ml + ((z + 50 - x0) / (x1 - x0)) * (PW - ml - 10);
    const sy = (v) => PH - mb - (v / ymax) * (PH - mb - mt);
    const g = [`<text class="t" x="${ml}" y="15">${esc(d.label)}</text>`];
    for (let t = 0; t <= ymax; t += ymax <= 30 ? 5 : 10) {
      g.push(`<line x1="${ml}" x2="${PW - 10}" y1="${sy(t)}" y2="${sy(t)}" stroke="#e4e3df"/><text x="${ml - 6}" y="${sy(t) + 4}" text-anchor="end">${t}%</text>`);
    }
    const step = x1 - x0 > 1500 ? 500 : 200;
    for (let z = Math.ceil(x0 / step) * step; z <= x1; z += step) {
      g.push(`<text x="${sx(z - 50).toFixed(1)}" y="${PH - mb + 16}" text-anchor="middle">${z.toLocaleString("en")} m</text>`);
    }
    for (const [v, label] of VIEWS) {
      const path = zs.map((z, i) => `${i ? "L" : "M"}${sx(z).toFixed(1)},${sy(share[v][i]).toFixed(1)}`).join(" ");
      g.push(`<path d="${path}" fill="none" stroke="${SERIES[v]}" stroke-width="2"/>`);
      zs.forEach((z, i) => g.push(`<circle cx="${sx(z).toFixed(1)}" cy="${sy(share[v][i]).toFixed(1)}" r="6" fill="transparent"><title>${label}: ${share[v][i].toFixed(1)}% of run traffic at ${z}–${z + 100} m</title></circle>`));
    }
    return `<svg width="${PW}" height="${PH}">${g.join("")}</svg>`;
  });
  return key(VIEWS.map(([v, l]) => [l, SERIES[v]])) + `<div style="display:flex;flex-wrap:wrap;gap:16px">${panels.join("")}</div>`;
}

const CSS = `body{margin:0;background:#fcfcfb;color:#0b0b0b;font:14px system-ui,sans-serif}
.wrap{padding:20px 28px;max-width:1100px} h1{font-size:20px;margin:0 0 4px} h2{font-size:16px;margin:28px 0 2px}
p{color:#52514e;margin:0 0 10px;max-width:900px} svg text{fill:#52514e;font-size:11px} svg .lab{fill:#0b0b0b;font-size:12px}
svg .t{fill:#0b0b0b;font-size:13px;font-weight:600} .key{display:inline-flex;align-items:center;gap:6px;margin-right:14px;font-size:12px}
.key i{width:12px;height:12px;border-radius:3px;display:inline-block}`;
const runInfo = domains.map((d) => `${esc(d.label)} ${(d.ms / 1000).toFixed(1)} s (${d.passes} passes)`).join(", ");
const html = `<!DOCTYPE html><html><head><meta charset="utf-8"><title>Busyness diagnostics</title><style>${CSS}</style></head><body>
<div class="wrap"><h1>Busyness diagnostics</h1><p>${new Date().toISOString().slice(0, 16).replace("T", " ")}. Engine runs: ${runInfo}. Hover for values.</p>
<h2>Lift bands by view</h2><p>How many lifts fall in each overlay band.</p>${bandsChart()}
<h2>Day waits at queued lifts</h2><p>Every lift with a day queue, by its modelled wait. Waits beyond about an hour grow every pass at lifts skiers can't avoid, and aren't real.</p>${waitsChart()}
<h2>Run traffic by altitude</h2><p>Share of each view's run traffic (skier-metres an hour) in each 100 m band.</p>${altitudeChart()}</div></body></html>`;
mkdirSync(dirname(out), { recursive: true });
writeFileSync(out, html);
console.log(`wrote ${out}`);
