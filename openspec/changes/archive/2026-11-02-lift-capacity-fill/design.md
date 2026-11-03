# Design

## Context

Today a lift's capacity is settled in `busyness/partition.py` (`_lift`): the recorded value if it's plausible, else `CAP_BY_TYPE`, with `cap_known` saying which. Its ride time is settled later, in `busyness/network.py`: the recorded duration, else the link's length ÷ `LIFT_SPEED` for its type. `cap_known` goes into the structure file and the fingerprint; the engine never reads it.

The analysis behind the tables lives in `prototypes/lift_capacity.py`, which has its own copy of the name patterns (`name_hints`) and its own lookup code. See proposal.md for why, and decision 013 for the evidence.

## Goals / Non-Goals

**Goals:**
- One place that turns a raw lift into capacity, speed and their sources, testable without the raw files.
- The prototype and the pipeline share the name patterns, so the tables are fitted on exactly what the pipeline reads.

**Non-Goals:**
- Changing the flat values themselves (`CAP_BY_TYPE`, `LIFT_SPEED`), including the cable car's 8 m/s ride speed. The formula's 8.5 m/s is a fitted constant for capacity, not a ride speed.
- Showing the sources on the review map. They're recorded so that this can come later.
- Construction year, or any other new data source.
- The legacy one-file prototype (`prototypes/busyness.py`).

## Decisions

- **A new module, `busyness/lifts.py`,** holds the name patterns and one function that takes a lift's raw properties and its length, and returns capacity, speed and both sources. `partition._lift` calls it. The alternative was to grow `_lift` in place; a separate module keeps the rules unit-testable from plain dicts, and gives the prototype something to import.
- **The prototype imports the name patterns from `busyness.lifts`,** and drops its own copy. The patterns then can't drift between what was fitted and what runs.
- **Speed is settled in partition, not network.** Each lift `Feature` gets `speed` (m/s, always set) and `speed_src`, alongside the recorded `dur`. The network keeps `f.dur or length / f.speed`. The chairlift lookup needs the lift's whole length, which partition has and the network's link doesn't need to know about.
- **`cap_known` becomes `cap_src`,** with `speed_src` beside it: `recorded`, `seats`, `name` or `type`. The fast-name hint refines a seats lookup but doesn't change its source. A boolean can't say "estimated from seats read from the name", and that's the distinction worth keeping.
- **Tables are plain dicts in `params.py`:**
  - `CHAIR_CAP[(seats, fast)]`
  - `CHAIR_SPEED[(seats, long)]`
  - `GONDOLA_CAP[seats]`
  - with `SEATS_MAX`, `LONG_M`, `CABLE_MIN_SEATS`, `CABLE_SPEED` and `CABLE_LOAD_S`.

  `prototypes/lift_capacity.py --params` prints them as Python, fitted on all lifts in ski areas, with cells of fewer than 5 lifts left out. They're pasted into `params.py` and reviewed by hand. Fitting at pipeline run time was rejected in decision 013: every download would move every domain.
- **Lookups fall back within the seat count before the type.** A chairlift with a fast name and 2 seats has no `(2, fast)` cell, since fast two-seaters are rare. It takes `(2, not fast)` rather than the type value, because seats say more than the hint. The same goes for `CHAIR_SPEED` across short and long. Only a seat count with no cell at all falls back to the type value, as the spec says.
- **Model version 3.** The structure format changes (`cap_src` and `speed_src` replace `cap_known`), and so do most lifts' values. Bumping `MODEL_VERSION` rebuilds every domain, rather than trusting the fingerprint to notice.

## Risks / Trade-offs

- [Results shift in the four test domains, and an observation that matched in decision 011 may stop matching] → Regenerate the fixtures, run the engine's observation tests, and recheck decision 011's table before archiving. A regression is investigated, not waved through.
- [Name patterns match the wrong thing, as "Doppel" once matched Doppelmayr] → Unit tests for each pattern family, including the known false matches. Seats from names already agree with recorded seats for 1,211 of 1,223 chairlifts.
- [Tables fitted on today's data age as lifts are rebuilt] → Accepted: they change only when someone regenerates and reviews them. The `--params` output makes that a short job.
- [A wrong recorded seat count now changes capacity, where before it was ignored] → `SEATS_MAX` catches capacities typed into seats. Smaller errors, such as a quad recorded as 2 seats, are accepted: the recorded value is still the best evidence.

## Migration Plan

Merge, then the busyness workflow rebuilds every domain (new model version) and publishes a full set. Rollback is reverting the change. The previous model version's published set stays live until the new one succeeds.
