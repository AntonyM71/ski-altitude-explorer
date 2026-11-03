// Views: the day average, the morning rush and the evening rush, per link, run and lift; and bands within the
// domain for the overlay (busyness-views, busyness-overlay; docs/decisions/010).

const VIEWS = ["day", "morning", "evening"];
const QUEUED_S = 30; // a wait beyond loading of at least this counts as a queue

/**
 * Runs by id (length-weighted over their pieces) and lifts by key: for each view, skiers boarded ÷ capacity (in the
 * evening, everyone the lift carries, up and down), with demand (skiers arriving ÷ capacity) and the average wait.
 * @param {Record<string, Float64Array>} views  per link and hour: day, morning, evening and commute (the day's)
 * @param {Record<string, Float64Array>} arrivals  per link and hour, by view: skiers arriving at a lift
 * @param {Record<string, Float64Array>} waits  per link, by view: average wait beyond loading, seconds
 */
export function summarise(net, views, arrivals, waits) {
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
        commute: views.commute[i], down: riding,
        day: views.day[i] / l.cap, morning: views.morning[i] / l.cap, evening: (views.evening[i] + riding) / l.cap,
        demand: Object.fromEntries(VIEWS.map((v) => [v, arrivals[v][i] / l.cap])),
        // seconds beyond loading, per view (busyness-queues)
        wait: Object.fromEntries(VIEWS.map((v) => [v, waits[v][i]])),
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
