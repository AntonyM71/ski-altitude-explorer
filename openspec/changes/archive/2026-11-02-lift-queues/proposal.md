# Proposal

## Why

The model lets skiers choose lifts without regard to how full they are. Lapping skiers who arrive at a lift beyond what it releases simply vanish: 17–22% of lap arrivals in the four test domains (GitHub #8). Commuters pass overfull lifts with no limit (#7). Lifts with no alternative look far busier than they could be, while others go unused. Real skiers queue. They avoid long queues by taking another lift, a lap off a slower one, or a run that ends somewhere quieter, often deciding before they reach the queue.

## What Changes

- **Queues form where more arrive than a lift releases.** Each lift's top still releases its capacity × (1 − commuting share), as today. Where more lapping skiers arrive at its bottom, it gets a wait, which grows until arrivals fall to what it releases. Lifts with no alternative keep their queue.
- **Queues repel:**
  - **At the lift:** a lift's pull falls as its wait grows.
  - **Seen ahead:** a run's pull falls with the queues at the lifts it leads to, so skiers avoid a run that ends at a long queue.
  - **On routes:** commuters' route times include each lift's wait.
  - Waits, pulls and routes are iterated until they settle.
- **All three views use it.**
  - The day average uses the overload waits.
  - The morning and evening rushes give a queue wherever demand over the rush exceeds a lift's capacity, and route commuters with those waits.
- **Overlay:** lifts below capacity are shown by load, and lifts with a queue by their modelled wait in minutes. Hover gives the wait, labelled as modelled. **BREAKING** for the overlay spec, which said nothing about queues.
- **Not in this change:**
  - **Full conservation:** circulating a fixed lapping population, so that quiet lifts run below capacity. A trial showed that a purely lapping population drains into groups of lifts it can't leave (one Les Trois Vallées lift reached a 6,000-minute queue). Fixing that needs skiers to break off laps for lunch, to head home or to move across the domain (known issue 17) and a proper population (#6). Deferred to that work.
  - **Joining lift bottoms a short walk apart** (known issue 16, Daille to the Funival). It's a separate change to the network, made first. This change's results are checked on that network.
  - **Unchanged:** riding down's existing cap; the Python pipeline and sectors.

## Capabilities

### New Capabilities

- `busyness-queues`: how lifts limit the flow. It covers waits from overload, queues repelling lapping skiers at the lift and ahead of it, queues repelling commuters, rush-hour queues, and solving by iteration.

### Modified Capabilities

- `busyness-laps`: "Skiers split at junctions by pull" lowers a lift's pull by its wait, and a run's pull by the queues ahead of it.
- `busyness-commuting`: "Routes vary" includes lift waits in route times.
- `busyness-views`:
  - "Lifts are reported against capacity" adds each lift's modelled wait.
  - "Busyness is a relative index" allows waits as modelled minutes.
- `busyness-overlay`:
  - "Lifts shown by load against capacity" shows queued lifts by wait.
  - "Presented as an experimental relative index" lets the hover give a modelled wait.

## Impact

- **Engine (`busyness-engine/`):**
  - `laps.js`: wait- and lookahead-dependent pull.
  - `queues.js`: overload waits and the lookahead.
  - `routing.js` and `evening.js`: waits in route times, and the outer iteration.
  - `views.js`: waits per view, and bands.
  - `worker.js` and `params.json`: queue constants.
  - Tests.
- **Site (`index.html`):** lift colours, legend and hover.
- **Results:** every domain's lift loads and run traffic change. Fixtures are rerun and decision 011 is rechecked; Plein Sud and the Funitel 3 Vallées are the likeliest to move. Engine run time rises by a few iterations.
- **Depends on:** the lift-bottom walks change, archived first.
- **Docs:**
  - decision 006 is updated, and a new decision record (015) covers the queue model and why conservation waits;
  - known issues: priority 2 resolved, and items 8 and 17 updated;
  - GitHub #7 and #8 are closed by the merge.
- **No new dependencies; no change to structure files.**
