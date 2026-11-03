# Spec Delta

## ADDED Requirements

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

## MODIFIED Requirements

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
