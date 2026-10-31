# Design

## Context

Route times on the way home multiply three factors on each run: the ability group's grade weight, the end-of-day penalty (`EVENING_FEEL`) and the skied-out factor. One helper gives a black its by-grade value blended by committed length, and it's currently used for both of the first two. See proposal.md for why that's wrong for the second.

Before short-black blending, joining runs where they cross alone had already put the way home in line with what's observed: the black quieter than the long green and the gondola ride down. With blending, the same black became one of the busiest runs in the evening rush.

## Goals / Non-Goals

**Goals:**
- Put back the full end-of-day penalty for every black, keeping short-black blending for daytime choices and ability weights.

**Non-Goals:**
- A separate penalty for low-altitude or south-facing runs. Possibly a better model of end-of-day conditions, but it's new behaviour with its own evidence to gather.
- Retuning `EVENING_FEEL`, `BLACK_SHORT_M` or `BLACK_LONG_M`.

## Decisions

- **Use the plain grade for the end-of-day penalty.** The evening penalty looks up the run's grade directly. The ability weight keeps the blended value. Alternatives considered:
  - *Blend both, but with a longer `BLACK_LONG_M` in the evening.* This keeps more of the penalty, but it ties conditions to how often a black is crossed, which is the wrong cause.
  - *Raise `EVENING_FEEL` for blacks.* This would offset the blending for crossed blacks, but over-penalise long uncrossed blacks, which already carry the full penalty.
- **Leave the skied-out factor alone.** It already depends on daytime traffic, not grade.

## Risks / Trade-offs

- [Short blacks that really are easy at the end of the day get the full evening penalty] → Accept for now: the observations so far are all of hard blacks at the end of the day. Revisit if a short black is observed busy in the evening.
- [Fixing one observation could break another] → Rerun all four test domains and compare with decision 011 before keeping the change.
