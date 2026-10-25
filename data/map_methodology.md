# Geography and count method

The three maps use the same **65 Prime Minister’s Literary Awards (PMLA) books** associated with the ten publishers that appear most often in the 2024–2026 PMLA book table. A winner is counted once as a listed book and once in the winner subset. The other 25 PMLA books have publishers outside this top-ten group and are not plotted in these maps.

## Sources

- Award books and outcomes: [Creative Australia, Prime Minister’s Literary Awards](https://www.creative.gov.au/news-events/events/prime-ministers-literary-awards). The source URL for each book appears in [`pmla_2024_2026.csv`](pmla_2024_2026.csv).
- Publisher office cities: each row in [`publisher_office_locations_top10.csv`](publisher_office_locations_top10.csv) has the publisher’s own office/about-page source. Publishers with several offices are represented by **one selected documented office**. These locations are not author residences, book settings, or evidence that a book physically travelled to an award venue.
- Metro reference coordinates: [GeoNames city coordinates](https://www.geonames.org/au/largest-cities-in-australia.html), with source URLs in the office table. The circle map places each selected publisher office at its metro reference point, rather than claiming a precise building coordinate.
- State outlines: [Australian Bureau of Statistics, ASGS Edition 3 (2021) States and Territories digital boundaries](https://www.abs.gov.au/statistics/standards/australian-statistical-geography-standard-asgs/edition-3-july-2021-june-2026/access-and-downloads/digital-boundary-files). [`abs_states_2021.geojson`](abs_states_2021.geojson) is a simplified version of the official GDA2020 shapefile, with small offshore islands omitted for legibility. The boundary is geographic source data; the map counts come from the award and office tables.

## Map encodings

1. **Proportional-symbol map:** join each top-ten publisher in the PMLA table to its documented office metro area. Count its listed books, then sum across publishers at the same metro reference coordinate. Circle area shows the summed count.
2. **State choropleth:** use the office state from that same join. Count books with outcome `Winner` in each state. States with no selected top-ten publisher office are grey; grey does not mean no publishing or no winners there. The hover also shows the listed-book denominator. Counts are in [`publisher_office_state_summary.csv`](publisher_office_state_summary.csv).
3. **State tile map:** count listed books from the same join by award year and office state. Tile positions form a schematic layout, not geographic coordinates or land area. Use the slider to filter the year. Counts are in [`publisher_office_state_year.csv`](publisher_office_state_year.csv).

The derived CSVs and simplified boundaries are reproducible with [`../scripts/build_geography.py`](../scripts/build_geography.py) and the official ABS States and Territories shapefile ZIP. The script uses only Python’s standard library. The script’s geographic simplification keeps source vertices and does not change the underlying count data.

I have not used a flow map because the award and office sources do not document origin-to-destination movements. Drawing links between cities would imply movements that the data cannot establish.
