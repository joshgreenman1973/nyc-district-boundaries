# The overlapping city

An interactive map of **every significant district boundary in New York City** — 23 layers, 8,529 individual district polygons — that you can overlay and compare. One patch of sidewalk sits inside a community board, a City Council district, a police precinct, a fire battalion, a school district, three legislative districts and more, all at once; this tool lets you switch any combination on and off and see where they cut across each other.

**Live map:** https://joshgreenman1973.github.io/nyc-district-boundaries/

## Layers

| Group | Layers |
|---|---|
| Foundational | Borough boundaries |
| City government | Community districts / boards, City Council districts, Community school districts |
| Public safety | Police precincts, Fire battalions, Fire divisions, Fire companies |
| City services | Sanitation districts, Health center districts, Health areas, Business improvement districts, Commercial waste zones |
| Emergency | Hurricane evacuation zones |
| State & federal | State Assembly, State Senate, Congressional, Election districts |
| Statistical & neighborhood | Neighborhood tabulation areas, Community district tabulation areas, Census tracts (2020), ZIP code tabulation areas |
| Preservation | Historic districts |

## How it works

- **Data:** official GeoJSON from [NYC Open Data](https://opendata.cityofnewyork.us/), mostly published by the Dept. of City Planning. Full source table on the [methodology page](https://joshgreenman1973.github.io/nyc-district-boundaries/methodology.html).
- **Base map:** boroughs are drawn as the "land"; there are no external map tiles, so the map is self-contained and loads instantly.
- **Rendering:** Leaflet. Each layer loads lazily on first toggle and draws as a distinct colored outline.
- **Opens populated:** the map loads with the city's ~10 main district systems on (`"default": true` in `scripts/layers.json`); "Show all" adds the granular statistical layers, "Hide all" clears.
- **Pinpoint lookup:** search any address (NYC City Planning GeoSearch autocomplete, free, no key) or click the map; a card lists every district that spot falls into, with a copy-as-text button.
- **Shareable links:** active layers and the dropped pin live in the URL hash (`#l=council,police&p=40.748,-73.985`), so any view can be shared as a link.
- Geometry is simplified for speed and labels are generated from source codes — treat exact edges as approximate.

## Rebuild

```bash
python3 scripts/build.py
```

Downloads each dataset, normalizes one label per feature, simplifies geometry with [mapshaper](https://github.com/mbloch/mapshaper), and writes `docs/data/*.json` plus `docs/data/manifest.json` (which drives the toggle panel). Layer definitions: `scripts/layers.json`.

Built with Claude Code.
