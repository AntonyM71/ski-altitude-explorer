# Design

## Context

See proposal.md (Why). Today the engine computes three views separately:
- **Day:** laps from fixed lift-top releases (`lapSources`), with overload waits iterated in `dayWaits`.
- **Morning and evening:** commuters routed over averaged passes (`routeEveryone`, `routeWithRidesDown`), plus a 40% ramp of the day's laps, with waits from a formula (`rushWaits`).

The pieces this design reuses:
- the network and its link times (`graph.js`, `rt`);
- pulls (`laps.js`), including the trialled full-weight rule, still uncommitted;
- route times by ability (`routeTimes`);
- commuter demand from the gravity model (`gravity`);
- village stations and populations from the structure file.

The overlay consumes `bands` and `liftsForSite`, and its format stays the same.

## Goals / Non-Goals

**Goals:**
- One simulated day that produces all three views, with skiers exactly conserved.
- Deterministic, with no random sampling of individual skiers.
- Runs each test domain in a few seconds in Node.

**Non-Goals:**
- The browser run-time budget, which is a later change (the overlay may be slow until then).
- Calibrating the population (decision 016) and tuning the windows.

## Decisions

### Skiers are fractional flows, not individual agents
State is an amount of skiers in each place. The simulation moves amounts, so 0.37 of a skier is fine.
- **Why:** it's deterministic, has no sampling noise, and its cost doesn't grow with the population.
- **Alternative: agents.** These need thousands of random draws per domain and noisy results, or many runs to average out. Reject.

### Cohorts by home village and purpose
Skiers are grouped by home village × what they're doing:
- lapping;
- heading for sector s;
- heading home.

Cohorts are needed because going home needs the village, and an outbound commuter needs their destination. Ability groups and route draws aren't separate cohorts. Their route choices are blended, as below.

### Time steps of one minute, with travel carried within the step
`STEP_S` = 60. Each link holds a delay line, keyed by the step in which its skiers come out. A link's time `rt` rarely fills whole minutes, so skiers entering it are split between the two steps either side of their exact arrival time. The split is in proportion, which keeps the mean travel time exact and conserves skiers.

Many links take seconds (pieces of runs cut at junctions, walks), so skiers due out in the same step are passed on within that step. Junctions are processed highest first, as in `skiDown`, so one sweep carries them down any chain of short pieces. A zero-delay link that climbs (a short walk up) carries over to the next step.
- **Alternative: whole-minute delays.** Rounding every piece up to a minute would make a run cut into ten pieces take ten minutes. Reject.

### Lifts: a queue at the bottom, boarding up to capacity
Each lift has a queue per cohort. Each step:
- it boards min(1, capacity per step ÷ queue) of every cohort's waiting skiers;
- they enter the ride's delay line;
- its wait is the queue ÷ capacity.

Rides down (`download` links) work the same way, with their queue at the top.

### Lappers choose by pull, refreshed every 5 minutes
Lappers arriving at a junction split by the pulls of its ways on. Pulls include each lift's current queue factor and the lookahead (busyness-laps). They're recomputed every `PULL_MIN` = 5 minutes from the current waits.
- **Why 5 minutes:** the lookahead is a pass over all junctions, and every step would be wasteful. 5 minutes is shorter than any queue's reaction time worth modelling.

### Commuters and skiers going home follow blended route trees, refreshed every 15 minutes
For each destination (a sector's lift bottoms, or a village's station) there's a tree of next steps towards it, worked out by Dijkstra backwards from the destination. It uses `routeTimes` with each lift's current wait, for each ability and each draw.

A cohort at a junction is split over the next steps the trees give, weighted by ability share and shared evenly between draws. The trees are refreshed every `REROUTE_MIN` = 15 minutes.
- **Trade-off:** blending means a skier doesn't keep one ability or one draw along a whole route. At the level of flows the shares come out the same; only correlations along a route are lost.
- **Why not routes per skier:** they'd need agents.

Outbound commuters reach their destination at any lift bottom of their sector, and switch to lapping there. At 15:00 every cohort switches to heading home:
- **skiers in a queue** stay in the proportion whose next step home is that lift, and the rest leave the queue at that junction;
- **skiers on a run or lift** carry on, and choose at the next junction.

### Population and departures
- **Locals who lap:** the village's skiers × (1 − its sector's commuting share).
- **Commuters:** the gravity demand per destination sector, unchanged (`gravity` with plain route times, computed once before the day).
- **Departures:** both appear at the village's stations by capacity, evenly over 09:00–10:00.

### Views from windows
Per link and window (morning 09:00–10:30, day 11:00–14:30, evening 15:00–16:30), the simulation accumulates:
- skiers entering it;
- for lifts, skiers boarding and the queue's growth;
- the wait, sampled each step.

Each is divided by the window's length for per-hour values, and the averaged wait comes from the samples. `summarise`, `bands` and `liftsForSite` work as now on these per-hour values. The day window is checked for settling: its two halves are compared, and links over 10% apart are listed.

### Dead ends, islands and nursery areas
Under conservation, a junction with no way on keeps every skier who reaches it; the old sweep dropped them silently. The pipeline adds a walk from each dead end to the nearest lift bottom within `DEAD_END_WALK_M` = 1,000 m (after the other walks, so it's only a backup), then drops runs and walks from which no lift bottom can be reached (islands). In the engine, nursery lifts and slopes pull like any other at `NURSERY_PULL` = 0.05, rather than not at all, so a junction whose only way on is a nursery slope isn't a trap. `plainPulls` (the sector check) keeps them at none, matching the pipeline's sectors.
- **Alternative: a longer station walk limit.** It would join lifts that shouldn't be joined as well as fill the gaps. Reject.
- **Alternative: fix each gap in OpenStreetMap.** Worth doing too (Isolée to Rocher de l'Enfer at Serre Chevalier), but the model must cope with gaps everywhere.

### What goes
`lapSources`, `dayWaits`, `descents`, `releases`, `rushWaits`, the MSA loop in `index.js`, `RAMP`, `DAY_HOURS` and `QUEUE_PASSES`. `PEAK_HOURS` is no longer used for the views. `routeWithRidesDown` and `DOWNLOAD_PASSES` go too: overfull rides down are handled by the queue at the top. `exchange` and `skiDown` stay, for the sector check against the pipeline.

## Risks / Trade-offs

- **[Too many skiers for the lifts]** Capacity ÷ 3.5 is about twice what lifts can cycle at the model's lap times (Little's law), so queues may build everywhere by day.
  - Mitigation: report the share of the population on the hill, waiting, riding and skiing, so the level is visible. Calibrating it is decision 016's next step, not this change's.
- **[Traps]** A group of lifts skiers can enter but not leave fills through the day.
  - Mitigation: they're listed as unsettled and shown, not capped, as the project owner prefers. Fix the network where they're real gaps.
- **[Run time]** Les Trois Vallées has about 900 junctions, 3,000 links and up to 26 villages.
  - Mitigation: skip empty cohorts at each junction, refresh pulls and routes on intervals, and reduce `DRAWS` for the trees if needed, recording it in the decision.
- **[Observation tests shift]** Everything moves at once.
  - Mitigation: render before and after (`bin/mapdiff.mjs`) on all four domains, and record each test's new result in decision 011. Tests that fail are marked as known failures with the reason, not loosened.
- **[Blended routes]** Correlations along a route are lost. This is acceptable at the level of flows.

## Migration Plan

The engine's entry point keeps its signature and result fields (`links`, `runs`, `lifts`, `bands`, `waits`), so the overlay worker and `liftsForSite` are unchanged. Rollback is reverting the change. Structure files and the pipeline are untouched.

## Open Questions

- The exact windows (11:00–14:30 for the day) and `PULL_MIN` / `REROUTE_MIN`. These are tunable later without changing the approach.
