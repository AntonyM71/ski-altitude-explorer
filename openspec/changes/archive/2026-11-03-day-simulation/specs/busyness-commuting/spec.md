# Spec Delta

## MODIFIED Requirements

### Requirement: Trips start and end where people are
Outbound trips SHALL start from each of the village's stations in proportion to the lifts leaving it, during the morning (busyness-day-simulation), and SHALL end at the first of the destination sector's lift bottoms the route reaches, from where the commuter laps. The trip home SHALL start at 15:00 from wherever the skier is, and SHALL end at the nearest of their village's stations.

#### Scenario: A village with two stations
- **WHEN** a village has two stations, one with twice the lift capacity of the other
- **THEN** two-thirds of its commuters set off from the bigger one

#### Scenario: Going home from where they are
- **WHEN** a commuter is lapping in their destination sector at 15:00
- **THEN** their trip home starts from the junction they're at

### Requirement: Routes vary
Routes SHALL be varied over `DRAWS` draws, each varying every link's time by about ±30% (`NOISE`), with the skiers on a route shared evenly between the draws. Run times SHALL also be scaled by gradient: near-flat runs ×1.4, runs steeper than 45% on average ×1.3. A lift's time SHALL include its current wait when the routes are worked out (busyness-queues). The draws SHALL come from a seeded random sequence (`SEED`), so the same structure and parameters give the same result every time.

#### Scenario: Two nearly equal routes
- **WHEN** two routes take almost the same time
- **THEN** commuters use both, not just the quicker

#### Scenario: A queue on the way
- **WHEN** a route's lift has a 15-minute queue when routes are worked out
- **THEN** that route takes 15 minutes longer for commuters routed then

#### Scenario: Running twice
- **WHEN** the engine runs twice on the same structure file in the same environment
- **THEN** both runs give identical traffic on every link

#### Scenario: Different browsers
- **WHEN** the engine runs on the same structure file in two different browsers
- **THEN** traffic on every link agrees to within 0.1%

### Requirement: Riding down, up to capacity
Riding an enclosed lift down SHALL feel ×1 to cautious skiers, ×4 to intermediates and ×5 to strong skiers (`DOWNLOAD_FEEL`). A lift SHALL carry no more than its capacity down: skiers riding down SHALL queue at its top like skiers at a bottom (busyness-queues), and the queue's wait SHALL count in their route time when routes are worked out again.

#### Scenario: Too many riding down
- **WHEN** more people want to ride a gondola down than its capacity
- **THEN** a queue builds at its top, and once it's long enough that skiing home is quicker, newly routed skiers ski home instead
