import { test } from "node:test";
import assert from "node:assert/strict";
import { bands, liftsForSite } from "../src/views.js";
import { checkTraffic, EngineError } from "../src/checks.js";
import { run } from "../src/index.js";
import { P, fixture } from "./helpers.js";

const lift = (a, b, cap, key, rt = 400) => ({ a, b, k: "lift", len: 1000, rt, cap, lift: key });
const run_ = (a, b, rt = 300) => ({ a, b, k: "run", len: 800, rt, g: 1, grad: 0.2, run: `r${a}${b}` });
// A village at the bottom (1) of a chairlift to the top (0), and a run back down.
const loop = (skiers, cap) => ({ z: [2000, 1500], links: [lift(1, 0, cap, 0), run_(0, 1)],
  lifts: { 0: { id: "L", sector: 0 } }, sectors: [{ cap, share: 0 }], runs: { r01: ["Run", 1] },
  villages: [{ sector: 0, nodes: [[1, cap]], cap, skiers }] });

test("a lift with more skiers than it can carry shows demand over 1.0x, its load at capacity and its wait", () => {
  const l = run(loop(1000, 1200), P).lifts[0];
  assert.ok(l.demand.morning > 1, `demand ${l.demand.morning}`); // the queue grows through the morning
  assert.ok(Math.abs(l.day - 1) < 0.01, `load ${l.day}`); // and the lift runs at capacity all day
  assert.ok(l.wait.day > 60);
});

test("a lift with room shows its load and no wait beyond loading", () => {
  const l = run(loop(100, 2000), P).lifts[0];
  assert.ok(l.day > 0 && l.day < 0.5, `load ${l.day}`);
  assert.equal(l.wait.day, 0);
});

test("reading a wait: a queue of 300 at a 1,800-an-hour lift is 10 minutes", () => {
  // Everyone arrives in the first minute (ARRIVE_MIN 1), only that minute is the morning window, and the lift boards
  // 30 of the 330 in it.
  const r = run(loop(330, 1800), { ...P, ARRIVE_MIN: 1, MORNING_TO_H: 9 + 1 / 60 });
  assert.ok(Math.abs(r.lifts[0].wait.morning - 600) < 1e-6, `${r.lifts[0].wait.morning} s`);
});

test("commuters count in the morning and evening views, not the day's", () => {
  const r = run(fixture("linked_valleys"), P);
  const most = (arr) => arr.reduce((m, x) => Math.max(m, x), 0);
  assert.ok(most(r.links.out) > 0 && most(r.links.back) > 0, "commuters cross links in the rushes");
  assert.ok(most(r.links.commute) < 1e-6, "and none by day");
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
