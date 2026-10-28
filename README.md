# Ski Altitude Explorer

Ski domains ranked by how much of their piste sits above a snow line you choose.

A resort can advertise 250 km of pistes that are mostly low, while a smaller one has far more of its skiing up high. This site measures piste length by altitude for every ski area in [OpenSkiMap](https://openskimap.org), to find domains that are both big and likely to have snow early and late in the season.

**Live site:** https://antonym71.github.io/ski-altitude-explorer/

## What's on the page

The page is split in two.

**Left: every domain that matches your filters** (region, countries, minimum size, linked domains, piste grades)

- **Size against high piste**: total piste km against km above the snow line, on one square scale so the diagonal is a true 45°. Dots are coloured by median altitude, and dotted lines mark 25%, 50% and 75% of piste above the snow line. Scroll to zoom, drag to pan.
- **Index**: the same domains ranked by km above the snow line, with an altitude profile strip per row.

**Right: the selected domain**

- **Title card**: km above the snow line, share, measured km, median altitude and top lift.
- **Piste map** (MapLibre): pistes in grade colours, faded below the snow line, over altitude-coloured relief with hillshading. Lifts are drawn in piste-map convention. Click a piste for its elevation and gradient profile.
- **Piste km by altitude**: a histogram in 100 m bands, as one total or stacked by grade. Drag the orange line to move the snow line.

On a computer the piste map fills the page behind frosted glass windows. Each window can be minimised to its title bar or expanded to full screen, and the map's own expand button moves the other windows aside. The snow line can be changed from any expanded view.

## How it's measured

1. Every operating downhill piste in OpenSkiMap is a line with an altitude at each vertex.
2. Each line is split into vertex-to-vertex segments. Each segment's horizontal length is measured with `pyproj.Geod`.
3. The length is added to the 100 m altitude band of the segment's midpoint, for every ski area the run belongs to.
4. A domain's total is the sum of its bands, and "km above the snow line" is the sum of the bands at or above it. Because the full histogram is stored, the snow line can move in the browser without rebuilding.

**Excluded:**

- ski routes, freeride and backcountry runs;
- pistes mapped as areas rather than lines (about 11,000 runs), since they have no length;
- runs with no ski area.

Elevation spikes, where a segment is steeper than about 63°, and implausible negative elevations are dropped.

**Grades** map OpenSkiMap's difficulty onto European colours: novice is green, easy blue, intermediate red, and advanced, expert or extreme black. Anything else is ungraded. North American and Japanese conventions differ, so a blue there isn't the same as a blue in the Alps.

**The snow line** is a single altitude. It doesn't account for slope aspect, latitude, glaciers or snowmaking, and snowmaking isn't in the data.

### Why sizes differ from resort brochures

The figures here are usually lower than published piste km, sometimes by a lot. Resorts measure in different ways:

- some count ski routes;
- some measure length along the slope rather than on the map;
- some count wide pistes as several runs;
- some quote a whole lift pass that covers unlinked valleys.

This site uses the horizontal length of what is mapped in OpenStreetMap, measured the same way everywhere. Use it to compare domains with each other, not with brochures.

### Linked domains and pass networks

Domains come from OpenSkiMap, which lists both linked areas (Les Trois Vallées) and the resorts inside them (Méribel, Val Thorens). The build marks area B as a sub-area of A when at least 80% of B's runs are also in A. "Linked domains" then shows just the top level.

Lift-pass networks of unlinked valleys would otherwise top the ranking. These are listed by hand in `PASS_NETWORKS` in `build_stats.py` (currently Dolomiti Superski and Ski amadé). They are never treated as a parent, and are hidden in the linked view.

### Regions

Each domain gets one region from its first listed country and its centre point (`region_of` in `build_stats.py`). Europe is split into mountain regions such as the Alps, Pyrenees, Nordics and Carpathians. The Alps use a rough bounding box, so the Jura falls under Central European Uplands.

## Running it locally

You need [uv](https://docs.astral.sh/uv/).

```sh
uv run python fetch.py          # download OpenSkiMap runs, ski areas and lifts into data/raw/ (about 1 GB, once)
uv run python build_stats.py    # build data/ski_area_stats.json and data/runs/ (about a minute)
uv run python -m http.server    # then open http://localhost:8000/
```

`fetch.py` reuses files it has already downloaded. Pass `--force` to download them again. If the connection drops partway through a file, it retries that file up to five times. OpenSkiMap rebuilds its exports daily, so there's no need to re-download often.

## Project layout

| File | What it does |
|---|---|
| `fetch.py` | Downloads `runs.geojson`, `ski_areas.geojson` and `lifts.geojson` from `tiles.openskimap.org` into `data/raw/`. |
| `build_stats.py` | Streams the GeoJSON line by line. It writes `data/ski_area_stats.json` (about 2.4 MB): for each area, its altitude histogram, per-grade histograms, sub-area parent, region, top lift and other figures. It also writes `data/runs/<area id>.json` (34 MB in total), the simplified run and lift lines the map loads for one domain at a time. |
| `index.html` | The whole site: a static page with no build step. It loads MapLibre GL from unpkg and fonts from Google Fonts. |
| `.github/workflows/deploy.yml` | Rebuilds and deploys to GitHub Pages. |

`data/` is git-ignored. The data is never committed; the workflow builds it fresh on every run.

## Deployment

The workflow runs:

- on every push to `main`;
- every Monday at 04:17 UTC;
- on demand, from **Run workflow** in the Actions tab.

Each run downloads the OpenSkiMap data, runs `build_stats.py`, copies `index.html` and `data/` into a temporary site folder, and deploys it with GitHub Pages. GitHub Pages is set to deploy from **GitHub Actions** in the repository settings.

`build_stats.py` stops with an error if it finds fewer than 3,000 ski areas or no Les Trois Vallées, so a broken download can't replace the live site.

The raw OpenSkiMap download is cached for the current ISO week, so pushes during the week reuse it instead of downloading about 1 GB again. The Monday run falls in a new week and fetches fresh data. A build that runs for more than 45 minutes is stopped.

Pages can be shared with their current view: the address bar keeps the selected domain, snow line, filters, grade switches, histogram view, sort, plot zoom and map position in the query string, and the **Share** button copies that link (or opens the share sheet on phones).

## Known issues and next steps

- **Some linked domains aren't grouped in the data.** The Via Lattea (Montgenèvre, Claviere, Sansicario, Sestriere, Sauze d'Oulx) is one example, so its resorts are ranked separately. The plan is to detect links automatically where runs or lifts in different areas join, and to name known domains.
- **Pistes mapped as areas aren't counted**, which undercounts open bowls and some glacier skiing.
- **A domain's region comes from its first listed country,** so a few cross-border domains sit in a neighbouring region.
- **Grade colours use the European convention everywhere.**
- **One theme:** the glass style is dark only.

## Fixing or adding data

All pistes and lifts come from [OpenStreetMap](https://www.openstreetmap.org), via [OpenSkiMap](https://openskimap.org). If a piste is missing, misnamed or has the wrong grade, fix it in OpenStreetMap. The [piste mapping guide](https://wiki.openstreetmap.org/wiki/Piste_Maps) explains the tagging. Changes reach OpenSkiMap within about a day, and this site picks them up at the next weekly rebuild.

## Credits and licences

- **Piste, lift and ski area data:** © [OpenSkiMap](https://openskimap.org) and [OpenStreetMap contributors](https://www.openstreetmap.org/copyright), under the [Open Database Licence (ODbL)](https://opendatacommons.org/licenses/odbl/).
- **Map tiles:** [OpenFreeMap](https://openfreemap.org) and [OpenMapTiles](https://openmaptiles.org).
- **Terrain:** [AWS Terrain Tiles](https://registry.opendata.aws/terrain-tiles/).
- **Map rendering:** [MapLibre GL JS](https://maplibre.org).
- **Reference:** [dhimmel/openskistats](https://github.com/dhimmel/openskistats) was a useful reference for working with OpenSkiMap data.

The code doesn't have a licence yet.
