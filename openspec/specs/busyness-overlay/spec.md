# busyness-overlay Specification

## Purpose
Show visitors which runs and lifts are relatively busy within the domain they're looking at, computed in their browser from the domain's busyness structure, as an experimental overlay on the site's map.

## Requirements

### Requirement: An overlay on the domain map
When a modelled domain is shown on the map, the site SHALL offer a busyness overlay that colours its runs and lifts by modelled traffic. The overlay SHALL be off until the visitor turns it on. Domains without a structure file SHALL show no busyness control.

#### Scenario: Turning the overlay on
- **WHEN** a visitor opens a modelled domain and turns the busyness overlay on
- **THEN** its runs and lifts are coloured by modelled traffic

#### Scenario: A domain that isn't modelled
- **WHEN** a visitor opens a domain with no structure file
- **THEN** no busyness control is shown

### Requirement: Computed in the browser without blocking the page
The site SHALL compute the overlay with the busyness engine in a background worker, from the domain's structure file. The map SHALL stay usable while it computes, and SHALL show that it's computing.

#### Scenario: A large domain
- **WHEN** the visitor turns the overlay on for a domain that takes a few seconds to compute
- **THEN** the map can still be panned and zoomed, and a progress state is shown until the colours appear

#### Scenario: A browser that can't run the engine
- **WHEN** the browser can't start the background worker
- **THEN** the overlay control says busyness isn't available in this browser, and the rest of the site works as usual

### Requirement: Banded within the domain
Runs SHALL be coloured in bands by their rank among the same domain's runs: quiet, moderate, busy and busiest, split at the domain's 50th, 80th and 95th percentiles of length-weighted traffic (`BANDS`). Run colours SHALL NOT be comparable between domains. Lifts are shown by load instead (see "Lifts shown by load against capacity").

#### Scenario: Two domains of different sizes
- **WHEN** a small domain and a very large one are each shown with the overlay
- **THEN** each shows about the same share of its runs as busiest

#### Scenario: A run's band
- **WHEN** a run's traffic is above 95% of the domain's runs
- **THEN** it's shown in the busiest band

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

### Requirement: Day, morning and evening
The overlay SHALL offer the day average, the morning rush and the evening rush, and switching between them SHALL NOT recompute the model.

#### Scenario: Switching to the evening
- **WHEN** a visitor switches the overlay from day to evening
- **THEN** the colours change straight away to the evening bands

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

### Requirement: Sources are credited
When the overlay is shown, the site SHALL credit Overture Maps and OpenStreetMap contributors for the place and building data behind it.

#### Scenario: Attribution
- **WHEN** the overlay is on
- **THEN** the map's attribution includes Overture Maps and OpenStreetMap contributors
