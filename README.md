# Australian Literary Awards starter

This is a small starting point for FIT3179 Data Visualisation 2. It is **not** the completed assignment: it has one chart and no maps yet. The full submission needs at least ten charts, three distinct map idioms, meaningful advanced idioms, and the story sections in your sketch.

## Open it in VS Code

1. Unzip the project and open the `literary-awards-starter` folder in VS Code (`File > Open Folder`).
2. In VS Code, select `Terminal > New Terminal`.
3. Run `python3 -m http.server 8000` from this folder.
4. Visit `http://localhost:8000/` in a browser. Stop the server with `Ctrl+C` in the terminal.

The web server is necessary because the chart loads a local JSON spec and CSV file. You do not need npm or React.

## Files

- `index.html`: page layout and one `vegaEmbed` call, adapted from the FIT3179 teaching example.
- `css/styles.css`: responsive page styling.
- `charts/publisher_counts.vg.json`: human-readable Vega-Lite chart specification.
- `data/pmla_2024_2026.csv`: 90 shortlisted or winning books, 2024–2026.
- `data/stella_2024_2026.csv`: 36 longlisted, shortlisted or winning books, 2024–2026.
- `data/miles_franklin_2022_titles.csv`: 88 titles in the State Library of NSW 2022 Miles Franklin list, all published in 2021. This file has no outcome field; do not treat it as a shortlist.

## Data and template sources

- Prime Minister’s Literary Awards: https://www.creative.gov.au/news-events/events/prime-ministers-literary-awards
- Stella Prize: https://stella.org.au/past-prize-winners/
- State Library of NSW Miles Franklin 2022 list: https://content-lists.sl.nsw.gov.au/tabular-list/miles-franklin-literary-award-2022
- Course template: https://github.com/FIT3179/Vega-Lite/tree/main/5_multiple_charts_html

When publishing your final work, add your own authorship/date and acknowledge AI assistance in your submission as required by the spec.
