# busyness-day-simulation Specification

## Purpose
Simulate a domain's ski day minute by minute, with every skier conserved, so lift loads, queues and run traffic come from where skiers actually are rather than from fixed releases at lift tops.

## Requirements

### Requirement: Skiers are conserved
The simulation SHALL track every skier from the time they leave their village until they are home. A lift SHALL let off at its top only skiers who rode it, and a run, walk or lift SHALL pass on exactly the skiers who entered it, after its travel time.

#### Scenario: A lift nobody reaches
- **WHEN** no skier ever arrives at a lift's bottom
- **THEN** the lift carries nobody and nobody comes off its top

#### Scenario: Counting skiers
- **WHEN** the simulation is at any minute of the day
- **THEN** the skiers at villages, waiting at lifts, riding and skiing add up to the domain's population

### Requirement: Lifts load from their queue
Each minute, a lift SHALL board the skiers waiting at its bottom, up to its capacity for the minute (capacity ÷ 60). Skiers who can't board SHALL wait, and are the lift's queue. Boarding SHALL be shared evenly across the skiers waiting, whoever they are.

#### Scenario: Fewer waiting than the lift can carry
- **WHEN** 10 skiers are waiting at a 1,200-an-hour chairlift
- **THEN** all 10 board that minute, and there is no queue

#### Scenario: More waiting than the lift can carry
- **WHEN** 50 skiers are waiting at a 1,200-an-hour chairlift
- **THEN** 20 board that minute and 30 stay in the queue

### Requirement: Travel takes time
A skier SHALL take a link's time to cross it: a lift's ride time, a run's time at its grade and gradient, or a walk's time. They SHALL reach the junction at its far end only then.

#### Scenario: A long run
- **WHEN** skiers set off down a run that takes 6 minutes
- **THEN** they reach its bottom 6 minutes later

### Requirement: Skiers leave their villages in the morning
Each village's skiers SHALL appear at its stations evenly over the hour from 09:00 (`START_H` = 9, `ARRIVE_MIN` = 60), in proportion to each station's lift capacity. Lapping locals SHALL then choose by pull, and commuters SHALL set off by route for their destination sector.

#### Scenario: A village with two stations
- **WHEN** a village has two stations, one with twice the lift capacity of the other
- **THEN** two-thirds of its skiers appear at the bigger one, spread evenly over 09:00–10:00

### Requirement: Skiers lap by pull
A skier who is lapping SHALL choose at each junction between its ways on in proportion to their pulls (busyness-laps), with each lift's current wait. A commuter who reaches their destination sector SHALL lap from there.

#### Scenario: Two ways on
- **WHEN** a lapping skier reaches a junction where a lift pulls 3 and a run pulls 1
- **THEN** three-quarters of the skiers there take the lift and a quarter the run

### Requirement: Everyone heads home at the end of the day
At 15:00 (`HOME_H` = 15), every skier still out SHALL stop lapping and head for their own village by route (busyness-commuting), from wherever they are. Skiers waiting at a lift SHALL stay in the queue if that lift is on their way home, and leave it otherwise.

#### Scenario: A skier far from home at 15:00
- **WHEN** a skier is in another sector at 15:00
- **THEN** they take the route home from where they are, including any lifts back over

#### Scenario: Home by the end of the evening
- **WHEN** the simulation reaches the end of the evening window
- **THEN** it reports the share of the population not yet home

### Requirement: Routes see the current queues
Routes for commuters and skiers heading home SHALL be worked out again at least every 15 minutes (`REROUTE_MIN` = 15), with each lift's current wait in its time.

#### Scenario: A queue builds on the quick way
- **WHEN** a lift on the quickest route builds a 20-minute queue
- **THEN** routes worked out after that take another way where one is quicker

### Requirement: The middle of the day settles
Between the morning and the evening, the simulation SHALL reach a settled state: each link's traffic over 11:00–12:45 and 12:45–14:30 SHALL agree to within 10% for links carrying at least 100 skiers an hour. The engine SHALL report the links that don't.

#### Scenario: A settled domain
- **WHEN** the simulation runs on a domain with no traps
- **THEN** busy links carry about the same traffic in the first and second halves of the day window

#### Scenario: A trap
- **WHEN** skiers can reach a group of lifts but not leave it
- **THEN** the queues there keep growing through the day, and the engine lists those lifts as unsettled

### Requirement: The same result every time
The simulation SHALL give the same result every time the engine runs on the same structure and parameters. Any random variation in routes SHALL come from the seeded sequence (`SEED`).

#### Scenario: Running twice
- **WHEN** the engine runs twice on the same structure file
- **THEN** every link's traffic and every lift's wait are identical
