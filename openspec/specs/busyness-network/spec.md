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
A lift's top SHALL link to every run starting within 150 m (`LIFT_TOP_M`) and between 150 m below and 30 m above it. Every run ending within 100 m (`LIFT_BOTTOM_M`) and between 30 m below and 60 m above a lift's bottom SHALL link to it. Each walking link SHALL take 30 s (`WALK_S`).

#### Scenario: A run starting just below a lift's top
- **WHEN** a run starts 120 m from a lift's top and 40 m lower
- **THEN** skiers can walk from the lift's top to the run, in 30 s

### Requirement: Enclosed lifts can be ridden down in the evening
Gondolas, cable cars, funiculars and mixed lifts SHALL also have a downhill link, taking the ride time plus queueing. It SHALL be usable only on the way home in the evening, never for laps or in the morning.

#### Scenario: At the top of a gondola
- **WHEN** a skier going home and a lapping skier are both at a gondola's top
- **THEN** riding it down is an option for the skier going home
- **AND** never for the lapping skier

### Requirement: Nursery areas are links only
Magic carpets, rope tows and drag lifts shorter than 300 m SHALL be nursery lifts. Green runs shorter than 400 m that end within 100 m of a nursery lift's bottom SHALL be nursery slopes. Nursery lifts and slopes SHALL stay in the network for skiers passing through, but SHALL have no pull for laps and SHALL NOT count as village lifts.

#### Scenario: A magic carpet that's the only way up
- **WHEN** a magic carpet is the only way from one area back up to another
- **THEN** commuters and people going home can still use it
- **AND** lapping skiers don't choose it
