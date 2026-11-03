// The busyness engine: from a domain's structure file to traffic in the day, morning and evening views, by simulating
// the day (busyness-day-simulation; docs/decisions/017).
import { network } from "./graph.js";
import { sectorEnds, gravity } from "./demand.js";
import { simulate } from "./simulate.js";
import { summarise, bands } from "./views.js";
import { checkShares, checkTraffic, EngineError } from "./checks.js";

export { EngineError };

/**
 * Run the model on a structure file.
 * @param {object} structure  a structure file (busyness-pipeline)
 * @param {object} P  the behaviour constants (src/params.json)
 * @returns {{links: object, runs: object, lifts: object, bands: object, demand: object, ms: object,
 *   waits: {day: Float64Array, morning: Float64Array, evening: Float64Array}, report: object}}
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
  const ends = sectorEnds(net);
  const demand = gravity(net, P, ends, new Float64Array(net.L.length));
  lap("demand");
  const { views, commute, arrivals, waits, report } = simulate(net, P, { demand, ends });
  lap("simulation");
  const links = { day: views.day, morning: views.morning, evening: views.evening, commute: commute.day,
    out: commute.morning, back: commute.evening };
  checkTraffic(links, net.L);
  const summary = summarise(net, { ...views, commute: commute.day }, arrivals, waits);
  const banded = bands(summary, P);
  lap("views");
  return { links, runs: summary.runs, lifts: summary.lifts, bands: banded, demand, ms, waits, report };
}
