# busyness-network Specification

## Purpose
Build the network that skiers move through: runs downhill, lifts uphill, and the junctions, walks and rides down that connect them. Every other part of the busyness model traces skiers over this network. Rationale and examples: [decision 005](../../../docs/decisions/005-busyness-network.md).

## Requirements

### Requirement: Runs and lifts become directed links
The model SHALL represent each run as links pointing downhill and each lift as one link pointing uphill, using the altitude at each end. A run SHALL be cut into links at every junction along it. A lift SHALL connect to the network only at its ends.

#### Scenario: A run drawn uphill
- **WHEN** a run's line starts lower than it ends
- **THEN** its links point from the higher end to the lower end

#### Scenario: A run passing under a lift
- **WHEN** a run passes beneath a lift's line, away from its stations
- **THEN** the run and the lift are not connected there

### Requirement: Line ends join nearby lines
A run's end SHALL join the nearest point of any other run within 40 m (`SNAP_M`), and that point SHALL cut the other run. A lift's end SHALL join any run passing within 100 m (`LIFT_STATION_M`).

#### Scenario: A run ending beside another
- **WHEN** a run ends 30 m from the middle of another run
- **THEN** the second run is cut there, and skiers can pass from the first to the second

#### Scenario: A lift station beside a run
- **WHEN** a run passes 80 m from a lift's top
- **THEN** the lift's top joins that run

### Requirement: Runs join where they cross
Where two runs cross mid-way, the model SHALL add a junction on both at the crossing, so skiers can switch between them. Crossings within 40 m of either line's end SHALL be left to the end joins. A crossing at a point shared by two segments SHALL count once.

#### Scenario: Two runs crossing in an X
- **WHEN** an easier run crosses a harder run part-way down both
- **THEN** both runs are cut at the crossing, and skiers on either can switch to the other there

### Requirement: Very short pieces don't break runs apart
A piece of run shorter than 1 m (two cuts at one place) SHALL be dropped, and its two ends SHALL become one junction, so the run stays connected.

#### Scenario: Two cuts at one place
- **WHEN** two crossings fall at the same place on a run
- **THEN** the run continues through that place, with no dead end

### Requirement: Walking links at lift stations
A lift's top SHALL link to every run starting within 150 m (`LIFT_TOP_M`) and between 150 m below and 30 m above it. Every run ending within 100 m (`LIFT_BOTTOM_M`) and between 30 m below and 60 m above a lift's bottom SHALL link to it. Each of these walking links SHALL take 30 s (`WALK_S`). A lift's top or bottom SHALL also link to another lift's bottom within 250 m (`LIFT_WALK_M`) and 30 m of height (`LIFT_WALK_RISE_M`), where runs and walks don't already lead from one to the other. These links take their distance ÷ 1 m/s (`WALK_SPEED`), and at least `WALK_S`. No walking link SHALL lead to a lift's top.

#### Scenario: A run starting just below a lift's top
- **WHEN** a run starts 120 m from a lift's top and 40 m lower
- **THEN** skiers can walk from the lift's top to the run, in 30 s

#### Scenario: Two lift bottoms a short walk apart
- **WHEN** two lifts' bottom stations are 184 m apart and 15 m different in height, with no run between them
- **THEN** skiers can walk between them either way, in about 3 minutes

#### Scenario: A lift's top near another lift's bottom
- **WHEN** a lift's top is 161 m from another lift's bottom and 6 m lower, with no run between them
- **THEN** skiers can walk from the top to the other lift's bottom, but not the other way

#### Scenario: A run already joins them
- **WHEN** a lift's top is 200 m from another lift's bottom, and a run leads from one to the other
- **THEN** no walking link is added: skiers ski it

#### Scenario: Lift bottoms too far apart
- **WHEN** two lifts' bottom stations are 300 m apart
- **THEN** they aren't linked

### Requirement: Enclosed lifts can be ridden down in the evening
Gondolas, cable cars, funiculars and mixed lifts SHALL also have a downhill link, taking the ride time plus queueing. It SHALL be usable only on the way home in the evening, never for laps or in the morning.

#### Scenario: At the top of a gondola
- **WHEN** a skier going home and a lapping skier are both at a gondola's top
- **THEN** riding it down is an option for the skier going home
- **AND** never for the lapping skier

### Requirement: Nursery areas are links only
Magic carpets, rope tows and drag lifts shorter than 300 m SHALL be nursery lifts. Green runs shorter than 400 m that end within 100 m of a nursery lift's bottom SHALL be nursery slopes, unless they start at a junction that is a non-nursery lift's station (a way on between lifts). Nursery lifts and slopes SHALL stay in the network. Lapping skiers SHALL take them only as a last resort: their pull SHALL be 0.05 of an ordinary lift's or slope's (`NURSERY_PULL`, busyness-laps). They SHALL NOT count as village lifts.

#### Scenario: A short green from a lift's station past a nursery area
- **WHEN** a short green starts at a chairlift's bottom station and ends beside a magic carpet's bottom
- **THEN** it isn't a nursery slope, and lapping skiers can take it

#### Scenario: A magic carpet that's the only way up
- **WHEN** a magic carpet is the only way from one area back up to another
- **THEN** commuters, people going home and lapping skiers can all use it

#### Scenario: A nursery slope beside an ordinary run
- **WHEN** a junction offers a nursery slope and an ordinary blue run to equal lifts
- **THEN** lapping skiers take the blue 20 times as often as the nursery slope

### Requirement: Dead ends walk to the nearest lift
A junction with no run, walk or lift leading on (rides down aside) SHALL get a walking link within 1,000 m (`DEAD_END_WALK_M`): from the end of a run to the nearest lift bottom, and from a lift's top to the nearest run start. It takes its distance ÷ 1 m/s (`WALK_SPEED`), and at least `WALK_S`. It's a backup for gaps in the map: where any other way on exists, no such walk SHALL be added.

#### Scenario: A run that stops short of the run it meets
- **WHEN** a run ends 300 m from a chairlift's bottom, with nothing mapped leading on
- **THEN** skiers there can walk to the chairlift in 5 minutes

#### Scenario: A lift's top with no run mapped from it
- **WHEN** a gondola's top is 400 m from the nearest run start, with only the ride down leading on
- **THEN** skiers there can walk to the run in about 7 minutes

#### Scenario: A junction with another way on
- **WHEN** a run ends at a junction from which a nursery slope leads on
- **THEN** no walk is added: the nursery slope is the way on

### Requirement: Islands are dropped
Runs and walks from which no lift bottom can be reached, by any links, SHALL be left out of the network, as islands too far from the rest of the domain to model.

#### Scenario: A run ending far from any lift
- **WHEN** a run ends 1,500 m from the nearest lift bottom, with nothing leading on
- **THEN** it and any runs that lead only to it are left out
