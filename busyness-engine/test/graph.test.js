import { test } from "node:test";
import assert from "node:assert/strict";
import { gaussian } from "../src/random.js";
import { network, routes, addPath } from "../src/graph.js";

test("a seed always gives the same sequence, roughly standard normal", () => {
  const a = gaussian(1);
  const b = gaussian(1);
  const xs = Array.from({ length: 20000 }, () => a());
  assert.deepEqual(Array.from({ length: 5 }, () => b()), xs.slice(0, 5));
  const mean = xs.reduce((s, x) => s + x) / xs.length;
  const sd = Math.sqrt(xs.reduce((s, x) => s + (x - mean) ** 2, 0) / xs.length);
  assert.ok(Math.abs(mean) < 0.03 && Math.abs(sd - 1) < 0.03, `mean ${mean}, sd ${sd}`);
  assert.notEqual(gaussian(2)(), xs[0]);
});

// 0 -> 1 -> 3 takes 10 + 10; 0 -> 2 -> 3 takes 5 + 30; 3 -> 0 is a lift (40).
const tiny = {
  z: [2000, 1900, 1850, 1500],
  links: [
    { a: 0, b: 1, k: "run", len: 100, rt: 10, g: 1, grad: 0.2 },
    { a: 1, b: 3, k: "run", len: 100, rt: 10, g: 1, grad: 0.2 },
    { a: 0, b: 2, k: "run", len: 50, rt: 5, g: 1, grad: 0.2 },
    { a: 2, b: 3, k: "run", len: 300, rt: 30, g: 1, grad: 0.2 },
    { a: 3, b: 0, k: "lift", len: 1000, rt: 40, cap: 1000, lift: 9 },
  ],
  lifts: { 9: { sector: 0 } },
};

test("quickest routes forward and back, and the path along them", () => {
  const net = network(tiny);
  const times = Float64Array.from(tiny.links, (l) => l.rt);
  const fwd = routes(net, [0], times);
  assert.deepEqual(Array.from(fwd.best), [0, 10, 5, 20]);
  const back = routes(net, [0], times, true); // to junction 0
  assert.equal(back.best[3], 40);
  assert.equal(back.best[1], 50);
  const acc = new Float64Array(tiny.links.length);
  addPath(net, fwd, 3, 0, false, 7, acc);
  assert.deepEqual(Array.from(acc), [7, 7, 0, 0, 0]);
  assert.deepEqual(net.lifts, [4]);
});
