# busyness-laps Specification

## Purpose
Estimate where skiers who stay in their own area go: from each lift's top, down the runs, to the next lift. Rationale and examples: [decision 004](../../../docs/decisions/004-busyness-from-lift-capacity.md) and [decision 006](../../../docs/decisions/006-laps-flow.md).

## Requirements

### Requirement: Every lift runs at capacity
Each lift SHALL be assumed to carry its capacity: its recorded capacity or, where that's missing or implausible, the estimate from busyness-lift-estimates. The lift SHALL record which it is.

#### Scenario: A chairlift with no recorded capacity
- **WHEN** a chairlift has no capacity in the data but records its seats
- **THEN** it carries the estimate for its seats
- **AND** its capacity source is `seats`

### Requirement: Lapping skiers leave each lift's top
Each lift's top SHALL send skiers down at its capacity, less its sector's commuting share (see busyness-commuting). Nursery lifts SHALL send none. Where several lifts share a top station, the skiers they send SHALL add up.

#### Scenario: A lift in a sector with 40% commuting
- **WHEN** a 2,000-an-hour chairlift is in a sector whose commuting share is 40%
- **THEN** 1,200 an hour of lapping skiers leave its top

#### Scenario: Two lifts sharing a top station
- **WHEN** two 2,000-an-hour chairlifts in a sector with no commuting arrive at the same top station
- **THEN** 4,000 an hour of lapping skiers leave that station

### Requirement: Skiers split at junctions by pull
At each junction, skiers SHALL divide between the options in proportion to each option's pull:
- a lift: its capacity ÷ 800 (`LIFT_PULL`), divided by its queue factor (busyness-queues);
- a run: its grade's weight (`GRADE_PULL`: green and blue 1.0, red 0.8, black 0.4, ungraded 0.7) × its gradient factor (average under 6% ×0.35, under 10% ×0.7, over 45% ×0.6), divided by the queue factor of the lifts it leads to (busyness-queues);
- a walking link: the pull of the best run or lift it leads to, or 1 if it leads to neither;
- a nursery lift or slope, or a ride down: none.

Skiers SHALL keep skiing down until a lift takes them.

#### Scenario: A big lift beside two runs
- **WHEN** a junction offers a 2,000-an-hour chairlift with no queue and two blue runs of ordinary gradient whose lifts have no queues
- **THEN** the chairlift takes 2.5 / 4.5 of the skiers and each run 1 / 4.5

#### Scenario: The same lift with a queue
- **WHEN** the chairlift has a 10-minute queue
- **THEN** its pull halves to 1.25, and it takes 1.25 / 3.25 of the skiers

#### Scenario: A run that ends at a queue
- **WHEN** one of the two blue runs leads only to a lift with a 10-minute queue
- **THEN** that run's pull halves to 0.5

#### Scenario: A walk to a nearby lift
- **WHEN** a 2,500-an-hour gondola's bottom offers the gondola and a walk to a 1,500-an-hour funicular's bottom, neither with a queue
- **THEN** the gondola takes 3.125 / (3.125 + 1.875) of the skiers there, and the walk the rest

#### Scenario: A near-flat run
- **WHEN** a run averages under 6% gradient
- **THEN** its pull is 0.35 of a normal run of its grade

### Requirement: Skiers favour higher areas by day
In the day laps, a lift's pull SHALL be multiplied by its altitude factor, `ALT_RATIO` ^ (h − 0.5), where h is the height of its bottom station within the domain's range of lift bottoms (0 lowest, 1 highest) and `ALT_RATIO` = 2. A run's pull SHALL be multiplied by the pull-weighted average altitude factor of the lifts its skiers go on to reach. The factor SHALL NOT apply to the rushes or to finding sectors.

#### Scenario: Two equal lifts at different heights
- **WHEN** a junction offers two 2,000-an-hour chairlifts, one at the domain's highest lift bottom and one at its lowest
- **THEN** the higher takes 2 / 3 of the lifts' share of skiers, and the lower 1 / 3

#### Scenario: Two runs to lifts at different heights
- **WHEN** a junction offers two equal blue runs, one leading only to the domain's highest lift bottom and the other only to its lowest
- **THEN** the run to the higher lift takes 2 / 3 of the skiers

#### Scenario: A low resort
- **WHEN** a domain's lift bottoms range from 600 m to 1,200 m
- **THEN** a lift starting at 1,200 m has the highest factor, as a lift starting at 3,000 m does in a domain whose lift bottoms top out there

#### Scenario: Sectors are unchanged
- **WHEN** sectors are found for a domain
- **THEN** they use pulls without the altitude factor

### Requirement: Short blacks count more like reds
A black's grade weight SHALL depend on its committed length: the black skied from its top before the next way out (an easier run, a lift or a walk), taking the shortest. Up to 300 m (`BLACK_SHORT_M`) it SHALL take the red weight. From 1,000 m (`BLACK_LONG_M`) it SHALL take the black weight. In between, it SHALL blend linearly. The rule SHALL apply to the lap pull and to each ability group's route weights, but NOT to end-of-day conditions (see busyness-commuting).

#### Scenario: A short black with a way out
- **WHEN** a black reaches a junction with an easier run 250 m from its top
- **THEN** it takes the red weight

#### Scenario: A black part-way between
- **WHEN** a black's committed length is 650 m
- **THEN** its weight is halfway between the red and black weights

#### Scenario: A long black with no way out
- **WHEN** a black has 1,200 m from its top before any way out
- **THEN** it takes the full black weight

#### Scenario: A short black at the end of the day
- **WHEN** a skier going home weighs a black whose committed length is 250 m
- **THEN** its ability weight is the red one
- **AND** its end-of-day penalty is the full black one

### Requirement: Flat runs are slow
A run's speed SHALL be its grade's typical speed scaled by its average gradient: under 4% ×0.4, under 8% ×0.6, under 12% ×0.85.

#### Scenario: A very flat run
- **WHEN** a blue run averages 3%
- **THEN** it is skied at 40% of the blue speed
