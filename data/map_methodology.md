# Award geography: sources and count method

The main dashboard compares **2024–2026** Prime Minister’s Literary Awards
(PMLA) and Stella Prize lists. The geographic section extends the **PMLA
selection to 2022–2026**. This gives 144 book records with a named publisher:
90 from the [2024–2026 table](pmla_2024_2026.csv) and 54 from the
[2022–2023 extension](pmla_2022_2023_geography.csv). These are shortlist
records, including winners, rather than all submitted books or all Australian
literary awards.

The earlier extension draws from Creative Australia’s
[2022 winners and shortlistees](https://creative.gov.au/2022-prime-ministers-literary-awards-winners-shortlistees-and-judges)
and [2023 winners and shortlistees](https://creative.gov.au/2023-prime-ministers-literary-awards-winners-shortlistees-and-judges).
The 2022 page provides a publisher for 25 entries and the 2023 page for 29.
Entries without a published publisher field are excluded from the map
extension. Each CSV row keeps its original publisher label and page URL;
the `publisher_key` column merges clearly identified imprint or name variants
for the geographic join. The 2023 Australian history winner is verified by
[Creative Australia’s winner announcement](https://www.creative.gov.au/news-events/news/winners-2023-prime-ministers-literary-awards).
The checked-in extension can be rebuilt from saved plain-text versions of the
official pages with [the extraction script](../scripts/build_extended_pmla.py).

## Location evidence

The [publisher-contact table](publisher_contact_locations.csv) gives one
documented Australian locality for each of 33 publishers. It records the
publisher, parent company, institution or postal source for that locality.
Some sources identify an office, some a mailing address, and two only a
metro. A company can have more than one office; this table selects one
supported Australian contact for each publisher. These are **not** author
homes, book settings, sales, readership, or travel routes.

The longitude and latitude fields are centroids of the stated locality from
[OpenStreetMap contributors](https://www.openstreetmap.org/copyright), not
geocoded building entrances. Each row links the exact OSM object. The
Australia-wide city symbols use separate [GeoNames metro reference
points](https://www.geonames.org/AU/largest-cities-in-australia.html), because
their unit is the metro rather than the suburb. Little River is grouped with
Geelong following [City of Greater Geelong planning material](https://www.geelongaustralia.com.au/common/Public/Documents/8d9a8466b3d2832-gphs2024-summaryreport.pdf).
The state outlines derive from the
[ABS ASGS 2021 digital state boundaries](https://www.abs.gov.au/statistics/standards/australian-statistical-geography-standard-asgs/edition-3-july-2021-june-2026/access-and-downloads/digital-boundary-files).
The national GeoJSON is simplified for rendering. The Sydney and Melbourne
views use [ABS 2021 Suburbs and Localities (SAL) boundaries](https://geo.abs.gov.au/arcgis/rest/services/ASGS2021/SAL/MapServer/0)
queried for each metropolitan viewport and stored as compact local GeoJSON.
They provide real coastline and harbour shapes under a faint geographic grid.
Internal suburb boundaries are hidden to keep the small maps legible. The
boundaries are background geography; the award counts remain at documented
publisher contacts. The [preparation script](../scripts/prepare_suburb_boundaries.py)
rewinds the official GeoJSON polygons for Vega's spherical rendering convention.

There are **135 mapped book records from 33 publishers**, including all 30
winners. Nine records are unmapped. Four are from the 2024–2026 table:
Vagabond Press (two), Quemar Press (one), and Shearsman Books (one). Five older
records have no supported Australian contact for the publisher label:
Fomite, The Hare & Tortoise Books, Yandaarra Community Group, Virago, and
MIP. The last label appears on Creative Australia’s page for *A World in a
Shell*; [The MIT Press](https://mitpress.mit.edu/9780262047029/a-world-in-a-shell/)
publishes that edition. It is not assigned an Australian coordinate.
An author’s own location is never substituted for a missing publisher contact.

## What the maps count

1. **National equal-area bins:** one documented contact locality per publisher
   is placed into a 115 km radius hexagonal cell in a Lambert azimuthal
   equal-area projection. Colour counts distinct publishers with at least one
   book in the five-year selection. Nine of 225 displayed land cells contain
   contacts; the neutral cells provide national context. The slider changes
   the minimum publisher count shown in colour. The [derived GeoJSON](pmla_publisher_contact_hex_bins.geojson)
   also stores listed and winning records by cell.
2. **Sydney and Melbourne close-ups:** the location map's city controls, or
   clicking a national city symbol, switch
   from national metro totals to documented suburb centroids over ABS suburb
   geography. The plus and minus buttons adjust the city projection scale.
   Circle area counts listed-book records at the contact locality,
   and tooltips name the publishers. The close-ups separate multiple contacts
   that overlap in a national view. Sydney has 14 mapped publishers and 67
   listed records; Melbourne has 11 and 39. Their combined 106 records
   represent 78.5% of the 135 mapped records.
3. **National proportional symbols:** [the metro summary](publisher_contact_city_summary.csv)
   aggregates the same book records into eight areas. Sydney has 67,
   Melbourne 39, Brisbane 16, Broome five, Newcastle and Perth three each,
   and Geelong and Canberra one each. Circle area, not radius, follows the
   record count.
4. **State winner-share map:** [the state summary](publisher_contact_state_summary.csv)
   divides winning records by listed records associated with a publisher
   contact state. Queensland has five of 16 (31.2%), WA two of eight (25.0%),
   NSW 15 of 70 (21.4%), Victoria eight of 40 (20.0%), and ACT zero of one.
   States without mapped publisher contacts are neutral. These values describe
   **this award selection**, not publishers’ underlying success rates or the
   state where an author lives.

The city, locality and state summaries can be regenerated with
[`build_geography.py --counts-only`](../scripts/build_geography.py).
The national bins come from [`build_award_hex_map.py`](../scripts/build_award_hex_map.py).
Both use only Python’s standard library. Rebuilding the state boundaries
requires the official ABS state shapefile ZIP cited above.

Australia has many other literary awards with different categories, date
ranges, eligibility and public metadata. Their records are not added to the
PMLA map totals, because combining unlike shortlist fields or assigning
unsupported locations would make the count misleading.
