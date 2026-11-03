# 015. Lift queues: waits where lifts are overfull, and skiers who avoid them

**Status:** Proposed (OpenSpec change `lift-queues`): accepted once the overlay is deployed

**Code:**
- [busyness-engine/src/queues.js](../../busyness-engine/src/queues.js): day waits.
- [busyness-engine/src/laps.js](../../busyness-engine/src/laps.js) (`pulls`): queues at the lift and ahead.
- [busyness-engine/src/routing.js](../../busyness-engine/src/routing.js): waits in route times.
- [busyness-engine/src/views.js](../../busyness-engine/src/views.js) (`rushWaits`, `bands`): rush waits and bands.
- [busyness-engine/src/index.js](../../busyness-engine/src/index.js): the loop.

## Context

Lapping skiers chose lifts without regard to how full they were. Where more arrived at a lift than its top released, the extra simply vanished: 17–22% of lap arrivals in the four test domains (GitHub #8). Commuters crossed overfull lifts with no limit (#7). Real skiers queue, and avoid long queues: they take another lift, or a run that ends somewhere quieter, often deciding before they reach the queue.

## Decision

- **Day waits from overload.** Where more lapping skiers arrive at a lift's bottom than its capacity, it gets a wait, which grows until arrivals fall to its capacity. A lift with no way round keeps its queue. Capacity is the same yardstick as the rush queues'. Day commuters, about a fifth of day lift traffic, aren't counted, because they're routed after the laps; they will be once lift tops release only what they carried (conservation, #6).
- **Queues repel lapping skiers at the lift:** a lift's pull is divided by 1 + its wait beyond loading ÷ 10 minutes (`QUEUE_TOLERANCE_MIN`).
- **...and ahead of it:** a run's pull is divided by the average queue factor of the lifts its skiers go on to reach. A skier can see Cucumelle's queue from above the Côte Chevalier split, and the model's skiers now can too.
- **Queues repel commuters:** a lift's route time includes its wait in the view being routed, morning waits going out and evening waits coming home.
- **Rush queues** grow through the 1.5-hour rush wherever demand exceeds capacity. A lift's average wait is (demand − capacity) × 1.5 h ÷ (2 × capacity), so a lift at 1.4× in the morning has about 18 minutes.
- **Settling:** commuters' routes are averaged over passes (the method of successive averages, as in traffic assignment), so they settle where none would gain by switching. Without averaging, the waits oscillated: everyone rerouted round a queue, then came back. The test domains settle in 6–16 passes.
- **Shown on the map** (014): lifts under 50% of capacity, 50% or more with no queue, a queue under 5 minutes, and a longer queue. Hovering gives the modelled queue in minutes.

## What a wait means, and what it doesn't

- **Rush waits are the model's best estimate of a queue's size:** Saulire about 18 minutes in the morning and 47 in the evening, Tovière 12 in the morning.
- **Day waits are fewer and shorter than rush waits,** as observed: 4–8 queued lifts per test domain by day, against 4–21 in the morning. The longest by day are Les Antenes (28 minutes, known issue 25), Cime Caron (18), Mont Blanc (14, known issue 24) and Cucumelle (11, within the 20 minutes observed).
- **Until 2026-11-03, day waits were measured against what a lift's top releases,** its capacity less its sector's commuting share, about 51–57% of capacity across a domain. Laps start from those same releases, so total arrivals always about equalled the total released, and any concentration put about half the lifts over: 32–86 lifts per test domain queued by day (median 13–30 minutes), though at most 2 carried more than their capacity. At valley lifts skiers couldn't avoid, such as La Daille, Aravet, Bachas and Pré Chabert, the wait grew every pass. Measuring against capacity removed these runaway queues.
- **Not a forecast:** a modelled wait ranks a domain's queues; it doesn't predict the wait on a given day.

## Alternatives considered

- **Full conservation:** a fixed lapping population circulating between lifts, so that quiet lifts run below capacity and queues balance the population by Little's law. Built and tried. Purely lapping skiers drain into groups of lifts they can enter but not leave: one Les Trois Vallées lift reached a 6,000-minute queue while lifts overall carried 8% of capacity. Restarting a share of laps at random helped but didn't converge. It needs time off the hill (known issue 17) and a sourced population (#6) first.
- **Balking:** skiers who reach a long queue with no way round give up and take a break, so the queue settles at 10 min × (overload − 1). It gave believable waits everywhere, such as Cucumelle at about 8–13 minutes. But the project owner observed that skiers mostly go somewhere else rather than stop, and that the lookahead captures that.
- **Capping day waits** (for example at 30 minutes): it hides the weakness rather than fixing it. Rejected for the same reason.
- **Loosening the regressed observation tests:** rejected. They were marked as known failures with the reason until fixed. Three passed again once day waits were measured against capacity.

## Consequences

- **One observation open:** Cucumelle in the morning (0.87×, 7th; decision 011). Lac de la Chambre, Edelweiss and Pelvoux regressed while day waits were measured against releases, and pass again.
- **Plein Sud is fuller in the morning** (0.76×). Pista Llarga eased while day queues pushed skiers elsewhere, and is 2nd by day again.
- **Run time:** Les Trois Vallées takes about 22 s in Node, 16 routing passes of about 1.4 s. The overlay can't ship at that speed; approximating comes once the model is settled.
