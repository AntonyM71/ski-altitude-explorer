# 011. Validate against skiers' observations, not usage data

**Status:** Proposed (issue #3, prototype)

**Code:** [busyness/](../../busyness/) (structure: network, villages, sectors) and [busyness-engine/](../../busyness-engine/) (behaviour: laps, commuting, views); see [012](012-busyness-production-architecture.md)

## Context

There's no ground truth for busyness: no lift scan data or skier counts. Without some check, the model's weights (006, 009) can't be judged.

## Decision

Each change to the model is rerun on four test domains: Les Trois Vallées, Tignes–Val d'Isère, Serre Chevalier and Grandvalira. Their structure files are kept as test fixtures, and CI runs the engine on them and checks every observation marked ✓ below (`busyness-engine/test/observations.test.js`). The results are checked against observations from people who ski there. Review maps with day, morning and evening views make that check quick. The observations themselves are kept in [docs/observations.md](../observations.md). The table below tracks how the model compares, and a change that breaks an earlier match is treated as a regression.

The model also checks itself: a run stops with an error, rather than writing results, if any commuting share falls outside 0–100% or any traffic comes out negative. A variable-reuse bug once produced negative shares, and so negative skiers, which reached the review maps before this check existed.

## Observations and how the model compares

As of the production pipeline and engine (busyness-production-architecture): structure files built by the `busyness` package, with villages from Overture Maps places and exact sectors, and the JavaScript engine, which counts lapping skiers from every lift where several share a top station (the prototype kept only one). Earlier refinements are as described in 005–010: places sized by their own lifts, nursery areas as links only, commuters setting off from their own part of the village, evenings that mirror the morning, commuting that rises with how much of the domain lies elsewhere, end-of-day conditions, skied-out runs, faster easy runs for able skiers, riding down, runs joined where they cross, and short blacks counting more like reds except in end-of-day conditions.

| Domain | Observation | Model |
|---|---|---|
| Les Trois Vallées | Plein Sud is usually full in the mornings, often with a queue | ~ 0.65× in the morning (38th of 127 lifts). **Open** (known issues 4, 8). |
| Les Trois Vallées | The Funitel 3 Vallées is often full at the start of the day, partly with commuters; reached by Plein Sud or Pionniers | ✓ 1.6× in the morning (6th). Pionniers 1.0×. |
| Les Trois Vallées | Lac de la Chambre is busy | ✓ 5th and 6th of 318 by day |
| Les Trois Vallées | Doubt about Ours's ranking against Sittelle | Sittelle 2nd, Ours 12th by day. Unconfirmed. |
| Tignes–Val d'Isère | The Face de Bellevarde is often less chewed up than Joseray; Joseray may be moguled by evening | ✓ In the evening Face 1,125, Joseray 1,656 an hour. By day the Face is busier (906 against 658), since short blacks count more like reds (006) and more skiers lap Bellevarde. |
| Tignes–Val d'Isère | Henri, Lac and Combe are busy | ✓ Henri 3rd, Combe 24th, Lac 36th of 151 by day: all in the busiest quarter (Combe and Lac were 11th and 21st before the shared-top fix) |
| Tignes–Val d'Isère | Edelweiss and Combe carry Tignes → Val d'Isère traffic | ✓ Edelweiss 5th by day, mostly commuters |
| Tignes–Val d'Isère | Piste M is busy at the end of the day; quieter during the day | ✗ 46th of 151 in the evening (about 670 an hour). **Open** (known issue 1). |
| Tignes–Val d'Isère | Skiers avoid flat runs such as the Traversée du Laisinant | ✗ Avoided by day (48th), but 4th in the evening (about 1,760 an hour), with Piste L 3rd, as the only way home from the Laisinant side without a bus. **Open** (known issue 1). |
| Tignes–Val d'Isère | Santons is a busy home run at the end of the day | ✗ Santons haut 63rd and Santons 70th in the evening. **Open** (known issue 2). |
| Tignes–Val d'Isère | Staying in Tignes: home down Johan Clarey | ✓ 23rd in the evening |
| Tignes–Val d'Isère | People ride Solaise, the Olympique and Tovière down at the end of the day | ✓ Solaise 606, Olympique 1,866 and Tovière 1,761 an hour riding down. ~ Tovière at 80% of capacity is probably still too much (known issue 10). |
| Tignes–Val d'Isère | Le Fornet's cable car is adequate for its village | ✓ 0.37× in the morning |
| Serre Chevalier | Pelvoux is busy, carrying the Prorel population into the main bowl | ✓ 4th of 88 by day (the busiest before the shared-top fix) |
| Serre Chevalier | Traverse is busy | ✓ 3rd of 88 by day |
| Serre Chevalier | Le Monêtier's lifts head over to Cucumelle (expected, not observed) | ✓ the Cucumelle chair 0.96× in the morning (4th of 43 lifts) |
| Serre Chevalier | Prorel: some people ride it down, never full | ✓ 326 and 409 an hour riding down (14% and 17%) |
| Serre Chevalier | Going home to Chantemerle, people mostly ride Ratier down or ski Briance; Luc Alphand should be quieter than Briance | ✗ Luc Alphand 10th in the evening (1,233 an hour), Briance 470, Ratier 664 riding down. **Open** (known issue 3). |
| Serre Chevalier | Pylônes is fine for confident intermediates: greens cross it, so you can bail out at any time | ✓ crossings by greens joined (005); 712 m at most before a way out, so by day it counts partly as a red: 346 an hour. |
| Grandvalira | The Soldeu gondola is busy in the morning, but not with 20-minute queues | ✓ 0.85× (12th of 45 lifts) |
| Grandvalira | Grau Roig is a thoroughfare, not a village | ✓ excluded (10 buildings in Overture's data) |
| Grandvalira | Gall de Bosc is busy | Out by design: a beginner area, left to ski school (005). |
| Grandvalira | Pista Llarga seemed unusually busy | ~ fixed by wider lift joins (005); now 3rd by day at about 1,400 an hour, still well under its old 2,200. |

## Consequences

- **Small sample:** four domains and a dozen observations, from one person, partly from memory. More observers and domains would make the weights more trustworthy.
- **Tuned to these resorts:** the model is tuned to these resorts, and may behave differently elsewhere.
