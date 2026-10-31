# 005. Build a lift and run network, with wide joins at lift stations

**Status:** Proposed (issue #3, prototype)

**Code:** [busyness/](../../busyness/) (structure: network, villages, sectors) and [busyness-engine/](../../busyness-engine/) (behaviour: laps, commuting, views); see [012](012-busyness-production-architecture.md)

## Context

To trace skiers we need a network of where you can go:
- runs downhill;
- lifts uphill;
- junctions where they meet.

OpenStreetMap draws runs and lifts as separate lines. They rarely share points at lift stations, and a run often just passes near a station.

## Decision

- **Junctions.** Runs are cut wherever another run or a lift ends on them. Line ends within 40 m (`SNAP_M`) join into one junction.
- **Crossings.** Where two runs cross mid-way, both get a junction at the crossing, so skiers can switch from one to the other. Crossings within 40 m of a line's end are left to the end joins. A piece shorter than 1 m (two cuts in one place) is dropped, and its ends become one junction.
- **Direction.** Runs point downhill and lifts uphill, using the altitude at each end.
- **Lifts join only at their ends,** so a run passing under a lift doesn't connect to it.
- **Lift stations are big.** A lift's end joins any run passing within 100 m (`LIFT_STATION_M`).
- **Walking links.** A lift's top links to every run starting within 150 m (`LIFT_TOP_M`). Every run ending within 100 m (`LIFT_BOTTOM_M`) links to its bottom. Each walking link takes 30 s.
- **Riding down.** Gondolas, cable cars, funiculars and mixed lifts also get a downhill link, ride time plus queue, that can only be used on the way home in the evening (009, 010). Lapping skiers and morning trips never use it, and it carries at most the lift's capacity. Observed: at the end of the day a share of people ride Prorel, Solaise or the Olympique down rather than ski hard, low or icy runs home.
- **Nursery areas are links only.** Nursery lifts are magic carpets and rope tows, plus drag lifts shorter than 300 m. Nursery slopes are green runs under 400 m long that end within 100 m of a nursery lift's bottom. They stay in the network so commuters and people going home can pass through them. But they're left to ski school: lapping skiers ignore them (006), and they don't count as village lifts or morning departures (008).

## Evidence

**Too tight a join funnelled traffic.** At Grandvalira, the Pic Blanc chairlift's top is 20 m from Pista Llarga, 100 m from Jordi Angles and 140 m from Directa I. With only the 40 m join, every Pic Blanc skier was sent down Pista Llarga. It became the domain's busiest run, at about 2,200 skiers an hour, which the project owner questioned. With wider joins, Pic Blanc's riders spread over all three runs, and Pista Llarga drops to about 1,100 an hour.

**Crossings were invisible.** Runs joined only where one ended on another, so a run crossing another in an X didn't connect. At Serre Chevalier, 3 Croix, Lièvre Blanc and Chêne cross the Pylônes black, and the project owner bails out onto them, but the model saw 1,184 m of black with only Draye, a red, at its top. Joining crossings (61 in Serre Chevalier, 22 in Tignes–Val d'Isère, 30 in Grandvalira) breaks Pylônes into stretches of 272, 712, 155 and 113 m. The altitudes of the two runs agree at every crossing found, because OpenSkiMap's heights come from one terrain model.

**Dropped pieces broke runs apart.** Pieces under 1 m long were dropped without joining their ends. That was harmless until crossings were added: a crossing exactly on a shared point, or three runs crossing at one place, put two cuts in the same spot, and Briance fell apart into dead ends, carrying 13 skiers an hour in the evening instead of about 1,000. Each crossing is now counted once, and the ends of a dropped piece are joined.

**Narrow joins also hid the way on.** Mid-mountain stations had no way on downhill, so they looked like dead ends, and dead ends looked like villages (see 008).

**Nursery areas distorted the model, but some are links.** Val Thorens's five magic carpets took about a fifth of its morning departures, and at the top of the Solaise gondola a dozen beginner-area loops each drew as many lapping skiers as Le Plan, the main descent. Removing nursery areas entirely fixed both and stopped the flat Traversée du Laisinant drawing traffic. But it also cut the Solaise back side off from Le Plan and Piste M: the Pim and Pam magic carpets are the only way back up to the gondola's top. Keeping nursery areas as links, with no pull for laps, kept the fixes and restored the route.

## Consequences

- **Spurious walks:** a wide join can connect a station to a run that's actually separated by a fence or cliff. This hasn't been seen yet.
- **Bridges and tunnels:** a run passing over or under another is joined to it as if it crossed. None has been seen in the test domains, but OpenStreetMap's bridge and tunnel tags could exclude them.
- **Missing runs:** a crossing that isn't mapped can't be joined. The project owner bails out of Pylônes onto Mézies, which isn't in the data.
- **Loops:** walking links can climb slightly, so the flow calculation sweeps repeatedly rather than once (see 006).
- **The nursery rules are crude.** A long green beginner run, or a short drag lift that's a real link, can be misclassified.
- **No buses.** Free valley ski buses aren't in the network, so skiers who end up in the wrong village must ski home, for example along the Traversée du Laisinant to Val d'Isère (see known issues).
