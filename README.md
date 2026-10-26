# Behind Australia's literary shortlists

A FIT3179 Data Visualisation 2 dashboard about publisher visibility in the 2024–2026 Prime Minister’s Literary Awards and Stella Prize lists. The page contains eleven Vega and Vega-Lite charts, including three geographic views.

## View locally

Run `python3 -m http.server 8000` in this folder, then open `http://localhost:8000/`. A local web server is needed because the specifications load CSV and GeoJSON files. The published dashboard is at [freshflick.github.io/FIT3179_A2](https://freshflick.github.io/FIT3179_A2/).

## Files

- `index.html`: story text, chart containers, and the `vegaEmbed` calls that load each JSON specification with the chart action menu enabled.
- `css/styles.css`: responsive layout and chart cards.
- `charts/section1`–`charts/section4`: all Vega and Vega-Lite chart specifications. The first three section folders contain the non-map charts; the fourth contains the three maps.
- `data/`: award tables, cited publisher contact locations, derived city/state/hex summaries, and simplified official state outlines.
- `data/map_methodology.md`: geographic sources, count method, and limitations.
- `scripts/build_geography.py` and `scripts/build_award_hex_map.py`: reproducible award-map summaries and hex-grid preparation.

## Data sources

- [Creative Australia, Prime Minister’s Literary Awards](https://www.creative.gov.au/news-events/events/prime-ministers-literary-awards), 2024–2026; individual book source links are in `data/pmla_2024_2026.csv`.
- [Stella Prize](https://stella.org.au/prize/), 2024–2026.
- [Australian Bureau of Statistics ASGS 2021 state boundaries](https://www.abs.gov.au/statistics/standards/australian-statistical-geography-standard-asgs/edition-3-july-2021-june-2026/access-and-downloads/digital-boundary-files).
- Publisher and coordinate source URLs are recorded for each of the 26 mapped publishers in `data/publisher_contact_locations.csv`.

The maps locate documented publisher contact metro areas for 86 of 90 PMLA-listed books and all 18 winners. They do not locate authors or book settings or trace book movements.

## Visual encodings

The heatmap uses a rose scale for publisher-by-category counts; the hex map uses green for distinct publisher contacts per cell; the metro circle map uses blue for listed books; the state map uses copper for the winner share among mapped listed books. Stella genre groups keep the same categorical colours in the year grids and the longlist-to-winner flow. The hex slider filters coloured cells by publisher count without changing the source data. A geographic flow map is not used because these sources do not establish book movements between places.
