"""Build city map specs using the reference dashboard's geographic structure.

Award counts come from publisher_contact_locality_summary.csv and
pmla_publisher_contact_hex_bins.geojson. ABS state boundaries provide map context.
"""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

CITIES = {
    "sydney": {
        "label": "Sydney",
        "boundaries": "data/abs_sydney_suburbs_2021.geojson",
        "center": [151.02, -33.845],
        "fit": [[150.65, -34.12], [151.39, -33.57]],
        "graticule_extent": [[149.65, -35.12], [152.39, -32.57]],
        "graticule_step": [0.2, 0.2],
    },
    "melbourne": {
        "label": "Melbourne",
        "boundaries": "data/abs_melbourne_suburbs_2021.geojson",
        "center": [145.07, -37.88],
        "fit": [[144.57, -38.21], [145.57, -37.55]],
        "graticule_extent": [[143.57, -39.21], [146.57, -36.55]],
        "graticule_step": [0.25, 0.25],
    },
}


def params(prefix):
    return [
        {"name": f"{prefix}_zoom", "value": 1},
        {"name": f"{prefix}_pan_x", "value": 0},
        {"name": f"{prefix}_pan_y", "value": 0},
    ]


def projection(config, prefix, width_signal="childWidth"):
    return {
        "type": "mercator",
        "center": config["center"],
        "fit": {
            "type": "Feature",
            "properties": {},
            "geometry": {"type": "MultiPoint", "coordinates": config["fit"]},
        },
        "extent": {
            "expr": (
                f"[[{width_signal} / 2 + {prefix}_pan_x - ({width_signal} - 20) * "
                f"{prefix}_zoom / 2, height / 2 + {prefix}_pan_y - "
                f"(height - 20) * {prefix}_zoom / 2], [{width_signal} / 2 + "
                f"{prefix}_pan_x + ({width_signal} - 20) * {prefix}_zoom / 2, "
                f"height / 2 + {prefix}_pan_y + (height - 20) * "
                f"{prefix}_zoom / 2]]"
            )
        },
        "clipExtent": {"expr": f"[[0, 0], [{width_signal}, height]]"},
    }


def map_base(config):
    return [
        {
            "data": {"sphere": True},
            "mark": {"type": "geoshape", "fill": "#EAF3F8", "stroke": None, "clip": True},
        },
        {
            "data": {
                "url": config["boundaries"] + "?v=3",
                "format": {"type": "json", "property": "features"},
            },
            "mark": {
                "type": "geoshape",
                "fill": "#F4F3EF",
                "stroke": "#92A6AE",
                "strokeWidth": 0.45,
                "clip": True,
            },
        },
        {
            "data": {
                "graticule": {
                    "step": config["graticule_step"],
                    "extent": config["graticule_extent"],
                }
            },
            "mark": {
                "type": "geoshape",
                "fill": None,
                "stroke": "#B9D1DE",
                "strokeWidth": 0.4,
                "opacity": 0.35,
                "clip": True,
            },
        },
    ]


def symbol_specification(slug, config):
    prefix = slug
    layers = map_base(config)
    layers.append(
        {
            "data": {"url": "data/publisher_contact_locality_summary.csv"},
            "transform": [
                {"filter": f"datum.map_city === '{config['label']}'"},
                {
                    "calculate": "datum.winning_books / datum.listed_books * 100",
                    "as": "winner_share_pct",
                },
            ],
            "mark": {
                "type": "circle",
                "opacity": 0.9,
                "stroke": "white",
                "strokeWidth": 0.8,
                "clip": True,
            },
            "encoding": {
                "longitude": {"field": "longitude", "type": "quantitative"},
                "latitude": {"field": "latitude", "type": "quantitative"},
                "order": {"field": "listed_books", "type": "quantitative", "sort": "descending"},
                "size": {
                    "field": "listed_books",
                    "type": "quantitative",
                    "title": "Listed books",
                    "scale": {"type": "linear", "domain": [0, 22], "range": [12, 850], "zero": True},
                    "legend": {
                        "orient": "bottom",
                        "values": [1, 10, 20],
                        "symbolFillColor": "white",
                        "symbolStrokeColor": "#74300B",
                        "symbolStrokeWidth": 1.5,
                    },
                },
                "color": {
                    "field": "winner_share_pct",
                    "type": "quantitative",
                    "title": "Winner share (%)",
                    "scale": {
                        "domain": [0, 20, 40],
                        "range": ["#E8BB82", "#BB7330", "#74300B"],
                        "interpolate": "lab",
                        "clamp": True,
                    },
                    "legend": {
                        "gradientLength": 190,
                        "gradientThickness": 10,
                        "values": [0, 20, 40],
                        "format": ".0f",
                        "titleOrient": "top",
                        "titleAnchor": "start",
                    },
                },
                "tooltip": [
                    {"field": "map_city", "type": "nominal", "title": "City"},
                    {"field": "contact_locality", "type": "nominal", "title": "Area"},
                    {"field": "listed_books", "type": "quantitative", "title": "Listed books", "format": ","},
                    {"field": "winning_books", "type": "quantitative", "title": "Winners"},
                    {"field": "winner_share_pct", "type": "quantitative", "title": "Winner share", "format": ".1f"},
                ],
            },
        }
    )
    return {
        "$schema": "https://vega.github.io/schema/vega-lite/v5.json",
        "description": (
            f"Publisher-contact localities around {config['label']} for Prime Minister's "
            "Literary Awards shortlist records, 2022–2026. Circle area shows listed books; "
            "copper color shows winner share."
        ),
        "width": "container",
        "height": 340,
        "background": "white",
        "params": params(prefix),
        "projection": projection(config, prefix, width_signal="width"),
        "layer": layers,
        "config": {
            "font": "Arial",
            "title": {"font": "Georgia", "subtitleFont": "Arial"},
            "view": {"stroke": "#C7D6DE", "strokeWidth": 0.7},
            "legend": {"labelFont": "Arial", "titleFont": "Arial", "orient": "bottom"},
        },
    }


def bin_small_multiples_spec():
    panels = []
    for slug, config in CITIES.items():
        prefix = slug
        bins = map_base(config)
        bins.append(
            {
                "transform": [{"filter": f"datum.metro === '{config['label']}'"}],
                "mark": {"type": "geoshape", "stroke": "white", "strokeWidth": 1, "opacity": 0.94, "clip": True},
                "encoding": {
                    "color": {
                        "field": "listed_books",
                        "type": "quantitative",
                        "title": "Award books in one area",
                        "scale": {
                            "domain": [1, 34],
                            "range": ["#DCEDE4", "#0F6652"],
                            "clamp": True,
                        },
                        "legend": None,
                    },
                    "tooltip": [
                        {"field": "metro", "type": "nominal", "title": "Contact metro"},
                        {"field": "publishers", "type": "quantitative", "title": "Distinct publishers"},
                        {"field": "listed_books", "type": "quantitative", "title": "Listed books"},
                        {"field": "winning_books", "type": "quantitative", "title": "Winners"},
                    ],
                },
            }
        )
        panels.append(
            {
                "name": prefix,
                "width": 500,
                "height": 238,
                "title": {
                    "text": config["label"],
                    "anchor": "start",
                    "fontSize": 15,
                    "fontWeight": "bold",
                    "offset": 4,
                    "color": "#173B69" if slug == "sydney" else "#8C6D00",
                },
                "projection": projection(config, prefix, width_signal=500),
                "layer": bins,
            }
        )
    return {
        "$schema": "https://vega.github.io/schema/vega-lite/v5.json",
        "description": "Equal-area bins show the number of Prime Minister’s Literary Awards books associated with documented publisher contacts across Sydney and Melbourne, 2022–2026.",
        "spacing": 16,
        "params": params("sydney") + params("melbourne"),
        "data": {
            "url": "data/pmla_publisher_contact_hex_bins.geojson?v=4",
            "format": {"type": "json", "property": "features"},
        },
        "transform": [
            {"calculate": "datum.properties.metro_areas", "as": "metro"},
            {"calculate": "datum.properties.publishers", "as": "publishers"},
            {"calculate": "datum.properties.listed_books", "as": "listed_books"},
            {"calculate": "datum.properties.winning_books", "as": "winning_books"},
        ],
        "hconcat": panels,
        "resolve": {"scale": {"color": "shared"}, "legend": {"color": "shared"}},
        "config": {
            "background": "white",
            "font": "Arial",
            "view": {"stroke": "#C7D6DE", "strokeWidth": 0.7},
            "title": {"font": "Georgia", "subtitleFont": "Arial"},
            "legend": {
                "orient": "bottom",
                "direction": "horizontal",
                "titleFontSize": 12,
                "titleFontWeight": "bold",
                "labelFontSize": 12,
                "labelColor": "#202124",
                "titleColor": "#202124",
                "offset": 8,
                "padding": 0,
            },
        },
    }


if __name__ == "__main__":
    for slug, config in CITIES.items():
        target = ROOT / f"charts/section4/publisher_{slug}_localities.vl.json"
        target.write_text(json.dumps(symbol_specification(slug, config), indent=2) + "\n")
        print(target.relative_to(ROOT))
    bin_target = ROOT / "charts/section4/publisher_contact_hex_small_multiples.vl.json"
    bin_target.write_text(json.dumps(bin_small_multiples_spec(), indent=2) + "\n")
    print(bin_target.relative_to(ROOT))
