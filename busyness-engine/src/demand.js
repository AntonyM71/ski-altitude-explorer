// Commuter demand: a gravity model of where each village's commuters spend the day (busyness-commuting;
// docs/decisions/009).
import { routes } from "./graph.js";
import { routeTimes } from "./routing.js";

/**
 * Lift bottoms and tops of each sector, weighted by capacity (lifts that carry skiing only).
 * @returns {{bottoms: Map<number, number>[], tops: Map<number, number>[]}}
 */
export function sectorEnds(net) {
  const S = net.structure.sectors.length;
  const bottoms = Array.from({ length: S }, () => new Map());
  const tops = Array.from({ length: S }, () => new Map());
  for (const i of net.lifts) {
    const l = net.L[i];
    const s = net.sectorOf(l.lift);
    bottoms[s].set(l.a, (bottoms[s].get(l.a) || 0) + l.cap);
    tops[s].set(l.b, (tops[s].get(l.b) || 0) + l.cap);
  }
  return { bottoms, tops };
}

/**
 * For each ability and village: [sector, commuters per day] for every other sector it can reach. A sector draws in
 * proportion to its capacity, discounted by e for every DECAY_MIN minutes of travel as the group feels it.
 * @returns {Record<string, [number, number][]>}  keyed "ability|village index"
 */
export function gravity(net, P, ends, laps) {
  const { sectors, villages } = net.structure;
  const demand = {};
  for (const [ability, { share, feel }] of Object.entries(P.ABILITIES)) {
    const plain = routeTimes(net, P, { feel, laps });
    villages.forEach((v, vi) => {
      const { best } = routes(net, v.nodes.map(([n]) => n), plain);
      const draw = new Map();
      sectors.forEach((s, sj) => {
        if (sj === v.sector) return;
        let td = 0;
        let tc = 0;
        for (const [n, c] of ends.bottoms[sj]) {
          if (best[n] < Infinity) {
            td += best[n] * c;
            tc += c;
          }
        }
        if (tc > 0) draw.set(sj, s.cap * Math.exp(-(td / tc) / 60 / P.DECAY_MIN));
      });
      let total = 0;
      for (const w of draw.values()) total += w;
      const commuters = sectors[v.sector].share * share * v.skiers;
      demand[`${ability}|${vi}`] = [...draw].map(([sj, w]) => [sj, (commuters * w) / total]);
    });
  }
  return demand;
}
