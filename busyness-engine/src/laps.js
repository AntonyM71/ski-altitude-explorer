// Laps: how lapping skiers choose at junctions, by pull, and how they spread downhill until a lift takes them
// (busyness-laps; docs/decisions/006, 017).

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
 * Each link's pull at the junction it leaves (busyness-laps).
 * - A lift pulls by its capacity ÷ LIFT_PULL, divided by its queue factor, 1 + its wait beyond loading ÷
 *   QUEUE_TOLERANCE_MIN (busyness-queues); with `altitude` (lapping skiers), times ALT_RATIO ^ (h − 0.5), h being how
 *   high its bottom station sits in the domain's range of lift bottoms.
 * - A run pulls like the lifts it leads to, at full weight, times how pleasant the way there is: the lower of its own
 *   attractiveness (grade and gradient) and the easiest way on beyond it. A lift a short run away counts as fully as one
 *   at hand, a long black on the only way there dissuades, and a black beside an easier way doesn't.
 * - A walk pulls the same way, as a level stretch, or as a near-flat run where it climbs.
 * - Nursery lifts and slopes pull NURSERY_PULL times as much as an ordinary lift or run: a last resort.
 * @param {Float64Array} [wait]  per link: a lift's wait beyond loading, in seconds
 * @param {{altitude?: boolean}} [opts]
 * @returns {Float64Array}
 */
export function pulls(net, P, wait = null, { altitude = false } = {}) {
  const { L, outs, z } = net;
  const pull = new Float64Array(L.length);
  const bottoms = net.lifts.map((i) => z[L[i].a]);
  const lo = Math.min(...bottoms);
  const span = Math.max(...bottoms) - lo || 1;
  const height = (i) => (altitude ? P.ALT_RATIO ** ((z[L[i].a] - lo) / span - 0.5) : 1);
  const queue = (i) => 1 + (wait ? wait[i] : 0) / 60 / P.QUEUE_TOLERANCE_MIN;
  // How pleasant a link is to take on the way to a lift, 0..1. ponytail: any climb counts as uphill; a small
  // threshold if skating over a bump matters.
  const ease = (l) =>
    l.k === "run" ? byGrade(l, P.GRADE_PULL, P) * gradientPull(l.grad, P.GRADIENT_PULL) * (l.nur ? P.NURSERY_PULL : 1)
      : z[l.b] > z[l.a] ? P.GRADIENT_PULL.flat[0][1] : 1;
  let sq = 0;
  let sum = 0;
  L.forEach((l, i) => {
    if (l.k !== "lift") return;
    const base = l.cap / P.LIFT_PULL;
    pull[i] = (base * (l.nur ? P.NURSERY_PULL : 1) * height(i)) / queue(i);
    if (l.nur) return;
    sq += base * base;
    sum += base;
  });
  // The domain's typical lift pull ahead (the pull-weighted average used below, over every lift's base pull): for a
  // way on to a junction with no lift ahead.
  const typical = sum > 0 ? sq / sum : 1;
  // Per junction: the lift pull ahead (pull-weighted over its ways on: a lift's own pull, or the pull ahead beyond a
  // run or walk) and the easiest way on (the best over its ways on: 1 for a lift, or a run or walk's ease capped by
  // the easiest way on beyond it). Junctions are numbered highest first, so going from the last to the first sees every
  // junction below before the ones above it. A walk up to a junction not yet seen takes the lifts leaving it.
  const ahead = new Float64Array(net.N).fill(typical);
  const easiest = new Float64Array(net.N).fill(1);
  const seen = new Uint8Array(net.N);
  const liftsAt = (n) => {
    let p2 = 0;
    let p1 = 0;
    for (const j of outs[n]) if (L[j].k === "lift" && pull[j] > 0) { p2 += pull[j] ** 2; p1 += pull[j]; }
    return p1 > 0 ? p2 / p1 : typical;
  };
  for (let n = net.N - 1; n >= 0; n--) {
    let total = 0;
    let weighted = 0;
    let best = 0;
    for (const i of outs[n]) {
      const l = L[i];
      if (l.k === "lift") {
        if (pull[i] > 0) { total += pull[i]; weighted += pull[i] ** 2; best = 1; }
        continue;
      }
      if (l.k === "download") continue;
      const known = seen[l.b];
      const way = Math.min(ease(l), known ? easiest[l.b] : 1);
      const beyond = known ? ahead[l.b] : liftsAt(l.b);
      pull[i] = way * beyond;
      total += pull[i];
      weighted += pull[i] * beyond;
      best = Math.max(best, way);
    }
    if (total > 0) ahead[n] = weighted / total;
    if (best > 0) easiest[n] = best;
    seen[n] = 1;
  }
  return pull;
}

/**
 * Plain pulls, as the structure pipeline uses to find sectors (busyness/sectors.py): a lift by capacity ÷ LIFT_PULL,
 * a run by its own grade and gradient, a walk as the best run or lift it leads to (1 if neither), nursery links and
 * rides down none. No queues, altitude or lookahead.
 */
export function plainPulls(net, P) {
  const { L, outs } = net;
  const pull = new Float64Array(L.length);
  const own = (i) => {
    const l = L[i];
    if (l.k === "download" || l.nur) return 0;
    if (l.k === "lift") return l.cap / P.LIFT_PULL;
    if (l.k === "run") return byGrade(l, P.GRADE_PULL, P) * gradientPull(l.grad, P.GRADIENT_PULL);
    return null;
  };
  L.forEach((l, i) => {
    const p = own(i);
    if (p !== null) pull[i] = p;
    else {
      let best = -Infinity;
      for (const j of outs[l.b]) if (L[j].k === "run" || L[j].k === "lift") best = Math.max(best, own(j));
      pull[i] = best === -Infinity ? 1 : best;
    }
  });
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
 * Share of a lift's riders who next ride each lift, by running its laps alone (to check the pipeline's exact
 * exchange shares).
 * @returns {Map<number, number>}
 */
export function exchange(net, P, liftKey, pull = plainPulls(net, P)) {
  const i = net.lifts.find((j) => net.L[j].lift === liftKey);
  const sources = new Float64Array(net.N);
  sources[net.L[i].b] = 1e6; // large, so the sweep's stop (under 1 skier left) doesn't cut it short
  const { liftLaps } = skiDown(net, sources, pull, P);
  return new Map([...liftLaps].map(([k, q]) => [k, q / 1e6]));
}
