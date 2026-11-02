// The busyness engine: from a domain's structure file to traffic in the day, morning and evening views.
import { network } from "./graph.js";
import { dayWaits } from "./queues.js";
import { sectorEnds, gravity } from "./demand.js";
import { routeWithRidesDown } from "./evening.js";
import { linkViews, summarise, bands, rushWaits } from "./views.js";
import { checkShares, checkTraffic, EngineError } from "./checks.js";

export { EngineError };

/**
 * Run the model on a structure file.
 * @param {object} structure  a structure file (busyness-pipeline)
 * @param {object} P  the behaviour constants (src/params.json)
 * @returns {{links: object, runs: object, lifts: object, bands: object, ms: object, passes: number,
 *   waits: {day: Float64Array, morning: Float64Array, evening: Float64Array}}}
 */
export function run(structure, P) {
  const ms = {};
  let t0 = performance.now();
  const lap = (name) => {
    const t = performance.now();
    ms[name] = t - t0;
    t0 = t;
  };
  checkShares(structure);
  const net = network(structure);
  // Day: laps, with each overfull lift's wait and queues seen ahead (busyness-queues).
  const day = dayWaits(net, P);
  const { laps, liftLaps } = day;
  lap("laps");
  const ends = sectorEnds(net);
  const demand = gravity(net, P, ends, laps);
  lap("demand");
  // Rushes: route with the current rush waits, and average each pass's routes with all before it (the method of
  // successive averages, as in traffic assignment), so commuters settle where none gains by switching. Rush waits
  // come from the averaged views; stop once no wait moves over 30 s.
  let waits = { morning: new Float64Array(net.L.length), evening: new Float64Array(net.L.length) };
  let routed;
  let views;
  let passes = 0;
  for (let pass = 1; pass <= P.QUEUE_PASSES; pass++) {
    passes++;
    const r = routeWithRidesDown(net, P, { laps, demand, ends, waits });
    if (!routed) routed = r;
    else for (const k of ["out", "back", "evening"]) for (let i = 0; i < net.L.length; i++) routed[k][i] += (r[k][i] - routed[k][i]) / pass;
    views = linkViews(net, P, { laps, liftLaps, routed });
    const next = rushWaits(net, P, views);
    let moved = 0;
    for (const v of ["morning", "evening"]) {
      for (let i = 0; i < net.L.length; i++) moved = Math.max(moved, Math.abs(next[v][i] - waits[v][i]));
    }
    waits = next;
    if (moved <= 30) break;
  }
  lap("routing");
  checkTraffic({ laps, out: routed.out, back: routed.back, ...views }, net.L);
  const summary = summarise(net, views, liftLaps, { day: day.wait, ...waits });
  const banded = bands(summary, P);
  lap("views");
  return {
    links: { laps, out: routed.out, back: routed.back, ...views },
    runs: summary.runs,
    lifts: summary.lifts,
    bands: banded,
    demand,
    ms,
    passes,
    waits: { day: day.wait, ...waits },
  };
}
