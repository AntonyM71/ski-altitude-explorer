// Routing: commuters out and home, and locals home in the evening, each by the route that feels quickest to their
// ability group, averaged over seeded random draws (busyness-commuting; docs/decisions/009, 010).
import { routes, addPath } from "./graph.js";
import { byGrade } from "./laps.js";
import { gaussian } from "./random.js";

/**
 * How long each link feels to one ability group, optionally varied at random. On the way home (evening) harder runs
 * feel harder (by plain grade), busy runs are skied out, able skiers go faster on greens, and enclosed lifts can be
 * ridden down, which most people would rather not.
 * @param {object} opts
 * @param {number[]} opts.feel  the group's view of each grade
 * @param {Float64Array} opts.laps  lapping skiers per link (for skied-out runs)
 * @param {() => number} [opts.rnd]  normal random numbers, to vary times
 * @param {string} [opts.ability]  needed in the evening
 * @param {boolean} [opts.evening]
 * @param {Float64Array} [opts.downPenalty]  per link: how much slower an overfull ride down feels
 * @returns {Float64Array}
 */
export function routeTimes(net, P, { feel, laps, rnd = null, ability = null, evening = false, downPenalty = null }) {
  const { L } = net;
  const times = new Float64Array(L.length);
  for (let i = 0; i < L.length; i++) {
    const l = L[i];
    let t;
    if (l.k === "download") {
      if (!evening) {
        times[i] = Infinity;
        continue;
      }
      t = l.rt * P.DOWNLOAD_FEEL[ability] * (downPenalty ? downPenalty[i] : 1);
    } else {
      t = l.rt;
    }
    if (l.k === "run") {
      t *= byGrade(l, feel, P);
      if (evening) {
        const skiedOut = Math.min(1, laps[i] / (P.WIDTH[l.g] * P.SKIED_OUT_REF));
        t *= P.EVENING_FEEL[l.g] * (1 + P.SKIED_OUT_MAX * skiedOut);
        if (l.g === 0) t *= P.EASY_PACE[ability];
      }
    }
    times[i] = rnd ? t * Math.exp(rnd() * P.NOISE) : t;
  }
  return times;
}

/** Share amount over the routes between home and each end, weighted by the end's capacity. */
function spread(net, ends, r, home, reverse, amount, acc) {
  let total = 0;
  for (const [n, w] of ends) if (r.best[n] < Infinity) total += w;
  for (const [n, w] of ends) if (r.best[n] < Infinity) addPath(net, r, n, home, reverse, (amount * w) / total, acc);
}

/**
 * One routing pass over DRAWS draws: commuters' trips out and home (per day), and locals' trips home in the evening
 * rush (per hour). Each pass starts the random sequence afresh from SEED.
 * @returns {{out: Float64Array, back: Float64Array, evening: Float64Array}}
 */
export function routeEveryone(net, P, { laps, demand, ends, downPenalty }) {
  const { L, outs, structure } = net;
  const { sectors, villages, lifts } = structure;
  const out = new Float64Array(L.length);
  const back = new Float64Array(L.length);
  const evening = new Float64Array(L.length);
  const rnd = gaussian(P.SEED);
  for (let draw = 0; draw < P.DRAWS; draw++) {
    for (const [ability, { share, feel }] of Object.entries(P.ABILITIES)) {
      const times = routeTimes(net, P, { feel, laps, rnd });
      const homeTimes = routeTimes(net, P, { feel, laps, rnd, ability, evening: true, downPenalty });
      villages.forEach((v, vi) => {
        // People set off from, and return to, their own part of the village: each station's share is its lifts'.
        for (const [n, stationCap] of v.nodes) {
          const part = stationCap / v.cap;
          if (part <= 0) continue;
          const o = routes(net, [n], times);
          const b = routes(net, [n], homeTimes, true);
          for (const [sj, c] of demand[`${ability}|${vi}`]) {
            spread(net, ends.bottoms[sj], o, n, false, (c * part) / P.DRAWS, out);
            spread(net, ends.tops[sj], b, n, true, (c * part) / P.DRAWS, back);
          }
          // Locals going home: the reverse of their morning, from wherever this station's lifts took them.
          const local = v.skiers * (1 - sectors[v.sector].share) * share * part;
          const into = new Map();
          for (const i of outs[n]) {
            const l = L[i];
            if (l.k !== "lift" || l.nur) continue;
            for (const [sj, frac] of Object.entries(lifts[l.lift].day_sectors || {})) {
              into.set(Number(sj), (into.get(Number(sj)) || 0) + l.cap * frac);
            }
          }
          for (const [sj, c] of into) {
            spread(net, ends.tops[sj], b, n, true, (local * c) / stationCap / P.DRAWS / P.PEAK_HOURS, evening);
          }
        }
      });
    }
  }
  return { out, back, evening };
}
