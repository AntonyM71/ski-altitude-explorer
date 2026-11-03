# 011. Validate against skiers' observations, not usage data

**Status:** Proposed (issue #3, prototype)

**Code:** [busyness/](../../busyness/) (structure: network, villages, sectors) and [busyness-engine/](../../busyness-engine/) (behaviour: laps, commuting, views); see [012](012-busyness-production-architecture.md)

## Context

There's no ground truth for busyness: no lift scan data or skier counts. Without some check, the model's weights (006, 009) can't be judged.

## Decision

Each change to the model is rerun on four test domains: Les Trois Vallées, Tignes–Val d'Isère, Serre Chevalier and Grandvalira. Their structure files are kept as test fixtures, and CI runs the engine on them and checks every observation marked ✓ below (`busyness-engine/test/observations.test.js`). The results are checked against observations from people who ski there. Review maps with day, morning and evening views make that check quick. The observations themselves are kept in [docs/observations.md](../observations.md). The table below tracks how the model compares, and a change that breaks an earlier match is treated as a regression.

The model also checks itself: a run stops with an error, rather than writing results, if any commuting share falls outside 0–100% or any traffic comes out negative. A variable-reuse bug once produced negative shares, and so negative skiers, which reached the review maps before this check existed.

## Observations and how the model compares

As of the fair-weather altitude preference (006) and lift queues (015: queues where more skiers arrive than a lift's capacity, avoided at the lift and ahead, and rush queues) and lift-bottom walks (lift stations a short walk apart joined where nothing else joins them, 005) and lift estimates (013: missing capacities and speeds from seats, names and cable car length) on the production pipeline and engine (busyness-production-architecture): structure files built by the `busyness` package, with villages from Overture Maps places and exact sectors, and the JavaScript engine, which counts lapping skiers from every lift where several share a top station (the prototype kept only one). Earlier refinements are as described in 005–010: places sized by their own lifts, nursery areas as links only, commuters setting off from their own part of the village, evenings that mirror the morning, commuting that rises with how much of the domain lies elsewhere, end-of-day conditions, skied-out runs, faster easy runs for able skiers, riding down, runs joined where they cross, and short blacks counting more like reds except in end-of-day conditions.

| Domain | Observation | Model |
|---|---|---|
| Les Trois Vallées | Plein Sud is usually full in the mornings, often with a queue | ~ 0.75× in the morning (36th of 127 lifts; 0.64× before lift queues). **Open** (known issues 4, 8). |
| Les Trois Vallées | The Funitel 3 Vallées is often full at the start of the day, partly with commuters; reached by Plein Sud or Pionniers | ✓ 1.05× in the morning (16th; 1.6× before lift queues, as skiers spread to other lifts). Pionniers 1.0×. |
| Les Trois Vallées | Lac de la Chambre is busy | ✓ 7th and 6th of 318 by day (5th and 6th before lift queues; 9th and 11th while day waits were measured against releases, 015). |
| Les Trois Vallées | Doubt about Ours's ranking against Sittelle | Sittelle 3rd, Ours 15th by day. Unconfirmed. |
| Tignes–Val d'Isère | The Face de Bellevarde is often less chewed up than Joseray; Joseray may be moguled by evening | ✓ In the evening Face 1,153, Joseray 1,676 an hour. By day the Face is busier (1,154 against 781), since short blacks count more like reds (006) and more skiers lap Bellevarde. |
| Tignes–Val d'Isère | Henri, Lac and Combe are busy | ✓ Henri 8th, Combe 24th, Lac 45th of 151 by day: all in the busiest 30% (Lac was 34th, in the busiest quarter, until lift-bottom walks regrouped Val d'Isère's sectors; Combe and Lac were 11th and 21st before the shared-top fix) |
| Tignes–Val d'Isère | Edelweiss and Combe carry Tignes → Val d'Isère traffic | ✓ Edelweiss 9th by day, 42% commuters (7th and 44% before lift queues; 19th and 39% while day waits were measured against releases, 015). |
| Tignes–Val d'Isère | Piste M is busy at the end of the day; quieter during the day | ✗ 48th of 151 in the evening (about 820 an hour). **Open** (known issue 1). |
| Tignes–Val d'Isère | Skiers avoid flat runs such as the Traversée du Laisinant | ✗ Not avoided by day any more (11th; 60th before lift queues, as skiers on the Le Fornet side steer away from the queued Glacier and Datcha chairs, 92 and 82 minutes by day), and 7th in the evening (about 1,930 an hour), with Piste L 4th. **Open** (known issue 1; whether the Glacier and Datcha chairs really queue by day is unconfirmed). |
| Tignes–Val d'Isère | Santons is a busy home run at the end of the day | ✗ Santons haut 41st and Santons 54th in the evening. **Open** (known issue 2). |
| Tignes–Val d'Isère | Daille sits fairly empty during the day | ✗ the Daille gondola has a runaway day queue in the model (about 850 minutes, not a real wait), as everyone skiing down to La Daille ends there; the Funival beside it, a short walk away, has none. **Open** (known issue 18). |
| Tignes–Val d'Isère | Le Fornet's Glacier and Datcha chairs aren't heavily queued; skiers stay in the bowls above | ✗ 92 and 82 minutes by day in the model. **Open** (known issue 18). |
| Tignes–Val d'Isère | Staying in Tignes: home down Johan Clarey | ✓ 27th in the evening |
| Tignes–Val d'Isère | People ride Solaise, the Olympique and Tovière down at the end of the day | ✓ Solaise 851, Olympique 2,335 and Tovière 1,658 an hour riding down. ~ Tovière at 69% of capacity is probably still too much (known issue 10). |
| Tignes–Val d'Isère | Le Fornet's cable car is adequate for its village | ✓ 0.41× in the morning |
| Serre Chevalier | Pelvoux is busy, carrying the Prorel population into the main bowl | ✓ 3rd of 88 by day, Traverse 4th (4th before lift queues; 6th while day waits were measured against releases, 015). |
| Serre Chevalier | Traverse is busy | ✓ 3rd of 88 by day |
| Serre Chevalier | Le Monêtier's lifts head over to Cucumelle (expected, not observed) | ~ the Cucumelle chair 0.87× in the morning (7th of 43 lifts; 0.96× and 3rd before lift queues, 0.68× while day waits were measured against releases, 015). **Open:** it has an 11-minute day queue, so fewer laps are under way at the rush. |
| Serre Chevalier | Cucumelle is a natural bottleneck, but its queue is never more than about 20 minutes | ~ 52 minutes by day in the model (38 before the altitude preference). It's a key transit route, so it should be busy; the wait is still above the observed 20. **Open** (known issues 18, 19; population, #6). |
| Serre Chevalier | Aravet is usually quiet during the day | ✗ a runaway day queue in the model (about 264 minutes, not a real wait): skiers reaching its bottom have no other way on, since Casse du Bœuf isn't linked. **Open** (known issues 18, 19). |
| Serre Chevalier | Prorel: some people ride it down, never full | ✓ 344 and 321 an hour riding down (about 15% and 14%) |
| Serre Chevalier | Going home to Chantemerle, people mostly ride Ratier down or ski Briance; Luc Alphand should be quieter than Briance | ✗ Luc Alphand 10th in the evening (1,386 an hour), Briance 665, Ratier 678 riding down. **Open** (known issue 3). |
| Serre Chevalier | Pylônes is fine for confident intermediates: greens cross it, so you can bail out at any time | ✓ crossings by greens joined (005); 712 m at most before a way out, so by day it counts partly as a red: 390 an hour. |
| Grandvalira | The Soldeu gondola is busy in the morning, but not with 20-minute queues | ✓ 0.73× (17th of 45 lifts), no queue; the TSD6 Soldeu beside it, a short walk away, is 1.02× with about a minute's queue |
| Grandvalira | Grau Roig is a thoroughfare, not a village | ✓ excluded (10 buildings in Overture's data) |
| Grandvalira | Gall de Bosc is busy | Out by design: a beginner area, left to ski school (005). |
| Grandvalira | Pista Llarga seemed unusually busy | ~ 1st by day at about 2,140 an hour since the greens from Les Antenes to Pic Blanc stopped being nursery slopes (005; 2nd at 1,630 before; 1st at 2,030 before lift queues; 11th while day waits were measured against releases, 015). **Open** (known issue 15). |

## Consequences

- **Small sample:** four domains and a dozen observations, from one person, partly from memory. More observers and domains would make the weights more trustworthy.
- **Tuned to these resorts:** the model is tuned to these resorts, and may behave differently elsewhere.
