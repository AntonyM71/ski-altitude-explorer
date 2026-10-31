# 003. Count pistes mapped only as areas, with an estimated length

**Status:** Accepted (issue #2, commit `637ee57`)

## Context

Some pistes are mapped in OpenStreetMap as an outline of the slope (an area) with no line down it. The build skipped all areas, because an outline has no length. Most areas sit on top of a run line that's already counted, but some don't, and a few resorts are mapped almost entirely as areas. Cairngorm counted 0.02 km, and resorts such as Tannaskroket and Laceno were missing from the site.

## Decision

- **Which areas count.** An area is counted as its own piste unless more than 40 m (`AREA_LINE_M`) of a counted run lies within 15 m (`AREA_EDGE_M`) of its outline.
- **Length:** the long side of a strip with the same area *A* and perimeter *P*: `(P/2 + sqrt((P/2)² − 4A)) / 2`.
- **Altitude:** the length is spread evenly between the outline's lowest and highest vertex, into the 100 m bands.
- **What it feeds:** the area's own grade and the domain's run count. Outlines also take part in linking (001).
- **Every area counts,** including snow parks, slalom stadiums and ski-school meeting areas.
- **On the map:** areas are drawn as grade-coloured fills, faded below the snow line.

## Evidence

Measured worldwide on 11,128 kept piste areas.

**Matching areas to lines.** Lines drawn just along an area's edge are common, so the tolerance matters:

| A line counts if it runs… | Area-only pistes found |
|---|---|
| inside the area | 1,355 |
| within 15 m of the edge | 906 |
| within 30 m of the edge | 694 |

**Length.** Three estimates were tested on 1,128 areas with a single run along them, so the true length is known:

| Estimate | Estimate ÷ true length: median (p10–p90) | Within ±25% |
|---|---|---|
| Long side of the smallest enclosing rectangle | 1.00 (0.82–1.14) | 90% |
| **Ribbon (chosen)** | **1.03 (0.98–1.17)** | **95%** |
| Area ÷ typical width for the grade | 1.08 (0.55–2.21) | 42% |

**Altitude.** The real line's median altitude is typically within 11 m of the outline's mid-range (40 m at the 90th percentile), and the vertical range differs by about 5 m.

**Effect.** 345 km added worldwide (under 1%) and nothing shrank:
- Cairngorm grew from 0.02 to 18.5 km, and Alpensia from 0.4 to 10.3 km.
- About 290 resorts appear for the first time.
- Les Trois Vallées grew by 2.3 km.

## Alternatives considered

- **Area ÷ typical width:** far less accurate (42% within ±25%).
- **A medial-axis centreline:** more complex. The ribbon estimate was already accurate enough.
- **Excluding parks and ski-school areas by name:** only about 40 are named like that, and small ones add almost nothing.

## Consequences

- **Accuracy limits:** branching or very irregular areas can be further off than the 25% band.
- **Dependency:** the build needs `shapely`, and takes 130 s instead of 91 s.
