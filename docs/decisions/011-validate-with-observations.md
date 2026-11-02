# 011. Validate against skiers' observations, not usage data

**Status:** Proposed (issue #3, prototype)

**Code:** [busyness/](../../busyness/) (structure: network, villages, sectors) and [busyness-engine/](../../busyness-engine/) (behaviour: laps, commuting, views); see [012](012-busyness-production-architecture.md)

## Context

There's no ground truth for busyness: no lift scan data or skier counts. Without some check, the model's weights (006, 009) can't be judged.

## Decision

Each change to the model is rerun on four test domains: Les Trois Vallées, Tignes–Val d'Isère, Serre Chevalier and Grandvalira. Their structure files are kept as test fixtures, and CI runs the engine on them and checks every observation marked ✓ below (`busyness-engine/test/observations.test.js`). The results are checked against observations from people who ski there. Review maps with day, morning and evening views make that check quick. The observations themselves are kept in [docs/observations.md](../observations.md). The table below tracks how the model compares, and a change that breaks an earlier match is treated as a regression.

The model also checks itself: a run stops with an error, rather than writing results, if any commuting share falls outside 0–100% or any traffic comes out negative. A variable-reuse bug once produced negative shares, and so negative skiers, which reached the review maps before this check existed.

## Observations and how the model compares

As of lift queues (015: queues where more skiers arrive than a lift releases, avoided at the lift and ahead, and rush queues) and lift-bottom walks (lift stations a short walk apart joined where nothing else joins them, 005) and lift estimates (013: missing capacities and speeds from seats, names and cable car length) on the production pipeline and engine (busyness-production-architecture): structure files built by the `busyness` package, with villages from Overture Maps places and exact sectors, and the JavaScript engine, which counts lapping skiers from every lift where several share a top station (the prototype kept only one). Earlier refinements are as described in 005–010: places sized by their own lifts, nursery areas as links only, commuters setting off from their own part of the village, evenings that mirror the morning, commuting that rises with how much of the domain lies elsewhere, end-of-day conditions, skied-out runs, faster easy runs for able skiers, riding down, runs joined where they cross, and short blacks counting more like reds except in end-of-day conditions.

| Domain | Observation | Model |
|---|---|---|
| Les Trois Vallées | Plein Sud is usually full in the mornings, often with a queue | ~ 0.76× in the morning (35th of 127 lifts; 0.64× before lift queues). **Open** (known issues 4, 8). |
| Les Trois Vallées | The Funitel 3 Vallées is often full at the start of the day, partly with commuters; reached by Plein Sud or Pionniers | ✓ 1.05× in the morning (17th; 1.6× before lift queues, as skiers spread to other lifts). Pionniers 1.0×. |
| Les Trois Vallées | Lac de la Chambre is busy | ~ 10th and 12th of 318 by day (5th and 6th before lift queues). **Open** since lift queues (015): skiers steer away from runaway valley queues (known issues 18, 19). |
| Les Trois Vallées | Doubt about Ours's ranking against Sittelle | Sittelle 4th, Ours 15th by day. Unconfirmed. |
| Tignes–Val d'Isère | The Face de Bellevarde is often less chewed up than Joseray; Joseray may be moguled by evening | ✓ In the evening Face 1,179, Joseray 1,673 an hour. By day the Face is busier (1,221 against 806), since short blacks count more like reds (006) and more skiers lap Bellevarde. |
| Tignes–Val d'Isère | Henri, Lac and Combe are busy | ✓ Henri 8th, Combe 24th, Lac 44th of 151 by day: all in the busiest 30% (Lac was 34th, in the busiest quarter, until lift-bottom walks regrouped Val d'Isère's sectors; Combe and Lac were 11th and 21st before the shared-top fix) |
| Tignes–Val d'Isère | Edelweiss and Combe carry Tignes → Val d'Isère traffic | ~ Edelweiss 17th by day, 39% commuters (7th and 44% before lift queues). **Open** since lift queues (015): skiers steer away from runaway valley queues (known issues 18, 19). |
| Tignes–Val d'Isère | Piste M is busy at the end of the day; quieter during the day | ✗ 48th of 151 in the evening (about 830 an hour). **Open** (known issue 1). |
| Tignes–Val d'Isère | Skiers avoid flat runs such as the Traversée du Laisinant | ✗ Not avoided by day any more (11th; 60th before lift queues, as skiers on the Le Fornet side steer away from the queued Glacier and Datcha chairs, 74 and 65 minutes by day), and 8th in the evening (about 1,930 an hour), with Piste L 4th. **Open** (known issue 1; whether the Glacier and Datcha chairs really queue by day is unconfirmed). |
| Tignes–Val d'Isère | Santons is a busy home run at the end of the day | ✗ Santons haut 41st and Santons 51st in the evening. **Open** (known issue 2). |
| Tignes–Val d'Isère | Daille sits fairly empty during the day | ✗ the Daille gondola and the Funival have runaway day queues in the model (about 1,130 and 1,350 minutes, which aren't real waits), as everyone skiing down to La Daille ends there. **Open** (known issue 18). |
| Tignes–Val d'Isère | Le Fornet's Glacier and Datcha chairs aren't heavily queued; skiers stay in the bowls above | ✗ 74 and 65 minutes by day in the model. **Open** (known issue 18). |
| Tignes–Val d'Isère | Staying in Tignes: home down Johan Clarey | ✓ 27th in the evening |
| Tignes–Val d'Isère | People ride Solaise, the Olympique and Tovière down at the end of the day | ✓ Solaise 851, Olympique 2,349 and Tovière 1,658 an hour riding down. ~ Tovière at 69% of capacity is probably still too much (known issue 10). |
| Tignes–Val d'Isère | Le Fornet's cable car is adequate for its village | ✓ 0.41× in the morning |
| Serre Chevalier | Pelvoux is busy, carrying the Prorel population into the main bowl | ~ 7th of 88 by day (4th before lift queues). **Open** since lift queues (015): skiers steer away from runaway valley queues (known issues 18, 19). |
| Serre Chevalier | Traverse is busy | ✓ 3rd of 88 by day |
| Serre Chevalier | Le Monêtier's lifts head over to Cucumelle (expected, not observed) | ~ the Cucumelle chair 0.68× in the morning (9th of 43 lifts; 0.96× and 3rd before lift queues). **Open** since lift queues (015): by day the model gives it a long queue, so fewer laps are under way at the rush (known issues 18, 19). |
| Serre Chevalier | Cucumelle is a natural bottleneck, but its queue is never more than about 20 minutes | ✗ 38 minutes by day in the model. **Open** (known issues 18, 19). |
| Serre Chevalier | Aravet is usually quiet during the day | ✗ a runaway day queue in the model (about 335 minutes, not a real wait): skiers reaching its bottom have no other way on, since Casse du Bœuf isn't linked. **Open** (known issues 18, 19). |
| Serre Chevalier | Prorel: some people ride it down, never full | ✓ 344 and 324 an hour riding down (about 15% and 14%) |
| Serre Chevalier | Going home to Chantemerle, people mostly ride Ratier down or ski Briance; Luc Alphand should be quieter than Briance | ✗ Luc Alphand 9th in the evening (1,401 an hour), Briance 686, Ratier 678 riding down. **Open** (known issue 3). |
| Serre Chevalier | Pylônes is fine for confident intermediates: greens cross it, so you can bail out at any time | ✓ crossings by greens joined (005); 712 m at most before a way out, so by day it counts partly as a red: 389 an hour. |
| Grandvalira | The Soldeu gondola is busy in the morning, but not with 20-minute queues | ✓ 0.79× (12th of 45 lifts); the TSD6 Soldeu beside it, a short walk away, is 0.93× |
| Grandvalira | Grau Roig is a thoroughfare, not a village | ✓ excluded (10 buildings in Overture's data) |
| Grandvalira | Gall de Bosc is busy | Out by design: a beginner area, left to ski school (005). |
| Grandvalira | Pista Llarga seemed unusually busy | ~ eased by wider lift joins (005) and lift queues (015): 10th by day at about 1,580 an hour (1st at 2,030 before lift queues). **Open** (known issue 15). |

## Consequences

- **Small sample:** four domains and a dozen observations, from one person, partly from memory. More observers and domains would make the weights more trustworthy.
- **Tuned to these resorts:** the model is tuned to these resorts, and may behave differently elsewhere.
