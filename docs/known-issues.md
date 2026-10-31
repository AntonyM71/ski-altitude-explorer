# Known issues

Open problems that need fixing, and ideas to come back to. Each links to the decision record it concerns ([docs/decisions/](decisions/)). Observations from skiing that the model is checked against are in [observations.md](observations.md). Remove an item once it's fixed, and note the fix in the record.

## Busyness model (issue #3: `busyness/` and `busyness-engine/`)

1. **No ski buses, so the Solaise back side skis home along the traverse** (Tignes–Val d'Isère). Observed: Piste M is busy at the end of the day, and skiers avoid flat runs like the Traversée du Laisinant. With no buses, Val d'Isère's locals on the Solaise side go home down Piste L and along the flat traverse, rather than back over Solaise and down Piste M; in reality many take the free bus from Le Laisinant. The traverse is 4th in the evening (about 1,760 an hour), Piste L 3rd, Piste M only 46th (about 670). It got worse with the production pipeline: the exact sectors merge Le Fornet's sector with the Solaise back side, so more of Val d'Isère's locals spend the day there and come home this way. Fix: add free valley ski buses as links between nearby villages (wait plus ride, say 10–15 minutes), for commuters and people going home. [005](decisions/005-busyness-network.md), [010](decisions/010-time-of-day-views.md)
2. **Santons is quiet in the evening rush** (Santons haut 63rd, Santons 70th; 35th and 46th before the production pipeline), though observed to be a busy home run. It was 12th–22nd until riding down was added; most of Val d'Isère's evening traffic now goes home over Bellevarde's other runs or rides the Olympique down. Likely tied to item 1. [010](decisions/010-time-of-day-views.md)
3. **Luc Alphand is busier than Briance on the way home to Chantemerle** (10th in the evening at 1,233 an hour; Briance 470, Ratier 664 riding down). Observed: people mostly ride Ratier down or ski Briance. Briance crosses Luc Alphand several times, so its longest black stretch without a way out is 466 m and it counts nearly like a red. Keeping the full end-of-day penalty helped only partly. Options:
   - use the plain black weight for route choice on the way home, not just for the end-of-day penalty;
   - count a crossing as a way out only if the crossing run heads the same way, since Briance is a winding road you wouldn't choose halfway down a black.

   [006](decisions/006-laps-flow.md), [009](decisions/009-commuting.md)
4. **Plein Sud isn't full in the morning** (0.65×, 38th of 127 lifts), though observed full, often with a queue. Partly the morning level (item 8), partly that Pionniers takes more of the commuters heading for the Funitel. [011](decisions/011-validate-with-observations.md)
5. **Villages: remaining gaps.** [008](decisions/008-villages.md)
   - **Sectors with no village still house skiers at a fallback station,** often a thoroughfare (Serre Chevalier's Yret, at 2,155 m, and TK Bez). Now that villages are sized by their own lifts, it isn't needed: a sector without a village is skied by people coming in. Remove it.
   - **Odd place names:** Overture's point for Courchevel isn't where Courchevel 1850 is, so 1850 appears as its quarters (La Choulière, Le Hameau, Brelin). Val Claret is now named correctly.
6. **Mézies is missing from the data.** It crosses Pylônes, along with 3 Croix and Lièvre Blanc, but doesn't appear in OpenSkiMap, so Pylônes's 712 m stretch between 3 Croix and Lièvre Blanc is probably shorter in reality. Check OpenStreetMap. [005](decisions/005-busyness-network.md)
7. **Recorded capacities can be wrong, with no way to override them.** Serre Chevalier's "Serre Chevalier" cable car is recorded at 400 an hour and shows as 6× overloaded in the morning, now that its base station belongs to the Serre Ratier village. [004](decisions/004-busyness-from-lift-capacity.md)
8. **Baseline loads rest on unsourced assumptions.** They set the model's normal level of traffic and should be rethought together. [004](decisions/004-busyness-from-lift-capacity.md), [006](decisions/006-laps-flow.md), [008](decisions/008-villages.md), [009](decisions/009-commuting.md)
   - **The morning level.** Every village's lifts carry about 0.3× of their capacity from locals in the morning, so a village lift can only stand out through traffic passing through (Plein Sud, item 4). Option: scale the morning view so a typical village lift reads about 0.8×. That's a presentation choice, not new information.
   - **3.5 rides per skier per hour.** It sets the number of skiers, the size of the rushes and the balance between commuting and laps, so it changes rankings, not just levels. Options: derive each domain's typical lap time from the network's ride and run times, add an explicit share of the day spent skiing, and test that the observations still hold between about 2.5 and 4.5.
   - **Lapping skiers wander without purpose.** Only commuters have a destination, and only in another sector. Nobody heads for a favourite area or a lunch spot within their own sector, and wanderers may over-gather at hubs, where big lifts pull hardest. Option: give more skiers destinations, using the commuting machinery.
   - **Other guesses:** the 60% top commuting share, the ability groups' shares and grade weights, the 1.5-hour rush, the 40% of laps already running during a rush, and the 60-minute travel-time decay. The decision records should say plainly that these are assumptions.
9. **Quality varies by region, with no confidence flag yet.** The production pipeline (012) runs every domain with at least 30 km of piste and 5 lifts, but the data behind it varies: capacities are often missing (typical values stand in), North American bases are often not tagged as places (Overture's building footprints help with sizing, not with naming), and layouts differ in Japan and Scandinavia. The overlay is labelled experimental; a per-domain confidence flag (for example the share of lifts with recorded capacity, and whether villages came from places or the lift layout) would let the site hide or caveat weak domains. A North American domain such as Big Sky is worth checking first. [012](decisions/012-busyness-production-architecture.md)
10. **Unconfirmed against observations:**
   - **Ours against Sittelle** (Les Trois Vallées): the ranking is doubted.
   - **Tovière riding down** (1,761 of 2,200 an hour): people like riding it down, but this much is probably too many.

   [011](decisions/011-validate-with-observations.md)
11. **Sectors mix two ideas: home areas and ski areas.** Sectors come from how lifts exchange skiers (007), but the model uses them for two things:
   - **Home areas,** where people stay: they set a village's commuting share and where its locals start and end. Le Fornet is part of Val d'Isère: "nobody would bat an eyelid".
   - **Ski areas,** places people go skiing: they're commuters' destinations. La Daille, "in the middle" between Tignes and Val d'Isère, and Orelle are places in their own right. Today's sectors lose Orelle, putting its gondola base in Val Thorens's sector.

   Trials of alternatives (2026-10-30, four test domains):
   - **Network catchments** (each lift belongs to the village with the shortest round trip) capture home areas, but lose La Daille and Orelle. They also need riding down allowed on the way home, or valley villages such as Encamp, Canillo, Brides-les-Bains and Le Fornet end up with nothing.
   - **Merging villages you can ski between without a lift** gives Val Thorens with Les Menuires, all of Courchevel, and Méribel with Mottaret, matching how the owner names them. But it keeps Tignes apart from Val Claret, and Villeneuve apart from Le Bez.
   - **Merging villages within 15 minutes** fixes those two, but splits Val Thorens from Les Menuires.
   - **Communes** (from Overture's place hierarchy) match most examples, but are too coarse in places: Pas de la Casa is in Encamp parish, and La Plagne Tarentaise takes in almost all of La Plagne.
   - **OpenSkiMap sub-areas** capture ski areas, including Orelle, where they're mapped (Les Trois Vallées, Paradiski), but most domains have none.

   Next: a separate modelling change that splits the two ideas, combining these signals, with its own trial against the examples. The architecture keeps today's sectors behind a replaceable step, so this can change without touching the engine. [007](decisions/007-sectors-from-network.md), [008](decisions/008-villages.md), [009](decisions/009-commuting.md)

### Ideas pinned for later

- **Snow conditions: low, sun-facing runs are avoided.** Low runs facing the equator (south in the northern hemisphere, north in the southern) get slush and ice, and people avoid them, especially late in the day. After the architecture (item 9).
  - **Shape:** a penalty that grows with how directly a run faces the equator (half for east or west) and how low it sits within the domain's own altitude range, so it works from the Alps to Japan. Say up to ×1.3 for the lowest equator-facing runs, applied like the end-of-day penalty.
  - **To decide:** evening only, or a little by day too (refrozen sunny slopes are icy first thing); whether west faces are worse than east in the evening; and whether the end-of-day penalty should then cover tired legs only.
  - **Data:** a run's line gives its direction of travel, not the way the slope faces; they differ on traverses. A terrain model would give the true aspect.
  - **Expected effect:** it favours the Face de Bellevarde over Joseray (both east-facing, Joseray about 340 m lower). It doesn't separate Luc Alphand from Briance (item 3; both face north-east at about 1,650 m), and slightly penalises Piste M (west) against Piste L (north).
  - **Needed:** observations of runs that are slushy or icy late in the day.

  [009](decisions/009-commuting.md)
- **A lift's pull should reflect where it takes you, not just its capacity.** The old Pontillas standing gondola at Serre Chevalier was rarely busy: it went somewhere less useful than the Casse du Bœuf six-seater beside it. Locals' first lift and lapping skiers choose by capacity alone. Pull could also weigh how much skiing, or how many onward lifts, a lift's top leads to. [006](decisions/006-laps-flow.md)

## Linked domains (issue #1)

12. **Long joined names.** Add clean names to `LINKED_NAMES` for "Skicircus Saalbach-Hinterglemm Leogang Fieberbrunn / Schmittenhöhe Zell am See", "Big Sky Resort / Yellowstone Club" and "GrandValira / Canaro". [002](decisions/002-joined-domain-identity.md)
13. **Pragelato isn't joined to the Via Lattea.** Its ski area holds a single 0.3 km run that touches nothing. Check its lifts and pistes in OpenStreetMap. [001](decisions/001-join-touching-ski-areas.md)
14. **Shiga Kogen comes out as two joined domains.** The Yokoteyama end doesn't touch the rest in the data. [001](decisions/001-join-touching-ski-areas.md)
