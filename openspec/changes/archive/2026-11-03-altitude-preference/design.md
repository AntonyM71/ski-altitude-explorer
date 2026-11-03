# Design

## Context

`pulls(net, P, wait)` in `busyness-engine/src/laps.js` gives each link's pull. It's used in three places:
- **`dayWaits`** (`queues.js`), for the day laps, with waits and the queue lookahead.
- **`descents`,** once with base pulls, to time each lift's run down.
- **`exchange`,** with base pulls, to check the engine against Python's sector finding (busyness-validation).

A scratch trial added an altitude factor inside `pulls`, at ratios of 2 and 4, on the four test domains. See proposal.md for what it showed.

## Goals / Non-Goals

**Goals:**
- A fair-weather preference for higher areas in the day laps, relative to each domain, that repels skiers into queues rather than piling them up without limit.

**Non-Goals:**
- **Conservation and population** (#6, known issue 17): the next change, where this preference starts to matter.
- **Weather:** in bad weather, skiers seek lower, sheltered terrain.
- **Aspect and snow conditions** (the snow-conditions idea in ideas-and-fixes.md): altitude is the first proxy.
- **Tuning `ALT_RATIO`:** later, against observations, once conservation is in.

## Decisions

- **Opt-in through `pulls`' options:** `pulls(net, P, wait, { altitude: true })`. Only `dayWaits` passes it, so sectors (`exchange`) and descent times stay on base pulls. That matches the spec ("not for sectors"), and keeps the Python–engine check exact.
- **Relative height of the lift's bottom station.** Heights run from 0 (the domain's lowest non-nursery lift bottom) to 1 (its highest). The bottom station is where a lapping skier joins the lift, so it says how high the skier stays. Using the top instead would favour long lifts from the valley.
- **The factor is `ALT_RATIO` ^ (h − 0.5),** centred so a mid-height lift keeps today's pull, with the extremes √R apart from it. It's bounded by design: at R = 2, the highest bottom pulls twice the lowest.
- **Runs through the lookahead.** One bottom-up pass over the junctions, like the queue lookahead, computes each junction's pull-weighted average altitude factor over its ways on: a lift's own factor, or what lies beyond a run or walk. A run's pull is multiplied by the factor at the junction it ends at. It's computed before the queue lookahead, so queues ahead still divide the result.
- **No change to the rushes.** In the morning, locals load their village lifts by capacity. In the evening, people go home. Altitude preference is about where skiers spend the day.

## Risks / Trade-offs

- **[Little visible effect]** → Expected while lift tops release full capacity. The proposal and docs say so, and the effect is rechecked after conservation.
- **[Queues move uphill]** → Modest in the trial (Cucumelle 38 → 52 minutes, the Grande Motte 6 → 12). Watched against "no massive queues at the top" (the Grande Motte, the Montet).
- **[Two lookahead passes cost time]** → Each is one pass over the junctions per `pulls` call. That's small next to routing.

## Migration Plan

An engine change. `params.json` changes every fingerprint, so there's a one-off rebuild, with no change to the structure files' contents. Rollback is reverting the change.
