import { test } from "node:test";
import assert from "node:assert/strict";
import { network } from "../src/graph.js";
import { byGrade, pulls, lapSources, laps, exchange, gradientPull } from "../src/laps.js";
import { P, fixture } from "./helpers.js";

const lift = (a, b, cap, key) => ({ a, b, k: "lift", len: 1000, rt: 400, cap, lift: key });
const run = (a, b, g = 1, grad = 0.2, extra = {}) => ({ a, b, k: "run", len: 500, rt: 80, g, grad, ...extra });

test("a lift in a sector with 40% commuting sends 1,200 an hour from a 2,000 lift", () => {
  const s = { z: [2000, 1500], links: [lift(1, 0, 2000, 0), run(0, 1)], lifts: { 0: { sector: 0 } },
              sectors: [{ share: 0.4 }] };
  assert.equal(lapSources(network(s))[0], 1200);
});

test("two lifts sharing a top station: their riders add up", () => {
  const s = fixture("shared_top");
  const net = network(s);
  const tops = net.lifts.map((i) => s.links[i].b);
  assert.equal(new Set(tops).size, 1, "the fixture's two lifts share a top");
  assert.equal(lapSources(net)[tops[0]], 4000); // one sector: no commuting
  const { liftLaps } = laps(net, P);
  const total = [...liftLaps.values()].reduce((a, b) => a + b);
  assert.ok(Math.abs(total - 4000) < 1, `all 4,000 reach a lift, got ${total}`);
});

test("a 2,000 lift beside two ordinary blue runs takes 2.5 / 4.5 of the skiers", () => {
  const s = { z: [2000, 1900, 1500, 1400],
    links: [run(0, 1), lift(1, 0, 2000, 0), run(1, 2), run(1, 3), lift(2, 0, 1000, 1), lift(3, 0, 1000, 2)],
    lifts: { 0: { sector: 0 }, 1: { sector: 0 }, 2: { sector: 0 } }, sectors: [{ share: 0 }] };
  const net = network(s);
  const src = new Float64Array(4);
  src[1] = 4500;
  const pull = pulls(net, P);
  assert.equal(pull[1], 2.5);
  const from1 = [1, 2, 3].map((i) => (4500 * pull[i]) / (pull[1] + pull[2] + pull[3]));
  assert.deepEqual(from1.map(Math.round), [2500, 1000, 1000]);
});

test("a lift with a 10-minute queue pulls half as much: two equal lifts split a third and two thirds", () => {
  const s = { z: [2000, 1900, 1500, 1400],
    links: [run(0, 1), lift(1, 0, 2000, 0), lift(2, 0, 2000, 1), lift(3, 0, 2000, 2), run(1, 2), run(1, 3)],
    lifts: { 0: { sector: 0 }, 1: { sector: 0 }, 2: { sector: 0 } }, sectors: [{ share: 0 }] };
  const net = network(s);
  const wait = new Float64Array(s.links.length);
  wait[2] = 600; // ten minutes beyond loading
  const pull = pulls(net, P, wait);
  assert.equal(pull[2], 1.25);
  assert.equal(pull[3], 2.5);
  assert.ok(Math.abs(pull[2] / (pull[2] + pull[3]) - 1 / 3) < 1e-12);
  // The busyness-laps scenario: the queued lift beside two blue runs takes 1.25 / 3.25.
  assert.ok(Math.abs(pull[2] / (pull[2] + 1 + 1) - 1.25 / 3.25) < 1e-12);
});

test("a walk to a nearby lift pulls like that lift: a gondola's bottom splits 3.125 to 1.875", () => {
  const s = { z: [2300, 1795, 2600, 1810],
    links: [lift(1, 0, 2500, 0), lift(3, 2, 1500, 1), { a: 1, b: 3, k: "walk", len: 184, rt: 184 }],
    lifts: { 0: { sector: 0 }, 1: { sector: 0 } }, sectors: [{ share: 0 }] };
  const pull = pulls(network(s), P);
  assert.equal(pull[0], 3.125);
  assert.equal(pull[2], 1.875);
});

test("queues are seen ahead: of two equal blue runs, the one ending at a 10-minute queue takes a third", () => {
  // Junction 0 offers two blue runs: to junction 1 (a lift with a queue) and junction 2 (a lift with none).
  const s = { z: [2000, 1500, 1500, 2500],
    links: [run(0, 1), run(0, 2), lift(1, 3, 2000, 0), lift(2, 3, 2000, 1), run(3, 0)],
    lifts: { 0: { sector: 0 }, 1: { sector: 0 } }, sectors: [{ share: 0 }] };
  const net = network(s);
  const wait = new Float64Array(s.links.length);
  wait[2] = 600;
  const pull = pulls(net, P, wait);
  assert.ok(Math.abs(pull[0] - 0.5) < 1e-12, "a run that ends at a queue: its pull halves to 0.5");
  assert.ok(Math.abs(pull[0] / (pull[0] + pull[1]) - 1 / 3) < 1e-12);
});

test("with no waits, pulls are exactly today's", () => {
  const s = fixture("fork_and_loop");
  const net = network(s);
  assert.deepEqual(Array.from(pulls(net, P, new Float64Array(s.links.length))), Array.from(pulls(net, P)));
});

test("skiers favour higher areas by day: of two equal lifts, the one at the highest bottom takes two thirds", () => {
  // Junction 0 (1,800 m) offers a lift from there and runs to junction 1 (the highest bottom, 2,400) and 2 (the lowest).
  const s = { z: [2600, 2400, 1200, 3000],
    links: [lift(1, 3, 2000, 0), lift(2, 3, 2000, 1), run(0, 1), run(0, 2), run(3, 0)],
    lifts: { 0: { sector: 0 }, 1: { sector: 0 } }, sectors: [{ share: 0 }] };
  const net = network(s);
  const pull = pulls(net, P, null, { altitude: true });
  assert.ok(Math.abs(pull[0] / (pull[0] + pull[1]) - 2 / 3) < 1e-12, "two equal lifts at different heights");
  assert.ok(Math.abs(pull[2] / (pull[2] + pull[3]) - 2 / 3) < 1e-12, "two runs to lifts at different heights");
});

test("altitude is relative to the domain: a low resort's highest lift bottom gets the highest factor", () => {
  const make = (lo, hi) => network({ z: [hi + 200, hi, lo, hi + 400],
    links: [lift(1, 3, 2000, 0), lift(2, 3, 2000, 1), run(0, 1), run(0, 2), run(3, 0)],
    lifts: { 0: { sector: 0 }, 1: { sector: 0 } }, sectors: [{ share: 0 }] });
  const low = pulls(make(600, 1200), P, null, { altitude: true });
  const high = pulls(make(1800, 3000), P, null, { altitude: true });
  assert.deepEqual(Array.from(low), Array.from(high));
});

test("without the altitude option, pulls are unchanged", () => {
  const s = fixture("fork_and_loop");
  const net = network(s);
  assert.deepEqual(Array.from(pulls(net, P, null, {})), Array.from(pulls(net, P)));
});

test("sectors are unchanged: exchange shares ignore the altitude preference", () => {
  const s = fixture("two_valleys");
  const net = network(s);
  const key = net.L[net.lifts[0]].lift;
  assert.deepEqual([...exchange(net, P, key)], [...exchange(net, { ...P, ALT_RATIO: 4 }, key)]);
});

test("near-flat runs pull 0.35 of a normal run; very steep 0.6", () => {
  assert.equal(gradientPull(0.03, P.GRADIENT_PULL), 0.35);
  assert.equal(gradientPull(0.08, P.GRADIENT_PULL), 0.7);
  assert.equal(gradientPull(0.3, P.GRADIENT_PULL), 1);
  assert.equal(gradientPull(0.5, P.GRADIENT_PULL), 0.6);
});

test("short blacks count like reds, long ones fully black, and blend between", () => {
  const black = (cm) => ({ g: 3, cm });
  assert.equal(byGrade(black(250), P.GRADE_PULL, P), P.GRADE_PULL[2]);
  assert.equal(byGrade(black(1200), P.GRADE_PULL, P), P.GRADE_PULL[3]);
  assert.ok(Math.abs(byGrade(black(650), P.GRADE_PULL, P) - (P.GRADE_PULL[2] + P.GRADE_PULL[3]) / 2) < 1e-12);
});

for (const name of ["shared_top", "fork_and_loop", "two_valleys"]) {
  test(`laps agree with the pipeline's exact exchange shares: ${name}`, () => {
    const s = fixture(name);
    const net = network(s);
    for (const [from, expected] of Object.entries(s.expected.exchange)) {
      const got = exchange(net, P, Number(from));
      for (const [to, share] of Object.entries(expected)) {
        const g = got.get(Number(to)) || 0;
        assert.ok(Math.abs(g - share) <= 0.001, `lift ${from} -> ${to}: engine ${g}, pipeline ${share}`);
      }
    }
  });
}
