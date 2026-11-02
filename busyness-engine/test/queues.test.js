import { test } from "node:test";
import assert from "node:assert/strict";
import { network } from "../src/graph.js";
import { dayWaits } from "../src/queues.js";
import { P } from "./helpers.js";

const lift = (a, b, cap, key) => ({ a, b, k: "lift", len: 1000, rt: 400, cap, lift: key });
const run = (a, b) => ({ a, b, k: "run", len: 500, rt: 80, g: 1, grad: 0.2 });

// Junctions highest first: 0 the top of Y and Z, 1 the top of X, 2 the bottom of Y and Z, 3 the bottom of X.
// X (1,200 an hour) brings skiers to Y and Z (1,000 each). Y's sector commutes half its skiers away, so it releases
// only 500: overfull, with Z beside it. Y and Z both lead back to X, which is the only way on from its bottom.
const domain = () =>
  network({
    z: [2500, 2000, 1500, 1000],
    links: [lift(3, 1, 1200, 0), run(1, 2), lift(2, 0, 1000, 1), lift(2, 0, 1000, 2), run(0, 3)],
    lifts: { 0: { sector: 0 }, 1: { sector: 1 }, 2: { sector: 0 } },
    sectors: [{ share: 0 }, { share: 0.5 }],
  });

test("before waits: Y gets half of X's 1,200 though it releases 500, and X gets 1,500 though it releases 1,200", () => {
  const { liftLaps } = dayWaits(domain(), { ...P, QUEUE_PASSES: 0 });
  assert.ok(Math.abs(liftLaps.get(1) - 600) < 1 && Math.abs(liftLaps.get(0) - 1500) < 1);
});

test("a lift with an alternative beside it: its wait grows until skiers take the other", () => {
  const r = dayWaits(domain(), P);
  assert.ok(r.wait[2] > 0, "Y has a wait");
  assert.ok(r.liftLaps.get(1) <= 500 * 1.05, `Y gets ${r.liftLaps.get(1)}, about what it releases`);
});

test("a lift with no alternative keeps its queue", () => {
  const r = dayWaits(domain(), P);
  assert.ok(r.wait[0] > 60, `X waits ${r.wait[0]} s`);
  assert.ok(Math.abs(r.liftLaps.get(0) - 1500) < 1, "everyone still comes to X: there's no other way on");
});

test("a lift with room has no wait beyond loading", () => {
  const r = dayWaits(domain(), P);
  assert.equal(r.wait[3], 0);
});
