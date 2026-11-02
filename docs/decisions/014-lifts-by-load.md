# 014. Show lifts by modelled load against their own capacity

**Status:** Proposed (OpenSpec change `lift-load-overlay`): accepted once the overlay is deployed

**Code:** [busyness-engine/src/views.js](../../busyness-engine/src/views.js) (`bands`, `liftsForSite`), [busyness-engine/src/params.json](../../busyness-engine/src/params.json) (`LIFT_LOAD_BANDS`) and the overlay in [index.html](../../index.html)

## Context

The overlay (012) coloured runs and lifts alike: four bands ranked within the domain, in the same four colours. For a lift, that hid what the model actually says about it, its demand ÷ capacity (010). A lift at 40% of capacity could show as "busiest" in a quiet domain, and a red lift read like a red run although they measure different things. With capacities now estimated from seats, names and length (013), the load figure is fair enough to show directly.

## Decision

- **Lifts are coloured by load against their own capacity**, in four fixed bands: under 50%, 50–80%, 80–100%, and over 100% (`LIFT_LOAD_BANDS` = 0.5, 0.8, 1.0). The bands are the same in every domain.
  - **Since lift queues ([015](015-lift-queues.md)):** the top two bands show a modelled queue, under 5 minutes or longer, instead of 80–100% and over 100% (`LIFT_LOAD_BANDS` = 0.5, 1.0; `LIFT_WAIT_BANDS_MIN` = 5).
- **Lifts have a colour scale of their own:** one purple ramp, light to dark (#8a6ad8, #6a44c8, #4a24a0, #2a0d66). Purple isn't used by the runs' bands or the piste grades. The ramp was checked with the dataviz palette validator in ordinal mode. Its lightest step clears 2:1 on every relief tint up to 3,000 m, and 3:1 on the white casing drawn under every lift line, including over bare rock.
- **The legend shows two scales:** "Runs, for this domain" and "Lifts, of capacity".
- **Hovering over a lift gives its percentage of capacity**, to the nearest 10%: for example, "modelled at 140% of capacity". A lift just over 100% says so, rather than rounding to 100%. It says nothing about queues. Since lift queues (015), a lift with a queue gives its modelled wait in minutes instead.
- **Nursery lifts** carry no laps in the model, so they're drawn in plain lift ink, with no load.
- **Runs are unchanged:** still four bands ranked within the domain.

## What a lift's percentage means

Every lift is assumed to run at capacity, and a domain's skiers are its total lift capacity ÷ 3.5 rides an hour (004). So a lift's percentage shows how the model spreads that domain's skiers across its lifts: which lifts it sends more skiers to than they can carry, and which have room. It isn't an observed queue.

It also means no domain can come out quiet overall. A domain that's short of lifts and one with lifts to spare get the same overall load, so percentages aren't truly comparable between domains, even on the same scale. Sizing skiers from something other than the domain's own lifts is [issue #5](https://github.com/AntonyM71/ski-altitude-explorer/issues/5).

## Alternatives considered

- **Keep lifts ranked within the domain.** Consistent with runs, but it hides the one absolute figure the model has for a lift.
- **A continuous colour scale.** More precise, but four bands read at a glance and match the runs' legend.
- **A gauge at the bottom station.** It shows where queues form, but it's a new glyph to design and place, for the same information.
- **Say "likely queue" over 100%.** Plainer, but it claims more than the model can support while issue #5 is open.

## Consequences

- **More purple on the map:** with the overlay on, lifts are purple, and the runs' traffic colours are left to the runs.
- **A one-off rebuild:** adding `LIFT_LOAD_BANDS` to the engine's parameters changes every domain's fingerprint, so the next busyness run rebuilds every structure file once. Their contents are unchanged.
- **The review map** already showed load on a continuous scale, and is unchanged.
