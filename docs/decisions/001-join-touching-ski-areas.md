# 001. Join ski areas whose runs or lifts touch into linked domains

**Status:** Accepted (issue #1, commit `0a7bf89`)

## Context

The site ranks linked domains, and relies on OpenSkiMap's grouping of resorts into them. OpenSkiMap doesn't group every linked domain. The Via Lattea exists only as five separate resorts, none a sub-area of another, so each ranked separately, well down the list. Other domains had the same problem, and some resorts were mapped twice as separate areas.

## Decision

The build joins top-level ski areas that physically connect:

- **A link** is a run or lift end within 30 m (`SNAP_M`) of a run or lift of another top-level area, or a run tagged to both areas.
- **One link is enough** (`LINK_MIN = 1`).
- **Links chain:** A–B and B–C make one set, so a string of resorts becomes one domain, however long. Joining uses union-find over all linked pairs.
- **Every lift type counts,** including trains and funiculars.
- **Pass networks are never joined** (`PASS_NETWORKS`: lift-pass groupings of unlinked valleys, such as Dolomiti Superski).
- **Pistes mapped only as areas** take part through their outlines (see 003).

The build prints every joined set, so the list can be reviewed each week.

## Evidence

- **How the Via Lattea connects in the data:** Claviere–Montgenèvre touch at 14 points, Sauze d'Oulx–Sansicario at 14, Sestriere–Sansicario at 5, Sestriere–Sauze d'Oulx at 2, and Claviere–Sansicario at 1. That one point is the real link at Cesana, a chairlift meeting a gondola. A threshold of 2 would have split the Via Lattea in two, hence `LINK_MIN = 1`.
- **Result:** the Via Lattea becomes one domain of 249 km, and 130–138 domains are joined in all.
- **Review:** all 154 linked pairs were checked on a map. Doubtful-looking links were accepted as genuine by the project owner, including Grindelwald–Mürren (mostly through railway and funicular ends) and Big Sky–Yellowstone Club (physically skiable, though the club is private).
- **No regressions:** compared with the previous build on the same data, no area's figures changed. 300 previously top-level areas gained a parent, and nothing else moved.
- **Build time** went from 45 s to 91 s, because the raw files are read a second time to find contacts.

## Alternatives considered

- **A higher threshold** (2–5 contacts). This drops weak false links but splits real domains like the Via Lattea.
- **Excluding train and funicular contacts.** This would have removed Grindelwald–Mürren and Garmisch–Zugspitze, but the owner judged those links legitimate.
- **A hand-kept exclusion list.** Not needed after review. It's the fallback if a false link appears.

## Consequences

- **Over-joining is possible:** resorts that touch, or share a valley lift or train, are joined even where most skiers treat them as separate. The README lists this as a known issue.
- **Data dependence:** links depend on OpenStreetMap mapping. A resort whose pistes stop short of its neighbour's won't join. Pragelato isn't joined to the Via Lattea because its ski area holds a single 0.3 km run.
