# Behind Australia's literary shortlists

A FIT3179 Data Visualisation 2 dashboard about publisher visibility in the 2024–2026 Prime Minister’s Literary Awards and Stella Prize lists. The geographic section extends the PMLA selection to 2022–2026. The page contains Vega and Vega-Lite charts, including Sydney and Melbourne contact-bin maps, a national location map that zooms into both cities, and a state choropleth.

## View locally

Run `python3 -m http.server 8000` in this folder, then open `http://localhost:8000/`. A local web server is needed because the specifications load CSV and GeoJSON files. The published dashboard is at [freshflick.github.io/FIT3179_A2](https://freshflick.github.io/FIT3179_A2/).

## Files

- `index.html`: story text, chart containers, and the `vegaEmbed` calls that load each JSON specification with the chart action menu enabled.
- `css/styles.css`: responsive layout and chart cards.
- `charts/section1`–`charts/section4`: all Vega and Vega-Lite chart specifications. The first three section folders contain the non-map charts; the fourth contains the maps.
- `data/`: award tables, cited publisher contact locations, derived city/state/hex summaries, and simplified official state outlines.
- `data/map_methodology.md`: geographic sources, count method, and limitations.
- `scripts/build_extended_pmla.py`, `scripts/build_geography.py`, `scripts/build_award_hex_map.py`, `scripts/prepare_suburb_boundaries.py`, and `scripts/build_city_maps.py`: reproducible award and map preparation.
- `scripts/build_stella_outcome_alluvial.py`: regenerates the Stella progression chart, including books that stop at each stage.

## Data sources

- [Creative Australia, Prime Minister’s Literary Awards](https://www.creative.gov.au/news-events/events/prime-ministers-literary-awards), 2022–2026. The main story uses 2024–2026; the maps include [publisher-attributed 2022–2023 records](data/pmla_2022_2023_geography.csv).
- [Stella Prize](https://stella.org.au/prize/), 2024–2026.
- [Australian Bureau of Statistics ASGS 2021 state boundaries](https://www.abs.gov.au/statistics/standards/australian-statistical-geography-standard-asgs/edition-3-july-2021-june-2026/access-and-downloads/digital-boundary-files).
- Publisher and coordinate source URLs are recorded for each of the 33 mapped publishers in `data/publisher_contact_locations.csv`; locality centroids come from [OpenStreetMap contributors](https://www.openstreetmap.org/copyright). City land shapes come from [ABS 2021 Suburbs and Localities](https://geo.abs.gov.au/arcgis/rest/services/ASGS2021/SAL/MapServer/0).

The maps locate documented publisher contact localities for 135 of 144 publisher-attributed PMLA shortlist records and all 30 winners across 2022–2026. They do not locate authors or book settings or trace book movements.

## Visual encodings

The heatmap uses a rose scale for publisher-by-category counts; the city bins use green for distinct publisher contacts per cell; the city and metro circle maps use blue for listed-book records; the state map uses copper for the winner share among mapped records. Stella genre groups keep the same categorical colours in the year grids and the longlist-to-winner alluvial. A geographic flow map is not used because these sources do not establish book movements between places.
