# Spec Delta

## MODIFIED Requirements

### Requirement: Results files
The pipeline SHALL write one structure file per modelled domain (see busyness-pipeline), and the engine SHALL compute every view from it: for each link and lift, its traffic per hour in the day average, morning rush and evening rush, demand ÷ capacity for lifts, and riding down in the evening. Results SHALL NOT be stored per domain; anything that needs them, including tests, runs the engine.

#### Scenario: Running a domain
- **WHEN** the engine is given a domain's structure file
- **THEN** it returns every link's and lift's traffic for the three views

#### Scenario: Checking a domain from the command line
- **WHEN** the engine's command-line runner is given a structure file
- **THEN** it prints the domain's busiest runs and lifts for each view

### Requirement: Review map
`prototypes/busyness_review.html?d=<domain id>` SHALL load a domain's structure file, run the engine, and show the domain's runs coloured by skiers an hour and its lifts by demand ÷ capacity, with day, morning and evening views, lists of the busiest runs and lifts and the quietest named runs, and details on hover.

#### Scenario: No results for the domain
- **WHEN** the page is opened with a domain id that has no structure file
- **THEN** it says so and shows the command to produce one
