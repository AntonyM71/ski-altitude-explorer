# Spec Delta

## MODIFIED Requirements

### Requirement: Lapping skiers leave each lift's top
Each lift's top SHALL send skiers down at its capacity, less its sector's commuting share (see busyness-commuting). Nursery lifts SHALL send none. Where several lifts share a top station, the skiers they send SHALL add up.

#### Scenario: A lift in a sector with 40% commuting
- **WHEN** a 2,000-an-hour chairlift is in a sector whose commuting share is 40%
- **THEN** 1,200 an hour of lapping skiers leave its top

#### Scenario: Two lifts sharing a top station
- **WHEN** two 2,000-an-hour chairlifts in a sector with no commuting arrive at the same top station
- **THEN** 4,000 an hour of lapping skiers leave that station
