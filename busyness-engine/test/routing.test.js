import { test } from "node:test";
import assert from "node:assert/strict";
import { network, routes } from "../src/graph.js";
import { routeTimes } from "../src/routing.js";
import { routeWithRidesDown } from "../src/evening.js";
import { sectorEnds, gravity } from "../src/demand.js";
import { laps as computeLaps } from "../src/laps.js";
import { run } from "../src/index.js";
import { P, fixture } from "./helpers.js";

test("two equal valleys share commuters both ways, and nobody commutes in a one-sector resort", () => {
  const linked = run(fixture("linked_valleys"), P);
  const total = Object.values(linked.demand).flat().reduce((s, [, c]) => s + c, 0);
  // 30% of each valley's 1,143 skiers commute to the other (no other sector to choose from).
  assert.ok(Math.abs(total - 0.3 * 4 * 571.4) < 1, `commuters ${total}`);
  const one = run(fixture("shared_top"), P);
  assert.equal(Object.values(one.demand).flat().length, 0);
  assert.ok(one.links.out.every((x) => x === 0));
});

test("gravity: of two equal sectors, the one an hour nearer draws e times as many", () => {
  // Village at junction 0; sector 1's lift bottom is 30 min away, sector 2's 90 min.
  const s = {
    z: [1000, 900, 800],
    links: [
      { a: 0, b: 1, k: "run", len: 1, rt: 1800, g: 1, grad: 0.2 },
      { a: 0, b: 2, k: "run", len: 1, rt: 5400, g: 1, grad: 0.2 },
      { a: 0, b: 0, k: "lift", len: 1, rt: 1, cap: 1000, lift: 0 },
      { a: 1, b: 0, k: "lift", len: 1, rt: 1, cap: 1000, lift: 1 },
      { a: 2, b: 0, k: "lift", len: 1, rt: 1, cap: 1000, lift: 2 },
    ],
    lifts: { 0: { sector: 0 }, 1: { sector: 1 }, 2: { sector: 2 } },
    sectors: [{ cap: 1000, share: 0.5 }, { cap: 1000, share: 0.5 }, { cap: 1000, share: 0.5 }],
    villages: [{ sector: 0, nodes: [[0, 1000]], cap: 1000, skiers: 100 }],
  };
  const net = network(s);
  const d = gravity(net, P, sectorEnds(net), new Float64Array(5));
  const [[, near], [, far]] = d["intermediate|0"].sort((a, b) => a[0] - b[0]);
  assert.ok(Math.abs(near / far - Math.E) < 1e-9);
});

test("cautious skiers take the slower blues; strong skiers take the long black", () => {
  // Junction 0 to 2: a 1,200 m black (100 s) or two blues (150 s).
  const s = {
    z: [2000, 1800, 1500],
    links: [
      { a: 0, b: 2, k: "run", len: 1200, rt: 100, g: 3, grad: 0.4, cm: 1200 },
      { a: 0, b: 1, k: "run", len: 500, rt: 75, g: 1, grad: 0.2 },
      { a: 1, b: 2, k: "run", len: 500, rt: 75, g: 1, grad: 0.2 },
    ],
  };
  const net = network(s);
  const firstLink = (ability) => {
    const r = routes(net, [0], routeTimes(net, P, { feel: P.ABILITIES[ability].feel, laps: new Float64Array(3) }));
    let n = 2;
    let i;
    while (n !== 0) {
      i = r.prev[n];
      n = net.L[i].a;
    }
    return i;
  };
  assert.equal(firstLink("cautious"), 1);
  assert.equal(firstLink("strong"), 0);
});

test("the same structure gives identical traffic every time", () => {
  const a = run(fixture("linked_valleys"), P);
  const b = run(fixture("linked_valleys"), P);
  assert.deepEqual(Array.from(a.links.day), Array.from(b.links.day));
  assert.deepEqual(Array.from(a.links.evening), Array.from(b.links.evening));
});

test("routes vary: two nearly equal routes both carry commuters", () => {
  // In the linked valleys each valley's two lifts feed the link; commuters spread over more than one link out.
  const r = run(fixture("linked_valleys"), P);
  const s = fixture("linked_valleys");
  const used = s.links.map((l, i) => [l, r.links.out[i]]).filter(([l, x]) => l.k === "lift" && x > 1);
  assert.ok(used.length >= 2, "commuters use more than one lift out");
});

test("too many riding down: the excess skis home", () => {
  // A village at the bottom; its locals spend the day above. Home: ride the gondola (cap 100) or ski 3,000 s.
  const s = {
    z: [2000, 1000],
    links: [
      { a: 1, b: 0, k: "lift", len: 1000, rt: 300, cap: 100, lift: 0 },
      { a: 0, b: 1, k: "run", len: 3000, rt: 3000, g: 1, grad: 0.3 },
      { a: 0, b: 1, k: "download", len: 1000, rt: 300, cap: 100, lift: 0 },
    ],
    lifts: { 0: { sector: 0, day_sectors: { 0: 1 } } },
    sectors: [{ cap: 100, share: 0 }],
    villages: [{ sector: 0, nodes: [[1, 100]], cap: 100, skiers: 1000 }],
  };
  const net = network(s);
  const { laps } = computeLaps(net, P);
  const once = routeWithRidesDown(net, { ...P, DOWNLOAD_PASSES: 1 }, { laps, demand: { "cautious|0": [], "intermediate|0": [], "strong|0": [] }, ends: sectorEnds(net) });
  const capped = routeWithRidesDown(net, P, { laps, demand: { "cautious|0": [], "intermediate|0": [], "strong|0": [] }, ends: sectorEnds(net) });
  assert.ok(once.evening[2] > 100, `without the cap, ${once.evening[2]} an hour ride down`);
  assert.ok(capped.evening[2] < once.evening[2] && capped.evening[1] > once.evening[1], "the excess skis home");
  assert.ok(capped.passes > 1);
});
