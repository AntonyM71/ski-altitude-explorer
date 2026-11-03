# 011. Validate against skiers' observations, not usage data

**Status:** Proposed (issue #3, prototype)

**Code:** [busyness/](../../busyness/) (structure: network, villages, sectors) and [busyness-engine/](../../busyness-engine/) (behaviour: laps, commuting, views); see [012](012-busyness-production-architecture.md)

## Context

There's no ground truth for busyness: no lift scan data or skier counts. Without some check, the model's weights (006, 009) can't be judged.

## Decision

Each change to the model is rerun on four test domains: Les Trois Vallées, Tignes–Val d'Isère, Serre Chevalier and Grandvalira. Their structure files are kept as test fixtures, and CI runs the engine on them and checks every observation marked ✓ below (`busyness-engine/test/observations.test.js`). The results are checked against observations from people who ski there. Review maps with day, morning and evening views make that check quick. The observations themselves are kept in [docs/observations.md](../observations.md). The table below tracks how the model compares, and a change that breaks an earlier match is treated as a regression.

The model also checks itself: a run stops with an error, rather than writing results, if any commuting share falls outside 0–100% or any traffic comes out negative. A variable-reuse bug once produced negative shares, and so negative skiers, which reached the review maps before this check existed.

## Observations and how the model compares

As of the simulated day (017: skiers conserved from their villages at 09:00 to home after 15:00, lifts loading from their queues, runs pulling like the lifts they lead to, backup walks out of dead ends, nursery areas as a last resort), the fair-weather altitude preference (006) and lift queues (015: queues where more skiers arrive than a lift's capacity, avoided at the lift and ahead, and rush queues) and lift-bottom walks (lift stations a short walk apart joined where nothing else joins them, 005) and lift estimates (013: missing capacities and speeds from seats, names and cable car length) on the production pipeline and engine (busyness-production-architecture): structure files built by the `busyness` package, with villages from Overture Maps places and exact sectors, and the JavaScript engine, which counts lapping skiers from every lift where several share a top station (the prototype kept only one). Earlier refinements are as described in 005–010: places sized by their own lifts, nursery areas as links only, commuters setting off from their own part of the village, evenings that mirror the morning, commuting that rises with how much of the domain lies elsewhere, end-of-day conditions, skied-out runs, faster easy runs for able skiers, riding down, runs joined where they cross, and short blacks counting more like reds except in end-of-day conditions.

| Domain | Observation | Model |
|---|---|---|
| Les Trois Vallées | Plein Sud is usually full in the mornings, often with a queue | ~ 0.93× in the morning with a 2-minute queue (23rd of 127 lifts; 0.75× before the simulated day, 017). **Open** (known issues 4, 8). |
| Les Trois Vallées | The Funitel 3 Vallées is often full at the start of the day, partly with commuters; reached by Plein Sud or Pionniers | ✗ 0.89× in the morning with a 5-minute queue (32nd), since the simulated day (017; 1.05× before). **Open:** the population is still capacity ÷ 3.5 (016). |
| Les Trois Vallées | Lac de la Chambre is busy | ✗ 71st and 79th of 317 by day since the simulated day (017; 7th and 6th before). **Open.** |
| Les Trois Vallées | Doubt about Ours's ranking against Sittelle | Sittelle 12th, Ours 46th by day. Unconfirmed. |
| Tignes–Val d'Isère | The Face de Bellevarde is often less chewed up than Joseray; Joseray may be moguled by evening | ✓ In the evening Face 350, Joseray 578 an hour; by day the Face is busier (677 against 393). |
| Tignes–Val d'Isère | Henri, Lac and Combe are busy | ✗ Henri 9th, Combe 29th, Lac 69th of 151 by day since the simulated day (017): Lac is outside the busiest 30% (45th). **Open.** |
| Tignes–Val d'Isère | Edelweiss and Combe carry Tignes → Val d'Isère traffic | ~ Edelweiss 21st by day and 17th in the morning. Commuters now count in the rushes, not the day (017), so the test's day share no longer applies. **Open.** |
| Tignes–Val d'Isère | Piste M is busy at the end of the day; quieter during the day | ~ 15th of 151 in the evening (about 700 an hour; 48th before the simulated day). **Open** (known issue 1). |
| Tignes–Val d'Isère | Skiers avoid flat runs such as the Traversée du Laisinant | ~ 34th by day, 6th in the evening as a way home (about 1,070 an hour). **Open** (known issue 1). |
| Tignes–Val d'Isère | Santons is a busy home run at the end of the day | ~ Santons haut 23rd and Santons 31st in the evening (41st and 54th before the simulated day). **Open** (known issue 2). |
| Tignes–Val d'Isère | Daille sits fairly empty during the day | ✗ the Daille gondola runs at capacity by day with a 209-minute queue in the simulated day (017): skiers skiing down to La Daille keep arriving, and the population is still capacity ÷ 3.5 (016). **Open** (known issue 18). |
| Tignes–Val d'Isère | Le Fornet's Glacier and Datcha chairs aren't heavily queued; skiers stay in the bowls above | ✓ Glacier 0.96× with a 1-minute queue, Datcha 0.84× and none, by day in the simulated day (017; 92 and 82 minutes before lift queues were measured against capacity). |
| Tignes–Val d'Isère | Staying in Tignes: home down Johan Clarey | ✓ 11th in the evening |
| Tignes–Val d'Isère | People ride Solaise, the Olympique and Tovière down at the end of the day | ✓ Solaise 416, Olympique 1,506 and Tovière 1,202 an hour riding down, each within capacity (queues at the top, 017). |
| Tignes–Val d'Isère | Le Fornet's cable car is adequate for its village | ✓ 0.61× in the morning |
| Serre Chevalier | Pelvoux is busy, carrying the Prorel population into the main bowl | ✗ 12th of 88 by day since the simulated day (017; 3rd before); Traverse 1st. **Open.** |
| Serre Chevalier | Traverse is busy | ✓ 1st of 88 by day |
| Serre Chevalier | Le Monêtier's lifts head over to Cucumelle (expected, not observed) | ~ the Cucumelle chair 0.67× in the morning (18th of 43 lifts; 0.87× before the simulated day, 017). **Open.** |
| Serre Chevalier | Cucumelle is a natural bottleneck, but its queue is never more than about 20 minutes | ✓ 0.81× by day with no queue in the simulated day (017; 52 minutes before). |
| Serre Chevalier | Aravet is usually quiet during the day | ✗ at capacity by day with a 171-minute queue in the simulated day (017): skiers reaching its bottom have no other way on, since Casse du Bœuf isn't linked. **Open** (known issues 18, 19). |
| Serre Chevalier | Prorel: some people ride it down, never full | ✗ Prorel 1 98 and Prorel 2 319 an hour riding down (4% and 13% of capacity) since the simulated day (017). **Open.** |
| Serre Chevalier | Going home to Chantemerle, people mostly ride Ratier down or ski Briance; Luc Alphand should be quieter than Briance | ✗ Luc Alphand 13th in the evening (about 670 an hour), Briance about 240. **Open** (known issue 3). |
| Serre Chevalier | Pylônes is fine for confident intermediates: greens cross it, so you can bail out at any time | ✓ crossings by greens joined (005); 712 m at most before a way out, so by day it counts partly as a red: 488 an hour. |
| Grandvalira | The Soldeu gondola is busy in the morning, but not with 20-minute queues | ✓ 0.94× in the morning with a 5-minute queue in the simulated day (017). |
| Grandvalira | Grau Roig is a thoroughfare, not a village | ✓ excluded (10 buildings in Overture's data) |
| Grandvalira | Gall de Bosc is busy | Out by design: a beginner area, left to ski school (005). |
| Grandvalira | Pista Llarga seemed unusually busy | ~ 1st by day at about 2,390 an hour (2,140 before the simulated day, 017). **Open** (known issue 15). |

## Consequences

- **Small sample:** four domains and a dozen observations, from one person, partly from memory. More observers and domains would make the weights more trustworthy.
- **Tuned to these resorts:** the model is tuned to these resorts, and may behave differently elsewhere.
