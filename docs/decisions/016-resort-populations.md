# 016. Resort populations: published bed counts as the reference

**Status:** Open. The reference figures are gathered; the approach is still to be decided.

**Code today:** [busyness/villages.py](../../busyness/villages.py) (`skiers = lift capacity ÷ LIFTS_PER_HOUR`), [busyness/params.py](../../busyness/params.py) (`LIFTS_PER_HOUR = 3.5`).

## Context

A domain's skiers are its total lift capacity ÷ 3.5 rides an hour (004). They are shared among villages by the lift capacity leaving each one (008). Two problems follow (GitHub #5 and #6, known issue 17):

- **The total is assumed, not measured.** It scales with lift capacity, so a domain with lots of lifts gets lots of skiers, whatever its beds. The model's own flows imply only about half that many skiers on the hill at once (Little's law).
- **The shares follow lifts, not beds.** A village with one big gondola gets many skiers, even if few people stay there. Overture building counts don't fix this: Val Thorens has 15 buildings within 500 m of its point, Encamp 573 and Le Monêtier 1,013.

Before choosing a replacement, we need something to judge it against. Resorts publish bed counts (*lits touristiques*), so this record collects them as the reference.

## Reference figures

"All beds" includes second homes that are seldom let (*lits froids*). "Registered" counts only hotels and tourist apartments. "n.d." means the source gives no date.

| Domain | Area | Beds | Counts | Year | Source |
|---|---|---|---|---|---|
| Les Trois Vallées | Val Thorens | 25,543 | all (tourist office) | 2022 | [Hospitality-On](https://hospitality-on.com/fr/montagne/la-plus-haute-station-de-ski-deurope-fete-ses-50-ans); 22,500 per [skiresort.info](https://www.skiresort.info/ski-holiday-in/val-thorens-202/) |
| Les Trois Vallées | Les Menuires and Saint-Martin-de-Belleville | 30,308 | all | 2014 | [Savoie Mont Blanc](https://www.savoie-mont-blanc.com/?p=688097) |
| Les Trois Vallées | Vallée des Belleville (both of the above) | 60,000–74,000 | all | n.d. | [mon-sejour-en-montagne](https://www.mon-sejour-en-montagne.com/actualites/savoie-ou-haute-savoie-qui-est-le-plus-touristique-on-fait-le-match/): 74,000 from the observatory, 60,000 from the mayor |
| Les Trois Vallées | Vallée de Méribel | 39,720 | all; 34% let commercially, 12% let by owners, 54% cold | c. 2022 | [Mairie des Allues](https://mairiedesallues.fr/wp-content/uploads/2022/12/413-agir-pour-optimiser-loccupation-des-lits.pdf) |
| Les Trois Vallées | Courchevel | about 40,000 | unclear | n.d. | [Guide Tourisme France](https://www.guide-tourisme-france.com/TOURISME/tourisme-courchevel-2129.htm) (weak source) |
| Tignes – Val d'Isère | Tignes | 34,475 | all | n.d. | [Alti-Mag](https://www.alti-mag.com/stations/tignes); 30,000 per [Cirkwi](https://www.cirkwi.com/en/point-interet/1328798-station-de-tignes) |
| Tignes – Val d'Isère | Val d'Isère | 25,800 | commune | n.d. | [Custup](https://www.custup.com/retour-experience-val-isere-tourisme-unification-donnees-deploiement-cdp/); over 33,000 per [france-voyage](https://www.france-voyage.com/cities-towns/val-d-isere-29658.htm) |
| Serre Chevalier | The whole valley, Briançon included | 52,784 | all | 2023 | [Serre Chevalier tourist office](https://www.serre-chevalier.com/sites/default/files/2023-05/SCV_VALLEE_REALISE_H23.pdf): Monêtier, Villeneuve and Chantemerle together have about 4× Briançon's beds; 1.56 M nights in winter 2022–23 |
| Grandvalira | Canillo parish (Soldeu, El Tarter, Canillo) | 6,091 | registered | n.d. | [La Ciutat](https://laciutat.cat/laciutatandorra/andorra-perd-mes-600-llits-en-hotels-apartaments-turistics_889455_102.html); 6,865 per [Bondia](https://www.bondia.ad/societat/andorra-disposa-de-46-590-places-d-allotjament-disponibles-en-363-establiments) |
| Grandvalira | Encamp parish (Encamp, Pas de la Casa) | 5,823 | registered | n.d. | [La Ciutat](https://laciutat.cat/laciutatandorra/andorra-perd-mes-600-llits-en-hotels-apartaments-turistics_889455_102.html) |
| Grandvalira | All of Andorra | 42,201 | registered | n.d. | [La Ciutat](https://laciutat.cat/laciutatandorra/andorra-perd-mes-600-llits-en-hotels-apartaments-turistics_889455_102.html) |

No split was found below the commune or parish, for example Soldeu against El Tarter, or Pas de la Casa against Encamp.

## Today's model against the reference

The table shows the modelled skiers (lift capacity ÷ 3.5, by village) for each area, summed over its villages or sectors.

| Area | Beds | Modelled skiers | Skiers per bed |
|---|---|---|---|
| Val Thorens | 25,543 | 12,671 | 0.50 |
| Les Menuires and Saint-Martin | 30,308 | 19,616 | 0.65 |
| Vallée de Méribel (Mottaret included) | 39,720 | 26,010 | 0.65 |
| Courchevel (Moriond included) | ~40,000 | 15,441 | 0.39 |
| Tignes | 34,475 | 21,713 | 0.63 |
| Val d'Isère | 25,800 | 15,553 | 0.60 |
| Serre Chevalier | 52,784 | 18,928 | 0.36 |
| Grandvalira (Canillo and Encamp) | 11,914 registered | 25,154 | 2.11 |

**What this says, before any decision:**

- **The French resorts sit at 0.4–0.65 skiers per bed.** This is plausible: peak occupancy below 100%, and some guests who don't ski or aren't on the hill. The rule of capacity ÷ 3.5 is roughly right in total for these resorts.
- **Courchevel and Serre Chevalier are low.** Courchevel's figure is weak. Serre Chevalier's beds include Briançon, a town of permanent residents as well as visitors.
- **Grandvalira is the outlier, at twice its registered beds.** Second homes aren't counted. Day skiers come from Andorra la Vella and Escaldes, which hold much of Andorra's 42,000 beds, and from Spain and France. Beds in the domain's own parishes would undercount it badly.
- **Shares within a domain differ more than totals.** Val Thorens has as many beds as Val d'Isère, or more, but fewer modelled skiers, because its lift capacity is shared with Les Menuires through Saint-Martin's sectors.

**Reviewed with the project owner (2026-11-03): the totals look explainable.** Serre Chevalier is low because Briançon is a real town, with many houses that are homes, not visitors' beds. Tignes, by contrast, is purely a resort. Grandvalira is high because of car traffic: day skiers fill big car parks such as Pas de la Casa's. Day visitors are a separate problem, known issue 23, not a reason to change the totals here.

## Approaches to evaluate

1. **Building volume** (Overture footprint × height) shares the domain's skiers among villages. Counts of buildings fail (see above). Volume may do better, because Val Thorens is a few very large blocks.
2. **Bed counts directly,** where published, with building volume to split a commune among its villages. This is accurate where figures exist, but most domains have none.
3. **Lift capacity for the total, buildings for the shares.** The total stays as today, which the table supports for French resorts, and buildings decide where skiers start.

Each would be judged against the table above: per-area shares within a domain first, then totals. Day visitors (Andorra, and city-side resorts generally) need a separate source of skiers whichever approach is chosen.

## Open questions

- How much of a bed count is on the hill on a busy day? Occupancy × the share who ski × the share on the hill at once (known issue 17).
- Should cold beds count fully, or be discounted, as Méribel's split allows?
- How should day visitors be modelled, and from where (valley towns, road access)?
