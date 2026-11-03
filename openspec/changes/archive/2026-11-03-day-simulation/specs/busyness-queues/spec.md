# Spec Delta

## MODIFIED Requirements

### Requirement: Waits from overload
A lift's queue SHALL be the skiers waiting at its bottom (busyness-day-simulation), and its wait SHALL be the time to board them: the queue ÷ its capacity, on top of the fixed loading time (`WAIT_S`). A queue SHALL grow while more skiers arrive than the lift carries, and shrink when fewer do. A lift with room SHALL have no wait beyond loading.

#### Scenario: A lift with an alternative beside it
- **WHEN** skiers at a junction can take either of two lifts, and more arrive at one than it carries
- **THEN** its queue grows, it pulls less, and more skiers take the other until arrivals and boarding balance

#### Scenario: A lift with no alternative
- **WHEN** the only way on from a junction is a lift, and more skiers arrive than it carries
- **THEN** its queue grows until fewer skiers reach it, as skiers elsewhere avoid the runs that lead to it

#### Scenario: A lift with room
- **WHEN** fewer skiers arrive at a lift than its capacity
- **THEN** it has no wait beyond the fixed loading time

#### Scenario: Reading a wait
- **WHEN** 300 skiers are waiting at a 1,800-an-hour chairlift
- **THEN** its wait is 10 minutes beyond loading

### Requirement: Queues repel lapping skiers
A lift's pull at a junction SHALL be divided by its queue factor: 1 + its current wait beyond the fixed loading time ÷ 10 minutes (`QUEUE_TOLERANCE_MIN`).

#### Scenario: Two equal lifts, one with a queue
- **WHEN** a junction offers two 2,000-an-hour chairlifts, one with a 10-minute queue and one with none
- **THEN** the one with the queue takes a third of the lifts' share of skiers, and the other two thirds

### Requirement: Queues are seen ahead
A run's pull SHALL carry the queues of the lifts it leads to, through their pull (busyness-laps). So skiers avoid a run that ends at a long queue before they reach it.

#### Scenario: Two runs to different lifts
- **WHEN** a junction offers two equal blue runs, one leading only to a lift with a 10-minute queue and the other only to an equal lift with none
- **THEN** the run to the queue takes a third of the skiers, and the other two thirds

### Requirement: Queues repel commuters
A lift's route time for commuters and people going home SHALL include its current wait when their routes are worked out (busyness-day-simulation).

#### Scenario: A queue on the quick way
- **WHEN** the quickest route crosses a lift with a 15-minute queue, and another route is 10 minutes slower without it
- **THEN** commuters routed while the queue lasts take the other route

## REMOVED Requirements

### Requirement: Queues in the rushes
**Reason**: Rush queues came from a formula over demand that assumed fixed lift releases and a 40% ramp of laps. In the simulated day they're the skiers actually waiting.
**Migration**: Rush waits are the average wait over the rush windows of the simulated day (busyness-views).

### Requirement: Solved by iteration
**Reason**: Waits, routes and flows were iterated to a fixed point with averaged routes. The simulated day finds them by stepping through time instead.
**Migration**: busyness-day-simulation: Routes see the current queues, The middle of the day settles, The same result every time.
