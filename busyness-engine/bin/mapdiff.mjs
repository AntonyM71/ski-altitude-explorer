#!/usr/bin/env node
// Maps of the busyness overlay before and after an engine change, side by side, as the site draws them: runs by band
// within the domain, lifts by load band, labelled where they queue. Writes one HTML file; hover for values.
//   node busyness-engine/bin/mapdiff.mjs [--base dir] [--out data/mapdiff.html] [--set KEY=VALUE,...] [domain names...]
// --base is a copy of busyness-engine/src to compare against; without it, the last commit's engine is exported from
// git. --set overrides params.json values for "after", to trial a setting. With no names, the four test domains
// (tests/fixtures/busyness/domains/).
import { readFileSync, readdirSync, writeFileSync, mkdirSync, rmSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";
import { execSync } from "node:child_process";
import { tmpdir } from "node:os";

const ROOT = join(dirname(fileURLToPath(import.meta.url)), "..", "..");
const args = process.argv.slice(2);
const opt = (name) => {
  const at = args.indexOf(name);
  return at >= 0 ? args.splice(at, 2)[1] : null;
};
const out = opt("--out") || join(ROOT, "data", "mapdiff.html");
const set = Object.fromEntries((opt("--set") || "").split(",").filter(Boolean).map((kv) => [kv.split("=")[0], Number(kv.split("=")[1])]));
let base = opt("--base");
let cleanup = null;
if (!base) {
  const dir = join(tmpdir(), `mapdiff-${process.pid}`);
  base = join(dir, "src");
  mkdirSync(base, { recursive: true });
  for (const f of execSync("git ls-tree --name-only HEAD busyness-engine/src/", { cwd: ROOT }).toString().split("\n").filter(Boolean)) {
    writeFileSync(join(base, f.split("/").pop()), execSync(`git show HEAD:${f}`, { cwd: ROOT }));
  }
  cleanup = dir;
}
const engine = async (src) => ({
  ...(await import(pathToFileURL(join(src, "index.js")).href)),
  ...(await import(pathToFileURL(join(src, "views.js")).href)),
  P: JSON.parse(readFileSync(join(src, "params.json"), "utf8")),
});
const before = await engine(base);
const after = await engine(join(ROOT, "busyness-engine", "src"));
Object.assign(after.P, set);
const setText = Object.entries(set).map(([k, v]) => `${k} = ${v}`).join(", ");
const commit = execSync("git log -1 --format=%h", { cwd: ROOT }).toString().trim();

const fixtures = join(ROOT, "tests", "fixtures", "busyness", "domains");
const structures = readdirSync(fixtures).map((f) => JSON.parse(readFileSync(join(fixtures, f), "utf8")));
const chosen = args.length ? structures.filter((s) => args.includes(s.domain.name)) : structures;

const VIEWS = [["day", "Day"], ["morning", "Morning"], ["evening", "Evening"]];
const RUN = ["#7f93a6", "#ffd166", "#f77f00", "#e3263a"]; // the site's run bands: quiet, moderate, busy, busiest
const LIFT = ["#8a6ad8", "#6a44c8", "#4a24a0", "#2a0d66"]; // the site's lift bands
const LIFT_NAMES = ["under 50%", "50–100%", "queue under 5 min", "queue 5 min+"];
const esc = (s) => String(s ?? "").replace(/&/g, "&amp;").replace(/</g, "&lt;");

function panel(s, geo, res, view, W) {
  const pts = [...geo.runs, ...geo.lifts].flatMap((f) => f.c.flat());
  const lat0 = pts.reduce((a, p) => a + p[1], 0) / pts.length;
  const kx = Math.cos((lat0 * Math.PI) / 180);
  const xs = pts.map((p) => p[0] * kx), ys = pts.map((p) => p[1]);
  const [x0, x1, y0, y1] = [Math.min(...xs), Math.max(...xs), Math.min(...ys), Math.max(...ys)];
  const k = (W - 20) / (x1 - x0);
  const H = Math.round((y1 - y0) * k + 20);
  const xy = (p) => `${((p[0] * kx - x0) * k + 10).toFixed(1)},${((y1 - p[1]) * k + 10).toFixed(1)}`;
  const path = (c) => c.map((line) => "M" + line.map(xy).join("L")).join("");
  const g = [];
  for (const r of geo.runs) {
    const b = res.runs[r.i]?.[view];
    const col = b == null ? "#c9ccd1" : RUN[b];
    g.push(`<path d="${path(r.c)}" stroke="${col}" stroke-width="${b == null ? 1 : 1.6 + b * 0.5}" fill="none"><title>${esc(r.n || "unnamed run")} (${esc(r.d)}): ${b == null ? "no band" : ["quiet", "moderate", "busy", "busiest"][b]}</title></path>`);
  }
  const labels = [];
  for (const l of geo.lifts) {
    const [b, load, wait] = res.lifts[l.i]?.[view] || [];
    const col = b == null ? "#9a9aa0" : LIFT[b];
    const min = Math.round((wait || 0) / 60);
    g.push(`<path d="${path(l.c)}" stroke="#fff" stroke-width="${b == null ? 2 : 4.5}" fill="none"/><path d="${path(l.c)}" stroke="${col}" stroke-width="${b == null ? 1 : 2.6}" fill="none"><title>${esc(l.n || "unnamed lift")}: ${load == null ? "nursery" : `${Math.round(load * 100)}% of capacity`}${min ? `, ${min} min queue` : ""}</title></path>`);
    if (min >= 5) {
      const [x, y] = xy(l.c[0][0]).split(",");
      labels.push(`<text x="${x}" y="${+y - 4}" class="q">${esc(l.n)} ${min}′</text>`);
    }
  }
  // Villages, at the bottom of a lift leaving them, for orientation.
  const byId = new Map(geo.lifts.map((l) => [l.i, l]));
  for (const v of s.villages) {
    const link = s.links.find((x) => x.k === "lift" && x.a === v.nodes[0][0]);
    const l = link && byId.get(s.lifts[link.lift].id);
    if (!l) continue;
    const ends = [l.c[0][0], l.c[l.c.length - 1].at(-1)];
    const [x, y] = xy(ends[0][2] <= ends[1][2] ? ends[0] : ends[1]).split(",");
    labels.push(`<circle cx="${x}" cy="${y}" r="3" fill="#0b0b0b"/><text x="${+x + 5}" y="${+y + 12}" class="v">${esc(v.name)}</text>`);
  }
  return `<svg width="${W}" height="${H}" viewBox="0 0 ${W} ${H}">${g.join("")}${labels.join("")}</svg>`;
}

function changes(s, geo, a, b, view) {
  const rows = [];
  for (const l of geo.lifts) {
    const pa = a.lifts[l.i]?.[view], pb = b.lifts[l.i]?.[view];
    if (!pa || !pb || pa[1] == null) continue;
    rows.push({ n: l.n, from: pa[1], to: pb[1], wa: pa[2] / 60, wb: pb[2] / 60 });
  }
  rows.sort((x, y) => Math.abs(y.to - y.from) - Math.abs(x.to - x.from));
  return rows.slice(0, 10).map((r) => `<li>${esc(r.n)}: ${Math.round(r.from * 100)}% → <b>${Math.round(r.to * 100)}%</b>${r.wa >= 1 || r.wb >= 1 ? ` (queue ${Math.round(r.wa)} → ${Math.round(r.wb)} min)` : ""}</li>`).join("");
}

const sections = [];
for (const s of chosen) {
  const geo = JSON.parse(readFileSync(join(ROOT, "data", "runs", `${s.domain.id}.json`), "utf8"));
  const run = (e) => {
    const r = e.run(s, e.P);
    return { runs: r.bands.runs, lifts: e.liftsForSite(s, r) };
  };
  const a = run(before), b = run(after);
  console.log(`${s.domain.name}: rendered`);
  const W = 640;
  const views = VIEWS.map(([v, label]) => `<h3>${label}</h3><div class="pair"><div><p>Before (${commit})</p>${panel(s, geo, a, v, W)}</div><div><p>After (working copy${setText ? `, ${setText}` : ""})</p>${panel(s, geo, b, v, W)}</div><div class="ch"><p>Biggest lift changes</p><ul>${changes(s, geo, a, b, v)}</ul></div></div>`).join("");
  sections.push(`<section><h2>${esc(s.domain.name)}</h2>${views}</section>`);
}

const key = (cols, names) => cols.map((c, i) => `<span class="key"><i style="background:${c}"></i>${names[i]}</span>`).join("");
const html = `<!DOCTYPE html><html><head><meta charset="utf-8"><title>Busyness: before and after</title><style>
body{margin:0;background:#fcfcfb;color:#0b0b0b;font:14px system-ui,sans-serif} .wrap{padding:16px 24px}
h1{font-size:20px;margin:0 0 4px} h2{font-size:17px;margin:28px 0 0} h3{font-size:14px;margin:14px 0 4px;color:#52514e}
.pair{display:flex;gap:14px;align-items:flex-start;flex-wrap:wrap} .pair p{margin:0 0 2px;font-size:12px;color:#52514e}
svg{background:#f1f2ef;border-radius:6px} .v{font-size:11px;fill:#0b0b0b;paint-order:stroke;stroke:#f1f2ef;stroke-width:3px} svg path:hover{stroke-width:6} .q{font-size:11px;fill:#2a0d66;font-weight:600;paint-order:stroke;stroke:#fff;stroke-width:3px}
.ch ul{margin:0;padding-left:18px;font-size:12px;max-width:260px} .key{display:inline-flex;align-items:center;gap:5px;margin-right:12px;font-size:12px}
.key i{width:12px;height:12px;border-radius:3px;display:inline-block}</style></head><body><div class="wrap">
<h1>Busyness overlay: before and after</h1><p>Before: engine at ${commit}. After: the working copy. Runs are banded within each domain, so a run can change colour because others moved. Lifts labelled with their queue where it's 5 minutes or more. Hover for values.</p>
<div>Runs: ${key(RUN, ["quiet", "moderate", "busy", "busiest"])} Lifts: ${key(LIFT, LIFT_NAMES)}</div>
${sections.join("")}</div></body></html>`;
mkdirSync(dirname(out), { recursive: true });
writeFileSync(out, html);
if (cleanup) rmSync(cleanup, { recursive: true, force: true });
console.log(`wrote ${out}`);
