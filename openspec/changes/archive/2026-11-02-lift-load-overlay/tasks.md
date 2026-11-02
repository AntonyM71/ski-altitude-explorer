# Tasks

## 1. Engine

- [x] 1.1 Add `LIFT_LOAD_BANDS: [0.5, 0.8, 1.0]` to `busyness-engine/src/params.json`. In `views.js` `bands()`, cut lifts at those fixed thresholds instead of percentiles, giving nursery lifts `null`, and update the doc comment. In `test/views.test.js`, limit the percentile test to runs, and add lift cases: a quiet domain with every lift in band 0, 1.2× in band 3, exactly 1.0× in band 2, and a nursery lift `null`. Verify that `npm test` in `busyness-engine/` passes.
- [x] 1.2 Move the worker's per-lift merge into an exported function in `views.js`, giving each lift id and view `[band, load]`, from the piece with the highest load. Call it from `worker.js` and update the worker's header comment. Add a test for a lift mapped in two pieces. Verify that `npm test` passes.

## 2. Site

- [x] 2.1 Choose four purple steps, light to dark, and check them with the dataviz validator in ordinal mode (`node <dataviz skill>/scripts/validate_palette.js "<hexes>" --ordinal`) against the map's background colour. Verify that every hard check passes, and note the result in a comment beside the colours in `index.html`.
- [x] 2.2 In `index.html`, colour lift lines and dashed drag lifts from the lift band with the purple ramp. Nursery lifts keep the plain lift ink, and runs keep `BAND_COLOR`. Read the worker's new `[band, load]` shape. Verify by serving the repository locally (`python -m http.server`), opening a modelled test domain with the overlay on in each view, and taking a screenshot. Lifts must read purple and distinct from runs, and the lightest step must still be visible on the terrain.
- [x] 2.3 Replace the busyness legend with two groups: "Runs, for this domain: quiet … busiest" and "Lifts, of capacity: under 50% … over 100%". Change the lift hover to "Busyness in the <view>: modelled at N% of capacity" (nearest 10%), with no queue wording. Drop "a ranking" from the toggle's tooltip. Verify in the same local check: hovering over a lift over capacity in the morning view shows its percentage, and the legend shows both scales.

## 3. Docs

- [x] 3.1 Write `docs/decisions/014-lifts-by-load.md`: lifts are shown by modelled load against capacity, in fixed bands, and what a percentage does and doesn't mean (domain skiers sized to capacity, 004), linking issue #5 for the fix. Add it to `docs/decisions/README.md`, and narrow decision 012's "relative within the domain" bullet to runs, pointing to 014. Verify that the links resolve.

## 4. Check

- [x] 4.1 Run `npm test` in `busyness-engine/` and `uv run pytest`. Verify that both pass, and that decision 011's observation tests are unaffected, since the model's numbers don't change.

## Workflow follow-up

- Review the overlay with the project owner before archiving.
- Archive the change with `/opsx:archive`, which merges the delta into `openspec/specs/`.
