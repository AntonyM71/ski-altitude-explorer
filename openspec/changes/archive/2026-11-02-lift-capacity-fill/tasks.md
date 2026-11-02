# Tasks

## 1. Name patterns, shared

- [x] 1.1 Create `busyness/lifts.py` with the name patterns from `prototypes/lift_capacity.py` (`name_hints`: the fast class and seats from names). Add `tests/busyness/test_lifts.py` covering each pattern family, including "Doppelmayr" giving no seats and recorded seats winning over the name. Verify that `uv run pytest tests/busyness/test_lifts.py` passes.
- [x] 1.2 Make `prototypes/lift_capacity.py` import the patterns from `busyness.lifts` and delete its own copy. Verify that `--names` still reports 804 fast-named chairlifts and 1,211 of 1,223 seats agreeing.

## 2. Tables

- [x] 2.1 Add `--params` to `prototypes/lift_capacity.py`. It prints `CHAIR_CAP`, `CHAIR_SPEED` and `GONDOLA_CAP` as Python, fitted on all lifts in ski areas with cells under 5 lifts left out, and the cable car constants from `fit_cable` on all ski-area lifts. Verify that it runs and that its values match decision 013, for example a two-seat chairlift at about 1,200 an hour and the cable car constants near 8.5 m/s and 140 s.
- [x] 2.2 Paste the output into `busyness/params.py`, under a "Lift estimates (013)" heading, with `SEATS_MAX`, `LONG_M`, `CABLE_MIN_SEATS`, `CABLE_SPEED` and `CABLE_LOAD_S`. Verify that `uv run ruff check busyness` passes.

## 3. Estimates

- [x] 3.1 In `busyness/lifts.py`, add the function that turns a lift's raw properties and length into capacity, speed and their sources, following busyness-lift-estimates and design.md: fall back within a seat count before the type value, and the fast hint doesn't change the source. Extend `tests/busyness/test_lifts.py` with one test per scenario in `specs/busyness-lift-estimates/spec.md`. Verify that the tests pass.

## 4. Pipeline

- [x] 4.1 In `busyness/partition.py`, replace `cap_known` on `Feature` with `cap_src`, and add `speed` and `speed_src`. `_lift` computes the lift's length and calls the estimate function. Update `tests/busyness/helpers.py` and `test_partition.py`, adding a case where a lift with seats and no capacity gets its estimate. Verify that `uv run pytest tests/busyness` passes.
- [x] 4.2 In `busyness/network.py`, take a lift's ride time from `f.dur or length / f.speed`. Verify that `uv run pytest tests/busyness/test_network.py` passes.
- [x] 4.3 In `busyness/structure.py`, write `cap_src` and `speed_src` for each lift in place of `cap_known`, and include them in the fingerprint. Bump `MODEL_VERSION` to 3. Verify that `uv run pytest tests/busyness` and `uv run ruff check busyness tests` pass.
- [x] 4.4 Update the busyness-pipeline structure-file description in decision 012, if it lists `cap_known`. Verify by grepping `docs/` and `openspec/specs/` for `cap_known`, with none left.

## 5. Test domains and observations

- [x] 5.1 Build the four test domains (`python -m busyness build --name ...`) and regenerate the fixtures with `python -m tests.busyness.fixtures --domains`. Verify that the structure files carry `cap_src` and `speed_src` and model version 3.
- [x] 5.2 Run the engine tests (`npm test` in `busyness-engine/`) and `uv run pytest`. Verify that both pass. If an observation test fails, investigate it before going on, and record the outcome in 5.3.
- [x] 5.3 Recheck decision 011's comparison table against the new results, and update the numbers that moved. Verify that no row marked ✓ has become ✗ without a recorded reason.

## 6. Docs

- [x] 6.1 Update decision 013's code line to point at `busyness/lifts.py` and `busyness/params.py`. Make decision 004's "Missing capacity" bullet point to 013 for lifts with seats. Verify that the links resolve.

## Workflow follow-up

- Review the results with the project owner before archiving.
- Archive the change with `/opsx:archive`, which merges the deltas into `openspec/specs/`.
