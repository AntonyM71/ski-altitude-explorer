# Design

## Context

- **Engine:** `bands()` in `busyness-engine/src/views.js` cuts runs and lifts alike at the domain's `BANDS` percentiles (0.5, 0.8, 0.95). Lifts are cut on demand ÷ capacity, and nursery lifts get band 0.
- **Worker:** `worker.js` sends the site only the bands, taking a lift's busiest piece where it's mapped in several.
- **Site:** `index.html` paints runs and lifts from one `BAND_COLOR` expression. It shows one legend ("quiet … busiest, for this domain") and the same hover wording for both: "a modelled ranking, not a count of crowds or queues".

The load figure itself, demand ÷ capacity per lift and view, already exists in the engine's summary (`views.js`, `summarise`), and the review map shows it.

## Goals / Non-Goals

**Goals:**
- A lift's colour and hover text say how its modelled demand compares with its own capacity, on a scale that's clearly not the runs'.

**Non-Goals:**
- Changing how runs are banded or coloured.
- Changing the model or its numbers, including how a domain's skiers are sized (issue #5).
- The review map, which already shows load on a continuous scale.
- A separate glyph or gauge at lift stations. It was considered and set aside in favour of colouring the lift line on its own scale.

## Decisions

- **Fixed lift bands in the engine.** `bands()` cuts lifts at `LIFT_LOAD_BANDS` (0.5, 0.8, 1.0, in `params.json`) rather than at percentiles, using the same `x > cut` count. Exactly 100% falls in the 80–100% band, and anything over it in the top band. Nursery lifts get `null`, not 0, so the site can tell "no load" from "quiet". Banding stays in the engine, rather than moving to the site, so the thresholds live with the other behaviour constants and are tested there.
- **The worker sends the load as well as the band.** Each lift and view gets `[band, load]`. A lift mapped in pieces takes the piece with the highest load, and that piece's band. Sending the load is what lets the hover say "140%".
- **One purple ramp for lifts, four steps light to dark.** Purple isn't used by the runs' bands (grey, yellow, orange, red) or the piste grades (green, blue, red, black), so a lift can't be read as either. The steps are checked with the dataviz palette validator in ordinal mode against the map's background, so the lightest still stands out. Alternatives considered:
  - *A continuous gradient:* set aside by the project owner in favour of four bands that read at a glance.
  - *A gauge at the bottom station:* a new glyph to design and place, for the same information.
- **Nursery lifts are drawn as they are with the overlay off:** the dark lift ink, no load colour.
- **Two legends side by side when the overlay is on.** "Runs, for this domain: quiet … busiest", and "Lifts, of capacity: under 50% … over 100%".
- **Hover wording:** "Busyness in the morning rush: modelled at 140% of capacity". The percentage is rounded to the nearest 10%, to avoid false precision. The overlay toggle's tooltip drops "a ranking", since lifts are no longer ranked.

## Risks / Trade-offs

- [Lift percentages look like measurements] → They're labelled "modelled", and the overlay stays "experimental". Decision 014 records what they mean: every lift is assumed to run at capacity, and a domain's skiers are its capacity ÷ 3.5 rides an hour (004). So a percentage says how the model spreads skiers across lifts, not an observed queue. A domain can't show every lift as quiet, because its skiers are sized to its lifts. Fixing that sizing is issue #5, outside this change.
- [Domains now look comparable for lifts] → The bands are the same everywhere, but the hover still doesn't compare domains. Decision 014 explains the limit above.
- [Purple on terrain is hard to read, especially the lightest step] → The validator check, plus the white casing already drawn under lift lines. Look at the result on a test domain before finishing.

## Migration Plan

A site and engine change with no data migration. Adding `LIFT_LOAD_BANDS` to `params.json` changes every domain's fingerprint, because the pipeline hashes the engine's parameters, so the next busyness run rebuilds every structure file once, with identical contents apart from the fingerprint. The test fixtures are regenerated for the same reason. Rollback is reverting the change.
