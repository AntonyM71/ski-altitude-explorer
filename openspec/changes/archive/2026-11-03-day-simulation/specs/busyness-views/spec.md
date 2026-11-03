# Spec Delta

## MODIFIED Requirements

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
