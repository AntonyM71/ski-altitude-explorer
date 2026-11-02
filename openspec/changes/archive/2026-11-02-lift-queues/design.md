# Design

## Context

Today the engine runs in three steps (`busyness-engine/src/index.js`):
1. **Laps** (`laps.js`): every lift's top sends out its capacity × (1 − sector commuting share), and `skiDown` spreads it down the runs by pull, a lift's pull being capacity ÷ `LIFT_PULL`. Arrivals at each lift's bottom (`liftLaps`) are its lap demand. They can exceed what the lift releases, and the difference vanishes.
2. **Routing** (`routing.js`, `evening.js`): commuters and people going home take the quickest-feeling routes, with each lift's time its ride plus `WAIT_S`. Only rides down are re-routed when overfull.
3. **Views** (`views.js`): the day, morning and evening views combine laps and routed trips, then bands are worked out.

A scratch trial lowered each overfull lift's pull in proportion to its overload and iterated. In the four test domains, the share of lap arrivals beyond what lifts release fell from 17–22% to 4–12%. The rest sat at lifts with no real alternative, which is where queues belong. See proposal.md for why, and the specs for the behaviour.

## Goals / Non-Goals

**Goals:**
- One mechanism, a lift's wait, drives laps' choices (at the lift and ahead of it) and commuters' routes, in every view.
- Waits come from each lift's own overload, so they appear only where skiers can't spread out.

**Non-Goals:**
- **Full conservation**, with a fixed lapping population circulating between lifts and quiet lifts running below capacity. Ruled out for now: see "Alternatives considered".
- **A better population figure:** that's #6.
- **Sectors:** the pipeline still finds them from base pulls, without waits.
- **Joining lift bottoms a short walk apart:** a separate change, done first.
- **Within-day dynamics** beyond the rush-average formula.

## Decisions

### Day waits from each lift's overload (`queues.js`)

Lift tops release capacity × (1 − share), as today (`lapSources`). Each pass:

1. **Pulls:**
   - A lift's pull = capacity ÷ `LIFT_PULL` ÷ its queue factor, 1 + wait ÷ `QUEUE_TOLERANCE_MIN`.
   - A run's pull = its grade-and-gradient pull ÷ the queue factor ahead of it (the lookahead, below).
2. **Laps:** `skiDown` from the tops gives each lift's arrivals a_k. Each lift releases r_k = capacity × (1 − share).
3. **Waits:**
   - A lift's visit is ride + wait + descent, the descent being the expected skiing time from its top to the next lift, measured once with base pulls.
   - To take r_k ÷ a_k of its arrivals, the visit must take about a_k ÷ r_k times longer. So the target wait is visit × a_k ÷ r_k − ride − descent, and the wait moves halfway towards it, never below 0.
   - A lift with no overload and no wait stays at 0.
4. **Stop** when no wait moves by more than 30 s, or after `QUEUE_PASSES`.

Where skiers have another way on, their pull shifts until the lift isn't overfull. Where they don't, the wait keeps growing until the cap on passes, so it reads as a long queue. That's the honest answer for a bottleneck while skiers aren't conserved: the queue is real, and the skiers in it are counted as demand, not held.

### The lookahead: queues seen ahead

For each run, the queue factor ahead is the average queue factor of the lifts its skiers reach, weighted by how many reach each. It's computed in one bottom-up pass over the junctions, using the current pulls:
- **A junction's factor:** the pull-weighted average over its ways on of the lift's queue factor (for a lift) or the run's factor ahead (for a run or walk).
- **A run's factor ahead:** the factor at the junction it ends at.

Junctions are numbered highest first, so processing them lowest first visits each junction's downstream before it. Run links that climb are handled by the sweep order already used in `skiDown`: the factor ahead is taken from the previous pass for those few links. A run's pull is then divided by its factor ahead. This can't double-count at the junction itself: a lift's own factor applies only to the lift link, and the factor ahead only to runs.

Alternative considered: looking ahead along whole routes, as commuters do. That's heavier, and it doesn't match how lapping skiers decide, run by run.

### Commuters in the same loop

Commuters' routes use waits: each lift's route time = ride + wait in the view being routed:
- outbound trips use morning waits;
- trips home and locals going home use evening waits.

Routing runs in an outer loop after the day waits (which don't depend on commuters, since what a lift releases is its capacity less its sector's commuting share). Each pass routes with the current rush waits, with the ride-down re-routing inside it, and works out the views and rush waits.

Each pass's routes are averaged with all before it, with weight 1 ÷ pass: the method of successive averages from traffic assignment. Without it, the waits oscillated: a queue sent every commuter round it, the other route queued, and they all came back. Grandvalira's largest change cycled between about 930 and 1,015 s for 30 passes. With averaging, the four test domains settled within 30 s in 6–16 passes.

### Rush waits from the rush-average formula

The morning and evening views keep their construction. A lift whose rush demand d exceeds capacity c gets an average wait of (d − c) × `PEAK_HOURS` ÷ (2c), on top of `WAIT_S`: a queue growing steadily through the rush. Those waits feed back into commuters' routing in the next routing pass.

### Reporting and the overlay

- **Each lift reports, per view:** demand ÷ capacity (as today), its wait, and whether it's queued (wait of at least 30 s beyond loading).
- **Bands:**
  - 0: under 50%
  - 1: 50% or more with no queue
  - 2: a queue under 5 minutes
  - 3: a queue of 5 minutes or more

  These use `LIFT_LOAD_BANDS` [0.5, 1.0] and `LIFT_WAIT_BANDS_MIN` [5].
- **The worker** sends [band, load, wait].
- **The site** relabels the legend "under 50% · 50–100% · queue under 5 min · queue 5 min+". On hover, it gives "modelled queue about N minutes", or "modelled at N% of capacity".

### Parameters

`QUEUE_TOLERANCE_MIN` 10, `QUEUE_PASSES` 30 (a safety limit; the test domains settle in 6–16) and `LIFT_WAIT_BANDS_MIN` [5] go in `params.json`, marked unsourced (known issue 8), and `LIFT_LOAD_BANDS` becomes [0.5, 1.0]. Changing `params.json` changes every domain's fingerprint, so there's a one-off rebuild, with no change to the structure files' contents.

## Alternatives considered

**Full conservation as a closed queueing network.** The domain's lapping population circulates. Each top releases what arrived, up to capacity, and waits balance the population by Little's law. It was built and tried on the four test domains. The lift-to-lift chain from downhill laps has traps: groups of lifts skiers can enter but not leave. A circulating population drains into them, giving one Les Trois Vallées lift a 6,000-minute queue while lifts overall carried 8% of capacity.

Restarting a share of laps at lifts by capacity helped:
- **10%:** waits of thousands of minutes remained.
- **25%:** hundreds of minutes.
- **50%:** 27–52 minutes at a few valley bottlenecks.

But it didn't converge within 40 passes in Les Trois Vallées. Doing this properly needs skiers to break off laps for lunch, heading home or moving across the domain (known issue 17), and a sourced population (#6). It's deferred to that work. This change's waits and lookahead carry over to it unchanged.

## Risks / Trade-offs

- **[Waits at bottlenecks grow until the pass cap]** → Report them as long queues, and list the longest in 5.2. Known issue 16 (Daille to the Funival) shows some are missing walks, not real bottlenecks; the walks change comes first for that reason.
- **[The waits oscillate or settle slowly]** → Day waits are damped. Rush routes are averaged across passes (above), with at most 30 passes, and convergence is checked on the four test domains, with `passes` reported.
- **[Run time]** → Correct results come first; speed is a later piece of work. Les Trois Vallées takes about 22 s in Node: 16 routing passes of about 1.4 s, each over 30 draws × 3 ability groups × every village station. The overlay can't ship at that speed. Approximating (fewer draws, reusing routes between passes) is a follow-up once the model is settled, measured against these results.
- **[Day waits at lifts with no way round]** → Where every skier ends up at a lift with no alternative, such as the valley lifts at La Daille and Aravet, the day wait grows each pass, so its minutes depend on `QUEUE_PASSES`. They're shown as they are, not capped: the project owner prefers a visible weakness to a tidy number. Known issue 18 (skiers favour higher areas by day) is the real fix.
- **[Observations move]** → Rerun decision 011's checks. A regression is investigated, not waved through.
- **[Waits read as forecasts]** → Labelled "modelled", and explained in decision 015.

## Migration Plan

An engine and site change. Structure files don't change, apart from the one-off rebuild when `params.json` changes. Rollback is reverting the change.

## Open Questions

- **The 10-minute tolerance and 5-minute band edge** are guesses. They can be tuned against observations without changing the approach.
