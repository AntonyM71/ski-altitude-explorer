// Shared test helpers: the parameters, the shared fixtures, and test domains' structure files.
import { readFileSync } from "node:fs";

export const P = JSON.parse(readFileSync(new URL("../src/params.json", import.meta.url), "utf8"));

/** A small hand-made network from tests/fixtures/busyness/, shared with the Python tests. */
export const fixture = (name) =>
  JSON.parse(readFileSync(new URL(`../../tests/fixtures/busyness/${name}.json`, import.meta.url), "utf8"));

/** A test domain's structure file from tests/fixtures/busyness/domains/. */
export const domain = (name) =>
  JSON.parse(readFileSync(new URL(`../../tests/fixtures/busyness/domains/${name}.json`, import.meta.url), "utf8"));
