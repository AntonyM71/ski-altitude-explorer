# busyness-validation Specification

## Purpose
Keep the model honest without usage data: check it against skiers' observations and stop it from writing impossible results. Rationale: [decision 011](../../../docs/decisions/011-validate-with-observations.md). The observations themselves are in [docs/observations.md](../../../docs/observations.md), and 011 records which ones the model matches.

## Requirements

### Requirement: Impossible results stop the run
A run SHALL stop with an error, without writing results, if any commuting share falls outside 0–100% or any traffic is negative. The pipeline SHALL check commuting shares before writing a structure file, and the engine SHALL check traffic before returning results.

#### Scenario: A negative commuting share
- **WHEN** a bug produces a commuting share below 0%
- **THEN** the run exits with an error and no results are written

#### Scenario: Negative traffic in the engine
- **WHEN** a bug in the engine produces negative traffic on a link
- **THEN** the engine reports an error instead of returning results, and the overlay says it couldn't be computed

### Requirement: Changes are checked on the test domains
Each change to the model SHALL be rerun on the test domains listed in decision 011, and their results compared with the observations. Structure files for the test domains SHALL be kept as test fixtures, and CI SHALL run the engine on them and check every observation decision 011 marks as matched.

#### Scenario: A model change
- **WHEN** a change to the model is made
- **THEN** every test domain is rerun and decision 011's comparison table is updated

#### Scenario: A change breaks an observation in CI
- **WHEN** a change to the engine makes a matched observation fail on a test domain's fixture
- **THEN** the CI checks fail, naming the observation

### Requirement: Matched observations stay matched
The model SHALL keep reproducing every observation that decision 011 marks as matched. A change that breaks one SHALL be treated as a regression, to fix or justify before the change is kept.

#### Scenario: A change breaks a match
- **WHEN** a change makes a run that's observed to be quiet busier than one observed to be busy
- **THEN** the change is a regression until fixed or justified

### Requirement: Observations not yet reproduced are tracked
Observations the model doesn't match SHALL be marked open in decision 011 and listed in [docs/known-issues.md](../../../docs/known-issues.md), with the model's numbers.

#### Scenario: Recording a new mismatch
- **WHEN** a run contradicts an observation
- **THEN** the mismatch is added to the known issues with the model's numbers

### Requirement: The two halves agree
The pipeline and the engine SHALL be tested against the same small fixture networks, and the pipeline's exact lift-to-lift exchange shares SHALL match the engine's laps on them.

#### Scenario: A fixture network
- **WHEN** a fixture network with two lifts, a shared top station and a junction is run through both halves
- **THEN** the pipeline's exchange shares and the engine's laps agree to within 0.1%
