// Decision 011's matched observations, checked on the four test domains' structure files
// (tests/fixtures/busyness/domains/; refresh with python -m tests.busyness.fixtures --domains).
// Each test is named after the observation in docs/observations.md and decision 011's table.
import { test } from "node:test";
import assert from "node:assert/strict";
import { run } from "../src/index.js";
import { P, domain } from "./helpers.js";

const cache = new Map();
/** The engine's results for a test domain, with named runs (over 300 m, length-weighted) ranked in each view. */
function results(name) {
  if (cache.has(name)) return cache.get(name);
  const s = domain(name);
  const r = run(s, P);
  const by = new Map();
  for (const [id, x] of Object.entries(r.runs)) {
    const [runName, g] = s.runs[id];
    if (!runName) continue;
    const k = `${runName}|${g}`;
    const v = by.get(k) || { name: runName, g, len: 0, day: 0, morning: 0, evening: 0, commute: 0 };
    for (const view of ["day", "morning", "evening", "commute"]) v[view] += x[view] * x.len;
    v.len += x.len;
    by.set(k, v);
  }
  const runs = [...by.values()].filter((v) => v.len > 300);
  for (const v of runs) for (const view of ["day", "morning", "evening", "commute"]) v[view] /= v.len;
  const rank = (view, v) => 1 + runs.filter((o) => o[view] > v[view]).length;
  const named = (n, g) => {
    const found = runs.filter((v) => v.name === n && (g === undefined || v.g === g));
    assert.ok(found.length, `no run named ${n}`);
    return found;
  };
  const lift = (n) => {
    const found = Object.values(r.lifts).filter((l) => !l.nursery && l.name === n);
    assert.ok(found.length, `no lift named ${n}`);
    return found[0];
  };
  const out = { s, r, runs, rank, named, lift };
  cache.set(name, out);
  return out;
}

test("Les Trois Vallées: the Funitel 3 Vallées is full at the start of the day", () => {
  const { lift } = results("les-trois-vallees");
  assert.ok(lift("Funitel 3 Vallées").morning >= 1.0);
});

test("Les Trois Vallées: Lac de la Chambre is busy", () => {
  const { named, rank } = results("les-trois-vallees");
  for (const v of named("Lac de la Chambre")) assert.ok(rank("day", v) <= 10, `rank ${rank("day", v)}`);
});

test("Tignes–Val d'Isère: the Face de Bellevarde is less chewed up than Joseray by evening", () => {
  const { named } = results("tignes-val-d-isere");
  assert.ok(named("Face de Bellevarde", 3)[0].evening < named("Joseray", 2)[0].evening);
});

test("Tignes–Val d'Isère: Henri, Combe and Lac are busy", () => {
  const { named, rank, runs } = results("tignes-val-d-isere");
  for (const n of ["Henri", "Combe", "Lac"]) {
    const v = named(n, 1)[0];
    assert.ok(rank("day", v) <= runs.length / 4, `${n} is ${rank("day", v)} of ${runs.length}`);
  }
});

test("Tignes–Val d'Isère: Edelweiss carries Tignes to Val d'Isère traffic", () => {
  const { named, rank } = results("tignes-val-d-isere");
  const v = named("Edelweiss", 1)[0];
  assert.ok(rank("day", v) <= 10, `rank ${rank("day", v)}`);
  assert.ok(v.commute / v.day > 0.5, `commuters are ${Math.round((100 * v.commute) / v.day)}%`);
});

test("Tignes–Val d'Isère: staying in Tignes, home down Johan Clarey", () => {
  const { named, rank, runs } = results("tignes-val-d-isere");
  const v = named("Johan Clarey", 3)[0];
  assert.ok(rank("evening", v) <= runs.length / 4, `rank ${rank("evening", v)}`);
});

test("Tignes–Val d'Isère: people ride Solaise, the Olympique and Tovière down", () => {
  const { lift } = results("tignes-val-d-isere");
  for (const n of ["Solaise", "Olympique", "Tovière"]) {
    const l = lift(n);
    assert.ok(l.down > 300 && l.down <= l.cap * 1.05, `${n}: ${Math.round(l.down)} an hour down, capacity ${l.cap}`);
  }
});

test("Tignes–Val d'Isère: Le Fornet's cable car is adequate for its village", () => {
  const { lift } = results("tignes-val-d-isere");
  assert.ok(lift("Fornet").morning < 1.0);
});

test("Serre Chevalier: Pelvoux and Traverse are busy", () => {
  const { named, rank } = results("serre-chevalier");
  assert.ok(rank("day", named("Pelvoux", 0)[0]) <= 5);
  assert.ok(rank("day", named("Traverse", 1)[0]) <= 5);
});

test("Serre Chevalier: Le Monêtier's lifts head over to Cucumelle", () => {
  const { lift, r } = results("serre-chevalier");
  const cucumelle = lift("Cucumelle");
  const ranked = Object.values(r.lifts).filter((l) => !l.nursery).sort((a, b) => b.morning - a.morning);
  assert.ok(cucumelle.morning >= 0.8 && ranked.indexOf(cucumelle) < 5);
});

test("Serre Chevalier: some people ride Prorel down, never full", () => {
  const { lift } = results("serre-chevalier");
  for (const n of ["Prorel 1", "Prorel 2"]) {
    const l = lift(n);
    assert.ok(l.down > 0.05 * l.cap && l.down < 0.5 * l.cap, `${n}: ${Math.round(l.down)} of ${l.cap}`);
  }
});

test("Serre Chevalier: Pylônes is crossed by greens, so it's never long without a way out", () => {
  const { s } = results("serre-chevalier");
  const pieces = s.links.filter((l) => l.k === "run" && s.runs[l.run][0] === "Pylônes");
  assert.ok(pieces.length > 1 && Math.max(...pieces.map((l) => l.cm)) < 800);
});

test("Grandvalira: the Soldeu gondola is busy in the morning, but not swamped", () => {
  const { lift } = results("grandvalira");
  const l = lift("TC8 Soldeu");
  assert.ok(l.morning > 0.5 && l.morning < 1.2, `${l.morning.toFixed(2)}x`);
});

test("Grandvalira: Grau Roig is a thoroughfare, not a village", () => {
  const { s } = results("grandvalira");
  assert.ok(!s.villages.some((v) => v.name === "Grau Roig"));
  assert.ok(s.villages.some((v) => v.name === "Pas de la Casa"));
});
