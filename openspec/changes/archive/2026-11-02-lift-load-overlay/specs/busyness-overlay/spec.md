# Spec Delta

## MODIFIED Requirements

### Requirement: Banded within the domain
Runs SHALL be coloured in bands by their rank among the same domain's runs: quiet, moderate, busy and busiest, split at the domain's 50th, 80th and 95th percentiles of length-weighted traffic (`BANDS`). Run colours SHALL NOT be comparable between domains. Lifts are shown by load instead (see "Lifts shown by load against capacity").

#### Scenario: Two domains of different sizes
- **WHEN** a small domain and a very large one are each shown with the overlay
- **THEN** each shows about the same share of its runs as busiest

#### Scenario: A run's band
- **WHEN** a run's traffic is above 95% of the domain's runs
- **THEN** it's shown in the busiest band

### Requirement: Presented as an experimental relative index
The overlay SHALL be labelled as an experimental model, not a measure of crowds or queues, and SHALL NOT show skier numbers as counts of people. Details on hover SHALL give a run's band within the domain, and a lift's modelled load as a percentage of its capacity, with no mention of queues. They SHALL NOT compare a run or lift with other domains.

#### Scenario: Hovering over a run
- **WHEN** a visitor hovers over a run with the overlay on
- **THEN** the run's name and band are shown, with no count of people

#### Scenario: Hovering over a lift over capacity
- **WHEN** a visitor hovers over a lift whose modelled morning demand is 1.4× its capacity, in the morning view
- **THEN** the lift is described as modelled at 140% of capacity
- **AND** nothing is said about queues, and no count of people is shown

## ADDED Requirements

### Requirement: Lifts shown by load against capacity
Each lift SHALL be coloured by its modelled demand ÷ capacity in the current view, in four fixed bands: under 50%, 50–80%, 80–100% and over 100% (`LIFT_LOAD_BANDS` = 0.5, 0.8, 1.0). The bands SHALL be the same in every domain. Lifts SHALL use a colour scale of one hue, light to dark, distinct from the runs' colours, and the legend SHALL show the two scales separately. Nursery lifts SHALL have no load colour.

#### Scenario: A quiet domain
- **WHEN** every lift in a domain is modelled under half full
- **THEN** every lift is shown in the lightest band, and none in the over-capacity band

#### Scenario: A lift over capacity
- **WHEN** a lift's modelled demand in the current view is 1.2× its capacity
- **THEN** it's shown in the darkest band

#### Scenario: A lift and a run side by side
- **WHEN** a lift in the over-capacity band runs beside a run in the busiest band
- **THEN** they are drawn in different hues, and the legend names each scale

#### Scenario: A lift mapped in pieces
- **WHEN** a lift is mapped as several lines
- **THEN** it's shown in the band of its most loaded piece

#### Scenario: A nursery lift
- **WHEN** the overlay is on and a domain has a magic carpet
- **THEN** the magic carpet is drawn without a load colour
