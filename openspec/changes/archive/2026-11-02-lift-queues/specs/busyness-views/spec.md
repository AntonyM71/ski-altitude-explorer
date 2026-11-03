# Spec Delta

## MODIFIED Requirements

### Requirement: Busyness is a relative index
Results SHALL be presented as a relative index for ranking runs and lifts within a domain, not as counts of people. A lift's wait SHALL be presented as a modelled wait in minutes, an indication rather than a measured queue.

#### Scenario: Comparing two runs
- **WHEN** one run shows 1,200 an hour and another 600
- **THEN** the first is read as about twice as busy, not as carrying exactly 1,200 people

#### Scenario: A lift's wait
- **WHEN** a lift shows a modelled wait of 8 minutes
- **THEN** it's read as one of the domain's queues, not as a forecast of the wait on a given day

### Requirement: Lifts are reported against capacity
Each lift SHALL be reported as demand ÷ capacity for each view, with its modelled wait in minutes (busyness-queues). In the evening, people riding down SHALL count towards it and SHALL be reported separately.

#### Scenario: A queue
- **WHEN** a lift's morning demand is 1.5× its capacity
- **THEN** it shows 1.5× and a modelled wait

#### Scenario: A lift with room
- **WHEN** a lift's day demand is 0.6× its capacity
- **THEN** it shows 0.6× and no wait beyond loading
