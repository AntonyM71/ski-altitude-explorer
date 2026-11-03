// Routing: how long each link feels to an ability group, for the routes of commuters and skiers going home
// (busyness-commuting; docs/decisions/009, 010, 017).
import { byGrade } from "./laps.js";

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
 * @param {Float64Array} [opts.wait]  per link: a lift's wait beyond loading, in seconds, in the view being routed
 * @returns {Float64Array}
 */
export function routeTimes(net, P, { feel, laps, rnd = null, ability = null, evening = false, downPenalty = null,
  wait = null }) {
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
      t = l.rt + (wait && l.k === "lift" ? wait[i] : 0); // a queue on the way adds its wait (busyness-queues)
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
