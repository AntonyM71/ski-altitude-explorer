// Browser worker: runs the engine off the page's main thread (busyness-overlay). Message in:
// {id, structure: URL of the domain's structure file, params: URL of params.json}. Message out:
// {id, runs: {run id: {day, morning, evening}}, lifts: {lift id: {...}}, ms} with bands 0 quiet .. 3 busiest, or
// {id, error}. Lifts mapped in several pieces get their busiest piece's band.
import { run } from "./index.js";

async function json(url) {
  const r = await fetch(url);
  if (!r.ok) throw new Error(`couldn't load ${url} (${r.status})`);
  return r.json();
}

self.onmessage = async ({ data }) => {
  try {
    const [structure, P] = await Promise.all([json(data.structure), json(data.params)]);
    const t = performance.now();
    const r = run(structure, P);
    const lifts = {};
    for (const [key, band] of Object.entries(r.bands.lifts)) {
      const id = structure.lifts[key].id;
      const cur = lifts[id] || { day: 0, morning: 0, evening: 0 };
      for (const v of ["day", "morning", "evening"]) cur[v] = Math.max(cur[v], band[v]);
      lifts[id] = cur;
    }
    self.postMessage({ id: data.id, runs: r.bands.runs, lifts, ms: performance.now() - t });
  } catch (e) {
    self.postMessage({ id: data.id, error: String(e.message || e) });
  }
};
