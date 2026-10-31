# Tasks

## 1. Model

- [x] 1.1 In `prototypes/busyness.py`, make the end-of-day penalty use the run's plain grade (`EVENING_FEEL[grade]`), keeping the blended ability weight, and update the comment by `EVENING_FEEL`. Verify that `uv run --group busyness python prototypes/busyness.py "Serre-Chevalier"` completes without error.

## 2. Check against observations

- [x] 2.1 Rerun all four test domains (Les Trois Vallées, Tignes–Val d'Isère, Serre Chevalier, Grandvalira). Verify that each run exits 0 and writes new results.
- [x] 2.2 Compare the results with decision 011's table, using the scratchpad check script or the review map. Verify that the black home to the valley is quieter than the long green in the evening, and that no row marked matched becomes a regression. Outcome: no regressions. The black moved the right way (1,694 → 1,432 an hour, the green 342 → 518) but is still busier than the green. The project owner accepted the partial fix, with known issue 6a left open.

## 3. Docs

- [x] 3.1 Update decision 009 ("The way home is different" and its evidence table) and decision 011's comparison table with the new numbers. Verify that the numbers quoted match the results from 2.1.
- [x] 3.2 Update `docs/known-issues.md` 6a to resolved, pending review, or with what remains open. Verify that the item's numbers match the results from 2.1.

## Workflow follow-up

- Review the results with the project owner before archiving.
- Archive the change with `/opsx:archive`, which merges the deltas into `openspec/specs/`.
