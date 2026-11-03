// The simulated day (busyness-day-simulation; docs/decisions/017). Skiers are fractional flows, grouped into cohorts
// by home village and purpose (lapping, heading for a sector, heading home), stepped through the day STEP_S at a
// time. A lift boards only who is waiting at its bottom, up to its capacity; nobody comes off a lift's top unless
// they rode it. The views are averages over windows of the day.
import { routes } from "./graph.js";
import { pulls } from "./laps.js";
import { routeTimes } from "./routing.js";
import { gaussian } from "./random.js";

const EPS = 1e-9;

/**
 * Simulate a domain's day.
 * @param {ReturnType<import("./graph.js").network>} net
 * @param {object} P
 * @param {{demand: Record<string, [number, number][]>, ends: {bottoms: Map<number, number>[]},
 *   onStep?: (t: number, total: number) => void}} opts  commuters per "ability|village" and destination sector
 *   (demand.js), each sector's lift bottoms, and (for tests) a check after each step given everyone accounted for
 * @returns {{views: Record<string, Float64Array>, commute: Record<string, Float64Array>,
 *   arrivals: Record<string, Float64Array>, waits: Record<string, Float64Array>, report: object}}  per link and per
 *   hour for each window (day, morning, evening): skiers entering a run or walk, or boarding a lift; the same for
 *   commuters and skiers heading home; skiers arriving at a lift; its average wait beyond loading, in seconds
 */
export function simulate(net, P, { demand, ends, onStep = null }) {
  const { N, L, outs, structure } = net;
  const { villages, sectors } = structure;
  const V = villages.length;
  const S = sectors.length;
  const M = S + 2; // purposes: 0 lapping, 1 heading home, 2 + s heading for sector s
  const C = V * M;
  const step = P.STEP_S;
  const steps = Math.round(((P.EVENING_TO_H - P.START_H) * 3600) / step);
  const at = (h) => Math.round(((h - P.START_H) * 3600) / step); // the step at an hour of the day
  const homeStep = at(P.HOME_H);
  const windows = {
    morning: [0, at(P.MORNING_TO_H)],
    day: [at(P.DAY_FROM_H), at(P.DAY_TO_H)],
    evening: [homeStep, steps],
  };
  const dayMid = Math.round((windows.day[0] + windows.day[1]) / 2);
  const carriers = []; // lifts, and rides down: they board from a queue at their start
  L.forEach((l, i) => {
    if (l.k === "lift" || l.k === "download") carriers.push(i);
  });

  // Where skiers are: at junctions (pool), on their way along a link (ring, by the step they arrive), at a lift.
  let maxRt = 0;
  for (const l of L) maxRt = Math.max(maxRt, l.rt);
  const R = Math.ceil(maxRt / step) + 2;
  // ponytail: dense N × cohorts slots (tens of MB for the biggest domains); sparse slots if memory matters.
  const ring = Array.from({ length: R }, () => new Float64Array(N * C));
  const pool = new Float64Array(N * C);
  const queue = new Float64Array(L.length * C);
  const home = new Float64Array(V);

  /** Send amount of cohort c along link i (taking rt seconds) from junction n at step t. */
  const travel = (i, c, a, t, n) => {
    const l = L[i];
    const d = l.rt / step;
    const f = Math.floor(d);
    const late = d - f; // split between the steps either side of the exact arrival, keeping the mean time
    for (const [k, part] of [[f, a * (1 - late)], [f + 1, a * late]]) {
      if (part <= 0) continue;
      if (k === 0 && l.b > n) pool[l.b * C + c] += part; // lower down: reached later in this step's sweep
      else ring[(t + Math.max(k, 1)) % R][l.b * C + c] += part;
    }
  };

  // Lapping choices: each junction's ways on and their shares of pull, refreshed every PULL_MIN.
  let lapHops = [];
  const wait = new Float64Array(L.length); // a lift's current wait beyond loading, seconds
  const queued = (i) => {
    let q = 0;
    for (let c = 0; c < C; c++) q += queue[i * C + c];
    return q;
  };
  const refreshWaits = () => {
    for (const i of carriers) wait[i] = (queued(i) / L[i].cap) * 3600;
  };
  const refreshPulls = () => {
    const pull = pulls(net, P, wait, { altitude: true });
    lapHops = Array.from({ length: N }, (_, n) => {
      let total = 0;
      const ways = outs[n].filter((i) => L[i].a !== L[i].b && pull[i] > 0); // runs looping within a station: none
      for (const i of ways) total += pull[i];
      return total > 0 ? ways.map((i) => [i, pull[i] / total]) : null;
    });
  };

  // Routes: per destination, each junction's next links, blended over abilities (by share) and draws (evenly).
  const sectorDest = Array.from({ length: S }, (_, s) => [...ends.bottoms[s].keys()]);
  const villageDest = villages.map((v) => v.nodes.map(([n]) => n));
  const isSectorEnd = sectorDest.map((ns) => new Set(ns));
  const isHome = villageDest.map((ns) => new Set(ns));
  const dayRate = new Float64Array(L.length); // runs' day traffic per hour, for skied-out runs on the way home
  let sectorHops = [];
  let homeHops = [];
  const trees = (dests, evening) => {
    const rnd = gaussian(P.SEED);
    const hops = dests.map(() => Array.from({ length: N }, () => new Map()));
    for (let draw = 0; draw < P.DRAWS; draw++) {
      for (const [ability, { share, feel }] of Object.entries(P.ABILITIES)) {
        const times = routeTimes(net, P, { feel, laps: dayRate, rnd, ability, evening, wait });
        dests.forEach((nodes, k) => {
          const { prev } = routes(net, nodes, times, true);
          for (let n = 0; n < N; n++) {
            const i = prev[n];
            if (i >= 0) hops[k][n].set(i, (hops[k][n].get(i) || 0) + share / P.DRAWS);
          }
        });
      }
    }
    return hops.map((perNode) => perNode.map((m) => (m.size ? [...m] : null)));
  };

  // Departures over ARRIVE_MIN from START_H: each station's share of its village is its lifts'.
  const departing = new Float64Array(N * C);
  const arriveSteps = Math.max(1, Math.round((P.ARRIVE_MIN * 60) / step));
  let population = 0;
  villages.forEach((v, vi) => {
    const locals = v.skiers * (1 - sectors[v.sector].share);
    const commuters = new Float64Array(S);
    for (const ability of Object.keys(P.ABILITIES)) {
      for (const [s, c] of demand[`${ability}|${vi}`] || []) commuters[s] += c;
    }
    for (const [n, stationCap] of v.nodes) {
      const part = v.cap > 0 ? stationCap / v.cap : 1 / v.nodes.length;
      departing[n * C + vi * M] += (locals * part) / arriveSteps;
      for (let s = 0; s < S; s++) departing[n * C + vi * M + 2 + s] += (commuters[s] * part) / arriveSteps;
    }
    population += locals + commuters.reduce((a, b) => a + b, 0);
  });

  // Accumulators, per window.
  const VIEWS = Object.keys(windows);
  const acc = Object.fromEntries(VIEWS.map((v) => [v, { flow: new Float64Array(L.length), commute: new Float64Array(L.length),
    arrive: new Float64Array(L.length), wait: new Float64Array(L.length) }]));
  const halves = [new Float64Array(L.length), new Float64Array(L.length)];
  const flow = new Float64Array(L.length);
  const commute = new Float64Array(L.length);
  const arrive = new Float64Array(L.length);
  let noon = null;

  /** At HOME_H, everyone still out heads home; queued skiers stay only in the share whose way home is that lift. */
  const goHome = () => {
    const toHome = (arr, n0) => {
      for (let base = 0; base < arr.length; base += C) {
        for (let vi = 0; vi < V; vi++) {
          let moved = 0;
          for (let m = 0; m < M; m++) {
            if (m === 1) continue;
            moved += arr[base + vi * M + m];
            arr[base + vi * M + m] = 0;
          }
          arr[base + vi * M + 1] += moved;
          if (n0) n0(base / C, vi, moved);
        }
      }
    };
    toHome(pool);
    for (const slot of ring) toHome(slot);
    toHome(queue, (i, vi, moved) => {
      if (moved <= 0) return;
      const hops = homeHops[vi][L[i].a];
      const stay = hops ? hops.filter(([j]) => j === i).reduce((s, [, w]) => s + w, 0) : 0;
      const leave = moved * (1 - stay);
      queue[i * C + vi * M + 1] -= leave;
      pool[L[i].a * C + vi * M + 1] += leave;
    });
  };

  refreshWaits();
  refreshPulls();
  sectorHops = trees(sectorDest, false);
  for (let t = 0; t < steps; t++) {
    if (t > 0 && t % Math.round((P.PULL_MIN * 60) / step) === 0) {
      refreshWaits();
      refreshPulls();
    }
    const reroute = t > 0 && t % Math.round((P.REROUTE_MIN * 60) / step) === 0;
    if (t < homeStep && reroute) sectorHops = trees(sectorDest, false);
    if (t === homeStep) {
      for (let i = 0; i < L.length; i++) dayRate[i] = acc.day.flow[i] / ((windows.day[1] - windows.day[0]) * step / 3600);
      refreshWaits();
      homeHops = trees(villageDest, true);
      goHome();
    } else if (t > homeStep && reroute) {
      refreshWaits();
      homeHops = trees(villageDest, true);
    }

    // Arrivals due this step, and departures from the villages.
    const slot = ring[t % R];
    for (let k = 0; k < pool.length; k++) pool[k] += slot[k];
    slot.fill(0);
    if (t < arriveSteps) for (let k = 0; k < pool.length; k++) pool[k] += departing[k];
    flow.fill(0);
    commute.fill(0);
    arrive.fill(0);

    // The sweep: junctions highest first, so skiers pass down any chain of short links within the step.
    for (let n = 0; n < N; n++) {
      const base = n * C;
      for (let vi = 0; vi < V; vi++) {
        const c0 = base + vi * M;
        for (let s = 0; s < S; s++) {
          if (pool[c0 + 2 + s] > 0 && isSectorEnd[s].has(n)) { // commuters arrive, and lap from here
            pool[c0] += pool[c0 + 2 + s];
            pool[c0 + 2 + s] = 0;
          }
        }
        if (pool[c0 + 1] > 0 && isHome[vi].has(n)) {
          home[vi] += pool[c0 + 1];
          pool[c0 + 1] = 0;
        }
        for (let m = 0; m < M; m++) {
          const a = pool[c0 + m];
          if (a <= EPS) continue;
          const hops = m === 0 ? lapHops[n] : m === 1 ? homeHops[vi]?.[n] : sectorHops[m - 2][n];
          if (!hops) continue; // nowhere to go from here: they wait at the junction
          pool[c0 + m] = 0;
          const c = vi * M + m;
          for (const [i, w] of hops) {
            const x = a * w;
            if (L[i].k === "lift" || L[i].k === "download") {
              queue[i * C + c] += x;
              arrive[i] += x;
            } else {
              flow[i] += x;
              if (m !== 0) commute[i] += x;
              travel(i, c, x, t, n);
            }
          }
        }
      }
    }

    // Lifts board from their queues, up to capacity, shared evenly across who is waiting.
    for (const i of carriers) {
      const q = queued(i);
      if (q <= EPS) {
        wait[i] = 0;
        continue;
      }
      const board = Math.min(q, (L[i].cap * step) / 3600);
      const r = board / q;
      for (let c = 0; c < C; c++) {
        const x = queue[i * C + c] * r;
        if (x <= 0) continue;
        queue[i * C + c] -= x;
        if (c % M !== 0) commute[i] += x;
        travel(i, c, x, t, Infinity);
      }
      flow[i] += board;
      wait[i] = ((q - board) / L[i].cap) * 3600; // sampled for the views; pulls and routes refresh on their own clock
    }

    for (const v of VIEWS) {
      const [from, to] = windows[v];
      if (t < from || t >= to) continue;
      const a = acc[v];
      for (let i = 0; i < L.length; i++) {
        a.flow[i] += flow[i];
        a.commute[i] += commute[i];
        a.arrive[i] += arrive[i];
        a.wait[i] += wait[i];
      }
      if (v === "day") {
        const h = halves[t < dayMid ? 0 : 1];
        for (let i = 0; i < L.length; i++) h[i] += flow[i];
      }
    }
    if (onStep) {
      let total = home.reduce((s, x) => s + x, 0);
      for (const arr of [pool, queue, ...ring]) for (const x of arr) total += x;
      if (t + 1 < arriveSteps) for (const x of departing) total += x * (arriveSteps - t - 1); // not yet set off
      onStep(t, total);
    }
    if (t === at(12)) {
      const sum = (arr) => arr.reduce((s, x) => s + x, 0);
      const byJunction = Array.from({ length: N }, (_, n) => [n, pool.subarray(n * C, (n + 1) * C).reduce((s, x) => s + x, 0)]);
      noon = { atJunctions: sum(pool), queued: sum(queue), moving: ring.reduce((s, r) => s + sum(r), 0),
        stuck: byJunction.filter(([, x]) => x > 1).sort((x, y) => y[1] - x[1]).slice(0, 25) };
    }
  }

  // Per hour over each window; waits averaged over its steps.
  const views = {};
  const commuteViews = {};
  const arrivals = {};
  const waits = {};
  for (const v of VIEWS) {
    const n = windows[v][1] - windows[v][0];
    const hours = (n * step) / 3600;
    views[v] = acc[v].flow.map((x) => x / hours);
    arrivals[v] = acc[v].arrive.map((x) => x / hours);
    waits[v] = acc[v].wait.map((x) => x / n);
    commuteViews[v] = acc[v].commute.map((x) => x / hours);
  }
  const halfHours = ((windows.day[1] - windows.day[0]) * step) / 3600 / 2;
  const unsettled = [];
  for (let i = 0; i < L.length; i++) {
    const [a, b] = [halves[0][i] / halfHours, halves[1][i] / halfHours];
    const hi = Math.max(a, b);
    if (hi >= 100 && Math.abs(a - b) / hi > 0.1) unsettled.push({ link: i, first: a, second: b });
  }
  const sumHome = home.reduce((s, x) => s + x, 0);
  return {
    views, commute: commuteViews, arrivals, waits,
    report: { population, notHome: population > 0 ? 1 - sumHome / population : 0, noon, unsettled },
  };
}
