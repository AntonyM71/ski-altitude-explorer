#!/usr/bin/env node
// Run the engine on a structure file and print the busiest runs and lifts in each view.
//   node busyness-engine/bin/run.mjs data/busy/<domain id>.json [--top 12] [--json]
import { readFileSync } from "node:fs";
import { run } from "../src/index.js";

const args = process.argv.slice(2);
const file = args.find((a) => !a.startsWith("--"));
if (!file) {
  console.error("usage: node busyness-engine/bin/run.mjs <structure file> [--top N] [--json]");
  process.exit(2);
}
const top = Number(args[args.indexOf("--top") + 1]) || 12;
const P = JSON.parse(readFileSync(new URL("../src/params.json", import.meta.url), "utf8"));
const s = JSON.parse(readFileSync(file, "utf8"));
const t = performance.now();
const r = run(s, P);
const ms = performance.now() - t;
const GRADES = "GBRKU";

// Named runs as decision 011 compares them: runs sharing a name and grade (mapped in pieces) combined,
// length-weighted, then those over 300 m in all. Lifts that carry skiing.
const named = Object.entries(r.runs)
  .map(([id, x]) => ({ id, name: s.runs[id][0], grade: s.runs[id][1], ...x }))
  .filter((x) => x.name);
const byName = new Map();
for (const x of named) {
  const k = `${x.name}|${x.grade}`;
  const v = byName.get(k) || { name: x.name, grade: x.grade, len: 0, day: 0, morning: 0, evening: 0, commute: 0 };
  for (const f of ["day", "morning", "evening", "commute"]) v[f] += x[f] * x.len;
  v.len += x.len;
  byName.set(k, v);
}
const runs = [...byName.values()].filter((v) => v.len > 300).map((v) => ({ ...v, day: v.day / v.len,
  morning: v.morning / v.len, evening: v.evening / v.len, commute: v.commute / v.len }));
const lifts = Object.values(r.lifts).filter((l) => !l.nursery);

if (args.includes("--json")) {
  console.log(JSON.stringify({ domain: s.domain, ms, runs, lifts }));
} else {
  console.log(`${s.domain.name}: ${s.z.length} junctions, ${s.links.length} links; computed in ${Math.round(ms)} ms ` +
    `(${r.passes} routing pass${r.passes > 1 ? "es" : ""})`);
  for (const view of ["day", "morning", "evening"]) {
    console.log(`\n${view}: busiest runs (skiers an hour)`);
    runs.sort((a, b) => b[view] - a[view]).slice(0, top).forEach((x, i) =>
      console.log(`  ${String(i + 1).padStart(2)}. ${x.name} (${GRADES[x.grade]}) ${Math.round(x[view])}`));
    console.log(`${view}: busiest lifts (demand / capacity)`);
    lifts.sort((a, b) => b[view] - a[view]).slice(0, top).forEach((l, i) =>
      console.log(`  ${String(i + 1).padStart(2)}. ${l.name} ${l[view].toFixed(2)}x` +
        (view === "evening" && l.down ? ` (${Math.round(l.down)} an hour riding down)` : "")));
  }
}
