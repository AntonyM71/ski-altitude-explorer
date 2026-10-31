# 007. Find sectors from the network, not from place names

**Status:** Proposed (issue #3, prototype). Supersedes the first prototype's use of each lift's commune.

**Code:** [busyness/](../../busyness/) (structure: network, villages, sectors) and [busyness-engine/](../../busyness-engine/) (behaviour: laps, commuting, views); see [012](012-busyness-production-architecture.md)

## Context

Commuting (009) needs **sectors**: parts of a domain between which skiers travel, such as Courchevel, Méribel and Val Thorens. The first prototype used the commune OpenSkiMap records for each lift. That failed in all four test domains:

- **Tignes–Val d'Isère:** Bonneval-sur-Arc, Lanslevillard and Champagny became separate sectors, because a few of the domain's lifts sit on their land.
- **Serre Chevalier:** the Briançon sector was split across Briançon, Puy-Saint-André and Puy-Saint-Pierre. Pelvoux, which carries the whole Prorel population into the main bowl, came out too quiet.
- **Grandvalira:** lifts carry only the Andorran parish (55 of 77 are "Encamp"), so there were almost no sectors and almost no commuting.

## Decision

Sectors come from how lifts exchange skiers:

1. Work out, for each lift, the share of skiers leaving its top who next ride each other lift. Laps (006) are a Markov chain: each junction's ways on are weighted by pull, and a lift ends the lap. So the shares are exact absorption probabilities, B = (I − Q)⁻¹ R, rather than the result of running the laps flow from each lift. (The prototype ran the flow; see the evidence below.)
2. Treat lifts as points joined by those exchanges, and group lifts that mostly swap skiers among themselves. This uses Louvain community detection, from `networkx`.
3. Merge any sector under 4% of the domain's lift capacity (`SECTOR_MIN`) into the neighbour it exchanges most with.
4. Name each sector by its most common commune (or region) and its biggest lift, for example "Val d'Isère (Solaise)".

## Evidence

**Exact exchange shares** (busyness-production-architecture). Computing the shares exactly gives the same groupings as running the flow: identical for Serre Chevalier; one sector differing by 2 lifts in Les Trois Vallées. In Tignes–Val d'Isère it merges the Le Fornet (Cascade) and Solaise back-side (Leissières) sectors, which matches the owner's view that Le Fornet is part of Val d'Isère. It also fixed a prototype bug: the flow recorded every lift at a junction as reached, even nursery lifts with no pull, and those zero exchanges pulled 24 nursery lifts into Serre Chevalier's Combes sector, doubling its capacity and cutting its commuting share from 45% to 35%. Sectors still conflate home areas and ski areas (known issue 11), so this step sits behind a replaceable function.

The sectors match the real ski areas:

| Domain | Sectors found |
|---|---|
| Grandvalira | Pas de la Casa–Grau Roig, El Tarter, Encamp, Canillo, Soldeu (from data with no village names) |
| Tignes–Val d'Isère | Val d'Isère's Bellevarde–La Daille and Solaise sides, Tignes Le Lac, Tignes Les Boisses–Brévières, Le Fornet–Pissaillas |
| Serre Chevalier | Chantemerle, Villeneuve, Briançon (Prorel), Le Monêtier, and the Vallons |
| Les Trois Vallées | six sectors, splitting Val Thorens from Les Menuires and Courchevel's lower villages from its upper slopes |

After the change, Pelvoux rose from outside the top 15 to among Serre Chevalier's busiest runs.

## Consequences

- **Sensitive to the laps model:** sectors depend on the laps weights (006), so changing those can regroup lifts. The Soldeu regression is a likely example: after `LIFT_PULL` changed, the Soldeu gondola's morning load fell to 0.
- **Arbitrary edges:** Louvain is randomised, with a fixed seed, and its sector boundaries aren't unique.
