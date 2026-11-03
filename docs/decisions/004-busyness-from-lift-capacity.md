# 004. Estimate busyness as a relative index from lift capacity

**Status:** Proposed (issue #3, prototype)

> **Since [017](017-day-simulation.md):** lifts no longer run at capacity by assumption. They carry the skiers who reach them, up to capacity, in a simulated day. The domain's skiers are still lift capacity ÷ 3.5, now visibly too many (see 016).

**Code:** [busyness/](../../busyness/) (structure: network, villages, sectors) and [busyness-engine/](../../busyness-engine/) (behaviour: laps, commuting, views); see [012](012-busyness-production-architecture.md)

## Context

We want to show which pistes and lifts are likely to be busy. OpenSkiMap has no usage data: no skier counts, ticket scans or visitor numbers. It does record lift capacity in people per hour, and coverage is good in the big Alpine domains:

| | Lift capacity filled in |
|---|---|
| All 31,032 operating lifts | 23% |
| Les Trois Vallées | 68% |
| SkiWelt | 83% |
| Ischgl | 17% |

Lift type is always filled in. Ride time is filled in for 18% overall, and seats per chair for 32%.

## Decision

Busyness is modelled from **uplift**: every lift is assumed to run at its full capacity, and the model works out where those skiers go. Where more arrive at a lift than it releases, they queue, and skiers avoid long queues ([015](015-lift-queues.md)). A fixed population that would let quiet lifts run below capacity is deferred: see 015 and #6. The output is a **relative index**, which ranks runs and lifts against each other within a domain. It isn't a count of people.

- **Missing capacity** is filled from the lift's seats where it has them (chairlifts, gondolas and cable cars; see [013](013-fill-lift-capacity-and-speed.md)), and otherwise with a typical value for the lift type, from the medians in the data. For example: chairlift 2,000 an hour, gondola 2,200, T-bar 1,000, platter or drag 720, magic carpet 900.
- **Implausible capacities** (under 100 or over 6,000 an hour) are treated as missing.
- **Flagging:** each lift records where its capacity came from (recorded, seats, name or type; [013](013-fill-lift-capacity-and-speed.md)), so busy results on guessed capacities can be discounted.
- **Skiers in a sector** are estimated as its total lift capacity ÷ 3.5 rides per skier per hour (`LIFTS_PER_HOUR`).

## Alternatives considered

- **Skier density from beds or visitor numbers.** Not available in the data.
- **Lift capacity per km of piste, per domain.** Simple and robust, and still a good index column, but it can't say which runs are busy.

## Consequences

- **What it can't see:** school holidays, weekends, weather and lifts that are closed.
- **Guessed capacities:** where most capacities are typical values, as at Grandvalira, results are rougher. Wrong recorded capacities, such as Serre Chevalier's cable car at 400 an hour, show up as false overloads.
