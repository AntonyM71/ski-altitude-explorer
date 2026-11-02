# Ideas and fixes

Ideas for the busyness model to come back to, fixes to make in the map data, and issues with linked domains. Problems that affect the busyness model's results today are in [known-issues.md](known-issues.md). Items keep their number as an ID, shared with that document. Remove an item once it's done, and note it in the decision record it concerns.

## Ideas for the busyness model

- **Snow conditions: low, sun-facing runs are avoided.** Low runs facing the equator (south in the northern hemisphere, north in the southern) get slush and ice, and people avoid them, especially late in the day.
  - **Shape:** a penalty that grows with how directly a run faces the equator (half for east or west) and how low it sits within the domain's own altitude range, so it works from the Alps to Japan. Say up to ×1.3 for the lowest equator-facing runs, applied like the end-of-day penalty.
  - **To decide:** evening only, or a little by day too (refrozen sunny slopes are icy first thing); whether west faces are worse than east in the evening; and whether the end-of-day penalty should then cover tired legs only.
  - **Data:** a run's line gives its direction of travel, not the way the slope faces; they differ on traverses. A terrain model would give the true aspect.
  - **Expected effect:** it favours the Face de Bellevarde over Joseray (both east-facing, Joseray about 340 m lower). It doesn't separate Luc Alphand from Briance ([known issue 3](known-issues.md#mismatches-with-observations); both face north-east at about 1,650 m), and slightly penalises Piste M (west) against Piste L (north).
  - **Needed:** observations of runs that are slushy or icy late in the day.

  [009](decisions/009-commuting.md)
- **A lift's pull should reflect where it takes you, not just its capacity.** The old Pontillas standing gondola at Serre Chevalier was rarely busy: it went somewhere less useful than the Casse du Bœuf six-seater beside it. Locals' first lift and lapping skiers choose by capacity alone. Pull could also weigh how much skiing, or how many onward lifts, a lift's top leads to. [006](decisions/006-laps-flow.md)

## Fixes in the map data

Pistes and lifts come from OpenStreetMap via OpenSkiMap, so these are fixed there, not in the code.

- **6. Mézies is missing from the data.** It crosses Pylônes, along with 3 Croix and Lièvre Blanc, but doesn't appear in OpenSkiMap, so Pylônes's 712 m stretch between 3 Croix and Lièvre Blanc is probably shorter in reality. Check OpenStreetMap. [005](decisions/005-busyness-network.md)

## Linked domains (issue #1)

12. **Long joined names.** Add clean names to `LINKED_NAMES` for "Skicircus Saalbach-Hinterglemm Leogang Fieberbrunn / Schmittenhöhe Zell am See", "Big Sky Resort / Yellowstone Club" and "GrandValira / Canaro". [002](decisions/002-joined-domain-identity.md)
13. **Pragelato isn't joined to the Via Lattea.** Its ski area holds a single 0.3 km run that touches nothing. Check its lifts and pistes in OpenStreetMap. [001](decisions/001-join-touching-ski-areas.md)
14. **Shiga Kogen comes out as two joined domains.** The Yokoteyama end doesn't touch the rest in the data. [001](decisions/001-join-touching-ski-areas.md)
