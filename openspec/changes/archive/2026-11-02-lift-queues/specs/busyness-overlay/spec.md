# Spec Delta

## MODIFIED Requirements

### Requirement: Lifts shown by load against capacity
Each lift SHALL be coloured in four fixed bands for the current view: under 50% of capacity, 50–100% with no queue, a modelled queue under 5 minutes, and a queue of 5 minutes or more (`LIFT_LOAD_BANDS` = 0.5, 1.0; `LIFT_WAIT_BANDS_MIN` = 5). A queue SHALL mean a wait beyond the fixed loading time (busyness-queues). The bands SHALL be the same in every domain. Lifts SHALL use a colour scale of one hue, light to dark, distinct from the runs' colours, and the legend SHALL show the two scales separately. Nursery lifts SHALL have no load colour.

#### Scenario: A quiet domain
- **WHEN** every lift in a domain is modelled under half full
- **THEN** every lift is shown in the lightest band, and none in a queue band

#### Scenario: A lift over capacity
- **WHEN** a lift's modelled demand in the current view is 1.2× its capacity
- **THEN** it has a modelled queue, and is shown in one of the two queue bands by its wait

#### Scenario: A lift with a long queue
- **WHEN** a lift's modelled wait in the current view is 8 minutes beyond loading
- **THEN** it's shown in the darkest band

#### Scenario: A full lift with a short queue
- **WHEN** a lift is at capacity with a modelled wait of 3 minutes beyond loading
- **THEN** it's shown in the third band

#### Scenario: A lift and a run side by side
- **WHEN** a lift in the darkest band runs beside a run in the busiest band
- **THEN** they are drawn in different hues, and the legend names each scale

#### Scenario: A lift mapped in pieces
- **WHEN** a lift is mapped as several lines
- **THEN** it's shown in the band of its most loaded piece

#### Scenario: A nursery lift
- **WHEN** the overlay is on and a domain has a magic carpet
- **THEN** the magic carpet is drawn without a load colour

### Requirement: Presented as an experimental relative index
The overlay SHALL be labelled as an experimental model, not a measure of crowds, and SHALL NOT show skier numbers as counts of people. Details on hover SHALL give a run's band within the domain, and a lift's modelled load as a percentage of its capacity or, where it has a queue, its modelled wait in minutes, labelled as modelled. They SHALL NOT compare a run or lift with other domains.

#### Scenario: Hovering over a run
- **WHEN** a visitor hovers over a run with the overlay on
- **THEN** the run's name and band are shown, with no count of people

#### Scenario: Hovering over a lift over capacity
- **WHEN** a visitor hovers over a lift whose modelled morning demand is 1.4× its capacity, in the morning view, so its modelled wait is 18 minutes
- **THEN** the lift is described as having a modelled queue of about 18 minutes
- **AND** no count of people is shown

#### Scenario: Hovering over a lift with room
- **WHEN** a visitor hovers over a lift at 60% of capacity with no queue
- **THEN** the lift is described as modelled at 60% of capacity
