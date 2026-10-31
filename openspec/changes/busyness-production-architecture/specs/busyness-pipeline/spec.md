# Spec Delta

## Purpose

Prepare each eligible domain's busyness structure (its network, villages and sectors) from the weekly map data, cache it, and publish the last good set for the site, without ever blocking the site's own build.

## ADDED Requirements

### Requirement: Domains are those the site shows
The pipeline SHALL prepare busyness for domains by the site's domain id, including linked domains, using the same membership of ski areas, runs and lifts as the site's statistics. It SHALL NOT look domains up by name.

#### Scenario: A linked domain
- **WHEN** the site joins several ski areas into one linked domain
- **THEN** its busyness structure covers the runs and lifts of all its members, under the linked domain's id

#### Scenario: Two ski areas with the same name
- **WHEN** two unrelated ski areas share a name
- **THEN** each domain's structure contains only its own runs and lifts

### Requirement: Only domains large enough are modelled
The pipeline SHALL prepare busyness only for top-level domains with at least 30 km of piste (`MIN_KM`) and at least 5 lifts that aren't nursery lifts (`MIN_LIFTS`). Other domains SHALL have no structure file.

#### Scenario: A small resort
- **WHEN** a domain has 12 km of piste
- **THEN** no structure file is written for it, and the site shows no overlay for it

### Requirement: A structure file per domain
For each modelled domain, the pipeline SHALL write a structure file holding everything the engine needs and nothing it computes: junctions with altitudes, links with their kind, grade, length, gradient, committed length, route time, capacity and nursery flag, each run link's run id in the site's runs file, lifts' sectors, sector capacities and commuting shares, and villages with their stations, capacity and skiers. It SHALL include the model version and the inputs' fingerprint.

#### Scenario: Behaviour stays out of the structure
- **WHEN** a weighting such as a grade's pull changes
- **THEN** no structure file needs to change, only the engine's parameters

#### Scenario: Linking results to the map
- **WHEN** the engine produces traffic for a run link
- **THEN** the site can find that run's line in its runs file by the link's run id

### Requirement: Only changed domains are recomputed
A domain's structure SHALL be reused from the previous run if its fingerprint (its runs, lifts, places data release and model version) is unchanged, and recomputed otherwise.

#### Scenario: A quiet week
- **WHEN** a weekly run finds that a domain's runs and lifts haven't changed
- **THEN** its structure file is reused without recomputing

#### Scenario: A model change
- **WHEN** the structure code's model version changes
- **THEN** every domain is recomputed

### Requirement: Places and buildings are harvested once per release
Places and building counts SHALL come from Overture Maps at a pinned release (`OVERTURE_RELEASE`), queried in batches covering many domains at once, and cached by release. A domain SHALL NOT query Overture again unless the pinned release changes or the domain's area does.

#### Scenario: Moving the pin
- **WHEN** the pinned Overture release is changed
- **THEN** places and building counts are harvested again, and every domain's fingerprint changes

#### Scenario: Overture unavailable
- **WHEN** Overture can't be reached during a run
- **THEN** domains with cached places are prepared as usual, and domains without fall back to finding villages from the lift layout

### Requirement: The site uses the last good set
The busyness workflow SHALL run separately from the site's build and publish a complete set of structure files only when it succeeds. The site's build SHALL include the most recently published set, and SHALL succeed without one.

#### Scenario: A failed busyness run
- **WHEN** the busyness workflow fails
- **THEN** the previously published set stays in place, and the site's next build uses it

#### Scenario: No set published yet
- **WHEN** the site builds before any busyness set has been published
- **THEN** the site builds and deploys as usual, with no overlay
