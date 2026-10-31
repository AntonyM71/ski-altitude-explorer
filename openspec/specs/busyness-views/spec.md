# busyness-views Specification

## Purpose
Combine laps and commuting into views by time of day, write them out, and show them on a review map. Rationale: [decision 004](../../../docs/decisions/004-busyness-from-lift-capacity.md) and [decision 010](../../../docs/decisions/010-time-of-day-views.md).

## Requirements

### Requirement: Busyness is a relative index
Results SHALL be presented as a relative index for ranking runs and lifts within a domain, not as counts of people.

#### Scenario: Comparing two runs
- **WHEN** one run shows 1,200 an hour and another 600
- **THEN** the first is read as about twice as busy, not as carrying exactly 1,200 people

### Requirement: Day average view
The model SHALL produce a day average per hour: laps plus each commuter's outbound and return trip, spread over 6 hours (`DAY_HOURS`).

#### Scenario: Commuters over a run
- **WHEN** 600 commuters cross a run on their way out and back again on their way home
- **THEN** the run's day average includes 1,200 trips ÷ 6 hours = 200 an hour from them

### Requirement: Morning rush view
The model SHALL produce a morning rush per hour: everyone leaves their village within 1.5 hours (`PEAK_HOURS`). Locals ride the village lifts by capacity, commuters take their outbound route, and laps already under way are added at 40% (`RAMP`).

#### Scenario: A village lift at the start of the day
- **WHEN** a village's locals set off
- **THEN** they load its lifts in proportion to each lift's capacity

### Requirement: Evening rush view
The model SHALL produce an evening rush per hour: everyone goes home within 1.5 hours, back to where they set off. Locals SHALL set off from the sectors their village's lifts took them to, commuters from the sector they visited. Laps are added at 40%.

#### Scenario: A run busy only at the end of the day
- **WHEN** a run is the way home for a village but rarely lapped
- **THEN** it ranks low in the day view and high in the evening view

### Requirement: Lifts are reported against capacity
Each lift SHALL be reported as demand ÷ capacity for each view. In the evening, people riding down SHALL count towards it and SHALL be reported separately.

#### Scenario: A queue
- **WHEN** a lift's morning demand is 1.5× its capacity
- **THEN** it shows 1.5×, meaning a queue

### Requirement: Results files
Each run SHALL write `data/busyness/<slug>/busy.geojson`, with every run piece and lift and its values for each view, and `summary.json`. A black run piece SHALL include its committed length.

#### Scenario: Running a domain
- **WHEN** `uv run --group busyness python prototypes/busyness.py "<ski area>"` finishes
- **THEN** `busy.geojson` and `summary.json` exist in `data/busyness/<slug>/`, where the slug is the domain's name in lower case with hyphens

### Requirement: Review map
`prototypes/busyness_review.html?d=<slug>` SHALL show the domain's runs coloured by skiers an hour and its lifts by demand ÷ capacity, with day, morning and evening views, lists of the busiest runs and lifts and the quietest named runs, and details on hover.

#### Scenario: No results for the domain
- **WHEN** the page is opened with a slug that has no results
- **THEN** it says so and shows the command to produce them
