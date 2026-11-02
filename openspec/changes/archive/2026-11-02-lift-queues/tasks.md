# Tasks

## 0. Before starting

- [x] 0.1 Check that the lift-bottom walks change (known issue 16) is archived, and rebuild the four test domains and their fixtures on its network. Verify that `openspec list` shows it archived, and that the fixtures carry its walking links.

## 1. Day waits and the lookahead (laps)

- [x] 1.1 Add `QUEUE_TOLERANCE_MIN` (10) and `QUEUE_PASSES` (12) to `busyness-engine/src/params.json`, with an `_about` note that they're unsourced (known issue 8). Make `pulls()` in `laps.js` take optional waits, and divide a lift's pull by 1 + its extra wait ÷ `QUEUE_TOLERANCE_MIN`. Add a test for the busyness-queues scenario "Two equal lifts, one with a queue" and the busyness-laps scenario "The same lift with a queue". Verify that `npm test` passes.
- [x] 1.2 Rework `busyness-engine/src/queues.js` to the overload waits in design.md:
  - lift tops release capacity × (1 − share) as today;
  - each lift's descent time is measured once with base pulls;
  - waits move halfway towards visit × arrivals ÷ release − ride − descent, until no wait moves over 30 s or `QUEUE_PASSES` is reached.

  Remove the population, visit-rate and Little's-law code drafted for full conservation. Test the busyness-queues scenarios "A lift with an alternative beside it", "A lift with no alternative" and "A lift with room". Verify that `npm test` passes.
- [x] 1.3 Add the lookahead: one bottom-up pass over the junctions giving each run the queue factor ahead of it, with `pulls()` dividing a run's pull by it. Test the busyness-queues scenario "Two runs to different lifts" and the busyness-laps scenario "A run that ends at a queue". Also test that with no waits, pulls are exactly today's. Verify that `npm test` passes.

## 2. Commuters and the rushes

- [x] 2.1 In `routing.js`, add each lift's wait for the view being routed to its route time: morning waits outbound, evening waits for the way home. Test the busyness-queues scenario "A queue on the quick way" and the busyness-commuting scenario "A queue on the way". Verify that `npm test` passes.
- [x] 2.2 In `views.js`, add rush waits: (demand − capacity) × `PEAK_HOURS` ÷ (2 × capacity) beyond `WAIT_S`, per lift, for the morning and evening. Test the scenario "A village lift at 1.4× in the morning" (18 minutes). Verify that `npm test` passes.
- [x] 2.3 In `index.js`: compute day waits and the lookahead (group 1), then route in passes with the current rush waits (ride-down re-routing inside each pass). Average each pass's routes with all before it (the method of successive averages), and stop when no rush wait moves over 30 s, or at `QUEUE_PASSES` (30). Report `passes` and the waits. Test "Running twice" (identical results), and check that the existing ride-down test still passes. Verify that `npm test` passes (decision 011's observation tests are investigated in 5.1), and that each test domain converges within `QUEUE_PASSES`, recording its passes and run time.

  Notes: converged in 6 passes (Tignes–Val d'Isère), 10 (Serre Chevalier), 15 (Grandvalira) and 16 (Les Trois Vallées, about 22 s in Node). Four observation tests fail and go to 5.1: Lac de la Chambre, Edelweiss, Pelvoux and Traverse, and Le Monêtier to Cucumelle.

## 3. Reporting

- [x] 3.1 In `views.js`, report each lift's wait per view in `summarise`. Set `LIFT_LOAD_BANDS` to [0.5, 1.0], and add `LIFT_WAIT_BANDS_MIN` [5] to `params.json`. Band lifts as: under 50%; 50–100% with no queue; a queue under 5 minutes; a queue of 5 minutes or more. `liftsForSite` sends [band, load, wait]. Update the views tests: "A quiet domain", "A lift over capacity", "A lift with a long queue", "A full lift with a short queue", and the two-piece lift. Make `bin/run.mjs` print waits for the busiest lifts. Verify that `npm test` passes.

## 4. Site

- [x] 4.1 In `index.html`, read [band, load, wait], and relabel the lift legend "under 50% · 50–100% · queue under 5 min · queue 5 min+". On hover, show "modelled queue about N minutes" for a queued lift (to the nearest minute) and "modelled at N% of capacity" otherwise. Update the toggle's tooltip, which says "not a count of crowds or queues". Verify locally (`python -m http.server`) on a test domain in all three views: a queued lift's hover gives minutes, the legend shows both scales, and the screenshot reads clearly.

## 5. Results

- [x] 5.1 Regenerate the test fixtures (`python -m tests.busyness.fixtures`, and `--domains` after building the four test domains), since `params.json` changes the fingerprint. Run `npm test` and `uv run pytest`. Verify that both pass. If an observation test fails, investigate and record the outcome in 5.2 before changing any test.

  Notes: four observations regressed:
  - Lac de la Chambre: 10th and 12th, was 5th and 6th.
  - Edelweiss: 17th and 39% commuters, was 7th and 44%.
  - Pelvoux: 7th, was 4th.
  - Cucumelle in the morning: 0.68× and 9th, was 0.96× and 3rd.

  They're insensitive to the tolerance (10, 15 and 20 minutes give nearly the same). Cause: runaway day queues at valley lifts with no way round (Aravet, Bachas, Pré Chabert, Daille and the Funival) steer lapping skiers away from them, through the lookahead, and onto other runs (Gentiane 3,500 an hour, Lacets). Those queues come from known issues 18 (skiers favour higher areas by day) and 19 (Aravet isn't linked to Casse du Bœuf). The project owner chose to finish the change with honest results: the four tests are marked `todo` with that reason, and decision 011 marks them open.
- [x] 5.2 Recheck decision 011's table against the new results and update the numbers that moved, noting Plein Sud (known issue 4) and the Funitel 3 Vallées. Record, for each test domain, the number of queued lifts, the longest waits (and whether they're real bottlenecks or missing links like known issue 16), and the share of lap arrivals still beyond what lifts release. Verify that no row marked ✓ has become ✗ without a recorded reason.

  Notes:
  - **Rush queues look plausible:**
    - morning: Saulire 18 min, Pas du Lac 17, Tovière 12, TSD4 Cubil 13, the Serre Chevalier cable car 9 (its recorded 400 an hour is suspect, known issue 7);
    - evening: Saulire 47 min, Dou des Lanches 30.
    - 2–22 lifts per domain have a rush queue.
  - **Day queues are dominated by valley lifts that can't shed skiers** (known issues 18, 19):
    - Les Trois Vallées: 86 of 127 lifts queued (Tortollet 182 min, Cime Caron 125);
    - Tignes–Val d'Isère: 42 of 66 (the Funival 1,348, Daille 1,132);
    - Serre Chevalier: 32 of 43 (Pré Chabert 339, Aravet 335);
    - Grandvalira: 36 of 45 (Portella 425).
    - These minutes grow with the pass count and aren't real waits.
  - **Lap arrivals beyond what lifts release:** 4–7%, down from 17–22%.
  - **Decision 011:** no row marked ✓ became ✗. Four ✓ rows became open, with the reason recorded (Lac de la Chambre, Edelweiss, Pelvoux, Cucumelle). The Laisinant row, already ✗, got worse by day. Plein Sud and Pista Llarga improved.

## 6. Docs

- [x] 6.1 Write decision 015 (`docs/decisions/015-lift-queues.md`): waits from overload, queues repelling skiers at the lift and ahead, rush waits, what a modelled wait means, and why full conservation waits for #6 and known issue 17 (the trial). Update:
  - decision 004 (lifts still release capacity; full conservation deferred, see 015);
  - decision 006 (pull and waits);
  - decision 014 (the lift bands);
  - the decisions index.

  Verify that the links resolve.
- [x] 6.2 Bring `docs/known-issues.md` up to date with this change:
  - **Priorities:** remove "Lifts don't limit the flow" and renumber the rest. In "How many skiers a domain has", note that a sourced population is also what full conservation needs (item 17).
  - **Item 8:** remove the "Lifts don't limit the flow" bullet. Add `QUEUE_TOLERANCE_MIN`, the 5-minute band edge and the rush-average queue to "Other guesses".
  - **Item 17:** note that full conservation (fixed lapping population) waits on it, with the trial's findings (traps; 6,000-minute queues; restart shares).
  - **Mismatches:** update every item's numbers from 5.2: 1, 2, 3, 4 (Plein Sud), 10 (Tovière) and 15 (Pista Llarga). Mark any now matched, and add any new mismatch the rerun shows.
  - **Status diagram:** Laps "Overfull lifts" and Commuting "Uphill cap" go to 🟢 G if the results hold. Add a Views item for the modelled waits.

  Verify that every number in the document matches 5.2, and that every open row in decision 011 appears under Mismatches.

## Workflow follow-up

- Review the results with the project owner before archiving.
- Mention "Fixes #7, fixes #8" in the pull request, so GitHub closes them on merge.
- Archive the change with `/opsx:archive`.
