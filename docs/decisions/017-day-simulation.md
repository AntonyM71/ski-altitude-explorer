# 017. Simulate the day, with every skier conserved

**Status:** Proposed (OpenSpec change `day-simulation`): accepted once the overlay is deployed

**Code:**
- [busyness-engine/src/simulate.js](../../busyness-engine/src/simulate.js): the simulated day.
- [busyness-engine/src/laps.js](../../busyness-engine/src/laps.js) (`pulls`): how lapping skiers choose at junctions.
- [busyness-engine/src/index.js](../../busyness-engine/src/index.js): the engine's entry point.
- [busyness/network.py](../../busyness/network.py) (`dead_end_walks`, `drop_islands`): walks out of dead ends, and islands dropped.

## Context

The model didn't conserve skiers.
- **Lift tops invented skiers.** Every lift's top let off a fixed share of its capacity (its capacity less its sector's commuting share, about 55% across a domain), whether or not anyone rode it. So every lift looked about half full by day, and a lift nobody reached still sent skiers down its runs.
- **Dead ends deleted them.** Where a run ended with nothing leading on, the lap sweep silently dropped the skiers there.
- **Areas skiers left were never refilled.** High areas emptied out and valley lifts collected everyone (known issues 18 and 22).

Tuning pulls could only move this fixed traffic around. Trials of a stronger altitude preference (`ALT_RATIO` 4 and 8), lift pull by vertical per minute, and a discount for lifts further away all failed to bring skiers back to Tignes' glaciers. Grande Motte stayed at 37–55% and the glacier lifts at 6–18%.

The day, morning and evening were also three separate calculations with their own assumptions: laps from the fixed releases, a 40% ramp of laps in the rushes (`RAMP`), and a formula for rush queues.

## Decision

- **Simulate the day, one minute at a time.**
  - Each village's skiers appear at its stations over 09:00–10:00, by lift capacity.
  - Locals lap. Commuters head for the sector the gravity model gives them (009), then lap there.
  - At 15:00 everyone heads home from wherever they are.
- **Skiers are conserved.**
  - A lift boards only who is waiting at its bottom, up to its capacity per minute. The rest are its queue, and its wait is the queue ÷ capacity.
  - Nobody comes off a lift's top unless they rode it, and every run takes its time to ski.
  - Skiers are fractional flows grouped by home village and purpose, not individuals, so the result is deterministic.
- **The views are windows of the day:**

  | View | Window |
  |---|---|
  | Morning rush | 09:00–10:30 |
  | Day | 11:00–14:30 |
  | Evening rush | 15:00–16:30 |

- **Choices see the current queues.** Lapping skiers' pulls are refreshed every 5 minutes. Routes for commuters and skiers going home are refreshed every 15, with each lift's current wait in its time.
- **A run pulls like the lifts it leads to,** at full weight. Its pull is the lift pull ahead × the easiest way on from it: the lower of the run's own weight and the easiest way on beyond.
  - A bigger lift a short run away counts as fully as a small lift at hand.
  - A long black on the only way to a lift dissuades skiers.
  - A black beside an easier way doesn't count against the run leading to them.
  - A walk that climbs pulls like a near-flat run.
- **Backup walks out of dead ends.** Where nothing leads on (rides down aside), the pipeline adds a walk within 1 km (`DEAD_END_WALK_M`): from a run's end to the nearest lift bottom, from a lift's top to the nearest run start. Runs from which no lift can be reached are dropped as islands.
- **Nursery lifts and slopes are a last resort,** not off limits. Lapping skiers take them at 0.05 of the pull (`NURSERY_PULL`), so a junction whose only way on is a nursery slope isn't a trap. The project owner's phrase: "allowed, but bad form".

## Evidence

**The pull rule at Mont Blanc** (Tignes–Val d'Isère). Mont Blanc (1,600 an hour) drew 3,274 lapping skiers an hour before queues, with a 14-minute day queue. Meanwhile Tommeuses (4,500 an hour), 30 m further down the run, ran at 63%. Testing showed three causes:
- **Pull only compared the ways on from the junction a skier was standing at.** The run on towards Tommeuses pulled about 1 against Mont Blanc's 2.0.
- **A first version of the lookahead divided the lift pull ahead by the domain's typical lift pull.** So the same lift counted fully at hand but only partly a run away. This was a bug, not a modelling choice.
- **Two walks led from the junctions below back up to Mont Blanc's bottom** (7 m and 27 m higher). Each pulled as strongly as Mont Blanc itself. Removing them cut its queue from 13 minutes to 4.

**Dead ends.** Once skiers were conserved, at noon 4–39% of each domain's skiers were stuck at junctions with no way on. They were mostly where a run ends in a village away from any lift, or at a lift top with no run mapped from it (the Perce-Neige funicular's top on the Grande Motte). Some came from nursery slopes, and one from a gap in the map (Isolée at Serre Chevalier stops short of Rocher de l'Enfer). With backup walks and nursery areas as a last resort, none are stuck.

| Domain | Stuck at noon, before → after | Junctions with no way on, before → after |
|---|---|---|
| Grandvalira | 4% → 0% | 4 → 0 |
| Les Trois Vallées | 26% → 0% | 16 → 0 |
| Serre Chevalier | 13% → 0% | 3 → 0 |
| Tignes–Val d'Isère | 39% → 0% | 11 → 0 |

**Results on the test domains** (task 4.3):

| Domain | Run time (Node) | Skiers | At noon: queuing / riding or skiing | Not home by 16:30 | Links unsettled by day |
|---|---|---|---|---|---|
| Grandvalira | 1.4 s | 25,154 | 42% / 58% | 26% | 197 |
| Les Trois Vallées | 13–18 s | 73,739 | 28% / 72% | 32% | 468 |
| Serre Chevalier | 1.6 s | 18,928 | 28% / 72% | 28% | 339 |
| Tignes–Val d'Isère | 3.2 s | 37,266 | 42% / 58% | 39% | 474 |

**Observations (decision 011).** Some are better:
- Grande Motte and the Le Fornet glacier chairs are used: Grande Motte 0.98× by day, Glacier and Datcha without the old runaway queues.
- Piste M rises from 48th to 15th in the evening, and Santons from 41st to 23rd.
- Cucumelle has no day queue.

Some regressed: Lac de la Chambre, Lac at Tignes, Pelvoux, the Funitel 3 Vallées in the morning, Prorel riding down and Edelweiss. Daille and Aravet have long day queues again (209 and 171 minutes). The failing tests are marked as known failures with their figures.

## What the results mean

- **The population is too big for the lifts,** as the design predicted. Capacity ÷ 3.5 puts everyone on the hill all day, about twice what the lifts can cycle at the model's lap times. The excess can only queue: 28–42% of skiers are in a queue at noon. The same excess keeps queues growing through the day, which is why links don't settle, and leaves a quarter to a third not home by 16:30. Valley lifts with no way round (Daille, Aravet) collect the excess.
- **That's now a measurement, not a hidden assumption.** The next step is the population from decision 016: bed counts × occupancy × the share on the hill at once. Calibrate against the noon figures here, not by tuning pulls.
- **The rushes behave plausibly.** Village lifts load at 09:00–10:30 with short queues, and home lifts and rides down queue in the evening.

## Alternatives considered

- **Keep fixed releases and tune pulls** (stronger altitude preference, vertical per minute, distance). Tried; none moved skiers back up, because the fixed releases set where they start.
- **A closed loop solved for a steady state.** Tried before (015). Purely lapping skiers drained into groups of lifts they could enter but not leave, one queue reaching 6,000 minutes. Simulating a finite day bounds how far any trap can fill, and lists it as unsettled.
- **Individual skiers (agents):** random draws, noisy results, and a cost that grows with the population. Fractional flows give the same averages deterministically.
- **Breaks and lunch:** out of scope. They average out over the day, apart perhaps from lunch.

## Consequences

- **Removed:** the fixed lift-top releases (`lapSources`), the day-wait iteration (`dayWaits`), the rush-wait formula (`rushWaits`), `RAMP`, `DAY_HOURS`, `PEAK_HOURS`, `QUEUE_PASSES` and the ride-down passes (`DOWNLOAD_PASSES`).
- **The overlay's format is unchanged.** Lifts now also report demand (skiers arriving ÷ capacity) per view.
- **Run time:** Les Trois Vallées takes 13–18 s in Node, too slow for the browser. That's a later change.
- **Runs looping within a station** (formerly known issue 26) carry no traffic: lapping skiers don't take them, and no quickest route uses them.
- **Rendering:** every change is now rendered before and after with `node busyness-engine/bin/mapdiff.mjs`.
