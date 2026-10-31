# 010. Three views: day average, morning rush and evening rush

**Status:** Proposed (issue #3, prototype)

**Code:** [busyness/](../../busyness/) (structure: network, villages, sectors) and [busyness-engine/](../../busyness-engine/) (behaviour: laps, commuting, views); see [012](012-busyness-production-architecture.md)

## Context

Busyness changes through the day. Village lifts queue first thing and home runs fill at close. A single all-day average hides both. The project owner's first check, Plein Sud and the Funitel 3 Vallées full at the start of the day, is a morning effect.

## Decision

The model produces three views, all per hour:

| View | What's counted |
|---|---|
| **Day average** | Laps (006), plus each commuter's outbound and return trip, spread over a 6-hour day (`DAY_HOURS`). |
| **Morning rush** | Everyone leaves their village within 1.5 hours (`PEAK_HOURS`). Locals ride the village lifts, split by capacity. Commuters take their outbound route. Laps already under way are added at 40% (`RAMP`). |
| **Evening rush** | Everyone skis home within 1.5 hours, back to where they set off from: the morning in reverse, but starting on the mountain. Locals set off from where their village's lifts took them, by the sectors of the lifts those riders take next, in the same proportions as they left. Commuters set off home from the sector they visited. On the way home, harder runs feel harder still and enclosed lifts can be ridden down (009). Laps are added at 40%. |

Lifts are reported as demand ÷ capacity. Over 1× means a queue.

## Evidence

- **Funitel 3 Vallées:** 7th of 169 lifts at 0.4× in the first version; 5th to 8th at 1.2–1.5× in the morning view. This matches the owner's experience.
- **Village lifts full in the morning:** the El Tarter and Soldeu gondolas at Grandvalira, and the Funival and Tommeuses at Val d'Isère, come out at or near capacity.
- **A bug that inflated the rushes.** Commuting in both rushes was 6× too high, because the day's trips were multiplied by the day length instead of being spread over the rush. It was found and fixed.
- **Where locals set off from in the evening.** At first, a village's locals all set off home from one sector: the one the village was assigned to. Val-d'Isère's six village lifts all count as the Bellevarde ("Olympique") sector, including the Solaise gondola, whose riders spend the day on the Solaise side. So nobody came home over Solaise and down Piste M, which the owner observes is busy at the end of the day. Following where each village lift's riders go next sets the Solaise gondola's riders off from the Solaise side. Santons rose to 12th in the evening, which also matches observation.

## Consequences

- **Fixed timing:** the 1.5-hour rush and the 40% ramp are fixed assumptions, so the rushes are sharp. Real arrival is spread out by ski school, late starters and buses.
- **A highly sensitive view:** the evening view depends on village detection (008) more than the other views do.
- **No buses home.** Skiers who come down to the wrong village must ski home, because valley ski buses aren't in the network. On the Solaise back side, the quickest way home to Val d'Isère is down Piste L and along the flat traverse, so they take it rather than coming back over Solaise and down Piste M (see known issues).
