# Proposal

## Why

On the busyness overlay, a lift is coloured by its rank among the domain's lifts, in the same four colours as the runs. That hides what the model actually says about a lift: how its modelled demand compares with its own capacity. A lift at 40% of capacity can show as "busiest" in a quiet domain, and a red lift reads like a red run although they measure different things. Now that capacities are estimated more fairly (decision 013), the load figure is worth showing directly.

## What Changes

- **Lifts show their modelled load against their own capacity**, in four fixed bands: under 50%, 50–80%, 80–100%, and over capacity. The bands are the same in every domain, not ranked within it.
- **Lifts get a colour scale of their own:** one hue, light to dark, drawn on the lift line, so they can't be mistaken for the runs' traffic colours. The legend shows the two scales separately.
- **Hovering over a lift gives its load as a percentage of capacity**, for example "modelled at 140% of capacity". It says nothing about queues and gives no count of people.
- **Runs are unchanged:** still four bands ranked within the domain, in the current colours.
- **Nursery lifts**, which carry no laps in the model, are drawn without a load colour.
- **Docs:** a new decision record (014) explains the change. Decision 012's "relative within the domain" is narrowed to runs.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `busyness-overlay`:
  - "Banded within the domain" now covers runs only.
  - A new requirement shows lifts by load against capacity, in fixed bands on a scale of their own.
  - "Presented as an experimental relative index" says what a lift's hover shows: a percentage of capacity, with no queue wording.

## Impact

- **Engine (`busyness-engine/`):**
  - `views.js` bands lifts at fixed load thresholds (a new `LIFT_LOAD_BANDS` in `params.json`) instead of percentiles.
  - `worker.js` also passes each lift's load, so the site can show the percentage.
  - The views tests are updated to match.
- **Site (`index.html`):** the lift line colours, the legend, and the lift hover text.
- **Unchanged:** the model's results, structure files and the Python pipeline. Only how lifts are banded and shown changes.
- **Not in scope:** the review map (`prototypes/busyness_review.html`) already colours lifts on a continuous load scale, and stays as it is.
- **No new dependencies.**
