# Spec Delta

## Purpose

Show visitors which runs and lifts are relatively busy within the domain they're looking at, computed in their browser from the domain's busyness structure, as an experimental overlay on the site's map.

## ADDED Requirements

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
Runs SHALL be coloured in bands by their rank among the same domain's runs: quiet, moderate, busy and busiest, split at the domain's 50th, 80th and 95th percentiles of length-weighted traffic (`BANDS`). Lifts SHALL be banded the same way by demand ÷ capacity among the domain's lifts. Colours SHALL NOT be comparable between domains.

#### Scenario: Two domains of different sizes
- **WHEN** a small domain and a very large one are each shown with the overlay
- **THEN** each shows about the same share of its runs as busiest

#### Scenario: A run's band
- **WHEN** a run's traffic is above 95% of the domain's runs
- **THEN** it's shown in the busiest band

### Requirement: Day, morning and evening
The overlay SHALL offer the day average, the morning rush and the evening rush, and switching between them SHALL NOT recompute the model.

#### Scenario: Switching to the evening
- **WHEN** a visitor switches the overlay from day to evening
- **THEN** the colours change straight away to the evening bands

### Requirement: Presented as an experimental relative index
The overlay SHALL be labelled as an experimental model of relative busyness within the domain, not a measure of crowds or queues, and SHALL NOT show skier numbers as counts of people. Details on hover SHALL give a run's or lift's band, and SHALL NOT compare it with other domains.

#### Scenario: Hovering over a run
- **WHEN** a visitor hovers over a run with the overlay on
- **THEN** the run's name and band are shown, with no count of people

### Requirement: Sources are credited
When the overlay is shown, the site SHALL credit Overture Maps and OpenStreetMap contributors for the place and building data behind it.

#### Scenario: Attribution
- **WHEN** the overlay is on
- **THEN** the map's attribution includes Overture Maps and OpenStreetMap contributors
