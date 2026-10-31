# busyness-laps Specification

## Purpose
Estimate where skiers who stay in their own area go: from each lift's top, down the runs, to the next lift. Rationale and examples: [decision 004](../../../docs/decisions/004-busyness-from-lift-capacity.md) and [decision 006](../../../docs/decisions/006-laps-flow.md).

## Requirements

### Requirement: Every lift runs at capacity
Each lift SHALL be assumed to carry its recorded capacity. A missing capacity, or one under 100 or over 6,000 an hour, SHALL be replaced by a typical value for the lift type, and the lift SHALL be flagged as using a typical value.

#### Scenario: A chairlift with no recorded capacity
- **WHEN** a chairlift has no capacity in the data
- **THEN** it carries 2,000 an hour
- **AND** it is flagged as a typical value

### Requirement: Lapping skiers leave each lift's top
Each lift's top SHALL send skiers down at its capacity, less its sector's commuting share (see busyness-commuting). Nursery lifts SHALL send none.

#### Scenario: A lift in a sector with 40% commuting
- **WHEN** a 2,000-an-hour chairlift is in a sector whose commuting share is 40%
- **THEN** 1,200 an hour of lapping skiers leave its top

### Requirement: Skiers split at junctions by pull
At each junction, skiers SHALL divide between the options in proportion to each option's pull:
- a lift: its capacity ÷ 800 (`LIFT_PULL`);
- a run: its grade's weight (`GRADE_PULL`: green and blue 1.0, red 0.8, black 0.4, ungraded 0.7) × its gradient factor (average under 6% ×0.35, under 10% ×0.7, over 45% ×0.6);
- a walking link: the pull of the best run it leads to;
- a nursery lift or slope, or a ride down: none.

Skiers SHALL keep skiing down until a lift takes them.

#### Scenario: A big lift beside two runs
- **WHEN** a junction offers a 2,000-an-hour chairlift and two blue runs of ordinary gradient
- **THEN** the chairlift takes 2.5 / 4.5 of the skiers and each run 1 / 4.5

#### Scenario: A near-flat run
- **WHEN** a run averages under 6% gradient
- **THEN** its pull is 0.35 of a normal run of its grade

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
