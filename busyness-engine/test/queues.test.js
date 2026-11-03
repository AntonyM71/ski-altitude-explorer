import { test } from "node:test";
import assert from "node:assert/strict";
import { network } from "../src/graph.js";
import { dayWaits } from "../src/queues.js";
import { P } from "./helpers.js";

const lift = (a, b, cap, key) => ({ a, b, k: "lift", len: 1000, rt: 400, cap, lift: key });
const run = (a, b, g = 1) => ({ a, b, k: "run", len: 500, rt: 80, g, grad: 0.2, cm: 1200 });

// Junctions: 0 the top of Y and Z, 1 the top of X, 2 the bottom of Y, 3 the bottom of X, 4 the bottom of Z.
// X (1,400 an hour) brings skiers down a blue to Y (600) or a black to Z (1,200), so Y gets 1,000: overfull, with Z
// as the other way on. Y's sector commutes half its skiers away, so Y's top releases 300, and Z's 1,200. Both lead
// back to X, which gets 1,500, over its capacity, and is the only way on from its bottom.
const domain = () =>
  network({
    z: [2500, 2000, 1500, 1000, 1500],
    links: [lift(3, 1, 1400, 0), run(1, 2), run(1, 4, 3), lift(2, 0, 600, 1), lift(4, 0, 1200, 2), run(0, 3)],
    lifts: { 0: { sector: 0 }, 1: { sector: 1 }, 2: { sector: 0 } },
    sectors: [{ share: 0 }, { share: 0.5 }],
  });

test("before waits: Y gets 1,000 for its 600 capacity, and X 1,500 for its 1,400", () => {
  const { liftLaps } = dayWaits(domain(), { ...P, QUEUE_PASSES: 0 });
  assert.ok(Math.abs(liftLaps.get(1) - 1000) < 1 && Math.abs(liftLaps.get(0) - 1500) < 1);
});

test("a lift with an alternative: its wait grows until skiers take the other", () => {
  const r = dayWaits(domain(), P);
  assert.ok(r.wait[3] > 0, "Y has a wait");
  assert.ok(r.liftLaps.get(1) <= 600 * 1.05, `Y gets ${r.liftLaps.get(1)}, about its capacity`);
});

test("a lift with no alternative keeps its queue", () => {
  const r = dayWaits(domain(), P);
  assert.ok(r.wait[0] > 0, `X waits ${r.wait[0]} s`);
  assert.ok(Math.abs(r.liftLaps.get(0) - 1500) < 1, "everyone still comes to X: there's no other way on");
});

test("a lift with room has no wait beyond loading", () => {
  const r = dayWaits(domain(), P);
  assert.equal(r.wait[4], 0, "Z, under its capacity, has none");
});
