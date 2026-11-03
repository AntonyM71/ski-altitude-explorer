# Proposal

## Why

Lapping skiers spread downhill by pull alone, so many drift to valley-bottom lifts. In reality, in fair weather, skiers favour the higher areas with better snow and stay in the big bowls; valley lifts like Aravet and Daille sit fairly empty by day (known issues 18 and 22). The model has no notion of this. It's one of the pieces a conceptually correct model needs, before tuning.

## What Changes

- **In the day laps, a lift attracts more the higher its bottom station sits within its domain's range of lift bottoms.** Its pull is multiplied by `ALT_RATIO` ^ (relative height − 0.5), with `ALT_RATIO` = 2 to start: the highest lift bottom pulls √2 times as much as a mid one, the lowest 1/√2. A **run** is weighted by the lifts it leads to, through the same lookahead pass as queues. The height is relative to each domain, so the rule works from the Alps to Japan.
- **Queues stop skiers piling up at the top:** a favoured lift that fills gets a queue, which repels skiers (decision 015).
- **Day laps only.** The morning and evening rushes keep their construction, and sectors (found from base pulls) are unchanged.
- **Expected effect: small, until conservation.** Each lift's top still releases its full capacity, so a preference can change which lift skiers ski to, not how much each lift carries. A trial showed run traffic by altitude barely moving: at a ratio of 2, valley waits fell somewhat (Daille 1,132 → 847 minutes) and top waits rose modestly (Cucumelle 38 → 52). Its full effect needs lifts that carry only what arrives, which is the population and conservation work (#6, known issue 17). The project owner chose to build the conceptually right pieces first, then tune.
- **Not modelled: bad weather,** when skiers seek lower, sheltered terrain and the top runs empty. The preference is a fair-weather one.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `busyness-laps`: a new requirement, "Skiers favour higher areas by day".

## Impact

- **Engine (`busyness-engine/`):**
  - `laps.js`: the altitude factor, opt-in, in `pulls`.
  - `queues.js`: day laps use it.
  - `params.json`: `ALT_RATIO`.
  - Tests.
- **Results:** the day view's queues shift a little uphill, and fixtures are rerun. Decision 011 is rechecked, and nothing regressed is expected to recover yet.
- **Docs:** decision 006, and known issues 18 and 22 (the preference is in, its effect awaits conservation). A new record isn't needed, since 006 covers pull.
- **No change to structure files or sectors.** `params.json` changes every fingerprint, so there's a one-off rebuild.
