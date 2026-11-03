# Spec Delta

## MODIFIED Requirements

### Requirement: Every lift runs at capacity
Each lift SHALL be assumed to carry its capacity: its recorded capacity or, where that's missing or implausible, the estimate from busyness-lift-estimates. The lift SHALL record which it is.

#### Scenario: A chairlift with no recorded capacity
- **WHEN** a chairlift has no capacity in the data but records its seats
- **THEN** it carries the estimate for its seats
- **AND** its capacity source is `seats`
