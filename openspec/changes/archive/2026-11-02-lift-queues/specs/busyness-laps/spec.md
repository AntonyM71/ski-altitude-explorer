# Spec Delta

## MODIFIED Requirements

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
