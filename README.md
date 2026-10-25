# Behind Australia's literary shortlists

A FIT3179 Data Visualisation 2 dashboard about publisher visibility in the 2024–2026 Prime Minister’s Literary Awards and Stella Prize lists. The page contains eleven Vega and Vega-Lite charts, including three geographic views.

## View locally

Run `python3 -m http.server 8000` in this folder, then open `http://localhost:8000/`. A local web server is needed because the specifications load CSV and GeoJSON files. The published dashboard is at [freshflick.github.io/FIT3179_A2](https://freshflick.github.io/FIT3179_A2/).

## Files

- `index.html`: story text, chart containers, and the `vegaEmbed` calls that load each JSON specification with the chart action menu enabled.
- `css/styles.css`: responsive layout and chart cards.
- `charts/section1`–`charts/section4`: all Vega and Vega-Lite chart specifications. The first three section folders contain the non-map charts; the fourth contains the three maps.
- `data/`: award tables, publisher office references, simplified official state outlines, and a prepared historical public-library location table and hex grid.
- `data/map_methodology.md`: geographic sources, count method, and limitations.
- `scripts/build_geography.py` and `scripts/build_library_map.py`: reproducible state and hex-grid preparation.

## Data sources

- [Creative Australia, Prime Minister’s Literary Awards](https://www.creative.gov.au/news-events/events/prime-ministers-literary-awards), 2024–2026; individual book source links are in `data/pmla_2024_2026.csv`.
- [Stella Prize](https://stella.org.au/prize/), 2024–2026.
- [Australian Bureau of Statistics ASGS 2021 state boundaries](https://www.abs.gov.au/statistics/standards/australian-statistical-geography-standard-asgs/edition-3-july-2021-june-2026/access-and-downloads/digital-boundary-files).
- [Carl Higgs, Australian public lending library locations (2016–2018), RMIT University](https://doi.org/10.25439/rmt.21944840.v1). The library map is explicitly a historical comparison. Its adapted files retain the [CC BY-SA 4.0 licence](data/LICENSE_public_libraries.md).

The maps locate documented publisher office metro areas and historically recorded public libraries. They do not locate authors or book settings, trace book movements, or identify which award titles libraries held.
