# Proposal

## Why

Since short blacks began counting more like reds (by committed length), the end-of-day penalty for blacks has been blended away along with the others. A long black that's crossed by easier runs now counts almost like a red on the way home, so it draws the evening rush away from the green and the gondola people actually use (known issue 6a). Being able to bail out makes a black less daunting to start, but it doesn't make a hard, low, icy run any easier on tired legs at the end of the day.

## What Changes

- The end-of-day penalty for blacks (`EVENING_FEEL`, ×1.6) applies in full to every black, whatever its committed length.
- Short-black blending still applies to the lap pull and to each ability group's route weights, by day and in the evening.
- Docs: decision 009 and known issue 6a are updated with the result, and decision 011's comparison table is refreshed.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `busyness-laps`: "Short blacks count more like reds" no longer applies wherever a black's grade sets a weight. It applies to the lap pull and route weights, but not to end-of-day conditions.
- `busyness-commuting`: "End-of-day conditions" states that the black penalty applies in full, regardless of committed length.

## Impact

- **Code:** `prototypes/busyness.py`, where the evening route times are worked out. It's a one-line change in effect.
- **Results:** mainly the evening rush view in every test domain. The day average changes a little too, because commuters' return trips use the way-home times. The morning rush and laps are unchanged.
- **Docs:** decision 009 (the way home), decision 011 (comparison table) and `docs/known-issues.md` (6a).
- **No new dependencies.**
