// Lift queues: where more lapping skiers arrive at a lift than its capacity, it gets a wait, which grows until
// skiers who have another way on take it. Queues pull less, so skiers spread to other lifts; where there's no other
// way, the queue stays (busyness-queues; docs/decisions/015).
import { pulls, skiDown, lapSources } from "./laps.js";

const PROBE = 1e6; // skiers sent from one lift top to time its descent (large, so skiDown's 1-skier stop doesn't cut it)

/** Per link: a lift's expected seconds skiing and walking from its top to the next lift, with the given pulls. */
export function descents(net, P, pull) {
  const { L, lifts } = net;
  const out = new Float64Array(L.length);
  for (const i of lifts) {
    const src = new Float64Array(net.N);
    src[L[i].b] = PROBE;
    const { laps } = skiDown(net, src, pull, P);
    let time = 0;
    for (let j = 0; j < L.length; j++) if (laps[j] > 0) time += laps[j] * L[j].rt;
    out[i] = time / PROBE;
  }
  return out;
}

/**
 * The day's waits from each lift's overload. A visit to a lift (ride, queue, run down) must take about
 * arrivals ÷ capacity times longer for the lift to carry them, so each overfull lift's wait moves halfway towards
 * that, until no wait moves by more than 30 s or QUEUE_PASSES is reached. Capacity is the same yardstick as the
 * rushes' (rushWaits).
 * @param {(net, P, wait: Float64Array) => Float64Array} [pullsWith]  pulls for given waits (default: with the day's
 *   altitude preference; descent times use base pulls)
 * @returns {{wait: Float64Array, laps: Float64Array, liftLaps: Map<number, number>, pull: Float64Array, passes: number}}
 */
export function dayWaits(net, P, pullsWith = (n, p, w) => pulls(n, p, w, { altitude: true })) {
  const { L, lifts } = net;
  const wait = new Float64Array(L.length);
  const descent = descents(net, P, pulls(net, P));
  const src = lapSources(net);
  let passes = 0;
  for (let pass = 0; pass < P.QUEUE_PASSES; pass++) {
    passes++;
    const { liftLaps } = skiDown(net, src, pullsWith(net, P, wait), P);
    let moved = 0;
    for (const i of lifts) {
      const arrived = liftLaps.get(L[i].lift) || 0;
      // ponytail: day commuters (about a fifth of day lift traffic) aren't counted here: they're routed after the
      // laps. Count them once lift tops release only what they carried (conservation, #6).
      if (L[i].cap <= 0 || (arrived <= L[i].cap && wait[i] === 0)) continue;
      const visit = L[i].rt + wait[i] + descent[i];
      const target = Math.max(0, (visit * arrived) / L[i].cap - L[i].rt - descent[i]);
      const next = wait[i] + 0.5 * (target - wait[i]);
      moved = Math.max(moved, Math.abs(next - wait[i]));
      wait[i] = next;
    }
    if (moved <= 30) break;
  }
  const pull = pullsWith(net, P, wait);
  return { wait, pull, passes, ...skiDown(net, src, pull, P) };
}
