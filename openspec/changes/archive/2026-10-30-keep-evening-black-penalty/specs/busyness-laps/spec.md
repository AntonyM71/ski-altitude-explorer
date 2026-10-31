# Spec Delta

## MODIFIED Requirements

### Requirement: Short blacks count more like reds
A black's grade weight SHALL depend on its committed length: the black skied from its top before the next way out (an easier run, a lift or a walk), taking the shortest. Up to 300 m (`BLACK_SHORT_M`) it SHALL take the red weight. From 1,000 m (`BLACK_LONG_M`) it SHALL take the black weight. In between, it SHALL blend linearly. The rule SHALL apply to the lap pull and to each ability group's route weights, but NOT to end-of-day conditions (see busyness-commuting).

#### Scenario: A short black with a way out
- **WHEN** a black reaches a junction with an easier run 250 m from its top
- **THEN** it takes the red weight

#### Scenario: A black part-way between
- **WHEN** a black's committed length is 650 m
- **THEN** its weight is halfway between the red and black weights

#### Scenario: A long black with no way out
- **WHEN** a black has 1,200 m from its top before any way out
- **THEN** it takes the full black weight

#### Scenario: A short black at the end of the day
- **WHEN** a skier going home weighs a black whose committed length is 250 m
- **THEN** its ability weight is the red one
- **AND** its end-of-day penalty is the full black one
