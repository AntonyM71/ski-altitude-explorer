# busyness-views Specification

## Purpose
Combine laps and commuting into views by time of day, write them out, and show them on a review map. Rationale: [decision 004](../../../docs/decisions/004-busyness-from-lift-capacity.md) and [decision 010](../../../docs/decisions/010-time-of-day-views.md).

## Requirements

### Requirement: Busyness is a relative index
Results SHALL be presented as a relative index for ranking runs and lifts within a domain, not as counts of people. A lift's wait SHALL be presented as a modelled wait in minutes, an indication rather than a measured queue.

#### Scenario: Comparing two runs
- **WHEN** one run shows 1,200 an hour and another 600
- **THEN** the first is read as about twice as busy, not as carrying exactly 1,200 people

#### Scenario: A lift's wait
- **WHEN** a lift shows a modelled wait of 8 minutes
- **THEN** it's read as one of the domain's queues, not as a forecast of the wait on a given day

### Requirement: Day average view
The model SHALL produce a day view per hour: each link's traffic averaged over the settled middle of the simulated day, 11:00–14:30 (`DAY_FROM_H`, `DAY_TO_H`), counting laps and commuters alike.

#### Scenario: Commuters over a run
- **WHEN** commuters cross a run on their way out at 09:30 and home at 15:30
- **THEN** they count in the morning and evening views, not the day view

#### Scenario: A run lapped all day
- **WHEN** 600 skiers an hour ski a run between 11:00 and 14:30
- **THEN** its day view is 600 an hour

### Requirement: Morning rush view
The model SHALL produce a morning rush per hour: each link's traffic averaged over 09:00–10:30 of the simulated day (`START_H`, `MORNING_TO_H`), as everyone leaves their village and the first laps begin.

#### Scenario: A village lift at the start of the day
- **WHEN** a village's skiers appear at its station over 09:00–10:00
- **THEN** its lifts carry them, up to capacity, with a queue for the rest

### Requirement: Evening rush view
The model SHALL produce an evening rush per hour: each link's traffic averaged over 15:00–16:30 of the simulated day (`HOME_H`, `EVENING_TO_H`), as everyone heads home from wherever they are.

#### Scenario: A run busy only at the end of the day
- **WHEN** a run is the way home for a village but rarely lapped
- **THEN** it ranks low in the day view and high in the evening view

### Requirement: Lifts are reported against capacity
Each lift SHALL be reported for each view as the skiers it boarded an hour ÷ its capacity, plus its demand: boarded plus the growth of its queue, ÷ capacity. Its modelled wait SHALL be its average wait over the view's window (busyness-queues). In the evening, people riding down SHALL count towards it and SHALL be reported separately.

#### Scenario: A queue
- **WHEN** a lift boards at capacity through the morning window while its queue grows
- **THEN** it shows demand over 1.0× and its average wait

#### Scenario: A lift with room
- **WHEN** a lift boards 0.6× its capacity through the day window with no queue
- **THEN** it shows 0.6× and no wait beyond loading

### Requirement: Results files
The pipeline SHALL write one structure file per modelled domain (see busyness-pipeline), and the engine SHALL compute every view from it: for each link and lift, its traffic per hour in the day average, morning rush and evening rush, demand ÷ capacity for lifts, and riding down in the evening. Results SHALL NOT be stored per domain; anything that needs them, including tests, runs the engine.

#### Scenario: Running a domain
- **WHEN** the engine is given a domain's structure file
- **THEN** it returns every link's and lift's traffic for the three views

#### Scenario: Checking a domain from the command line
- **WHEN** the engine's command-line runner is given a structure file
- **THEN** it prints the domain's busiest runs and lifts for each view

### Requirement: Review map
`prototypes/busyness_review.html?d=<domain id>` SHALL load a domain's structure file, run the engine, and show the domain's runs coloured by skiers an hour and its lifts by demand ÷ capacity, with day, morning and evening views, lists of the busiest runs and lifts and the quietest named runs, and details on hover.

#### Scenario: No results for the domain
- **WHEN** the page is opened with a domain id that has no structure file
- **THEN** it says so and shows the command to produce one
