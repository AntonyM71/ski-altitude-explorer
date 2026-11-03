# Spec Delta

## ADDED Requirements

### Requirement: Skiers favour higher areas by day
In the day laps, a lift's pull SHALL be multiplied by its altitude factor, `ALT_RATIO` ^ (h − 0.5), where h is the height of its bottom station within the domain's range of lift bottoms (0 lowest, 1 highest) and `ALT_RATIO` = 2. A run's pull SHALL be multiplied by the pull-weighted average altitude factor of the lifts its skiers go on to reach. The factor SHALL NOT apply to the rushes or to finding sectors.

#### Scenario: Two equal lifts at different heights
- **WHEN** a junction offers two 2,000-an-hour chairlifts, one at the domain's highest lift bottom and one at its lowest
- **THEN** the higher takes 2 / 3 of the lifts' share of skiers, and the lower 1 / 3

#### Scenario: Two runs to lifts at different heights
- **WHEN** a junction offers two equal blue runs, one leading only to the domain's highest lift bottom and the other only to its lowest
- **THEN** the run to the higher lift takes 2 / 3 of the skiers

#### Scenario: A low resort
- **WHEN** a domain's lift bottoms range from 600 m to 1,200 m
- **THEN** a lift starting at 1,200 m has the highest factor, as a lift starting at 3,000 m does in a domain whose lift bottoms top out there

#### Scenario: Sectors are unchanged
- **WHEN** sectors are found for a domain
- **THEN** they use pulls without the altitude factor
