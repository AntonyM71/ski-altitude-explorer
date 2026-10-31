// Laps: lapping skiers spread downhill from each lift's top, splitting at junctions by pull, until a lift takes them
// (busyness-laps; docs/decisions/006).

/**
 * A by-grade value for a run; a black counts more like a red the shorter its committed stretch.
 * @param {import("./graph.js").Link} l
 * @param {number[]} table
 * @param {object} P  params
 */
export function byGrade(l, table, P) {
  if (l.g !== 3) return table[l.g];
  const mix = Math.min(1, Math.max(0, (l.cm - P.BLACK_SHORT_M) / (P.BLACK_LONG_M - P.BLACK_SHORT_M)));
  return table[2] + mix * (table[3] - table[2]);
}

/** How a run's average gradient scales its pull: near-flat and very steep runs are avoided. */
export function gradientPull(g, rule) {
  for (const [below, factor] of rule.flat) if (g < below) return factor;
  const [above, factor] = rule.steep;
  return g > above ? factor : 1;
}

/**
 * Each link's pull at the junction it leaves.
 * @returns {Float64Array}
 */
export function pulls(net, P) {
  const { L, outs } = net;
  const pull = new Float64Array(L.length);
  const walks = [];
  L.forEach((l, i) => {
    if (l.k === "download" || l.nur) pull[i] = 0;
    else if (l.k === "lift") pull[i] = l.cap / P.LIFT_PULL;
    else if (l.k === "run") pull[i] = byGrade(l, P.GRADE_PULL, P) * gradientPull(l.grad, P.GRADIENT_PULL);
    else walks.push(i);
  });
  for (const i of walks) {
    // A walk is as strong as the best run it leads to.
    let best = -Infinity;
    for (const j of outs[L[i].b]) if (L[j].k === "run") best = Math.max(best, pull[j]);
    pull[i] = best === -Infinity ? 1 : best;
  }
  return pull;
}

/**
 * Spread skiers ({junction: per hour}) downhill until lifts take them.
 * @param {ReturnType<import("./graph.js").network>} net
 * @param {Float64Array} sources  skiers per hour starting at each junction
 * @param {Float64Array} pull
 * @param {object} P
 * @returns {{laps: Float64Array, liftLaps: Map<number, number>}}  per link, and per lift (by key)
 */
export function skiDown(net, sources, pull, P) {
  const { N, L, outs, z } = net;
  const laps = new Float64Array(L.length);
  const liftLaps = new Map();
  let pending = Float64Array.from(sources);
  for (let sweep = 0; sweep < P.SWEEPS; sweep++) {
    let sum = 0;
    for (let n = 0; n < N; n++) sum += pending[n];
    if (sum < 1) break;
    const climbed = new Float64Array(N);
    for (let n = 0; n < N; n++) {
      // Junctions are numbered highest first, so one pass carries skiers all the way down.
      const q = pending[n];
      pending[n] = 0;
      if (q <= 0 || !outs[n].length) continue;
      let total = 0;
      for (const i of outs[n]) total += pull[i];
      if (total <= 0) continue; // only nursery ways on: left to ski school
      for (const i of outs[n]) {
        const share = (q * pull[i]) / total;
        const l = L[i];
        if (l.k === "lift") {
          liftLaps.set(l.lift, (liftLaps.get(l.lift) || 0) + share);
          continue;
        }
        laps[i] += share;
        (z[l.b] <= z[n] ? pending : climbed)[l.b] += share;
      }
    }
    for (let n = 0; n < N; n++) pending[n] += climbed[n];
  }
  return { laps, liftLaps };
}

/**
 * Lapping skiers leaving each lift's top: its capacity less its sector's commuting share. Where several lifts
 * share a top station their riders add up (the prototype kept only one).
 */
export function lapSources(net) {
  const { structure, L, lifts } = net;
  const sources = new Float64Array(net.N);
  for (const i of lifts) sources[L[i].b] += L[i].cap * (1 - structure.sectors[net.sectorOf(L[i].lift)].share);
  return sources;
}

/** The domain's laps. */
export function laps(net, P, pull = pulls(net, P)) {
  return skiDown(net, lapSources(net), pull, P);
}

/**
 * Share of a lift's riders who next ride each lift, by running its laps alone (to check the pipeline's exact
 * exchange shares).
 * @returns {Map<number, number>}
 */
export function exchange(net, P, liftKey, pull = pulls(net, P)) {
  const i = net.lifts.find((j) => net.L[j].lift === liftKey);
  const sources = new Float64Array(net.N);
  sources[net.L[i].b] = 1e6; // large, so the sweep's stop (under 1 skier left) doesn't cut it short
  const { liftLaps } = skiDown(net, sources, pull, P);
  return new Map([...liftLaps].map(([k, q]) => [k, q / 1e6]));
}
