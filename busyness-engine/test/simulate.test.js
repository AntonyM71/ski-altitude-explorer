import { test } from "node:test";
import assert from "node:assert/strict";
import { network } from "../src/graph.js";
import { sectorEnds } from "../src/demand.js";
import { simulate } from "../src/simulate.js";
import { P } from "./helpers.js";

const lift = (a, b, cap, key, rt = 400) => ({ a, b, k: "lift", len: 1000, rt, cap, lift: key });
const run = (a, b, rt = 300, g = 1, grad = 0.2, extra = {}) => ({ a, b, k: "run", len: 800, rt, g, grad, ...extra });
const village = (nodes, skiers, sector = 0) => ({ name: "V", sector, nodes, cap: nodes.reduce((s, [, c]) => s + c, 0), skiers });
const sim = (s, { demand = {}, params = {}, onStep } = {}) => {
  const net = network(s);
  return { net, r: simulate(net, { ...P, ...params }, { demand, ends: sectorEnds(net), onStep }) };
};

// A village at the bottom (1) of one chairlift to the top (0), and a run back down.
const loop = (skiers = 500, cap = 1200) => ({ z: [2000, 1500], links: [lift(1, 0, cap, 0), run(0, 1)],
  lifts: { 0: { sector: 0 } }, sectors: [{ share: 0 }], villages: [village([[1, cap]], skiers)] });

test("skiers are conserved every step", () => {
  let checked = 0;
  sim(loop(), { onStep: (t, total) => {
    assert.ok(Math.abs(total - 500) < 1e-6, `step ${t}: ${total} accounted for`);
    checked++;
  } });
  assert.ok(checked > 400);
});

test("a village with two stations sends two-thirds of its skiers from the one with twice the lifts", () => {
  const s = { z: [2500, 2400, 1500, 1500], links: [lift(2, 0, 20000, 0), lift(3, 1, 10000, 1), run(0, 2), run(1, 3)],
    lifts: { 0: { sector: 0 }, 1: { sector: 0 } }, sectors: [{ share: 0 }], villages: [village([[2, 20000], [3, 10000]], 900)] };
  const { r } = sim(s, { params: { MORNING_TO_H: 9 + 1 / 60 } }); // the first minute: departures only
  assert.ok(Math.abs(r.views.morning[0] / r.views.morning[1] - 2) < 1e-9);
});

test("a lift nobody reaches carries nobody", () => {
  const s = loop();
  s.z.push(1800, 2300);
  s.links.push(lift(2, 3, 2000, 1)); // a lift whose bottom nothing leads to
  s.z = [2300, 2000, 1800, 1500];
  s.links = [lift(3, 1, 1200, 0), run(1, 3), lift(2, 0, 2000, 1)];
  s.lifts[1] = { sector: 0 };
  s.villages = [village([[3, 1200]], 500)];
  const { r } = sim(s);
  for (const v of ["morning", "day", "evening"]) assert.equal(r.views[v][2], 0);
  assert.ok(r.views.day[0] > 0);
});

test("a lift beside an overfull one gains skiers as the queue grows", () => {
  // From the top (0): a blue to a 600 chairlift's bottom (1) and a near-flat run to a 1,500 one's (2), which is
  // where the village is; 600 skiers lapping. Without queues, the small lift gets about half of them.
  const s = { z: [2500, 1600, 1500], links: [lift(1, 0, 600, 0), lift(2, 0, 1500, 1), run(0, 1), run(0, 2, 300, 1, 0.03)],
    lifts: { 0: { sector: 0 }, 1: { sector: 0 } }, sectors: [{ share: 0 }], villages: [village([[2, 1500]], 600)] };
  const queues = sim(s).r;
  const blind = sim(s, { params: { QUEUE_TOLERANCE_MIN: 1e9 } }).r;
  assert.ok(queues.waits.day[0] > 60, "the small lift queues");
  assert.ok(queues.arrivals.day[1] > blind.arrivals.day[1] * 1.05,
    `the big lift gets ${Math.round(queues.arrivals.day[1])} with queues seen, ${Math.round(blind.arrivals.day[1])} without`);
});

// Commuters from the village (4, sector 0) to sector 1 (bottom 3): a quick small lift A (4 → 0) or a slow big one B
// (4 → 2), then a run down to 3. Sector 1 has lift C (3 → 1) and runs back to 3 and home to 4.
const commute = (capA = 120) => ({ z: [2300, 2200, 2100, 1800, 1500],
  links: [lift(4, 0, capA, 0, 300), run(0, 3, 120), lift(4, 2, 5000, 1, 900), run(2, 3, 120), lift(3, 1, 2000, 2, 300),
    run(1, 3, 120), run(1, 4, 300)],
  lifts: { 0: { sector: 0 }, 1: { sector: 0 }, 2: { sector: 1 } }, sectors: [{ share: 1 }, { share: 0 }],
  villages: [village([[4, 5120]], 600)] });
const commuters = { "cautious|0": [[1, 600]] };

test("commuters reach their sector and lap there", () => {
  const { r } = sim(commute(5000), { demand: commuters });
  assert.ok(r.arrivals.morning[4] > 0, "sector 1's lift gets skiers in the morning");
  assert.ok(r.views.day[4] > 0, "and they lap it by day");
});

test("a queue on the quick way moves later routes to the other way", () => {
  const { r } = sim(commute(), { demand: commuters });
  assert.ok(r.waits.morning[0] > 20 * 60, `the small lift's queue averages ${Math.round(r.waits.morning[0] / 60)} min`);
  assert.ok(r.views.morning[2] > 0, "commuters routed after it builds take the big lift");
});

test("everyone is home by the end of the evening", () => {
  const { r } = sim(loop());
  assert.ok(r.report.notHome < 0.01, `${(100 * r.report.notHome).toFixed(1)}% not home`);
});

test("a ride down over capacity queues at its top", () => {
  // A gondola from the village (1) to the top (0), a 100-an-hour ride down, and a long slow black home.
  const s = { z: [2500, 1500], links: [lift(1, 0, 2000, 0, 400), { a: 0, b: 1, k: "download", len: 1000, rt: 400, cap: 100, lift: 0 },
    run(0, 1, 3000, 3, 0.3, { cm: 2000 })], lifts: { 0: { sector: 0 } }, sectors: [{ share: 0 }],
    villages: [village([[1, 2000]], 1000)] };
  const { r } = sim(s);
  assert.ok(r.waits.evening[1] > 60, `the ride down's queue averages ${Math.round(r.waits.evening[1])} s`);
  assert.ok(r.views.evening[1] <= 100 + 1e-6, "it carries no more than its capacity down");
});

test("a settled day lists no links; a trap is listed", () => {
  assert.deepEqual(sim(loop()).r.report.unsettled, []);
  // From X's top (0), a run back to the village (3) and a near-flat black into a loop (T, 2 → 1) with no way out.
  const s = { z: [2500, 2400, 1800, 1500],
    links: [lift(3, 0, 2000, 0, 600), run(0, 3), run(0, 2, 300, 3, 0.03, { cm: 2000 }), lift(2, 1, 2000, 1, 600), run(1, 2)],
    lifts: { 0: { sector: 0 }, 1: { sector: 0 } }, sectors: [{ share: 0 }], villages: [village([[3, 2000]], 1000)] };
  const { unsettled } = sim(s).r.report;
  assert.ok(unsettled.some((u) => u.link === 0), "the lift out of the village carries less and less");
});

test("the views follow the windows' settings", () => {
  const a = sim(loop()).r.views.morning[0];
  const b = sim(loop(), { params: { MORNING_TO_H: 9.25 } }).r.views.morning[0];
  assert.notEqual(a, b);
});

test("each test domain gives identical results when run twice", async () => {
  const { run } = await import("../src/index.js");
  const { domain } = await import("./helpers.js");
  for (const name of ["grandvalira", "les-trois-vallees", "serre-chevalier", "tignes-val-d-isere"]) {
    const [a, b] = [run(domain(name), P), run(domain(name), P)];
    for (const v of ["day", "morning", "evening"]) {
      assert.deepEqual(Array.from(a.links[v]), Array.from(b.links[v]), `${name} ${v}`);
      assert.deepEqual(Array.from(a.waits[v]), Array.from(b.waits[v]), `${name} ${v} waits`);
    }
  }
});
