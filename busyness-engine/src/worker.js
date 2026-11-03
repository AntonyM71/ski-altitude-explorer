// Browser worker: runs the engine off the page's main thread (busyness-overlay). Message in:
// {id, structure: URL of the domain's structure file, params: URL of params.json}. Message out:
// {id, runs: {run id: {day, morning, evening}}, lifts: {lift id: {day: [band, load], ...}}, ms}, or {id, error}.
// Runs have bands 0 quiet .. 3 busiest within the domain; lifts a load band (0 under 50% .. 3 over capacity, null for
// nursery lifts) and their load, demand / capacity, from their most loaded piece (views.js liftsForSite).
import { run } from "./index.js";
import { liftsForSite } from "./views.js";

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
    self.postMessage({ id: data.id, runs: r.bands.runs, lifts: liftsForSite(structure, r), ms: performance.now() - t });
  } catch (e) {
    self.postMessage({ id: data.id, error: String(e.message || e) });
  }
};
