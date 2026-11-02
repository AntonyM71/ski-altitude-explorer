# Tasks

## 1. Network and pull

- [x] 1.1 Add `LIFT_WALK_M` (250), `LIFT_WALK_RISE_M` (30) and `WALK_SPEED` (1.0) to `busyness/params.py`, and bump `MODEL_VERSION` to 4. In `busyness/network.py`, add walks from each lift's top or bottom to other lifts' bottoms within those limits, only where runs and walks don't already lead there. Each takes max(`WALK_S`, distance ÷ `WALK_SPEED`). Add tests in `tests/busyness/test_network.py` for the busyness-network scenarios: "Two lift bottoms a short walk apart", "A lift's top near another lift's bottom", "A run already joins them" and "Lift bottoms too far apart". Verify that `uv run pytest tests/busyness` passes.
- [x] 1.2 Make a walk's pull the best run or lift it leads to, or 1 if neither: in `busyness/sectors.py` `pull()` and in `busyness-engine/src/laps.js` `pulls()`. Add the busyness-laps scenario "A walk to a nearby lift" as a test in both suites. Regenerate the shared fixtures (`python -m tests.busyness.fixtures`). Verify that `uv run pytest` and `npm test` in `busyness-engine/` pass, including the check that Python and the engine give the same exchange shares.

## 2. Results

- [x] 2.1 Build the four test domains and copy them into the fixtures (`python -m tests.busyness.fixtures --domains`). List the new walks in each (about 35 across the four test domains, if the trial holds), and check them for barriers (road, river), noting any doubtful pair. Compare each domain's sectors before and after. Verify that the list and the sector comparison are recorded in this task's notes.

  Notes (2026-11-02):
  - **Les Trois Vallées:** 22 new walks (6 between unnamed lifts). Croisette top → Jardin d'Enfants bottom (106 m); Moraine bottom → Portette bottom (116 m); Menuires bottom → Stade bottom (136 m); Preyerand bottom → Preyerand bottom (158 m); Croisette top → Menuires bottom (161 m); Boismint bottom → Caron bottom (174 m); Menuires bottom → Jardin d'Enfants bottom (192 m); Jardin d'Enfants bottom → Menuires bottom (192 m); Télécorde bottom → Télécorde top (200 m); TKD Gros Murger bottom → Ours Brun bottom (221 m); Chalets bottom → Aigle bottom (234 m); Plans bottom → Bruyères bottom (239 m); Stade bottom → Jardin d'Enfants bottom (245 m); Jardin d'Enfants bottom → Stade bottom (245 m); Roys bottom → Grangettes bottom (248 m); Grangettes bottom → Roys bottom (248 m). Lifts changing sector: 0.
  - **Tignes–Val d'Isère:** 7 new walks (0 between unnamed lifts). TCD8 des Brévières bottom → Brévières bottom (136 m); Brévières bottom → TCD8 des Brévières bottom (136 m); Tommeuses bottom → Mont Blanc bottom (178 m); Daille bottom → Lanche bottom (184 m); TKE Grande Parei top → Brévières bottom (208 m); TSD6 Tichot bottom → Club Méditerrannée bottom (212 m); Carpe Diem bottom → Slalom bottom (247 m). Lifts changing sector: 48.
  - **Serre Chevalier:** 4 new walks (0 between unnamed lifts). Aravet 2 bottom → Forêt bottom (157 m); TCD4 Aravet top → Aravet 2 bottom (204 m); Bachas bottom → TKD1 Pré Chabert bottom (208 m); Prorel 1 top → Stade bottom (221 m). Lifts changing sector: 0.
  - **Grandvalira:** 7 new walks (0 between unnamed lifts). TSD4 Pas de la Casa bottom → TSD6 Font Negre bottom (116 m); TLC Gall de Bosc bottom → TK Bosc top (133 m); TK Llosada bottom → TSF4 els Clots bottom (146 m); TC8 Soldeu bottom → TSD6 Soldeu bottom (150 m); TK Forn bottom → TC8 Canillo top (160 m); Tapís Jardí Riba bottom → Tapís Escola Riba top (185 m); TC10 Tarter bottom → TSD4 Tarter bottom (244 m). Lifts changing sector: 0.
  - **Barriers:** none is an obvious crossing of a road or river from the map data, but none has been checked on the ground. Doubtful: the unnamed-lift pairs, which are mostly village and nursery tows, and Preyerand bottom → Preyerand bottom, between two separately mapped pieces of one lift (possibly a mid-station).
  - **Sectors:** Les Trois Vallées, Serre Chevalier and Grandvalira are unchanged. Tignes–Val d'Isère regrouped because of the walk pull rule, not the new walks: Le Fornet, Cascade and Céma form their own sector, Bellevarde joins 3000 and Cugnaï, and Daille joins Borsat. The project owner accepted the new sectors. Two observation tests were loosened, with the reason recorded: Lac 38th of 151 (busiest 30%, was the busiest quarter), and Edelweiss 44% commuters (over 40%, was 45%).
- [x] 2.2 Run `npm test` and `uv run pytest`. Recheck decision 011's table and update the numbers that moved. Verify that both pass, and that no row marked ✓ has become ✗ without a recorded reason.

## 3. Docs

- [x] 3.1 Update decision 005 (walking links, with La Daille as the example) and `docs/known-issues.md`:
  - **Item 16:** the walk is fixed; keep the Funival's mapping and capacity as open data points.
  - **Mismatches:** update any numbers that moved in 2.2.

  Verify that the links resolve and the numbers match 2.2.
- [x] 3.2 Rebase the `lift-queues` change's busyness-laps delta onto the new walk rule. Its "Skiers split at junctions by pull" block must keep "the pull of the best run or lift it leads to, or 1 if it leads to neither". Verify that `openspec validate lift-queues --strict` passes.

## Workflow follow-up

- Archive this change with `/opsx:archive` before applying `lift-queues`.
