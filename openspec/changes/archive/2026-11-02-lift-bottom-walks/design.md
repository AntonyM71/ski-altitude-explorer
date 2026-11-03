# Design

## Context

`busyness/network.py` builds walking links after runs and lifts are joined, in two kinds:
- from a lift's top to run starts within `LIFT_TOP_M`;
- from run ends to a lift's bottom within `LIFT_BOTTOM_M`.

Each takes `WALK_S` (30 s). Lift bottoms that line ends snapped together (within `SNAP_M`) already share a junction: Tovière, Palafour and Almes at Tignes Le Lac, for example. Lift bottoms further apart than that aren't linked at all.

A walk's pull, "the best run it leads to", is computed in two places that must agree (busyness-validation):
- `pull()` in `busyness/sectors.py`, for the exact exchange shares behind sectors;
- `pulls()` in `busyness-engine/src/laps.js`, for laps.

A trial on Tignes–Val d'Isère found these pairs of bottoms within 250 m and 30 m of height:
- Daille and Funival (184 m);
- the Brévières pair (137 m);
- the Tichot cluster (212 m);
- the Marmottes cluster (247 m);
- Mont Blanc and Tommeuses (178 m), which the project owner confirmed is a natural walk.

Tommeuses' bottom and Daille's top (303 m away, 49 m up) aren't joined: that's bottom to top, and outside the limits anyway.

## Goals / Non-Goals

**Goals:**
- Skiers can walk to a nearby lift's bottom where the network has no other way there, at a realistic walking cost, in laps, commuting and sectors alike.

**Non-Goals:**
- Walks to a lift's top, and walks beside routes that runs already provide.
- Checking for barriers between stations (a river, a road, a building). The rule is distance and height only.
- Ski buses (known issue 1).
- Fixing the Funival's mapping in two pieces, or its capacity: those are data issues, kept in known issue 16.

## Decisions

- **To a lift's bottom, from a lift's top or bottom, filling gaps only.** For each lift station (top or bottom) and each other lift's bottom (nursery lifts included), within `LIFT_WALK_M` (250) horizontally and `LIFT_WALK_RISE_M` (30) of height, add a walk only if runs and walks don't already lead there. That's checked by a search over runs and walks from the station, before any of these walks are added. Two nearby bottoms are checked each way, so they're usually joined both ways. No walk leads to a lift's top, so a skier is never sent from a lift's bottom up to another lift's top (as from Tommeuses' bottom to Daille's top, which the project owner ruled out).
  - **Why only gaps:** a walk's pull is the lift's (below), so a walk beside an existing run would draw skiers off the run and onto the lift. It would cut laps short, as if skiers walked to the next lift rather than ski to it. From Roc 1's top, the run Violette already reaches Roc 2's bottom (391 m), and Portette's top and Thorens's bottom already share a junction. Both stay as they are.
  - **What the trial found** (250 m and 30 m, four test domains): 98 pairs in range, of which 35 had no run or walk between them. Of those, 3 are top to bottom and 32 bottom to bottom, mostly village hubs. Distances use the network's local metric frame (`Network.dist`), and the pairs come from a plain double loop: a few hundred at most per domain.
- **Time by distance:** max(`WALK_S`, distance ÷ `WALK_SPEED`), with `WALK_SPEED` = 1.0 m/s, walking in ski boots with skis. The existing short walks keep a flat `WALK_S`, so today's results don't move for them. The route time equals the time, since walking has no grade factor.
- **A walk's pull is the best run or lift it leads to.** Without the lift, a walk to a lift bottom with no run gets the default 1.0, which would make the Funival a weak option beside the gondola (pull 3.1). The same rule applies to the existing run-end-to-lift walks, which are equally "walk to a lift". It's done the same way in Python and JavaScript, and covered by the busyness-validation check that both halves give the same exchange shares.
- **Ping-pong between two bottoms is harmless.** At each end, a share walks across and a share takes the lift. In both `skiDown` and the exact absorbing-chain computation, the walk back and forth is a geometric series that the lifts absorb. Walks don't climb more than 30 m, so `skiDown` handles them in its sweeps like any other link.
- **Model version 4**, so every domain is rebuilt.

## Risks / Trade-offs

- **[A walk across a barrier]** (a lift bottom on the other side of a road or river within 250 m) → Accepted for now. Check the new pairs listed for the four test domains in task 2.1, and add an exception if one is clearly wrong.
- **[Sectors shift]** where a walk joins lifts of different sectors → Expected and probably right, since a short walk means one place. Compare the four test domains' sectors before and after.
- **[The run-end walk rule change moves today's results]** → Rerun decision 011's observations. Any regression is investigated, not waved through.

## Migration Plan

The pipeline rebuilds every domain once (model version 4). Rollback is reverting the change.
