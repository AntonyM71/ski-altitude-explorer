// The evening rides down: a gondola, cable car or funicular carries at most its capacity down. Where more want to
// ride than that, riding feels slower and everyone is routed again, up to DOWNLOAD_PASSES times, so the excess skis
// home (busyness-commuting; docs/decisions/009).
import { routeEveryone } from "./routing.js";

/**
 * Route everyone, re-routing while any ride down is overfull.
 * @returns {{out: Float64Array, back: Float64Array, evening: Float64Array, downPenalty: Float64Array, passes: number}}
 */
export function routeWithRidesDown(net, P, { laps, demand, ends }) {
  const { L } = net;
  const downPenalty = new Float64Array(L.length).fill(1);
  const downs = [];
  L.forEach((l, i) => {
    if (l.k === "download") downs.push(i);
  });
  let res;
  let passes = 0;
  for (let pass = 0; pass < P.DOWNLOAD_PASSES; pass++) {
    res = routeEveryone(net, P, { laps, demand, ends, downPenalty });
    passes++;
    let changed = false;
    for (const i of downs) {
      const load = (res.back[i] / P.PEAK_HOURS + res.evening[i]) / L[i].cap;
      if (load > P.DOWNLOAD_MAX_LOAD * 1.05) {
        downPenalty[i] *= load / P.DOWNLOAD_MAX_LOAD;
        changed = true;
      }
    }
    if (!changed) break;
  }
  return { ...res, downPenalty, passes };
}
