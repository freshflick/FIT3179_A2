"""Prepare ABS SAL GeoJSON for Vega's spherical polygon winding convention.

Query the official ASGS2021 SAL layer at
https://geo.abs.gov.au/arcgis/rest/services/ASGS2021/SAL/MapServer/0/query
with a Sydney or Melbourne bounding envelope, outSR=4326, and f=geojson.
Pass the downloaded city GeoJSON and output path to this script. Vega/D3
requires clockwise outer rings, the reverse of RFC 7946 GeoJSON output.
"""

import json
import sys
from pathlib import Path


def signed_area(ring):
    return sum(a[0] * b[1] - b[0] * a[1]
               for a, b in zip(ring, ring[1:])) / 2


def orient_polygon(rings):
    prepared = []
    for index, ring in enumerate(rings):
        clockwise = signed_area(ring) < 0
        if clockwise != (index == 0):
            ring = list(reversed(ring))
        prepared.append(ring)
    return prepared


def main(source, target):
    document = json.loads(Path(source).read_text())
    features = []
    for feature in document["features"]:
        geometry = feature["geometry"]
        if geometry["type"] == "Polygon":
            coordinates = orient_polygon(geometry["coordinates"])
        elif geometry["type"] == "MultiPolygon":
            coordinates = [orient_polygon(polygon) for polygon in geometry["coordinates"]]
        else:
            continue
        features.append({"type": "Feature",
                         "properties": {"name": feature["properties"].get(
                             "sal_name_2021", feature["properties"].get("name"))},
                         "geometry": {"type": geometry["type"],
                                      "coordinates": coordinates}})
    Path(target).write_text(json.dumps({"type": "FeatureCollection",
                                        "features": features}, separators=(",", ":")))
    print(f"Wrote {len(features)} suburb polygons to {target}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
