# Proposal

## Why

Lift bottom stations a short walk apart aren't linked in the network, so skiers who come down to one lift's bottom can only take that lift. At La Daille, the gondola and the Funival's bottom stations are 184 m apart and 15 m different in height, but everyone heading up is sent to the gondola. In the lift-queues trial it got a 48-minute queue (known issue 16). Skiers walk between nearby lift bottoms in villages and lift hubs all the time.

## What Changes

- **Lift stations a short walk apart are joined, where nothing else joins them.** A lift's top or bottom gets a walking link to another lift's bottom within 250 m horizontally (`LIFT_WALK_M`) and 30 m of height (`LIFT_WALK_RISE_M`), wherever runs and walks don't already lead from one to the other. Two nearby bottoms are joined both ways. No walk leads to a lift's top. Where a run already joins two lifts (from Roc 1's top to Roc 2's bottom, for example), skiers keep skiing it rather than walking.
  - **Size:** across the four test domains, this adds about 35 walks. They fill real gaps:
    - Daille to the Funival;
    - the lift bottoms at Soldeu and El Tarter;
    - Croisette's top to the Menuires and Roc 1 bottoms.
- **Longer walks take longer.** These walks take their distance ÷ 1 m/s (`WALK_SPEED`), and at least the usual 30 s (`WALK_S`): about 3 minutes for La Daille's 184 m.
- **A walk is as attractive as what it leads to.** A walking link's pull becomes that of the best run or lift it leads to, not only the best run. This also applies to the existing walks from run ends to lift bottoms: those took a default pull of 1.0 where the bottom had no run, and now take the lift's pull. Python's sector finding and the engine use the same rule.
- **The model version goes up**, so every domain is rebuilt.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `busyness-network`: "Walking links at lift stations" adds walks from a lift's top or bottom to another lift's bottom a short walk away, where nothing else joins them, with a time by distance.
- `busyness-laps`: "Skiers split at junctions by pull" gives a walking link the pull of the best run or lift it leads to.

## Impact

- **Code:**
  - `busyness/network.py` (the new walks);
  - `busyness/params.py` (the three constants, and `MODEL_VERSION` 4);
  - `busyness/sectors.py` (walk pull);
  - `busyness-engine/src/laps.js` (walk pull);
  - tests in both.
- **Results:** every domain's structure file changes. Lift hubs with several bottom stations spread lapping skiers and commuters between their lifts. Sectors may shift slightly where walks join lifts of different sectors. The four test domains are rebuilt, and decision 011 is rechecked.
- **Other changes:** `lift-queues` waits on this one. Its delta for "Skiers split at junctions by pull" is rebased onto the new walk rule.
- **Docs:** decision 005 and known issue 16.
- **No new dependencies.**
