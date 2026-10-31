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
