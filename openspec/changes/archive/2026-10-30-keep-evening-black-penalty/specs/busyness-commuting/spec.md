# Spec Delta

## MODIFIED Requirements

### Requirement: End-of-day conditions
On the way home in the evening, reds SHALL feel ×1.2 and blacks ×1.6 harder (`EVENING_FEEL`), on top of each group's weights, for tired legs and worse snow. The black penalty SHALL apply in full to every black, whatever its committed length: a way out makes a black less daunting to start, not easier at the end of the day.

#### Scenario: A long black at the end of the day
- **WHEN** an intermediate going home weighs a long black against a blue
- **THEN** the black feels 2.5 × 1.6 = 4× slower than it is

#### Scenario: A black crossed by easier runs at the end of the day
- **WHEN** an intermediate going home weighs a long black crossed by easier runs every 400 m
- **THEN** its ability weight is blended towards the red one by committed length
- **AND** it still feels the full ×1.6 end-of-day penalty
