// The busyness engine: from a domain's structure file to traffic in the day, morning and evening views.
import { network } from "./graph.js";
import { laps as computeLaps } from "./laps.js";
import { sectorEnds, gravity } from "./demand.js";
import { routeWithRidesDown } from "./evening.js";
import { linkViews, summarise, bands } from "./views.js";
import { checkShares, checkTraffic, EngineError } from "./checks.js";

export { EngineError };

/**
 * Run the model on a structure file.
 * @param {object} structure  a structure file (busyness-pipeline)
 * @param {object} P  the behaviour constants (src/params.json)
 * @returns {{links: object, runs: object, lifts: object, bands: object, ms: object, passes: number}}
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
  const { laps, liftLaps } = computeLaps(net, P);
  lap("laps");
  const ends = sectorEnds(net);
  const demand = gravity(net, P, ends, laps);
  lap("demand");
  const routed = routeWithRidesDown(net, P, { laps, demand, ends });
  lap("routing");
  const views = linkViews(net, P, { laps, liftLaps, routed });
  checkTraffic({ laps, out: routed.out, back: routed.back, ...views }, net.L);
  const summary = summarise(net, views, liftLaps);
  const banded = bands(summary, P);
  lap("views");
  return {
    links: { laps, out: routed.out, back: routed.back, ...views },
    runs: summary.runs,
    lifts: summary.lifts,
    bands: banded,
    demand,
    ms,
    passes: routed.passes,
  };
}
