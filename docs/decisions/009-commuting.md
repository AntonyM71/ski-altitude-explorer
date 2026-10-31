# 009. Commuting: a gravity model with ability groups and varied routes

**Status:** Proposed (issue #3, prototype)

**Code:** [busyness/](../../busyness/) (structure: network, villages, sectors) and [busyness-engine/](../../busyness-engine/) (behaviour: laps, commuting, views); see [012](012-busyness-production-architecture.md)

## Context

In big linked domains, many skiers spend the day in another sector, such as Val Thorens to Méribel or Tignes to Val d'Isère. They load the link runs and lifts, a pattern that laps alone can't produce.

## Decision

- **Who commutes depends on how much there is to go to.** In a small resort you don't make a mission to the other side, you just end up there through laps. In a big domain you might go somewhere else most days. Each sector's commuting share is `COMMUTE_TOP` (60%) × (1 − the sector's share of the domain's lift capacity): 0% for a single-sector resort, 30% for two equal halves, and 34–56% across the sectors of the four test domains. A village's skiers commute at its sector's share; the rest stay local and lap.
- **Where they go (a gravity model).** A sector draws commuters in proportion to its lift capacity, discounted by e for every hour of travel (`DECAY_MIN = 60`).
- **Start and end points.** Trips start from the commuter's own part of the village: each of the village's stations, in proportion to the lifts leaving it, stands in for where people are staying. They end anywhere in the destination sector, spread over its lift bottoms by capacity. The trip home starts from its lift tops and returns to the same station.
- **Ability groups.** Commuters come in three groups (`ABILITIES`). Each feels the grades differently:

  | Group | Share | Reds feel | Blacks feel |
  |---|---|---|---|
  | Cautious | 30% | 2× slower | 6× slower (effectively avoided) |
  | Intermediate | 50% | 1.3× slower | 2.5× slower |
  | Strong | 20% | as they are | 1.1× slower |

  A short black you can bail out of feels more like a red, scaled by its committed length, as in laps (006). Each group chooses destinations and routes separately, and their traffic is added up. In the evening rush, locals going home are split into the same groups.
- **The way home is different.** On the way home in the evening, for commuters and locals alike:
  - **End-of-day conditions.** Harder runs feel harder still, for tired legs and worse snow: reds ×1.2 and blacks ×1.6 on top of each group's weights (`EVENING_FEEL`). It applies in full to every black, however short: a way out makes a black less daunting to start, not easier on tired legs at the end of the day.
  - **Skied-out runs.** A run busy all day is moguled or chopped up by evening, and feels up to 1.5× harder, reaching that at 30 lapping skiers an hour per metre of width (`SKIED_OUT_MAX`, `SKIED_OUT_REF`).
  - **Able skiers go faster on easy runs.** Greens take intermediates 0.6× and strong skiers 0.5× of the grade's typical time (`EASY_PACE`); the typical green speed is a beginner's.
  - **Riding down.** Gondolas, cable cars and funiculars can be ridden down (005). Most people would rather ski home, so riding down feels as it is to cautious skiers, 4× slower to intermediates and 5× to strong skiers (`DOWNLOAD_FEEL`). A lift carries at most its capacity down: beyond that, riding it feels slower and everyone is routed again, up to three times (`DOWNLOAD_MAX_LOAD`, `DOWNLOAD_PASSES`), so the excess skis home.
- **Route.** Each trip takes the route that feels quickest to its group. Run times are also scaled by gradient for everyone: near-flat runs ×1.4 for the poling, runs steeper than 45% on average ×1.3.
- **Spread over routes (stochastic assignment).** 30 draws (`DRAWS`), each varying every journey time by about ±30% (`NOISE`), averaged.
- **Times.**
  - Lifts use their recorded ride time where it exists, otherwise length ÷ a typical speed for the type, plus 90 s of queueing and loading.
  - Runs use a typical speed by grade, slowed on flat runs (006).

## Evidence

Each refinement fixed something visible:

| Problem | Fix |
|---|---|
| Valleys weighted by lift capacity rather than skier numbers sent 25,000 commuters an hour from one valley. | Count skiers as capacity ÷ 3.5 rides an hour: about 1,200 an hour each way between Belleville and Courchevel. |
| Everyone took the single quickest path, so some pistes were 90%+ commuters. | Random variation over 30 draws spreads trips over several routes. |
| Commuters skied the Face de Bellevarde. | Grade-aware route times. |
| Commuters' trips home were never counted. | Route the return leg as well as the outbound. |
| The way home was treated like any other trip. Luc Alphand, a low black to Chantemerle, was the 4th busiest run in Serre Chevalier's evening rush, though it's often difficult at that hour; nobody rode gondolas down. | End-of-day conditions and riding down: Luc Alphand fell to 68th, and Prorel, Solaise and the Olympique carried people down. |
| Riding down then took over: Tovière carried 5,844 an hour down, 2.7× its capacity, and Santons, Piste M and Johan Clarey emptied. | Most people prefer to ski home (riding down feels 2.5×, later 4×, slower to intermediates), and a cap on rides down. A first cap at 50% of capacity matched Prorel ("some people") but pushed Ratier's excess onto Luc Alphand. Ratier is busier because its alternatives are a black or a long green, so the cap became the lift's physical capacity. |
| Intermediates took Luc Alphand over Briance, the green home to Chantemerle, because the model thought 5.5 km of green took them 27 minutes: beginner pace. | Able skiers go faster on easy runs. Briance (985 an hour) now matches Luc Alphand (998), and Ratier carries 966 down. |
| Runs crossing each other weren't joined (005). | With crossings joined, Luc Alphand became quieter than Briance in the evening (878 against 1,004 an hour), with Ratier carrying 934 down. |
| Every black counted the same, however short. | Blacks scaled by committed length (006). But Briance crosses Luc Alphand so often that its longest stretch is 466 m, so it counts nearly like a red and became 3rd busiest in the evening (1,694 an hour), with Briance down to 342. Tovière, at capacity riding down, eased to 1,517 of 2,200 an hour. |
| The end-of-day penalty was blended away with the rest. | Keep it in full for every black (OpenSpec change `keep-evening-black-penalty`). Luc Alphand fell to 7th (1,432 an hour) and Briance rose to 518, with Ratier carrying 930 down. That's better, but Luc Alphand is still busier than Briance. Accepted as a partial fix; the rest is open (known issues). Tovière riding down rose to 1,830. |
| Joseray was observed to be skied out by the end of the day, making the Face more appealing. | Skied-out runs feel harder in the evening: Joseray 1,736 an hour, the Face 896. |
| A flat 25% of every village's skiers commuted, in every resort. The project owner, staying in Tignes, skied away from the home area on two days out of three. | The share now rises with how much of the domain lies elsewhere (34–56% in the test domains). The Face de Bellevarde became clearly quieter than Joseray again (570 against 657 skiers an hour), the Funitel 3 Vallées rose to 6th in the morning (1.5×), Lac de la Chambre to 6th by day, and Edelweiss to 733 commuters an hour. |
| A village was treated as one point, so all its commuters set off from whichever station gave the quickest route. All of Val Thorens's commuters went up Pionniers, though some parts of the village can't easily reach it. | Commuters set off from each of the village's stations in proportion to its lifts. Plein Sud's commuters rose from 494 to 768 an hour in the morning rush, with Pionniers still the busier of the two. |
| Every commuter was the same average intermediate. A black was used only when it was far quicker or a random draw favoured it, so strong skiers, who happily take blacks, weren't represented. | Three ability groups. Some strong skiers now take blacks such as the Face de Bellevarde, and cautious ones stay off red links. |

The result matches the owner's observations: Edelweiss and Combe carry Tignes → Val d'Isère traffic, and Lac de la Chambre is busy.

## Consequences

- **Guessed parameters.** The 60% top share, the 60-minute decay, and the ability groups' shares and grade weights are guesses, with no data to calibrate them. They're tuned against observations (011).
- **Laps don't use the groups.** Laps (006) already split skiers in proportion at each junction, which stands in for a mix of abilities.
- **More computation.** Each group is routed separately, so commuting takes about three times as long. Les Trois Vallées runs in about 35 s in all.
