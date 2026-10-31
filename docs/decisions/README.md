# Decision records

Each record explains one analytical decision: the problem, what we chose, the evidence behind it, and what it costs. Records are kept when a decision is replaced, with their status updated, so the reasoning stays traceable.

**Status:**
- **Accepted:** built and shipped.
- **Proposed:** in the busyness model, not yet deployed.
- **Superseded:** replaced by a later record.

## Domains and measurement

| # | Decision | Status |
|---|---|---|
| [001](001-join-touching-ski-areas.md) | Join ski areas whose runs or lifts touch into linked domains | Accepted |
| [002](002-joined-domain-identity.md) | How a joined domain is counted, named and identified | Accepted |
| [003](003-count-area-only-pistes.md) | Count pistes mapped only as areas, with an estimated length | Accepted |

## Busyness model (issue #3)

| # | Decision | Status |
|---|---|---|
| [004](004-busyness-from-lift-capacity.md) | Estimate busyness as a relative index from lift capacity | Proposed |
| [005](005-busyness-network.md) | Build a lift and run network, with wide joins at lift stations | Proposed |
| [006](006-laps-flow.md) | Laps: skiers spread downhill by weighted choice at junctions | Proposed |
| [007](007-sectors-from-network.md) | Find sectors from the network, not from place names | Proposed |
| [008](008-villages.md) | Find villages from places (Overture Maps), sized by their buildings | Proposed |
| [009](009-commuting.md) | Commuting: a gravity model with ability groups and varied routes | Proposed |
| [010](010-time-of-day-views.md) | Three views: day average, morning rush and evening rush | Proposed |
| [011](011-validate-with-observations.md) | Validate against skiers' observations, not usage data | Proposed |
| [012](012-busyness-production-architecture.md) | Run busyness as Python structure plus a JavaScript engine in the browser | Proposed |
