# Spec Delta

## MODIFIED Requirements

### Requirement: Routes vary
Routes SHALL be averaged over 30 draws (`DRAWS`), each varying every link's time by about ±30% (`NOISE`). Run times SHALL also be scaled by gradient: near-flat runs ×1.4, runs steeper than 45% on average ×1.3. The draws SHALL come from a seeded random sequence (`SEED`), so the same structure and parameters give the same result every time.

#### Scenario: Two nearly equal routes
- **WHEN** two routes take almost the same time
- **THEN** commuters use both, not just the quicker

#### Scenario: Running twice
- **WHEN** the engine runs twice on the same structure file in the same environment
- **THEN** both runs give identical traffic on every link

#### Scenario: Different browsers
- **WHEN** the engine runs on the same structure file in two different browsers
- **THEN** traffic on every link agrees to within 0.1%
