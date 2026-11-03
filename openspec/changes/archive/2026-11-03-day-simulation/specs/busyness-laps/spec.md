# Spec Delta

## MODIFIED Requirements

### Requirement: Every lift runs at capacity
Each lift SHALL carry up to its capacity: its recorded capacity or, where that's missing or implausible, the estimate from busyness-lift-estimates. It SHALL carry only the skiers who reach it (busyness-day-simulation), so a lift may run below capacity. The lift SHALL record which capacity it uses.

#### Scenario: A chairlift with no recorded capacity
- **WHEN** a chairlift has no capacity in the data but records its seats
- **THEN** it carries up to the estimate for its seats
- **AND** its capacity source is `seats`

#### Scenario: A lift few skiers reach
- **WHEN** 300 skiers an hour reach a 2,000-an-hour chairlift
- **THEN** it carries 300 an hour, 15% of its capacity

### Requirement: Skiers split at junctions by pull
At each junction, skiers SHALL divide between the options in proportion to each option's pull:
- a lift: its capacity ÷ 800 (`LIFT_PULL`), divided by its queue factor (busyness-queues);
- a run: the pull of the lifts it leads to, averaged by how many skiers reach each, times how pleasant the way there is: the lower of the run's own weight and the easiest way on beyond it. A run's own weight is its grade's weight (`GRADE_PULL`: green and blue 1.0, red 0.8, black 0.4, ungraded 0.7) × its gradient factor (average under 6% ×0.35, under 10% ×0.7, over 45% ×0.6). A run that leads to no lift takes the domain's typical lift pull;
- a walking link: as a run of weight 1, or of the near-flat weight (0.35) where it climbs;
- a nursery lift or slope: as a lift or run, times 0.05 (`NURSERY_PULL`), a last resort;
- a ride down: none.

Skiers SHALL keep skiing down until a lift takes them.

#### Scenario: A big lift beside two runs
- **WHEN** a junction offers a 2,000-an-hour chairlift with no queue and two blue runs of ordinary gradient, each leading only to another 2,000-an-hour chairlift with no queue
- **THEN** each run pulls as much as the chairlift at hand, 2.5, and each option takes a third of the skiers

#### Scenario: The same lift with a queue
- **WHEN** the chairlift at hand has a 10-minute queue
- **THEN** its pull halves to 1.25, and it takes 1.25 / 6.25 of the skiers

#### Scenario: A run that ends at a queue
- **WHEN** one of the two blue runs leads only to a lift with a 10-minute queue
- **THEN** that run's pull halves to 1.25

#### Scenario: A bigger lift a short run away
- **WHEN** a junction offers a 1,600-an-hour chairlift and a short blue run leading only to a 4,000-an-hour chairlift, neither with a queue
- **THEN** the run pulls 5.0 against the chairlift's 2.0, and takes 5 / 7 of the skiers

#### Scenario: A long black on the only way to a big lift
- **WHEN** the run to the 4,000-an-hour chairlift is a long black (weight 0.4) instead
- **THEN** it pulls 2.0, the same as the 1,600-an-hour chairlift at hand

#### Scenario: A black beside an easier way
- **WHEN** a blue run leads to a junction from which both a long black and a blue lead on to the same lift
- **THEN** the blue run counts as fully pleasant: the black doesn't lower its pull

#### Scenario: A walk to a nearby lift
- **WHEN** a 2,500-an-hour gondola's bottom offers the gondola and a level walk to a 1,500-an-hour funicular's bottom, neither with a queue
- **THEN** the gondola takes 3.125 / (3.125 + 1.875) of the skiers there, and the walk the rest

#### Scenario: A walk uphill
- **WHEN** the walk to the funicular climbs
- **THEN** it pulls 0.35 × 1.875

#### Scenario: A near-flat run
- **WHEN** a run averages under 6% gradient
- **THEN** its weight is 0.35 of a normal run of its grade

### Requirement: Skiers favour higher areas by day
A lift's pull for lapping skiers SHALL be multiplied by its altitude factor, `ALT_RATIO` ^ (h − 0.5), where h is the height of its bottom station within the domain's range of lift bottoms (0 lowest, 1 highest) and `ALT_RATIO` = 2. Runs SHALL carry the factor through the pull of the lifts they lead to. The factor SHALL NOT apply to routes or to finding sectors.

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

## REMOVED Requirements

### Requirement: Lapping skiers leave each lift's top
**Reason**: Lift tops released a fixed share of capacity whether or not anyone rode the lift, so skiers weren't conserved: every lift looked about half full, and areas skiers left were never refilled.
**Migration**: Skiers come off a lift's top only after riding it, in the simulated day (busyness-day-simulation: Skiers are conserved, Lifts load from their queue).
