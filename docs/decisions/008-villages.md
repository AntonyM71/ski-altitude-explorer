# 008. Find villages from OpenStreetMap places, sized by their buildings

**Status:** Proposed (issue #3, prototype)

**Code:** [busyness/](../../busyness/) (structure: network, villages, sectors) and [busyness-engine/](../../busyness-engine/) (behaviour: laps, commuting, views); see [012](012-busyness-production-architecture.md)

## Context

The morning and evening rushes (010) start and end where skiers sleep. The data has no village or bed locations. The project owner's observation that Plein Sud and the Funitel 3 Vallées in Val Thorens are often full first thing can't be reproduced without them.

## Decision

Villages come from OpenStreetMap, with the lift-layout rules below kept as a fallback.

- **Places.** Town, village, hamlet and neighbourhood points around the domain, from Overture Maps (its `divisions` theme, which comes from OpenStreetMap) at a pinned release (`OVERTURE_RELEASE`), queried with DuckDB and cached per release. Overpass, the source in the prototype, couldn't take a weekly load for every domain; it remains for local use.
- **Size.** Each place is sized by counting buildings within 500 m of its point (`PLACE_BUILDINGS_M`), from Overture's buildings theme: OpenStreetMap first, with gaps filled by national datasets and Microsoft and Google footprints. Places with fewer than 50 (`PLACE_MIN_BUILDINGS`) are thoroughfares that skiers pass through, not villages.
- **Matching.** Every lift station within 1 km (`PLACE_M`) of a town, village or hamlet belongs to the nearest one; only where there's none does it belong to the nearest neighbourhood. (Overture maps many towns as several neighbourhoods, such as Val d'Isère's quarters; some resorts, such as Val Claret, are only a neighbourhood.) A place's stations merge into one village. A village is its streets, not the slope above it, so only stations within 200 m of height above its lowest station belong (`VILLAGE_RISE_M`).
- **Village lifts.** A place needs at least 500 an hour of lifts leaving it (`PLACE_VILLAGE_CAP`). Nursery lifts (005) don't count: they're for ski school, not the way out of the village.

**Fallback when places can't be fetched:**

- **Clusters.** Lift bottoms within 300 m and 120 m of altitude of each other form a cluster.
- **Villages.** A cluster is a village if it has at least 1,500 an hour of lift capacity leaving it (`VILLAGE_CAP`), and no other station of that size lies more than 50 m lower within 1.5 km (`VILLAGE_RADIUS_M`). Small lifts below a village, such as nursery tows, don't count against it.
- **Spread.** A village takes in other lift stations within 800 m (`VILLAGE_SPREAD_M`) and up to 200 m above its low point (`VILLAGE_RISE_M`).
- **Residents.** The domain's skiers (004) live in its villages, in proportion to the lift capacity leaving each village. A village is sized by its own lifts out, not by the terrain above it: resorts build access lifts for the people staying there, and the terrain is skied by people from everywhere, through laps and commuting. A sector with no village still houses skiers at its busiest station (to be removed; see known issues).

## Evidence

Each earlier rule failed in a specific way:

| Rule tried | Failure |
|---|---|
| A village needs runs finishing at it | Missed Encamp and Canillo, whose gondolas start in town with no piste down to them. Mid-mountain stations were picked instead, and small drag lifts came out 4–5× over capacity in the morning. |
| Can't ski from it to a lower lift of the same sector | Mid-mountain stations still qualified, partly because narrow joins (005) made them dead ends. |
| Only the lowest cluster in a village | Missed Plein Sud, which starts higher up in Val Thorens. Val Thorens's lifts start anywhere from 2,200 to 2,350 m. The spread rule raised Plein Sud from 112th to about 30th in the morning. |
| Villages from lift layout alone (any rule above) | Grandvalira showed the limit: mid-mountain hubs passed as villages (El Forn, the top of the Canillo gondola; Llac del Cubil; the Funicamp mid-station), because the gondolas up to them are longer than 1.5 km. Grau Roig's 11 lifts made it house more skiers than Pas de la Casa, and Pas de la Casa was split in two. Every new rule fixed one resort and broke another. |
| Places without a size threshold | Small places on the way between villages became villages: Grau Roig (3 buildings) between Pas de la Casa and Soldeu, les Bordes d'Envalira (23), and Fréjus (43) and Serre Ratier (39) at Serre Chevalier. With a 50-building minimum they're thoroughfares, and Pas de la Casa becomes Grandvalira's biggest village. Real villages pass easily: Soldeu has 76 buildings, La Daille 87, Val-d'Isère 490 and Le Monêtier-les-Bains 997. |
| Each sector's skiers (its total lift capacity ÷ 3.5) housed in its own villages | Sized villages by the terrain above them. Le Fornet, a hamlet below the Pissaillas glacier, housed the whole sector's 3,500 skiers, so its 1,000-an-hour cable car read 2.4× in the morning, when it's adequate for its village. Sizing villages by their own lifts out put it at 0.5×, with Soldeu at 0.7× and the Funitel 3 Vallées 2nd at 1.6×. |
| Stations within 800 m of a place | Plein Sud's station is 869 m from Val Thorens's place point, so it dropped out of the village and fell to 0.2× in the morning. Widened to 1 km. |
| No height limit on a place's stations | The Funitel 3 Vallées starts about 350 m above Val Thorens, at the top of Plein Sud, but was swept into the village, so commuters "walked" to it and skipped Plein Sud (20 commuters an hour, against the Funitel's 2,177). With the 200 m limit they ride Plein Sud or Pionniers up to it. |
| Any lower lift station within 1.5 km disqualifies a village; a sector with no village houses its skiers at its lowest station | Soldeu was disqualified by the Canaro nursery tows, 850 m away and 100 m lower, with 1,200 an hour between them. Its sector then housed everyone at those tows, so the Soldeu gondola, which people walk to from their hotels, showed 0.0× in the morning. Counting only village-sized stations against a village, and falling back to a sector's busiest station, raised it to 0.5× (22nd of 77). |

With places and buildings, the villages are:

- **Grandvalira:** Pas de la Casa, el Tarter, Encamp, Soldeu and Canillo.
- **Tignes–Val d'Isère:** La Daille, Val-d'Isère, Le Laisinant, Tignes, Les Brévières and Les Boisses.
- **Serre Chevalier:** Le Monêtier-les-Bains, Villeneuve, L'Envers (Chantemerle), Le Pinet, Le Bez and Puy-Saint-Pierre.
- **Les Trois Vallées:** Val Thorens, Les Ménuires, Les Bruyères, Saint-Martin-de-Belleville, Méribel-Mottaret, Méribel's villages, Courchevel's villages and La Tania. Plan-Bouchet (38 buildings), the hamlet at the top of the Orelle gondola, and Le Molard (26) are thoroughfares; Plan-Bouchet's skiers move to Val Thorens.

## Consequences

- **Sectors without their own village.** Some sectors have no village of their own, so their visitors appear to live at their busiest station. In reality most come from a neighbouring village, as the Fornet–Pissaillas sector's skiers mostly come from Val d'Isère.
- **Every village's lifts carry the same share from locals.** Sizing villages by their own lifts means locals load every village's lifts equally in the morning (about 0.3×). Differences come from traffic passing through. Without bed data that's the honest default, but the absolute level is an assumption.
- **Building counts aren't used for size,** only to rule out thoroughfares. Dense apartment blocks (La Daille) and scattered chalets count the same per building.
- **Fit to these domains.** The thresholds were tuned on four domains and may need adjusting elsewhere.
- **An outside service.** Places and buildings come from the public Overpass service, which is slow and sometimes unavailable (it returned "502 Bad Gateway" during testing, and Les Trois Vallées's building counts timed out on the first attempt). Fine for a prototype; not for a weekly build across every domain (see known issues).
