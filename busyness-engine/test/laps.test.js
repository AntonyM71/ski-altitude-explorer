import { test } from "node:test";
import assert from "node:assert/strict";
import { network } from "../src/graph.js";
import { byGrade, pulls, exchange, gradientPull } from "../src/laps.js";
import { P, fixture } from "./helpers.js";

const lift = (a, b, cap, key) => ({ a, b, k: "lift", len: 1000, rt: 400, cap, lift: key });
const run = (a, b, g = 1, grad = 0.2, extra = {}) => ({ a, b, k: "run", len: 500, rt: 80, g, grad, ...extra });

const near = (a, b) => Math.abs(a - b) < 1e-9;
const one = { 0: { sector: 0 }, 1: { sector: 0 }, 2: { sector: 0 } };

// Junction 0 offers a 2,000 chairlift (to 3) and two blue runs, to junctions 1 and 2, each the bottom of another
// 2,000 chairlift.
const bigLiftBesideTwoRuns = () => network({ z: [2000, 1500, 1500, 2500],
  links: [lift(0, 3, 2000, 0), run(0, 1), run(0, 2), lift(1, 3, 2000, 1), lift(2, 3, 2000, 2), run(3, 0)],
  lifts: one, sectors: [{ share: 0 }] });

test("a big lift beside two runs to equal lifts: each run pulls as much as the lift at hand", () => {
  const pull = pulls(bigLiftBesideTwoRuns(), P);
  assert.equal(pull[0], 2.5);
  assert.ok(near(pull[1], 2.5) && near(pull[2], 2.5), `runs pull ${pull[1]}, ${pull[2]}`);
});

test("the lift at hand with a 10-minute queue pulls 1.25 and takes 1.25 / 6.25", () => {
  const wait = new Float64Array(6);
  wait[0] = 600;
  const pull = pulls(bigLiftBesideTwoRuns(), P, wait);
  assert.equal(pull[0], 1.25);
  assert.ok(near(pull[0] / (pull[0] + pull[1] + pull[2]), 1.25 / 6.25));
});

test("a run that ends at a 10-minute queue pulls half as much: 1.25", () => {
  const wait = new Float64Array(6);
  wait[3] = 600;
  const pull = pulls(bigLiftBesideTwoRuns(), P, wait);
  assert.ok(near(pull[1], 1.25), `run pulls ${pull[1]}`);
  assert.ok(near(pull[2], 2.5));
});

// Junction 0 offers a 1,600 chairlift and a run to junction 1, the bottom of a 4,000 chairlift.
const biggerLiftAhead = (g, extra = {}) => network({ z: [2000, 1950, 2600],
  links: [lift(0, 2, 1600, 0), run(0, 1, g, 0.2, extra), lift(1, 2, 4000, 1), run(2, 0)],
  lifts: one, sectors: [{ share: 0 }] });

test("a bigger lift a short run away: the blue run pulls 5.0 against the lift at hand's 2.0", () => {
  const pull = pulls(biggerLiftAhead(1), P);
  assert.equal(pull[0], 2);
  assert.ok(near(pull[1], 5));
  assert.ok(near(pull[1] / (pull[0] + pull[1]), 5 / 7));
});

test("a long black on the only way to the big lift pulls 2.0, as much as the lift at hand", () => {
  const pull = pulls(biggerLiftAhead(3, { cm: 1200 }), P);
  assert.ok(near(pull[1], 2), `black pulls ${pull[1]}`);
});

test("a black beside an easier way doesn't lower the pull of the run leading to them", () => {
  // A blue from 0 to 1; from 1, a long black and a blue both lead to 2, a 2,000 lift's bottom.
  const net = network({ z: [2400, 2200, 1800, 2600],
    links: [run(0, 1), run(1, 2, 3, 0.4, { cm: 1200 }), run(1, 2), lift(2, 3, 2000, 0), run(3, 0)],
    lifts: one, sectors: [{ share: 0 }] });
  const pull = pulls(net, P);
  assert.ok(near(pull[0], 2.5), `the blue above pulls ${pull[0]}`);
  assert.ok(near(pull[1], 1) && near(pull[2], 2.5), "at the fork, the black still pulls less than the blue");
});

test("a run that leads to no lift takes the domain's typical lift pull", () => {
  const net = network({ z: [2000, 1500, 2500, 1000],
    links: [lift(1, 2, 2000, 0), run(2, 1), run(1, 3)], lifts: one, sectors: [{ share: 0 }] });
  assert.ok(near(pulls(net, P)[2], 2.5));
});

test("a nursery slope beside a blue to an equal lift takes 1 / 21 of the skiers", () => {
  const net = network({ z: [2000, 1500, 1500, 2500],
    links: [run(0, 1, 0, 0.2, { nur: 1 }), run(0, 2), lift(1, 3, 2000, 0), lift(2, 3, 2000, 1), run(3, 0)],
    lifts: one, sectors: [{ share: 0 }] });
  const pull = pulls(net, P);
  assert.ok(near(pull[0] / (pull[0] + pull[1]), 1 / 21));
});

test("a magic carpet that's the only way up is taken", () => {
  const net = network({ z: [1600, 1500], links: [{ ...lift(1, 0, 600, 0), nur: 1 }, run(0, 1)],
    lifts: { 0: { sector: 0 } }, sectors: [{ share: 0 }] });
  assert.ok(pulls(net, P)[0] > 0);
});

const walkTo = (zFar) => network({ z: [2300, 1795, 2600, zFar],
  links: [lift(1, 0, 2500, 0), lift(3, 2, 1500, 1), { a: 1, b: 3, k: "walk", len: 184, rt: 184 }],
  lifts: { 0: { sector: 0 }, 1: { sector: 0 } }, sectors: [{ share: 0 }] });

test("a level walk to a nearby lift pulls like that lift: a gondola's bottom splits 3.125 to 1.875", () => {
  const pull = pulls(walkTo(1790), P);
  assert.equal(pull[0], 3.125);
  assert.ok(near(pull[2], 1.875));
});

test("a walk that climbs pulls like a near-flat run: 0.35 of the lift it leads to", () => {
  assert.ok(near(pulls(walkTo(1810), P)[2], 0.35 * 1.875));
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
