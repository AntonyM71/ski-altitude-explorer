import { test } from "node:test";
import assert from "node:assert/strict";
import { network } from "../src/graph.js";
import { linkViews, bands } from "../src/views.js";
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

test("bands split at the 50th, 80th and 95th percentiles within the domain, whatever its size", () => {
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
