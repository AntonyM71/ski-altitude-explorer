# busyness-commuting Specification

## Purpose
Route skiers who spend the day in another sector, and everyone's trip home, through the network by the route that feels quickest to them. Rationale and examples: [decision 009](../../../docs/decisions/009-commuting.md).

## Requirements

### Requirement: Commuting share rises with how much lies elsewhere
Each sector's commuting share SHALL be 60% (`COMMUTE_TOP`) × (1 − the sector's share of the domain's lift capacity). Its villages' skiers SHALL commute at that share, and the rest SHALL stay local and lap.

#### Scenario: A single-sector resort
- **WHEN** a domain has one sector
- **THEN** nobody commutes

#### Scenario: Two equal halves
- **WHEN** a domain has two sectors of equal capacity
- **THEN** each sector's commuting share is 30%

### Requirement: Destinations by a gravity model
A sector SHALL draw commuters in proportion to its lift capacity, discounted by a factor of e for every hour of travel (`DECAY_MIN` = 60).

#### Scenario: Two equal sectors at different distances
- **WHEN** two sectors have equal capacity, one 30 minutes away and the other 90 minutes away
- **THEN** the nearer one draws e times as many commuters

### Requirement: Trips start and end where people are
Outbound trips SHALL start from each of the village's stations in proportion to the lifts leaving it, and SHALL end at the destination sector's lift bottoms, by capacity. The trip home SHALL start from the destination's lift tops and return to the same station.

#### Scenario: A village with two stations
- **WHEN** a village has two stations, one with twice the lift capacity of the other
- **THEN** two-thirds of its commuters set off from the bigger one

### Requirement: Three ability groups
Commuters and people going home SHALL be split into ability groups, each with its own sense of how slow each grade feels:

| Group | Share | Red | Black |
|---|---|---|---|
| Cautious | 30% | ×2.0 | ×6.0 |
| Intermediate | 50% | ×1.3 | ×2.5 |
| Strong | 20% | ×1.0 | ×1.1 |

Blacks SHALL be scaled by committed length, as in busyness-laps. Each group SHALL choose destinations and routes separately.

#### Scenario: A long black against a slower blue route
- **WHEN** the quickest route uses a long black and a route 50% slower uses blues
- **THEN** cautious skiers take the blues
- **AND** strong skiers take the black

### Requirement: Routes vary
Routes SHALL be averaged over 30 draws (`DRAWS`), each varying every link's time by about ±30% (`NOISE`). Run times SHALL also be scaled by gradient: near-flat runs ×1.4, runs steeper than 45% on average ×1.3. The draws SHALL come from a seeded random sequence (`SEED`), so the same structure and parameters give the same result every time.

#### Scenario: Two nearly equal routes
- **WHEN** two routes take almost the same time
- **THEN** commuters use both, not just the quicker

#### Scenario: Running twice
- **WHEN** the engine runs twice on the same structure file in the same environment
- **THEN** both runs give identical traffic on every link

#### Scenario: Different browsers
- **WHEN** the engine runs on the same structure file in two different browsers
- **THEN** traffic on every link agrees to within 0.1%

### Requirement: End-of-day conditions
On the way home in the evening, reds SHALL feel ×1.2 and blacks ×1.6 harder (`EVENING_FEEL`), on top of each group's weights, for tired legs and worse snow. The black penalty SHALL apply in full to every black, whatever its committed length: a way out makes a black less daunting to start, not easier at the end of the day.

#### Scenario: A long black at the end of the day
- **WHEN** an intermediate going home weighs a long black against a blue
- **THEN** the black feels 2.5 × 1.6 = 4× slower than it is

#### Scenario: A black crossed by easier runs at the end of the day
- **WHEN** an intermediate going home weighs a long black crossed by easier runs every 400 m
- **THEN** its ability weight is blended towards the red one by committed length
- **AND** it still feels the full ×1.6 end-of-day penalty

### Requirement: Skied-out runs
On the way home, a run SHALL feel up to 1.5× harder in proportion to its lapping traffic, reaching the maximum at 30 lapping skiers an hour per metre of width (`SKIED_OUT_MAX`, `SKIED_OUT_REF`).

#### Scenario: A heavily lapped run beside a quiet one
- **WHEN** one run has been heavily lapped all day and a parallel run hasn't
- **THEN** in the evening the quiet run is chosen more than its daytime share suggests

### Requirement: Able skiers go faster on easy runs
On the way home, greens SHALL take intermediates 0.6× and strong skiers 0.5× of the grade's typical time (`EASY_PACE`), which is a beginner's.

#### Scenario: A long green home
- **WHEN** an intermediate considers a long green home
- **THEN** it takes them 0.6× the beginner time

### Requirement: Riding down, up to capacity
Riding an enclosed lift down SHALL feel ×1 to cautious skiers, ×4 to intermediates and ×5 to strong skiers (`DOWNLOAD_FEEL`). No lift SHALL carry more than its capacity down: an overfull ride SHALL feel slower and everyone SHALL be routed again, up to three times (`DOWNLOAD_PASSES`).

#### Scenario: Too many riding down
- **WHEN** more people want to ride a gondola down than its capacity
- **THEN** the excess skis home instead
