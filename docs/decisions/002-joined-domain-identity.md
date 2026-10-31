# 002. How a joined domain is counted, named and identified

**Status:** Accepted (issue #1, commits `0a7bf89` and `637ee57`)

## Context

A joined set of resorts (see 001) has to appear on the site as one domain, with its own figures, name and shareable link. Runs shared between members must not be counted twice.

## Decision

- **Counting.** A joined domain is built from every run, area-only piste and lift of its members and their sub-areas, each counted once. Its altitude histograms, run count, altitude range and map file are rebuilt from those, not summed from its members.
- **Membership.** Members become sub-areas of the joined domain. With "Linked domains" on, only the joined domain is ranked, and searching for a member shows "part of" the joined domain.
- **Name.** A short hand-kept list, `LINKED_NAMES`, names a set by any member: for example "Sestriere" gives "Via Lattea". Otherwise the set keeps its largest member's name if that member holds at least 85% of the km (`LINKED_ALONE`). Failing that, it takes the first three names joined by " / ", with "+N" for the rest.
- **Id.** `linked-` plus a hash of the id of the member with the most runs. Shared links survive members joining or leaving.
- **Title card.** The card lists the joined domain's resorts ("linking Montgenèvre, Sestriere, …").

## Evidence

- **Via Lattea:** 249 km and 485 runs, against OpenSkiMap's own 252 km for the same resorts.
- **Id stability:** the first version hashed all member ids, so the id changed whenever membership did. When piste areas (003) added a member to two sets, their ids changed and links to them would have broken. Hashing the main member fixed this.
- **Old links:** a saved link to a member, such as Saalbach, still opens that resort.

## Alternatives considered

- **Summing members' figures.** Rejected, because it double-counts runs tagged to two members.
- **Hashing all member ids.** Rejected for the instability above.

## Consequences

- **Clumsy names:** names built automatically can be long ("Skicircus Saalbach-Hinterglemm Leogang Fieberbrunn / Schmittenhöhe Zell am See"). They need entries in `LINKED_NAMES` to read well.
- **Id changes:** the id changes if the main member changes, which should be rare.
