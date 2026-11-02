// Views: the day average, the morning rush and the evening rush, per link, run and lift; and bands within the
// domain for the overlay (busyness-views, busyness-overlay; docs/decisions/010).

/**
 * Per link: traffic per hour in each view.
 * @returns {{day: Float64Array, morning: Float64Array, evening: Float64Array, commute: Float64Array}}
 */
export function linkViews(net, P, { laps, liftLaps, routed }) {
  const { L, outs, structure } = net;
  const E = L.length;
  const morning = new Float64Array(E);
  const evening = new Float64Array(E);
  const day = new Float64Array(E);
  const commute = new Float64Array(E);
  // Morning: locals ride their village's lifts, split by capacity.
  for (const v of structure.villages) {
    const local = (v.skiers * (1 - structure.sectors[v.sector].share)) / P.PEAK_HOURS;
    for (const [n] of v.nodes) {
      for (const i of outs[n]) {
        if (L[i].k === "lift" && !L[i].nur) morning[i] += (local * L[i].cap) / v.cap;
      }
    }
  }
  for (let i = 0; i < E; i++) {
    const lap = L[i].k === "lift" ? liftLaps.get(L[i].lift) || 0 : laps[i];
    const trips = routed.out[i] + routed.back[i]; // the day's commuting trips, out and home
    morning[i] += routed.out[i] / P.PEAK_HOURS + P.RAMP * lap;
    evening[i] = routed.evening[i] + routed.back[i] / P.PEAK_HOURS + P.RAMP * lap;
    day[i] = lap + trips / P.DAY_HOURS;
    commute[i] = trips / P.DAY_HOURS;
  }
  return { day, morning, evening, commute };
}

const VIEWS = ["day", "morning", "evening"];
const QUEUED_S = 30; // a wait beyond loading of at least this counts as a queue

/**
 * Rush waits: where a lift's demand over the rush exceeds its capacity, a queue grows through the rush, and its
 * average wait is (demand − capacity) × PEAK_HOURS ÷ (2 × capacity), in seconds beyond loading (busyness-queues).
 * @returns {{morning: Float64Array, evening: Float64Array}}  per link
 */
export function rushWaits(net, P, views) {
  const out = { morning: new Float64Array(net.L.length), evening: new Float64Array(net.L.length) };
  net.L.forEach((l, i) => {
    if (l.k !== "lift" || l.nur) return;
    for (const v of ["morning", "evening"]) {
      const over = views[v][i] - l.cap;
      if (over > 0) out[v][i] = (over * P.PEAK_HOURS * 3600) / (2 * l.cap);
    }
  });
  return out;
}

/**
 * Runs by id (length-weighted over their pieces) and lifts by key (demand / capacity; in the evening, everyone the
 * lift carries, up and down).
 */
export function summarise(net, views, liftLaps, waits = null) {
  const { L, structure } = net;
  const runs = {};
  const lifts = {};
  const down = new Map();
  L.forEach((l, i) => {
    if (l.k === "download") down.set(l.lift, views.evening[i]);
  });
  L.forEach((l, i) => {
    if (l.k === "run") {
      const r = (runs[l.run] ||= { len: 0, day: 0, morning: 0, evening: 0, commute: 0 });
      r.len += l.len;
      for (const v of [...VIEWS, "commute"]) r[v] += views[v][i] * l.len;
    } else if (l.k === "lift") {
      const info = structure.lifts[l.lift];
      const riding = down.get(l.lift) || 0;
      lifts[l.lift] = {
        id: info.id, name: info.name, cap: l.cap, nursery: !!l.nur,
        laps: liftLaps.get(l.lift) || 0, commute: views.commute[i], down: riding,
        day: views.day[i] / l.cap, morning: views.morning[i] / l.cap, evening: (views.evening[i] + riding) / l.cap,
        // seconds beyond loading, per view (busyness-queues)
        wait: Object.fromEntries(VIEWS.map((v) => [v, waits ? waits[v][i] : 0])),
      };
    }
  });
  for (const r of Object.values(runs)) {
    for (const v of [...VIEWS, "commute"]) r[v] = r.len > 0 ? r[v] / r.len : 0;
  }
  return { runs, lifts };
}

/** The value below which a share q of the total weight lies. */
function weightedQuantile(pairs, q) {
  const sorted = pairs.filter(([, w]) => w > 0).sort((a, b) => a[0] - b[0]);
  const total = sorted.reduce((s, [, w]) => s + w, 0);
  let acc = 0;
  for (const [x, w] of sorted) {
    acc += w;
    if (acc >= q * total) return x;
  }
  return sorted.length ? sorted[sorted.length - 1][0] : 0;
}

/**
 * Runs: bands within the domain, 0 quiet, 1 moderate, 2 busy, 3 busiest, split at the BANDS quantiles of
 * length-weighted traffic. Lifts, the same in every domain (014, 015): 0 under 50% of capacity, 1 at 50% or more
 * with no queue, 2 a queue under LIFT_WAIT_BANDS_MIN minutes, 3 a longer queue. A queue is a wait of at least 30 s
 * beyond loading. Nursery lifts carry no laps and get null.
 */
export function bands(summary, P) {
  const out = { runs: {}, lifts: {}, thresholds: { runs: {}, lifts: {} } };
  const band = (x, cuts) => cuts.filter((c) => x > c).length;
  for (const v of VIEWS) {
    const runCuts = P.BANDS.map((q) => weightedQuantile(Object.values(summary.runs).map((r) => [r[v], r.len]), q));
    out.thresholds.runs[v] = runCuts;
    out.thresholds.lifts[v] = { load: P.LIFT_LOAD_BANDS, waitMin: P.LIFT_WAIT_BANDS_MIN };
    for (const [id, r] of Object.entries(summary.runs)) (out.runs[id] ||= {})[v] = band(r[v], runCuts);
    for (const [k, l] of Object.entries(summary.lifts)) {
      const wait = l.wait ? l.wait[v] : 0;
      (out.lifts[k] ||= {})[v] = l.nursery ? null
        : wait >= QUEUED_S ? 2 + band(wait / 60, P.LIFT_WAIT_BANDS_MIN)
        : l[v] >= P.LIFT_LOAD_BANDS[0] ? 1 : 0;
    }
  }
  return out;
}

/**
 * What the site needs per lift: by lift id, for each view, [band, load, wait in seconds beyond loading]. A lift mapped
 * in several pieces takes its most loaded piece. Nursery lifts have a null band.
 */
export function liftsForSite(structure, result) {
  const out = {};
  for (const [key, l] of Object.entries(result.lifts)) {
    const id = structure.lifts[key].id;
    const cur = (out[id] ||= {});
    for (const v of VIEWS) {
      if (!cur[v] || l[v] > cur[v][1]) cur[v] = [result.bands.lifts[key][v], l[v], l.wait ? l.wait[v] : 0];
    }
  }
  return out;
}
