"""Build compact Vega-Lite close-ups from ABS 2021 suburb boundaries.

The checked-in ABS GeoJSON files are selected suburb polygons returned by the
official ASGS2021 SAL ArcGIS service. They are geographic context, not data
about the awards. Award counts come only from publisher_contact_locality_summary.csv.
"""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

CITIES = {
    "sydney": {"label": "Sydney", "center": [151.12, -33.87], "scale": 70000,
               "highlight": ["Crows Nest", "Parramatta"],
               "extent": [150.8, -34.05, 151.4, -33.65],
               "longitudes": [150.9, 151.0, 151.1, 151.2, 151.3],
               "latitudes": [-34.0, -33.9, -33.8, -33.7]},
    "melbourne": {"label": "Melbourne", "center": [144.99, -37.84], "scale": 70000,
                  "highlight": ["Collingwood", "Southbank"],
                  "extent": [144.7, -38.08, 145.3, -37.60],
                  "longitudes": [144.8, 144.9, 145.0, 145.1, 145.2],
                  "latitudes": [-38.0, -37.9, -37.8, -37.7]},
}


def specification(slug, config):
    city = config["label"]
    highlights = ", ".join(repr(name) for name in config["highlight"])
    left, bottom, right, top = config["extent"]
    grid = ([{"type": "Feature", "geometry": {"type": "LineString",
                                             "coordinates": [[longitude, bottom], [longitude, top]]},
              "properties": {}} for longitude in config["longitudes"]] +
            [{"type": "Feature", "geometry": {"type": "LineString",
                                             "coordinates": [[left, latitude], [right, latitude]]},
              "properties": {}} for latitude in config["latitudes"]])
    return {
        "$schema": "https://vega.github.io/schema/vega-lite/v5.json",
        "description": (f"Documented publisher-contact localities around {city} for "
                        "PMLA-listed books, 2022–2026. ABS 2021 suburb polygons provide "
                        "geographic context; circle area shows listed-book records."),
        "width": "container", "height": 400, "background": "#ffffff",
        "projection": {"type": "mercator", "center": config["center"],
                       "scale": config["scale"]},
        "layer": [
            {"data": {"url": f"data/abs_{slug}_suburbs_2021.geojson?v=2",
                      "format": {"type": "json", "property": "features"}},
             "mark": {"type": "geoshape", "fill": "#f1ede4", "stroke": "#d7ddd9", "strokeWidth": 0.32,
                      "clip": True}},
            {"data": {"values": grid},
             "mark": {"type": "geoshape", "fill": None, "stroke": "#bdd3da",
                      "strokeWidth": 0.55, "clip": True}},
            {"data": {"url": "data/publisher_contact_locality_summary.csv"},
             "transform": [{"filter": f"datum.map_city == '{city}'"}],
             "layer": [
                 {"mark": {"type": "circle", "color": "#286f91", "opacity": 0.86,
                           "stroke": "#ffffff", "strokeWidth": 1.7, "clip": True},
                  "encoding": {"longitude": {"field": "longitude", "type": "quantitative"},
                               "latitude": {"field": "latitude", "type": "quantitative"},
                               "size": {"field": "listed_books", "type": "quantitative",
                                        "title": "Listed books", "scale": {"domain": [0, 22],
                                                                     "range": [55, 1600]},
                                        "legend": {"orient": "bottom", "values": [1, 10, 20],
                                                   "symbolFillColor": "#286f91"}},
                               "tooltip": [
                                   {"field": "contact_locality", "type": "nominal",
                                    "title": "Contact locality"},
                                   {"field": "listed_books", "type": "quantitative",
                                    "title": "Listed books"},
                                   {"field": "winning_books", "type": "quantitative",
                                    "title": "Winners"},
                                   {"field": "publishers", "type": "quantitative",
                                    "title": "Publishers"},
                                   {"field": "publisher_names", "type": "nominal",
                                    "title": "Publisher names"}]}},
                 {"transform": [{"filter": f"indexof([{highlights}], datum.contact_locality) >= 0"}],
                  "mark": {"type": "text", "dy": -17, "font": "Arial", "fontSize": 12,
                           "fontWeight": "bold", "color": "#213b48", "clip": True},
                  "encoding": {"longitude": {"field": "longitude", "type": "quantitative"},
                               "latitude": {"field": "latitude", "type": "quantitative"},
                               "text": {"field": "contact_locality", "type": "nominal"}}}
             ]}
        ],
        "config": {"view": {"stroke": None, "fill": "#d9edf4"},
                   "legend": {"labelFont": "Arial", "titleFont": "Arial"}}
    }


def bin_specification(slug, config):
    """One geographic close-up of occupied 2 km publisher-contact cells."""
    city = config["label"]
    left, bottom, right, top = config["extent"]
    grid = ([{"type": "Feature", "geometry": {"type": "LineString",
                                             "coordinates": [[longitude, bottom], [longitude, top]]},
              "properties": {}} for longitude in config["longitudes"]] +
            [{"type": "Feature", "geometry": {"type": "LineString",
                                             "coordinates": [[left, latitude], [right, latitude]]},
              "properties": {}} for latitude in config["latitudes"]])
    return {
        "$schema": "https://vega.github.io/schema/vega-lite/v5.json",
        "description": (f"Distinct publishers of 2022–2026 PMLA-listed books in "
                        f"occupied 2 km equal-area cells around {city}. "
                        "Locations are sourced publisher-contact locality centroids."),
        "width": "container", "height": 340, "background": "#ffffff",
        "projection": {"type": "mercator", "center": config["center"],
                       "scale": config["scale"]},
        "layer": [
            {"data": {"url": f"data/abs_{slug}_suburbs_2021.geojson?v=2",
                      "format": {"type": "json", "property": "features"}},
             "mark": {"type": "geoshape", "fill": "#f1ede4", "stroke": "#d7ddd9", "strokeWidth": 0.32,
                      "clip": True}},
            {"data": {"values": grid},
             "mark": {"type": "geoshape", "fill": None, "stroke": "#bdd3da",
                      "strokeWidth": 0.55, "clip": True}},
            {"data": {"url": "data/pmla_publisher_contact_hex_bins.geojson?v=4",
                      "format": {"type": "json", "property": "features"}},
             "transform": [
                 {"calculate": "datum.properties.metro_areas", "as": "metro"},
                 {"calculate": "datum.properties.publishers", "as": "publishers"},
                 {"calculate": "datum.properties.listed_books", "as": "listed_books"},
                 {"calculate": "datum.properties.winning_books", "as": "winning_books"},
                 {"filter": f"datum.metro == '{city}'"}
             ],
             "mark": {"type": "geoshape", "stroke": "#ffffff", "strokeWidth": 1.3,
                      "opacity": 0.96, "clip": True},
             "encoding": {
                 "color": {"field": "publishers", "type": "ordinal", "legend": None,
                           "scale": {"domain": [1, 2, 3, 4],
                                     "range": ["#b5d9c7", "#7dbda2", "#3e9878", "#0f6652"]}},
                 "tooltip": [
                     {"field": "metro", "type": "nominal", "title": "Contact metro"},
                     {"field": "publishers", "type": "quantitative", "title": "Publishers"},
                     {"field": "listed_books", "type": "quantitative", "title": "Listed books"},
                     {"field": "winning_books", "type": "quantitative", "title": "Winners"}
                 ]}}
        ],
        "config": {"view": {"stroke": None, "fill": "#d9edf4"}}
    }


if __name__ == "__main__":
    for slug, config in CITIES.items():
        target = ROOT / f"charts/section4/publisher_{slug}_localities.vl.json"
        target.write_text(json.dumps(specification(slug, config), indent=2) + "\n")
        print(target.relative_to(ROOT))
        bin_target = ROOT / f"charts/section4/pmla_publisher_{slug}_hex.vl.json"
        bin_target.write_text(json.dumps(bin_specification(slug, config), indent=2) + "\n")
        print(bin_target.relative_to(ROOT))
