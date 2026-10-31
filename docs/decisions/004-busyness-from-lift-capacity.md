# 004. Estimate busyness as a relative index from lift capacity

**Status:** Proposed (issue #3, prototype)

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

Busyness is modelled from **uplift**: every lift is assumed to run at its full capacity, and the model works out where those skiers go. The output is a **relative index**, which ranks runs and lifts against each other within a domain. It isn't a count of people.

- **Missing capacity** is filled with a typical value for the lift type, from the medians in the data. For example: chairlift 2,000 an hour, gondola 2,200, T-bar 1,000, platter or drag 720, magic carpet 900.
- **Implausible capacities** (under 100 or over 6,000 an hour) are treated as missing.
- **Flagging:** lifts using a typical value are marked, so busy results on guessed capacities can be discounted.
- **Skiers in a sector** are estimated as its total lift capacity ÷ 3.5 rides per skier per hour (`LIFTS_PER_HOUR`).

## Alternatives considered

- **Skier density from beds or visitor numbers.** Not available in the data.
- **Lift capacity per km of piste, per domain.** Simple and robust, and still a good index column, but it can't say which runs are busy.

## Consequences

- **What it can't see:** school holidays, weekends, weather and lifts that are closed.
- **Guessed capacities:** where most capacities are typical values, as at Grandvalira, results are rougher. Wrong recorded capacities, such as Serre Chevalier's cable car at 400 an hour, show up as false overloads.
