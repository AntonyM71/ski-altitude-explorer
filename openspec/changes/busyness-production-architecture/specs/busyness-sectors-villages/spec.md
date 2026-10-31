# Spec Delta

## MODIFIED Requirements

### Requirement: Sectors from how lifts exchange skiers
Sectors SHALL be found from the share of skiers leaving each lift's top who next ride each other lift, computed exactly from the network as a Markov chain (ways on weighted by pull, lifts ending the lap). Lifts that mostly exchange skiers among themselves SHALL be grouped (Louvain). A sector with under 4% of the domain's lift capacity (`SECTOR_MIN`) SHALL merge into the neighbour it exchanges most with. Nursery lifts SHALL take the sector of the nearest other lift.

#### Scenario: A small sector
- **WHEN** a group of lifts has 3% of the domain's capacity
- **THEN** it merges into the sector it passes most skiers to

#### Scenario: Exchange shares agree with laps
- **WHEN** the engine's laps are run from one lift's top alone on the same network
- **THEN** the share of those skiers reaching each lift matches the exact exchange share to within 0.1%

### Requirement: Villages come from OpenStreetMap places
Villages SHALL come from place points (towns, villages, hamlets and neighbourhoods) and building footprints in Overture Maps, at a pinned release (`OVERTURE_RELEASE`), cached by release. A lift station SHALL belong to the nearest place within 1 km (`PLACE_M`), if it's no more than 200 m above the place's lowest station (`VILLAGE_RISE_M`). A place SHALL be a village only if it has at least 50 buildings within 500 m (`PLACE_MIN_BUILDINGS`) and at least 500 an hour of non-nursery lifts leaving it.

#### Scenario: A thoroughfare
- **WHEN** a place has lift stations but fewer than 50 buildings within 500 m
- **THEN** it isn't a village

#### Scenario: A station high above the village
- **WHEN** a lift station is within 1 km of a place's point but more than 200 m above the village's lowest station
- **THEN** it doesn't belong to the village

#### Scenario: Squares and car parks aren't places
- **WHEN** Overture has a named square or car park (a microhood) near a lift station
- **THEN** it isn't treated as a place

#### Scenario: A neighbourhood with lifts
- **WHEN** a named neighbourhood has its own lift station and enough buildings, and no town, village or hamlet is within 1 km of the station
- **THEN** it can be a village in its own right

#### Scenario: A town mapped as many neighbourhoods
- **WHEN** a lift station is within 1 km of both a town's point and a nearer neighbourhood of it
- **THEN** the station belongs to the town
