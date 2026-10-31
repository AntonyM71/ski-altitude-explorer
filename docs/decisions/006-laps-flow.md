# 006. Laps: skiers spread downhill by weighted choice at junctions

**Status:** Proposed (issue #3, prototype)

**Code:** [busyness/](../../busyness/) (structure: network, villages, sectors) and [busyness-engine/](../../busyness-engine/) (behaviour: laps, commuting, views); see [012](012-busyness-production-architecture.md)

## Context

Most skiers spend the day lapping lifts near where they are. We need to decide, at each junction, how skiers coming down divide between the runs and lifts on offer.

## Decision

- **Where skiers come from.** Each lift's riders leave its top: its capacity, less its sector's share of commuters (34–56% in the test domains; see 009). They ski down until a lift takes them.
- **Nursery areas have no pull.** Lapping skiers never choose a nursery lift or slope (005); those are left to ski school.
- **How they split.** At each junction they divide in proportion to each option's pull:
  - **Lifts** pull by capacity ÷ 800 (`LIFT_PULL`), so a 2,000-an-hour chairlift draws as many skiers as 2.5 runs. Skiers mostly take the next lift rather than skiing to the valley floor.
  - **Runs** pull by grade (`GRADE_PULL`): green and blue 1.0, red 0.8, black 0.4, ungraded 0.7.
  - **Short blacks count more like reds.** A black's weight depends on its committed length: how much black you ski from its top before the next way out, which can be an easier run, a lift or a walk. Up to 300 m (`BLACK_SHORT_M`), it counts like a red. From 1,000 m (`BLACK_LONG_M`), it's fully black. In between, it blends from one to the other. The same rule applies to route choice (009).
  - **Steepness** scales a run's pull, using its average gradient over its whole length: under 6% ×0.35, under 10% ×0.7, over 45% ×0.6.
- **Speed.** Flat runs are slower: under 4% average, a run goes at 40% of its grade's speed; under 8%, 60%; under 12%, 85%.
- **Calculation.** Flow is pushed downhill, highest junction first, and repeated until settled, because walking links can climb a little.

## Evidence

Each weighting fixed a specific error:

| Problem | Fix |
|---|---|
| An equal split sent as many skiers into a small platter as into a big gondola. Some drag lifts came out 6–8× over capacity. | Weight lifts by capacity. |
| The Face de Bellevarde (black) carried more traffic than the Joseray red beside it. The project owner finds the black often less chewed up, enough to prefer it. | Weight runs by grade: the Face fell from 1,445 to about 500 an hour, below Joseray. |
| Traversée du Laisinant, 1,355 m long but dropping only 79 m (5.8%), carried as much traffic as a proper slope. The owner notes that skiers avoid flat runs. | Weight and slow runs by gradient: the traverse fell from 1,654 to about 690 an hour. |
| Every black counted the same. The project owner finds that confident intermediates don't mind a black they can bail out of: Pylônes at Serre Chevalier is crossed by greens, so it's less daunting than "2 km of black with no other option". | Weight blacks by committed length, once crossings were joined (005). Pylônes's longest stretch is 712 m, and it rose from 239 to 366 skiers an hour by day. The Face de Bellevarde (1,339 m), Tabuc (3,300 m) and Sache (2,026 m) stay fully black. |
| Where several lifts shared a top station, the prototype counted lapping skiers from only one of them: a later lift's riders overwrote an earlier one's. In Les Trois Vallées, 18 stations covering 39 of 127 lifts were affected. Found when the JavaScript engine matched the prototype only after copying the overwrite. | Riders from lifts sharing a top add up (busyness-laps). With the production pipeline, Pelvoux fell from the busiest run by day in Serre Chevalier to 4th, and Combe and Lac from 11th and 21st to 24th and 36th in Tignes–Val d'Isère, all still busy (011). |
| Valley runs collected every skier from the slopes above. Pista Llarga, Corvaria and Piste L ranked near the top. | Raise lifts' pull (`LIFT_PULL` 1,500 → 800): Piste L fell from 3rd to 10th. |

## Consequences

- **The weights are judgement, not measurement.** They should be tuned against more observations (see 011).
- **Not a closed system:** lift demand from laps isn't capped at capacity. An overloaded lift shows as over 1×, rather than its excess skiers being sent elsewhere.
