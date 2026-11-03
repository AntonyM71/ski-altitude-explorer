# Tasks

## 1. Engine

- [x] 1.1 Add `ALT_RATIO` (2) to `busyness-engine/src/params.json`, with an `_about` note that it's an unsourced fair-weather guess (known issue 8). In `laps.js`, give `pulls` an options argument (`{ altitude }`). When it's on, multiply each lift's pull by its altitude factor, and each run's by the altitude factor ahead (one bottom-up pass, before the queue lookahead). Add tests for the busyness-laps scenarios "Two equal lifts at different heights", "Two runs to lifts at different heights" and "A low resort". Also test that pulls without the option are unchanged. Verify that `npm test` passes.
- [x] 1.2 Make `dayWaits` in `queues.js` use the altitude option for the day laps only (not `descents`). Check that `exchange` still uses base pulls: the scenario "Sectors are unchanged", plus the existing Python–engine exchange-share check. Verify that `npm test` and `uv run pytest` pass.

## 2. Results

- [x] 2.1 Regenerate the fixtures (`params.json` changes the fingerprint) and run both suites. For the four test domains, record:
  - the share of run traffic in the low, mid and high thirds;
  - the day waits at the valley lifts (Daille, the Funival, Aravet, Pré Chabert);
  - the day waits at the top lifts (the Grande Motte, the Montet, Cucumelle, Cime Caron).

  Notes (ratio 2):
  - **Run traffic, low/mid/high thirds:** Tignes–Val d'Isère 29/67/4, Les Trois Vallées 24/58/18, Serre Chevalier 30/54/16, Grandvalira 13/50/37. Unchanged within a point, as expected while lift tops release full capacity.
  - **Valley waits ease:** Daille 1,132 → 847 minutes, Aravet 335 → 264, Pré Chabert 339 → 236. Portella and Plateau 1 rise a little.
  - **Top lifts:** the Grande Motte 12 minutes and the Montet 0. Two are over 30:
    - Cucumelle 52, was 38. The project owner notes it's a key transit route, so it should be busy.
    - Cime Caron 142, was 125. Odd, and put down to the population being wrong (#6).
  - Both were over 30 before this change. The project owner chose to carry on and revisit after conservation.

  Verify that both suites pass (the known `todo`s may stay), and that no top lift's day wait exceeds 30 minutes. If one does, record it and pause.
- [x] 2.2 Recheck decision 011's table and update the numbers that moved. Verify that no row marked ✓ has become ✗ without a recorded reason.

## 3. Docs

- [x] 3.1 Update decision 006 (pull: the altitude factor, fair weather only) and `docs/known-issues.md`:
  - **Items 18 and 22:** the preference is in, and its effect awaits conservation (#6, item 17).
  - **Item 8 "Other guesses":** `ALT_RATIO`.
  - **The status diagram:** add a Laps item for altitude preference.

  Verify that the links resolve and the numbers match 2.1.

## Workflow follow-up

- Archive with `/opsx:archive`, then start the population and conservation change.
