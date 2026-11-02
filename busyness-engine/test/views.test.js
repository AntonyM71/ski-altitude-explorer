import { test } from "node:test";
import assert from "node:assert/strict";
import { network } from "../src/graph.js";
import { linkViews, bands, liftsForSite, rushWaits } from "../src/views.js";
import { checkTraffic, EngineError } from "../src/checks.js";
import { run } from "../src/index.js";
import { P, fixture } from "./helpers.js";

const tiny = {
  z: [2000, 1500],
  links: [
    { a: 0, b: 1, k: "run", len: 1000, rt: 200, g: 1, grad: 0.3, run: "r" },
    { a: 1, b: 0, k: "lift", len: 1000, rt: 400, cap: 2000, lift: 0 },
    { a: 1, b: 0, k: "lift", len: 1000, rt: 400, cap: 1000, lift: 1 },
  ],
  lifts: { 0: { sector: 0 }, 1: { sector: 0 } },
  sectors: [{ cap: 3000, share: 0.4 }],
  villages: [{ sector: 0, nodes: [[1, 3000]], cap: 3000, skiers: 900 }],
};
const zeros = () => new Float64Array(3);

test("600 commuters out and back over a run add 200 an hour to its day average", () => {
  const net = network(tiny);
  const routed = { out: Float64Array.from([600, 0, 0]), back: Float64Array.from([600, 0, 0]), evening: zeros() };
  const v = linkViews(net, P, { laps: zeros(), liftLaps: new Map(), routed });
  assert.equal(v.day[0], 200);
});

test("a village's locals load its lifts in proportion to capacity in the morning", () => {
  const net = network(tiny);
  const routed = { out: zeros(), back: zeros(), evening: zeros() };
  const v = linkViews(net, P, { laps: zeros(), liftLaps: new Map(), routed });
  const local = (900 * 0.6) / P.PEAK_HOURS;
  assert.ok(Math.abs(v.morning[1] - (local * 2) / 3) < 1e-9 && Math.abs(v.morning[2] - local / 3) < 1e-9);
});

test("a run busy only on the way home ranks higher in the evening than by day", () => {
  const net = network(tiny);
  const routed = { out: zeros(), back: zeros(), evening: Float64Array.from([500, 0, 0]) };
  const v = linkViews(net, P, { laps: Float64Array.from([10, 0, 0]), liftLaps: new Map(), routed });
  assert.ok(v.evening[0] > 50 * v.day[0]);
});

test("run bands split at the 50th, 80th and 95th percentiles within the domain, whatever its size", () => {
  const domainOf = (n, scale) => ({
    runs: Object.fromEntries(Array.from({ length: n }, (_, i) => [`r${i}`, { len: 100, day: (i + 1) * scale, morning: 0, evening: 0 }])),
    lifts: {},
  });
  for (const [n, scale] of [[20, 1], [400, 1000]]) {
    const b = bands(domainOf(n, scale), P);
    const busiest = Object.values(b.runs).filter((r) => r.day === 3).length;
    assert.equal(busiest / n, 0.05, `${n} runs`);
    assert.equal(b.runs[`r${n - 1}`].day, 3);
    assert.equal(b.runs.r0.day, 0);
  }
});

test("lifts are banded by load, or by their queue, the same in every domain", () => {
  const lift = (load, waitMin = 0, nursery = false) => ({ day: load, morning: load, evening: load, nursery,
    wait: { day: waitMin * 60, morning: waitMin * 60, evening: waitMin * 60 } });
  const quiet = bands({ runs: {}, lifts: { a: lift(0.1), b: lift(0.3), c: lift(0.45) } }, P);
  assert.deepEqual(Object.values(quiet.lifts).map((l) => l.day), [0, 0, 0]); // a quiet domain: no queue bands
  const b = bands({ runs: {}, lifts: { room: lift(0.6), over: lift(1.2, 3), long: lift(1.4, 8), carpet: lift(2, 0, true) } }, P);
  assert.equal(b.lifts.room.day, 1); // 50% or more, no queue
  assert.equal(b.lifts.over.day, 2); // a lift over capacity has a queue: under 5 minutes is the third band
  assert.equal(b.lifts.long.morning, 3); // 8 minutes: the darkest band
  assert.equal(b.lifts.carpet.evening, null); // nursery lifts have no band
});

test("negative traffic makes the engine stop with an error", () => {
  assert.throws(() => checkTraffic({ day: Float64Array.from([5, -3]) }, [{ k: "run" }, { k: "lift" }]), EngineError);
  const bad = structuredClone(fixture("two_valleys"));
  bad.sectors[0].share = -0.2;
  assert.throws(() => run(bad, P), EngineError);
});

test("every run and lift gets a value and a band in each view", () => {
  const s = fixture("linked_valleys");
  const r = run(s, P);
  assert.deepEqual(Object.keys(r.runs).sort(), Object.keys(s.runs).sort());
  for (const view of ["day", "morning", "evening"]) {
    for (const id of Object.keys(s.runs)) assert.ok(r.bands.runs[id][view] >= 0 && r.bands.runs[id][view] <= 3);
  }
  const lift = Object.values(r.lifts)[0];
  assert.ok(["day", "morning", "evening", "down"].every((k) => Number.isFinite(lift[k])));
});

test("a lift mapped in two pieces shows its most loaded piece", () => {
  const structure = { lifts: { 0: { id: "L" }, 1: { id: "L" }, 2: { id: "M" } } };
  const w = (day, morning, evening) => ({ wait: { day, morning, evening } });
  const result = {
    lifts: { 0: { day: 0.4, morning: 1.3, evening: 0.2, ...w(0, 420, 0) }, 1: { day: 0.9, morning: 0.7, evening: 0.1, ...w(0, 0, 0) },
      2: { day: 0.3, morning: 0.3, evening: 0.3, ...w(0, 0, 0) } },
    bands: { lifts: { 0: { day: 0, morning: 3, evening: 0 }, 1: { day: 2, morning: 1, evening: 0 },
      2: { day: 0, morning: 0, evening: 0 } } },
  };
  const out = liftsForSite(structure, result);
  assert.deepEqual(out.L, { day: [2, 0.9, 0], morning: [3, 1.3, 420], evening: [0, 0.2, 0] });
  assert.deepEqual(out.M.day, [0, 0.3, 0]);
});

test("a village lift at 1.4x in the morning: its queue averages 18 minutes over the 1.5-hour rush", () => {
  const net = network({ z: [2000, 1000], links: [{ a: 1, b: 0, k: "lift", len: 1000, rt: 400, cap: 2000, lift: 0 }],
    lifts: { 0: { sector: 0 } }, sectors: [{ share: 0 }] });
  const w = rushWaits(net, P, { morning: Float64Array.from([2800]), evening: Float64Array.from([1500]) });
  assert.equal(w.morning[0], 18 * 60);
  assert.equal(w.evening[0], 0);
});
