# Spec Delta

## MODIFIED Requirements

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
