# Observations from skiing

First-hand observations from the project owner's ski trips. There's no usage data for pistes or lifts, so these are the only ground truth the busyness model ([issue #3](https://github.com/AntonyM71/ski-altitude-explorer/issues/3)) is checked against. How the model currently compares is in decision record [011](decisions/011-validate-with-observations.md).

Each observation says when it applies (morning, during the day or end of day), because a run can be quiet all day and packed at close. Some are recollections from trips a while ago. Add new ones as they come up, and don't edit old ones to fit the model.

## Les Trois Vallées

Not skied for a while.

- **Plein Sud** (Val Thorens) is usually full in the mornings, often with a decent queue.
- **Funitel 3 Vallées** (Val Thorens) is often completely full at the start of the day, partly with commuters. To reach it from the village you take **Plein Sud**, or **Pionniers**. Both are usually busy in the morning, and some parts of Val Thorens can't easily reach Pionniers.
- **Lac de la Chambre** being busy makes sense.
- Not convinced that **Ours** should rank where the model puts it against **Sittelle**.
- **Plan des Mains** is just a place where some lifts start, not a village with its own population.
- **The Cascades piste** near Val Thorens is mapped only as an area, with no line down it (prompted issue #2).

## Tignes–Val d'Isère

- **Face de Bellevarde** (black) is often less chewed up than the **Joseray** red alongside it, so much that the owner often picks the black as the easier run.
- **Henri**, **Lac** and **Combe** are busy.
- **Edelweiss** and **Combe** carry the Tignes → Val d'Isère traffic.
- Skiers avoid flat runs like the **Traversée du Laisinant**.
- **Piste M** is busy at the end of the day, with people coming down to get back to their accommodation in Val d'Isère. During the day it isn't especially busy: people generally stick to one side or the other.
- **Solaise and Olympique** gondolas: at the end of the day a share of people ride them down to Val d'Isère to get home, rather than ski the more difficult, low and possibly icy runs.
- **Tovière** (Tignes): people like riding it down to get home, as an alternative to the difficult black or a detour into Val Claret.
- **Prorel** too (Serre Chevalier): a fair number ride it down, but it's "some people", certainly not full lifts with lines. The same is likely true of the others.
- **Lac / Parc à Moutons** heads down into the top of the Solaise gondola. (In OpenStreetMap it's drawn the other way, from the gondola's top down towards the back side; the Pim and Pam magic carpets carry people back up to the gondola's top.)
- **A trip staying in Tignes:**
  - Day 1: stayed in the Tignes / Val Claret bowl, back to Tignes.
  - Day 2: went to La Daille, skied the routes there, came back via Val Claret.
  - Day 3: went over to Val d'Isère, skied around there, came back via La Daille and straight down **Johan Clarey** into Tignes.

  So: two days out of three away from the home area, and a different route home each time.

## Serre Chevalier

- **Pelvoux** is busy: the whole Prorel (Briançon) population comes off it to get into the main Serre Chevalier bowl.
- **Traverse** being busy makes sense.
- From Le Monêtier, presumably all the lifts head over towards **Cucumelle** to get into the bowl. (Not stayed there.)
- The **old Pontillas** lift, a standing gondola, didn't usually get busy: it went to a not very useful place, and the modern **Casse du Bœuf** six-seater next to it goes somewhere much more useful. The **new Pontillas** is much better located.
- **Fréjus** is a tiny village with only a few houses, possibly not a ski place at all; it shouldn't count as a ski village.
- Short black sections such as the **Pylônes** are fine for confident intermediates, who jump down a bit and get back onto the blue or green.
- **Pylônes** is crossed at several points by **3 Croix**, and also by **Mézies** and **Lièvre Blanc**, so you can bail out at any time if you're not feeling it. That makes it less intimidating than "here is 2 km of black with no other option".
- **Luc Alphand** (black) shouldn't be especially busy in the evening rush: it's a black with often difficult conditions, often more so than **Casse du Bœuf**. It should be quieter than **Briance**.
- **Going home to Chantemerle** at the end of the day, people most likely ride the **Ratier** gondola down, or ski **Briance**, the long green that goes down to Chantemerle, rather than Luc Alphand. (Both Briance and Luc Alphand end at Chantemerle.)
- **Prorel**: at the end of the day a share of people ride the gondola down to get home, rather than ski difficult, low and possibly icy runs.

## Grandvalira

- **Soldeu** is a small village, with a gondola and a six-seater chair. The **Soldeu gondola** is usually busy in the morning, with people going up from Soldeu into the resort; the owner walked straight to it from their accommodation. Busy, but not 20-minute queues.
- **Grau Roig** is a small place on the way between Pas de la Casa and Soldeu: a busy thoroughfare, not a village.
- **Gall de Bosc** being busy makes sense (a beginner area).

## How skiers behave, in general

- **People don't build lifts for nobody.** A lift's load usually reflects the capacity provided, though not always: layouts change, and some ideas don't pay off (the old Pontillas).
- **A village's access lifts are sized for its own population,** not for the terrain above it (Le Fornet's cable car).
- **Nursery slopes and their lifts are for ski school.**
- **People go home to where they came from.** You don't start in Tignes le Lac and finish in Val d'Isère. The evening is like the morning, except everyone starts on the mountain instead of in their village.
- **Skiers mostly stick to one side** during the day, and head somewhere or ski all the runs off a lift rather than lapping one run, though people do lap a nice run.
- **Commuting depends on the domain.** In a big domain such as Les Trois Vallées, Tignes–Val d'Isère or Paradiski you might go somewhere else most days. In a small resort you don't make a "mission" to the other side; you just end up there.
- **Black runs:** confident intermediates don't mind a short black pitch with an easy way out, and a well-skied black can be less chewed up than the red beside it. What makes a black daunting is how long you're committed to it without a way out.
- **Flat runs** (traverses, cat tracks) are avoided where there's a choice.
- **Riding down at the end of the day.** Where the way home is hard, low or icy, a share of people take a gondola or cable car down rather than ski it, notably Prorel (Serre Chevalier) and Solaise and Olympique (Val d'Isère).
- **End-of-day conditions** make difficult runs, especially low blacks, harder still, so they're quieter in the evening rush than their daytime use suggests.
- **Skied-out runs.** A run that's been busy through the morning and the day gets skied out, moguled or chopped up, so it takes longer and feels harder than when it was fresh. Joseray, for example, may be full of moguls by then, which makes the Face de Bellevarde relatively more appealing.

## Linked domains

- The **Via Lattea** (Milky Way) is one domain: Sestriere, Sauze d'Oulx, Claviere, Cesana Torinese and Montgenèvre are all linked (prompted issue #1). Wikipedia also lists Pragelato and gives "more than 400 km".
