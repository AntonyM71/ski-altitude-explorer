# busyness-queues Specification

## Purpose
Make lifts limit the flow of skiers: queues form where more skiers arrive than a lift releases, and lapping skiers and commuters avoid long queues, at the lift and before they reach it. Rationale: decision 015.

## Requirements

### Requirement: Waits from overload
In the day view, a lift whose lapping arrivals exceed what its top releases (its capacity less its sector's commuting share) SHALL have a wait. The wait SHALL grow until arrivals fall to what the lift releases, or stay wherever skiers have no other way on. A lift whose arrivals don't exceed what it releases SHALL have no wait beyond the fixed loading time (`WAIT_S`).

#### Scenario: A lift with an alternative beside it
- **WHEN** skiers at a junction can take either of two lifts, and one is overfull
- **THEN** its wait grows until enough skiers take the other that it's no longer overfull

#### Scenario: A lift with no alternative
- **WHEN** the only way on from a junction is a lift, and more skiers arrive than it releases
- **THEN** it keeps a queue

#### Scenario: A lift with room
- **WHEN** fewer lapping skiers arrive at a lift than it releases
- **THEN** it has no wait beyond the fixed loading time

### Requirement: Queues repel lapping skiers
A lift's pull at a junction SHALL be divided by its queue factor: 1 + its wait beyond the fixed loading time ÷ 10 minutes (`QUEUE_TOLERANCE_MIN`).

#### Scenario: Two equal lifts, one with a queue
- **WHEN** a junction offers two 2,000-an-hour chairlifts, one with a 10-minute queue and one with none
- **THEN** the one with the queue takes a third of the lifts' share of skiers, and the other two thirds

### Requirement: Queues are seen ahead
A run's pull SHALL also be divided by the queue factor of the lifts its skiers go on to reach, averaged by how many of them reach each. So skiers avoid a run that ends at a long queue before they reach it.

#### Scenario: Two runs to different lifts
- **WHEN** a junction offers two equal blue runs, one leading only to a lift with a 10-minute queue and the other only to a lift with none
- **THEN** the run to the queue takes a third of the skiers, and the other two thirds

### Requirement: Queues repel commuters
A lift's route time for commuters and people going home SHALL include its wait in the view being routed.

#### Scenario: A queue on the quick way
- **WHEN** the quickest route crosses a lift with a 15-minute queue, and another route is 10 minutes slower without it
- **THEN** most commuters take the other route

### Requirement: Queues in the rushes
In the morning and evening rushes, a lift whose demand exceeds its capacity SHALL have a queue that grows through the rush. Its wait SHALL be the average over the rush: (demand − capacity) × the rush's length (`PEAK_HOURS`) ÷ (2 × capacity), on top of the fixed loading time.

#### Scenario: A village lift at 1.4× in the morning
- **WHEN** a lift's morning demand is 1.4× its capacity over a 1.5-hour rush
- **THEN** its average wait is 0.4 × 1.5 ÷ 2 hours, 18 minutes, beyond the fixed loading time

### Requirement: Solved by iteration
Waits, pulls, routes and flows SHALL be iterated until no wait changes by more than 30 seconds, for at most 30 passes (`QUEUE_PASSES`). Each pass's routes SHALL be averaged with all the passes before it (the method of successive averages), so commuters settle where none would gain by switching. The result SHALL be the same every time the engine runs on the same structure and parameters.

#### Scenario: Commuters settle
- **WHEN** a queue on the quickest route sends every commuter to the other, so that the other route queues instead
- **THEN** the averaged routes split commuters between the two until their times are about equal, rather than flipping each pass

#### Scenario: Running twice
- **WHEN** the engine runs twice on the same structure file
- **THEN** every lift's wait and every link's traffic are identical
